"""Tests for fhodot.app.utils"""

from unittest import TestCase

from flask import request
from sqlalchemy.orm.query import Query
from werkzeug.exceptions import BadRequest

from fhodot.app import app
from fhodot.app.utils import get_bbox, query_within_bbox
from fhodot.database import Session
from fhodot.models.fhrs import FHRSAuthority, FHRSEstablishment
from fhodot.models.osm import OSMObject
from tests import TestCaseWithReconfiguredSession


def helper_get_bbox_params(bbox):
    """Helper function to get bounding box parameters from dict"""
    return "&".join([f"{key}={value}" for key, value in bbox.items()])


class TestGetBbox(TestCase):
    """Test get_bbox"""

    def test_valid_bbox(self):
        """Should return a dict of bounding box co-ordinates"""
        bbox = {"l": 1.234, "b": 2.345, "r": 3.456, "t": 4.567}
        params = helper_get_bbox_params(bbox)
        with app.test_request_context(f"/test?{params}"):
            self.assertEqual(get_bbox(request.args), bbox)


    def test_missing_key(self):
        """Should abort request with 400 error"""
        with self.assertLogs(level="ERROR"):
            with self.assertRaises(BadRequest):
                with app.test_request_context("/test?l=1.234"):
                    get_bbox(request.args)


    def test_bad_key(self):
        """Should abort request with 400 error"""
        # 'a' instead of 'l'
        bbox = {"a": 1.234, "b": 2.345, "r": 3.456, "t": 4.567}
        params = helper_get_bbox_params(bbox)
        with self.assertLogs(level="ERROR"):
            with self.assertRaises(BadRequest):
                with app.test_request_context(f"/test?{params}"):
                    get_bbox(request.args)


    def test_bad_value(self):
        """Should abort request with 400 error"""
        bbox = {"l": "bad", "b": 2.345, "r": 3.456, "t": 4.567}
        params = helper_get_bbox_params(bbox)
        with self.assertLogs(level="ERROR"):
            with self.assertRaises(BadRequest):
                with app.test_request_context(f"/test?{params}"):
                    get_bbox(request.args)


def helper_create_est(fhrs_id, lat, lon, auth):
    """Helper function to create FHRS establishment for testing"""
    est = FHRSEstablishment(
        fhrs_id=fhrs_id,
        name="Establishment Name",
        authority=auth)
    est.set_location(lat=lat, lon=lon)
    return est


def helper_create_osm(osm_id, lat, lon):
    """Helper function to create OSM object for testing"""
    osm_object = OSMObject(osm_id_single_space=osm_id,
                           location=f"POINT({lon} {lat})")
    return osm_object


class TestQueryWithinBbox(TestCaseWithReconfiguredSession):
    """Test query_within_bbox"""

    def setUp(self):
        super().setUp()

        # test authority with not null columns set
        self.auth = FHRSAuthority(
            code=321,
            name="Authority Name",
            region_name="Authority Region",
            xml_url="http://ratings.food.gov.uk/OpenDataFiles/FHRS760en-GB.xml")
        Session.add(self.auth)
        Session.commit()

        # common bounding box
        self.bbox = {"l": -1, "b": -1, "r": 1, "t": 1}


    # inherits tearDown


    def test_returns_query(self):
        """Returns a query object which can be iterated over

        There doesn't seem any benefit in returning query.all() instead.
        """
        self.assertIsInstance(query_within_bbox(FHRSEstablishment, self.bbox),
                              Query)


    def test_returns_establishments_within_bbox(self):
        """Should return the two establishments within the bbox"""

        within_1 = helper_create_est(1, lat="0", lon="0", auth=self.auth)
        within_2 = helper_create_est(2, lat="0.5", lon="0.5", auth=self.auth)
        outside = helper_create_est(3, lat="1.5", lon="1.5", auth=self.auth)
        Session.add_all([within_1, within_2, outside])
        Session.commit()

        fhrs_ids_returned = [est.fhrs_id for est in
                             query_within_bbox(FHRSEstablishment, self.bbox)]
        self.assertIn(1, fhrs_ids_returned)
        self.assertIn(2, fhrs_ids_returned)
        self.assertNotIn(3, fhrs_ids_returned)


    def test_returns_osm_objects_within_bbox(self):
        """Should return the two OSM objects within the bbox"""

        within_1 = helper_create_osm(osm_id=1, lat="0", lon="0")
        within_2 = helper_create_osm(osm_id=2, lat="0.5", lon="0.5")
        outside = helper_create_osm(osm_id=3, lat="1.5", lon="1.5")
        Session.add_all([within_1, within_2, outside])
        Session.commit()

        osm_ids_returned = [osm_object.osm_id_single_space for osm_object in
                            query_within_bbox(OSMObject, self.bbox)]
        self.assertIn(1, osm_ids_returned)
        self.assertIn(2, osm_ids_returned)
        self.assertNotIn(3, osm_ids_returned)


    def test_bad_object_class(self):
        """Should raise AssertionError"""
        with self.assertRaises(AssertionError):
            query_within_bbox(FHRSAuthority, self.bbox)
