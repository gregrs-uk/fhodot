import { expect } from "chai";
import { DivIcon } from "leaflet";
import { describe, it, beforeEach } from "mocha";
import { stub } from "sinon";

import {
  createClusterIcon, styleMarker, getHighlightedCircleMarkerStyle,
} from "./marker_styling";

describe("Marker styling", () => {
  // create example markers (each a single object/establishment)
  const markerWithMismatchedFHRSID = Object.freeze({
    feature: {
      properties: {
        numMismatchedFHRSIDs: 1,
        numMatchesDifferentPostcodes: 0,
        numMatchesSamePostcodes: 1,
      },
    },
  });
  const markerWithMatchDifferentPostcodes = Object.freeze({
    feature: {
      properties: {
        numMismatchedFHRSIDs: 0,
        numMatchesDifferentPostcodes: 1,
        numMatchesSamePostcodes: 1,
      },
    },
  });
  const markerWithNoMappings = Object.freeze({
    feature: {
      properties: {
        numMismatchedFHRSIDs: 0,
        numMatchesDifferentPostcodes: 0,
        numMatchesSamePostcodes: 0,
      },
    },
  });
  const markerWithMatchSamePostcode = Object.freeze({
    feature: {
      properties: {
        numMismatchedFHRSIDs: 0,
        numMatchesDifferentPostcodes: 0,
        numMatchesSamePostcodes: 1,
      },
    },
  });
  const markerWithNoMappingsWithID = Object.freeze({
    feature: {
      properties: {
        numMismatchedFHRSIDs: 0,
        numMatchesDifferentPostcodes: 0,
        numMatchesSamePostcodes: 0,
        id: 123,
      },
    },
  });

  // create example DataSources
  const dataSourceWithoutSelectedFeature = Object.freeze({
    selectedFeatureID: null,
    getFeatureID: () => 1,
  });
  const dataSourceWithSelectedFeature = Object.freeze({
    selectedFeatureID: 123,
    getFeatureID: (feature) => feature.properties.id,
  });

  describe("createClusterIcon", () => {
    const clusterMock = {};

    beforeEach(() => {
      clusterMock.getAllChildMarkers = stub();
    });

    /**
     * Test template
     */
    const expectCSSClassFromChildMarkers = (
      childMarkersMock,
      cssClass,
      dataSource = dataSourceWithoutSelectedFeature,
    ) => {
      clusterMock.getAllChildMarkers.onFirstCall().returns(childMarkersMock);
      const icon = createClusterIcon(clusterMock, dataSource);
      expect(icon).to.be.instanceOf(DivIcon);
      expect(icon.options.className).to.equal(`marker-cluster ${cssClass}`);
    };

    it("CSS class 'bad' when cluster contains an ID mismatch", () => {
      const childMarkersMock = [
        markerWithMismatchedFHRSID, // bad
        markerWithNoMappings,
        markerWithMatchSamePostcode,
      ];
      expectCSSClassFromChildMarkers(childMarkersMock, "bad");
    });

    it("CSS class 'bad' when cluster contains a postcode mismatch", () => {
      const childMarkersMock = [
        markerWithMatchDifferentPostcodes, // bad
        markerWithNoMappings,
        markerWithMatchSamePostcode,
      ];
      expectCSSClassFromChildMarkers(childMarkersMock, "bad");
    });

    it("CSS class 'unmatched' when cluster contains unmatched", () => {
      const childMarkersMock = [
        markerWithNoMappings, // unmatched
        markerWithMatchSamePostcode,
      ];
      expectCSSClassFromChildMarkers(childMarkersMock, "unmatched");
    });

    it("CSS class 'matched' when cluster contains only matched", () => {
      const childMarkersMock = [markerWithMatchSamePostcode];
      expectCSSClassFromChildMarkers(childMarkersMock, "matched");
    });

    it("CSS class 'selected' when cluster contains selected feature", () => {
      const childMarkersMock = [markerWithNoMappingsWithID];
      expectCSSClassFromChildMarkers(
        childMarkersMock, "unmatched selected", dataSourceWithSelectedFeature,
      );
    });
  });

  describe("styleMarker", () => {
    it("styles marker pink when it contains an ID mismatch", () => {
      const styles = styleMarker(
        markerWithMismatchedFHRSID.feature, dataSourceWithoutSelectedFeature,
      );
      expect(styles.fillColor).to.equal("rgb(255, 137, 172)");
    });

    it("styles marker pink when it contains a postcode mismatch", () => {
      const styles = styleMarker(
        markerWithMatchDifferentPostcodes.feature,
        dataSourceWithoutSelectedFeature,
      );
      expect(styles.fillColor).to.equal("rgb(255, 137, 172)");
    });

    it("styles marker blue when it is unmatched", () => {
      const styles = styleMarker(
        markerWithNoMappings.feature, dataSourceWithoutSelectedFeature,
      );
      expect(styles.fillColor).to.equal("rgb(0, 203, 255)");
    });

    it("styles marker green when it is matched (only) successfully", () => {
      const styles = styleMarker(
        markerWithMatchSamePostcode.feature, dataSourceWithoutSelectedFeature,
      );
      expect(styles.fillColor).to.equal("rgb(122, 206, 0)");
    });

    it("styles marker appropriately when feature is selected", () => {
      const styles = styleMarker(
        markerWithNoMappingsWithID.feature, dataSourceWithSelectedFeature,
      );
      const correctStyle = getHighlightedCircleMarkerStyle();
      Object.keys(correctStyle).forEach((key) => {
        expect(styles[key]).to.equal(correctStyle[key]);
      });
    });
  });
});
