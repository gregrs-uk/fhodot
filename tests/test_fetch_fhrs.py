"""Tests for fhodot.fetch_fhrs"""

from contextlib import redirect_stderr
from copy import deepcopy
from datetime import datetime, timedelta
from io import StringIO
from os.path import abspath, dirname, join
from xml.etree.ElementTree import ParseError

from requests import RequestException
from sqlalchemy.exc import IntegrityError

from fhodot import fetch_fhrs
from fhodot.database import Session, session_scope
from fhodot.models.fhrs import DeclarativeBase, FHRSAuthority, \
    FHRSEstablishment
from tests import TestCaseWithReconfiguredSession


def helper_read_xml(filename):
    """Helper to read XML file in test_fetch_fhrs_data directory"""

    path = join(dirname(abspath(__file__)), "test_fetch_fhrs_data", filename)
    with open(path, "r") as data_file:
        string = data_file.read()
    return string


AUTHORITIES_VALID_XML = helper_read_xml("authorities_valid.xml")
ESTABLISHMENTS_VALID_XML = helper_read_xml("establishments_valid.xml")


class TestRetryIfRequestException(TestCaseWithReconfiguredSession):
    """Test retry_if_request_exception"""

    def test_retry_if_request_exception(self):
        """Test retry_if_request_exception"""
        self.assertTrue(
            fetch_fhrs.retry_if_request_exception(RequestException()))
        self.assertFalse(
            fetch_fhrs.retry_if_request_exception(RuntimeError))


class TestParseXMLAuthorities(TestCaseWithReconfiguredSession):
    """Test parsing FHRS authorities from XML"""


    # inherits setUp and tearDown


    def test_parse_xml_authorities_valid_count(self):
        """Parsing example XML should return a list of 3 authorities"""

        authorities = fetch_fhrs.parse_xml_authorities(AUTHORITIES_VALID_XML)
        self.assertEqual(len(authorities), 3)
        self.assertTrue(isinstance(authorities[0], FHRSAuthority))


    def test_parse_xml_authorities_null_code(self):
        """Missing authority code should raise a TypeError"""

        xml_string = helper_read_xml("authorities_null_code.xml")
        with self.assertRaises(TypeError):
            fetch_fhrs.parse_xml_authorities(xml_string)


    def test_parse_xml_authorities_null_xml_url(self):
        """Missing XML URL should raise a ValueError"""

        xml_string = helper_read_xml("authorities_null_url.xml")
        with self.assertRaises(ValueError):
            fetch_fhrs.parse_xml_authorities(xml_string)


    def test_parse_xml_authorities_bad_xml(self):
        """XML parsing error should log and re-raise exception"""

        with self.assertRaises(ParseError):
            with self.assertLogs(level="CRITICAL"):
                fetch_fhrs.parse_xml_authorities("some invalid xml")


class TestCompareAuthorityCounts(TestCaseWithReconfiguredSession):
    """Test comparing count of authorities supplied with database"""

    def setUp(self):
        super().setUp()
        # load three valid authorities into the database
        authorities = fetch_fhrs.parse_xml_authorities(AUTHORITIES_VALID_XML)
        with self.assertLogs(level="DEBUG"):
            fetch_fhrs.merge_authorities_with_session(authorities)
        self.assertEqual(Session.query(FHRSAuthority).count(), 3)
        Session.close()


    # inherits tearDown


    def test_compare_authority_counts_equal(self):
        """Method returns True when counts are equal"""

        authorities = [FHRSAuthority(), FHRSAuthority(), FHRSAuthority()]
        self.assertEqual(len(authorities), 3)
        self.assertTrue(
            fetch_fhrs.compare_authority_counts(authorities))


    def test_compare_authority_counts_db_more_stop(self):
        """RuntimeError when database has >= 'stop' more authorities"""

        authorities = [FHRSAuthority()]
        self.assertEqual(len(authorities), 1)
        with self.assertRaises(RuntimeError):
            fetch_fhrs.compare_authority_counts(authorities, stop=2)


    def test_compare_authority_counts_db_more_warn(self):
        """Warning when database has >= 1, < 'stop' more authorities"""

        authorities = [FHRSAuthority(), FHRSAuthority()]
        self.assertEqual(len(authorities), 2)
        with self.assertLogs(level="WARNING"):
            fetch_fhrs.compare_authority_counts(authorities, stop=2)


    def test_compare_authority_counts_db_less(self):
        """Info given when database has fewer authorities"""

        authorities = [FHRSAuthority(), FHRSAuthority(),
                       FHRSAuthority(), FHRSAuthority()]
        self.assertEqual(len(authorities), 4)
        with self.assertLogs(level="INFO"):
            fetch_fhrs.compare_authority_counts(authorities)


