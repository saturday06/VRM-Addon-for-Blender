#!/bin/bash

set -eu -o pipefail

# Dockerイメージは積極的にキャッシュされ、パッケージが古いままのことが多いのでここでアップデート
sudo dnf update -y

./tools/devcontainer_fixup_workspace.sh

./tools/install_hugo.sh
./tools/install_hadolint.sh
./tools/install_shfmt.sh

uv self update
