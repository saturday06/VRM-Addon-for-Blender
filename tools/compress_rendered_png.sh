#!/bin/sh

set -eux

cd "$(dirname "$0")/.."

for path in $(git ls-files "tests/**/*.png"); do
  zopflipng -m "$path" "${path}.zopflipng"
  mv "${path}.zopflipng" "$path"
done
