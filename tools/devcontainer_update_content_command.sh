#!/bin/bash

set -eu -o pipefail

./tools/devcontainer_fixup_workspace.sh

poetry run python -c "" # 稀にvenvが壊れていることがある。このコマンドで復元する。
if ! ln -fs "$(poetry env info --path)" .venv-devcontainer; then
  sudo rm -f .venv-devcontainer
  ln -fsv "$(poetry env info --path)" .venv-devcontainer
fi

# Refreshing repository
# https://git-scm.com/docs/git-status#_background_refresh
git status
