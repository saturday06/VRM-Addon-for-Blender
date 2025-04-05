# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from pathlib import Path

from bpy.types import Context, Object


class UniVrmVrmAnimationImporter:
    """Import VRM animation. The import result is the same as UniVRM.

    https://github.com/vrm-c/UniVRM
    """

    @staticmethod
    def execute(_context: Context, _path: Path, _armature: Object) -> set[str]:
        return {"CANCELLED"}
