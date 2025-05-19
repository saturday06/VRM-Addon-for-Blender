#!/bin/bash

set -eu -o pipefail

cd "$(dirname "$0")/.."

if [ "$(id --user --name)" = "developer" ]; then
  sudo env PYTHONDONTWRITEBYTECODE=1 ./tools/devcontainer_fixup_workspace_files.py
fi

./tools/devcontainer_create_venv.sh
