"""Functions relating to OSM endpoint for Flask API"""

from fhodot.models.osm import OSMObject


def get_selected_osm_properties(osm_object):
    """Get selected properties of an OSM object"""

    assert isinstance(osm_object, OSMObject)

    bad_fhrs_ids_string = ""
    if not osm_object.fhrs_ids_string_valid:
        bad_fhrs_ids_string = osm_object.fhrs_ids_string

    return {"name": osm_object.name,
            "osmIDByType": osm_object.osm_id_by_type,
            "osmType": osm_object.osm_type,
            "postcode": osm_object.addr_postcode,
            "notPostcode": osm_object.not_addr_postcode,
            "badFHRSIDsString": bad_fhrs_ids_string,
            "numMatchesSamePostcodes":
                osm_object.num_matches_same_postcodes,
            "numMatchesDifferentPostcodes":
                osm_object.num_matches_different_postcodes,
            "numMismatchedFHRSIDs":
                osm_object.num_mismatched_fhrs_ids}


def get_fhrs_mappings(osm_object, include_distance=False,
                      include_location=False):
    """Get FHRS mappings for an OSM object"""

    assert isinstance(osm_object, OSMObject)

    results = []
    for mapping in osm_object.fhrs_mappings:
        result = {"fhrsID" : mapping.fhrs_id,
                  "postcodesMatch": mapping.postcodes_match}
        if include_distance:
            result["distance"] = mapping.distance
        establishment = mapping.fhrs_establishment
        if establishment:
            result["fhrsEstablishment"] = {
                "name": establishment.name,
                "postcode": establishment.postcode,
                "postcodeOriginal": establishment.postcode_original,
                "ratingDate": str(establishment.rating_date)}
            if include_location:
                result["fhrsEstablishment"]["lat"] = (
                    establishment.lat)
                result["fhrsEstablishment"]["lon"] = (
                    establishment.lon)
        results.append(result)

    return results
