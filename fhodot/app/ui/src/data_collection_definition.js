/**
 * Defines the specific set of DataSource instances to be used
 */

import { LayerGroup } from "leaflet";

import DataSource from "./lib/data_source";
import DataCollection from "./lib/data_collection";
import {
  fhrsNoLocationTable,
  fhrsPostcodeDifferencesTable,
  fhrsUnmatchedTable,
  mismatchesTable,
  osmPostcodeDifferencesTable,
  osmUnmatchedTable,
} from "./table_definitions";

// define data sources, layers and associated functions
const getDataCollection = (inspector) => new DataCollection([
  new DataSource({
    name: "fhrs",
    type: "fhrs",
    label: "FHRS establishments",
    jsonURL: `api/fhrs`,
    statsJSONURL: `api/stats_fhrs`,
    markerClickFunction: (data) => inspector.updateFHRS(data),
    tables: [
      fhrsPostcodeDifferencesTable, fhrsUnmatchedTable, fhrsNoLocationTable,
    ],
    keyboardShortcut: "f",
  }),
  new DataSource({
    name: "osm",
    type: "osm",
    label: "OSM objects",
    jsonURL: `api/osm`,
    statsJSONURL: `api/stats_osm`,
    markerClickFunction: (data) => inspector.updateOSM(data, false),
    tables: [mismatchesTable, osmPostcodeDifferencesTable, osmUnmatchedTable],
    keyboardShortcut: "o",
  }),
  new DataSource({
    name: "suggest",
    type: "osm",
    label: "Suggested matches",
    jsonURL: `api/suggest`,
    markerClickFunction: (data) => inspector.updateOSM(data, true),
    tables: [],
    keyboardShortcut: "s",
  }),
  new DataSource({
    name: "distant",
    type: "osm",
    label: "Distant matches",
    lineLayer: new LayerGroup(),
    jsonURL: `api/distant`,
    markerClickFunction: (data) => inspector.updateOSM(data, false),
    tables: [osmPostcodeDifferencesTable],
    keyboardShortcut: "d",
  }),
]);

export default getDataCollection;
