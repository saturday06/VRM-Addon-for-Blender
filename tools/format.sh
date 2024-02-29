#!/bin/sh

set -eux

cd "$(dirname "$0")/.."

git ls-files "*.py" | xargs poetry run ruff format
git ls-files "*.py" | xargs poetry run ruff check --fix
git ls-files "*.sh" | xargs shfmt -w -s
