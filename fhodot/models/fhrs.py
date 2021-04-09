"""SQLAlchemy database models for FHRS establishments and authorities

N.B. @validates methods are triggered when setting values, but not when
committing an object with unset values (i.e. None) that should not be
null.
"""

from datetime import datetime, timedelta
from logging import warning
from re import fullmatch, sub

from geoalchemy2 import Geography, Geometry
from geoalchemy2.functions import ST_X, ST_Y
from sqlalchemy import (cast, Column, Date, DateTime, ForeignKey, Integer, or_,
                        String, Text)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import column_property, joinedload, relationship, validates

from fhodot.database import Session
from fhodot.models.base import DeclarativeBase


# 1st capture group:
#   1-2 letters, 1 number, 1 number or letter
# 2nd capture group (optional):
#   optional space, 1 number (or letter O) and optionally 2 letters
#   letter O instead of zero (common error) converted later
POSTCODE_PATTERN = r"^([A-Z]{1,2}[0-9][A-Z0-9]?)( ?[O0-9]([A-Z]{2})?)?$"


class FHRSEstablishment(DeclarativeBase):
    """A Food Hygience Rating Scheme establishment

    The lat/lon properties can only be returned once the instance is
    persistent i.e. added to session and session flushed (perhaps
    automatically before a query).
    """

    # pylint: disable=no-self-use

    __tablename__ = "fhrs_establishments"

    fhrs_id = Column(Integer, primary_key=True, autoincrement=False)
    location = Column(Geography('POINT'))
    lat = column_property(ST_Y(cast(location, Geometry)))
    lon = column_property(ST_X(cast(location, Geometry)))
    name = Column(Text(), nullable=False)
    address_1 = Column(Text())
    address_2 = Column(Text())
    address_3 = Column(Text())
    address_4 = Column(Text())
    postcode = Column(String(8)) # length ensured by validator regex
    postcode_original = Column(Text) # unvalidated
    rating_date = Column(Date)
    authority_code = Column(
        Integer, ForeignKey("fhrs_authorities.code"), nullable=False)

    authority = relationship("FHRSAuthority", back_populates="establishments")
    osm_mappings = relationship(
        "OSMFHRSMapping", back_populates="fhrs_establishment", uselist=True,
        primaryjoin=("foreign(FHRSEstablishment.fhrs_id) == " +
                     "OSMFHRSMapping.fhrs_id"))
    district = relationship(
        "LocalAuthorityDistrict",
        primaryjoin=("func.ST_Intersects(" +
                     "foreign(FHRSEstablishment.location)," +
                     "LocalAuthorityDistrict.boundary).as_comparison(1, 2)"),
        back_populates="fhrs_establishments",
        sync_backref=False,
        viewonly=True)


    def __repr__(self):
        return f"<FHRSEstablishment: {self.name} ({self.fhrs_id})>"


    def set_location(self, lat, lon):
        """Set the establishment's location using its lat/lon"""
        if lat and lon:
            assert isinstance(lat, str) and isinstance(lon, str)
            self.location = f"POINT({lon} {lat})"
        else:
            self.location = None


    @hybrid_property
    def num_matches_same_postcodes(self):
        """Return number of matched OSM objects with same postcode"""
        return [mapping.postcodes_match
                for mapping in self.osm_mappings].count(True)


    @num_matches_same_postcodes.expression
    def num_matches_same_postcodes(self):
        """Not implemented at expression level"""
        raise NotImplementedError(
            "num_matches_same_postcodes not implemented at expression level")


    @hybrid_property
    def num_matches_different_postcodes(self):
        """Return num of matched OSM objects with different postcode

        i.e. OSM fhrs:id tag matches FHRS establishment but the OSM and
        FHRS postcodes are different (including if a postcode is missing
        on either but not both sides)
        """
        return [mapping.postcodes_match
                for mapping in self.osm_mappings].count(False)


    @num_matches_different_postcodes.expression
    def num_matches_different_postcodes(self):
        """Not implemented at expression level"""
        raise NotImplementedError("num_matches_different_postcodes not " +
                                  "implemented at expression level")


    @validates("fhrs_id", "authority_code")
    def validate_integer_keys(self, column, value):
        """Validate the FHRS ID and authority code"""
        return validate_positive_integer(column, value)


    @validates("name")
    def validate_not_null(self, column, value):
        """Validate not null columns with no other conditions"""
        if not value:
            raise TypeError(f"Value for column {column} is missing")
        return value.strip() # trim whitespace


    @validates("postcode_original")
    def validate_postcode_original(self, _, value):
        """Strip whitespace and convert blank string to None"""
        if value is not None:
            assert isinstance(value, str)
            value = value.strip()
            value = value if value else None # convert blank to None
        return value


    @validates("address_1", "address_2", "address_3", "address_4")
    def validate_address_lines(self, column, value):
        """Move postcode from address line if no postcode already

        Also strip whitespace and convert blank string to None.
        """
        if isinstance(value, str):
            value = value.strip()
            value = value if value else None # convert blank to None
        if value is None:
            return value

        assert isinstance(value, str)
        match = fullmatch(POSTCODE_PATTERN, value)
        # valid postcode including second part
        if match and match.group(2) and not self.postcode:
            msg = f"Moving {value} from {column} to postcode"
            if self.fhrs_id:
                msg += f" for establishment {self.fhrs_id}"
            warning(msg)
            self.postcode = value
            value = None

        return value


    @validates("postcode")
    def validate_postcode(self, _, value):
        """Standardise and validate the postcode"""

        if value is None:
            return value

        assert isinstance(value, str)
        value = value.strip().upper()
        if not value: # if (now) blank string
            return None

        # replace any (inner) whitespace with a single space
        value = sub(r"\s+", " ", value)

        match = fullmatch(POSTCODE_PATTERN, value)
        if not match:
            warning(f"Postcode {value} invalid: not storing")
            return None

        first_part, second_part = match.group(1, 2) # 0 is full match
        assert first_part # not blank

        if not second_part:
            return first_part

        # replace letter O at start of 2nd part with zero (common error)
        # to ensure space between parts, take out then add back in
        second_part = sub("^O", "0", second_part.lstrip())
        return f"{first_part} {second_part}"


