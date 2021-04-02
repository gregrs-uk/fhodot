"""Setup for SQLAlchemy database models

See the fhrs and osm modules for the actual models, which import the
same DeclarativeBase from fhodot.models.base.
"""

# The imports below register all model classes so that the mapper can
# locate class names needed within relationships, even when we only
# import a single class elsewhere.

import fhodot.models.district
import fhodot.models.fhrs
import fhodot.models.mapping
import fhodot.models.os_open_names
import fhodot.models.osm
import fhodot.models.stats
