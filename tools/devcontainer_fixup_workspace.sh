#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

cd "$(dirname "$0")/.."

if [ "$(id --user --name)" = "developer" ]; then
  # Set the owner and permissions of the working folder.
  # Since sudo is too powerful, use only OS packages without going through uv.
  sudo env PYTHONDONTWRITEBYTECODE=1 ./tools/devcontainer_fixup_workspace_files.py
fi

./tools/devcontainer_create_venv.sh
