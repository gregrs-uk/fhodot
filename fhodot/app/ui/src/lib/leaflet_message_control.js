import { Control } from "leaflet";
import { createElementWith } from "./utils";

/**
 * A Leaflet control for displaying a message
 */
export default class MessageControl extends Control {
  constructor() {
    super();
    this.options.position = "bottomright";
    this.element = createElementWith(
      "div",
      `<div class="leaflet-bar"></div>`,
      "leaflet-message-control",
    );
    this.messagePara = document.createElement("p");
    this.element.querySelector("div.leaflet-bar").append(this.messagePara);
    this.element.classList.add("hidden");
    this.abortMessageClear = false;
  }

  /**
   * Create the control (called when adding control to Leaflet map)
   */
  onAdd() {
    return this.element;
  }

  /**
   * Set the message but don't change visible/hidden state
   */
  setMessage(html) {
    this.messagePara.innerHTML = html;
  }

  /**
   * Show the control and display the supplied message
   */
  showMessage(html) {
    this.element.classList.remove("hidden");
    this.setMessage(html);
    this.abortMessageClear = true;
  }

  /**
   * Hide the control
   */
  hide() {
    this.element.classList.add("hidden");
    this.abortMessageClear = false;
    setTimeout(() => {
      if (!this.abortMessageClear) this.setMessage("");
    }, 1000);
  }
}
