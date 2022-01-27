#!/bin/sh

# absolute path to script
script=$(readlink -f "$0")
scriptpath=$(dirname "$script")
. "$scriptpath"/import_osm_config.sh

# cd because imposm_config.json references files in osm_import_dir
original_dir="$(pwd)"
cd $osm_import_dir || exit 1

$imposm_binary_dir/imposm import -quiet -config imposm_config.json \
	-read $data_file -overwritecache -write || exit 1

psql -d $database_name -q -f $osm_import_dir/post_import.sql

cd $original_dir
