/**
 * The multi-layer Leaflet slippy map and associated methods
 *
 * The actual Leaflet map object is SlippyMap.leafletMap, which can be
 * populated with a layer for each DataSource.
 */

import { control, map as leafletMap, tileLayer } from "leaflet";
import EditControl from "./leaflet_edit_control";
import MessageControl from "./leaflet_message_control";

export default class SlippyMap {
  constructor(elementID, options = {}) {
    // default view is of entire of Great Britain (with no markers)
    const initialCentre = options.initialCentre || [55.6, -5.2];
    const initialZoom = options.initialZoom || 5;
    // can comfortably see smallest stats multipolygons at zoom level 10
    this.minZoomWithMarkers = options.minZoomWithMarkers || 11;
    this.maxZoom = options.maxZoom || 19;
    this.leafletMap = leafletMap(elementID, {
      center: initialCentre,
      zoom: initialZoom,
      maxZoom: this.maxZoom,
    });

    new EditControl().addTo(this.leafletMap);
    this.messageControl = new MessageControl().addTo(this.leafletMap);

    const attribution = `
      &copy; <a href='https://www.openstreetmap.org/copyright' target='_blank'>
      OpenStreetMap contributors</a>. Contains
      <a href='https://www.food.gov.uk/crown-copyright' target='_blank'>
      food hygiene rating data</a> and
      <a href='https://www.ons.gov.uk/methodology/geography/licences'
      target='_blank'>OS data</a> &copy; Crown copyright and database right
      </a>.`;

    tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution,
      maxZoom: this.maxZoom,
    }).addTo(this.leafletMap);

    this.previousZoom = null;
    this.leafletMap.addEventListener("zoomstart", this.onZoomStart.bind(this));
    this.leafletMap.addEventListener("zoomend", this.onZoomEnd.bind(this));
    this.leafletMap.addEventListener("moveend", () => {
      document.dispatchEvent(new Event("mapMoveEnd"));
    });
    this.leafletMap.addEventListener("baselayerchange", () => {
      document.dispatchEvent(new Event("mapLayerChange"));
    });
  }

  /**
   * Return true if the map is too zoomed out for markers to be shown
   */
  get belowMinZoomWithMarkers() {
    if (this.leafletMap.getZoom() < this.minZoomWithMarkers) {
      return true;
    }
    return false;
  }

  /**
   * Add a LayerControl to the map and populate using dataCollection
   */
  addLayerControl(dataCollection) {
    this.layerControl = control.layers().addTo(this.leafletMap);
    dataCollection.dataSources.forEach((dataSource) => {
      this.layerControl.addBaseLayer(
        dataSource.layerGroup,
        `${dataSource.label} <kbd>${dataSource.keyboardShortcut}</kbd>`,
      );
    });
  }

  /**
   * Get the bounding box of the current map view as an object
   */
  get bboxParams() {
    return {
      l: this.leafletMap.getBounds().getWest(),
      b: this.leafletMap.getBounds().getSouth(),
      r: this.leafletMap.getBounds().getEast(),
      t: this.leafletMap.getBounds().getNorth(),
    };
  }

  /**
   * Get the centre of the current map view as a Leaflet.LatLng
   *
   * The object returned has the properties lat and lng (not lon).
   */
  get currentCentreLatLon() {
    return this.leafletMap.getCenter();
  }

  /**
   * Get the zoom level of the current map view
   */
  get currentZoom() {
    return this.leafletMap.getZoom();
  }

  /**
   * Store the previous zoom level when starting a zoom
   */
  onZoomStart() {
    this.previousZoom = this.leafletMap.getZoom();
  }

  /**
   * Trigger an appropriate event on document when finishing a zoom
   */
  onZoomEnd() {
    const currentZoom = this.leafletMap.getZoom();
    if (currentZoom === this.minZoomWithMarkers - 1
        && currentZoom < this.previousZoom) {
      document.dispatchEvent(new Event("mapZoomNoMarkers"));
    } else if (currentZoom === this.minZoomWithMarkers
        && currentZoom > this.previousZoom) {
      document.dispatchEvent(new Event("mapZoomMarkersVisible"));
    }
  }

  /**
   * Centre the map on the specified location and set zoom to maxZoom
   */
  zoomTo(lat, lon) {
    this.leafletMap.setView({ lat, lon }, this.maxZoom);
  }
}
