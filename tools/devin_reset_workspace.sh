#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux -o pipefail

cd "$(dirname "$0")/.."

(
  # このファイル自身も削除されたり変更されたりするので、
  # 一度シェルに最後まで読ませるために括弧で囲む。
  git fetch --prune
  git reset --hard origin/main
  find . -mindepth 1 -maxdepth 1 -name .git -prune -o -exec rm -fr {} \;
  git restore .
  git submodule update --init --recursive
)
