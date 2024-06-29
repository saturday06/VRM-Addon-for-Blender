#!/bin/bash

set -eu -o pipefail

./tools/devcontainer_fixup_workspace.sh

# Refreshing repository
# https://git-scm.com/docs/git-status#_background_refresh
git status
