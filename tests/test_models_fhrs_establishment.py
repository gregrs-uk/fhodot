"""Tests for fhodot.models.fhrs.FHRSEstablishment"""

from sqlalchemy import inspect

from fhodot.database import Session
from fhodot.models.fhrs import FHRSAuthority, FHRSEstablishment
from fhodot.models.mapping import OSMFHRSMapping
from fhodot.models.osm import OSMObject
from tests import TestCaseWithReconfiguredSession


class TestFHRSEstablishmentValidation(TestCaseWithReconfiguredSession):
    """Test validation of FHRS establishment fields"""

    def setUp(self):
        super().setUp()
        self.est = FHRSEstablishment()


    # inherits tearDown


    def test_set_location(self):
        """Test set_location"""

        self.est.set_location("13.579", "24.680")
        self.assertEqual(self.est.location, "POINT(24.680 13.579)")
        self.est.set_location("1.234", None)
        self.assertIsNone(self.est.location)
        self.est.set_location(None, None)
        self.assertIsNone(self.est.location)
        with self.assertRaises(AssertionError):
            self.est.set_location(13.579, 24.680)


    # don't need to test validation of FHRS ID and authority code
    # because it calls the same function as validation of
    # FHRSAuthority.authority_code, which is tested


    def test_establishment_name_validation(self):
        """Test validation of establishment name"""

        self.est.name = "  Whitespace  "
        self.assertEqual(self.est.name, "Whitespace")
        with self.assertRaises(TypeError):
            self.est.name = ""
        with self.assertRaises(TypeError):
            self.est.name = None


    def test_address_postcode_original_whitespace_removal(self):
        """Test whitespace removal from address and original postcode"""
        for field in ["address_1", "address_2", "address_3", "address_4",
                      "postcode_original"]:
            setattr(self.est, field, "  Whitespace  ")
            self.assertEqual(getattr(self.est, field), "Whitespace")
            setattr(self.est, field, "  ")
            self.assertIsNone(getattr(self.est, field))
            setattr(self.est, field, None)
            self.assertIsNone(getattr(self.est, field))


    def test_move_postcode_from_address(self):
        """Move postcode from address line if no postcode already"""
        example_postcode = "AB12 3XY"
        self.est.postcode = None
        with self.assertLogs(level="WARNING"):
            self.est.address_1 = example_postcode
        self.assertEqual(self.est.postcode, example_postcode)
        self.assertIsNone(self.est.address_1)


    def test_keep_postcode_in_address_if_postcode_already(self):
        """If existing postcode, don't move postcode from address line"""
        self.est.postcode = "AB12 3XY"
        self.est.address_1 = "XY45 6AB"
        self.assertEqual(self.est.postcode, "AB12 3XY") # unchanged
        # stored in address_1 even though it matches postcode pattern
        self.assertEqual(self.est.address_1, "XY45 6AB")


    def test_postcode_validation_valid(self):
        """Test validation/formatting of valid postcodes

        Lowercase should be converted to uppercase. Leading and trailing
        whitespace should be stripped. Multiple inner spaces should be
        converted to a single space. Letter O at start of second part
        should be converted to zero.
        """

        # dict of all valid input formats and expected output
        valid = {
            # first part only
            " a1 ": "A1", " a1b ": "A1B", " a12 ": "A12", " ab1 ": "AB1",
            " ab1c ": "AB1C", " ab12 ": "AB12",
            # first part and number of second part with space
            " a1 2 ": "A1 2", " a1b 2 ": "A1B 2", " a12 3 ": "A12 3",
            " ab1 2 ": "AB1 2", " ab1c 2 ": "AB1C 2", " ab12 3 ": "AB12 3",
            " ab12 o ": "AB12 0",
            # first part and number of second part with 2 spaces
            " a1  2 ": "A1 2", " a1b  2 ": "A1B 2", " a12  3 ": "A12 3",
            " ab1  2 ": "AB1 2", " ab1c  2 ": "AB1C 2", " ab12  3 ": "AB12 3",
            " ab12  o ": "AB12 0",
            # first part and number of second part without space
            # N.B. a12 or ab12 interpreted as first part only
            " a1b2 ": "A1B 2", " a123 ": "A12 3", " ab1c2 ": "AB1C 2",
            " ab123 ": "AB12 3", " ab12o ": "AB12 0",
            # full postcode with space
            " a1 2xy ": "A1 2XY", " a1b 2xy ": "A1B 2XY",
            " a12 3xy ": "A12 3XY", " ab1 2xy ": "AB1 2XY",
            " ab1c 2xy ": "AB1C 2XY", " ab12 3xy ": "AB12 3XY",
            " ab12 oxy ": "AB12 0XY",
            # full postcode with 2 spaces
            " a1  2xy ": "A1 2XY", " a1b  2xy ": "A1B 2XY",
            " a12  3xy ": "A12 3XY", " ab1  2xy ": "AB1 2XY",
            " ab1c  2xy ": "AB1C 2XY", " ab12  3xy ": "AB12 3XY",
            " ab12  oxy ": "AB12 0XY",
            # full postcode without space
            " a12xy ": "A1 2XY", " a1b2xy ": "A1B 2XY",
            " a123xy ": "A12 3XY", " ab12xy ": "AB1 2XY",
            " ab1c2xy ": "AB1C 2XY", " ab123xy ": "AB12 3XY",
            " ab12oxy ": "AB12 0XY",
            # empty
            "": None, "  ": None, None: None}

        for input_string, expected_output in valid.items():
            self.est.postcode = input_string
            self.assertEqual(self.est.postcode, expected_output)


    def test_postcode_validation_invalid(self):
        """Test validation/formatting of invalid postcodes"""

        # selection of invalid postcodes inspired by the real data
        invalid = ["AB1 2 XY", "AB 12 3XY", "AB12 3XY.", "AB12 XYZ", "AB1 XY2",
                   "AB1 @XY", "Devon", "No Postcode"]

        for input_string in invalid:
            with self.assertLogs(level="WARNING"):
                self.est.postcode = input_string
            self.assertIsNone(self.est.postcode)


