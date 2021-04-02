import { expect } from "chai";
import {
  describe, it, beforeEach, afterEach,
} from "mocha";

import DataCollection from "./data_collection";
import DataSource from "./data_source";
import SlippyMap from "./slippy_map";

describe("DataCollection", () => {
  const dataCollection = new DataCollection([
    new DataSource({
      name: "one",
      type: "fhrs",
    }),
    new DataSource({
      name: "two",
      type: "osm",
    }),
  ]);

  describe("constructor", () => {
    it("throws an error if the argument supplied is not an array", () => {
      expect(() => new DataCollection("not an array")).to.throw();
    });
  });

  describe("getCurrentDataSource", () => {
    const mapDiv = document.createElement("div");
    mapDiv.id = "map";
    let map;

    beforeEach(() => {
      document.querySelector("body").append(mapDiv);
      map = new SlippyMap("map");
    });

    afterEach(() => {
      map.leafletMap.remove();
      mapDiv.remove();
    });

    it("returns the currently enabled data source", () => {
      dataCollection.dataSources[1].addLayerGroupTo(map);
      expect(dataCollection.getCurrentDataSource(map))
        .to.equal(dataCollection.dataSources[1]);
    });

    it("throws an error if no data source is enabled", () => {
      // pass function to expect rather than its result
      expect(() => dataCollection.getCurrentDataSource(map)).to.throw();
    });
  });

  describe("getDataSourceByName", () => {
    it("returns the correct data source by name", () => {
      expect(dataCollection.getDataSourceByName("one"))
        .to.equal(dataCollection.dataSources[0]);
      expect(dataCollection.getDataSourceByName("two"))
        .to.equal(dataCollection.dataSources[1]);
    });

    it("returns null if name doesn't match a data source", () => {
      expect(dataCollection.getDataSourceByName("three")).to.equal(null);
    });
  });
});
