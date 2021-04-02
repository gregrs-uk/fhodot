"""Functions for parsing an FHRS address into OSM addr:* tags

For an overview of the process, see the parse_establishment_address
method. The main parsing logic happens in the classify_tokens method.

The following data is used for parsing: a list of counties from
Wikipedia, a list of post towns (by postcode area) from Wikipedia, and
the named roads and populated places from OS Open Names, queried from
the database.

The following tags are generated as appropriate: addr:floor, addr:unit,
addr:housename, addr:housenumber, addr:street, addr:hamlet,
addr:village, addr:suburb, addr:town, addr:city, addr:county. The post
town is tagged addr:city, whether or not this is actually a city.
Otherwise place types (hamlet, village, suburb, town and city) are
chosen based on the OS Open Names data.

Tokens that cannot be parsed or that would create duplicate tags are
tagged with fixme:addr:*.
"""

from itertools import chain, groupby
from os.path import abspath, dirname, join
from re import search

from sqlalchemy import or_

from fhodot.database import Session
from fhodot.models.fhrs import FHRSEstablishment
from fhodot.models.os_open_names import OSPlace, OSRoad
from fhodot.standardise import standardise


# relative path as can't rely on working directory in production
module_dir = dirname(abspath(__file__))
data_dir = join(module_dir, "parse_addresses_data")

# load and standardise counties, ignoring empty/comment lines
with open(join(data_dir, "counties.txt"), "r") as file:
    counties = [standardise(line) for line in file.read().splitlines()
                if line.strip() and not line.startswith("#")]

# load dict of standardised post towns by postcode area,
# ignoring empty/comment lines
with open(join(data_dir, "post_towns.txt"), "r") as file:
    lines = file.read().splitlines()
    post_towns_by_area = {}
    for line in lines:
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split("\t")
        assert len(fields) == 2
        post_towns_by_area[fields[0]] = [
            standardise(town) for town in fields[1].split(",")]

# store generator output as list to allow using more than once
all_post_towns = list(chain.from_iterable(post_towns_by_area.values()))

NUM_RANGE_PATTERN = "[0-9]+[A-Za-z]?( *[-–] *[0-9]+[A-Za-z]?)?"


def prepare_tokens(establishment):
    """Prepare tokens from establishment address"""

    if establishment.address_1 == establishment.name:
        establishment.address_1 = None

    tokens = [establishment.address_1, establishment.address_2,
              establishment.address_3, establishment.address_4]
    tokens = [token for token in tokens if token] # i.e. not empty
    # further split by commas
    tokens = chain.from_iterable([token.split(",") for token in tokens])
    tokens = [token.strip() for token in tokens]
    # remove any consecutive duplicates e.g. same post town & county
    tokens = [group[0] for group in groupby(tokens)]

    token_dicts = []
    for token in tokens:
        token_dicts.extend(split_number_and_create_dicts(token))
    return token_dicts


def split_number_and_create_dicts(token):
    """Return list of 1 or 2 dicts for token, with number/range split"""

    match = search(f"^({NUM_RANGE_PATTERN})( +.*)?$", token)
    if match: # number/range at start
        number_token = {"string": match.group(1), "tag": "number"}
        if match.lastindex == 3 and match.group(3).strip():
            # non-whitespace found after number/range
            remainder_token = {"string": match.group(3).strip(), "tag": None}
            return [number_token, remainder_token]
        return [number_token]
    # if not number/range at start
    return [{"string": token, "tag": None}]


def get_postcode_area(establishment):
    """Extract postcode area to use for filtering"""
    if not establishment.postcode:
        return None
    match = search("^[A-Z]{1,2}", establishment.postcode)
    assert match # validator function should prevent invalid postcodes
    postcode_area = match.group(0)
    if postcode_area in post_towns_by_area.keys():
        return postcode_area
    return False


def is_county(string):
    """Check whether a string matches the name of a county"""
    return standardise(string) in counties


def is_post_town(string, postcode_area):
    """Check whether a string matches the name of a post town

    Uses postcode area to narrow down search if possible.
    """
    if postcode_area:
        return standardise(string) in post_towns_by_area[postcode_area]
    return standardise(string) in all_post_towns


def get_os_object(string, model_class, postcode_area):
    """Get the first matching OS Open Names object

    Uses postcode area to narrow down search if possible.
    """
    string = standardise(string)
    if not string: # e.g. a number or number-range token
        return False

    query = Session.query(model_class)
    if postcode_area:
        query = query.filter(model_class.postcode_area == postcode_area)
    return query.filter(or_(model_class.name_1_std.like(string),
                            model_class.name_2_std.like(string))).first()


def get_place_tag(string, postcode_area):
    """Get place tag if string matches name of a place, otherwise False

    Uses postcode area to narrow down search if possible. N.B. OS Open
    Names data doesn't cover Northern Ireland.
    """

    os_place = get_os_object(string, OSPlace, postcode_area)
    if not os_place:
        return False

    if os_place.place_type == "Other Settlement":
        place_tag = "fixme:place"
    elif os_place.place_type == "Suburban Area":
        place_tag = "addr:suburb"
    else:
        # city, town, village, hamlet
        place_tag = "addr:" + os_place.place_type.lower()

    return place_tag


