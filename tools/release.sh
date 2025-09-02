#!/bin/sh
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu

if [ $# -lt 1 ]; then
  echo "Usage: $0 <release_tag_name>"
  release_tag_name=v0.0.0
  echo "Continuing with release_tag_name=${release_tag_name}"
else
  release_tag_name=$1
fi

set -x
shellcheck "$0"

cd "$(dirname "$0")/.."

export PYTHONDONTWRITEBYTECODE=1
prefix_name=VRM_Addon_for_Blender

if ! git status; then
  uname -a
  id
  ls
  exit 1
fi

if ! git --no-pager diff --exit-code || ! git --no-pager diff --cached --exit-code; then
  echo "changes are detected in working copy."
  exit 1
fi

git clean -xdff src

underscore_version=$(ruby -e "puts ARGV[0].sub(/^v/, '').split('.', 3).join('_')" "$release_tag_name")
version=$(ruby -e "puts ARGV[0].split('_', 3).join('.')" "$underscore_version")
blender_manifest_version=$(
  python3 <<'PRINT_BLENDER_MANIFEST_VERSION'
import tomllib
from pathlib import Path

blender_manifest_path = Path("src/io_scene_vrm/blender_manifest.toml")
blender_manifest_text = blender_manifest_path.read_text()
blender_manifest = tomllib.loads(blender_manifest_text)
print(blender_manifest["version"])
PRINT_BLENDER_MANIFEST_VERSION
)

if [ "$version" != "$blender_manifest_version" ]; then
  release_postfix=draft
else
  release_postfix=release
fi

for postfix in "$release_postfix" "$underscore_version"; do
  work_dir=$(mktemp -d --suffix=-release-archive-work-dir)
  base="${prefix_name}-${postfix}"
  cp -r src/io_scene_vrm "${work_dir}/${base}"
  cp -r LICENSE* "${work_dir}/${base}/"
  (
    cd "$work_dir"
    find . -name "__pycache__" -type d -exec rm -fr {} \;
    advzip --add --shrink-insane --iter 20 "${prefix_name}-${postfix}.zip" "${base}"
  )
  cp "${work_dir}/${prefix_name}-${postfix}.zip" .
done
website_release_path="./${prefix_name}-${release_postfix}.zip"
github_release_path="./${prefix_name}-${underscore_version}.zip"

./tools/build_extension.sh
original_extension_path=$(find extension_output -name "vrm_*_*.zip" | sort | head -n 1)
if [ ! -f "$original_extension_path" ]; then
  echo "No extension output"
  exit 1
fi

extension_path="./${prefix_name}-Extension-${underscore_version}.zip"
mv -v "$original_extension_path" "$extension_path"
mkdir -p website_release_output/releases
cp "$website_release_path" website_release_output/releases/

(
  set +x
  echo
  echo "====================================================================="
  echo "Release Build Completed"
  echo "Blender 4.2 or later: ${extension_path}"
  echo "Blender 2.93 - 4.1 website release: ${website_release_path}"
  echo "Blender 2.93 - 4.1 github release: ${github_release_path}"
  echo "====================================================================="
  echo
)

gh auth status

if ! gh release view "$release_tag_name"; then
  echo "No release tag: $release_tag_name"
  exit 1
fi

gh release upload "$release_tag_name" "${extension_path}#(Blender 4.2 or later) VRM Add-on for Blender Extension ${version} (zip)"
gh release upload "$release_tag_name" "${github_release_path}#(Blender 2.93 - 4.1) VRM Add-on for Blender ${version} (zip)"

# Create release notes for Blender Extensions
github_release_body_path=$(mktemp)
blender_extensions_release_note_path=$(mktemp)
gh release view "$release_tag_name" --json body --jq .body | tee "$github_release_body_path"
ruby -- - "$github_release_body_path" "$blender_extensions_release_note_path" <<'CREATE_BLENDER_EXTENSIONS_RELEASE_NOTE'
require "uri"

input_path, output_path = ARGV
title, body = File.read(input_path).strip.split("\n\n", 2)

uri_str = title.strip.sub(/^## \[[.0-9]+\]\(/, "").sub(/\).*$/, "").strip
uri = nil
begin
  uri = URI.parse(uri_str)
rescue => e
  p e
end

output = body.strip + "\n\n\n"
if uri
  output += "**Full Changelog:** #{uri}\n"
end

File.write(output_path, output)
CREATE_BLENDER_EXTENSIONS_RELEASE_NOTE
cat "$blender_extensions_release_note_path"

if [ "$release_postfix" = "release" ]; then
  gh release edit "$release_tag_name" --draft=false --latest

  # https://developer.blender.org/docs/features/extensions/ci_cd/
  set +x # Hide the content of Authorization variables
  curl \
    --fail-with-body \
    --show-error \
    --retry 5 \
    --retry-delay 60 \
    --retry-all-errors \
    --output blender_extensions_upload.log \
    --request POST \
    --header "Authorization:bearer $BLENDER_EXTENSIONS_TOKEN" \
    --form "version_file=@$extension_path" \
    --form "release_notes=<$blender_extensions_release_note_path" \
    "https://extensions.blender.org/api/v1/extensions/vrm/versions/upload/"
  set -x
else
  gh release edit "$release_tag_name" --prerelease
fi
