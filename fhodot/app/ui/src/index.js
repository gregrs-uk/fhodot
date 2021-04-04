/**
 * The script to be included in index.html
 */

import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "./styles.css";

import Inspector from "./lib/inspector";
import SlippyMap from "./lib/slippy_map";
import GraphArea from "./lib/graph_area";
import getDataCollection from "./data_collection_definition";
import { tableGroup } from "./table_definitions";

const initialURL = new URL(window.location.href);
// expect null if URL parameter not specified
const initialLat = initialURL.searchParams.get("lat");
const initialLon = initialURL.searchParams.get("lon");
let initialCentre = null;
if (initialLat && initialLon) {
  initialCentre = [initialLat, initialLon];
}
const initialZoom = initialURL.searchParams.get("zoom");
const initialLayer = initialURL.searchParams.get("layer");

const map = new SlippyMap("map", { initialCentre, initialZoom });
const inspector = new Inspector("inspector");
const dataCollection = getDataCollection(inspector);
const graphArea = new GraphArea("graphs");

map.addLayerControl(dataCollection);

const refreshCurrentDataSource = () => {
  dataCollection.getCurrentDataSource(map).refresh(map);
};

// null if layer name invalid
const initialDataSource = dataCollection.getDataSourceByName(initialLayer);
if (initialDataSource) {
  initialDataSource.addLayerGroupTo(map);
} else {
  dataCollection.dataSources[0].addLayerGroupTo(map);
}
refreshCurrentDataSource();

if (map.belowMinZoomWithMarkers) {
  inspector.showZoomInMessage();
  if (dataCollection.getCurrentDataSource(map).statsLayer) {
    inspector.showStatsDiv();
    inspector.updateStatsDiv(
      null, dataCollection.getCurrentDataSource(map).name,
    );
  }
}

const updateURL = () => {
  // may not be same URL as initial page load
  const url = new URL(window.location.href);
  url.searchParams.set("lat", map.currentCentreLatLon.lat.toFixed(5));
  url.searchParams.set("lon", map.currentCentreLatLon.lng.toFixed(5));
  url.searchParams.set("zoom", map.currentZoom);
  url.searchParams.set(
    "layer", dataCollection.getCurrentDataSource(map).name,
  );
  window.history.replaceState(null, "", url);
};

// use document as a global message bus

// map-related events
document.addEventListener("mapZoomNoMarkers", () => {
  inspector.showZoomInMessage();
  if (dataCollection.getCurrentDataSource(map).statsLayer) {
    inspector.showStatsDiv();
    inspector.updateStatsDiv(
      null, dataCollection.getCurrentDataSource(map).name,
    );
  }
  tableGroup.clear();
});
document.addEventListener("mapZoomMarkersVisible", () => {
  inspector.removeZoomInMessage();
  inspector.removeStatsDiv();
  graphArea.clear();
});
document.addEventListener("mapMoveEnd", () => {
  refreshCurrentDataSource();
  updateURL();
});
document.addEventListener("mapLayerChange", () => {
  inspector.clearAll();
  inspector.forgetRememberedProperties();
  if (map.belowMinZoomWithMarkers) {
    inspector.showZoomInMessage();
    if (dataCollection.getCurrentDataSource(map).statsLayer) {
      inspector.showStatsDiv();
      inspector.updateStatsDiv(
        null, dataCollection.getCurrentDataSource(map).name,
      );
    }
  }
  tableGroup.clear();
  graphArea.clear();
  refreshCurrentDataSource();
  updateURL();
});

// district polygon-related events
document.addEventListener("districtMouseOver", (e) => {
  inspector.updateStatsDiv(
    e.detail, dataCollection.getCurrentDataSource(map).name,
  );
});
document.addEventListener("districtMouseOut", () => {
  inspector.updateStatsDiv(
    null, dataCollection.getCurrentDataSource(map).name,
  );
});
document.addEventListener("districtClick", (e) => {
  const graphType = dataCollection.getCurrentDataSource(map).name;
  const url = `graphs/${graphType}-${e.detail.districtCode}.png`;
  graphArea.updateGraph(url);
});

// automatically switching layers when linking OSM/FHRS features
document.addEventListener("autoChooseLayer", () => {
  const currentDataSource = dataCollection.getCurrentDataSource(map);
  currentDataSource.removeLayerGroupFrom(map);
  const newDataSource = (currentDataSource.type === "osm" ? "fhrs" : "osm");
  // this will also cause SlippyMap to fire mapLayerChange event on document
  dataCollection.getDataSourceByName(newDataSource).addLayerGroupTo(map);
});

// switching layer by keyboard shortcut
document.addEventListener("keyup", (e) => {
  const newDataSource = dataCollection.getDataSourceByKeyboardShortcut(e.key);
  if (!newDataSource) return;
  const currentDataSource = dataCollection.getCurrentDataSource(map);
  if (newDataSource !== currentDataSource) {
    currentDataSource.removeLayerGroupFrom(map);
    newDataSource.addLayerGroupTo(map);
  }
});

// select feature and optionally zoom map
document.addEventListener("requestSelect", (e) => {
  dataCollection.getCurrentDataSource(map)
    .markerClickFunction(e.detail.properties);
});
document.addEventListener("requestSelectAndZoom", (e) => {
  const [lon, lat] = e.detail.geometry.coordinates;
  map.zoomTo(lat, lon);
  dataCollection.getCurrentDataSource(map)
    .markerClickFunction(e.detail.properties);
});
