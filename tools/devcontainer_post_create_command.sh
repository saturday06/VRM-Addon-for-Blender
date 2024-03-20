#!/bin/bash

set -eux -o pipefail

# 発生条件は不明だが、稀にファイルの所有者がすべてroot:rootになることがある
# 「Unsafeなパーミッションのレポジトリを操作している」という警告が出るので所有権を自分に設定する。
# またmacOSでは.gitフォルダ内のファイルの所有者が変更できないエラーが発生するので `|| true` を付与している。
# 失敗した場合結局「Unsafeなパーミッションのレポジトリを操作している」が警告が
# 発生するはずだが、なぜか出なかった。誤って警告を抑制したのかもしれないが要調査
sudo chown -R vscode:vscode . || true

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