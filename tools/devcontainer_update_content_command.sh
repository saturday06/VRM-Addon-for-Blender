#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

# Dockerイメージは積極的にキャッシュされ、パッケージが古いままのことが多いのでここでアップデート
sudo apt update
sudo apt dist-upgrade --yes

./tools/devcontainer_fixup_workspace.sh

./tools/install_hugo.sh
./tools/install_hadolint.sh
./tools/install_shfmt.sh
./tools/install_editorconfig-checker.sh

uv self update
deno upgrade
