"""Functions to calculate statistics by authority/district"""


from datetime import date
from logging import debug, info

from sqlalchemy.orm import joinedload

from fhodot.database import Session
from fhodot.models import (FHRSAuthority, FHRSAuthorityStatistic,
                           LocalAuthorityDistrict,
                           OSMLocalAuthorityDistrictStatistic)


FHRS_STATUSES = ["matched_same_postcodes", "matched_different_postcodes",
                 "unmatched_with_location", "unmatched_without_location"]
OSM_STATUSES = ["matched_same_postcodes", "matched_different_postcodes",
                "mismatched", "unmatched"]


def get_fhrs_stats_for_authority(authority):
    """Return FHRS establishment statistics for FHRS authority"""

    statuses = []
    for establishment in authority.establishments:
        status = "unmatched_with_location"
        if establishment.osm_mappings:
            if any(not osm_mapping.postcodes_match
                   for osm_mapping in establishment.osm_mappings):
                status = "matched_different_postcodes"
            else:
                status = "matched_same_postcodes"
        elif not establishment.location:
            status = "unmatched_without_location"
        statuses.append(status)

    stats = []
    for status in FHRS_STATUSES:
        stats.append(
            FHRSAuthorityStatistic(
                authority_code=authority.code,
                date=date.today(),
                statistic=status,
                value=statuses.count(status)))

    return stats


def get_fhrs_stats_by_authority():
    """Return FHRS statistics by authority for all authorities"""

    query = Session.query(FHRSAuthority.code)
    authority_codes = [row[0] for row in query]

    authority_stats = []
    for authority_code in authority_codes:
        authority = Session.query(FHRSAuthority).\
            options(joinedload("establishments").joinedload("osm_mappings").
                    joinedload("osm_object")).\
            get(authority_code)

        debug(f"Calculating statistics for FHRS authority {authority.name}")
        authority_stats.extend(get_fhrs_stats_for_authority(authority))

    return authority_stats


def get_osm_stats_for_district(district):
    """Return OSM object statistics for local authority district

    district (LocalAuthorityDistrict)
    """

    statuses = []
    for osm_object in district.osm_objects:
        status = "unmatched"
        if osm_object.fhrs_mappings:
            if any(not fhrs_mapping.fhrs_establishment
                   for fhrs_mapping in osm_object.fhrs_mappings):
                status = "mismatched"
            elif any(not fhrs_mapping.postcodes_match
                     for fhrs_mapping in osm_object.fhrs_mappings):
                status = "matched_different_postcodes"
            else:
                status = "matched_same_postcodes"
        statuses.append(status)

    stats = []
    for status in OSM_STATUSES:
        stats.append(
            OSMLocalAuthorityDistrictStatistic(
                district_code=district.code,
                date=date.today(),
                statistic=status,
                value=statuses.count(status)))

    return stats


def get_osm_stats_by_district():
    """Return OSM object statistics by district for all districts"""

    query = Session.query(LocalAuthorityDistrict.code)
    district_codes = [row[0] for row in query]

    district_stats = []
    for district_code in district_codes:
        district = Session.query(LocalAuthorityDistrict).\
            options(joinedload("osm_objects").joinedload("fhrs_mappings").
                    joinedload("fhrs_establishment")).\
            get(district_code)

        debug(f"Calculating OSM statistics for district {district.name}")
        district_stats.extend(get_osm_stats_for_district(district))

    return district_stats


def replace_current_stats_in_session():
    """Add/replace today's statistics in the database session

    This doesn't commit the session.
    """

    info("Calculating statistics for FHRS authorities")
    Session.query(FHRSAuthorityStatistic).\
        filter(FHRSAuthorityStatistic.date == date.today()).\
        delete()
    Session.add_all(get_fhrs_stats_by_authority())

    info("Calculating statistics for OSM objects")
    Session.query(OSMLocalAuthorityDistrictStatistic).\
        filter(OSMLocalAuthorityDistrictStatistic.date == date.today()).\
        delete()
    Session.add_all(get_osm_stats_by_district())
