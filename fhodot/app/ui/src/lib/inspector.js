/**
 * The right-hand panel, where data is displayed for clicked markers
 */

import {
  getFHRSEstablishmentDiv,
  getOSMObjectDiv,
  getUnparsedAddressFootnote,
  handleJOSMAction,
  highlightBadClass,
} from "./inspector_helpers";

import {
  createElementWith, fetchAbortPrevious, getJOSMAddTagsURL,
} from "./utils";

export default class Inspector {
  constructor(elementID) {
    this.element = document.getElementById(elementID);
    this.zoomMessage = null;
    this.statsDiv = null;
    this.rememberDiv = null;
    this.rememberedProperties = null;
    this.linkDiv = null; // for linking a remembered object
  }

  /**
   * Shorthand to get the first paragraph element of the link div
   */
  get linkDivFirstPara() {
    return this.linkDiv.querySelector("p");
  }

  /**
   * Remove everything from inspector
   */
  clearAll() {
    this.element.innerHTML = "";
  }

  /**
   * Remove everything from the inspector apart from certain elements
   *
   * exceptions (array): elements to leave in place
   */
  clearExcept(exceptions) {
    Array.from(this.element.children)
      .filter((child) => !exceptions.includes(child))
      .forEach((child) => child.remove());
  }

  /**
   * Forget the remembered properties from starting to link objects
   */
  forgetRememberedProperties() {
    this.rememberedProperties = null;
  }

  /**
   * Show 'zoom in to load markers' message in inspector
   */
  showZoomInMessage() {
    this.clearAll();
    this.zoomMessage = createElementWith(
      "p", "Zoom in to load markers", "zoom-message",
    );
    this.element.append(this.zoomMessage);
  }

  /**
   * Remove 'zoom in to load markers' message from inspector
   */
  removeZoomInMessage() {
    this.zoomMessage.remove();
  }

  /**
   * Update inspector with FHRS establishment details
   */
  updateFHRS(properties) {
    const { postcode, numMatchesDifferentPostcodes } = properties;

    let postcodeMatchesRemembered = null;

    if (this.rememberedProperties) { // remembered OSM object
      this.clearExcept([this.rememberDiv]);
      this.showJOSMAddTagsLinkForRememberedOSM(
        this.rememberedProperties, properties,
      );
      postcodeMatchesRemembered = (
        postcode === this.rememberedProperties.postcode
        || postcode === this.rememberedProperties.notPostcode
      );
      if (!postcodeMatchesRemembered) {
        this.rememberDiv.querySelector("p.postcode")
          .classList.add(highlightBadClass);
      } else {
        // in case establishment with matching postcode selected after
        // one with mismatching postcode
        this.rememberDiv.querySelector("p.postcode")
          .classList.remove(highlightBadClass);
      }
    } else {
      // in case of fetch error there can be a remember div but no properties
      this.clearAll();
    }

    const fhrsDiv = getFHRSEstablishmentDiv(properties, {
      heading: "FHRS establishment",
      cssClass: "clicked",
      showRememberPara: true,
    });
    if ((this.rememberedProperties && !postcodeMatchesRemembered)
        || (!this.rememberedProperties && numMatchesDifferentPostcodes)) {
      fhrsDiv.querySelector("p.postcode").classList.add(highlightBadClass);
    }

    const rememberPara = fhrsDiv.querySelector("p.remember");
    const data = { type: "fhrs", properties };
    rememberPara.addEventListener("click", () => this.remember(data));
    fhrsDiv.querySelector("div.actions").append(rememberPara);

    this.element.append(fhrsDiv);

    this.addOSMMappings(properties);
  }

  /**
   * Add all of an FHRS establishment's OSM mappings to the inspector
   */
  addOSMMappings(properties) {
    properties.osmMappings.forEach((osmMapping) => {
      this.addSingleOSMMapping(osmMapping);
    });

    if (properties.numMatchesDifferentPostcodes) this.appendPostcodeFootnote();
  }

