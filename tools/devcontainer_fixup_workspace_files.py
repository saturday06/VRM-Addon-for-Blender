#!/usr/bin/python3
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
"""Restore the owner and permissions of the devcontainer workspace folder.

This script should be run as root. Since root privileges are too powerful,
it is executed using only OS packages without going through uv.
"""

import argparse
import grp
import logging
import os
import pwd
import stat
import sys
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

import tqdm as type_checking_tqdm
from pygit2 import Repository
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


def fixup_files(
    warning_messages: list[str],
    progress: tqdm,
    *,
    workspace_path: Path,
    uid: int,
    gid: int,
    umask: int,
) -> None:
    total_progress_count = 0

    dot_git_path = workspace_path / ".git"
    if not dot_git_path.is_dir():
        warning_messages.append(f"No .git folder: {dot_git_path}")
        return

    # Conditions are unknown, but rarely all file owners become root:root
    # A warning about "operating on unsafe permission repository" appears, so
    # set ownership to yourself. Also reset permissions for recursive processing
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

    # Get path and permission mapping from git repository
    git_index_path_to_mode: dict[Path, int] = {}
    repo = Repository(str(workspace_path))
    for index_entry in repo.index:
        progress.update()
        path_str = index_entry.path
        if ".." in path_str:
            continue
        path = Path(path_str)
        if path.is_absolute():
            continue
        git_index_path_to_mode[path.absolute()] = int(index_entry.mode)
        total_progress_count += 1

    progress.reset(total=total_progress_count)

    # Set file permissions as correctly as possible
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
                # On macOS, changing ownership of files under .git folder may fail
                if not file_path.is_relative_to(dot_git_path):
                    warning_messages.append(f"Failed to change owner: {file_path}")
                continue

        if stat.S_ISLNK(st.st_mode):
            continue

        # For git-managed files, apply permissions stored in git
        git_mode = git_index_path_to_mode.pop(file_path.absolute(), None)
        if git_mode is None:
            continue

        git_mode &= 0o0777
        if git_mode == (st.st_mode & 0o0777):
            continue

        progress.update()

        try:
            file_path.chmod(git_mode)
        except OSError:
            warning_messages.append(f"Failed to change permission: {file_path}")
            continue

    progress.update(len(git_index_path_to_mode))


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Restore the owner and permissions of the devcontainer workspace folder."
        )
    )
    parser.add_argument(
        "--user",
        type=str,
        default="vscode",
        help="User name to set ownership to.",
    )
    parser.add_argument(
        "--group",
        type=str,
        default="vscode",
        help="Group name to set ownership to.",
    )
    args = parser.parse_args()

    uid = pwd.getpwnam(args.user).pw_uid
    gid = grp.getgrnam(args.group).gr_gid
    umask = 0o022
    workspace_path = Path.cwd()

    warning_messages: list[str] = []
    with tqdm(unit="files", ascii=" =", dynamic_ncols=True) as progress:
        fixup_files(
            warning_messages,
            progress,
            workspace_path=workspace_path,
            uid=uid,
            gid=gid,
            umask=umask,
        )
    for index, warning_message in enumerate(warning_messages):
        if index > 5:
            logger.warning("...")
            break
        logger.warning(warning_message)


if __name__ == "__main__":
    main()
