# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from bpy.types import Library

def abspath(
    path: str,
    start: str | bytes | None = None,
    library: Library | None = None,
) -> str: ...
def basename(path: str) -> str: ...
def clean_name(name: str, replace: str = "_") -> str: ...
