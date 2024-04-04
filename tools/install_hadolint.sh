#!/bin/bash

set -eu -o pipefail

mkdir -p ~/.local/bin

case "$(uname -m)" in
"x86_64")
  url=https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64
  ;;
"aarch64")
  url=https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-arm64
  ;;
*)
  exit 0
  ;;
esac

curl \
  --fail \
  --show-error \
  --location \
  --retry 20 \
  --retry-all-errors \
  --output ~/.local/bin/hadolint \
  "$url"

chmod 755 ~/.local/bin/hadolint
