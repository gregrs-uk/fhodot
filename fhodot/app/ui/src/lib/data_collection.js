/**
 * A DataCollection represents a set of DataSource instances
 */

export default class DataCollection {
  constructor(dataSources) {
    if (!(dataSources instanceof Array)) {
      throw new Error("dataSources argument should be an Array");
    }
    this.dataSources = dataSources;
  }

  /**
   * Return the DataSource whose layer is currently enabled on the map
   */
  getCurrentDataSource(map) {
    const result = this.dataSources.find(
      (dataSource) => dataSource.isEnabled(map),
    );
    if (!result) {
      throw new Error("Map doesn't have any data sources enabled");
    }
    return result;
  }

  /**
   * Return the DataSource with the given name, or null
   */
  getDataSourceByName(name) {
    const result = this.dataSources.find(
      (dataSource) => dataSource.name === name,
    );
    return result || null;
  }
}
