/**
 * A table with associated header and other text, all in a <div>
 *
 * For the <table> itself, the definition Map defines the columns by
 * listing each column header and associated property to be extracted
 * from the data. The table can be refreshed with new data using
 * Table.refresh, which calls the supplied getProperties function to
 * pre-process the data. The getProperties function should accept the
 * data argument supplied to refresh and return an array of objects with
 * a property for each column in the definition.
 */

export default class Table {
  constructor(arg) {
    if (!(arg instanceof Object)) {
      throw new Error("Expecting an object argument");
    }
    if (!(arg.definition instanceof Map)) {
      throw new Error("arg.definition should be a Map");
    }

    // will be added to table group div by refresh method
    this.element = document.createElement("div");
    this.element.id = arg.elementID;
    this.tableGroup = arg.tableGroup;
    this.heading = arg.heading;
    this.preTableMsg = arg.preTableMsg;
    this.emptyTableMsg = arg.emptyTableMsg;
    this.definition = arg.definition;
    this.getProperties = arg.getProperties;
    this.visible = false; // remember visibility e.g. when moving map
  }

  /**
   * Hide the <table> element and the pre-table message
   *
   * Also sets up the show/hide link for showing the table.
   */
  hideTable() {
    this.element.querySelector("p.pre-table-msg").style.display = "none";
    this.element.querySelector("table").style.display = "none";
    this.visible = false;
    const hideShowElement = this.element.querySelector("p.show-hide a");
    hideShowElement.innerHTML = "Show table";
    hideShowElement.removeEventListener("click", this.hideTable.bind(this));
    hideShowElement.addEventListener("click", this.showTable.bind(this));
  }

  /**
   * Show the <table> element and the pre-table message
   *
   * Also sets up the show/hide link for hiding the table.
   */
  showTable() {
    this.element.querySelector("p.pre-table-msg").style.display = "block";
    this.element.querySelector("table").style.display = "table";
    this.visible = true;
    const hideShowElement = this.element.querySelector("p.show-hide a");
    hideShowElement.innerHTML = "Hide table";
    hideShowElement.removeEventListener("click", this.showTable.bind(this));
    hideShowElement.addEventListener("click", this.hideTable.bind(this));
  }

  /**
   * Use table definition to return <table> HTMLElement for features
   */
  getTable(features) {
    const table = document.createElement("table");

    const headerRow = table.createTHead().insertRow();
    this.definition.forEach((field, colHeader) => {
      headerRow.insertCell().innerHTML = colHeader;
    });

    const tableBody = table.createTBody();
    features.forEach((feature) => {
      const row = tableBody.insertRow();
      this.definition.forEach((field) => {
        if (typeof feature[field] === "string") {
          row.insertCell().innerHTML = feature[field];
        } else if (feature[field] instanceof HTMLElement
                   && feature[field].nodeName === "TD") {
          row.append(feature[field]);
        } else {
          throw new Error("Expecting field to be string or <td> HTMLELement");
        }
      });
    });

    return table;
  }

  /**
   * Refresh the table's entire <div> using the data provided
   */
  refresh(data) {
    // ensure table div present in table group div e.g. if layer has changed
    this.element.remove();
    this.tableGroup.element.append(this.element);

    let html = `<h2>${this.heading}</h2>`;
    const features = this.getProperties(data);
    if (features.length) {
      // text will be added by hideTable/showTable below
      html += `<p class="show-hide"><a></a></p>`;
      html += `<p class="pre-table-msg">${this.preTableMsg}</p>`;
      this.element.innerHTML = html;
      this.element.append(this.getTable(features));
      if (this.visible) {
        this.showTable();
      } else {
        this.hideTable();
      }
    } else {
      html += `<p>${this.emptyTableMsg}</p>`;
      this.element.innerHTML = html;
    }
  }
}
