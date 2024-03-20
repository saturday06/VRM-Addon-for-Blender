#!/bin/bash

set -eux -o pipefail

# 発生条件は不明だが、稀にファイルの所有者がすべてroot:rootになることがある
sudo chown -R vscode:vscode .

# 発生条件は不明だが、稀にファイルのパーミッションがすべて777になり、
# かつgit diffでパーミッションの変更が検知されないという状況になる。
# git ls-filesの値は正常のため、それに従ってパーミッションを再設定する。
git ls-files | while read -r f; do
  case "$(git ls-files --format='%(objectmode)' "$f")" in
  "100755") chmod 755 "$f" ;;
  "100644") chmod 644 "$f" ;;
  esac
done

poetry install