class FHRSAuthority(DeclarativeBase):
    """A Food Hygience Rating Scheme local authority"""

    # pylint: disable=no-self-use

    __tablename__ = "fhrs_authorities"

    # N.B. called LocalAuthorityIdCode in data from Authorities API endpoint
    code = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(Text(), nullable=False)
    region_name = Column(Text(), nullable=False)
    last_published = Column(DateTime)
    email = Column(Text())
    # need the URL to download establishment data for this authority
    xml_url = Column(Text(), nullable=False)
    district_code = Column(
        String(9), ForeignKey("la_districts.code", ondelete="SET NULL"))

    establishments = relationship("FHRSEstablishment",
                                  back_populates="authority",
                                  cascade="all, delete-orphan")
    district = relationship("LocalAuthorityDistrict",
                            back_populates="fhrs_authority")
    statistics = relationship(
        "FHRSAuthorityStatistic",
        back_populates="authority",
        uselist=True,
        primaryjoin=("foreign(FHRSAuthority.code) == " +
                     "FHRSAuthorityStatistic.authority_code"))


    def __repr__(self):
        return f"<FHRSAuthority: {self.name} ({self.code})>"


    def get_local_authority_district(self):
        """Returns the LocalAuthorityDistrict for this authority

        Calculates this geographically by finding the district boundary
        within which most of this authority's establishments are found.
        This may not work if there isn't a 1:1 relationship between FHRS
        authorities and Local Authority Districts.
        """

        # This method is preferable to finding the district in which the
        # centroid of the establishments falls because sometimes this
        # centroid can fall outside the district depending on the shape
        # of its boundary.

        query = Session.query(FHRSEstablishment).\
            filter(
                FHRSEstablishment.authority_code == self.code,
                # a number of establishments in East Renfrewshire have
                # this postcode and location far away in Chelmsford
                or_(FHRSEstablishment.postcode_original != "PRIVATE",
                    FHRSEstablishment.postcode_original.is_(None))).\
            options(
                # fhrs_authority used by add_authority_districts_in_session
                joinedload("district").joinedload("fhrs_authority"))

        # only use establishments that have a location set and are
        # within a district
        districts = [est.district for est in query if est.district]
        if not districts:
            return None # avoid ValueError in max() below
        counts = {dist:districts.count(dist) for dist in districts}
        top_district = max(counts, key=counts.get)
        proportion = counts[top_district] / sum(counts.values())

        # if 90% or more of the authority's establishments are in the
        # top district, assume that they are associated
        if proportion > 0.9:
            return top_district
        return None


    def set_last_published_from_string(self, string):
        """Set last_published from string as obtained from FHRS API

        Return True if correctly interpreted as datetime, false
        otherwise.
        """

        if not string:
            self.last_published = None
            return False

        assert isinstance(string, str)

        # format example: 2020-06-30T00:30:51.223
        # remove trailing full stop and up to 3 digits
        string = sub(r"\.\d{0,3}$", "", string)
        try:
            self.last_published = datetime.strptime(
                string, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            warning(f"last_published '{string}' of authority '{self.name}'" +
                    f"({self.code}) doesn't match expected format")
            self.last_published = None
            return False

        return True


    @validates("code")
    def validate_code(self, column, value):
        """Validate the authority code"""
        return validate_positive_integer(column, value)


    @validates("name", "region_name")
    def validate_not_null(self, column, value):
        """Validate not null columns with no other conditions"""

        if not value:
            raise TypeError(f"Value for column {column} is missing")
        return value


    @validates("last_published")
    def validate_last_published(self, __, value):
        """Check last published date is None or a datetime in the past
        or less than 90 minutes into the future to allow for possible
        British Summer Time issues
        """

        if value is None:
            return value

        assert isinstance(value, datetime)
        if value > datetime.now() + timedelta(minutes=90):
            raise ValueError(
                f"last_published date {value} of authority '{self.name}' " +
                f"({self.code}) should be in the past")
        return value


    @validates("email")
    def validate_email(self, __, value):
        """Validate the email, converting invalid to None with a
        warning. None/blank left unchanged with a warning.
        """

        if not value: # None or blank
            warning(f"Email address missing for authority '{self.name}' " +
                    f"({self.code})")
            return value

        # remove any whitespace
        value = value.strip()
        # an overly simple regex check
        if fullmatch(r"^\S+@\S+\.\S+$", value):
            return value

        warning(f"Email address '{value}' of authority '{self.name}' " +
                f"({self.code}) invalid: not storing")
        return None


    @validates("xml_url")
    def validate_xml_url(self, __, value):
        """Validate the XML URL, not allowing blank or None"""

        if not value:
            raise ValueError(f"xml_url of authority '{self.name}' " +
                             f"({self.code}) is missing")

        if isinstance(value, str):
            # remove any whitespace
            value = value.strip()
            # an overly simple regex check
            if fullmatch(r"^https*://.*\.gov\.uk/.*\.xml$", value):
                return value

        raise ValueError(
            f"xml_url '{value}' of authority '{self.name}' ({self.code}) " +
            "is invalid")


def validate_positive_integer(column, value):
    """Validate positive values stored in an Integer column

    Convert to integer where possible e.g. from a string. N.B. Integer
    column could store negative values too but we want validation to
    fail in this case.
    """

    if isinstance(value, str):
        try:
            value = int(value)
        except ValueError:
            raise ValueError(
                f"Could not convert string '{value}' to integer for {column}")

    if not isinstance(value, int): # e.g. NoneType
        raise TypeError(
            f"Value for column {column} should be an integer or string " +
            f"representation of an integer, not {type(value).__name__})")

    # https://www.postgresql.org/docs/9.1/datatype-numeric.html
    if value < 0 or value > 2147483647:
        raise ValueError(
            f"{column} value {value} should be between 0 and 2147483647")

    return value
