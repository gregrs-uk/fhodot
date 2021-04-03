#!/bin/bash
cd /home/gregrs/fhodot || exit 1
source venv/bin/activate || exit 1
# overwrites previous file
wget --no-verbose http://download.geofabrik.de/europe/britain-and-ireland-latest.osm.pbf -O import/osm/britain-and-ireland-latest.osm.pbf && \
	scripts/import_osm.sh
python -m scripts.update_fhrs
python -m scripts.calculate_statistics
cd stats
R -q -e "targets::tar_make(reporter='silent')" && \
	cp output/* /home/gregrs/public_html/fhodot/graphs/ &&
	cp summary.html /home/gregrs/public_html/fhodot/