class TestGetAuthoritiesRequiringFetch(TestCaseWithReconfiguredSession):
    """Test calculating which FHRS authorities require fetching"""

    def setUp(self):
        super().setUp()
        self.auth = FHRSAuthority(
            code=123,
            name="Authority Name",
            region_name="Authority Region",
            xml_url="http://ratings.food.gov.uk/OpenDataFiles/FHRS760en-GB.xml")


    # inherits tearDown


    def helper_add_authority(self, last_published):
        """Add an authority with particular last_published"""
        # separate instance from self.auth
        db_auth = deepcopy(self.auth)
        db_auth.last_published = last_published
        with self.assertLogs(level="DEBUG"):
            with session_scope():
                with self.assertLogs(level="DEBUG"):
                    fetch_fhrs.merge_authorities_with_session([db_auth])


    def test_get_authorities_requiring_fetch_stale(self):
        """An authority with stale data should be updated"""

        past = datetime.now() - timedelta(days=1)
        self.helper_add_authority(past)
        self.assertEqual(
            Session.query(FHRSAuthority).get(123).last_published, past)
        Session.close()

        # authority has newer last published
        self.auth.last_published = datetime.now()
        result = fetch_fhrs.get_authorities_requiring_fetch([self.auth])
        Session.close()
        self.assertEqual(result, [self.auth])


    def test_get_authorities_requiring_fetch_fresh(self):
        """An authority with up-to-date data should not be updated"""

        now = datetime.now()
        self.helper_add_authority(now)
        self.assertEqual(
            Session.query(FHRSAuthority).get(123).last_published, now)
        Session.close()

        # authority has same last published
        self.auth.last_published = now
        result = fetch_fhrs.get_authorities_requiring_fetch([self.auth])
        Session.close()
        self.assertEqual(result, [])


    def test_get_authorities_requiring_fetch_no_date_xml(self):
        """An XML authority with no last_published should be updated"""

        self.assertIsNone(self.auth.last_published)
        result = fetch_fhrs.get_authorities_requiring_fetch([self.auth])
        self.assertEqual(result, [self.auth])


    def test_get_authorities_requiring_fetch_no_date_database(self):
        """A database authority with no last_published should be updated"""

        self.helper_add_authority(None)
        self.assertIsNone(
            Session.query(FHRSAuthority).get(123).last_published)
        Session.close()

        # authority has last published in new data
        self.auth.last_published = datetime.now()
        result = fetch_fhrs.get_authorities_requiring_fetch([self.auth])
        self.assertEqual(result, [self.auth])


    def test_get_authorities_requiring_fetch_not_in_db(self):
        """An XML authority not in the database should be updated"""

        self.assertEqual(Session.query(FHRSAuthority).count(), 0)
        Session.close()

        self.auth.last_published = datetime.now()
        result = fetch_fhrs.get_authorities_requiring_fetch([self.auth])
        self.assertEqual(result, [self.auth])


class TestDeleteObsoleteAuthorities(TestCaseWithReconfiguredSession):
    """Test deleting obselete authorities from session"""

    def setUp(self):
        super().setUp()
        # load three valid authorities
        authorities = fetch_fhrs.parse_xml_authorities(AUTHORITIES_VALID_XML)

        # add an establishment to first authority
        authorities[0].establishments.append(FHRSEstablishment(
            fhrs_id=123, name="Test establishment"))
        self.auth_copy = deepcopy(authorities) # prevent detached instance

        # put into database
        with self.assertLogs(level="DEBUG"):
            with session_scope():
                with self.assertLogs(level="DEBUG"):
                    fetch_fhrs.merge_authorities_with_session(authorities)
        self.assertEqual(Session.query(FHRSAuthority).count(), 3)
        self.assertEqual(Session.query(FHRSEstablishment).count(), 1)
        Session.close()


    # inherits tearDown


    def test_delete_obsolete_authorities_none(self):
        """Non-obsolete authorities should not be deleted"""

        with self.assertLogs(level="DEBUG"):
            with session_scope():
                fetch_fhrs.delete_obsolete_authorities_from_session(
                    self.auth_copy)
        self.assertEqual(Session.query(FHRSAuthority).count(), 3)
        self.assertEqual(Session.query(FHRSEstablishment).count(), 1)
        Session.close()


    def test_delete_obsolete_authority_with_establishment(self):
        """Obsolete authorities and their establishments are deleted"""

        self.assertEqual(len(self.auth_copy[0].establishments), 1)
        del self.auth_copy[0]
        self.assertEqual(len(self.auth_copy), 2)

        with self.assertLogs(level="DEBUG"):
            with session_scope():
                with self.assertLogs(level="INFO"):
                    fetch_fhrs.delete_obsolete_authorities_from_session(
                        self.auth_copy)
        self.assertEqual(Session.query(FHRSAuthority).count(), 2)
        self.assertEqual(Session.query(FHRSEstablishment).count(), 0)
        Session.close()


    def test_delete_obsolete_authority_no_establishments(self):
        """Obsolete authorities without establishments are deleted"""

        self.assertEqual(len(self.auth_copy[1].establishments), 0)
        del self.auth_copy[1]
        self.assertEqual(len(self.auth_copy), 2)

        with self.assertLogs(level="DEBUG"):
            with session_scope():
                with self.assertLogs(level="INFO"):
                    fetch_fhrs.delete_obsolete_authorities_from_session(
                        self.auth_copy)
        self.assertEqual(Session.query(FHRSAuthority).count(), 2)
        self.assertEqual(Session.query(FHRSEstablishment).count(), 1)
        Session.close()


