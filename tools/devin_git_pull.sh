#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

# Please copy and paste this file to devin's 'Git Pull' code input area.
cd ~/repos/VRM-Addon-for-Blender && git fetch --prune && git reset --hard origin/main && find . -mindepth 1 -maxdepth 1 -name .git -prune -o -exec rm -fr {} \; && git restore . && git submodule update --init --recursive
