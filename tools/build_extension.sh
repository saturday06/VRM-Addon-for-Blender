#!/bin/bash

set -eux -o pipefail

cd "$(dirname "$0")/.."

which blender
blender --version

pushd src/io_scene_vrm
git clean -xdff .
popd

rm -fr extension_output
mkdir extension_output

blender --command extension build \
  --source-dir src/io_scene_vrm \
  --output-dir extension_output

blender --command extension validate \
  extension_output/vrm_extension.zip
