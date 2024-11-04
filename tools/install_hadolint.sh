#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

mkdir -p ~/.local/bin

case "$(uname -m)" in
"x86_64")
  url=https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64
  md5=4f6a32a281ff18f84351ab7b574dfe68
  ;;
"aarch64")
  url=https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-arm64
  md5=2faefba159991c4dd2a164ad68cdbdea
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
  --output hadolint.tmp \
  "$url"

test "$(md5sum hadolint.tmp)" = "$md5  hadolint.tmp"
chmod 755 hadolint.tmp
mv hadolint.tmp ~/.local/bin/hadolint
