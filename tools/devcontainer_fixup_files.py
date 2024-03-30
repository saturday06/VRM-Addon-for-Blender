#!/usr/bin/python3
# mypy: ignore-errors
# pyright: reportArgumentType=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportGeneralTypeIssues=false
# pyright: reportInvalidTypeArguments=false
# pyright: reportMissingImports=false

import grp
import logging
import os
import pwd
import stat
from pathlib import Path

from dulwich.repo import Repo
from tqdm import tqdm

logger = logging.getLogger(__name__)


def print_path_walk_error(_os_error: OSError) -> None:
    logger.exception("Failed to walk directories")


progress = tqdm()

uid = pwd.getpwnam("blender-vrm").pw_uid
gid = grp.getgrnam("blender-vrm").gr_gid
umask = 0o022

file_process_count = 0

# 発生条件は不明だが、稀にファイルの所有者がすべてroot:rootになることがある
# 「Unsafeなパーミッションのレポジトリを操作している」という警告が出るので
# 所有権を自分に設定する。また、再帰的に処理ができるようにパーミッションも再設定する。
# macOSでは.gitフォルダ内のファイルの所有者が変更できないエラーが発生する
workspace_dir = Path(__file__).parent.parent
os.lchown(workspace_dir, uid, gid)
workspace_dir.lchmod(0o755)
all_file_paths: list[Path] = []
for root, directory_names, file_names in workspace_dir.walk(
    on_error=print_path_walk_error
):
    for directory_name in directory_names:
        directory = root / directory_name
        st = directory.lstat()
        st_mode = st.st_mode
        st_valid_mode = (st_mode | stat.S_IRWXU) & ~umask
        if st.st_uid != uid or st.st_gid != gid:
            os.lchown(directory, uid, gid)
        if st_mode != st_valid_mode:
            directory.lchmod(st_valid_mode)
    file_process_count += len(file_names)
    progress.update()
    all_file_paths.extend([root / file_name for file_name in file_names])

# gitレポジトリから、パスとそのパーミッションの対応表を得る
git_index_path_and_modes: list[(Path, int)] = []
repo = Repo(workspace_dir)
repo_index = repo.open_index()
for path_bytes, _sha, mode in repo_index.iterobjects():
    progress.update()
    path_str = path_bytes.decode()
    if ".." in path_str:
        continue
    path = Path(path_str)
    if path.is_absolute():
        continue
    git_index_path_and_modes.append((path.absolute(), mode))
    file_process_count += 1

progress.reset(total=file_process_count)

# ファイルの所有者を書き換える
path_and_st_modes: dict[Path, int] = {}
for file_path in all_file_paths:
    progress.update()

    st = file_path.lstat()
    st_mode = st.st_mode
    if st.st_uid != uid or st.st_gid != gid:
        os.lchown(file_path, uid, gid)

    path_and_st_modes[file_path.absolute()] = st_mode

# 発生条件は不明だが、稀にファイルのパーミッションがすべて777になり、
# かつgit diffでパーミッションの変更が検知されないという状況になる。
# gitのパーミッションに合わせる
changed_messages: list[str] = []
for path, git_mode in sorted(git_index_path_and_modes):
    progress.update()

    st_mode = path_and_st_modes.get(path)
    if st_mode is None:
        continue
    if git_mode == 0o100644:
        valid_single_permission = 0o6
    elif git_mode == 0o10755:
        valid_single_permission = 0o7
    else:
        continue

    # グループと他人のパーミッションはマスク
    # 自分のパーミッションは固定し、調整後のパーミッションを作成
    max_group_other_permission = (
        (valid_single_permission << 3) | valid_single_permission
    ) & ~umask
    current_group_other_permission = st_mode & 0o077
    valid_group_other_permission = (
        current_group_other_permission & max_group_other_permission
    )
    valid_permission = (
        (valid_single_permission << 6) | valid_group_other_permission
    ) & ~umask
    if (st_mode & 0o777) == valid_permission:
        continue

    valid_full_permission = (st_mode & ~0o777) | valid_permission
    path.lchmod(valid_full_permission)
    changed_messages.append(f"{path}: {oct(st_mode)} => {oct(valid_full_permission)}")

progress.close()

for changed_message in changed_messages:
    logger.warning(changed_message)
