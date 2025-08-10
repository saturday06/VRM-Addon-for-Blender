#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

mkdir -p ~/.local/bin

case "$(uname -m)" in
"x86_64")
  url=https://github.com/mvdan/sh/releases/download/v3.12.0/shfmt_v3.12.0_linux_amd64
  sha256=d9fbb2a9c33d13f47e7618cf362a914d029d02a6df124064fff04fd688a745ea
  ;;
"aarch64")
  url=https://github.com/mvdan/sh/releases/download/v3.12.0/shfmt_v3.12.0_linux_arm64
  sha256=5f3fe3fa6a9f766e6a182ba79a94bef8afedafc57db0b1ad32b0f67fae971ba4
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
  --output shfmt.tmp \
  "$url"

test "$(sha256sum shfmt.tmp)" = "$sha256  shfmt.tmp"
chmod 755 shfmt.tmp
mv shfmt.tmp ~/.local/bin/shfmt
