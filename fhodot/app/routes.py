"""Routes for Flask API"""

from csv import writer
from io import StringIO
from logging import error

from flask import abort, make_response, request
from geojson import dumps, FeatureCollection
from sqlalchemy.orm import joinedload, undefer

from fhodot.app import app, limiter
from fhodot.app.fhrs import get_selected_fhrs_properties, get_osm_mappings
from fhodot.app.osm import get_selected_osm_properties, get_fhrs_mappings
from fhodot.app.parse_addresses import parse_establishment_address
from fhodot.app.stats import get_fhrs_stats_features, get_osm_stats_features
from fhodot.app.suggest import (get_suggested_matches_by_osm_id,
                                get_full_osm_objects_query,
                                get_full_fhrs_establishments_dict)
from fhodot.app.utils import (
    num_objects_within_limit, get_bbox, get_geojson_line, get_geojson_point,
    get_geojson_feature_collection_string, query_within_bbox)
from fhodot.database import Session
from fhodot.models import FHRSEstablishment, OSMFHRSMapping, OSMObject


# consistent path to allow redirect to wsgi-bin in production
API_ROOT = "/api"

@app.route(f"{API_ROOT}/distant")
def data_distant():
    """OSM object data for objects with at least one distant FHRS match

    Queries within a bounding box and returns data in GeoJSON format
    """

    osm_objects = query_within_bbox(OSMObject, get_bbox(request.args)).\
        filter(OSMObject.fhrs_mappings.any(OSMFHRSMapping.distant)).\
        options(joinedload("fhrs_mappings").joinedload("fhrs_establishment"),
                undefer("fhrs_mappings.distance"))

    point_features = []
    line_features = []
    for osm_object in osm_objects:
        properties = get_selected_osm_properties(osm_object)

        properties["fhrsMappings"] = get_fhrs_mappings(
            osm_object, include_distance=True, include_location=True)
        for fhrs_mapping in properties["fhrsMappings"]:
            fhrs_est = fhrs_mapping["fhrsEstablishment"]
            line_features.append(
                get_geojson_line(
                    [{"lat": osm_object.lat, "lon": osm_object.lon},
                     {"lat": fhrs_est["lat"], "lon": fhrs_est["lon"]}]))

        point_features.append(
            get_geojson_point(osm_object.lat, osm_object.lon, properties))

    points_feature_collection = FeatureCollection(point_features)
    lines_feature_collection = FeatureCollection(line_features)

    return dumps({"points": points_feature_collection,
                  "lines": lines_feature_collection}) # dump to JSON string


@app.route(f"{API_ROOT}/fhrs")
def data_fhrs():
    """FHRS establishment data for a bounding box in GeoJSON format"""

    bbox = get_bbox(request.args)
    if not num_objects_within_limit(FHRSEstablishment, bbox, 10000):
        abort(413)
    establishments = query_within_bbox(FHRSEstablishment, bbox).\
        options(joinedload("osm_mappings").joinedload("osm_object"),
                undefer("osm_mappings.distance"))

    features = []
    for est in establishments:
        properties = get_selected_fhrs_properties(est)
        properties["osmMappings"] = get_osm_mappings(est,
                                                     include_distance=True)
        features.append(
            get_geojson_point(est.lat, est.lon, properties))

    return get_geojson_feature_collection_string(features)


@app.route(f"{API_ROOT}/osm")
def data_osm():
    """OSM object data for a bounding box in GeoJSON format"""

    bbox = get_bbox(request.args)
    if not num_objects_within_limit(OSMObject, bbox, 10000):
        abort(413)
    osm_objects = query_within_bbox(OSMObject, bbox).\
        options(joinedload("fhrs_mappings").joinedload("fhrs_establishment"),
                undefer("fhrs_mappings.distance"))

    features = []
    for osm_object in osm_objects:
        properties = get_selected_osm_properties(osm_object)
        properties["fhrsMappings"] = get_fhrs_mappings(osm_object,
                                                       include_distance=True)
        features.append(
            get_geojson_point(osm_object.lat, osm_object.lon, properties))

    return get_geojson_feature_collection_string(features)


