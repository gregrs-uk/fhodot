"""Module for importing ONS Local Authority Districts boundaries"""

import fiona
from geoalchemy2.functions import ST_Transform
from geoalchemy2.shape import from_shape
from shapely.geometry import shape
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon

from fhodot.database import Session
from fhodot.models.district import LocalAuthorityDistrict


def add_boundaries_to_session(shapefile_path, field_prefix):
    """Read boundaries from shapefile and add to database session

    This doesn't commit the session.

    shapefile_path (string): path of boundaries shapefile
    field_prefix (string): prefix to code/name field names in shapefile
    """

    with fiona.open(shapefile_path) as collection:
        assert collection.crs["init"] == "epsg:27700"

        for feature in collection:
            properties = feature["properties"]
            boundary = shape(feature["geometry"])
            if isinstance(boundary, Polygon):
                boundary = MultiPolygon([boundary])
            wkb = from_shape(boundary, srid=27700)

            Session.add(
                LocalAuthorityDistrict(
                    code=properties[field_prefix + "CD"],
                    name=properties[field_prefix + "NM"],
                    boundary=ST_Transform(wkb, 4326)))