  /**
   * Add a single OSM mapping of an FHRS establishment to the inspector
   */
  addSingleOSMMapping(osmMapping) {
    const { distance, postcodesMatch, osmObject } = osmMapping;

    // pass mapping property along with object property
    osmObject.distance = distance;
    const osmMatchDiv = getOSMObjectDiv(osmObject, {
      heading: "Linked with OSM object",
      cssClass: "fhrs-id-match",
    });
    if (!postcodesMatch) {
      osmMatchDiv.querySelector("p.postcode").classList.add(highlightBadClass);
    }

    this.element.append(osmMatchDiv);
  }

  /**
   * Update inspector with OSM object details
   */
  updateOSM(properties, suggested) {
    const { postcode, notPostcode, numMatchesDifferentPostcodes } = properties;

    this.clearExcept([this.rememberDiv]);

    let postcodeMatchesRemembered = null;

    if (this.rememberedProperties) { // remembered FHRS establishment
      this.showJOSMAddTagsLinkForRememberedFHRS(
        this.rememberedProperties, properties,
      );
      postcodeMatchesRemembered = (
        postcode === this.rememberedProperties.postcode
        || notPostcode === this.rememberedProperties.postcode
      );
      if (!postcodeMatchesRemembered) {
        this.rememberDiv.querySelector("p.postcode")
          .classList.add(highlightBadClass);
      } else {
        // in case OSM object with matching postcode selected after one
        // with mismatching postcode
        this.rememberDiv.querySelector("p.postcode")
          .classList.remove(highlightBadClass);
      }
    }

    const osmDiv = getOSMObjectDiv(properties, {
      heading: "OSM object",
      cssClass: "clicked",
      showRememberPara: !suggested,
    });
    if ((this.rememberedProperties && !postcodeMatchesRemembered)
        || (!this.rememberedProperties && numMatchesDifferentPostcodes)) {
      osmDiv.querySelector("p.postcode").classList.add(highlightBadClass);
    }

    if (!suggested) {
      const rememberPara = osmDiv.querySelector("p.remember");
      const data = { type: "osm", properties };
      rememberPara.addEventListener("click", () => this.remember(data));
      osmDiv.querySelector("div.actions").append(rememberPara);
    }

    this.element.append(osmDiv);

    if (suggested) this.addSuggestedMatches(properties);
    this.addFHRSMappings(properties);
  }

  /**
   * Add all of an OSM object's FHRS mappings to the inspector
   */
  addFHRSMappings(properties) {
    properties.fhrsMappings.forEach((fhrsMapping) => {
      this.addSingleFHRSMapping(fhrsMapping);
    });

    if (properties.numMatchesDifferentPostcodes) this.appendPostcodeFootnote();
  }

  /**
   * Add a single OSM mapping of an FHRS establishment to the inspector
   */
  addSingleFHRSMapping(fhrsMapping) {
    const {
      fhrsID, distance, postcodesMatch, fhrsEstablishment,
    } = fhrsMapping;

    if (fhrsEstablishment) {
      // pass mapping properties along with establishment properties
      fhrsEstablishment.fhrsID = fhrsID;
      fhrsEstablishment.distance = distance;
      const fhrsMatchDiv = getFHRSEstablishmentDiv(fhrsEstablishment, {
        heading: "Linked with FHRS establishment",
        cssClass: "fhrs-id-match",
      });
      if (!postcodesMatch) {
        fhrsMatchDiv.querySelector("p.postcode")
          .classList.add(highlightBadClass);
      }
      this.element.append(fhrsMatchDiv);
    } else {
      const html = `
        <h3>FHRS ID mismatch</h3>
        <p>FHRS ID "${fhrsID}" doesn't match any establishments</p>`;
      this.element.append(createElementWith("div", html, "fhrs-id-mismatch"));
    }
  }

