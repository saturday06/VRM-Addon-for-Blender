#!/bin/sh

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

docker \
  build \
  --platform=linux/amd64 \
  --progress=plain \
  --tag \
  "$super_linter_tag_name" \
  --file \
  tools/super-linter.dockerfile \
  .
exec docker run --rm -v "${PWD}:/tmp/lint" "$super_linter_tag_name"
