#!/bin/bash

set -eu -o pipefail

# .venvがdevcontainer外のものと混ざるのを防ぐため、
# .devcontainer内に固有の.venvを作り
# あとで標準のものと別名でリンクを貼る
poetry config virtualenvs.in-project false
poetry run python -c "" # 稀にvenvが壊れていることがある。このコマンドで復元する。
if ! ln -fs "$(poetry env info --path)" .venv-devcontainer; then
  sudo rm -f .venv-devcontainer
  ln -fs "$(poetry env info --path)" .venv-devcontainer
fi

sudo ./tools/devcontainer_fixup_files.py
