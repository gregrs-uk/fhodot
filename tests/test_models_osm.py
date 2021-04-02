"""Tests for fhodot.models.osm.OSMObject"""

from fhodot.database import Session
from fhodot.models.fhrs import FHRSAuthority, FHRSEstablishment
from fhodot.models.mapping import OSMFHRSMapping
from fhodot.models.osm import OSMObject
from tests import TestCaseWithReconfiguredSession


class TestOSMObjectNumMatches(TestCaseWithReconfiguredSession):
    """Test num_matches_(same/different)_postcodes"""

    def setUp(self):
        super().setUp()
        # test object with not null column set
        self.osm = OSMObject(osm_id_single_space=123)


    # inherits tearDown


    def test_no_matches(self):
        """Both functions return 0 if no matches"""
        Session.add(self.osm)
        self.assertEqual(self.osm.num_matches_same_postcodes, 0)
        self.assertEqual(self.osm.num_matches_different_postcodes, 0)


    def test_three_matches_two_with_same_postcode(self):
        """Returns number of FHRS matches with same/different postcode"""

        # test authority with not null columns set
        auth = FHRSAuthority(
            code=321,
            name="Authority Name",
            region_name="Authority Region",
            xml_url="http://ratings.food.gov.uk/OpenDataFiles/FHRS760en-GB.xml")
        Session.add(auth)
        Session.commit()

        fhrs_1 = FHRSEstablishment(fhrs_id=1, name="Establishment Name",
                                   postcode="AB12 3XY", authority=auth)
        fhrs_2 = FHRSEstablishment(fhrs_id=2, name="Establishment Name",
                                   postcode="AB12 3XY", authority=auth)
        fhrs_3 = FHRSEstablishment(fhrs_id=3, name="Establishment Name",
                                   postcode="XY12 3AB", authority=auth)
        fhrs_extra = FHRSEstablishment(fhrs_id=4, name="Establishment Name",
                                       postcode="AB12 3XY", authority=auth)
        self.osm.addr_postcode = "AB12 3XY"
        self.osm.fhrs_mappings = [
            OSMFHRSMapping(osm_object=self.osm, fhrs_establishment=fhrs_1),
            OSMFHRSMapping(osm_object=self.osm, fhrs_establishment=fhrs_2),
            OSMFHRSMapping(osm_object=self.osm, fhrs_establishment=fhrs_3)]
        Session.add_all([self.osm, fhrs_extra])

        self.assertEqual(self.osm.num_matches_same_postcodes, 2)
        self.assertEqual(self.osm.num_matches_different_postcodes, 1)


    def test_mismatch(self):
        """Returns number of mismatched FHRS IDs"""

        self.osm.fhrs_mappings = [
            OSMFHRSMapping(osm_object=self.osm, fhrs_id=1)]
        Session.add(self.osm)
        self.assertEqual(self.osm.num_mismatched_fhrs_ids, 1)


    def test_expressions(self):
        """Should raise NotImplementedError"""

        with self.assertRaises(NotImplementedError):
            Session.query(OSMObject).\
                filter(OSMObject.num_matches_same_postcodes == 1)

        with self.assertRaises(NotImplementedError):
            Session.query(OSMObject).\
                filter(OSMObject.num_matches_different_postcodes == 1)

        with self.assertRaises(NotImplementedError):
            Session.query(OSMObject).\
                filter(OSMObject.num_mismatched_fhrs_ids == 1)
