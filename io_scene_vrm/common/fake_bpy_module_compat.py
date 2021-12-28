from typing import Optional

import bpy
from bpy.app.translations import pgettext as default_pgettext


def is_fake_bpy_module() -> bool:
    return bpy.app.binary_path is None


def pgettext(msg: str, msgctxt: Optional[str] = None) -> str:
    if is_fake_bpy_module():
        return msg
    return str(default_pgettext(msg, msgctxt))
