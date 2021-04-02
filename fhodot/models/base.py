"""DeclarativeBase for SQLAlchemy database models

Separate module to avoid circular imports.
"""

from sqlalchemy.ext.declarative import declarative_base

DeclarativeBase = declarative_base()
