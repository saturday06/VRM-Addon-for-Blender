#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

cd "$(dirname "$0")/.."

# In devcontainer, permission settings may be lost, so restore them.
/bin/bash ./tools/devcontainer_fixup_workspace.sh

# Docker images are aggressively cached and packages often remain outdated, so we update here
sudo ./tools/install_ubuntu_packages.sh

./tools/install_hadolint.sh
./tools/install_editorconfig-checker.sh

# error: GitHub API rate limit exceeded error may occur.
# In such cases, processing continues. In the future, we will make it possible to pass tokens.
uv self update || true

./tools/install_nvm.sh

deno upgrade

# deno install may fail, so retry several times.
for _ in $(seq 5); do
  if deno install; then
    break
  fi
  sleep 10
done

# Enable immediate testing of the addon under development from the system Blender
for blender_version in \
  5.2 \
  5.1 \
  5.0 \
  4.5 \
  4.4 \
  4.3 \
  4.2; do
  mkdir -p "${HOME}/.config/blender/$blender_version/extensions/user_default"
  ln -Tfs "${PWD}/src/io_scene_vrm" "${HOME}/.config/blender/$blender_version/extensions/user_default/vrm"
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
  mkdir -p "${HOME}/.config/blender/$blender_version/scripts/addons"
  ln -Tfs "${PWD}/src/io_scene_vrm" "${HOME}/.config/blender/$blender_version/scripts/addons/io_scene_vrm"
done

blender --background --python-expr 'import bpy; bpy.ops.preferences.addon_enable(module="io_scene_vrm"); bpy.ops.wm.save_userpref()'
