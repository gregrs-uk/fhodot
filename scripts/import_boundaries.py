"""Import the ONS Local Authority Districts boundaries shapefile"""

from fhodot.boundaries import add_boundaries_to_session
from fhodot.database import Session, session_scope
from fhodot.models.district import LocalAuthorityDistrict


SHAPEFILE_PATH = "import/boundaries/LAD_DEC_2025_UK_BGC.shp" # pylint: disable=line-too-long
FIELD_PREFIX = "LAD25"

with session_scope() as session:
    Session.query(LocalAuthorityDistrict).delete()
    add_boundaries_to_session(SHAPEFILE_PATH, FIELD_PREFIX)
