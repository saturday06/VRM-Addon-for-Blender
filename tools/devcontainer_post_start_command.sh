#!/bin/bash

set -eux -o pipefail

# .venvがdevcontainer外のものと混ざるのを防ぐため、
# .devcontainer内に固有の.venvを作り
# あとで標準のものと別名でリンクを貼る
poetry config virtualenvs.in-project false
poetry env info
poetry run python --version # 稀にvenvが壊れていることがある。このコマンドで復元する。
if ! ln -fsv "$(poetry env info --path)" .venv-devcontainer; then
  sudo rm -f .venv-devcontainer
  ln -fsv "$(poetry env info --path)" .venv-devcontainer
fi

# 発生条件は不明だが、稀にファイルの所有者がすべてroot:rootになることがある
# 「Unsafeなパーミッションのレポジトリを操作している」という警告が出るので所有権を自分に設定する。
# またmacOSでは.gitフォルダ内のファイルの所有者が変更できないエラーが発生するので `|| true` を付与している。
# 失敗した場合結局「Unsafeなパーミッションのレポジトリを操作している」が警告が
# 発生するはずだが、なぜか出なかった。誤って警告を抑制したのかもしれないが要調査
(sudo chown -R blender-vrm:blender-vrm . 2>&1 | sponge | head) || true

# 発生条件は不明だが、稀にファイルのパーミッションがすべて777になり、
# かつgit diffでパーミッションの変更が検知されないという状況になる。
# git ls-filesの値は正常のため、それに従ってパーミッションを再設定する。
set +x # ここから出力が多いので抑制
git ls-files --recurse-submodules | while read -r f; do
  case "$(git ls-files --recurse-submodules --format='%(objectmode)' "$f")" in
  "100755")
    base_permission="7"
    ;;
  "100644")
    base_permission="6"
    ;;
  *)
    continue
    ;;
  esac

  current_permission=$(stat -c %a "$f")

  # グループと他人のパーミッションはマスク
  group_other_permission=$(perl -e 'printf("%02o", oct($ARGV[0]) & oct($ARGV[1]));' "${current_permission:1:2}" "${base_permission}${base_permission}")
  # 自分のパーミッションは固定し、調整後のパーミッションを作成
  valid_permission="${base_permission}${group_other_permission}"
  if [ "$current_permission" != "$valid_permission" ]; then
    chmod -v "$valid_permission" "$f"
  fi
done
