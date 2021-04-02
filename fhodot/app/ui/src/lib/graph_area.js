/**
 * A GraphArea represents a <div> that contains graphs
 */

export default class GraphArea {
  constructor(elementID) {
    this.element = document.getElementById(elementID);
  }

  /**
   * Remove everything from graph area but keep graph area <div>
   */
  clear() {
    this.element.innerHTML = "";
  }

  /**
   *
   */
  updateGraph(filename) {
    this.element.innerHTML = `<img src="${filename}">`;
  }
}
