# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import Optional, Union

from bpy.types import Library

def abspath(
    path: str,
    start: Union[str, bytes, None] = None,
    library: Optional[Library] = None,
) -> str: ...
def basename(path: str) -> str: ...
def clean_name(name: str, replace: str = "_") -> str: ...
