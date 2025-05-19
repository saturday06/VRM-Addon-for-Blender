#!/bin/bash

set -eu -o pipefail

cd "$(dirname "$0")/.."

pwd_and_system="$(pwd):$(uname -a)"
case "$(uname -s)" in
"Linux")
  hash="$(echo "$pwd_and_system" | sha256sum | cut -d' ' -f1)"
  ;;
"Darwin")
  hash="$(echo "$pwd_and_system" | shasum -a 256 | cut -d' ' -f1)"
  ;;
*)
  echo >&2 "Unsupported OS"
  exit 1
  ;;
esac

docker build \
  --tag "super-linter:$hash" \
  --file ./tools/super-linter.dockerfile \
  .

docker run \
  --rm \
  --volume "$(pwd):/tmp/lint" \
  "super-linter:$hash"