  /**
   * Append postcode mismatch footnote to inspector
   */
  appendPostcodeFootnote() {
    const postcodeFootnote = createElementWith(
      "p",
      `At least one match has a mismatched postcode. N.B. This doesn't
      necessarily indicate an error with the OSM data. If you have
      verified that the OSM <code>addr:postcode</code> is correct, you
      can add the incorrect postcode to the
      <code>not:addr:postcode</code> tag to prevent this warning.`,
      "footnote",
    );
    this.element.append(postcodeFootnote);
  }

  /**
   * Add suggested matching FHRS establishments to the inspector
   */
  addSuggestedMatches(properties) {
    properties.suggestedMatches.forEach((suggestedMatch) => {
      const suggestedMatchDiv = getFHRSEstablishmentDiv(suggestedMatch, {
        heading: "Suggested match",
        cssClass: "suggested-match",
      });

      const josmAddTagsPara = createElementWith(
        "p", "Add tags in JOSM", "action",
      );
      handleJOSMAction({
        url: getJOSMAddTagsURL(suggestedMatch, properties),
        actionElement: josmAddTagsPara,
        statusElement: createElementWith("p", "", "footnote"),
        statusAfter: josmAddTagsPara,
      });
      suggestedMatchDiv.querySelector("div.actions").append(josmAddTagsPara);

      const unparsedAddressFootnote = (
        getUnparsedAddressFootnote(suggestedMatch)
      );
      if (unparsedAddressFootnote.innerHTML) {
        suggestedMatchDiv.querySelector("div.actions")
          .append(unparsedAddressFootnote);
      }

      this.element.append(suggestedMatchDiv);
    });
  }

  /**
   * Handle an error in loading a parsed FHRS establishment address
   */
  handleParsedAddressLoadError(error, fetchAddressFunction) {
    if (error instanceof TypeError) {
      this.linkDivFirstPara.innerHTML = `
        Error loading parsed address for FHRS establishment. Check network
        connection and <span class="action"> try again</span>`;
    } else if (error.name === "AbortError") {
      this.linkDivFirstPara.innerHTML = `
        Loading parsed address for FHRS establishment was cancelled because of
        another fetch action. <span class="action">Try again</span>`;
    } else {
      this.linkDivFirstPara.innerHTML = `
        API returned an error loading parsed address for FHRS establishment`;
      throw error;
    }
    this.linkDivFirstPara.querySelector("span.action")
      .addEventListener("click", fetchAddressFunction);
  }

  /**
   * Called by remember method to prepare remember div and link div
   */
  prepareRememberAndLinkDivs(type, properties) {
    this.linkDiv = createElementWith("div", "<p></p>", "link");

    if (type === "osm") {
      this.rememberDiv = getOSMObjectDiv(properties, {
        heading: "OSM object",
        cssClass: "remembered",
        showClearPara: true,
      });
      this.linkDivFirstPara
        .innerHTML = "Select an FHRS establishment on the map";
    } else {
      this.rememberDiv = getFHRSEstablishmentDiv(properties, {
        heading: "FHRS establishment",
        cssClass: "remembered",
        showClearPara: true,
      });
      this.linkDivFirstPara
        .innerHTML = "Loading parsed address for FHRS establishment";
    }

    this.rememberDiv.querySelector("p.clear")
      .addEventListener("click", () => {
        this.forgetRememberedProperties();
        this.rememberDiv.remove();
        this.linkDiv.remove();
      });
  }

