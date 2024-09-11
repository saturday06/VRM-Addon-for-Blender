#!/bin/bash

set -eu -o pipefail

# Dockerイメージは積極的にキャッシュされ、パッケージが古いままのことが多いのでここでアップデート
sudo dnf update -y

uv self update

./tools/install_hugo.sh
./tools/install_hadolint.sh
./tools/install_shfmt.sh
./tools/devcontainer_fixup_workspace.sh
