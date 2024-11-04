#!/usr/bin/python3
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
"""devcontainerの作業フォルダの所有者とパーミッションを正しい値に戻す.

このスクリプトはrootで実行する。rootの権限は強力すぎるため、
uvは経由せずOSのパッケージのみを用いて実行する。
"""

import functools
import grp
import logging
import os
import pwd
import stat
import sys
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

import tqdm as type_checking_tqdm
from dulwich.repo import Repo
from typing_extensions import TypeAlias

if TYPE_CHECKING:
    tqdm: TypeAlias = type_checking_tqdm.tqdm[NoReturn]  # noqa: PYI042
else:
    tqdm: TypeAlias = type_checking_tqdm.tqdm  # noqa: PYI042

logger = logging.getLogger(__name__)


if sys.platform == "win32":
    raise NotImplementedError


def print_path_walk_error(warning_messages: list[str], os_error: OSError) -> None:
    warning_messages.append(f"Failed to walk directories: {os_error}")


def fixup_directory_owner_and_permission(
    directory: Path, warning_messages: list[str], *, uid: int, gid: int, umask: int
) -> None:
    try:
        st = directory.lstat()
    except OSError:
        warning_messages.append(f"Failed to lstat: {directory}")
        return

    if st.st_uid != uid or st.st_gid != gid:
        try:
            os.lchown(directory, uid, gid)
        except OSError:
            warning_messages.append(f"Failed to change owner: {directory}")
            return

    if stat.S_ISLNK(st.st_mode):
        return

    st_valid_mode = (st.st_mode | stat.S_IRWXU) & ~umask
    if st.st_mode != st_valid_mode:
        try:
            directory.chmod(st_valid_mode)
        except OSError:
            warning_messages.append(f"Failed to change permission: {directory}")


def fixup_files(warning_messages: list[str], progress: tqdm) -> None:
    uid = pwd.getpwnam("developer").pw_uid
    gid = grp.getgrnam("developer").gr_gid
    umask = 0o022
    total_progress_count = 0

    # 発生条件は不明だが、稀にファイルの所有者がすべてroot:rootになることがある
    # 「Unsafeなパーミッションのレポジトリを操作している」という警告が出るので
    # 所有権を自分に設定する。また、再帰的に処理ができるようにパーミッションも再設定する
    workspace_path = Path(__file__).parent.parent
    fixup_directory_owner_and_permission(
        workspace_path, warning_messages, uid=uid, gid=gid, umask=umask
    )
    total_progress_count += 1
    all_file_paths: list[Path] = [workspace_path]
    for root, directory_names, file_names in os.walk(
        workspace_path,
        onerror=functools.partial(print_path_walk_error, warning_messages),
    ):
        root_path = Path(root)
        progress.update()
        for directory_name in directory_names:
            fixup_directory_owner_and_permission(
                root_path / directory_name,
                warning_messages,
                uid=uid,
                gid=gid,
                umask=umask,
            )

        file_count = len(file_names)
        progress.update(file_count)
        total_progress_count += file_count
        all_file_paths.extend(
            [(root_path / file_name).absolute() for file_name in file_names]
        )

    # gitレポジトリから、パスとそのパーミッションの対応表を得る
    git_index_path_to_mode: dict[Path, int] = {}
    repo = Repo(str(workspace_path))
    repo_index = repo.open_index()
    for path_bytes, _sha, mode in repo_index.iterobjects():
        progress.update()
        path_str = path_bytes.decode()
        if ".." in path_str:
            continue
        path = Path(path_str)
        if path.is_absolute():
            continue
        git_index_path_to_mode[path.absolute()] = mode
        total_progress_count += 1

    progress.reset(total=total_progress_count)

    # ファイルのパーミッションを可能な限り正しく設定
    for file_path in all_file_paths:
        progress.update()

        try:
            st = file_path.lstat()
        except OSError:
            warning_messages.append(f"Failed to lstat: {file_path}")
            continue

        if st.st_uid != uid or st.st_gid != gid:
            try:
                os.lchown(file_path, uid, gid)
            except OSError:
                # macOSでは.gitフォルダ以下のファイルは所有者の変更に失敗することがある
                dot_git_path = Path(__file__).parent.parent / ".git"
                if not file_path.is_relative_to(dot_git_path):
                    warning_messages.append(f"Failed to change owner: {file_path}")
                continue

        if stat.S_ISLNK(st.st_mode):
            continue

        # git管理対象ファイルは、gitに保存されているパーミッションを反映する
        git_mode = git_index_path_to_mode.pop(file_path.absolute(), None)
        if git_mode is None:
            continue

        progress.update()

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
        current_group_other_permission = st.st_mode & 0o077
        valid_group_other_permission = (
            current_group_other_permission & max_group_other_permission
        )
        valid_permission = (
            (valid_single_permission << 6) | valid_group_other_permission
        ) & ~umask
        if (st.st_mode & 0o777) == valid_permission:
            continue

        valid_full_permission = (st.st_mode & ~0o777) | valid_permission
        try:
            file_path.chmod(valid_full_permission)
        except OSError:
            warning_messages.append(f"Failed to change permission: {file_path}")
            continue

    progress.update(len(git_index_path_to_mode))


def main() -> None:
    warning_messages: list[str] = []
    with tqdm(unit="files", ascii=" =", dynamic_ncols=True) as progress:
        fixup_files(warning_messages, progress)
    for index, warning_message in enumerate(warning_messages):
        if index > 5:
            logger.warning("...")
            break
        logger.warning(warning_message)


if __name__ == "__main__":
    main()
