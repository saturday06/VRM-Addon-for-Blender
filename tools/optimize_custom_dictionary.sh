#!/bin/sh
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eux

cd "$(dirname "$0")/.."

seq "$(wc -l dictionary.txt | awk '{print $1}')" | while read -r n; do
  while sed -e "${n}d" dictionary.txt >removed.tmp; do
    if diff -u dictionary.txt removed.tmp; then
      break
    fi
    if ! (git ls-files "*.py" | xargs uv run flake8 --enable-extensions flake8-spellcheck --whitelist removed.tmp); then
      break
    fi
    cp removed.tmp dictionary.txt
  done
done
