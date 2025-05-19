#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

cd "$(dirname "$0")/.."

create_venv() (
  uv venv --prompt venv
)

create=yes

if grep -E "^home = /home/developer/.local/share/uv/python/" .venv/pyvenv.cfg >/dev/null &&
  readlink -e .venv/bin/python >/dev/null \
  ; then
  create=no
fi

if ([ "$create" = "yes" ] && ! create_venv) || ! uv run --isolated -- python -c ""; then
  if ! sudo rm -fr .venv; then
    echo >&2 # Line break for log formatting
    echo >&2 "####################################################"
    echo >&2 "Failed to remove '.venv'. Please remove it manually."
    echo >&2 "####################################################"
    exit 1
  fi
  create_venv
fi

for _ in $(seq 5); do
  if uv sync --reinstall-package starry-bpy-typings; then
    break
  fi
  sleep 10
done
