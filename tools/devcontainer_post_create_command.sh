#!/bin/bash

set -eu -o pipefail

# いちおうサブモジュールを取得するが、ワーキングコピーの状態が悪いと失敗するので `|| true` を付与
git submodule update --init --recursive || true

# .venvがdevcontainer外のものと混ざるのを防ぐため、
# .devcontainer内に固有の.venvを作り
# あとで標準のものと別名でリンクを貼る
poetry config virtualenvs.in-project false

# 環境によってはpoetry installは5%くらいの頻度で失敗するのでリトライする
for _ in $(seq 5); do
  if poetry install; then
    break
  fi
done
