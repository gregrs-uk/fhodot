"""fhodot: the Food Hygiene Open Data OpenStreetMap tool"""

from logging import basicConfig

from fhodot.config import LOG_LEVEL
from fhodot.database import Session
from fhodot.models.base import DeclarativeBase

basicConfig(format="%(levelname)s: %(message)s", level=LOG_LEVEL)

# create database tables if they don't already exist
DeclarativeBase.metadata.create_all(bind=Session.get_bind())
