/**
 * Functions for styling markers based on the data they represent
 */

import { divIcon, point } from "leaflet";

/**
 * Create appropriate divIcon for a cluster
 *
 * If there is at least one mismatched FHRS ID or postcode, use 'bad' CSS
 * class. If there are no mismatched but at least one unmatched, use
 * 'unmatched' CSS class. Otherwise use 'matched' CSS class.
 */
export const createClusterIcon = (cluster) => {
  let clusterClassAddOn = "matched";
  cluster.getAllChildMarkers().some((childMarker) => {
    const {
      badFHRSIDsString,
      numMismatchedFHRSIDs,
      numMatchesDifferentPostcodes,
      numMatchesSamePostcodes,
    } = childMarker.feature.properties;

    if (badFHRSIDsString || numMismatchedFHRSIDs > 0
        || numMatchesDifferentPostcodes > 0) {
      clusterClassAddOn = "bad";
      return true; // stop iterating
    }
    if (numMatchesSamePostcodes === 0) {
      clusterClassAddOn = "unmatched";
    }
    return false; // continue iterating
  });

  return divIcon({
    html: "<div><span>+</span></div>",
    className: `marker-cluster ${clusterClassAddOn}`,
    iconSize: point(12, 12),
  });
};

/**
 * Style a marker based on feature data
 */
export const styleMarker = (feature) => {
  const styles = {
    radius: 8,
    color: "black",
    weight: 1,
    fillOpacity: 0.75,
  };
  const {
    badFHRSIDsString,
    numMismatchedFHRSIDs,
    numMatchesDifferentPostcodes,
    numMatchesSamePostcodes,
  } = feature.properties;

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
