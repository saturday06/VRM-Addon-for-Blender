#!/bin/sh

set -eux

cd "$(dirname "$0")/.."

poetry check
git ls-files "*.sh" | xargs shellcheck
git ls-files "*.py" | xargs poetry run mypy --show-error-codes
git ls-files "*.py" | xargs poetry run flake8 --count --show-source --statistics
git ls-files "*.py" | xargs poetry run pylint
git ls-files "*.py" | xargs poetry run pyright
