"""Import the ONS Local Authority Districts boundaries shapefile"""

from fhodot.boundaries import add_boundaries_to_session
from fhodot.database import Session, session_scope
from fhodot.models.district import LocalAuthorityDistrict


SHAPEFILE_PATH = "import/boundaries/LAD_MAY_2023_UK_BGC_V2.shp" # pylint: disable=line-too-long
FIELD_PREFIX = "LAD23"

with session_scope() as session:
    Session.query(LocalAuthorityDistrict).delete()
    add_boundaries_to_session(SHAPEFILE_PATH, FIELD_PREFIX)
