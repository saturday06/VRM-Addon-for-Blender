#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

mkdir -p ~/.local/bin

case "$(uname -m)" in
"x86_64")
  url=https://github.com/editorconfig-checker/editorconfig-checker/releases/download/v3.3.0/ec-linux-amd64.tar.gz
  md5=405182f7a0967abb5783f40d8bd311d4
  bin_name=ec-linux-amd64
  ;;
"aarch64")
  url=https://github.com/editorconfig-checker/editorconfig-checker/releases/download/v3.3.0/ec-linux-arm64.tar.gz
  md5=5e03ddaa306069427f6ddf2268a95bce
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
