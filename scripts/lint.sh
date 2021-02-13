#!/bin/sh

set -eux

cd "$(dirname "$0")/.."

git ls-files "*.sh" | xargs -d '\n' shellcheck
git ls-files "*.py" | xargs -d '\n' poetry run mypy --show-error-codes
git ls-files "*.py" | xargs -d '\n' poetry run flake8 --count --show-source --statistics
