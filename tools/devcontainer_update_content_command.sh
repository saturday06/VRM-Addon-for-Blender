#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

cd "$(dirname "$0")/.."

# Dockerイメージは積極的にキャッシュされ、パッケージが古いままのことが多いのでここでアップデート
sudo ./tools/install_ubuntu_packages.sh

./tools/devcontainer_fixup_workspace.sh

./tools/install_hadolint.sh
./tools/install_editorconfig-checker.sh

uv self update
deno upgrade

# システムのBlenderから開発中のアドオンをすぐに動作確認できるようにする
for blender_version in \
  4.5 \
  4.4 \
  4.3 \
  4.2; do
  mkdir -p "$HOME/.config/blender/$blender_version/extensions/user_default"
  ln -Tfs "$PWD/src/io_scene_vrm" "$HOME/.config/blender/$blender_version/extensions/user_default/vrm"
done
for blender_version in \
  4.1 \
  4.0 \
  3.6 \
  3.5 \
  3.4 \
  3.3 \
  3.2 \
  3.1 \
  3.0 \
  2.93; do
  mkdir -p "$HOME/.config/blender/$blender_version/scripts/addons"
  ln -Tfs "$PWD/src/io_scene_vrm" "$HOME/.config/blender/$blender_version/scripts/addons/io_scene_vrm"
done
