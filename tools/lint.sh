#!/bin/sh

set -eux

cd "$(dirname "$0")/.."

git ls-files "*.sh" | xargs shellcheck
git ls-files "*.py" "*.pyi" | xargs uv run ruff check
git ls-files "*.py" "*.pyi" | xargs uv run codespell
git ls-files "*.py" "*.pyi" | xargs uv run mypy --show-error-codes
git ls-files "*.py" "*.pyi" | xargs uv run pyright
git ls-files "*.sh" | xargs shfmt -d -s
git ls-files "*/Dockerfile" "*.dockerfile" | xargs hadolint
npm install
npm exec --yes -- prettier --check .
npm exec --yes --package=gltf-validator -- node ./tools/vrm-validator.js
