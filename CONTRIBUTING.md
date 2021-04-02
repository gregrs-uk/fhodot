# Contributing

Bug reports, feature requests and pull requests are welcome but please bear in mind that there may be some delay before I have time to respond to these.

If planning a pull request you may wish to open an issue first to discuss your modifications. Please try to stick to the guidelines below. There are also [instructions on setting up a development environment](INSTALL.md).


## Tools

The following tools are used in this project:

### Server-side

With the exception of importing OpenStreetMap data and producing statistics/graphs, the backend is written in Python.

* OpenStreetMap import: [Imposm 3](https://imposm.org)
* Database: [PostGIS](https://postgis.net)
* Object Relational Mapper: [SQLAlchemy](https://docs.sqlalchemy.org/) (with [GeoAlchemy2](https://geoalchemy-2.readthedocs.io/))
* Web framework: [Flask](https://flask.palletsprojects.com/)
* Storage for rate limiting: [Redis](https://redis.io/)
* Unit testing: [unittest](https://docs.python.org/3/library/unittest.html)
* Statistics: written in [R](https://www.r-project.org) using [tidyverse](https://www.tidyverse.org/) packages

### Client-side

The frontend is written in JavaScript (ES6).

* [Node.js](https://nodejs.org/)
* Bundler: [Webpack](https://webpack.js.org/)
* Mapping: [Leaflet](https://leafletjs.com/)
* Unit testing: [Mocha](https://mochajs.org), [Chai](https://www.chaijs.com), [Karma](http://karma-runner.github.io) with [Headless Chrome](https://developers.google.com/web/updates/2017/04/headless-chrome)


## Coding style

### Python

* Please follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) and use pylint to check your code e.g. using the helper script `run_pylint.sh`
* Please use double quotes (") for strings
* Feel free to break up sections of code with a blank line
* Please put two blank lines between class and method definitions

### JavaScript

* Please follow the [Airbnb style guide](https://github.com/airbnb/javascript) with the modifications configured in `package.json` and use eslint to check your code e.g. using `npm run lint`
* Please use double quotes (") for strings

### Line length

* Code lines should be 79 characters or less, unless they contain a URL or finish with a coverage/pylint/eslint comment
* Python docstring lines should be 72 characters or less

### Imports

* Please separate Python standard library, third-party and local imports with a line break, and within each block import in alphabetical order of package
* In Python code, in general please use the `from x import y` style


## Unit tests

* These are a work in progress but please do write unit tests for any new code (apart from that which downloads external data) and check coverage

### Python

* You can find unit tests in `tests/` with a file per class per module
* `scripts/run_tests.sh` will run the tests and provide a coverage report in `coverage/python`

### JavaScript

* You can find unit tests in `fhodot/app/ui/src`
* `npm run test` will run the tests in  using  and provide a coverage report in `coverage/javascript`
* Tests can also be run in a browser (`http://127.0.0.1:5000/tests.html`) once bundled with `npm run watch` or `npm run build`
