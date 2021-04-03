/**
 * Helper functions for the Inspector class
 */

import {
  bindJOSMAction,
  getValueOrPlaceholder,
  getFSAURL,
  getIDEditURL,
  getOSMURL,
  getJOSMLoadURL,
} from "./utils";

// minimum distance at which to display warning
export const distanceThreshold = 240;

// CSS classes for highlighting
export const highlightBadClass = "highlight-bad";
const highlightWarningClass = "highlight-warning";

/**
 * Returns HTMLElement with inner HTML and optional class
 */
export const createElementWith = (tag, content = "", cssClass = null) => {
  if (!content && !cssClass) {
    throw Error(
      "createElementWith only got tag. Use document.createElement instead",
    );
  }
  const element = document.createElement(tag);
  if (cssClass) element.className = cssClass;
  element.innerHTML = content;
  return element;
};

/**
 * Returns postcode footnote HTML for an FHRS establishment
 */
const getFHRSPostcodeFootnote = (properties) => {
  const { postcode, postcodeOriginal } = properties;

  let footnote = "";
  if (!postcode && postcodeOriginal) {
    footnote = `<p class="footnote">The postcode
      &lsquo;<code>${postcodeOriginal}</code>&rsquo; from the FSA
      data is invalid and has been removed</p>`;
  } else if (postcode && !postcodeOriginal) {
    footnote = `<p class="footnote">A string matching the format of a
      postcode was found in one of the address fields in the FSA data.
      This has been assumed to be the postcode, which was missing from
      the postcode field in the FSA data.</p>`;
  } else if (postcode !== postcodeOriginal) {
    footnote = `<p class="footnote">The postcode
      &lsquo;<code>${postcodeOriginal}</code>&rsquo; from the FSA data
      has been reformatted to &lsquo;<code>${postcode}</code>&rsquo;. This
      usually indicates that the spacing and/or capitalisation of the
      original was incorrect.</p>`;
  }
  return footnote;
};

/**
 * Returns formatted rating date and CSS class for rating date
 */
const formatRatingDate = (ratingDateString, warningYears) => {
  if (ratingDateString === "None") {
    return { ratingDateFormatted: "None", ratingDateClass: "" };
  }

  const ratingDate = new Date(ratingDateString);
  const ratingDateFormatted = ratingDate.toLocaleDateString("en-GB", {
    day: "numeric", month: "short", year: "numeric",
  });
  const today = new Date();
  const warningDate = today.setFullYear(today.getFullYear() - warningYears);

  return {
    ratingDateFormatted,
    ratingDateClass: ratingDate < warningDate ? highlightWarningClass : "",
  };
};

/**
 * Returns HTMLElement for <div> with FHRS establishment details
 */
export const getFHRSEstablishmentDiv = (properties, options) => {
  const {
    heading, cssClass, showRememberPara, showClearPara,
  } = options;
  const {
    name, distance, fhrsID, postcode,
  } = properties;
  const {
    ratingDateFormatted, ratingDateClass,
  } = formatRatingDate(properties.ratingDate, 5);

  const html = `
    <h3>${heading}</h3>
    <div class="data">
    <p><span class="field">Name:</span> ${name}</p>
    <p><span class="field">FHRS ID:</span> ${fhrsID}</p>
    <p class="postcode">
      <span class="field">Postcode:</span>
      ${getValueOrPlaceholder(postcode)}</p>
    ${getFHRSPostcodeFootnote(properties)}
    <p class="${ratingDateClass}"><span class="field">Rating date:</span>
      ${ratingDateFormatted}</p>
    ${distance && distance > distanceThreshold ? `
      <p class=${highlightBadClass}>
        <span class="field">Distance from OSM object</span>:
        ${Math.round(distance)}&nbsp;metres</p>` : ""}
    </div>
    <div class="actions">
    <p><a href="${getFSAURL(fhrsID)}" target="_blank">
      View on FSA website</a></p>
    ${showRememberPara ? `
      <p class="action remember">Link with an OSM object</p>` : ""}
    ${showClearPara ? `<p class="action clear">Clear</p>` : ""}
    </div>`;

  return createElementWith("div", html, cssClass);
};

