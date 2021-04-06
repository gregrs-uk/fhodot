"""Functions relating to stats endpoints for Flask API"""


from itertools import groupby

from geoalchemy2 import Geometry
from geoalchemy2.functions import (ST_AsGeoJSON, ST_Intersects,
                                   ST_SimplifyPreserveTopology)
from geojson import Feature, loads
from sqlalchemy import cast, func

from fhodot.app.utils import get_envelope
from fhodot.database import Session
from fhodot.models import (FHRSAuthority, FHRSAuthorityStatistic,
                           LocalAuthorityDistrict,
                           OSMLocalAuthorityDistrictStatistic)


def get_pixel_size_degrees_for_zoom_level(zoom):
    """Returns size of one pixel in degrees for given zoom level"""
    return 360 / ((2**zoom) * 256)


def get_fhrs_stats_features(bbox, zoom):
    """Returns list of GeoJSON features for districts with FHRS stats"""

    subquery = Session.query(
        func.max(FHRSAuthorityStatistic.date).label("latest")
    ).subquery()

    stats_long = Session.query(FHRSAuthorityStatistic).\
        select_from(FHRSAuthorityStatistic).\
        filter(
            FHRSAuthorityStatistic.date == subquery.c.latest,
            ST_Intersects(LocalAuthorityDistrict.boundary, get_envelope(bbox))
        ).\
        join(FHRSAuthority,
             FHRSAuthority.code == FHRSAuthorityStatistic.authority_code).\
        join(LocalAuthorityDistrict).\
        all()

    stats_by_authority = groupby(stats_long,
                                 lambda instance: instance.authority)

    features = []
    for authority, stats in stats_by_authority:
        boundary_geojson = Session.query(
            ST_AsGeoJSON(ST_SimplifyPreserveTopology(
                cast(LocalAuthorityDistrict.boundary, Geometry),
                get_pixel_size_degrees_for_zoom_level(zoom)))
        ).\
        select_from(FHRSAuthority).\
        join(LocalAuthorityDistrict).\
        filter(FHRSAuthority.code == authority.code).\
        scalar()

        properties = {
            "name": authority.name,
            "districtCode": authority.district.code,
            "stats": {item.statistic: item.value for item in stats}
        }
        properties["stats"]["total"] = sum(properties["stats"].values())

        features.append(Feature(geometry=loads(boundary_geojson),
                                properties=properties))

    return features


def get_osm_stats_features(bbox, zoom):
    """Returns list of GeoJSON features for districts with OSM stats"""

    subquery = Session.query(
        func.max(OSMLocalAuthorityDistrictStatistic.date).label("latest")
    ).subquery()

    stats_long = Session.query(OSMLocalAuthorityDistrictStatistic).\
        filter(
            OSMLocalAuthorityDistrictStatistic.date == subquery.c.latest,
            ST_Intersects(LocalAuthorityDistrict.boundary, get_envelope(bbox))
        ).\
        join(LocalAuthorityDistrict,
             (OSMLocalAuthorityDistrictStatistic.district_code ==
              LocalAuthorityDistrict.code)).\
        all()

    stats_by_district = groupby(stats_long, lambda instance: instance.district)

    features = []
    for district, stats in stats_by_district:
        boundary_geojson = Session.query(
            ST_AsGeoJSON(ST_SimplifyPreserveTopology(
                cast(LocalAuthorityDistrict.boundary, Geometry),
                get_pixel_size_degrees_for_zoom_level(zoom)))
        ).\
        filter(LocalAuthorityDistrict.code == district.code).\
        scalar()

        properties = {
            "name": district.name,
            "districtCode": district.code,
            "stats": {item.statistic: item.value for item in stats}
        }
        properties["stats"]["total"] = sum(properties["stats"].values())

        features.append(Feature(geometry=loads(boundary_geojson),
                                properties=properties))

    return features