class TestAuthorityReadWrite(TestCaseWithReconfiguredSession):
    """Test writing, reading and deletion of FHRS authority data"""

    def setUp(self):
        super().setUp()
        # with not null columns set
        self.auth = FHRSAuthority(
            code=123,
            name="Authority Name",
            region_name="Authority Region",
            xml_url="http://ratings.food.gov.uk/OpenDataFiles/FHRS760en-GB.xml")


    # inherits tearDown


    def helper_merge_authorities(self, authorities):
        """Merge authorities using session_scope and swallow log"""
        with self.assertLogs(level="DEBUG"):
            with session_scope():
                fetch_fhrs.merge_authorities_with_session(authorities)


    def test_add_authorities_valid_count(self):
        """Adding 3 valid authorities should return count of 3"""

        authorities = fetch_fhrs.parse_xml_authorities(AUTHORITIES_VALID_XML)
        self.helper_merge_authorities(authorities)
        self.assertEqual(Session.query(FHRSAuthority).count(), 3)
        Session.close()


    def test_add_delete_authority_single_valid_some_empty(self):
        """Test write/read/delete of valid but partly empty authority"""
        # not null columns set above
        self.assertIsNone(self.auth.last_published)
        self.assertIsNone(self.auth.email)

        # add authority and check it's stored
        self.helper_merge_authorities([self.auth])
        self.assertTrue(Session.query(FHRSAuthority).get(self.auth.code))
        Session.close()

        # try deleting authority we just added
        with self.assertLogs(level="DEBUG"):
            with session_scope():
                Session.query(FHRSAuthority).\
                    filter(FHRSAuthority.code == self.auth.code).delete()
        self.assertIsNone(Session.query(FHRSAuthority).get(self.auth.code))
        Session.close()


    def test_modify_authority(self):
        """Existing authority should be modified"""

        self.helper_merge_authorities([self.auth])

        # modify authority
        self.auth.name = "Modified Authority Name"
        self.helper_merge_authorities([self.auth])

        self.assertEqual(Session.query(FHRSAuthority).count(), 1)
        fetched = Session.query(FHRSAuthority).get(self.auth.code)
        Session.close()
        self.assertEqual(fetched.name, self.auth.name)


    def test_add_authorities_no_table(self):
        """If authorities table doesn't exist, RuntimeError raised"""

        DeclarativeBase.metadata.drop_all(bind=self.connection)
        with self.assertRaises(RuntimeError):
            self.helper_merge_authorities([self.auth])


    def test_add_authorities_wrong_argument(self):
        """Bad argument raises TypeError"""

        with self.assertRaises(TypeError):
            self.helper_merge_authorities(self.auth) # not a list
        with self.assertRaises(TypeError):
            self.helper_merge_authorities([1, 2, 3]) # wrong type in list


    def test_commit_authority_with_nulls(self):
        """Committing authority with nulls raises IntegrityError

        Null authority code etc. should be caught by validator when
        calling parse_xml_authorities though.
        """

        # can't use self.auth because already has a value and the
        # validator won't let us set it back to None
        null_auth = FHRSAuthority()
        trap = StringIO()
        with self.assertRaises(IntegrityError):
            # trap error message
            with redirect_stderr(trap):
                self.helper_merge_authorities([null_auth])
        trap.close()