  /**
   * Get inspector ready for user to manually link FHRS/OSM objects
   *
   * Remembers the properties of the object, then switches map layer and
   * displays the remembered object at the top of the inspector.
   *
   * data (object): type and properties of FHRS/OSM object to remember
   */
  remember(data) {
    const { type, properties } = data;
    this.prepareRememberAndLinkDivs(type, properties);

    if (type === "osm") {
      // clears remembered properties
      document.dispatchEvent(new Event("autoChooseLayer"));
      this.rememberedProperties = properties;
    } else {
      // define as function so it can be bound to 'try again'
      const fetchAddress = () => {
        fetchAbortPrevious(`api/fhrs/${properties.fhrsID}`)
          .then((response) => response.json())
          .then((propertiesWithParsedAddress) => {
            // Only switch layer if address loaded, because if there's a
            // network issue the markers wouldn't load, and it makes
            // more sense to the user to stay on the existing layer.
            // Layer switch clears remembered properties and inspector.
            document.dispatchEvent(new Event("autoChooseLayer"));
            this.rememberedProperties = propertiesWithParsedAddress;
            this.linkDivFirstPara
              .innerHTML = "Select an OSM object on the map";
            this.element.append(this.rememberDiv);
            this.element.append(this.linkDiv);
          })
          .catch((error) => {
            this.handleParsedAddressLoadError(error, fetchAddress);
          });
      };

      fetchAddress();
    }
    // in case of remembered FHRS, this will be before fetch promise
    // resolves and will display the loading message
    this.clearAll();
    this.element.append(this.rememberDiv);
    this.element.append(this.linkDiv);
  }

  /**
   * Set link div to 'Add tags' link for remembered FHRS establishment
   *
   * fhrsProperties should already contain parsed address fetched by
   * the remember method.
   */
  showJOSMAddTagsLinkForRememberedFHRS(fhrsProperties, osmProperties) {
    this.linkDiv = createElementWith(
      "div",
      `<p><span class="action">Add tags in JOSM</span> to link with:</p>`,
      "link",
    );
    const addTagsPara = this.linkDiv.querySelector("p");
    this.rememberDiv.after(this.linkDiv);

    handleJOSMAction({
      url: getJOSMAddTagsURL(fhrsProperties, osmProperties),
      actionElement: addTagsPara.querySelector("span.action"),
      statusElement: createElementWith("p", "", "footnote"),
      statusAfter: addTagsPara,
    });

    const unparsedAddressFootnote = getUnparsedAddressFootnote(fhrsProperties);
    if (unparsedAddressFootnote.innerHTML) {
      this.linkDiv.append(unparsedAddressFootnote);
    }
  }

  /**
   * Set link div to 'Add tags' link for remembered OSM object
   */
  showJOSMAddTagsLinkForRememberedOSM(osmProperties, fhrsProperties) {
    this.linkDiv = createElementWith(
      "div",
      "<p>Loading parsed address for FHRS establishment&hellip;</p>",
      "link",
    );
    this.rememberDiv.after(this.linkDiv);

    // define as function so it can be bound to 'try again'
    const fetchAddress = () => {
      fetchAbortPrevious(`api/fhrs/${fhrsProperties.fhrsID}`)
        .then((response) => response.json())
        .then((fhrsPropertiesWithParsedAddress) => {
          this.linkDivFirstPara.innerHTML = `
            <span class="action">Add tags in JOSM</span> to link with:`;

          handleJOSMAction({
            url: getJOSMAddTagsURL(
              fhrsPropertiesWithParsedAddress, osmProperties,
            ),
            actionElement: this.linkDivFirstPara.querySelector("span"),
            statusElement: createElementWith("p", "", "footnote"),
            statusAfter: this.linkDivFirstPara,
          });

          const unparsedAddressFootnote = getUnparsedAddressFootnote(
            fhrsPropertiesWithParsedAddress,
          );
          if (unparsedAddressFootnote.innerHTML) {
            this.linkDiv.append(unparsedAddressFootnote);
          }
        })
        .catch((error) => {
          this.handleParsedAddressLoadError(error, fetchAddress);
        });
    };

    fetchAddress();
  }

  /**
   * Show district stats div
   */
  showStatsDiv() {
    this.statsDiv = document.createElement("div");
    this.element.append(this.statsDiv);
  }

