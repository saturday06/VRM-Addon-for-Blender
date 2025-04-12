// This code is derived from pyright's code. Please refer there for the license.
// https://github.com/microsoft/pyright/blob/1.1.399/packages/pyright/index.js

const path = require("node:path");
const rootDirectory = path.join(
  __dirname,
  "..",
  "node_modules",
  "pyright",
  "dist",
);

// deno-lint-ignore no-node-globals
global.__rootDirectory = rootDirectory;

require(path.join(rootDirectory, "pyright.js"));
