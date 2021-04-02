"""SQLAlchemy database models for Ordnance Survey Open Names"""

from sqlalchemy import Column, func, Index, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import column_property

from fhodot.models.base import DeclarativeBase


class OSOpenNamesObject:
    """Mixin class with common definitions for OS Open Names objects"""

    # pylint:disable=too-few-public-methods

    # Standardised names stored directly in database rather than using
    # column_property; it's not possible to use the (non-immutable)
    # Postgres 'unaccent' function within an index.

    os_id = Column(String(20), primary_key=True)
    name_1 = Column(String)
    name_1_lang = Column(String(3))
    name_1_std = Column(String)
    name_2 = Column(String)
    name_2_lang = Column(String(3))
    name_2_std = Column(String)
    postcode_district = Column(String(4))

    @declared_attr
    def postcode_area(cls): # pylint:disable=no-self-argument
        """Return leading letter(s) from postcode_district"""
        return column_property(
            func.substring(cls.postcode_district, "^[A-Z]+"))

    @declared_attr
    def __table_args__(cls): # pylint:disable=no-self-argument
        """Define indexes for table"""
        # pylint:disable=no-member
        # returns tuple
        # https://docs.sqlalchemy.org/en/13/orm/extensions/declarative/mixins.html#creating-indexes-with-mixins
        return (
            Index(f"{cls.__tablename__}_name_1_std_idx", cls.name_1_std),
            Index(f"{cls.__tablename__}_name_2_std_idx", cls.name_2_std),
            Index(f"{cls.__tablename__}_postcode_area_idx", cls.postcode_area))

    def __repr__(self):
        return f"<{type(self).__name__}: {self.name_1} ({self.os_id})>"


class OSPlace(DeclarativeBase, OSOpenNamesObject):
    """An Ordnance Survey Open Names populated place"""
    # pylint:disable=too-few-public-methods
    __tablename__ = "os_places"
    place_type = Column(String(16))


class OSRoad(DeclarativeBase, OSOpenNamesObject):
    """An Ordnance Survey Open Names named road"""
    # pylint:disable=too-few-public-methods
    __tablename__ = "os_roads"
