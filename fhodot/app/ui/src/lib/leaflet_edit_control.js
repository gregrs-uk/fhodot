import { Control } from "leaflet";
import { openJOSMURL } from "./utils";

// adapted from https://github.com/osmlab/leaflet-edit-osm/

/**
 * A Leaflet control with JOSM and iD editing links for current map view
 */
export default class EditControl extends Control {
  constructor() {
    super();
    this.options.position = "bottomleft";
  }

  /**
   * Create the control (called when adding control to Leaflet map)
   */
  onAdd() {
    const element = document.createElement("div");
    element.className = "leaflet-edit-control";
    element.innerHTML = `
      <div class="leaflet-bar">
      <p>Edit in <span class="action edit-josm">JOSM</span> /
      <span class="action edit-id">iD</span></p>
      </div>`;

    element.querySelector("span.edit-josm")
      .addEventListener("click", this.editJOSM.bind(this));
    element.querySelector("span.edit-id")
      .addEventListener("click", this.editID.bind(this));

    return element;
  }

  /**
   * Open a link to edit current map view in JOSM
   */
  editJOSM() {
    const url = new URL("http://127.0.0.1:8111/load_and_zoom");
    /* eslint-disable no-underscore-dangle */
    url.searchParams.append("left", this._map.getBounds().getWest());
    url.searchParams.append("bottom", this._map.getBounds().getSouth());
    url.searchParams.append("right", this._map.getBounds().getEast());
    url.searchParams.append("top", this._map.getBounds().getNorth());
    /* eslint-enable no-underscore-dangle */
    openJOSMURL(url)
      .catch((error) => {
        // don't throw an error if JOSM isn't running
        if (!(error instanceof TypeError)) {
          throw error;
        }
      });
  }

  /**
   * Open a link to edit current map view in iD
   */
  editID() {
    const url = new URL("http://www.openstreetmap.org/edit?editor=id");
    /* eslint-disable no-underscore-dangle */
    const centre = this._map.getCenter();
    url.searchParams.append("lat", centre.lat);
    url.searchParams.append("lon", centre.lng);
    url.searchParams.append("zoom", this._map.getZoom());
    /* eslint-enable no-underscore-dangle */
    window.open(url);
  }
}
