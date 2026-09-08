#!/bin/sh
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu

if [ $# -ne 1 ]; then
  echo "Usage: ${0} <release_tag_name>"
  exit 1
fi
release_tag_name=$1

set -x
shellcheck "$0"

cd "$(dirname "$0")/.."

gh auth status

is_draft_or_prerelease=$(gh release view "$release_tag_name" --json isDraft,isPrerelease --jq '.isDraft or .isPrerelease')
if [ "$is_draft_or_prerelease" = "true" ]; then
  echo "Skipping Blender Extensions upload for draft or prerelease: ${release_tag_name}"
  exit 0
fi

release_download_dir_path=$(mktemp -d --suffix=-blender-extensions-release)
trap 'rm -rf "$release_download_dir_path"' EXIT

prefix_name=VRM_Addon_for_Blender
underscore_version=$(ruby -e "puts ARGV[0].sub(/^v/, '').split('.', 3).join('_')" "$release_tag_name")
extension_name="${prefix_name}-Extension-${underscore_version}.zip"
extension_path="${release_download_dir_path}/${extension_name}"
gh release download "$release_tag_name" --pattern "$extension_name" --dir "$release_download_dir_path"
zip -T "$extension_path"

# Create release notes for Blender Extensions
github_release_body_path="${release_download_dir_path}/github_release_body.md"
blender_extensions_release_note_path="${release_download_dir_path}/blender_extensions_release_note.md"
gh release view "$release_tag_name" --json body --jq .body >"$github_release_body_path"
cat "$github_release_body_path"
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

# https://developer.blender.org/docs/features/extensions/ci_cd/
set +x # Hide the content of Authorization variables
echo "Uploading to Blender Extensions Platform..."
curl \
  --fail-with-body \
  --show-error \
  --retry 5 \
  --retry-delay 60 \
  --retry-all-errors \
  --output blender_extensions_upload.log \
  --request POST \
  --header "Authorization:bearer ${BLENDER_EXTENSIONS_TOKEN}" \
  --form "version_file=@${extension_path}" \
  --form "release_notes=<${blender_extensions_release_note_path}" \
  "https://extensions.blender.org/api/v1/extensions/vrm/versions/upload/"
set -x
: ----- OK ----- : +
