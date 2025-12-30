#!/bin/sh
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux

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
exec docker run --rm -v "${repository_root_path}:/tmp/lint" "$super_linter_tag_name"
