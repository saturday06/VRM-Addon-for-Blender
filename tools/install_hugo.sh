#!/bin/bash

set -eu -o pipefail

mkdir -p ~/.local/bin ~/.local/hugo_extended

case "$(uname -m)" in
"x86_64")
  url=https://github.com/gohugoio/hugo/releases/download/v0.111.3/hugo_extended_0.111.3_linux-amd64.tar.gz
  ;;
"aarch64")
  url=https://github.com/gohugoio/hugo/releases/download/v0.111.3/hugo_extended_0.111.3_linux-arm64.tar.gz
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
  --output ~/hugo_extended.tar.gz \
  "$url"

tar -C ~/.local/hugo_extended -xf ~/hugo_extended.tar.gz

ln -fs ~/.local/hugo_extended/hugo ~/.local/bin/hugo
