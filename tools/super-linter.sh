#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux -o pipefail

cd "$(dirname "$0")"

repository_root_path=$(
  cd ..
  pwd
)
cached_image_path=
cached_image_id=
if [ "${CI:-}" = "true" ]; then
  super_linter_tag_name="super-linter-local"
  if [ "${GITHUB_ACTIONS:-}" != "true" ]; then
    cached_image_path=ci-super-linter-local-image.tar.gz
    if [ -s "$cached_image_path" ]; then
      docker image load --input "$cached_image_path"
      cached_image_id=$(docker image inspect --format='{{.Id}}' "$super_linter_tag_name" || true)
    fi
  fi
else
  # To avoid duplication with docker images working in other folders or systems
  # Build using the combined hash value as the docker tag name
  pwd_and_system="$(pwd):$(uname -a)"
  pwd_and_system_hash=$(echo "$pwd_and_system" | md5sum | cut -d" " -f 1)
  super_linter_tag_name="super-linter-local-${pwd_and_system_hash}"
fi

docker \
  build \
  --platform=linux/amd64 \
  --progress=plain \
  --tag \
  "$super_linter_tag_name" \
  --file \
  super-linter.dockerfile \
  "$repository_root_path"

new_image_id=$(docker image inspect --format='{{.Id}}' "$super_linter_tag_name")
if [ -n "$cached_image_path" ] && [ "$cached_image_id" != "$new_image_id" ]; then
  # Build the super-linter image for execution. Since the dependencies requiring
  # download are massive and download failures frequently occur under poor network
  # conditions, store the final image in the CI cache for reuse.
  docker image save "$super_linter_tag_name" | gzip >"$cached_image_path"
fi

# Run the built super-linter.
# Assume an environment where bind mounts are not available, so perform a shallow copy
# of the repository to be linted into the container and run it.
super_linter_container_name="${super_linter_tag_name}-container"
docker container rm --force "$super_linter_container_name" || true
docker container create --rm --name "$super_linter_container_name" "$@" "$super_linter_tag_name"
lint_path=$(mktemp -d)
git clone --no-local --depth 1 "$repository_root_path" "$lint_path"
git -C "$repository_root_path" ls-files --cached --others --exclude-standard -z |
  rsync --archive --files-from=- --from0 --delete-missing-args "${repository_root_path}/" "${lint_path}/"
git -C "$lint_path" status --porcelain
docker container cp "${lint_path}/." "${super_linter_container_name}:/tmp/lint/"
docker container start --attach "$super_linter_container_name"

: ----- OK ----- : +
