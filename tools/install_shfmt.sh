#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

mkdir -p ~/.local/bin

case "$(uname -m)" in
"x86_64")
  url=https://github.com/mvdan/sh/releases/download/v3.11.0/shfmt_v3.11.0_linux_amd64
  sha256=1904ec6bac715c1d05cd7f6612eec8f67a625c3749cb327e5bfb4127d09035ff
  ;;
"aarch64")
  url=https://github.com/mvdan/sh/releases/download/v3.11.0/shfmt_v3.11.0_linux_arm64
  sha256=b3976121710fd4b12bf641b0a7fb2686da598fb0da9f148c641b61b54cfa3407
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
