import { expect } from "chai";
import { Control, LayerGroup, Map as LeafletMap } from "leaflet";
import {
  describe, it, beforeEach, afterEach,
} from "mocha";

import DataSource from "./data_source";
import DataCollection from "./data_collection";
import SlippyMap from "./slippy_map";

describe("SlippyMap", () => {
  const mapDiv = document.createElement("div");
  mapDiv.id = "map";

  describe("Constructor", () => {
    let map;

    beforeEach(() => {
      document.querySelector("body").append(mapDiv);
      map = new SlippyMap("map");
    });

    afterEach(() => {
      map.leafletMap.remove();
      mapDiv.remove();
    });

    it("creates a leaflet Map instance called leafletMap", () => {
      expect(map.leafletMap).to.be.an.instanceOf(LeafletMap);
    });

    it("sets appropriate minZoomWithMarkers", () => {
      expect(map.minZoomWithMarkers).to.be.a("number");
      expect(map.minZoomWithMarkers).to.be.at.least(0);
      expect(map.minZoomWithMarkers).to.be.at.most(19);
    });
  });

  describe("belowMinZoomWithMarkers", () => {
    let map;

    beforeEach(() => {
      document.querySelector("body").append(mapDiv);
      map = new SlippyMap("map");
    });

    afterEach(() => {
      map.leafletMap.remove();
      mapDiv.remove();
    });

    it("is true when below minZoomWithMarkers", (done) => {
      map.leafletMap.on("zoomend", () => {
        expect(map.belowMinZoomWithMarkers).to.equal(true);
        done();
      });
      map.leafletMap.setZoom(map.minZoomWithMarkers - 1, { animate: false });
    });

    it("is false when above minZoomWithMarkers", (done) => {
      map.leafletMap.on("zoomend", () => {
        expect(map.belowMinZoomWithMarkers).to.equal(false);
        done();
      });
      map.leafletMap.setZoom(map.minZoomWithMarkers + 1, { animate: false });
    });

    it("is false when at minZoomWithMarkers", (done) => {
      // zoom in first so we have somewhere to zoom to
      map.leafletMap.setZoom(map.minZoomWithMarkers + 1, { animate: false });
      map.leafletMap.on("zoomend", () => {
        expect(map.belowMinZoomWithMarkers).to.equal(false);
        done();
      });
      map.leafletMap.setZoom(map.minZoomWithMarkers, { animate: false });
    });
  });

  describe("addLayerControl", () => {
    let map;
    let dataCollection;

    beforeEach(() => {
      document.querySelector("body").append(mapDiv);
      map = new SlippyMap("map");
      dataCollection = new DataCollection([
        new DataSource({ label: "One", type: "fhrs", keyboardShortcut: "1" }),
        new DataSource({ label: "Two", type: "osm", keyboardShortcut: "2" }),
      ]);
      map.addLayerControl(dataCollection);
    });

    afterEach(() => {
      map.leafletMap.remove();
      mapDiv.remove();
    });

    it("creates leaflet Control.Layers instance", () => {
      expect(map.layerControl).to.be.an.instanceOf(Control.Layers);
    });

    /* eslint-disable no-underscore-dangle */

    it("adds layers correctly", () => {
      expect(map.layerControl._layers.length).to.equal(2);
      expect(map.layerControl._layers[0].layer).to.be.an
        .instanceOf(LayerGroup);
      expect(map.layerControl._layers[1].layer).to.be.an
        .instanceOf(LayerGroup);
    });

    it("uses labels correctly", () => {
      expect(map.layerControl._layers.length).to.equal(2);
      expect(map.layerControl._layers[0].name).to.equal("One <kbd>1</kbd>");
      expect(map.layerControl._layers[1].name).to.equal("Two <kbd>2</kbd>");
    });

    /* eslint-enable no-underscore-dangle */
  });

  describe("bboxParams", () => {
    let map;

    beforeEach(() => {
      document.querySelector("body").append(mapDiv);
      map = new SlippyMap("map");
    });

    afterEach(() => {
      map.leafletMap.remove();
      mapDiv.remove();
    });

    it("is an object", () => {
      expect(map.bboxParams).to.be.an("object");
    });

    it("has l, b, r and t, which are numbers", () => {
      expect(map.bboxParams.l).to.be.a("number");
      expect(map.bboxParams.b).to.be.a("number");
      expect(map.bboxParams.r).to.be.a("number");
      expect(map.bboxParams.t).to.be.a("number");
    });
  });
});
