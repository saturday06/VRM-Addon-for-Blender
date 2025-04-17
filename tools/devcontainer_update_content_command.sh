#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

cd "$(dirname "$0")/.."

# Dockerイメージは積極的にキャッシュされ、パッケージが古いままのことが多いのでここでアップデート
if command -v dnf; then
  sudo dnf update -y
elif command -v apt-get; then
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y
fi

./tools/devcontainer_fixup_workspace.sh

./tools/install_hugo.sh
./tools/install_hadolint.sh
./tools/install_shfmt.sh
./tools/install_editorconfig-checker.sh

uv self update
deno upgrade
