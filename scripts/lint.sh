#!/bin/sh

set -eux

cd "$(dirname "$0")/.."

git ls-files "*.sh" | xargs shellcheck
git ls-files "*.py" | xargs poetry run mypy --show-error-codes
git ls-files "*.py" | xargs poetry run flake8 --count --show-source --statistics
