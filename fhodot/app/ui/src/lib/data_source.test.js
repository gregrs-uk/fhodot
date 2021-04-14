/* eslint-disable no-unused-expressions */

import { expect, use } from "chai";
import {
  circleMarker, CircleMarker, FeatureGroup, geoJSON, GeoJSON, LayerGroup,
} from "leaflet";
import { MarkerClusterGroup } from "leaflet.markercluster";
import {
  describe, it, beforeEach, afterEach,
} from "mocha";
import { spy, stub } from "sinon";
import sinonChai from "sinon-chai";

import DataSource from "./data_source";
import SlippyMap from "./slippy_map";

use(sinonChai);

describe("DataSource", () => {
  const mapDiv = document.createElement("div");
  mapDiv.id = "map";

  describe("constructor", () => {
    let dataSource;

    beforeEach(() => {
      dataSource = new DataSource({ type: "osm" });
    });

    describe("pointLayer", () => {
      it("is a MarkerClusterGroup", () => {
        expect(dataSource.pointLayer).to.be.an.instanceOf(MarkerClusterGroup);
      });
    });

    describe("layerGroup", () => {
      it("is a LayerGroup", () => {
        expect(dataSource.layerGroup).to.be.an.instanceOf(LayerGroup);
      });
    });
  });

  describe("isEnabled", () => {
    let map;
    let dataSource;

    beforeEach(() => {
      document.querySelector("body").append(mapDiv);
      map = new SlippyMap("map");
      dataSource = new DataSource({ type: "osm" });
    });

    afterEach(() => {
      map.leafletMap.remove();
      mapDiv.remove();
    });

    it("is true if layer group is added to map", () => {
      dataSource.addLayerGroupTo(map);
      expect(dataSource.isEnabled(map)).to.equal(true);
    });

    it("is false if layer group is never added to map", () => {
      expect(dataSource.isEnabled(map)).to.equal(false);
    });

    it("is false if layer group is added to then removed from map", () => {
      dataSource.addLayerGroupTo(map);
      map.leafletMap.removeLayer(dataSource.layerGroup);
      expect(dataSource.isEnabled(map)).to.equal(false);
    });
  });

  describe("refresh", () => {
    let map;
    let dataSource;
    const fetchStub = stub(window, "fetch");
    fetchStub.returns(
      Promise.resolve({ json: () => Promise.resolve("data argument") }),
    );

    beforeEach(() => {
      // create map
      document.querySelector("body").append(mapDiv);
      map = new SlippyMap("map");

      dataSource = new DataSource({
        type: "osm",
        jsonURL: "http://example.org",
      });

      // add markers to pointLayer
      const point = {
        type: "Feature",
        geometry: { type: "Point", coordinates: [1, 52] },
      };
      const featureCollection = {
        type: "FeatureCollection",
        features: [point, point],
      };
      const markers = geoJSON(featureCollection, {
        pointToLayer: (feature, latlng) => circleMarker(latlng, {}),
      });
      dataSource.pointLayer.addLayer(markers);

      dataSource.addLayerGroupTo(map);
      expect(dataSource.isEnabled(map)).to.equal(true);
      // start with markers visible
      map.leafletMap.setZoom(map.minZoomWithMarkers, { animate: false });
    });

    afterEach(() => {
      map.leafletMap.remove();
      mapDiv.remove();
      fetchStub.resetHistory(); // forget calls but not behaviour
    });

    it("clears pointLayer at low zoom", () => {
      map.leafletMap.setZoom(map.minZoomWithMarkers - 1, { animate: false });
      dataSource.refresh(map);
      expect(dataSource.isEnabled(map)).to.equal(true);
      expect(dataSource.layerGroup.hasLayer(dataSource.pointLayer))
        .to.be.false;
      expect(map.leafletMap.hasLayer(dataSource.pointLayer)).to.be.false;
      expect(fetchStub).not.to.have.been.called;
    });

    it("calls fetch", () => {
      dataSource.refresh(map);
      expect(fetchStub).to.have.been.calledOnce;
    });
  });

  describe("replaceMarkersLines", () => {
    let map;
    let dataSource;
    let markers;
    const feature = {
      type: "Feature",
      geometry: { type: "Point", coordinates: [1, 52] },
      properties: {},
    };

    beforeEach(() => {
      // create map
      document.querySelector("body").append(mapDiv);
      map = new SlippyMap("map");

      dataSource = new DataSource({
        type: "osm",
        markerClickFunction: spy(),
      });
      dataSource.replaceMarkersLines({
        type: "FeatureCollection",
        features: [feature, feature, feature], // 3 features
      });
      dataSource.addLayerGroupTo(map);

      // Oddly, pointLayer.getLayers() returns array of CircleMarkers in
      // tests.html but returns array containing parent GeoJSON layer
      // when tests are run using Karma
      const layers = dataSource.pointLayer.getLayers();
      if (layers[0] instanceof GeoJSON) {
        markers = layers[0].getLayers(); // Karma
      } else {
        markers = layers; // tests.html
      }
    });

    afterEach(() => {
      map.leafletMap.remove();
      mapDiv.remove();
    });

    it("adds CircleMarkers to pointLayer", () => {
      expect(markers).to.be.an("array").of.length(3);
      expect(markers[0]).to.be.an.instanceof(CircleMarker);
    });

    it("clears existing markers to avoid duplication", () => {
      dataSource.replaceMarkersLines({
        type: "FeatureCollection",
        features: [feature, feature], // 2 features
      });
      const layers = dataSource.pointLayer.getLayers();
      if (layers[0] instanceof GeoJSON) {
        expect(layers[0].getLayers()).to.be.an("array").of.length(2); // Karma
      } else {
        expect(layers).to.be.an("array").of.length(2); // tests.html
      }
    });

    it("binds on click function to markers", () => {
      // simulate clicking a marker
      markers[0].fire("click", {}, true); // propagate
      expect(dataSource.markerClickFunction).to.have.been.called;
    });
  });
});
