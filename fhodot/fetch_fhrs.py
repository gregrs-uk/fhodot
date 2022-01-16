"""Module for downloading and importing FHRS data"""

from logging import critical, debug, error, info, warning
from xml.etree.ElementTree import fromstring, iselement, ParseError

from requests import get
from requests.exceptions import RequestException
from retrying import retry
from sqlalchemy import desc, func

from fhodot.config import USER_AGENT
from fhodot.database import Session
from fhodot.models import FHRSAuthority, FHRSEstablishment


def retry_if_request_exception(exception):
    """Return True if exception is a RequestException"""
    return isinstance(exception, RequestException)


@retry(wait_exponential_multiplier=2000, # wait 2^attempt * 2 secs
       wait_exponential_max=60000, # wait max 1'00" between attempts
       stop_max_delay=181000, # wait up to a maximum of 3'01"
       retry_on_exception=retry_if_request_exception) # don't retry on others
def download_with_retries(url, headers=None, encoding=None, verify=None): # pragma: no cover
    """Download data from the internet

    If first attempt fails, wait and try again. The wait time increases
    exponentially. The user agent header is added automatically.

    url (string): the URL to download
    headers (dict): headers to add in addition to the user agent
    encoding (string): set to override the response encoding

    Return the data downloaded
    """

    assert isinstance(url, str)
    headers = {} if headers is None else headers
    assert isinstance(headers, dict)

    # merge user agent into headers
    headers = {**headers, "user-agent": USER_AGENT}

    try:
        response = get(url, headers=headers, verify=verify)
        response.raise_for_status() # raise on 4xx or 5xx error
    except RequestException: # should cover all requests exceptions
        warning(
            "Error when trying to get data\n" +
            f"URL: {response.url}\n" +
            f"Headers: {headers}\n" +
            f"Status code: {response.status_code}")
        raise # caught by @retry unless final attempt fails

    if encoding:
        response.encoding = encoding

    return response.text


def download_from_api(endpoint): # pragma: no cover
    """Use the FHRS API to download XML data

    endpoint (string): endpoint part of URL

    Returns XML string
    """

    api_base_url = "http://api.ratings.food.gov.uk/"
    api_headers = {"x-api-version": "2",
                   "accept": "application/xml"}

    return download_with_retries(
        url=api_base_url + endpoint,
        headers=api_headers,
        verify="fhodot/food_cert_chain.pem")


def download_authorities_from_api(): # pragma: no cover
    """Call api_download to download authorities

    Returns XML string
    """
    return download_from_api("Authorities")


def get_xml_field(node, field, namespace=None):
    """Get the text for a specified field from an XML node"""

    namespace = "" if namespace is None else namespace
    string = None

    element = node.find(namespace + field)
    if iselement(element):
        string = element.text

    assert string != "" # empty field should return None
    return string


def parse_xml_authorities(xml_string):
    """Parse FHRS authorities XML into FHRSAuthority objects

    Returns list of FHRSAuthority objects
    """

    try:
        root = fromstring(xml_string)
    except ParseError:
        critical("Error parsing authorities XML file")
        raise

    namespace = "{http://schemas.datacontract.org/2004/07/FHRS.Model.Detailed}"

    authorities = []
    for node in root.iter(namespace + "authority"):
        authority = FHRSAuthority()

        # last_updated set using method below
        mapping = {"code": "LocalAuthorityIdCode",
                   "name": "Name",
                   "region_name": "RegionName",
                   "email": "Email",
                   "xml_url": "FileName"}
        for db_field, xml_field in mapping.items():
            setattr(authority, db_field,
                    get_xml_field(node, xml_field, namespace))
        authority.set_last_published_from_string(
            get_xml_field(node, "LastPublishedDate", namespace))

        authorities.append(authority)

    return authorities


def compare_authority_counts(authorities, stop=1):
    """Compare count of authorities supplied with database

    Raise RuntimeError if database has 'stop' (default 1) or more
    authorities than the list supplied. Warn if database has any more
    authorities than the list supplied and give info if list has more
    authorities than the database.
    """

    database_count = Session.query(FHRSAuthority).count()
    xml_count = len(authorities)

    # if database has more, difference will be positive
    if database_count - xml_count >= stop:
        raise RuntimeError(f"Database has {database_count} authorities but " +
                           f"new data only has {xml_count}")

    if database_count > xml_count:
        warning(f"Database has {database_count} authorities but new data " +
                f"only has {xml_count}")
        return False

    if xml_count > database_count:
        info(f"Database has {database_count} authorities but new data has " +
             f"{xml_count}")
        return False

    return True


def get_authorities_requiring_fetch(authorities):
    """Return authorities requiring new or updated establishment data

    authorities (list of FHRSAuthority objects): authorities to check

    Returns list of FHRSAuthority objects
    """

    requiring_update = []
    for xml_authority in authorities:
        # if no last published date provided in new data, assume it's
        # newer than what's already in the database
        if not xml_authority.last_published:
            requiring_update.append(xml_authority)
            break

        db_authority = Session.query(FHRSAuthority).get(xml_authority.code)
        # if authority is in database, has a last published date, and
        # this date is newer or same as xml data, don't need to fetch
        fetch_not_required = (
            db_authority and db_authority.last_published and
            db_authority.last_published >= xml_authority.last_published)

        if not fetch_not_required:
            requiring_update.append(xml_authority)

    return requiring_update


