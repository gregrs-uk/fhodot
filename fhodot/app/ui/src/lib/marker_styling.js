/**
 * Functions for styling markers based on the data they represent
 */

import { divIcon, point } from "leaflet";

import { getFeatureStatus } from "./utils";

/**
 * Create appropriate divIcon for a cluster
 *
 * If there is at least one mismatched FHRS ID or postcode, use 'bad'
 * CSS class. If there are no mismatched but at least one unmatched, use
 * 'unmatched' CSS class. Otherwise use 'matched' CSS class. If cluster
 * contains selected feature, also use 'selected' CSS class.
 */
export const createClusterIcon = (cluster, dataSource) => {
  const childMarkers = cluster.getAllChildMarkers();

  let clusterClassAddOn = "matched";
  childMarkers.some((marker) => {
    const status = getFeatureStatus(marker.feature);
    if (status === "bad") {
      clusterClassAddOn = "bad";
      return true; // stop iterating
    }
    if (status === "unmatched") clusterClassAddOn = "unmatched";
    return false; // continue iterating
  });

  const { selectedFeatureID, getFeatureID } = dataSource;
  if (selectedFeatureID && childMarkers.find((childMarker) => (
    selectedFeatureID === getFeatureID(childMarker.feature)
  ))) clusterClassAddOn += " selected";

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
export const styleMarker = (feature, dataSource = null) => {
  let styles;

  if (dataSource) {
    const { selectedFeatureID, getFeatureID } = dataSource;
    styles = (selectedFeatureID === getFeatureID(feature))
      ? getHighlightedCircleMarkerStyle()
      : getDefaultCircleMarkerStyle();
  } else {
    styles = getDefaultCircleMarkerStyle();
  }

  // colour palette from hclwizard.org
  // qualitative, n: 3, h: 0-230, c: 100, l: 75
  const colours = {
    bad: "rgb(255, 137, 172)",
    matched: "rgb(122, 206, 0)",
    unmatched: "rgb(0, 203, 255)",
  };
  styles.fillColor = colours[getFeatureStatus(feature)];

  return styles;
};
