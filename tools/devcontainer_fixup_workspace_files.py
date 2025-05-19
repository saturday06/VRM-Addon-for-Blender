#!/usr/bin/python3
"""Restore the owner and permissions of devcontainer's working directory.

This script is executed as root. Since root privileges are too powerful,
use only OS packages without going through uv.
"""

import os
import stat
import sys
import warnings
from pathlib import Path
from typing import List, Set, TypeVar

try:
    from pygit2 import Repository
except ImportError:
    print(
        "pygit2 is not installed. Please install it with `apt-get install python3-pygit2`"
    )
    sys.exit(1)

try:
    from rich.progress import Progress
except ImportError:
    T = TypeVar("T")

    class DummyProgress:
        def __enter__(self):
            return self

        def __exit__(self, *args, **kwargs):
            pass

        def add_task(self, *args, **kwargs):
            return 0

        def update(self, *args, **kwargs):
            pass

        def reset(self, *args, **kwargs):
            pass

    Progress = DummyProgress  # type: ignore


def fixup_directory_owner_and_permission(
    directory_path: Path,
    warning_messages: List[str],
    uid: int,
    gid: int,
    umask: int,
) -> None:
    """Fix the owner and permission of a directory."""
    try:
        os.lchown(directory_path, uid, gid)
    except OSError:
        warning_messages.append(f"Failed to change owner: {directory_path}")

    try:
        st = os.lstat(directory_path)
        if stat.S_ISDIR(st.st_mode):
            os.chmod(directory_path, 0o755 & ~umask)
    except OSError:
        warning_messages.append(f"Failed to change permission: {directory_path}")


def main() -> None:
    """Main function."""
    warning_messages: List[str] = []
    uid = os.getuid()
    gid = os.getgid()
    umask = 0o022
    total_progress_count = 0

    workspace_path = Path(__file__).parent.parent
    fixup_directory_owner_and_permission(
        workspace_path, warning_messages, uid=uid, gid=gid, umask=umask
    )

    all_file_paths: Set[Path] = set()
    root_path = workspace_path.absolute()

    with Progress() as progress:
        task = progress.add_task("Collecting files...", total=None)

        for root, _, file_names in os.walk(root_path, topdown=False):
            progress.update(task)
            for file_name in file_names:
                file_path = Path(root) / file_name
                all_file_paths.add(file_path)
                total_progress_count += 1

        progress.update(
            task,
            total=total_progress_count,
            completed=total_progress_count,
        )

    git_index_path_to_mode: dict[Path, int] = {}
    repo = Repository(str(workspace_path))
    for index_entry in repo.index:
        try:
            file_path = workspace_path / index_entry.path
            git_index_path_to_mode[file_path.absolute()] = index_entry.mode
        except Exception as e:
            warning_messages.append(f"Failed to get git index entry: {e}")

    progress.reset(total=total_progress_count)

    for file_path in all_file_paths:
        progress.update()

        try:
            st = os.lstat(file_path)
        except OSError:
            warning_messages.append(f"Failed to get file stat: {file_path}")
            continue

        if st.st_uid != uid or st.st_gid != gid:
            try:
                os.lchown(file_path, uid, gid)
            except OSError:
                dot_git_path = Path(__file__).parent.parent / ".git"
                if not file_path.is_relative_to(dot_git_path):
                    warning_messages.append(f"Failed to change owner: {file_path}")

        if stat.S_ISLNK(st.st_mode):
            continue

        git_mode = git_index_path_to_mode.pop(file_path.absolute(), None)
        if git_mode is None:
            continue

        valid_single_permission = 0
        if git_mode & stat.S_IXUSR:
            valid_single_permission = 0o1
        elif git_mode & stat.S_IRUSR:
            valid_single_permission = 0o4
        else:
            continue

        max_group_other_permission = (
            (valid_single_permission << 3) | valid_single_permission
        ) & ~umask
        valid_permission = (valid_single_permission << 6) | max_group_other_permission

        try:
            os.chmod(file_path, valid_permission)
        except OSError:
            warning_messages.append(f"Failed to change permission: {file_path}")

    for warning_message in warning_messages:
        warnings.warn(warning_message)


if __name__ == "__main__":
    main()
