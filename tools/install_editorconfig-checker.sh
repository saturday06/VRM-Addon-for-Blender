#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

mkdir -p ~/.local/bin

case "$(uname -m)" in
"x86_64")
  url=https://github.com/editorconfig-checker/editorconfig-checker/releases/download/v3.0.3/ec-linux-amd64.tar.gz
  md5=58f26c24feeed0d2bfbe0d89ba564a91
  bin_name=ec-linux-amd64
  ;;
"aarch64")
  url=https://github.com/editorconfig-checker/editorconfig-checker/releases/download/v3.0.3/ec-linux-arm64.tar.gz
  md5=732fb21660c5c79a63546d5ae65212c4
  bin_name=ec-linux-arm64
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
  --output "$HOME/editorconfig-checker.tar.gz" \
  "$url"

test "$(md5sum ~/editorconfig-checker.tar.gz)" = "$md5  $HOME/editorconfig-checker.tar.gz"
tar -x --strip-components=1 -f ~/editorconfig-checker.tar.gz
mv "$bin_name" ~/.local/bin/editorconfig-checker
chmod 755 ~/.local/bin/editorconfig-checker
