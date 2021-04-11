/**
 * The script to be included in index.html
 */

import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "./styles.css";

import GraphArea from "./lib/graph_area";
import Inspector from "./lib/inspector";
import { styleMarker } from "./lib/marker_styling";
import SlippyMap from "./lib/slippy_map";
import { PayloadTooLargeError } from "./lib/utils";
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

const currentDataSource = () => dataCollection.getCurrentDataSource(map);

const refreshDataSource = (dataSource) => {
  let refreshCompleted = false;

  dataSource.refresh(map)
    .then(() => {
      refreshCompleted = true;
      map.messageControl.setMessage("Loaded"); // without showing if hidden
      map.messageControl.hide(); // hide loading message if present
    })
    .catch((error) => {
      refreshCompleted = true; // even though unsuccessful
      if (error.name === "AbortError") {
        map.messageControl.hide(); // hide loading message if present
        return null;
      }
      if (error instanceof PayloadTooLargeError) {
        dataSource.clearPoints();
        dataSource.clearLines();
        map.messageControl.showMessage(`
          Cannot fetch map data for this area because there are too many
          objects. Try zooming in.`);
        return null;
      }
      map.messageControl.showMessage("Error loading map data");
      throw error;
    });

  setTimeout(() => {
    if (!refreshCompleted) {
      map.messageControl.showMessage("Loading&hellip;");
    }
  }, 500);
};

const refreshCurrentDataSource = () => {
  refreshDataSource(currentDataSource());
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
  if (currentDataSource().statsLayer) {
    inspector.showStatsDiv();
    inspector.updateStatsDiv(null, currentDataSource().name);
  }
}

const updateURL = () => {
  // may not be same URL as initial page load
  const url = new URL(window.location.href);
  url.searchParams.set("lat", map.currentCentreLatLon.lat.toFixed(5));
  url.searchParams.set("lon", map.currentCentreLatLon.lng.toFixed(5));
  url.searchParams.set("zoom", map.currentZoom);
  url.searchParams.set("layer", currentDataSource().name);
  window.history.replaceState(null, "", url);
};

// use document as a global message bus

// map-related events
document.addEventListener("mapMoveEnd", () => {
  map.messageControl.hide();
  refreshCurrentDataSource();
  updateURL();
});
document.addEventListener("layerGroupAdd", (e) => {
  refreshDataSource(e.detail);
  updateURL();
});
document.addEventListener("pointLayerRemove", (e) => {
  const dataSource = e.detail;
  map.messageControl.hide();
  dataSource.forgetSelectedFeature();
  inspector.clearAll();
  inspector.forgetRememberedProperties();
  if (map.belowMinZoomWithMarkers) inspector.showZoomInMessage();
  tableGroup.clear();
});
document.addEventListener("pointLayerAdd", () => {
  inspector.removeZoomInMessage();
});
document.addEventListener("statsLayerRemove", () => {
  inspector.removeStatsDiv();
  graphArea.clear();
});
document.addEventListener("statsLayerAdd", (e) => {
  const dataSource = e.detail;
  inspector.showStatsDiv();
  inspector.updateStatsDiv(null, dataSource.name);
});

// district polygon-related events
document.addEventListener("districtMouseOver", (e) => {
  inspector.updateStatsDiv(e.detail, currentDataSource().name);
});
document.addEventListener("districtMouseOut", () => {
  inspector.updateStatsDiv(null, currentDataSource().name);
});
document.addEventListener("districtClick", (e) => {
  const graphType = currentDataSource().name;
  const url = `graphs/${graphType}-${e.detail.districtCode}.png`;
  graphArea.updateGraph(url);
});

// automatically switching layers when linking OSM/FHRS features
document.addEventListener("autoChooseLayer", () => {
  const newDataSource = (currentDataSource().type === "osm" ? "fhrs" : "osm");
  currentDataSource().removeLayerGroupFrom(map);
  // this will also cause SlippyMap to fire mapLayerChange event on document
  dataCollection.getDataSourceByName(newDataSource).addLayerGroupTo(map);
});

// switching layer by keyboard shortcut
document.addEventListener("keyup", (e) => {
  const newDataSource = dataCollection.getDataSourceByKeyboardShortcut(e.key);
  if (!newDataSource) return;
  if (newDataSource !== currentDataSource()) {
    currentDataSource().removeLayerGroupFrom(map);
    newDataSource.addLayerGroupTo(map);
  }
});

// select feature and optionally zoom map
document.addEventListener("requestSelect", (e) => {
  const feature = e.detail;
  currentDataSource().selectFeature(feature);
  currentDataSource().markerClickFunction(feature.properties);
});
document.addEventListener("requestSelectAndZoom", (e) => {
  const feature = e.detail;
  const [lon, lat] = e.detail.geometry.coordinates;
  currentDataSource().selectFeature(feature);
  currentDataSource().markerClickFunction(feature.properties);
  map.zoomTo(lat, lon);
});
