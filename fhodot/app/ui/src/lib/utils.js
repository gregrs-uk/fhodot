/**
 * Return string supplied or a placeholder if string is empty
 */
export const getValueOrPlaceholder = (value) => (
  value || "<span class='empty-value'>[None]</span>");

/**
 * Return URL for establishment's page on FSA website
 */
export const getFSAURL = (fhrsID) => (
  `https://ratings.food.gov.uk/business/en-GB/${fhrsID}`);

/**
 * Return URL for OSM object's page on OpenStreetMap site
 */
export const getOSMURL = (osmType, osmIDByType) => (
  `https://openstreetmap.org/${osmType}/${osmIDByType}`);

/**
 * Return URL to load OSM object using JOSM remote control
 */
export const getJOSMLoadURL = (osmType, osmIDByType) => (
  "http://localhost:8111/load_object?objects="
  + `${osmType.substring(0, 1)}${osmIDByType}`);

/**
 * Return URL to open OSM object in iD editor
 */
export const getIDEditURL = (osmType, osmIDByType) => (
  `https://www.openstreetmap.org/edit?editor=id&${osmType}=${osmIDByType}`);

/**
 * Return JOSM remote control URL to add OSM tags for FHRS establishment
 */
export const getJOSMAddTagsURL = (fhrsProperties, osmProperties) => {
  const tags = {
    "fhrs:id": fhrsProperties.fhrsID,
    name: fhrsProperties.name,
    "addr:postcode": fhrsProperties.postcode,
    "source:addr": "FHRS Open Data",
  };
  fhrsProperties.parsedAddress.forEach((token) => {
    tags[token.tag] = token.string;
  });

  const tagStrings = [];
  Object.entries(tags).forEach((tag) => {
    if (tag[1]) tagStrings.push(`${tag[0]}=${tag[1]}`);
  });

  const { osmType, osmIDByType } = osmProperties;
  const url = new URL(getJOSMLoadURL(osmType, osmIDByType));
  url.searchParams.append("addtags", tagStrings.join("|"));
  return url.toString();
};

/**
 * Open JOSM URL using fetch and return promise
 *
 * This is preferred over a simple link because it avoids navigating
 * away from the browser page or opening a new tab which the user has to
 * close. It also allows the status to be reported.
 *
 * url (string): JOSM remote control URL
 */
export const openJOSMURL = (url) => (
  fetch(url) // not aborted by a new fetch, unlike API fetches
    .then((response) => {
      if (!response.ok) {
        throw new Error(
          `JOSM returned status ${response.status} trying to load ${url}`,
        );
      }
    })
  // returns promise to allow status reporting
);

/**
 * Bind JOSM load action to element click event and return promise
 *
 * The returned promise will resolve or reject once the element has been
 * clicked and the attempt to control JOSM remotely has either been
 * successful or not, allowing status to be displayed.
 *
 * url (string): JOSM remote control URL
 * element (HTMLElement): element that the user will click
 */
export const bindJOSMAction = (url, element) => (
  new Promise((resolve, reject) => {
    const onClick = () => {
      openJOSMURL(url)
        .then(() => resolve())
        .catch((error) => reject(error))
        // only use event listener once because promise can't be re-used
        .then(() => element.removeEventListener("click", onClick));
    };

    element.addEventListener("click", onClick);
  })
);

/**
 * AbortController for the previous fetch
 */
let fetchAbortController;

/**
 * Abort previous fetches that used this function and perform a fetch
 *
 * Also throw an error if the response is received but unsuccessful.
 *
 * Returns a promise
 */
export const fetchAbortPrevious = (url) => {
  if (fetchAbortController) {
    fetchAbortController.abort();
  }
  fetchAbortController = new AbortController();
  return fetch(url, { signal: fetchAbortController.signal })
    .then((response) => {
      if (!response.ok) {
        throw Error(
          `fetch received response ${response.status} ${response.statusText}`,
        );
      }
      return response;
    });
};