class TestParseXMLEstablishments(TestCaseWithReconfiguredSession):
    """Test parsing FHRS establishments from XML"""


    # inherits setUp and tearDown


    def test_parse_xml_establishments_valid_count(self):
        """Parsing example XML should return a list of 3 establishments"""

        establishments = fetch_fhrs.parse_xml_establishments(
            ESTABLISHMENTS_VALID_XML)
        self.assertEqual(len(establishments), 3)
        self.assertTrue(isinstance(establishments[0], FHRSEstablishment))


    def test_parse_xml_establishments_null_fhrsid(self):
        """Missing establishment FHRSID should raise a TypeError"""

        xml_string = helper_read_xml("establishments_null_fhrsid.xml")
        with self.assertRaises(TypeError):
            fetch_fhrs.parse_xml_establishments(xml_string)


    def test_parse_xml_establishments_null_authority_code(self):
        """Missing establishment auth'y code should raise a TypeError"""

        xml_string = helper_read_xml("establishments_null_authority.xml")
        with self.assertRaises(TypeError):
            fetch_fhrs.parse_xml_establishments(xml_string)


    def test_parse_xml_establishments_null_name(self):
        """Missing establishment name should raise a TypeError"""

        xml_string = helper_read_xml("establishments_null_name.xml")
        with self.assertRaises(TypeError):
            fetch_fhrs.parse_xml_establishments(xml_string)


    def test_parse_xml_establishments_bad_xml(self):
        """XML parsing error should log and re-raise exception"""

        with self.assertRaises(ParseError):
            with self.assertLogs(level="CRITICAL"):
                fetch_fhrs.parse_xml_establishments("some invalid xml")


