"""Functions relating to FHRS endpoint for Flask API"""

from geoalchemy2.functions import ST_Intersects

from fhodot.app.utils import get_envelope
from fhodot.database import Session
from fhodot.models import (FHRSAuthority, FHRSEstablishment,
                           LocalAuthorityDistrict)


def get_selected_fhrs_properties(fhrs_establishment):
    """Get selected properties of an FHRS establishment"""

    assert isinstance(fhrs_establishment, FHRSEstablishment)

    return {"name": fhrs_establishment.name,
            "fhrsID": fhrs_establishment.fhrs_id,
            "postcode": fhrs_establishment.postcode,
            "postcodeOriginal": fhrs_establishment.postcode_original,
            "ratingDate": str(fhrs_establishment.rating_date),
            "numMatchesSamePostcodes":
                fhrs_establishment.num_matches_same_postcodes,
            "numMatchesDifferentPostcodes":
                fhrs_establishment.num_matches_different_postcodes}


def get_osm_mappings(fhrs_establishment, include_distance=False):
    """Get OSM mappings for an FHRS establishment"""

    assert isinstance(fhrs_establishment, FHRSEstablishment)

    results = []
    for mapping in fhrs_establishment.osm_mappings:
        result = {"postcodesMatch": mapping.postcodes_match}
        if include_distance:
            result["distance"] = mapping.distance
        if mapping.osm_object:
            result["osmObject"] = {
                "name": mapping.osm_object.name,
                "osmType": mapping.osm_object.osm_type,
                "osmIDByType": mapping.osm_object.osm_id_by_type,
                "postcode": mapping.osm_object.addr_postcode,
                "notPostcode": mapping.osm_object.not_addr_postcode}
        results.append(result)

    return results


def query_fhrs_without_location_for_districts_in_bbox(bbox):
    """Query for establishments without location for districts in bbox

    Returns FHRS establishments without a location for any districts
    that intersect the supplied bounding box.

    Returns a query object which can be iterated over. N.B. doesn't
    eager load relationships so you may want to use joinedload if you
    plan to access related objects.
    """
    envelope = get_envelope(bbox)
    return Session.query(FHRSEstablishment).\
        join(FHRSAuthority).\
        join(LocalAuthorityDistrict).\
        filter(ST_Intersects(LocalAuthorityDistrict.boundary, envelope),
               FHRSEstablishment.location.is_(None)).\
        order_by(FHRSEstablishment.postcode, FHRSAuthority.name,
                 FHRSEstablishment.name)