  /**
   * Remove district stats div
   */
  removeStatsDiv() {
    this.statsDiv.remove();
  }

  /**
   * Update inspector with stats
   */
  updateStatsDiv(properties, dataSourceName) {
    if (dataSourceName === "fhrs") {
      this.updateStatsDivFHRS(properties);
    } else if (dataSourceName === "osm") {
      this.updateStatsDivOSM(properties);
    }
  }

  /**
   * Update inspector with authority stats for FHRS layer
   */
  updateStatsDivFHRS(properties) {
    if (!properties) {
      this.statsDiv.innerHTML = `
        <p>Darker green local authority districts have a greater proportion of
          the associated FHRS authority's establishments matched.</p>
        <p>Hover over a district to show current statistics for the associated
          FHRS authority.</p>
        <p>Click on a district to show a graph of historical statistics for the
          associated FHRS authority underneath the map.</p>
        <p>There are also <a href="summary.html" target="_blank">summary
          statistics/graphs</a> for the whole UK.</p>`;
      return;
    }

    const { stats } = properties;
    const proportion = stats.matched_same_postcodes
      / (stats.total - stats.unmatched_without_location);

    let html = `
      <h3>${properties.name}</h3>
      <p>Stats for FHRS establishments in this authority</p>
      <p><span class="field">Matched</span>:
        ${stats.matched_same_postcodes} (same postcodes)`;
    if (stats.matched_different_postcodes) {
      html += ` + 
        ${stats.matched_different_postcodes} (different postcodes)`;
    }
    html += `
        </p>
      <p><span class="field">Unmatched</span>:
        ${stats.unmatched_with_location} (+
        ${stats.unmatched_without_location} without a location in the FHRS
        data)</p>
      <p><span class="field">Total</span>: ${stats.total}</p>
      <p><span class="field">Proportion matched with same postcodes (ignoring
        any unmatched establishments without a location in the FHRS data)
        </span>: ${Math.round(proportion * 100)}%</p>`;

    this.statsDiv.innerHTML = html;
  }

  /**
   * Update inspector with district stats for OSM layer
   */
  updateStatsDivOSM(properties) {
    if (!properties) {
      this.statsDiv.innerHTML = `
        <p>Darker green local authority districts have a greater proportion of
          their OSM objects matched.</p>
        <p>Hover over a district to show current statistics for OSM objects
          within this district.</p>
        <p>Click on a district to show a graph of historical statistics for
          OSM objects within this district underneath the map.</p>
        <p>There are also <a href="summary.html" target="_blank">summary
          statistics/graphs</a> for the whole UK.</p>`;
      return;
    }

    const { stats } = properties;
    const proportion = stats.matched_same_postcodes / stats.total;

    const matchedDifferentPostcodesString = (
      stats.matched_different_postcodes
        ? `${stats.matched_different_postcodes} (different postcodes)`
        : ""
    );

    const html = `
      <h3>${properties.name}</h3>
      <p>Stats for OSM objects within this local authority district</p>
      <p><span class="field">Matched</span>:
        ${stats.matched_same_postcodes} (same postcodes)
        ${matchedDifferentPostcodesString}</p>
      <p><span class="field">Invalid <code>fhrs:id</code></span>:
        ${stats.mismatched}</p>
      <p><span class="field">Relevant objects without
        <code>fhrs:id</code></span>: ${stats.unmatched}</p>
      <p><span class="field">Total relevant objects</span>:
        ${stats.total}</p>
      <p><span class="field">Proportion of relevant objects matched with same
        postcodes</span>: ${Math.round(proportion * 100)}%</p>
      <p class="footnote">Relevant OSM objects are those likely to be
        included in the FHRS data (e.g. <code>amenity=cafe</code>) plus any
        others with an <code>fhrs:id</code></p>`;

    this.statsDiv.innerHTML = html;
  }
}