/**
 * Binds JOSM action. On click, shows status after statusAfter element
 *
 * On click, a paragraph showing status will be added after the supplied
 * statusAfter element. Once the JOSM action has completed, either
 * successfully or unsuccessfully, the status will update accordingly.
 *
 * url (string): JOSM URL to open
 * actionElement (HTMLElement): will trigger action when clicked
 * statusElement (HTMLElement): will display JOSM load status
 * statusAfter (HTMLElement): element that status should be shown after
 */
export const handleJOSMAction = (args) => {
  const {
    url,
    actionElement,
    // pass statusElement rather than creating here because need to use
    // same element for every click to avoid duplication
    statusElement,
    statusAfter,
  } = args;

  actionElement.addEventListener("click", () => {
    statusElement.innerHTML = "Loading in JOSM&hellip;";
    // not until click because empty last-child element affects CSS styling
    statusAfter.after(statusElement);
  });

  bindJOSMAction(url, actionElement)
    .then(() => {
      statusElement.innerHTML = "Loaded successfully";
      handleJOSMAction(args); // to allow another click, generates new promise
    })
    .catch((error) => {
      if (error instanceof TypeError) { // error connecting to JOSM
        statusElement.innerHTML = `
          Check that JOSM is running and remote control is enabled`;
      } else {
        statusElement.innerHTML = "JOSM returned an error";
      }
      handleJOSMAction(args); // to allow another click, generates new promise
      if (!(error instanceof TypeError)) throw error; // to aid debugging
    });
};

/**
 * Returns HTMLElement for <p> with JOSM/iD edit actions
 */
export const getOSMEditPara = (osmType, osmIDByType) => {
  const josmURL = getJOSMLoadURL(osmType, osmIDByType);
  const iDURL = getIDEditURL(osmType, osmIDByType);

  const editPara = createElementWith(
    "p",
    `Edit in <span class="action">JOSM</span> /
      <a href="${iDURL}" target="_blank">iD</a>`,
  );
  handleJOSMAction({
    url: josmURL,
    actionElement: editPara.querySelector("span.action"),
    statusElement: createElementWith("p", "", "footnote"),
    statusAfter: editPara,
  });

  return editPara;
};

/**
 * Returns HTMLElement for <div> with OSM object details
 */
export const getOSMObjectDiv = (properties, options) => {
  const {
    heading, cssClass, showRememberPara, showClearPara,
  } = options;
  const {
    osmType,
    osmIDByType,
    name,
    postcode,
    notPostcode,
    badFHRSIDsString,
    distance,
  } = properties;

  const html = `
    <h3>${heading}</h3>
    <div class="data">
    <p><code>name=${getValueOrPlaceholder(name)}</code></p>
    <p class="postcode">
    <code>addr:postcode=${getValueOrPlaceholder(postcode)}</code></p>
    ${notPostcode ? `
      <p><code>not:addr:postcode=${notPostcode}</code></p>` : ""}
    ${badFHRSIDsString ? `
      <p class="${highlightBadClass}" style="overflow-wrap: break-word;">
      <code>fhrs:id=${badFHRSIDsString}</code></p>` : ""}
    ${distance && distance > distanceThreshold ? `
      <p class=${highlightBadClass}>
        <span class="field">Distance from FHRS establishment</span>:
        ${Math.round(distance)}&nbsp;metres</p>` : ""}
    </div>
    </div>
    <div class="actions">
    <p><a href="${getOSMURL(osmType, osmIDByType)}" target="_blank">
      View on OpenStreetMap</a></p>
    ${showRememberPara ? `
      <p class="action remember">Link with an FHRS establishment</p>` : ""}
    ${showClearPara ? `<p class="action clear">Clear</p>` : ""}
    </div>`;

  const osmObjectDiv = createElementWith("div", html, cssClass);
  const editPara = getOSMEditPara(osmType, osmIDByType);
  osmObjectDiv.querySelector("div.actions").append(editPara);

  return osmObjectDiv;
};

/**
 * Check if FHRS address fully parsed and return footnote HTMLElement
 *
 * If FHRS address is fully parsed, returns element with no content.
 */
export const getUnparsedAddressFootnote = (fhrsProperties) => {
  const tagIsFixme = (token) => token.tag.startsWith("fixme");
  let html = "";
  if (fhrsProperties.parsedAddress.some(tagIsFixme)) {
    html = `
      N.B. Some parts of the address could not be automatically tagged
      with the appropriate OSM <code>addr:*</code> tag. If adding tags in
      JOSM, please change any <code>fixme:*</code> tags.`;
  }
  return createElementWith("p", html, "footnote");
};
