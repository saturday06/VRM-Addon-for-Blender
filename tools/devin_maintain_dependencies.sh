#!/bin/bash

set -eu -o pipefail

cd "$(dirname "$0")/.."

if ! command -v uv; then
  curl --fail --show-error --location https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.cargo/bin:$PATH"
fi

if ! command -v deno; then
  curl --fail --show-error --location https://deno.land/install.sh | sh -s -- --yes
  echo >>~/.bashrc
fi
