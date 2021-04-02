"""Update the FHRS database tables using the FSA's API"""


from logging import debug, info

from fhodot import fetch_fhrs
from fhodot.database import session_scope


info("Fetching authority data from API")
authorities_xml = fetch_fhrs.download_authorities_from_api()

info("Parsing XML")
authorities = fetch_fhrs.parse_xml_authorities(authorities_xml)

# database will not be committed until process completes and will be
# rolled back if any individual step fails

with session_scope() as session:
    info("Comparing authority counts")
    fetch_fhrs.compare_authority_counts(authorities)

    info("Deleting any obsolete authorities and their establishments")
    fetch_fhrs.delete_obsolete_authorities_from_session(authorities)

    info("Getting list of authorities to fetch")
    to_fetch = fetch_fhrs.get_authorities_requiring_fetch(authorities)

    info("Merging all authority data into database")
    fetch_fhrs.merge_authorities_with_session(authorities)

    for authority in to_fetch:
        info(f"Updating authority '{authority.name}'")

        debug("Downloading XML file")
        est_xml = fetch_fhrs.download_establishments_xml_file(authority)

        debug("Parsing XML file")
        establishments = fetch_fhrs.parse_xml_establishments(est_xml)

        debug("Replacing authority's establishments in database")
        fetch_fhrs.replace_establishments_for_authority_in_session(
            authority, establishments)

    if not to_fetch:
        info("All authorities' establishment data is already up to date")

    info("Associating authorities with local authority districts")
    fetch_fhrs.add_authority_districts_in_session()

info("FHRS data updated successfully")
