"""Tests for fhodot.models.fhrs.FHRSAuthority"""

from datetime import datetime, timedelta

from fhodot.models.fhrs import FHRSAuthority
from tests import TestCaseWithReconfiguredSession


class TestFHRSAuthorityValidation(TestCaseWithReconfiguredSession):
    """Test validation of FHRS authority fields"""

    def setUp(self):
        super().setUp()
        self.auth = FHRSAuthority()
        # not allowed to be null
        self.auth.code = 123
        self.auth.xml_url = "http://ratings.food.gov.uk/OpenDataFiles/FHRS760en-GB.xml"


    # inherits tearDown


    def test_authority_code_validation(self):
        """Setting invalid authority code raises appropriate exception"""

        with self.assertRaises(TypeError):
            self.auth.code = None
        for auth_code in ["string", 9999999999, -1]:
            with self.assertRaises(ValueError):
                self.auth.code = auth_code


    def test_authority_name_region_validation(self):
        """Setting authority name or region as None raises TypeError"""

        with self.assertRaises(TypeError):
            self.auth.name = None
        with self.assertRaises(TypeError):
            self.auth.region_name = None


    def test_last_published_validation(self):
        """Setting bad last_published raises a ValueError. Allow None"""

        with self.assertRaises(AssertionError): # programming error
            self.auth.last_published = "string"
        with self.assertRaises(ValueError):
            future = datetime.now() + timedelta(days=7)
            self.auth.last_published = future

        self.auth.last_published = None
        self.assertIsNone(self.auth.last_published)

        valid = datetime(2020, 1, 1, 12, 0, 0)
        self.auth.last_published = valid
        self.assertEqual(valid, self.auth.last_published)

        soon = datetime.now() + timedelta(minutes=89)
        self.auth.last_published = soon
        self.assertEqual(soon, self.auth.last_published)


    def test_email_validation(self):
        """Invalid email > None with warning. Blank email left blank."""

        with self.assertLogs(level="WARNING"):
            self.auth.email = "invalid@email"
        self.assertIsNone(self.auth.email)

        with self.assertLogs(level="WARNING"):
            self.auth.email = ""
        self.assertEqual(self.auth.email, "")


    def test_xml_url_validation(self):
        """Invalid or missing xml_url raises a ValueError"""

        with self.assertRaises(ValueError):
            self.auth.xml_url = None
        with self.assertRaises(ValueError):
            self.auth.xml_url = "http://1.2.3.4"


    def test_set_last_published_from_string(self):
        """Test set_last_published_from_string"""
        # non-string (programming error)
        with self.assertRaises(AssertionError):
            self.auth.set_last_published_from_string(123)
        # None or blank: returns False, sets to None
        self.assertFalse(self.auth.set_last_published_from_string(None))
        self.assertFalse(self.auth.set_last_published_from_string(""))
        self.assertEqual(self.auth.last_published, None)
        # bad format: returns False with warning, sets to None
        with self.assertLogs(level="WARNING"):
            self.assertFalse(
                self.auth.set_last_published_from_string("1/1/2020"))
        self.assertIsNone(self.auth.last_published)
        # correct with 3 trailing digits
        self.auth.set_last_published_from_string("2020-06-30T00:30:51.223")
        self.assertIsInstance(self.auth.last_published, datetime)
        self.assertEqual(self.auth.last_published,
                         datetime(2020, 6, 30, 0, 30, 51))
        # correct with 2 trailing digits
        self.auth.set_last_published_from_string("2020-06-30T00:30:51.22")
        self.assertIsInstance(self.auth.last_published, datetime)
        self.assertEqual(self.auth.last_published,
                         datetime(2020, 6, 30, 0, 30, 51))
