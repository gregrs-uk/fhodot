import { expect } from "chai";
import { DivIcon } from "leaflet";
import { describe, it, beforeEach } from "mocha";
import { stub } from "sinon";

import { createClusterIcon, styleMarker } from "./marker_styling";

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

  describe("createClusterIcon", () => {
    const clusterMock = {};

    beforeEach(() => {
      clusterMock.getAllChildMarkers = stub();
    });

    /**
     * Test template
     */
    const expectCSSClassFromChildMarkers = (childMarkersMock, cssClass) => {
      clusterMock.getAllChildMarkers.onFirstCall().returns(childMarkersMock);
      const icon = createClusterIcon(clusterMock);
      expect(icon).to.be.instanceOf(DivIcon);
      expect(icon.options.className).to.equal(`marker-cluster ${cssClass}`);
    };

    it("CSS class 'bad' when cluster contains an ID mismatch", () => {
      const childMarkersMock = [
        markerWithMatchSamePostcode,
        markerWithNoMappings,
        markerWithMismatchedFHRSID, // bad
      ];
      expectCSSClassFromChildMarkers(childMarkersMock, "bad");
    });

    it("CSS class 'bad' when cluster contains a postcode mismatch", () => {
      const childMarkersMock = [
        markerWithMatchSamePostcode,
        markerWithNoMappings,
        markerWithMatchDifferentPostcodes, // bad
      ];
      expectCSSClassFromChildMarkers(childMarkersMock, "bad");
    });

    it("CSS class 'unmatched' when cluster contains unmatched", () => {
      const childMarkersMock = [
        markerWithMatchSamePostcode,
        markerWithNoMappings, // unmatched
      ];
      expectCSSClassFromChildMarkers(childMarkersMock, "unmatched");
    });

    it("CSS class 'matched' when cluster contains only matched", () => {
      const childMarkersMock = [
        markerWithMatchSamePostcode,
      ];
      expectCSSClassFromChildMarkers(childMarkersMock, "matched");
    });
  });

  describe("styleMarker", () => {
    it("styles marker pink when it contains an ID mismatch", () => {
      const styles = styleMarker(markerWithMismatchedFHRSID.feature);
      expect(styles.fillColor).to.equal("rgb(255, 137, 172)");
    });

    it("styles marker pink when it contains a postcode mismatch", () => {
      const styles = styleMarker(
        markerWithMatchDifferentPostcodes.feature,
      );
      expect(styles.fillColor).to.equal("rgb(255, 137, 172)");
    });

    it("styles marker blue when it is unmatched", () => {
      const styles = styleMarker(markerWithNoMappings.feature);
      expect(styles.fillColor).to.equal("rgb(0, 203, 255)");
    });

    it("styles marker green when it is matched (only) successfully", () => {
      const styles = styleMarker(markerWithMatchSamePostcode.feature);
      expect(styles.fillColor).to.equal("rgb(122, 206, 0)");
    });
  });
});
