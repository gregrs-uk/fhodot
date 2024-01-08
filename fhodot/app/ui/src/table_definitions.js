/**
 * Defines the specific Table(s) to be used by each DataSource
 */

import Table from "./lib/table";
import TableGroup from "./lib/table_group";
import {
  createElementWith,
  getFeatureStatus,
  getValueOrPlaceholder,
  getFSAURL,
  getOSMURL,
  getJOSMLoadURL,
  getIDEditURL,
  openJOSMURL,
  getJOSMAddFHRSIDTagURL,
  bindJOSMAction,
} from "./lib/utils";

export const tableGroup = new TableGroup("tables");

/**
 * Get HTML string for link with target _blank
 */
const getLink = (text, url) => `<a href="${url}" target="_blank">${text}</a>`;

/**
 * Return a <td> containing JOSM/iD edit actions
 */
const getEditActionsCell = (osmType, osmIDByType) => {
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
 * Return a <td> containing map select/zoom actions
 */
const getMapActionsCell = (feature) => {
  const selectSpan = createElementWith("span", "Select", "action");
  selectSpan.addEventListener("click", () => {
    const event = new CustomEvent("requestSelect", { detail: feature });
    document.dispatchEvent(event);
  });

  const zoomSpan = createElementWith("span", "Select & zoom", "action");
  zoomSpan.addEventListener("click", () => {
    const event = new CustomEvent("requestSelectAndZoom", { detail: feature });
    document.dispatchEvent(event);
  });

  const cell = document.createElement("td");
  cell.append(selectSpan, " / ", zoomSpan);
  return cell;
};

/**
 * Return the name and mismatched FHRS IDs for an OSM feature
 */
const getMismatchRow = (feature) => {
  const {
    osmType, osmIDByType, name, fhrsMappings, postcode,
  } = feature.properties;

  return {
    name: getLink(
      getValueOrPlaceholder(name), getOSMURL(osmType, osmIDByType),
    ),
    fhrsIDs: fhrsMappings.filter(
      // true if FHRS ID doesn't match an establishment
      (fhrsMapping) => !("fhrsEstablishment" in fhrsMapping),
    ).map((fhrsMapping) => fhrsMapping.fhrsID).join(", "),
    postcode,
    editActions: getEditActionsCell(osmType, osmIDByType),
    mapActions: getMapActionsCell(feature),
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
    ["OSM <code>addr:postcode</code>", "postcode"],
    ["Edit", "editActions"],
    ["On map above", "mapActions"],
  ]),
  getProperties: (data) => (
    data.features
      .filter((feature) => feature.properties.numMismatchedFHRSIDs)
      .map(getMismatchRow)
  ),
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
    editActions: getEditActionsCell(osmType, osmIDByType),
    mapActions: getMapActionsCell(feature),
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
    ["Edit", "editActions"],
    ["On map above", "mapActions"],
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
    editActions: getEditActionsCell(osmType, osmIDByType),
    mapActions: getMapActionsCell(feature),
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
    ["Edit", "editActions"],
    ["On map above", "mapActions"],
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

/**
 * Return details of unmatched FHRS establishment
 */
const getFHRSUnmatchedRow = (feature) => {
  const row = feature.properties;

  const { fhrsID, name } = row;
  const nameLink = getLink(getValueOrPlaceholder(name), getFSAURL(fhrsID));
  row.nameCell = createElementWith("td", nameLink);
  row.nameCell.className = getFeatureStatus(feature);

  row.mapActions = getMapActionsCell(feature);

  return row;
};

/**
 * Table of unmatched FHRS establishments
 */
export const fhrsUnmatchedTable = new Table({
  tableGroup,
  elementID: "unmatched",
  heading: "Unmatched FHRS establishments with a location",
  preTableMsg: `The following FHRS establishments with a location have
    not been matched to an OSM object using the <code>fhrs:id</code>
    tag.`,
  emptyTableMsg: "No unmatched FHRS establishments found on map",
  definition: new Map([
    ["FHRS establishment name", "nameCell"],
    ["FHRS postcode", "postcode"],
    ["On map above", "mapActions"],
  ]),
  getProperties: (data) => (
    data.features.filter((feature) => {
      const {
        numMatchesSamePostcodes, numMatchesDifferentPostcodes,
      } = feature.properties;
      const matches = numMatchesSamePostcodes + numMatchesDifferentPostcodes;
      return feature.geometry && matches === 0;
    }).map(getFHRSUnmatchedRow)
  ),
});

/**
 * Return details of unmatched OSM object
 */
const getOSMUnmatchedRow = (feature) => {
  const {
    osmType, osmIDByType, name, postcode,
  } = feature.properties;

  const nameLink = getLink(
    getValueOrPlaceholder(name), getOSMURL(osmType, osmIDByType),
  );
  const nameCell = createElementWith("td", nameLink);
  nameCell.className = getFeatureStatus(feature);

  return {
    nameCell,
    postcode,
    editActions: getEditActionsCell(osmType, osmIDByType),
    mapActions: getMapActionsCell(feature),
  };
};

/**
 * Table of unmatched FHRS establishments
 */
export const osmUnmatchedTable = new Table({
  tableGroup,
  elementID: "unmatched",
  heading: "Unmatched OSM objects",
  preTableMsg: `The following OSM objects have not been successfully
    matched to an FHRS establishment using a valid <code>fhrs:id</code>.
    Objects with neither a name nor postcode are not shown in this table,
    but are shown on the map above.`,
  emptyTableMsg: "No unmatched OSM objects found on map",
  definition: new Map([
    ["OSM object name", "nameCell"],
    ["OSM <code>addr:postcode</code>", "postcode"],
    ["Edit", "editActions"],
    ["On map above", "mapActions"],
  ]),
  getProperties: (data) => (
    data.features.filter((feature) => {
      const {
        name, numMatchesSamePostcodes, numMatchesDifferentPostcodes, postcode,
      } = feature.properties;
      const unmatched = (
        numMatchesSamePostcodes + numMatchesDifferentPostcodes === 0
      );
      const containsNameOrPostcode = name || postcode;
      return unmatched && containsNameOrPostcode;
    }).map(getOSMUnmatchedRow)
  ),
});

/**
 * Return details of FHRS establishment without location
 */
const getFHRSNoLocationRow = (feature) => {
  const row = feature.properties;

  const { fhrsID, name } = row;
  const nameLink = getLink(getValueOrPlaceholder(name), getFSAURL(fhrsID));
  row.nameCell = createElementWith("td", nameLink);
  row.nameCell.className = getFeatureStatus(feature);

  row.address = [row.address1, row.address2, row.address3, row.address4]
    .filter((line) => line)
    .join(", ");

  const showInfoSpan = createElementWith("span", "Show info", "action");
  showInfoSpan.addEventListener("click", () => {
    const event = new CustomEvent("requestInspectorUpdateFHRS", {
      detail: feature,
    });
    document.dispatchEvent(event);
  });
  row.showInfoCell = document.createElement("td");
  row.showInfoCell.append(showInfoSpan);

  return row;
};

/**
 * Table of FHRS establishments without location
 */
export const fhrsNoLocationTable = new Table({
  tableGroup,
  elementID: "no-location",
  heading: "FHRS establishments without location",
  preTableMsg: `The following establishments have no location in the FHRS data
    but are associated with an FHRS authority whose local authority district
    is currently visible on the map.`,
  emptyTableMsg: `No FHRS establishments without a location for any FHRS
    authorities whose local authority district is currently visible on the
    map.`,
  definition: new Map([
    ["FHRS establishment name", "nameCell"],
    ["FHRS address", "address"],
    ["FHRS postcode", "postcode"],
    ["FHRS authority", "authorityName"],
    ["Show info above", "showInfoCell"],
  ]),
  getProperties: (data) => (
    data.features
      .filter((feature) => feature.geometry === null)
      .map(getFHRSNoLocationRow)
  ),
});

/**
 * Table of postcode matches
 */
const postcodeMatchTable = new Table({
  tableGroup,
  elementID: "postcode-matches",
  heading: `Unmatched OSM objects with postcodes matching unmatched FHRS
    establishments`,
  preTableMsg: `The following OSM objects either have no <code>fhrs:id</code>
    tag or the <code>fhrs:id</code> does not match an establishment in the
    current FSA data. The FHRS establishments listed alongside have not been
    successfully matched to OSM objects using a valid <code>fhrs:id</code> but
    their postcode matches the relevant OSM object.`,
  emptyTableMsg: `No unmatched OSM objects with postcodes matching unmatched
    FHRS establishments found on map`,
  definition: new Map([
    ["OSM <code>name</code>", null],
    ["Postcode", null],
    ["Edit", null],
    ["On map above", null],
    ["FHRS establishment name", null],
    ["FHRS ID", null],
    ["", null],
  ]), // fields not required: insertRowForFeature redefined below
  getProperties: (data) => data.features,
});

// redefine standard Table.insertRowForFeature method
postcodeMatchTable.insertRowForFeature = (feature, tableBody) => {
  const {
    osmType, osmIDByType, name, postcode, postcodeMatches,
  } = feature.properties;

  const nameLink = getLink(
    getValueOrPlaceholder(name), getOSMURL(osmType, osmIDByType),
  );
  const nameCell = createElementWith("td", nameLink);
  const postcodeCell = createElementWith(
    "td", getValueOrPlaceholder(postcode),
  );
  const editActionsCell = getEditActionsCell(osmType, osmIDByType);
  const mapActionsCell = getMapActionsCell(feature);

  let firstRowForFeature = true;
  postcodeMatches.forEach((postcodeMatch) => {
    const row = tableBody.insertRow();
    if (firstRowForFeature) {
      [nameCell, postcodeCell, editActionsCell, mapActionsCell]
        .forEach((osmCell) => {
          osmCell.setAttribute("rowspan", postcodeMatches.length);
          osmCell.className = getFeatureStatus(feature); // eslint-disable-line no-param-reassign
          row.append(osmCell);
        });
    }
    row.insertCell().innerHTML = getLink(
      getValueOrPlaceholder(postcodeMatch.name),
      getFSAURL(postcodeMatch.fhrsID),
    );
    row.insertCell().innerHTML = getValueOrPlaceholder(postcodeMatch.fhrsID);
    const JOSMPara = createElementWith(
      "p", "Add <code>fhrs:id</code> in JOSM", "action",
    );
    row.insertCell().append(JOSMPara);
    bindJOSMAction(
      getJOSMAddFHRSIDTagURL(feature.properties, postcodeMatch.fhrsID),
      JOSMPara,
    );
    firstRowForFeature = false;
  });
};

export { postcodeMatchTable };
