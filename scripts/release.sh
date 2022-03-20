#!/bin/sh

set -eux
shellcheck "$0"

export PYTHONDONTWRITEBYTECODE=1
prefix_name=VRM_Addon_for_Blender

tag_name=$(git describe --tags --exact-match || true)
if [ -z "$tag_name" ]; then
  exit 1
fi

version=$(ruby -e "puts ARGV[0].split('_', 3).join('.')" "$tag_name")
bl_info_version=$(python3 -c 'import io_scene_vrm; print(str(".".join(map(str, io_scene_vrm.bl_info["version"]))))')
if [ "$version" != "$bl_info_version" ]; then
  release_postfix=draft
elif [ "$(git rev-parse origin/main)" != "$(git rev-parse HEAD)" ]; then
  release_postfix=develop
else
  release_postfix=release
fi

for postfix in "$release_postfix" "$tag_name"; do
  work_dir=$(mktemp -d)
  base="${prefix_name}-${postfix}"
  cp -r io_scene_vrm "${work_dir}/${base}"
  cp -r LICENSE* "${work_dir}/${base}/"
  (
    cd "$work_dir"
    advzip --add --shrink-insane --iter 20 "${prefix_name}-${postfix}.zip" "${base}"
  )
  cp "${work_dir}/${prefix_name}-${postfix}.zip" .
done

if ! curl \
  --fail-with-body \
  --show-error \
  --location \
  --output release.json \
  --request POST \
  --data "{\"tag_name\":\"$tag_name\", \"name\": \"[DRAFT] Version $version\", \"draft\": true, \"prerelease\": true, \"generate_release_notes\": true}" \
  --header 'Accept: application/vnd.github.v3+json' \
  --header "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/$GITHUB_REPOSITORY/releases"; then

  cat release.json
  exit 1
fi

upload_url=$(ruby -rjson -e "puts JSON.parse(File.read('release.json'))['upload_url'].sub(/{.+}$/, '')")

if ! curl \
  --fail-with-body \
  --show-error \
  --location \
  --output release_upload.json \
  --request POST \
  --header 'Accept: application/vnd.github.v3+json' \
  --header "Authorization: Bearer $GITHUB_TOKEN" \
  --header "Content-Type: application/zip" \
  --data-binary "@${prefix_name}-${tag_name}.zip" \
  "${upload_url}?name=${prefix_name}-${tag_name}.zip&label=VRM%20Add-on%20for%20Blender%20${version}%20(zip)"; then

  cat release_upload.json
  exit 1
fi

archive_dir=$(mktemp -d)
git worktree add "${archive_dir}" release-archive
cp "${prefix_name}-${release_postfix}.zip" "${archive_dir}/"
(
  cd "${archive_dir}"
  git add "${prefix_name}-${release_postfix}.zip"
  git config --global user.email "isamu@leafytree.jp"
  git config --global user.name "Isamu Mogi (BOT)"
  git commit -m "Version $version"
  git push origin HEAD
)
