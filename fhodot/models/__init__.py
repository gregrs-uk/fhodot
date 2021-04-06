"""SQLAlchemy database models

Models should be imported from this module (fhodot.models), but see its
submodules for the model definitions, which import the same
DeclarativeBase from fhodot.models.base.
"""

# The imports below register all model classes so that the mapper can
# locate class names needed within relationships, even when we only
# import a single class elsewhere.

from fhodot.models.district import LocalAuthorityDistrict
from fhodot.models.fhrs import FHRSAuthority, FHRSEstablishment
from fhodot.models.mapping import OSMFHRSMapping
from fhodot.models.os_open_names import OSOpenNamesObject, OSPlace, OSRoad
from fhodot.models.osm import OSMObject
from fhodot.models.stats import (FHRSAuthorityStatistic,
                                 OSMLocalAuthorityDistrictStatistic)
