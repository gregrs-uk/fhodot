"""Test parsing example addresses using fhodot.app.parse_addresses"""

from unittest import TestCase

from fhodot.app import parse_addresses
from fhodot.database import Session
from fhodot.models.fhrs import FHRSEstablishment
from fhodot.models.os_open_names import OSRoad, OSPlace


# These tests rely on external data. Plain assert statements test
# assumptions about the data that are required for the tests to make
# sense, rather than testing the functions themselves


def helper_assert_road_exists(name, postcode_area):
    """Test assumption that road exists in OS Open Names

    This can be used to ensure that subsequent tests make sense.
    """
    assert Session.query(OSRoad).\
        filter(OSRoad.name_1 == name,
               OSRoad.postcode_area == postcode_area).\
        first() # pylint:disable=comparison-with-callable


def helper_assert_place_exists(name, postcode_area, place_type):
    """Test assumption that place exists in OS Open Names

    This can be used to ensure that subsequent tests make sense.
    """
    # pylint:disable=comparison-with-callable
    assert Session.query(OSPlace).\
        filter(OSPlace.name_1 == name,
               OSPlace.postcode_area == postcode_area,
               OSPlace.place_type == place_type).\
        first()


def helper_assert_post_town_exists(name, postcode_area):
    """Test assumption that post town exists

    This can be used to ensure that subsequent tests make sense.
    """
    assert name.lower() in parse_addresses.post_towns_by_area[postcode_area]


class TestParseEstablishmentAddress(TestCase):
    """Test fhodot.app.parse_establishment_address"""

    def helper_parse_and_check_tags(self, address, postcode, expected_tags):
        """Test whether tags from parsed address match expected_tags

        Return parsed address to allow any further checks.
        """

        assert isinstance(address, list) and len(address) <= 4
        assert isinstance(expected_tags, list)

        est = FHRSEstablishment()
        # set establishment address_* from list
        for (address_line, index) in zip(address, range(1, 5)):
            setattr(est, f"address_{index}", address_line)
        est.postcode = postcode

        parsed = parse_addresses.parse_establishment_address(est)
        self.assertEqual([token["tag"] for token in parsed], expected_tags)
        return parsed


    def test_most_tags(self):
        """Long but valid address using most addr:* tags"""
        helper_assert_road_exists("The Green", "CV")
        helper_assert_place_exists("Bilton", "CV", "Suburban Area")
        helper_assert_post_town_exists("Rugby", "CV")
        self.helper_parse_and_check_tags(
            ["Floor 1, Unit 2A, Building Name, 123 The Green",
             "Bilton", "Rugby", "Warwickshire"],
            "CV21",
            ["addr:floor", "addr:unit", "addr:housename", "addr:housenumber",
             "addr:street", "addr:suburb", "addr:city", "addr:county"])


    def test_northern_ireland(self):
        """Address in Northern Ireland"""
        helper_assert_post_town_exists("Belfast", "BT")
        self.helper_parse_and_check_tags(
            ["123 High Street", "Belfast"],
            "BT1 1AA",
            ["addr:housenumber", "addr:street", "addr:city"])


    def test_num_street_post_town(self):
        """Valid number, street and post town"""
        helper_assert_road_exists("Oxford Street", "W")
        helper_assert_post_town_exists("London", "W")
        self.helper_parse_and_check_tags(
            ["123 Oxford Street", "London"],
            "W1A 1AA",
            ["addr:housenumber", "addr:street", "addr:city"])


    def test_house_name_street_post_town(self):
        """Valid house name, street and post town"""
        helper_assert_road_exists("The Mall", "SW")
        helper_assert_post_town_exists("London", "SW")
        self.helper_parse_and_check_tags(
            ["Buckingham Palace", "The Mall", "London"],
            "SW1A 1AA",
            ["addr:housename", "addr:street", "addr:city"])


    def test_house_name_num_street_post_town(self):
        """Valid house name, number, street and post town"""
        helper_assert_road_exists("Oxford Street", "W")
        helper_assert_post_town_exists("London", "W")
        self.helper_parse_and_check_tags(
            ["Imaginary House", "123 Oxford Street", "London"],
            "W1A 1AA",
            ["addr:housename", "addr:housenumber", "addr:street", "addr:city"])


    def test_street_post_town_unparsed(self):
        """Street, post town and unparsed token"""
        helper_assert_road_exists("East Bay", "PH")
        helper_assert_post_town_exists("Mallaig", "PH")
        self.helper_parse_and_check_tags(
            ["East Bay", "Mallaig", "Highland"],
            "PH41",
            ["addr:street", "addr:city", "fixme:addr:1"])


    def test_units_house_name_street_post_town(self):
        """Valid units, house name, street and post town"""
        helper_assert_road_exists("Oxford Street", "W")
        helper_assert_post_town_exists("London", "W")
        parsed = self.helper_parse_and_check_tags(
            ["Units 1-2", "Industrial Estate", "Oxford Street", "London"],
            "W1A 1AA",
            ["addr:unit", "addr:housename", "addr:street", "addr:city"])
        self.assertEqual(parsed[0]["string"], "1-2")


    def test_two_nums(self):
        """Address with two house numbers

        It's assumed that the first number is the desired house number.
        """
        helper_assert_road_exists("Oxford Street", "W")
        self.helper_parse_and_check_tags(
            ["123 Building Name", "123 Oxford Street"],
            "W1A 1AA",
            ["addr:housenumber", "addr:housename", "fixme:addr:1",
             "addr:street"])
