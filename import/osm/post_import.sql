\set ON_ERROR_STOP true

-- rename here rather than in mapping.yml because if there isn't a column
-- called id, imposm will create an additional id column
ALTER TABLE import.osm RENAME id TO osm_id_single_space;
ALTER TABLE import.osm ADD CONSTRAINT osm_pkey
    PRIMARY KEY (osm_id_single_space);
DROP INDEX IF EXISTS import.osm_id_single_space_idx;

-- convert geometry column to location (centroid points, type geography)
ALTER TABLE import.osm ADD COLUMN location GEOGRAPHY;
UPDATE import.osm SET location = ST_Centroid(geometry)::geography;
ALTER TABLE import.osm DROP COLUMN geometry;

-- create index on location column
DROP INDEX IF EXISTS idx_osm_location;
CREATE INDEX idx_osm_location ON import.osm USING gist (location);

-- create association table between OSM objects and FHRS establishments
DROP TABLE IF EXISTS import.osm_fhrs_mapping;
CREATE TABLE import.osm_fhrs_mapping (
    osm_id_single_space BIGINT REFERENCES import.osm (osm_id_single_space),
    fhrs_id INT,
    PRIMARY KEY (osm_id_single_space, fhrs_id)
);

INSERT INTO import.osm_fhrs_mapping
    -- DISTINCT just in case an OSM object is linked to the same FHRS
    -- establishment multiple times
    SELECT DISTINCT
        osm_id_single_space,
        unnest(
            CASE
                -- check format of fhrs:id string
                -- allow optional single space after semicolons
                -- don't allow trailing semicolon
                WHEN fhrs_ids_string ~ '^([0-9]+(; ?(?!$))?)+$'
                    THEN string_to_array(fhrs_ids_string, ';')
                -- if invalid, create empty text array to unnest
                ELSE '{}'::text[]
            END
        )::int AS fhrs_id
    FROM import.osm;

-- create index on fhrs_id (no need to create one on id because it's
-- the first column of the primary key
DROP INDEX IF EXISTS import.idx_osm_fhrs_mapping_fhrs_id;
CREATE INDEX idx_osm_fhrs_mapping_fhrs_id ON import.osm_fhrs_mapping (fhrs_id);

-- rotate schemas here rather than using imposm deploy option in order
-- to include the materialized view
DROP SCHEMA IF EXISTS backup CASCADE;
CREATE SCHEMA backup;
ALTER TABLE IF EXISTS public.osm SET SCHEMA backup;
ALTER TABLE IF EXISTS public.osm_fhrs_mapping SET SCHEMA backup;
ALTER TABLE import.osm SET SCHEMA public;
ALTER TABLE import.osm_fhrs_mapping SET SCHEMA public;

VACUUM ANALYZE osm;
VACUUM ANALYZE osm_fhrs_mapping;
