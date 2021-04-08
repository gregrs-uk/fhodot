/**
 * Functions for styling markers based on the data they represent
 */

import { divIcon, point } from "leaflet";

/**
 * Create appropriate divIcon for a cluster
 *
 * If there is at least one mismatched FHRS ID or postcode, use 'bad'
 * CSS class. If there are no mismatched but at least one unmatched, use
 * 'unmatched' CSS class. Otherwise use 'matched' CSS class. If cluster
 * contains selected feature, also use 'selected' CSS class.
 */
export const createClusterIcon = (cluster, dataSource) => {
  let clusterClassAddOn = "matched";
  let clusterContainsSelectedFeature = false;

  cluster.getAllChildMarkers().forEach((childMarker) => {
    const {
      badFHRSIDsString,
      numMismatchedFHRSIDs,
      numMatchesDifferentPostcodes,
      numMatchesSamePostcodes,
    } = childMarker.feature.properties;
    const { selectedFeatureID, getFeatureID } = dataSource;

    if (selectedFeatureID === getFeatureID(childMarker.feature)) {
      clusterContainsSelectedFeature = true;
    }

    if (badFHRSIDsString || numMismatchedFHRSIDs > 0
        || numMatchesDifferentPostcodes > 0) {
      clusterClassAddOn = "bad";
    } else if (numMatchesSamePostcodes === 0 && clusterClassAddOn !== "bad") {
      clusterClassAddOn = "unmatched";
    }
  });

  if (clusterContainsSelectedFeature) clusterClassAddOn += " selected";

  return divIcon({
    html: "<div><span>+</span></div>",
    className: `marker-cluster ${clusterClassAddOn}`,
    iconSize: point(12, 12),
  });
};

/**
 * Returns default style for a circle marker
 *
 * Defined as a function rather than object to avoid the object being
 * modified elsewhere with unintended consequences.
 */
export const getDefaultCircleMarkerStyle = () => ({
  radius: 8,
  color: "black",
  weight: 1,
  fillOpacity: 0.75,
});

/**
 * Returns default style for a highlighted circle marker
 *
 * Defined as a function rather than object to avoid the object being
 * modified elsewhere with unintended consequences.
 */
export const getHighlightedCircleMarkerStyle = () => ({
  radius: 10.5,
  color: "rgb(255, 255, 127)",
  weight: 6,
  fillOpacity: 1,
});

/**
 * Style a marker based on feature data
 */
export const styleMarker = (feature, dataSource) => {
  const {
    badFHRSIDsString,
    numMismatchedFHRSIDs,
    numMatchesDifferentPostcodes,
    numMatchesSamePostcodes,
  } = feature.properties;
  const { selectedFeatureID, getFeatureID } = dataSource;

  // highlight marker if feature selected before map move
  const styles = (selectedFeatureID
                  && selectedFeatureID === getFeatureID(feature))
    ? getHighlightedCircleMarkerStyle()
    : getDefaultCircleMarkerStyle();

  // colour palette from hclwizard.org
  // qualitative, n: 3, h: 0-230, c: 100, l: 75
  if (badFHRSIDsString || numMismatchedFHRSIDs > 0
      || numMatchesDifferentPostcodes > 0) {
    styles.fillColor = "rgb(255, 137, 172)";
  } else if (numMatchesSamePostcodes > 0) {
    styles.fillColor = "rgb(122, 206, 0)";
  } else {
    styles.fillColor = "rgb(0, 203, 255)";
  }
  return styles;
};
