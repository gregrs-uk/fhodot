"""SQLAlchemy database model for local authority districts"""

from geoalchemy2 import Geography
from sqlalchemy import Column, String, Text
from sqlalchemy.orm import deferred, relationship

from fhodot.models.base import DeclarativeBase


class LocalAuthorityDistrict(DeclarativeBase):
    """A local authority district with a geographical boundary"""

    # pylint: disable=no-self-use,too-few-public-methods

    __tablename__ = "la_districts"

    code = Column(String(9), primary_key=True, autoincrement=False)
    boundary = deferred(Column(Geography("MULTIPOLYGON")))
    name = Column(Text(), nullable=False)

    fhrs_authority = relationship("FHRSAuthority",
                                  back_populates="district",
                                  uselist=False)
    fhrs_establishments = relationship(
        "FHRSEstablishment",
        primaryjoin=("func.ST_Intersects(" +
                     "foreign(FHRSEstablishment.location)," +
                     "LocalAuthorityDistrict.boundary)" +
                     ".as_comparison(1, 2)"),
        back_populates="district",
        sync_backref=False,
        viewonly=True)
    osm_objects = relationship(
        "OSMObject",
        primaryjoin=("func.ST_Intersects(foreign(OSMObject.location)," +
                     "LocalAuthorityDistrict.boundary)" +
                     ".as_comparison(1, 2)"),
        back_populates="district",
        sync_backref=False,
        viewonly=True)
    statistics_osm = relationship(
        "OSMLocalAuthorityDistrictStatistic",
        back_populates="district",
        uselist=True,
        primaryjoin=("foreign(LocalAuthorityDistrict.code) == " +
                     "OSMLocalAuthorityDistrictStatistic.district_code"))


    def __repr__(self):
        return f"<LocalAuthorityDistrict: {self.name} ({self.code})>"
