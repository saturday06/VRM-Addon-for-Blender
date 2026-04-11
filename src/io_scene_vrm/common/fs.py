# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from pathlib import Path
from typing import Optional


def create_unique_indexed_directory_path(path: Path) -> Path:
    name = path.name
    max_retry_count = 100_000
    for count in range(max_retry_count):
        count_str = f".{count}" if count else ""
        path = path.with_name(name + count_str)
        try:
            path.mkdir(parents=True)
        except FileExistsError:
            continue
        except OSError as exception:
            message = f"Failed to create unique directory path: {path}"
            raise RuntimeError(message) from exception
        return path
    message = (
        "Failed to create unique directory path "
        + f"(max retries: {max_retry_count} exceeded): {path}"
    )
    raise RuntimeError(message)


def create_unique_indexed_file_path(path: Path, binary: Optional[bytes] = None) -> Path:
    suffix = path.suffix
    stem = path.stem
    max_retry_count = 100_000
    for count in range(max_retry_count):
        count_str = f".{count}" if count else ""
        path = path.with_name(stem + count_str + suffix)

        if binary is None:
            try:
                if not path.exists():
                    return path
            except OSError as exception:
                message = f"Failed to create unique file path: {path}"
                raise RuntimeError(message) from exception
            continue

        try:
            path.touch(exist_ok=False)
        except FileExistsError:
            continue
        except OSError as exception:
            message = f"Failed to create unique file path: {path}"
            raise RuntimeError(message) from exception

        try:
            path.write_bytes(binary)
        except OSError as exception:
            message = f"Failed to write data to unique file path: {path}"
            raise RuntimeError(message) from exception
        return path

    message = (
        "Failed to create unique file path "
        + f"(max retries: {max_retry_count} exceeded): {path}"
    )
    raise RuntimeError(message)
