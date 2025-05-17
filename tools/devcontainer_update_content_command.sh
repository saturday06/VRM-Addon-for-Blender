#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

cd "$(dirname "$0")/.."

# Dockerイメージは積極的にキャッシュされ、パッケージが古いままのことが多いのでここでアップデート
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y

./tools/devcontainer_fixup_workspace.sh

./tools/install_hadolint.sh
./tools/install_editorconfig-checker.sh

uv self update
deno upgrade
