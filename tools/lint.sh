#!/bin/sh

set -eux

cd "$(dirname "$0")/.."

git ls-files "*.sh" | xargs shellcheck
git ls-files "*.py" "*.pyi" | xargs uv run ruff check
git ls-files "*.py" "*.pyi" | xargs uv run codespell
git ls-files "*.py" "*.pyi" | xargs uv run mypy --show-error-codes
git ls-files "*.sh" | xargs shfmt -d -s
git ls-files "*/Dockerfile" "*.dockerfile" | xargs hadolint
npm install
npm exec --yes -- pyright --warnings --pythonpath .venv/bin/python3
npm exec --yes -- prettier --check .
npm exec --yes --package=gltf-validator -- node ./tools/vrm_validator.js
