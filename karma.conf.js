const path = require("path");

module.exports = (config) => {
  config.set({

    basePath: "",
    frameworks: ["mocha"],

    files: [
      { pattern: "fhodot/app/ui/src/**/*.test.js", watched: false },
    ],

    preprocessors: {
      "fhodot/app/ui/src/**/*.test.js": ["webpack", "sourcemap"],
    },

    webpack: {
      mode: "development",
      module: {
        rules: [
          {
            test: /\.js$/,
            use: {
              loader: "istanbul-instrumenter-loader",
              query: {
                esModules: true,
                produceSourceMap: true,
              },
            },
            exclude: [
              path.resolve("node_modules"),
              /\.test\.js$/, // don't instrument test files
            ],
          },
        ],
      },
    },

    reporters: ["progress", "coverage"],

    coverageReporter: {
      dir: "coverage/javascript/",
      reports: ["html"],
    },

    port: 9876,
    colors: true,
    logLevel: config.LOG_INFO,
    autoWatch: true,
    browsers: ["ChromeHeadless"],
    singleRun: true,
    concurrency: Infinity,
  });
};
