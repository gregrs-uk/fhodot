"""SQLAlchemy database model for OpenStreetMap objects

Elsewhere, the OpenStreetMap data is imported by Imposm 3 and an
association table is generated using an SQL script. OSM database tables
are defined using Declarative rather than using Automap to reflect the
structure in order to allow easier creation of test cases. See also the
Imposm mapping YAML file.
"""

from geoalchemy2 import Geography, Geometry
from geoalchemy2.functions import ST_X, ST_Y
from sqlalchemy import BigInteger, case, cast, Column, or_, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import column_property, relationship

from fhodot.models.base import DeclarativeBase


class OSMObject(DeclarativeBase):
    """An OpenStreetMap node/way/relation"""

    __tablename__ = "osm"

    osm_id_single_space = Column(BigInteger, primary_key=True,
                                 autoincrement=False)
    osm_id_by_type = column_property(cast(case(
        [(osm_id_single_space <= -1e17, 0 - osm_id_single_space - 1e17),
         (osm_id_single_space < 0, 0 - osm_id_single_space)],
        else_=osm_id_single_space), BigInteger))
    osm_type = column_property(case(
        [(osm_id_single_space <= -1e17, "relation"),
         (osm_id_single_space < 0, "way")],
        else_="node"))
    location = Column(Geography)
    lat = column_property(ST_Y(cast(location, Geometry)))
    lon = column_property(ST_X(cast(location, Geometry)))
    fhrs_ids_string = Column(String)
    fhrs_ids_string_valid = column_property(
        or_(fhrs_ids_string == "",
            fhrs_ids_string.op("~")("^[0-9]+(;[0-9]+)*$")))
    name = Column(String)
    addr_postcode = Column(String)
    not_addr_postcode = Column(String)

    fhrs_mappings = relationship("OSMFHRSMapping", back_populates="osm_object")
    district = relationship(
        "LocalAuthorityDistrict",
        primaryjoin=("func.ST_Intersects(foreign(OSMObject.location)," +
                     "LocalAuthorityDistrict.boundary).as_comparison(1, 2)"),
        back_populates="osm_objects",
        sync_backref=False,
        viewonly=True)


    def __repr__(self):
        return f"<OSMObject: {self.name} ({self.osm_id_single_space})>"


    @hybrid_property
    def num_matches_same_postcodes(self):
        """Return number of matched establishments with same postcode"""
        return [mapping.postcodes_match
                for mapping in self.fhrs_mappings].count(True)


    @num_matches_same_postcodes.expression
    def num_matches_same_postcodes(self):
        """Not implemented at expression level"""
        raise NotImplementedError(
            "num_matches_same_postcodes not implemented at expression level")


    @hybrid_property
    def num_matches_different_postcodes(self):
        """Return num of matched establishments with different postcode

        i.e. OSM fhrs:id tag matches an FHRS establishment but the OSM
        and FHRS postcodes are different (including if a postcode is
        missing on either but not both sides)
        """
        return [mapping.postcodes_match
                for mapping in self.fhrs_mappings].count(False)


    @num_matches_different_postcodes.expression
    def num_matches_different_postcodes(self):
        """Not implemented at expression level"""
        raise NotImplementedError("num_matches_different_postcodes not " +
                                  "implemented at expression level")


    @hybrid_property
    def num_mismatched_fhrs_ids(self):
        """Return number of FHRS IDs that don't match an establishment"""
        return [mapping.fhrs_establishment
                for mapping in self.fhrs_mappings].count(None)


    @num_mismatched_fhrs_ids.expression
    def num_mismatched_fhrs_ids(self):
        """Not implemented at expression level"""
        raise NotImplementedError(
            "num_mismatched_fhrs_ids not implemented at expression level")
