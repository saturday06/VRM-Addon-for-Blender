#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux -o pipefail
shellcheck "$0"

cd "$(dirname "$0")/.."

if [ ! -f blender.tar.xz ]; then
  blender_archive_url="https://mirrors.ocf.berkeley.edu/blender/release/Blender4.2/blender-4.2.3-linux-x64.tar.xz"
  curl --fail --location --show-error --retry 5 --retry-all-errors "$blender_archive_url" -o blender.tar.xz
  if [ "$(md5sum blender.tar.xz)" != "34fe4456252a703c39cb93efbfa84f8c  blender.tar.xz" ]; then
    echo "Hash mismatch"
    exit 1
  fi
fi

rm -fr .local/blender
mkdir -p .local/blender
if ! tar xf blender.tar.xz -C .local/blender --strip-components=1; then
  echo "Please upgrade archive URL"
  exit 1
fi
./.local/blender/blender --version

if ! git --no-pager diff --exit-code || ! git --no-pager diff --cached --exit-code; then
  echo "changes are detected in working copy."
  exit 1
fi

pushd src/io_scene_vrm
git clean -xdff .
popd

rm -fr extension_output
mkdir extension_output
output_filepath="extension_output/vrm_$(LC_ALL=C date -u +%Y%m%d%H%M%S)_$(git rev-parse HEAD).zip"

find src/io_scene_vrm -name "__pycache__" -type d -exec rm -fr {} \;

./.local/blender/blender --command extension build \
  --source-dir src/io_scene_vrm \
  --output-filepath "$output_filepath"

./.local/blender/blender --command extension validate \
  "$output_filepath"

git checkout .
rm -fr .local/blender
