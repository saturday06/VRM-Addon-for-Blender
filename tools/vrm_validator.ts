#!/usr/bin/env -S deno run --allow-read
// SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import { Validator } from "npm:gltf-validator@2.0.0-dev.3.9";

const filePath = Deno.args[0];
if (!filePath) {
  console.error("Usage: vrm_validator.ts <file_path>");
  Deno.exit(1);
}

const fileData = await Deno.readFile(filePath);
const result = await Validator.validateBytes(new Uint8Array(fileData));

const messages = result.issues.messages;
if (messages.length === 0) {
  console.log("No issues found");
  Deno.exit(0);
}

let exitCode = 0;

for (const message of messages) {
  if (
    message.code == "ACCESSOR_ELEMENT_OUT_OF_MIN_BOUND" ||
    message.code == "ACCESSOR_ELEMENT_OUT_OF_MAX_BOUND"
  ) {
    continue;
  }

  if (
    message.code == "MULTIPLE_EXTENSIONS" &&
    message.pointer.endsWith("/extensions/KHR_materials_unlit")
  ) {
    // TODO: Should examine the contents in more detail
    continue;
  }

  if (message.code == "INVALID_EXTENSION_NAME_FORMAT") {
    // TODO: Should examine the contents
    continue;
  }

  if (message.code == "MESH_PRIMITIVE_GENERATED_TANGENT_SPACE") {
    // TODO: Need to notify the official glTF-Blender-IO
    continue;
  }

  console.log(message);
  exitCode = 1;
}

Deno.exit(exitCode);
