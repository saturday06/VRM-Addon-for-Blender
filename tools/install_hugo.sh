#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

mkdir -p ~/.local/bin ~/.local/hugo_extended

case "$(uname -m)" in
"x86_64")
  url=https://github.com/gohugoio/hugo/releases/download/v0.111.3/hugo_extended_0.111.3_linux-amd64.tar.gz
  md5=6e04ed51c93be2332a47255e98607e7c
  ;;
"aarch64")
  url=https://github.com/gohugoio/hugo/releases/download/v0.111.3/hugo_extended_0.111.3_linux-arm64.tar.gz
  md5=8bcfa8ae2039217b46f2283e16079aa9
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
  --output "$HOME/hugo_extended.tar.gz" \
  "$url"

test "$(md5sum ~/hugo_extended.tar.gz)" = "$md5  $HOME/hugo_extended.tar.gz"
tar -C ~/.local/hugo_extended -xf ~/hugo_extended.tar.gz
ln -fs ~/.local/hugo_extended/hugo ~/.local/bin/hugo
