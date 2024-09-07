#!/bin/bash

set -eu -o pipefail

# Hyper-Vバックエンドで、ランダムで$PWDフォルダの所有者が変更されてしまい、gitがエラーになる問題を回避
git config --global --add safe.directory "$PWD"
git config --global --add safe.directory "$PWD/tests/resources"

# いちおうサブモジュールを取得するが、作業フォルダの状態次第で失敗するので `|| true` を付与
git submodule update --init --recursive || true

# システムのBlenderから開発中のアドオンをすぐに動作確認できるようにする
for blender_version in \
  4.3 \
  4.2; do
  mkdir -p "$HOME/.config/blender/$blender_version/extensions/user_default"
  ln -fs "$PWD/src/io_scene_vrm" "$HOME/.config/blender/$blender_version/extensions/user_default/vrm"
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
  ln -fs "$PWD/src/io_scene_vrm" "$HOME/.config/blender/$blender_version/scripts/addons/"
done
