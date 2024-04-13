#!/bin/bash

set -eu -o pipefail

./tools/devcontainer_fixup_workspace.sh

# いちおうサブモジュールを取得するが、作業フォルダの状態次第で失敗するので `|| true` を付与
git submodule update --init --recursive || true

# 環境によってはpoetry installは5%くらいの頻度で失敗するのでリトライする
for _ in $(seq 5); do
  if poetry install; then
    break
  fi
done
