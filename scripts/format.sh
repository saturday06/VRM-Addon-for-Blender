#!/bin/sh

set -eux

cd "$(dirname "$0")/.."

git ls-files "*.py" | xargs -d '\n' poetry run autoflake --in-place --remove-all-unused-imports --remove-unused-variables
git ls-files "*.py" | xargs -d '\n' poetry run isort
git ls-files "*.py" | xargs -d '\n' poetry run black
