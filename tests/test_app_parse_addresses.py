"""Unit tests for most fhodot.app.parse_addresses functions"""

from unittest import TestCase

from fhodot.app import parse_addresses
from fhodot.database import Session
from fhodot.models.fhrs import FHRSEstablishment
from fhodot.models.os_open_names import OSPlace


# Some of these tests rely on external data. Plain assert statements
# test assumptions about the data that are required for the tests to
# make sense, rather than testing the functions themselves


def helper_create_dict(token, tag=None):
    """Helper function to create a token dict"""
    value = {"string": token, "tag": tag}
    return value


class TestPrepareTokens(TestCase):
    """Test prepare_tokens and split_number_and_create_dicts"""

    def setUp(self):
        self.est = FHRSEstablishment()


    def test_simple_tokenisation(self):
        """Each address line becomes a token"""

        self.est.address_1 = "First line"
        self.est.address_2 = "Second line"
        self.est.address_3 = "Third line"
        self.est.address_4 = "Fourth line"

        tokens = parse_addresses.prepare_tokens(self.est)
        self.assertEqual(len(tokens), 4)


    def test_name_equals_first_line(self):
        """First line removed if same as establishment name"""

        self.est.name = "Establishment name"
        self.est.address_1 = "Establishment name"
        self.est.address_2 = "Second line"

        tokens = parse_addresses.prepare_tokens(self.est)
        self.assertEqual(len(tokens), 1)


    def test_empty_lines(self):
        """Empty lines removed"""

        self.est.address_1 = "First line"
        self.est.address_2 = ""
        self.est.address_3 = None
        self.est.address_4 = "Fourth line"

        tokens = parse_addresses.prepare_tokens(self.est)
        self.assertEqual(len(tokens), 2)


    def test_split_comma(self):
        """Lines split into multiple tokens by commas"""

        self.est.address_1 = "First token, Second token, Third token"

        tokens = parse_addresses.prepare_tokens(self.est)
        self.assertEqual(len(tokens), 3)
        self.assertEqual(tokens[1], helper_create_dict("Second token"))


    def test_strip_whitespace(self):
        """Spaces stripped from tokens"""

        self.est.address_1 = "  One  "
        self.est.address_2 = "  Two  ,  Three  "

        tokens = parse_addresses.prepare_tokens(self.est)
        self.assertEqual(tokens[0]["string"], "One")
        self.assertEqual(tokens[1]["string"], "Two")
        self.assertEqual(tokens[2]["string"], "Three")


    def test_remove_consecutive_duplicates(self):
        """Consecutive duplicate lines will be removed"""

        self.est.address_1 = "One"
        self.est.address_2 = "Two"
        self.est.address_3 = "Two"
        self.est.address_4 = "Three"

        tokens = parse_addresses.prepare_tokens(self.est)
        self.assertEqual(len(tokens), 3)
        self.assertEqual(tokens[2]["string"], "Three") # i.e. third token


    def test_keep_non_consecutive_duplicates(self):
        """Non-consecutive duplicate lines will be kept"""

        self.est.address_1 = "One"
        self.est.address_2 = "Two"
        self.est.address_3 = "One"

        tokens = parse_addresses.prepare_tokens(self.est)
        self.assertEqual(len(tokens), 3)
        self.assertEqual(tokens[2]["string"], "One") # i.e. third token


    def test_number(self):
        """Leading number split and tagged"""

        self.est.address_1 = "123 High Street"

        tokens = parse_addresses.prepare_tokens(self.est)
        self.assertEqual(tokens[0], helper_create_dict("123", "number"))
        self.assertEqual(tokens[1], helper_create_dict("High Street"))


    def test_number_only(self):
        """Number only creates a single token with number tag"""

        self.est.address_1 = "123"

        tokens = parse_addresses.prepare_tokens(self.est)
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0], helper_create_dict("123", "number"))


    def test_number_range(self):
        """Leading number range split and tagged"""

        self.est.address_1 = "1-3 High Street"

        tokens = parse_addresses.prepare_tokens(self.est)
        self.assertEqual(tokens[0], helper_create_dict("1-3", "number"))
        self.assertEqual(tokens[1], helper_create_dict("High Street"))


    def test_number_range_space(self):
        """Leading number range with spaces split and tagged"""

        self.est.address_1 = "1 - 3 High Street"

        tokens = parse_addresses.prepare_tokens(self.est)
        self.assertEqual(tokens[0], helper_create_dict("1 - 3", "number"))
        self.assertEqual(tokens[1], helper_create_dict("High Street"))


    def test_number_letter_range(self):
        """Leading number range with letters split and tagged"""

        self.est.address_1 = "1A-1B High Street"

        tokens = parse_addresses.prepare_tokens(self.est)
        self.assertEqual(tokens[0], helper_create_dict("1A-1B", "number"))
        self.assertEqual(tokens[1], helper_create_dict("High Street"))


    def test_number_letter_range_space(self):
        """Number/letter range with spaces split and tagged"""

        self.est.address_1 = "1A - 1B High Street"

        tokens = parse_addresses.prepare_tokens(self.est)
        self.assertEqual(tokens[0], helper_create_dict("1A - 1B", "number"))
        self.assertEqual(tokens[1], helper_create_dict("High Street"))


    def test_floor(self):
        """Token representing numbered floor not split"""

        self.est.address_1 = "1st Floor"

        tokens = parse_addresses.prepare_tokens(self.est)
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0], helper_create_dict("1st Floor"))


