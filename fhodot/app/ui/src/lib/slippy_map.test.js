import { expect } from "chai";
import { Control, LayerGroup, Map as LeafletMap } from "leaflet";
import { MarkerClusterGroup } from "leaflet.markercluster";
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
        new DataSource({ label: "One", type: "fhrs" }),
        new DataSource({ label: "Two", type: "osm" }),
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
      expect(map.layerControl._layers[0].name).to.equal("One");
      expect(map.layerControl._layers[1].name).to.equal("Two");
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

  describe("onZoomStart", () => {
    let map;

    beforeEach(() => {
      document.querySelector("body").append(mapDiv);
      map = new SlippyMap("map");
    });

    afterEach(() => {
      map.leafletMap.remove();
      mapDiv.remove();
    });

    it("stores previous zoom when zooming in", (done) => {
      const before = map.leafletMap.getZoom();
      map.leafletMap.on("zoomend", () => {
        expect(before).to.equal(map.previousZoom);
        done();
      });
      map.leafletMap.setZoom(before + 1, { animate: false });
    });

    it("stores previous zoom when zooming out", (done) => {
      const before = map.leafletMap.getZoom();
      map.leafletMap.on("zoomend", () => {
        expect(before).to.equal(map.previousZoom);
        done();
      });
      map.leafletMap.setZoom(before - 1, { animate: false });
    });
  });

  describe("onZoomEnd", () => {
    let map;

    beforeEach(() => {
      document.querySelector("body").append(mapDiv);
      map = new SlippyMap("map");
      // start tests with markers visible
      map.leafletMap.setZoom(map.minZoomWithMarkers, { animate: false });
    });

    afterEach(() => {
      map.leafletMap.remove();
      mapDiv.remove();
    });

    it("triggers mapZoomNoMarkers", (done) => {
      map.leafletMap.setZoom(map.minZoomWithMarkers, { animate: false });
      const callDone = () => done();
      document.addEventListener("mapZoomNoMarkers", callDone);
      map.leafletMap.setZoom(map.minZoomWithMarkers - 1, { animate: false });
      document.removeEventListener("mapZoomNoMarkers", callDone);
    });

    it("doesn't trigger unnecessary mapZoomNoMarkers", (done) => {
      const callDone = () => done();
      // mocha checks for double done
      document.addEventListener("mapZoomNoMarkers", callDone);
      // should only trigger on next line
      map.leafletMap.setZoom(map.minZoomWithMarkers - 1, { animate: false });
      // shouldn't trigger when markers already hidden
      map.leafletMap.setZoom(map.minZoomWithMarkers - 2, { animate: false });
      map.leafletMap.setZoom(map.minZoomWithMarkers - 1, { animate: false });
      // shouldn't trigger when markers visible again
      map.leafletMap.setZoom(map.minZoomWithMarkers, { animate: false });
      document.removeEventListener("mapZoomNoMarkers", callDone);
    });

    it("triggers mapZoomMarkersVisible", (done) => {
      map.leafletMap.setZoom(map.minZoomWithMarkers - 1, { animate: false });
      const callDone = () => done();
      document.addEventListener("mapZoomMarkersVisible", callDone);
      map.leafletMap.setZoom(map.minZoomWithMarkers, { animate: false });
      document.removeEventListener("mapZoomMarkersVisible", callDone);
    });

    it("doesn't trigger unnecessary mapZoomMarkersVisible", (done) => {
      map.leafletMap.setZoom(map.minZoomWithMarkers - 1, { animate: false });
      const callDone = () => done();
      // mocha checks for double done
      document.addEventListener("mapZoomMarkersVisible", callDone);
      // should only trigger on next line
      map.leafletMap.setZoom(map.minZoomWithMarkers, { animate: false });
      // shouldn't trigger when markers already visible
      map.leafletMap.setZoom(map.minZoomWithMarkers + 1, { animate: false });
      map.leafletMap.setZoom(map.minZoomWithMarkers, { animate: false });
      // shouldn't trigger when markers hidden again
      map.leafletMap.setZoom(map.minZoomWithMarkers - 1, { animate: false });
      document.removeEventListener("mapZoomMarkersVisible", callDone);
    });
  });
});
