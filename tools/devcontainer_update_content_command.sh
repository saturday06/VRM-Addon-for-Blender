#!/bin/bash

set -eu -o pipefail

cd "$(dirname "$0")/.."

sudo ./tools/install_ubuntu_packages.sh

./tools/devcontainer_fixup_workspace.sh
./tools/install_git_hooks.sh
./tools/install_hadolint.sh
./tools/install_editorconfig-checker.sh

uv self update || true

deno upgrade

for _ in $(seq 5); do
  if deno install; then
    break
  fi
  sleep 10
done

for blender_version in \
  4.5 \
  4.4 \
  4.3 \
  4.2 \
  4.1 \
  4.0 \
  3.6 \
  3.5 \
  3.4 \
  3.3 \
  ; do
  blender_addons_dir="$HOME/.config/blender/$blender_version/scripts/addons"
  if [ -d "$blender_addons_dir" ]; then
    mkdir -p "$blender_addons_dir"
    ln -sf "$(pwd)/src" "$blender_addons_dir/VRM_Addon_for_Blender"
  fi
done
