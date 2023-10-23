# Setting up a development environment

You don't need to install anything to use this tool; simply use the [dev server instance](https://gregrs.dev.openstreetmap.org/fhodot/).

However if you would like to help with development or run a local version for some other reason, the easiest way to set up a development environment is to use the provided Docker configuration. Please see the instructions below. You may also wish to read the documentation on [contributing](CONTRIBUTING.md).

## Install Docker

On Mac and Windows you can install [Docker Desktop](https://www.docker.com/products/docker-desktop), which is free for non-commercial open source projects. On Linux you will need to install [Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/).

## Download source code

Clone this repository and `cd` to it.

## Install Node modules

Run `docker-compose run node npm ci` to build and run the `node` service and install the necessary Node modules in the `node_modules` directory.

## Download and import data

1. Download [ONS Local Authority Districts boundaries](https://geoportal.statistics.gov.uk/datasets/local-authority-districts-may-2023-uk-bgc) (BGC, i.e. 20m generalised and clipped to coastline) shapefiles, place them in the `import/boundaries` directory and run `docker-compose run python python -m scripts.import_boundaries`. (The first `python` is the name of the service and the second is part of the command. The service will be built the first time it is run)
1. Download [Ordnance Survey Open Names](https://osdatahub.os.uk/downloads/open/OpenNames) CSV files, place them in the `import/os_open_names` directory and run `docker-compose run python python -m scripts.import_os_open_names`
1. Download [Geofabrik export of Britain and Ireland](http://download.geofabrik.de/europe/britain-and-ireland-latest.osm.pbf), place the file in `import/osm`, and run `docker-compose up imposm` to build the `imposm` service and import the necessary OSM data to the database
1. Download and import FHRS data using `docker-compose run python python -m scripts.update_fhrs`
1. Calculate statistics using `docker-compose run python python -m scripts.calculate_statistics`
1. If you wish to display/develop the graphs and/or summary statistics, run `docker-compose up rstats` then copy `stats/output/*` to a new directory `fhodot/app/ui/dist/graphs`, and `stats/summary.html` to `fhodot/ui/dist`

## Run local server and watch for changes

1. Run `docker-compose up python node`. This will automatically run the Flask development server and database server, watch for changes and bundle the frontend using `npm run watch`, and run Redis to keep track of rate limiting
1. Navigate to [http://127.0.0.1:5000/index.html](http://127.0.0.1:5000/index.html) in your browser
