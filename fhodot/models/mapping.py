"""SQLAlchemy model for mapping OSM objects <-> FHRS establishments

Elsewhere, the OpenStreetMap data is imported by Imposm 3 and an
association table is generated using an SQL script. OSM database tables
are defined using Declarative rather than using Automap to reflect the
structure in order to allow easier creation of test cases. See also the
Imposm mapping YAML file.
"""

from geoalchemy2.functions import ST_Distance, ST_DWithin
from sqlalchemy import (
    and_, BigInteger, Column, ForeignKey, Integer, not_, or_, select)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import column_property, relationship

from fhodot.models.base import DeclarativeBase
from fhodot.models.fhrs import FHRSEstablishment
from fhodot.models.osm import OSMObject


class OSMFHRSMapping(DeclarativeBase):
    """A unique mapping between an OSMObject and an FHRSEstablishment

    Represents association table for many-to-many relationship between
    OSM objects and FHRS establishments. Doesn't necessarily indicate a
    successful match.
    """

    __tablename__ = "osm_fhrs_mapping"

    osm_id_single_space = Column(BigInteger,
                                 ForeignKey("osm.osm_id_single_space"),
                                 primary_key=True, autoincrement=False)
    # not a foreign key because fhrs_id in OSM data may not match FHRS data
    fhrs_id = Column(Integer, primary_key=True, autoincrement=False)

    osm_object = relationship("OSMObject", back_populates="fhrs_mappings")
    fhrs_establishment = relationship(
        "FHRSEstablishment", back_populates="osm_mappings", uselist=False,
        primaryjoin=("OSMFHRSMapping.fhrs_id == " +
                     "foreign(FHRSEstablishment.fhrs_id)"))

    # In analysis of existing matches, 95th percentile distance was 238m
    # so a mapping with a distance of 250m or more between OSMObject and
    # FHRSEstablishment is considered distant
    distant = column_property(
        select([not_(ST_DWithin(OSMObject.location, FHRSEstablishment.location,
                                250, use_spheroid=False))]).\
        where(and_(OSMObject.osm_id_single_space == osm_id_single_space,
                   FHRSEstablishment.fhrs_id == fhrs_id)),
        deferred=True # to prevent slowing queries where not required
    )

    distance = column_property(
        select([ST_Distance(OSMObject.location, FHRSEstablishment.location)]).\
        where(and_(OSMObject.osm_id_single_space == osm_id_single_space,
                   FHRSEstablishment.fhrs_id == fhrs_id)),
        deferred=True # to prevent slowing queries where not required
    )


    def __repr__(self):
        return (f"<OSMFHRSMapping: {repr(self.osm_object)} <=> " +
                f"{repr(self.fhrs_establishment)}>")


    @hybrid_property
    def postcodes_match(self):
        """Return value depends on whether OSM/FHRS postcodes match

        Checks addr:postcode and not:addr:postcode for a match and
        returns True if either matches, False if neither matches, None
        if FHRS ID doesn't match an establishment.
        """
        if not self.fhrs_establishment:
            return None
        return (self.osm_object.addr_postcode == \
                    self.fhrs_establishment.postcode or
                self.osm_object.not_addr_postcode == \
                    self.fhrs_establishment.postcode or
                not self.fhrs_establishment.postcode)


    @postcodes_match.expression
    def postcodes_match(cls): # pylint: disable=no-self-argument,no-self-use
        """Return value depends on whether OSM/FHRS postcodes match

        Checks addr:postcode and not:addr:postcode for a match and
        returns True if either matches, False if neither matches, None
        if FHRS ID doesn't match an establishment.

        N.B. unlike the Python version, the expression version requires
        appropriate joins to OSMObject and FHRSEstablishment.
        """
        # see https://docs.sqlalchemy.org/en/13/orm/extensions/hybrid.html#join-dependent-relationship-hybrid
        return or_(OSMObject.addr_postcode == FHRSEstablishment.postcode,
                   OSMObject.not_addr_postcode == FHRSEstablishment.postcode,
                   FHRSEstablishment.postcode.is_(None))
