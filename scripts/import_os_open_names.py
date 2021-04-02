"""Import OS Open Names data into the database"""

from logging import info
from os import listdir
from os.path import join

from fhodot.database import session_scope, Session
from fhodot.models.os_open_names import OSOpenNamesObject, OSPlace, OSRoad
from fhodot.os_open_names import import_csv

open_names_dir = "import/os_open_names"

# utf-8-sig encoding to remove leading BOM and
# strip to remove trailing newline
with open(join(open_names_dir, "DOC/OS_Open_Names_Header.csv"),
          "r", encoding="utf-8-sig") as headers_file:
    headers = headers_file.readline().strip().split(",")

with session_scope() as session:
    Session.query(OSPlace).delete() # all places
    Session.query(OSRoad).delete() # all roads
    data_dir = join(open_names_dir, "DATA")
    for filename in listdir(data_dir):
        info(f"Reading {filename}")
        import_csv(join(data_dir, filename), headers)
    info(f"Committing to database")
