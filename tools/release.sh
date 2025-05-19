#!/bin/sh

set -eu

if [ $# -lt 1 ]; then
  echo "Usage: $0 <release_tag_name>"
  exit 1
fi

release_tag_name="$1"
release_postfix="${release_tag_name#v}"

if [ "$release_tag_name" = "$release_postfix" ]; then
  echo "Error: release_tag_name must start with 'v'"
  exit 1
fi

if ! git rev-parse --verify "$release_tag_name" >/dev/null; then
  echo "Error: tag '$release_tag_name' does not exist"
  exit 1
fi

if ! command -v gh; then
  echo "Error: gh command not found"
  exit 1
fi

if ! command -v jq; then
  echo "Error: jq command not found"
  exit 1
fi

if ! command -v zip; then
  echo "Error: zip command not found"
  exit 1
fi

if ! command -v unzip; then
  echo "Error: unzip command not found"
  exit 1
fi

if ! command -v python; then
  echo "Error: python command not found"
  exit 1
fi

if ! command -v git; then
  echo "Error: git command not found"
  exit 1
fi

if ! command -v mktemp; then
  echo "Error: mktemp command not found"
  exit 1
fi

if ! command -v diff; then
  echo "Error: diff command not found"
  exit 1
fi

if ! command -v dirname; then
  echo "Error: dirname command not found"
  exit 1
fi

if ! command -v cd; then
  echo "Error: cd command not found"
  exit 1
fi

if ! command -v rm; then
  echo "Error: rm command not found"
  exit 1
fi

if ! command -v mkdir; then
  echo "Error: mkdir command not found"
  exit 1
fi

if ! command -v cp; then
  echo "Error: cp command not found"
  exit 1
fi

if ! command -v cat; then
  echo "Error: cat command not found"
  exit 1
fi

if ! command -v sed; then
  echo "Error: sed command not found"
  exit 1
fi

if ! command -v tee; then
  echo "Error: tee command not found"
  exit 1
fi

cd "$(dirname "$0")/.."

prefix_name="VRM_Addon_for_Blender"
addon_dir="src"
addon_check_dir="$(mktemp -d)"
addon_check_unzip_dir="$(mktemp -d)"
archive_branch_dir="$(mktemp -d)"

gh release download "$release_tag_name" --pattern "*.zip" --dir "$addon_check_dir"
unzip -q "$addon_check_dir/${prefix_name}-${release_postfix}.zip" -d "$addon_check_unzip_dir"
diff -ru "$addon_check_unzip_dir/${prefix_name}-${release_postfix}" "$addon_dir" || true

(
  cd "$archive_branch_dir"
  git init
  git config user.name "VRM Addon for Blender"
  git config user.email "vrm-addon-for-blender@example.com"
  git remote add origin "https://github.com/saturday06/VRM-Addon-for-Blender.git"
  git fetch origin release-archive
  git checkout -b release-archive origin/release-archive || git checkout -b release-archive
  mkdir -p "archives"
  cp "$addon_check_dir/${prefix_name}-${release_postfix}.zip" "archives/${prefix_name}-${release_postfix}.zip"
  git add "archives/${prefix_name}-${release_postfix}.zip"
  git commit -m "archive: ${release_tag_name}"
  git push origin HEAD:release-archive
)

github_release_body_path=$(mktemp)
release_note_path=$(mktemp)
gh release view "$release_tag_name" --json body --jq .body | tee "$github_release_body_path"
cat >"$release_note_path" <<EOFNOTE


1. Download the zip file from [GitHub Releases](https://github.com/saturday06/VRM-Addon-for-Blender/releases/tag/$release_tag_name)
2. In Blender, go to Edit > Preferences > Add-ons > Install
3. Select the downloaded zip file
4. Enable the addon


$(cat "$github_release_body_path")
EOFNOTE

echo "Release note for Blender Extensions:"
cat "$release_note_path"
