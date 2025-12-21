#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux -o pipefail

validate_file_name_characters() (
  set +x

  git ls-files -z | while IFS= read -r -d '' f; do
    encoding=$(echo "$f" | uchardet)
    if [ "$encoding" != "ASCII" ]; then
      echo "$f is not ascii file name but $encoding."
      exit 1
    fi
  done

  git ls-files -z "*.py" "*.pyi" | while IFS= read -r -d '' f; do
    if [ "$f" != "$(echo "$f" | LC_ALL=C tr "[:upper:]" "[:lower:]")" ]; then
      echo "$f contains uppercase character"
      exit 1
    fi
  done
)

validate_permissions() (
  set +x

  git ls-files -z ':!tools/*.sh' ':!tools/*.py' ':!tests/resources' ':!typings' | while IFS= read -r -d '' f; do
    if [ -x "$f" ]; then
      echo "$f has unnecessary executable permission."
      exit 1
    fi
  done
  git ls-files -z 'tools/*.sh' 'tools/*.py' | while IFS= read -r -d '' f; do
    if [ ! -x "$f" ]; then
      echo "$f has no executable permission."
      exit 1
    fi
  done
)

validate_vrm_validator_works_correctly() (
  set +x

  for failure_vrm_path in failure.vrm tests/failure.vrm; do
    touch "$failure_vrm_path"
    if deno task vrm-validator 2>/dev/null; then
      echo "VRM Validator doesn't work correctly"
      exit 1
    fi
    rm "$failure_vrm_path"
  done
)

cd "$(dirname "$0")/.."

validate_file_name_characters
uv run python -c "import io_scene_vrm; io_scene_vrm.register(); io_scene_vrm.unregister()"
git ls-files -z "*.sh" | xargs -0 shellcheck
git ls-files -z "*.py" "*.pyi" | xargs -0 uv run ruff check
uv run codespell
git ls-files -z "*.sh" | xargs -0 shfmt -d
git ls-files -z "*/Dockerfile" "*.dockerfile" | xargs -0 hadolint
deno lint
deno task pyright
deno task vrm-validator
validate_vrm_validator_works_correctly
validate_permissions
