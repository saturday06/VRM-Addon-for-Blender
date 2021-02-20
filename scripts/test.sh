#!/bin/sh

set -eux

cd "$(dirname "$0")/.."

poetry run python -m unittest discover