def delete_obsolete_authorities_from_session(authorities):
    """Delete any authorities not in supplied list from session

    Return number of authorities deleted from session
    """

    xml_authority_codes = [authority.code for authority in authorities]
    db_authorities = Session.query(FHRSAuthority).all()

    num_deleted = 0
    for db_authority in db_authorities:
        if db_authority.code not in xml_authority_codes:
            info(f"Deleting obsolete authority '{db_authority.name}' " +
                 f"({db_authority.code}) and its establishments")
            Session.delete(db_authority)
            num_deleted += 1

    return num_deleted


def merge_authorities_with_session(authorities):
    """Merge the authorities supplied with the session

    This doesn't commit the session. New authorities will be added to
    the session and modified authorities will be modified based on
    primary-key matching.

    authorities (list of FHRSAuthority objects)
    """

    if (not isinstance(authorities, list) or
            not isinstance(authorities[0], FHRSAuthority)):
        raise TypeError(
            f"Expected a list of FHRSAuthority objects, got {authorities}")

    if not FHRSAuthority.__table__.exists(bind=Session.get_bind()):
        raise RuntimeError(
            f"Table '{FHRSAuthority.__tablename__}' doesn't exist")

    for authority in authorities:
        debug(f"Merging {authority} with session")
        Session.merge(authority)


def download_establishments_xml_file(authority): # pragma: no cover
    """Download the establishments XML file for an authority"""

    return download_with_retries(
        url=authority.xml_url,
        headers={"accept": "text/xml"},
        encoding="UTF-8",
        verify="fhodot/food_cert_chain.pem")


def parse_xml_establishments(xml_string):
    """Parse FHRS establishments XML into FHRSEstablishment objects

    Returns list of FHRSEstablishment objects
    """

    try:
        root = fromstring(xml_string)
    except ParseError:
        critical("Error parsing establishments XML file")
        raise

    establishments = []
    for node in root.iter("EstablishmentDetail"):
        establishment = FHRSEstablishment()

        # location set using method below
        mapping = {"fhrs_id": "FHRSID",
                   "name": "BusinessName",
                   "postcode_original": "PostCode",
                   # before address because if an address line contains a
                   # postcode, the address validator needs to check whether
                   # postcode already filled
                   "postcode": "PostCode",
                   # address in reverse order so that if postcode is in one
                   # or more address lines, latest postcode line is used
                   "address_4": "AddressLine4",
                   "address_3": "AddressLine3",
                   "address_2": "AddressLine2",
                   "address_1": "AddressLine1",
                   "rating_date": "RatingDate",
                   "authority_code": "LocalAuthorityCode"}
        for db_field, xml_field in mapping.items():
            setattr(establishment, db_field,
                    get_xml_field(node, xml_field))
        establishment.set_location(
            get_xml_field(node, "Geocode/Latitude"),
            get_xml_field(node, "Geocode/Longitude"))

        establishments.append(establishment)

    return establishments


def replace_establishments_for_authority_in_session(authority, establishments):
    """Replace establishments for supplied authority in the session

    This doesn't commit the session.

    authority (FHRSAuthority object)
    establishments (list of FHRSEstablishment objects)
    """

    if not isinstance(authority, FHRSAuthority):
        raise TypeError(
            "First argument should be an FHRSAuthority object, " +
            f"got {authority}")

    if (not isinstance(establishments, list) or
            not isinstance(establishments[0], FHRSEstablishment)):
        raise TypeError(
            "Second argument should be a list of FHRSEstablishment objects, " +
            f"got {establishments}")

    if not FHRSEstablishment.__table__.exists(bind=Session.get_bind()):
        raise RuntimeError(
            f"Table '{FHRSEstablishment.__tablename__}' doesn't exist")

    # delete establishments for this authority
    Session.query(FHRSEstablishment).\
        filter(FHRSEstablishment.authority_code == authority.code).\
        delete()

    # add establishments
    for establishment in establishments:

        fetched = Session.query(FHRSEstablishment).get(establishment.fhrs_id)
        if fetched:
            # cannot just add it and handle any exception because
            # exception only raised on commit
            warning(
                f"Could not add establishment '{establishment.name}' in "
                f"authority '{authority.name}' because there is already one " +
                f"with the same FHRS ID ({establishment.fhrs_id}) in " +
                f"authority '{fetched.authority.name}'")
        else:
            Session.add(establishment)


def add_authority_districts_in_session():
    """Store district code for each authority in column in session

    Storing the code for the local authority district associated with
    each authority in a column prevents a costly geographical lookup in
    the FHRS stats endpoint. This should be run after populating
    authorities with establishments as it uses the locations of the
    establishments to calculate the associated local authority district.
    This doesn't commit the session.
    """

    debug("Clearing stored district codes for FHRS authorities")
    Session.query(FHRSAuthority).\
        update({FHRSAuthority.district_code: None})

    # iterate authorities in order of number of establishments because
    # there are some small authorities that shouldn't be associated with
    # a district
    query = Session.query(FHRSAuthority).\
        join(FHRSEstablishment).\
        group_by(FHRSAuthority).\
        order_by(desc(func.count(FHRSEstablishment.fhrs_id)))

    for authority in query:
        district = authority.get_local_authority_district()

        if district and not district.fhrs_authority:
            debug("Setting local authority district for FHRS authority " +
                  f"{authority.name} to {district.name}")
            authority.district = district
            Session.add(authority)
            continue

        if district and district.fhrs_authority:
            error(f"District '{district.name}' for authority " +
                  f"'{authority.name}' already associated with FHRS " +
                  f"authority '{district.fhrs_authority.name}'")
            # carry on and show next error message

        # should only affect statistics, so don't raise an exception
        # that would stop updated FHRS data from being committed
        error("Could not set a local authority district for FHRS " +
              f"authority {authority.name}")
