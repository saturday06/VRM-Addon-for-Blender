// SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import process from "node:process";
import { dirname, basename } from "path";
import { existsSync, promises, readFileSync } from "fs";
import gltfValidator from "gltf-validator";

const basePath = process.env.BLENDER_VRM_TEST_RESOURCES_PATH || process.cwd();
if (!existsSync(basePath)) {
  console.error(`No base path: "${basePath}"`);
  process.exit(1);
}

const paths = await promises.readdir(basePath, { recursive: true });
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
      new Uint8Array(readFileSync(path)),
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
      // TODO: もっと詳しく中身を見るべき
      continue;
    }

    if (message.code == "INVALID_EXTENSION_NAME_FORMAT") {
      // TODO: 中身を見るべき
      continue;
    }

    if (message.code == "MESH_PRIMITIVE_GENERATED_TANGENT_SPACE") {
      // TODO: glTF-Blender-IO公式に通知する必要がある
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
