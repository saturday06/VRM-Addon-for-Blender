#!/bin/sh

set -eux

cd "$(dirname "$0")/.."

uv run python -m unittest discover