def is_road(string, postcode_area):
    """Check whether a string matches the name of a road

    Uses postcode area to narrow down search if possible. OS Open Names
    data doesn't cover Northern Ireland, so if postcode area is 'BT',
    looks for common road-name endings instead.
    """
    if postcode_area == "BT": # i.e. Northern Ireland
        # common final words from OS Open Names roads in Great Britain
        # (not Northern Ireland), accounting for approx. 68% of roads
        words = ["road", "close", "street", "lane", "avenue", "drive", "way"]
        pattern = " (" + "|".join(words) + ")$"
        if search(pattern, string.lower()):
            return True
        return False

    # within Great Britain
    if get_os_object(string, OSRoad, postcode_area):
        return True
    return False


def get_floor(string):
    """Return floor number from string, or False if not recognised

    If string ends with ' floor' but doesn't match a recognised pattern,
    return the string unchanged.
    """

    if "floor" not in string.lower():
        return False
    string = string.strip()

    match = search("^([0-9]+)(st|nd|rd|th) +floor$", string.lower())
    if match:
        return match.group(1)

    match = search("^floor +([0-9]+)$", string.lower())
    if match:
        return match.group(1)

    match = search("^(ground|first|second) +floors?$", string.lower())
    if match:
        num_equivalent = {"ground": "0", "first": "1", "second": "2"}
        return num_equivalent[match.group(1)]

    # failsafes in case string contains 'floor' but doesn't match above
    if search(" floor$", string.lower()):
        return string
    return False


def get_unit(string):
    """Return unit from string, or False if not recognised"""

    opening_pattern = "^(unit|flat)s? +"
    if not search(opening_pattern, string.lower()):
        return False
    string = string.strip()

    match = search(f"{opening_pattern}({NUM_RANGE_PATTERN})$", string.lower())
    if match:
        return match.group(2).upper()

    # starts with 'unit(s) ' or 'flat(s) ' but otherwise unmatched
    return string


def set_addr_tag_if_unique(token, tag, existing_tags, string=None):
    """If tag not in existing_tags, set token['tag'] to 'addr:{tag}'

    If string supplied, also set token['string'] to string.
    """

    tag = f"addr:{tag}"
    if tag in existing_tags:
        return token # unchanged

    token["tag"] = tag
    if string:
        token["string"] = string
    return token


def classify_tokens(tokens, postcode_area): # pylint:disable=too-many-branches
    """Add tags to a list of token dicts to classify the tokens"""

    tokens.reverse() # address in reverse order

    for token in tokens:
        # skip any number tokens, which can't be a city, county or place
        if token["tag"] == "number":
            continue

        string = token["string"]
        existing_tags = [token["tag"] for token in tokens]

        # There should be max 1 addr:city and addr:county. If token is
        # both county and post town (e.g. London), tag as addr:city.
        # N.B. if token recognised but relevant tag already exists,
        # token will still drop down to the next elif.
        if ("addr:city" not in existing_tags and
                is_post_town(string, postcode_area)):
            token["tag"] = "addr:city"
        elif "addr:county" not in existing_tags and is_county(string):
            token["tag"] = "addr:county"
        # there can be multiple tokens tagged as a place, but not same type
        else:
            place_tag = get_place_tag(string, postcode_area) # (or False)
            if place_tag and place_tag not in existing_tags:
                token["tag"] = place_tag

    tokens.reverse() # address back to normal order

    for token in tokens:
        # stop classifying once we find a place, post town or county
        if token["tag"] and token["tag"] != "number":
            break

        string = token["string"]
        existing_tags = [token["tag"] for token in tokens]

        # There should be max 1 addr:floor, addr:unit, addr:housenumber,
        # addr:street and housename. N.B. if a token is recognised, it
        # doesn't drop down to the next elif e.g. a number token won't
        # end up as an addr:street or an addr:housename
        floor_number = get_floor(string)
        unit_number = get_unit(string)
        if floor_number:
            token = set_addr_tag_if_unique(
                token, "floor", existing_tags, floor_number)
        elif unit_number:
            token = set_addr_tag_if_unique(
                token, "unit", existing_tags, unit_number)
        elif token["tag"] == "number":
            if "addr:housenumber" in existing_tags:
                token["tag"] = None
            else:
                token["tag"] = "addr:housenumber"
        elif is_road(string, postcode_area):
            token = set_addr_tag_if_unique(token, "street", existing_tags)
        else:
            token = set_addr_tag_if_unique(token, "housename", existing_tags)

    return tokens


def correct_all_caps(token):
    """If token's string is all caps, correct to title case"""
    if token["string"] == token["string"].upper(): # i.e. all caps
        token["string"] = token["string"].title()
    return token


def set_tags_for_unparsed_tokens(tokens):
    """Set tags for tokens that were not successfully parsed

    The first unparsed token will be tagged with fixme:addr:1, the
    second with fixme:addr:2, and so on.
    """
    i = 1
    for token in tokens:
        if not token["tag"]:
            token["tag"] = f"fixme:addr:{i}"
            i += 1
    return tokens


def parse_establishment_address(establishment):
    """Parse an FHRS establishment's address into OSM addr:* tags"""

    assert isinstance(establishment, FHRSEstablishment)

    postcode_area = get_postcode_area(establishment)
    tokens = prepare_tokens(establishment)
    tokens = classify_tokens(tokens, postcode_area)
    tokens = [correct_all_caps(token) for token in tokens]
    tokens = set_tags_for_unparsed_tokens(tokens)
    assert all([token["tag"] for token in tokens])

    return tokens
