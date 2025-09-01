#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux -o pipefail
shellcheck "$0"

cd "$(dirname "$0")/.."

blender_archive_path="$PWD/.cache/blenders/extension-builder-blender.tar.xz"
blender_path="$PWD/.cache/blenders/extension-builder-blender/blender"

blender_archive_base_path="$(dirname "$blender_archive_path")"
blender_base_path="$(dirname "$blender_path")"

if [ ! -f "$blender_archive_path" ]; then
  mkdir -p "$blender_archive_base_path"
  blender_archive_url="https://mirrors.ocf.berkeley.edu/blender/release/Blender4.2/blender-4.2.3-linux-x64.tar.xz"
  curl --fail --show-error --location --retry 5 --retry-all-errors --output "$blender_archive_path" "$blender_archive_url"
  if [ "$(md5sum "$blender_archive_path")" != "34fe4456252a703c39cb93efbfa84f8c  $blender_archive_path" ]; then
    echo "Hash mismatch"
    exit 1
  fi
fi

if [ ! -f "$blender_path" ]; then
  rm -fr "$blender_base_path"
  mkdir -p "$blender_base_path"
  if ! tar -xf "$blender_archive_path" -C "$blender_base_path" --strip-components=1; then
    echo "Please upgrade archive URL"
    exit 1
  fi
fi

"$blender_path" --version

if ! git --no-pager diff --exit-code || ! git --no-pager diff --cached --exit-code; then
  echo "changes are detected in working copy."
  exit 1
fi

git clean -xdff src

rm -fr extension_output
mkdir extension_output
output_filepath="extension_output/vrm_$(LC_ALL=C date -u +%Y%m%d%H%M%S)_$(git rev-parse HEAD).zip"

"$blender_path" --command extension build \
  --source-dir src/io_scene_vrm \
  --output-filepath "$output_filepath"

"$blender_path" --command extension validate \
  "$output_filepath"

echo "Generated: $output_filepath"
