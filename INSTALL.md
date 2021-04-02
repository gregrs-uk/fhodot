# Setting up a development environment

You don't need to install anything to use this tool; simply use the [dev server instance](https://gregrs.dev.openstreetmap.org/fhodot/). However if you would like to help with development or run a local version for some other reason, then please see the instructions below.

You may also wish to read the documentation on [contributing](CONTRIBUTING.md).

## Prerequisites

The development environment can only be fully installed on Linux because [Imposm](https://imposm.org/docs/imposm3/latest/) only runs on Linux. However, macOS can be used if the database is copied from a Linux instance once data has been imported.

## Install software

First install the following software:

* [Python 3.8+](https://www.python.org/downloads/)
* [Node 14+](https://nodejs.org/en/download/)
* [R 4+](https://www.r-project.org) (for statistics)
* [Postgres 12.5+](https://www.postgresql.org/download/) with [PostGIS 3.0+](http://postgis.net/install/)
* [Imposm 3](https://github.com/omniscale/imposm3/releases)
* [Redis](https://redis.io/download) (storage for rate limiting)

## Download source code

* Clone this repository and `cd` to it
* Set up Python virtual environment e.g. `python3 -m venv venv`
* Activate the virtual environment e.g. `source venv/bin/activate`
* Install the necessary Python packages e.g. `pip install -r requirements.txt`
* Install the necessary Node modules e.g. `npm ci`

## Set up database

* Create a Postgres database e.g. `createdb fhodot`, log in e.g. `psql -d fhodot` and run `CREATE EXTENSION postgis`
* Set `DATABASE_URL` in `fhodot/config.py`

## Download and import data

* Download [ONS Local Authority Districts boundaries](https://geoportal.statistics.gov.uk/datasets/local-authority-districts-december-2020-uk-bgc) (BGC, i.e. 20m generalised and clipped to coastline) shapefiles, place them in the `import/boundaries` directory and run `python -m scripts.import_boundaries`
* Download [Ordnance Survey Open Names](https://osdatahub.os.uk/downloads/open/OpenNames) CSV files, place them in the `import/os_open_names` directory and run `python -m scripts.import_os_open_names`
* Download [Geofabrik export of Britain and Ireland](http://download.geofabrik.de/europe/britain-and-ireland-latest.osm.pbf), place the file in `import/osm`, and set the configuration variables in `scripts/import_osm.sh` before running it
* Download and import FHRS data using `python -m scripts.update_fhrs`
* Calculate statistics using `python -m scripts.calculate_statistics`
* If you wish to display/develop the graphs and/or summary statistics, run `R -e "targets::tar_make()"` and copy `stats/output/*` to a new directory `fhodot/app/ui/dist/graphs`, and `stats/summary.html` to `fhodot/ui/dist`

## Run local server and watch for changes

* Run the Flask development server using `scripts/run_flask_dev_server.sh`
* Run `npm run watch` to watch for changes and bundle the frontend
* Run `redis-server` to keep track of rate limiting
* Navigate to [http://127.0.0.1:5000/index.html](http://127.0.0.1:5000/index.html) in your browser
