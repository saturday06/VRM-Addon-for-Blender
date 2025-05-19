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
  4.2; do
  mkdir -p "$HOME/.config/blender/$blender_version/extensions/user_default"
  ln -Tfs "$PWD/src/io_scene_vrm" "$HOME/.config/blender/$blender_version/extensions/user_default/vrm"
done
for blender_version in \
  4.1 \
  4.0 \
  3.6 \
  3.5 \
  3.4 \
  3.3 \
  3.2 \
  3.1 \
  3.0 \
  2.93; do
  mkdir -p "$HOME/.config/blender/$blender_version/scripts/addons"
  ln -Tfs "$PWD/src/io_scene_vrm" "$HOME/.config/blender/$blender_version/scripts/addons/io_scene_vrm"
done
