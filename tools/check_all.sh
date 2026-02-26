#!/usr/bin/env bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -euo pipefail

cd "$(dirname "$0")/.."

printf '### uv sync ###\n'
uv sync

printf '### format (ruff format, ruff check --fix, shfmt, deno fmt) ###\n'
./tools/format.sh

printf '### lint (ruff, codespell, deno lint, pyright, vrm-validator) ###\n'
./tools/lint.sh

if [[ "${SKIP_TESTS:-}" == "1" || "${SKIP_TESTS:-}" == "true" ]]; then
  printf '### tests skipped (SKIP_TESTS=%s) ###\n' "${SKIP_TESTS}"
else
  printf '### tests (unittest discover) ###\n'
  ./tools/test.sh
fi
