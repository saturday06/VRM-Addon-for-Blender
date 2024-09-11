const process = require("node:process");
const { dirname, basename, resolve } = require("path");
const fs = require("fs");
const gltfValidator = require("gltf-validator");

// https://stackoverflow.com/a/45130990
function readDirRecursiveSync(dir) {
  const result = [];
  const dirents = fs.readdirSync(dir, { withFileTypes: true });
  for (const dirent of dirents) {
    const resolved = resolve(dir, dirent.name);
    if (dirent.isDirectory()) {
      result.push(...readDirRecursiveSync(resolved));
    } else {
      result.push(resolved);
    }
  }
  return result;
}

const basePath = process.env.BLENDER_VRM_TEST_RESOURCES_PATH || process.cwd();
if (!fs.existsSync(basePath)) {
  console.error(`No base path: "${basePath}"`);
  process.exit(1);
}

const paths = readDirRecursiveSync(basePath);
paths.forEach(async (path) => {
  if (basename(dirname(path)) == "in") {
    return;
  }
  if (!path.endsWith(".vrm")) {
    return;
  }

  let result;
  try {
    result = await gltfValidator.validateBytes(
      new Uint8Array(fs.readFileSync(path)),
    );
  } catch (e) {
    console.error(`Errors in "${path}":`);
    console.error(e);
    process.exitCode = 1;
    return;
  }

  if (result.issues.numErrors > 0) {
    console.error(`Errors in "${path}":`);
    result.issues.messages.forEach((message) => {
      console.error(message);
    });
    process.exitCode = 1;
    return;
  }
});
