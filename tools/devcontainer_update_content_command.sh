#!/bin/bash

set -eu -o pipefail

# Dockerイメージは積極的にキャッシュされ、パッケージが古いままのことが多いのでここでアップデート
sudo apt-get update
sudo apt-get dist-upgrade --yes

uv self update

./tools/install_hugo.sh
./tools/install_hadolint.sh
./tools/devcontainer_fixup_workspace.sh

# Refreshing repository
# https://git-scm.com/docs/git-status#_background_refresh
git status
