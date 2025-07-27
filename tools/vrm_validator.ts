// SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import process from "node:process";
import { basename, dirname } from "node:path";
import { readdir, readFile, stat } from "node:fs/promises";
import gltfValidator from "gltf-validator";

const basePath = process.env.BLENDER_VRM_TEST_RESOURCES_PATH || process.cwd();
if (!(await stat(basePath)).isDirectory()) {
  console.error(`No base path: "${basePath}"`);
  process.exit(1);
}

const paths = await readdir(basePath, { recursive: true });
paths.forEach(async (path) => {
  if (basename(dirname(path)) == "in" && path.endsWith(".vrm")) {
    return;
  }
  if (!path.endsWith(".vrm") && !path.endsWith(".vrma")) {
    return;
  }
  if ((await stat(path)).isDirectory()) {
    return;
  }

  let result;
  try {
    result = await gltfValidator.validateBytes(
      new Uint8Array(await readFile(path)),
    );
  } catch (e) {
    console.error(`Errors in "${path}":`);
    console.error(e);
    process.exitCode = 1;
    return;
  }

  let hasError = false;
  for (const message of result.issues.messages) {
    if (message.severity > 1) {
      continue;
    }

    if (
      message.code == "MULTIPLE_EXTENSIONS" &&
      message.pointer.endsWith("/extensions/KHR_materials_unlit")
    ) {
      // TODO: Should examine the content in more detail
      continue;
    }

    if (message.code == "INVALID_EXTENSION_NAME_FORMAT") {
      // TODO: Should examine the content
      continue;
    }

    if (message.code == "MESH_PRIMITIVE_GENERATED_TANGENT_SPACE") {
      // TODO: Need to notify the official glTF-Blender-IO
      continue;
    }

    console.error(`Error in "${path}":`);
    console.error(message);
    hasError = true;
  }

  if (hasError) {
    process.exitCode = 1;
    return;
  }
});
