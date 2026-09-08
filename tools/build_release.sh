#!/bin/sh
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu

exec "$(dirname "$0")/release_to_github.sh" --dry-run "$@"
