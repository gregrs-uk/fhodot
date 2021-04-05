"""Functions to suggest matching FHRS establishments for an OSM object"""

from collections import defaultdict
from itertools import chain
from re import sub

from fuzzywuzzy.fuzz import token_set_ratio
from geoalchemy2.functions import ST_DWithin, ST_Intersects
from sqlalchemy import not_
from sqlalchemy.orm import joinedload, Load
from unidecode import unidecode

from fhodot.database import Session
from fhodot.models import FHRSEstablishment, OSMObject
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


def standardised_names_match(osm_name_std, fhrs_name_std, ratio_threshold=90,
                             return_ratio=False):
    """Test whether two standardised names are a close match

    Uses fuzzywuzzy's token set ratio method for fuzzy string matching.
    Returns True if the names are sufficiently matched and False
    otherwise.

    ratio_threshold (0-100) defines how similar the names have to be to
    return True. Its default has been chosen by looking at examples.

    If return_ratio is True, the function will return the token set
    ratio itself rather than True if it is >= ratio_threshold, which can
    be used for analysis purposes.
    """
    # token_set_ratio checks for equality first so no need to here
    # strings already standardised, so full_process not required
    ratio = token_set_ratio(osm_name_std, fhrs_name_std, full_process=False)
    if ratio >= ratio_threshold:
        return ratio if return_ratio else True
    return False


def get_nearby_combinations(bbox, distance=160):
    """Get nearby combinations of OSM objects and FHRS establishments

    Only fetches names because it's quicker to fetch full info for only
    matched objects later. The default distance of 160m was at
    approximately the 90th percentile when existing matches were
    analysed. Returns query which can be iterated over.
    """

    envelope = get_envelope(bbox)

    # pylint: disable=no-member
    # cartesian product i.e. every combination
    return Session.query(OSMObject, FHRSEstablishment).\
        filter(
            # OSM within envelope
            ST_Intersects(OSMObject.location, envelope),
            # FHRS not already matched successfully
            not_(FHRSEstablishment.osm_mappings.any()),
            # OSM and FHRS within specified distance
            ST_DWithin(OSMObject.location, FHRSEstablishment.location,
                       distance, use_spheroid=False)).\
        options(Load(OSMObject).load_only("name"),
                Load(FHRSEstablishment).load_only("name"))


def get_suggested_matches_by_osm_id(bbox):
    """Get suggested matches for the supplied bounding box

    Returns a dict with OSM IDs as keys and lists of FHRS establishments
    as values.
    """

    # key: OSM object, value: list of nearby FHRS establishments
    nearby_combinations_by_osm = defaultdict(list)
    for osm_object, fhrs_establishment in get_nearby_combinations(bbox):
        nearby_combinations_by_osm[osm_object].append(fhrs_establishment)

    # key: OSM ID, value: list of matching FHRS establishments
    matches_by_osm_id = defaultdict(list)
    fhrs_names_std = {} # to store FHRS names already standardised
    for osm_object, fhrs_establishments in nearby_combinations_by_osm.items():
        osm_name_std = standardise_name(osm_object.name)
        for fhrs_establishment in fhrs_establishments:
            if fhrs_establishment.fhrs_id in fhrs_names_std:
                fhrs_name_std = fhrs_names_std[fhrs_establishment.fhrs_id]
            else:
                fhrs_name_std = standardise_name(fhrs_establishment.name)
                fhrs_names_std[fhrs_establishment.fhrs_id] = fhrs_name_std
            if standardised_names_match(osm_name_std, fhrs_name_std):
                matches_by_osm_id[osm_object.osm_id_single_space].append(
                    fhrs_establishment)

    return matches_by_osm_id


def get_full_osm_objects_query(suggested_matches_by_osm_id):
    """Get full OSM objects for the given suggested matches

    Returns a query that can be iterated over.
    """
    osm_ids = suggested_matches_by_osm_id.keys()
    return Session.query(OSMObject).\
        filter(OSMObject.osm_id_single_space.in_(osm_ids)).\
        options(joinedload("fhrs_mappings").joinedload("fhrs_establishment"))


def get_full_fhrs_establishments_dict(suggested_matches_by_osm_id):
    """Get full FHRS establishments for the given suggested matches

    Returns a dict of FHRS establishments with FHRS IDs as keys.
    """
    fhrs_ids = [fhrs_est.fhrs_id for fhrs_est
                in chain.from_iterable(suggested_matches_by_osm_id.values())]
    fhrs_establishments_full = Session.query(FHRSEstablishment).\
        filter(FHRSEstablishment.fhrs_id.in_(fhrs_ids))
    return {fhrs_est.fhrs_id : fhrs_est for fhrs_est
            in fhrs_establishments_full}
