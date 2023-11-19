#!/bin/sh

set -eux

cd "$(dirname "$0")/.."

git ls-files "*.py" | xargs poetry run ruff --fix
git ls-files "*.py" | xargs poetry run ruff format
git ls-files "*.sh" | xargs shfmt -w -s
