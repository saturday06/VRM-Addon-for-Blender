#!/bin/bash

set -eux -o pipefail

ln -fsv "$(poetry env info --path)" .venv-devcontainer

git ls-files | while read -r f; do
  case "$(git ls-files -s "$f" | awk '{print $1}')" in
  100644) chmod 644 "$f" ;;
  100755) chmod 755 "$f" ;;
  esac
done
