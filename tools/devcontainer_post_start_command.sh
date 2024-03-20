#!/bin/bash

set -eux -o pipefail

ln -fsv "$(poetry env info --path)" .venv-devcontainer