class TestGetPostcodeArea(TestCase):
    """Test get_postcode_area"""

    def setUp(self):
        self.est = FHRSEstablishment()
        self.valid_areas = parse_addresses.post_towns_by_area.keys()


    def test_no_postcode(self):
        """If establishment has no postcode, returns None"""
        assert self.est.postcode is None
        self.assertIsNone(parse_addresses.get_postcode_area(self.est))


    def test_invalid_area(self):
        """If postcode area is unrecognised, returns False"""
        assert "XX" not in self.valid_areas
        self.est.postcode = "XX12 3AB"
        self.assertEqual(parse_addresses.get_postcode_area(self.est), False)


    def test_valid_one_letter(self):
        """If one-letter postcode area is valid, returns letter"""
        assert "B" in self.valid_areas
        self.est.postcode = "B12 3AB"
        self.assertEqual(parse_addresses.get_postcode_area(self.est), "B")


    def test_valid_two_letters(self):
        """If two-letter postcode area is valid, returns letters"""
        assert "AB" in self.valid_areas
        self.est.postcode = "AB12 3AB"
        self.assertEqual(parse_addresses.get_postcode_area(self.est), "AB")


class TestGetPlaceTag(TestCase):
    """Test get_place_tag

    N.B. These tests depend upon the OS Open Names data.
    """

    def test_place_types(self):
        """Check that all place_type values in database are expected"""
        result = Session.query(OSPlace.place_type).\
            distinct(OSPlace.place_type).\
            all()
        db_types = [row[0] for row in result]
        expected_types = ["City", "Town", "Suburban Area", "Village", "Hamlet",
                          "Other Settlement"]
        self.assertTrue(
            all([db_type in expected_types for db_type in db_types]))


    def helper_get_example_place(self, place_type): # pylint:disable=no-self-use
        """Helper function to get an example place of type place_type"""
        place = Session.query(OSPlace).\
            filter(OSPlace.place_type == place_type).\
            first()
        assert place.name_1
        assert place.postcode_area
        return place


    def test_other_settlement(self):
        """'Other Settlement' should return 'fixme:place'"""
        place = self.helper_get_example_place("Other Settlement")
        place_tag = parse_addresses.get_place_tag(place.name_1.upper(),
                                                  place.postcode_area)
        self.assertEqual(place_tag, "fixme:place")


    def test_suburban_area(self):
        """'Suburban Area' should return 'addr:suburb'"""
        place = self.helper_get_example_place("Suburban Area")
        place_tag = parse_addresses.get_place_tag(place.name_1.upper(),
                                                  place.postcode_area)
        self.assertEqual(place_tag, "addr:suburb")


    def test_other_place_types(self):
        """Most place types should return 'addr:*'"""
        place = self.helper_get_example_place("Town")
        place_tag = parse_addresses.get_place_tag(place.name_1.upper(),
                                                  place.postcode_area)
        self.assertEqual(place_tag, "addr:town")


    def test_valid_no_postcode_area(self):
        """Valid place with no area supplied returns expected tag"""
        place = self.helper_get_example_place("City")
        place_tag = parse_addresses.get_place_tag(place.name_1.upper(), None)
        self.assertEqual(place_tag, "addr:city")


    def test_valid_outside_postcode_area(self):
        """If valid place outside postcode area, returns False"""
        self.assertFalse(
            parse_addresses.get_place_tag("Edinburgh", "B"))


    def test_invalid(self):
        """If invalid place, returns False"""
        self.assertFalse(parse_addresses.get_place_tag("Not a place", None))


    def test_standardises_to_empty(self):
        """If string standardises to an empty string, returns False"""
        self.assertFalse(parse_addresses.get_place_tag("123", None))


