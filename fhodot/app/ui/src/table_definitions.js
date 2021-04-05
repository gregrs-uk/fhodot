/**
 * Defines the specific Table(s) to be used by each DataSource
 */

import Table from "./lib/table";
import TableGroup from "./lib/table_group";
import {
  createElementWith,
  getValueOrPlaceholder,
  getFSAURL,
  getOSMURL,
  getJOSMLoadURL,
  getIDEditURL,
  openJOSMURL,
} from "./lib/utils";

export const tableGroup = new TableGroup("tables");

/**
 * Get HTML string for link with target _blank
 */
const getLink = (text, url) => `<a href="${url}" target="_blank">${text}</a>`;

/**
 * Return a <td> containing JOSM/iD edit actions
 */
const getEditCell = (osmType, osmIDByType) => {
  const josmLoadURL = getJOSMLoadURL(osmType, osmIDByType);
  const idEditURL = getIDEditURL(osmType, osmIDByType);

  const cell = createElementWith(
    "td", `<span class="action">JOSM</span> / ${getLink("iD", idEditURL)}`,
  );
  cell.querySelector("span.action")
    .addEventListener("click", () => openJOSMURL(josmLoadURL));

  return cell;
};

/**
 * Return the name and mismatched FHRS IDs for an OSM feature
 */
const getMismatchRow = (feature) => {
  const {
    osmType, osmIDByType, fhrsMappings, name,
  } = feature.properties;

  return {
    name: getLink(
      getValueOrPlaceholder(name), getOSMURL(osmType, osmIDByType),
    ),
    fhrsIDs: fhrsMappings.filter(
      // true if FHRS ID doesn't match an establishment
      (fhrsMapping) => !("fhrsEstablishment" in fhrsMapping),
    ).map((fhrsMapping) => fhrsMapping.fhrsID).join(", "),
    edit: getEditCell(osmType, osmIDByType),
  };
};

/**
 * Table of OSM objects with incorrect FHRS IDs
 */
export const mismatchesTable = new Table({
  tableGroup,
  elementID: "mismatches",
  heading: "OSM objects with incorrect FHRS IDs",
  preTableMsg: `The following OSM objects have FHRS IDs (set using the
    <code>fhrs:id</code> tag) that do not match an establishment in the FSA
    data. This often indicates that the establishment has closed, but please
    check before making any changes to the OSM data.`,
  emptyTableMsg: `No OSM objects with incorrect FHRS IDs found on map`,
  definition: new Map([
    ["OSM <code>name</code>", "name"],
    ["Incorrect FHRS ID(s)", "fhrsIDs"],
    ["Edit", "edit"],
  ]),
  getProperties: (data) => {
    const results = [];
    data.features.forEach((feature) => {
      if (feature.properties.numMismatchedFHRSIDs) {
        results.push(getMismatchRow(feature));
      }
    });
    return results;
  },
});

/**
 * Return the details of a postcode difference for a matched OSM object
 */
const getPostcodeDifferencesRowOSM = (feature, fhrsMapping) => {
  const {
    name: osmName, osmType, osmIDByType, postcode: osmPostcode,
  } = feature.properties;
  const { fhrsID } = fhrsMapping;
  const {
    name: fhrsName, postcode: fhrsPostcode,
  } = fhrsMapping.fhrsEstablishment;

  return {
    osmName: getLink(
      getValueOrPlaceholder(osmName), getOSMURL(osmType, osmIDByType),
    ),
    fhrsName: getLink(
      getValueOrPlaceholder(fhrsName), getFSAURL(fhrsID),
    ),
    osmPostcode: getValueOrPlaceholder(osmPostcode),
    fhrsPostcode: getValueOrPlaceholder(fhrsPostcode),
    edit: getEditCell(osmType, osmIDByType),
  };
};

/**
 * Table of OSM objects with a different postcode to their FHRS match
 */
export const osmPostcodeDifferencesTable = new Table({
  tableGroup,
  elementID: "postcode-differences",
  heading: "Matched OSM objects with missing/different postcodes",
  preTableMsg: `The following OSM objects have been matched to an FHRS
    establishment (using the <code>fhrs:id</code> tag) but their
    <code>addr:postcode</code> is missing or different from the postcode
    indicated in the FSA data. N.B. This does not necessarily indicate an error
    with the OSM data. To indicate that the postcode is incorrect in the FSA
    data, a <code>not:addr:postcode</code> can be added to the OSM object,
    which will also remove it from this table.`,
  emptyTableMsg: `No matched OSM objects with missing/different postcodes found
    on map`,
  definition: new Map([
    ["OSM <code>name</code>", "osmName"],
    ["OSM <code>addr:postcode</code>", "osmPostcode"],
    ["FHRS establishment name", "fhrsName"],
    ["FHRS postcode", "fhrsPostcode"],
    ["Edit", "edit"],
  ]),
  getProperties: (data) => {
    const results = [];
    data.features.forEach((feature) => {
      feature.properties.fhrsMappings.forEach((fhrsMapping) => {
        if (fhrsMapping.postcodesMatch === false) {
          results.push(
            getPostcodeDifferencesRowOSM(feature, fhrsMapping),
          );
        }
      });
    });
    return results;
  },
});

/**
 * Return details of postcode difference for matched FHRS establishment
 */
const getPostcodeDifferencesRowFHRS = (feature, osmMapping) => {
  const {
    fhrsID, name: fhrsName, postcode: fhrsPostcode,
  } = feature.properties;
  const {
    name: osmName, osmType, osmIDByType, postcode: osmPostcode,
  } = osmMapping.osmObject;

  return {
    fhrsName: getLink(getValueOrPlaceholder(fhrsName), getFSAURL(fhrsID)),
    osmName: getLink(
      getValueOrPlaceholder(osmName), getOSMURL(osmType, osmIDByType),
    ),
    fhrsPostcode: getValueOrPlaceholder(fhrsPostcode),
    osmPostcode: getValueOrPlaceholder(osmPostcode),
    edit: getEditCell(osmType, osmIDByType),
  };
};

/**
 * Table of FHRS establishments with different postcode to OSM match
 */
export const fhrsPostcodeDifferencesTable = new Table({
  tableGroup,
  elementID: "postcode-differences",
  heading: "Matched FHRS establishments with missing/different postcodes",
  preTableMsg: `The following FHRS establishments have been matched to an OSM
    object (using the <code>fhrs:id</code> tag) but the OSM object's
    <code>addr:postcode</code> is missing or different from the postcode
    indicated in the FSA data. N.B. This does not necessarily indicate an error
    with the OSM data. To indicate that the postcode is incorrect in the FSA
    data, a <code>not:addr:postcode</code> can be added to the OSM object,
    which will also remove it from this table.`,
  emptyTableMsg: `No matched FHRS establishments with missing/different
    postcodes found on map`,
  definition: new Map([
    ["FHRS establishment name", "fhrsName"],
    ["FHRS postcode", "fhrsPostcode"],
    ["OSM <code>name</code>", "osmName"],
    ["OSM <code>addr:postcode</code>", "osmPostcode"],
    ["Edit", "edit"],
  ]),
  getProperties: (data) => {
    const results = [];
    data.features.forEach((feature) => {
      feature.properties.osmMappings.forEach((osmMapping) => {
        if (osmMapping.postcodesMatch === false) {
          results.push(
            getPostcodeDifferencesRowFHRS(feature, osmMapping),
          );
        }
      });
    });
    return results;
  },
});
