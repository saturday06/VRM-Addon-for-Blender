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
warning_messages: list[str] = []
uid = pwd.getpwnam("blender-vrm").pw_uid
gid = grp.getgrnam("blender-vrm").gr_gid
umask = 0o022


def print_path_walk_error(os_error: OSError) -> None:
    warning_messages.append(f"Failed to walk directories: {os_error}")


def fixup_directory_owner_and_permission(directory: Path) -> None:
    try:
        st = directory.lstat()
        st_mode = st.st_mode
    except OSError:
        warning_messages.append(f"Failed to lstat: {directory}")
        return

    if st.st_uid != uid or st.st_gid != gid:
        try:
            os.lchown(directory, uid, gid)
        except OSError:
            warning_messages.append(f"Failed to change owner: {directory}")
            return

    st_valid_mode = (st_mode | stat.S_IRWXU) & ~umask
    if st_mode != st_valid_mode:
        try:
            directory.lchmod(st_valid_mode)
        except OSError:
            warning_messages.append(f"Failed to change permission: {directory}")


with tqdm(unit="files") as progress:
    total_progress_count = 0

    # 発生条件は不明だが、稀にファイルの所有者がすべてroot:rootになることがある
    # 「Unsafeなパーミッションのレポジトリを操作している」という警告が出るので
    # 所有権を自分に設定する。また、再帰的に処理ができるようにパーミッションも再設定する
    # macOSでは.gitフォルダ内のファイルの所有者が変更できないエラーが発生する
    workspace_path = Path(__file__).parent.parent
    fixup_directory_owner_and_permission(workspace_path)
    all_file_paths: list[Path] = []
    for root, directory_names, file_names in workspace_path.walk(
        on_error=print_path_walk_error
    ):
        progress.update()
        for directory_name in directory_names:
            fixup_directory_owner_and_permission(root / directory_name)

        file_count = len(file_names)
        progress.update(file_count)
        total_progress_count += file_count
        all_file_paths.extend([root / file_name for file_name in file_names])

    # gitレポジトリから、パスとそのパーミッションの対応表を得る
    git_index_path_and_modes: list[(Path, int)] = []
    repo = Repo(workspace_path)
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
        total_progress_count += 1

    progress.reset(total=total_progress_count)

    # ファイルの所有者を書き換える
    path_and_st_modes: dict[Path, int] = {}
    for file_path in all_file_paths:
        progress.update()

        try:
            st = file_path.lstat()
        except OSError:
            warning_messages.append(f"Failed to lstat: {file_path}")
            continue

        st_mode = st.st_mode
        if st.st_uid != uid or st.st_gid != gid:
            try:
                os.lchown(file_path, uid, gid)
            except OSError:
                warning_messages.append(f"Failed to change owner: {file_path}")
                continue

        path_and_st_modes[file_path.absolute()] = st_mode

    # 発生条件は不明だが、稀にファイルのパーミッションがすべて777になり、
    # かつgit diffでパーミッションの変更が検知されないという状況になる。
    # gitのパーミッションに合わせる
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
        try:
            path.lchmod(valid_full_permission)
        except OSError:
            warning_messages.append(f"Failed to change permission: {path}")
            continue
        warning_messages.append(
            f"{path}: {oct(st_mode)} => {oct(valid_full_permission)}"
        )

for warning_message in warning_messages:
    logger.warning(warning_message)
