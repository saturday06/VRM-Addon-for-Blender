#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

cd "$(dirname "$0")/.."

# Hyper-Vバックエンドで、ランダムで$PWDフォルダの所有者が変更されてしまい、gitがエラーになる問題を回避
git config --global --add safe.directory "$PWD"

# システムのBlenderから開発中のアドオンをすぐに動作確認できるようにする
for blender_version in \
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