class TestIsCounty(TestCase):
    """Test is_county"""

    def test_valid_county(self):
        """If valid county, returns True"""
        assert "worcestershire" in parse_addresses.counties
        self.assertTrue(parse_addresses.is_county("WORCESTERSHIRE"))


    def test_invalid_county(self):
        """If invalid county, returns False"""
        assert "fakeshire" not in parse_addresses.counties
        self.assertFalse(parse_addresses.is_county("Fakeshire"))


class TestIsPostTown(TestCase):
    """Test is_post_town"""

    def setUp(self):
        self.est = FHRSEstablishment()
        self.valid_areas = parse_addresses.post_towns_by_area.keys()


    def test_valid(self):
        """If valid post town in postcode area, returns True"""
        assert "birmingham" in parse_addresses.post_towns_by_area["B"]
        self.assertTrue(parse_addresses.is_post_town("Birmingham", "B"))


    def test_valid_no_postcode_area(self):
        """If valid post town and no area supplied, returns True"""
        assert "birmingham" in parse_addresses.all_post_towns
        self.assertTrue(parse_addresses.is_post_town("Birmingham", None))


    def test_valid_outside_postcode_area(self):
        """If valid post town outside postcode area, returns False"""
        assert "birmingham" in parse_addresses.post_towns_by_area["B"]
        assert "birmingham" not in parse_addresses.post_towns_by_area["E"]
        self.assertFalse(parse_addresses.is_post_town("Birmingham", "E"))


    def test_invalid(self):
        """If invalid post town, returns False"""
        assert "denver" not in parse_addresses.all_post_towns
        self.assertFalse(parse_addresses.is_post_town("Denver", None))


class TestIsRoad(TestCase):
    """Test is_road"""

    def test_northern_ireland_valid(self):
        """If postcode area 'BT' and string matches, returns True"""
        self.assertTrue(parse_addresses.is_road("High Street", "BT"))


    def test_northern_ireland_invalid(self):
        """If postcode area 'BT' and string doesn't match, returns False"""
        self.assertFalse(parse_addresses.is_road("Belfast", "BT"))


    def test_gb_valid(self):
        """In GB, if string matches road name, returns True"""
        self.assertTrue(parse_addresses.is_road("Oxford Street", "W"))


    def test_gb_invalid(self):
        """In GB, if string doesn't match road name, returns False"""
        self.assertFalse(parse_addresses.is_road("Not a road", "B"))


