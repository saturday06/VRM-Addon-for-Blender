#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

cd "$(dirname "$0")/../.local"
mkdir -p bin

case "$(uname -m)" in
"x86_64")
  url="https://github.com/nektos/act/releases/download/v0.2.84/act_Linux_x86_64.tar.gz"
  ;;
"aarch64")
  url="https://github.com/nektos/act/releases/download/v0.2.84/act_Linux_arm64.tar.gz"
  ;;
*)
  exit 0
  ;;
esac

install_path="${PWD}/bin/"
cd "$(mktemp -d)"

curl \
  --fail \
  --show-error \
  --location \
  --retry 20 \
  --retry-all-errors \
  --output act.tar.gz \
  "$url"

tar xf act.tar.gz
mv act "$install_path"
