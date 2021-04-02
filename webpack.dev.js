const HtmlWebpackPlugin = require("html-webpack-plugin");
const { merge } = require("webpack-merge");
const common = require("./webpack.common.js");

module.exports = merge(common, {
  mode: "development",
  entry: {
    tests: "mocha-loader!./fhodot/app/ui/src/tests.js",
  },
  plugins: [
    new HtmlWebpackPlugin({
      title: "Test runner",
      filename: "tests.html",
      chunks: ["tests"],
    }),
  ],
  devtool: "inline-source-map",
});
