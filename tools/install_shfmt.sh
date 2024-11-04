#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

mkdir -p ~/.local/bin ~/.local/hugo_extended

case "$(uname -m)" in
"x86_64")
  url=https://github.com/mvdan/sh/releases/download/v3.9.0/shfmt_v3.9.0_linux_amd64
  md5=fda7444998e303df59afe61de38fe63a
  ;;
"aarch64")
  url=https://github.com/mvdan/sh/releases/download/v3.9.0/shfmt_v3.9.0_linux_arm64
  md5=3f07c773219b3666bff11950faa510b6
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

test "$(md5sum shfmt.tmp)" = "$md5  shfmt.tmp"
chmod 755 shfmt.tmp
mv shfmt.tmp ~/.local/bin/shfmt
