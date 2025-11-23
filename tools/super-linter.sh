#!/bin/sh
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux

cd "$(dirname "$0")/.."

# To avoid duplication with docker images working in other folders or systems
# Build using the combined hash value as the docker tag name
pwd_and_system="$(pwd):$(uname -a)"
case "$(uname -s)" in
"Linux")
  pwd_and_system_hash=$(echo "$pwd_and_system" | md5sum | cut -d" " -f 1)
  ;;
"Darwin")
  pwd_and_system_hash=$(echo "$pwd_and_system" | md5)
  ;;
*)
  exit 0
  ;;
esac
super_linter_tag_name="super-linter-local-${pwd_and_system_hash}"

# Build the super-linter image for execution. Since the dependencies requiring
# download are massive and download failures frequently occur under poor network
# conditions, store the final image in the CI cache for reuse.
ci_super_linter_local_image_path=ci-super-linter-local-image.tar.gz
image_id=
if [ "${CI:-}" = "true" ] && [ -s "$ci_super_linter_local_image_path" ]; then
  docker load --input "$ci_super_linter_local_image_path"
  image_id=$(docker inspect --format='{{.Id}}' "$super_linter_tag_name" || true)
fi
docker \
  build \
  --platform=linux/amd64 \
  --progress=plain \
  --tag \
  "$super_linter_tag_name" \
  --file \
  tools/super-linter.dockerfile \
  .
new_image_id=$(docker inspect --format='{{.Id}}' "$super_linter_tag_name")
if [ "$image_id" != "$new_image_id" ]; then
  docker save "$super_linter_tag_name" | gzip >"$ci_super_linter_local_image_path"
fi

# Run the built super-linter.
exec docker run --rm -v "${PWD}:/tmp/lint" "$super_linter_tag_name"
