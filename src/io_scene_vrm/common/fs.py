# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import sys
from pathlib import Path
from typing import Optional


def create_unique_indexed_directory_path(path: Path) -> Path:
    name = path.name
    for count in range(sys.maxsize):
        count_str = f".{count}" if count else ""
        path = path.with_name(name + count_str)
        try:
            path.mkdir(parents=True)
        except OSError:
            continue
        return path
    message = f"Failed to create unique directory path: {path}"
    raise RuntimeError(message)


def create_unique_indexed_file_path(path: Path, binary: Optional[bytes] = None) -> Path:
    suffix = path.suffix
    stem = path.stem
    for count in range(sys.maxsize):
        count_str = f".{count}" if count else ""
        path = path.with_name(stem + count_str + suffix)

        if binary is None:
            if not path.exists():
                return path
            continue

        try:
            path.touch(exist_ok=False)
        except OSError:
            continue

        path.write_bytes(binary)
        return path

    message = f"Failed to create unique file path: {path}"
    raise RuntimeError(message)
