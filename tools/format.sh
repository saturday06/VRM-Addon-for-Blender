#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux -o pipefail

cd "$(dirname "$0")/.."

git ls-files "*.py" "*.pyi" | xargs uv run ruff format
git ls-files "*.py" "*.pyi" | xargs uv run ruff check --fix
git ls-files "*.sh" | xargs shfmt -w -s
deno fmt
