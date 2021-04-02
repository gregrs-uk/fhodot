/**
 * A TableGroup represents a <div> that contains Table <div> elements
 */

export default class TableGroup {
  constructor(elementID) {
    this.element = document.getElementById(elementID);
  }

  /**
   * Remove everything from table group but keep table group <div>
   */
  clear() {
    this.element.innerHTML = "";
  }
}