class TestFHRSEstablishmentLatLon(TestCaseWithReconfiguredSession):
    """Test latitude/longitude column properties"""

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
        # test establishment with not null columns set
        self.est = FHRSEstablishment(
            fhrs_id=123,
            name="Establishment Name",
            authority_code=321)
        self.est.set_location(lat="52.123", lon="-1.123")


    # inherits tearDown


    def test_establishment_lat_lon_transient_pending_instance(self):
        """lat/lon properties of transient/pending instance are None"""

        self.assertTrue(inspect(self.est).transient)
        self.assertIsNone(self.est.lat)
        self.assertIsNone(self.est.lon)

        Session.add(self.est)
        self.assertTrue(inspect(self.est).pending)
        self.assertIsNone(self.est.lat)
        self.assertIsNone(self.est.lon)


    def test_establishment_lat_lon_persistent_instance(self):
        """lat/lon properties of persistent instance should be returned"""

        Session.add(self.est)
        Session.flush() # e.g. before a query, doesn't need committing
        self.assertTrue(inspect(self.est).persistent)
        self.assertEqual(self.est.lat, 52.123)
        self.assertEqual(self.est.lon, -1.123)


    def test_establishment_lat_lon_query(self):
        """lat/lon properties in a query should be returned"""

        Session.add(self.est)
        fetched = Session.query(
            FHRSEstablishment.lat, FHRSEstablishment.lon).one()
        self.assertEqual(fetched.lat, 52.123)
        self.assertEqual(fetched.lon, -1.123)


class TestFHRSEstablishmentNumMatches(TestCaseWithReconfiguredSession):
    """Test num_matches_(same/different)_postcodes"""

    def setUp(self):
        super().setUp()
        # test authority with not null columns set
        auth = FHRSAuthority(
            code=321,
            name="Authority Name",
            region_name="Authority Region",
            xml_url="http://ratings.food.gov.uk/OpenDataFiles/FHRS760en-GB.xml")
        Session.add(auth)
        Session.commit()
        # test establishment with not null columns set
        self.est = FHRSEstablishment(
            fhrs_id=123,
            name="Establishment Name",
            authority=auth)


    # inherits tearDown


    def test_no_matches(self):
        """Both functions return 0 if no matches"""
        Session.add(self.est)
        self.assertEqual(self.est.num_matches_same_postcodes, 0)
        self.assertEqual(self.est.num_matches_different_postcodes, 0)


    def test_three_matches_two_with_same_postcode(self):
        """Returns number of OSM matches with same/different postcode"""

        osm_1 = OSMObject(osm_id_single_space=1, addr_postcode="AB12 3XY")
        osm_2 = OSMObject(osm_id_single_space=2, addr_postcode="AB12 3XY")
        osm_3 = OSMObject(osm_id_single_space=3, addr_postcode="XY12 3AB")
        osm_extra = OSMObject(osm_id_single_space=4, addr_postcode="AB12 3XY")
        self.est.postcode = "AB12 3XY"
        self.est.osm_mappings = [
            OSMFHRSMapping(fhrs_establishment=self.est, osm_object=osm_1),
            OSMFHRSMapping(fhrs_establishment=self.est, osm_object=osm_2),
            OSMFHRSMapping(fhrs_establishment=self.est, osm_object=osm_3)]
        Session.add_all([self.est, osm_extra])

        self.assertEqual(self.est.num_matches_same_postcodes, 2)
        self.assertEqual(self.est.num_matches_different_postcodes, 1)


    def test_expressions(self):
        """Should raise NotImplementedError"""

        with self.assertRaises(NotImplementedError):
            Session.query(FHRSEstablishment).\
                filter(FHRSEstablishment.num_matches_same_postcodes == 1)

        with self.assertRaises(NotImplementedError):
            Session.query(FHRSEstablishment).\
                filter(FHRSEstablishment.num_matches_different_postcodes == 1)
