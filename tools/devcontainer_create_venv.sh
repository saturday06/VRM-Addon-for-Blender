#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

cd "$(dirname "$0")/.."

venv_prompt=venv
if ! uv venv --allow-existing --prompt "$venv_prompt"; then
  if ! sudo rm -fr .venv; then
    # Files that cannot be deleted may remain when switching Docker for Windows backends, etc.
    echo >&2 # Output newline for log formatting
    echo >&2 "####################################################"
    echo >&2 "Failed to remove '.venv'. Please remove it manually."
    echo >&2 "####################################################"
    exit 1
  fi
  uv venv --prompt "$venv_prompt"
fi

# Package installation fails about 5% of the time depending on the environment, so retry
for _ in $(seq 5); do
  if uv sync --reinstall-package starry-bpy-typings; then
    break
  fi
  sleep 10
done