class TestEstablishmentReadWrite(TestCaseWithReconfiguredSession):
    """Test writing, reading and deletion of FHRS establishment data"""

    def setUp(self):
        super().setUp()
        # test authority with not null columns set
        self.auth = FHRSAuthority(
            code=760, # to match establishments_valid.xml
            name="Authority Name",
            region_name="Authority Region",
            xml_url="http://ratings.food.gov.uk/OpenDataFiles/FHRS760en-GB.xml")
        Session.add(self.auth)
        Session.commit()
        # test establishment with not null columns set
        self.est = FHRSEstablishment(
            fhrs_id=123,
            name="Establishment Name",
            authority_code=760)


    # inherits tearDown


    def helper_replace_establishments(self, authority, establishments):
        """Replace authorities using session_scope and swallow log"""
        with self.assertLogs(level="DEBUG"):
            with session_scope():
                fetch_fhrs.replace_establishments_for_authority_in_session(
                    authority, establishments)


    def test_add_establishments_valid_count(self):
        """Adding 3 valid establishments should return count of 3"""

        establishments = fetch_fhrs.parse_xml_establishments(
            ESTABLISHMENTS_VALID_XML)
        self.helper_replace_establishments(self.auth, establishments)
        self.assertEqual(Session.query(FHRSEstablishment).count(), 3)
        Session.close()


    def test_replace_establishments_valid(self):
        """Test replacing 3 establishments for an authority with 1"""

        # prevent detached instance errors
        auth_code = self.auth.code
        fhrs_id = self.est.fhrs_id

        # add 3 valid establishments
        establishments = fetch_fhrs.parse_xml_establishments(
            ESTABLISHMENTS_VALID_XML)
        self.helper_replace_establishments(self.auth, establishments)
        self.assertEqual(Session.query(FHRSEstablishment).count(), 3)
        Session.close()

        # replace with 1 valid establishment for same authority
        self.auth = Session.query(FHRSAuthority).get(auth_code)
        self.helper_replace_establishments(self.auth, [self.est])
        self.assertEqual(Session.query(FHRSEstablishment).count(), 1)
        self.assertTrue(Session.query(FHRSEstablishment).get(fhrs_id))


    def test_replace_establishments_other_authority(self):
        """Replacing establishments shouldn't affect other authorities"""

        # add 3 valid establishments
        establishments = fetch_fhrs.parse_xml_establishments(
            ESTABLISHMENTS_VALID_XML)
        self.helper_replace_establishments(self.auth, establishments)
        self.assertEqual(Session.query(FHRSEstablishment).count(), 3)
        Session.close()

        # add a second authority with not null columns set
        second_auth = FHRSAuthority(
            code=789,
            name="Second Authority",
            region_name="Authority Region",
            xml_url="http://ratings.food.gov.uk/OpenDataFiles/FHRS760en-GB.xml")
        Session.add(second_auth)
        Session.commit()

        # add 1 establishment for this second authority
        self.est.authority_code = 789
        fhrs_id = self.est.fhrs_id # prevent detached instance error
        self.helper_replace_establishments(second_auth, [self.est])
        self.assertTrue(Session.query(FHRSEstablishment).get(fhrs_id))
        self.assertEqual(
            Session.query(FHRSEstablishment).\
                filter(FHRSEstablishment.authority_code == 760).count(),
            3)
        self.assertEqual(
            Session.query(FHRSEstablishment).\
                filter(FHRSEstablishment.authority_code == 789).count(),
            1)
        self.assertEqual(Session.query(FHRSEstablishment).count(), 4)


    def test_add_delete_establishment_single_valid_some_empty(self):
        """Test write/read/delete of valid but partly empty authority"""
        # not null columns set above
        for column in ["address_1", "address_2", "address_3", "address_4",
                       "postcode", "postcode_original", "location"]:
            self.assertIsNone(getattr(self.est, column))

        # prevents detached instance error
        fhrs_id = self.est.fhrs_id

        # add establishment and check it's stored
        self.helper_replace_establishments(self.auth, [self.est])
        self.assertTrue(Session.query(FHRSEstablishment).get(fhrs_id))
        Session.close()

        # try deleting establishment we just added
        with self.assertLogs(level="DEBUG"):
            with session_scope():
                Session.query(FHRSEstablishment).\
                    filter(FHRSEstablishment.fhrs_id == fhrs_id).\
                    delete()
        self.assertIsNone(Session.query(FHRSEstablishment).get(fhrs_id))
        Session.close()


    def test_add_establishments_no_table(self):
        """If establishments table doesn't exist, RuntimeError raised"""

        DeclarativeBase.metadata.drop_all(bind=self.connection)
        with self.assertRaises(RuntimeError):
            self.helper_replace_establishments(self.auth, [self.est])


    def test_add_establishments_wrong_argument(self):
        """Bad argument raises TypeError"""

        # authority argument
        with self.assertRaises(TypeError):
            self.helper_replace_establishments(1, [self.est])

        # establishments argument
        with self.assertRaises(TypeError):
            # not a list
            self.helper_replace_establishments(self.auth, self.est)
        with self.assertRaises(TypeError):
            # wrong type in list
            self.helper_replace_establishments(self.auth, [1, 2, 3])


    def test_commit_establishment_with_nulls(self):
        """Committing establishment with nulls raises IntegrityError

        Null FHRS ID etc. should be caught by validator when calling
        parse_xml_establishments though.
        """

        # can't use self.est because already has a value and the
        # validator won't let us set it back to None
        null_est = FHRSEstablishment()
        trap = StringIO()
        with self.assertRaises(IntegrityError):
            # trap error message
            with redirect_stderr(trap):
                self.helper_replace_establishments(self.auth, [null_est])
        trap.close()


    def test_handle_fhrs_id_duplicate_in_session(self):
        """Duplicate FHRS IDs in session produces warning"""

        second_est = deepcopy(self.est)
        establishments = [self.est, second_est]
        # add both establishments
        with self.assertLogs(level="DEBUG"): # from session_scope
            with session_scope():
                with self.assertLogs(level="WARNING"):
                    fetch_fhrs.replace_establishments_for_authority_in_session(
                        self.auth, establishments)
        # check that exactly one is added
        self.assertEqual(Session.query(FHRSEstablishment).count(), 1)
        Session.close()


    def test_handle_fhrs_id_duplicate_in_database(self):
        """Duplicate FHRS ID in different authority produces warning"""

        second_est = deepcopy(self.est)

        # add one establishment
        self.helper_replace_establishments(self.auth, [self.est])
        self.assertEqual(Session.query(FHRSEstablishment).count(), 1)

        # add a second authority with not null columns set
        second_auth = FHRSAuthority(
            code=789,
            name="Second Authority",
            region_name="Authority Region",
            xml_url="http://ratings.food.gov.uk/OpenDataFiles/FHRS760en-GB.xml")
        Session.add(second_auth)
        Session.commit()

        # try adding second establishment with same FHRS ID in new authority
        auth = Session.query(FHRSAuthority).get(789)
        with self.assertLogs(level="DEBUG"): # from session_scope
            with session_scope():
                with self.assertLogs(level="WARNING"):
                    fetch_fhrs.replace_establishments_for_authority_in_session(
                        auth, [second_est])

        # check that exactly one is present
        self.assertEqual(Session.query(FHRSEstablishment).count(), 1)
        Session.close()
