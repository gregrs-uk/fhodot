"""SQLAlchemy database model for statistics"""

from sqlalchemy import (Column, Date, Integer, PrimaryKeyConstraint, String,
                        Text)
from sqlalchemy.orm import relationship

from fhodot.models.base import DeclarativeBase


class Statistic:
    """Mixin class with common definitions for statistics"""

    # pylint: disable=no-self-use,too-few-public-methods

    date = Column(Date)
    statistic = Column(Text)
    value = Column(Integer)


class FHRSAuthorityStatistic(DeclarativeBase, Statistic):
    """Statistic relating to an FHRS authority on a particular date"""

    # pylint: disable=no-self-use,too-few-public-methods

    __tablename__ = "stats_fhrs"
    __table_args__ = (
        PrimaryKeyConstraint("authority_code", "date", "statistic"),)

    # not a foreign key so that stats kept if authority disappears
    authority_code = Column(Integer)
    authority = relationship(
        "FHRSAuthority",
        back_populates="statistics",
        uselist=False,
        primaryjoin=("FHRSAuthorityStatistic.authority_code == " +
                     "foreign(FHRSAuthority.code)"))


    def __repr__(self):
        if self.authority:
            return (
                f"<FHRSAuthorityStatistic: {self.statistic} for " +
                f"{self.authority.name} on {self.date} = {self.value}>")
        return (
            f"<FHRSAuthorityStatistic: {self.statistic} for " +
            f"authority {self.authority_code} on {self.date} = {self.value}>")


class OSMLocalAuthorityDistrictStatistic(DeclarativeBase, Statistic):
    """Statistic relating to OSM objects in a district on a date"""

    # pylint: disable=no-self-use,too-few-public-methods

    __tablename__ = "stats_osm"
    __table_args__ = (
        PrimaryKeyConstraint("district_code", "date", "statistic"),)

    # not a foreign key in case districts have to change
    district_code = Column(String(9))
    district = relationship(
        "LocalAuthorityDistrict",
        back_populates="statistics_osm",
        uselist=False,
        primaryjoin=("OSMLocalAuthorityDistrictStatistic.district_code == " +
                     "foreign(LocalAuthorityDistrict.code)"))


    def __repr__(self):
        if self.district:
            return (
                f"<OSMLocalAuthorityDistrictStatistic: {self.statistic} for " +
                f"{self.district.name} on {self.date} = {self.value}>")
        return (
            f"<OSMLocalAuthorityDistrictStatistic: {self.statistic} for " +
            f"district {self.district_code} on {self.date} = {self.value}>")