@app.route(f"{API_ROOT}/fhrs/<int:fhrs_id>")
def data_fhrs_single(fhrs_id):
    """Properties for an FHRS establishment including parsed address"""
    fhrs_establishment = Session.query(FHRSEstablishment).get(fhrs_id)
    if not fhrs_establishment:
        abort(404)
    properties = get_selected_fhrs_properties(fhrs_establishment)
    properties["parsedAddress"] = parse_establishment_address(
        fhrs_establishment)
    return properties


@app.route(f"{API_ROOT}/stats_fhrs")
def data_stats_fhrs():
    """Local authority boundaries and statistics for FHRS objects"""

    try:
        zoom = int(request.args.get("zoom"))
    except (TypeError, ValueError):
        error("Zoom parameter not specified correctly")
        abort(400)

    features = get_fhrs_stats_features(get_bbox(request.args), zoom)
    return get_geojson_feature_collection_string(features)


@app.route(f"{API_ROOT}/stats_osm")
def data_stats_osm():
    """Local authority boundaries and statistics for OSM objects"""

    try:
        zoom = int(request.args.get("zoom"))
    except (TypeError, ValueError):
        error("Zoom parameter not specified correctly")
        abort(400)

    features = get_osm_stats_features(get_bbox(request.args), zoom)
    return get_geojson_feature_collection_string(features)


@app.route(f"{API_ROOT}/suggest")
def data_suggest():
    """OSM objects with suggested matches for a bbox in GeoJSON format"""

    bbox = get_bbox(request.args)
    if not num_objects_within_limit(OSMObject, bbox, 1000):
        abort(413)

    matches_by_osm_id = get_suggested_matches_by_osm_id(bbox)
    osm_objects_full = get_full_osm_objects_query(matches_by_osm_id)
    fhrs_establishments_full_by_id = get_full_fhrs_establishments_dict(
        matches_by_osm_id)

    # create a list of features that will become a GeoJSON feature collection
    features = []
    for osm_object in osm_objects_full:
        properties = get_selected_osm_properties(osm_object)
        properties["fhrsMappings"] = get_fhrs_mappings(osm_object)
        properties["suggestedMatches"] = []
        osm_id = osm_object.osm_id_single_space
        for suggested_match in matches_by_osm_id[osm_id]:
            suggested_match_full = fhrs_establishments_full_by_id[
                suggested_match.fhrs_id]
            est_properties = get_selected_fhrs_properties(suggested_match_full)
            properties["suggestedMatches"].append(est_properties)

        features.append(
            get_geojson_point(osm_object.lat, osm_object.lon, properties))

    return get_geojson_feature_collection_string(features)


@app.route(f"{API_ROOT}/surveyme")
@limiter.limit("1 per minute")
@limiter.limit("10 per day")
def data_surveyme():
    """CSV of incorrect fhrs:ids for Robert Whittaker's Survey Me!"""

    query = Session.query(OSMFHRSMapping).\
        filter(OSMFHRSMapping.fhrs_establishment == None).\
        options(joinedload("osm_object")) # pylint: disable=singleton-comparison

    string_io = StringIO()
    csv_writer = writer(string_io)
    csv_writer.writerow(["type", "id", "lat", "lon", "name", "fhrs:id"])
    for mapping in query:
        osm = mapping.osm_object
        csv_writer.writerow([osm.osm_type[0], osm.osm_id_by_type, osm.lat,
                             osm.lon, osm.name, mapping.fhrs_id])

    response = make_response(string_io.getvalue())
    response.headers[
        "Content-Disposition"] = "attachment; filename=surveyme.csv"
    response.headers["Content-type"] = "text/csv"
    return response
