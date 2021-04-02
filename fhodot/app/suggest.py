"""Functions to suggest matching FHRS establishments for an OSM object"""

from collections import defaultdict
from re import sub

from fuzzywuzzy.fuzz import token_set_ratio
from geoalchemy2.functions import ST_DWithin, ST_Intersects
from sqlalchemy import not_
from unidecode import unidecode

from fhodot.database import Session
from fhodot.models.fhrs import FHRSEstablishment
from fhodot.models.osm import OSMObject
from fhodot.app.utils import get_envelope


def standardise_name(string):
    """Standardise a name string to improve results of fuzzy matching

    N.B. different from fhodot.standardise.standardise function, which
    is intended for generic standardisation of place/street names
    """
    string = unidecode(string) # unaccent
    string = string.lower()
    # convert various characters to something specific
    string = sub("[./-]", " ", string)
    string = sub(r" ?& ?| ?\+ ?", " and ", string)
    string = sub(" ?@ ?", " at ", string)
    # remove any other extraneous characters
    string = sub(r"[^a-z0-9\s]", "", string)
    # remove 'ltd' (\b is a word boundary)
    string = sub(r"\bltd\b", "", string)
    # normalise whitespace
    string = string.strip()
    string = sub(r"\s+", " ", string)
    return string


def names_match(osm_object, fhrs_establishment, ratio_threshold=90,
                return_ratio=False):
    """Test whether the names of the two features are a close match

    Uses fuzzywuzzy's token set ratio method for fuzzy string matching.
    Returns True if the names are sufficiently matched and False
    otherwise.

    ratio_threshold (0-100) defines how similar the names have to be to
    return True. Its default has been chosen by looking at examples.

    If return_ratio is True, the function will return the token set
    ratio itself rather than True if it is >= ratio_threshold, which can
    be used for analysis purposes.
    """

    assert isinstance(osm_object, OSMObject)
    assert isinstance(fhrs_establishment, FHRSEstablishment)
    osm_name_std = standardise_name(osm_object.name)
    fhrs_name_std = standardise_name(fhrs_establishment.name)

    # token_set_ratio checks for equality first so no need to here
    # strings already standardised, so full_process not required
    ratio = token_set_ratio(osm_name_std, fhrs_name_std, full_process=False)
    if ratio >= ratio_threshold:
        return ratio if return_ratio else True
    return False


def get_suggested_matches_by_osm(bbox):
    """Get suggested matches for the supplied bounding box

    Returns a dict with OSM objects as keys and lists of FHRS
    establishments as values.
    """

    envelope = get_envelope(bbox)
    # cartesian product i.e. every combination
    nearby_combinations = Session.query(OSMObject, FHRSEstablishment).\
        filter(
            # OSM within envelope
            ST_Intersects(OSMObject.location, envelope),
            # FHRS not already matched successfully
            not_(FHRSEstablishment.osm_mappings.any()),
            # OSM and FHRS within 250m of each other
            ST_DWithin(OSMObject.location, FHRSEstablishment.location,
                       250, use_spheroid=False))

    # may have same OSM object listed multiple times
    matching_combinations = []
    for osm_object, fhrs_establishment in nearby_combinations: # iterate query
        if names_match(osm_object, fhrs_establishment):
            matching_combinations.append(
                {"osm_object": osm_object,
                 "fhrs_establishment": fhrs_establishment})

    # key: OSM object, value: list of matching FHRS establishments
    matches_by_osm = defaultdict(list)
    for match in matching_combinations:
        matches_by_osm[match["osm_object"]].append(match["fhrs_establishment"])

    return matches_by_osm
