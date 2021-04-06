"""Functions for importing OS Open Names data"""

from csv import DictReader

from fhodot.database import Session
from fhodot.models import OSOpenNamesObject, OSPlace, OSRoad
from fhodot.standardise import standardise


def add_os_object_to_session(os_class, row):
    """Add OSPlace or OSRoad to database session using data from row"""

    assert issubclass(os_class, OSOpenNamesObject)

    # Standardised names stored directly in database rather than using
    # column_property; it's not possible to use the (non-immutable)
    # Postgres 'unaccent' function within an index.
    os_object = os_class(os_id=row["ID"],
                         name_1=row["NAME1"],
                         name_1_lang=row["NAME1_LANG"],
                         name_1_std=standardise(row["NAME1"]),
                         name_2=row["NAME2"],
                         name_2_lang=row["NAME2_LANG"],
                         name_2_std=standardise(row["NAME2"]),
                         postcode_district=row["POSTCODE_DISTRICT"])
    if os_class == OSPlace:
        os_object.place_type = row["LOCAL_TYPE"]

    Session.add(os_object)


def process_row(row):
    """If row represents populated place or named road, add to database"""

    if row["TYPE"] == "populatedPlace":
        add_os_object_to_session(OSPlace, row)

    elif (row["TYPE"] == "transportNetwork" and
          row["LOCAL_TYPE"] == "Named Road"):
        add_os_object_to_session(OSRoad, row)


def import_csv(file_path, headers):
    """Filter a single OS CSV file and store relevant objects"""

    with open(file_path, "r", encoding="utf-8-sig") as data_file:
        for row in DictReader(data_file,
                              fieldnames=headers,
                              delimiter=",",
                              quotechar='"'):
            process_row(row)
