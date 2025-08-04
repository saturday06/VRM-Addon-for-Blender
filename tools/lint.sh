#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux -o pipefail

validate_file_name_characters() (
  set +x

  git ls-files | while read -r f; do
    encoding=$(echo "$f" | uchardet)
    if [ "$encoding" != "ASCII" ]; then
      echo "$f is not ascii file name but $encoding."
      exit 1
    fi
  done

  git ls-files "*.py" "*.pyi" | while read -r f; do
    if [ "$f" != "$(echo "$f" | LC_ALL=C tr "[:upper:]" "[:lower:]")" ]; then
      echo "$f contains uppercase character"
      exit 1
    fi
  done
)

cd "$(dirname "$0")/.."

validate_file_name_characters
git ls-files "*.sh" | xargs shellcheck
git ls-files "*.py" "*.pyi" | xargs uv run ruff check
git ls-files "*.py" "*.pyi" | xargs uv run codespell
git ls-files "*.sh" | xargs shfmt -d -s
git ls-files "*/Dockerfile" "*.dockerfile" | xargs hadolint
deno lint
deno task pyright
deno task vrm-validator
