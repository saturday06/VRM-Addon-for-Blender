#!/bin/sh
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux

cd "$(dirname "$0")/.."

exec uv run python -m unittest discover
