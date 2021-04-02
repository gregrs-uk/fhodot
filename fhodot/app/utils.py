"""Utility functions for Flask API"""

from logging import error

from flask import abort
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_Intersects, ST_MakeEnvelope
from geojson import dumps, Feature, FeatureCollection, LineString, Point
from sqlalchemy import cast

from fhodot.database import Session
from fhodot.models.fhrs import FHRSEstablishment
from fhodot.models.osm import OSMObject


def get_bbox(args):
    """Get and validate bounding box from URL parameters"""

    bbox = {"l": None, "b": None, "r": None, "t": None}
    for side in bbox.keys(): # pylint: disable=consider-iterating-dictionary
        parameter = args.get(side)
        try:
            bbox[side] = float(parameter)
        except (ValueError, TypeError):
            error("Bounding box parameters not specified correctly")
            abort(400)
    return bbox


def get_envelope(bbox):
    """Return envelope for bounding box"""
    assert isinstance(bbox, dict)
    return cast(
        ST_MakeEnvelope(bbox["l"], bbox["b"], bbox["r"], bbox["t"], 4326),
        Geography)


def query_within_bbox(object_class, bbox):
    """Query database for instances of object_class within bbox

    Returns a query object which can be iterated over or specified
    further. N.B. doesn't eager load relationships so you may want to
    use joinedload if you plan to access related objects.
    """

    assert object_class in [FHRSEstablishment, OSMObject]

    # ST_Intersects with the envelope cast to Geography is quicker than
    # ST_Within, even when there is a location::geometry index.

    envelope = get_envelope(bbox)
    result = Session.query(object_class).\
        filter(ST_Intersects(object_class.location, envelope))
    return result


def get_geojson_point(lat, lon, properties):
    """Returns a GeoJSON feature with Point geometry"""
    # pass a tuple to Point
    return Feature(geometry=Point((lon, lat)), properties=properties)


def get_geojson_line(points):
    """Returns a GeoJSON feature with LineString geometry

    Points argument should be a list of objects with lat and lon.
    """
    assert isinstance(points, list)
    for point in points:
        assert isinstance(point, dict)
        assert "lat" in point and "lon" in point
    # pass a list of tuples to LineString
    return Feature(geometry=LineString(
        [(point["lon"], point["lat"]) for point in points]))


def get_geojson_feature_collection_string(features):
    """Returns a GeoJSON FeatureCollection as a string"""
    feature_collection = FeatureCollection(features)
    return dumps(feature_collection) # dump to JSON string
