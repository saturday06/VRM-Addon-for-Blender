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
output_filepath="extension_output/vrm_$(LC_ALL=C date -u +%Y%m%d%H%M%S)_$(git rev-parse HEAD).zip"

blender --command extension build \
  --source-dir src/io_scene_vrm \
  --output-filepath "$output_filepath"

blender --command extension validate \
  "$output_filepath"

git checkout .
