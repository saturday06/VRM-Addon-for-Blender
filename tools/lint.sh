#!/bin/sh

set -eux

cd "$(dirname "$0")/.."

poetry check
git ls-files "*.sh" | xargs shellcheck
git ls-files "*.py" | xargs poetry run ruff check
git ls-files "*.py" | xargs poetry run codespell
git ls-files "*.py" | xargs poetry run mypy --show-error-codes
git ls-files "*.py" | xargs poetry run pyright
git ls-files "*.sh" | xargs shfmt -d -s
git ls-files "*/Dockerfile" "*.dockerfile" | xargs hadolint
