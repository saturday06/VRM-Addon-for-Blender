#!/bin/sh

set -eux

cd "$(dirname "$0")/.."

seq "$(wc -l whitelist.txt | awk '{print $1}')" | while read -r n; do
  while sed -e "${n}d" whitelist.txt > removed.tmp; do
    if ! (git ls-files "*.py" | xargs poetry run flake8 --enable-extensions flake8-spellcheck --whitelist removed.tmp); then
      break
    fi
    cp removed.tmp whitelist.txt
  done
done