class TestGetFloor(TestCase):
    """Test get_floor"""

    def test_not_floor(self):
        """If standardised string doesn't contain floor, returns False"""
        self.assertFalse(parse_addresses.get_floor("123 High Street"))


    def test_nth_floor(self):
        """String with ordinal floor returns floor number string"""
        self.assertEqual(parse_addresses.get_floor("1st Floor"), "1")
        self.assertEqual(parse_addresses.get_floor("22nd Floor"), "22")
        self.assertEqual(parse_addresses.get_floor("33rd Floor"), "33")
        self.assertEqual(parse_addresses.get_floor("44th Floor"), "44")


    def test_floor_n(self):
        """String with 'floor n' returns floor number string"""
        self.assertEqual(parse_addresses.get_floor("Floor 1"), "1")
        self.assertEqual(parse_addresses.get_floor("Floor 22"), "22")
        self.assertEqual(parse_addresses.get_floor("Floor 33"), "33")
        self.assertEqual(parse_addresses.get_floor("Floor 44"), "44")


    def test_word_nth_floor(self):
        """String with ground/first/second floor returns number string"""
        self.assertEqual(parse_addresses.get_floor("Ground Floor"), "0")
        self.assertEqual(parse_addresses.get_floor("First Floor"), "1")
        self.assertEqual(parse_addresses.get_floor("Second Floor"), "2")


    def test_unrecognised_ends_floor(self):
        """String ending 'floor' but otherwise unmatched returned as is"""
        string = "First and Second Floor"
        self.assertEqual(parse_addresses.get_floor(string), string)


    def test_unrecognised_contains_floor(self):
        """String containing 'floor' but unmatched returns False"""
        self.assertFalse(parse_addresses.get_floor("Bob's flooring"))


class TestGetUnit(TestCase):
    """Test get_unit"""

    def test_not_unit(self):
        """If standardised string not a unit, returns False"""
        self.assertFalse(parse_addresses.get_unit("123 High Street"))


    def test_number_letter_range(self):
        """Return unit number/letter range"""
        self.assertEqual(parse_addresses.get_unit("Units 1A - 2B"), "1A - 2B")


    def test_unrecognised_unit(self):
        """Return string with unrecognised unit number as is"""
        string = "Unit 1 and Unit 2"
        self.assertEqual(parse_addresses.get_unit(string), string)


class TestSetAddrTagIfUnique(TestCase):
    """Test set_addr_tag_if_unique"""

    def setUp(self):
        self.existing_tags = ["addr:housename"]
        self.token = {"string": "Token string", "tag": None}


    def test_tag_in_existing_tags(self):
        """If tag in existing tags, don't set token tag"""
        processed_token = parse_addresses.set_addr_tag_if_unique(
            self.token, "housename", self.existing_tags)
        self.assertEqual(processed_token, self.token)


    def test_add_tag_no_string(self):
        """If tag not in existing tags, set token tag"""
        processed_token = parse_addresses.set_addr_tag_if_unique(
            self.token, "street", self.existing_tags)
        expected = {"string": self.token["string"], "tag": "addr:street"}
        self.assertEqual(processed_token, expected)


    def test_add_tag_with_string(self):
        """Set token tag and string"""
        new_string = "New string"
        processed_token = parse_addresses.set_addr_tag_if_unique(
            self.token, "street", self.existing_tags, new_string)
        expected = {"string": new_string, "tag": "addr:street"}
        self.assertEqual(processed_token, expected)


class TestCorrectAllCaps(TestCase):
    """Test correct_all_caps"""

    def test_needs_correction(self):
        """If token string all caps, returns with string in title case"""
        original = helper_create_dict("WEST MIDLANDS")
        expected = helper_create_dict("West Midlands")
        self.assertEqual(parse_addresses.correct_all_caps(original), expected)


    def test_no_correction_required(self):
        """If token string not all caps, returns original token"""
        token = helper_create_dict("West Midlands")
        self.assertEqual(parse_addresses.correct_all_caps(token), token)


class TestSetTagsForUnparsedTokens(TestCase):
    """Test set_tags_for_unparsed_tokens"""

    def test_two_unparsed_tokens(self):
        """The unparsed tokens are tagged fixme:addr:1 and 2"""
        tokens = [helper_create_dict("One", "addr:housenumber"),
                  helper_create_dict("Two"),
                  helper_create_dict("Three", "addr:city"),
                  helper_create_dict("Four")]
        expected = tokens
        expected[1]["tag"] = "fixme:addr:1"
        expected[3]["tag"] = "fixme:addr:2"
        processed_tokens = parse_addresses.set_tags_for_unparsed_tokens(tokens)
        self.assertEqual(processed_tokens, expected)
