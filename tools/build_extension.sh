#!/bin/bash

set -eux -o pipefail

cd "$(dirname "$0")/.."

if ! git --no-pager diff --exit-code || ! git --no-pager diff --cached --exit-code; then
  echo "changes are detected in working copy."
  exit 1
fi

which blender
blender --version

pushd src/io_scene_vrm
git clean -xdff .
popd

patch -p1 <extension.patch
git --no-pager diff

rm -fr extension_output
mkdir extension_output

blender --command extension build \
  --source-dir src/io_scene_vrm \
  --output-dir extension_output

blender --command extension validate \
  extension_output/vrm_extension.zip

git checkout .
