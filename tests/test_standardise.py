"""Tests for fhodot.standardise"""

from unittest import TestCase

from fhodot.standardise import standardise


class TestStandardise(TestCase):
    """Test function for standardising place/street names for lookup"""

    def test_nothing_required(self):
        """If no changes required, return string unchanged"""
        string = "hello"
        self.assertEqual(standardise(string), string)


    def test_unaccent(self):
        """Accented letters should be returned unaccented"""
        self.assertEqual(standardise("ÉÈÜéèü"), "eeueeu")


    def test_lowercase(self):
        """Letters should be converted to lowercase"""
        self.assertEqual(standardise("Aberdeen"), "aberdeen")


    def test_punctuation_to_space(self):
        """Certain punctuation should be converted to a space"""
        self.assertEqual(standardise("high st."), "high st")
        self.assertEqual(standardise("high/low street"), "high low street")
        self.assertEqual(standardise("Whip-Ma-Whop-Ma-Gate"),
                         "whip ma whop ma gate")


    def test_convert_and_punctuation(self):
        """Punctuation indicating 'and' should be converted to 'and'"""
        self.assertEqual(standardise("business & retail"),
                         "business and retail")
        self.assertEqual(standardise("business + retail"),
                         "business and retail")


    def test_remove_extraneous(self):
        """Any numbers or punctuation should be removed"""
        self.assertEqual(standardise("cotton's corner"), "cottons corner")
        self.assertEqual(standardise('"catering trailer"'), "catering trailer")
        self.assertEqual(standardise("ash grove (north)"), "ash grove north")
        self.assertEqual(standardise("london sw15"), "london sw")


    def test_normalise_whitespace(self):
        """Extra whitespace should be removed"""
        self.assertEqual(standardise("  a b c  "), "a b c")
        self.assertEqual(standardise("a   b   c"), "a b c")
        self.assertEqual(standardise("a. b. c."), "a b c")
