# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import TYPE_CHECKING

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Event, Operator

from ..common import ops


class VRM_OT_import_vrm_via_file_handler(Operator):
    bl_idname = "vrm.import_vrm_via_file_handler"
    bl_label = "Import VRM via FileHandler"

    filepath: StringProperty(  # type: ignore[valid-type]
        subtype="FILE_PATH",
        options={"SKIP_SAVE"},
    )

    @classmethod
    def poll(cls, _context: Context) -> bool:
        return True

    def execute(self, _context: Context) -> set[str]:
        return ops.import_scene.vrm(filepath=self.filepath, use_addon_preferences=True)

    def invoke(self, context: Context, _event: Event) -> set[str]:
        return self.execute(context)

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        filepath: str  # type: ignore[no-redef]


class VRM_OT_import_vrma_via_file_handler(Operator):
    bl_idname = "vrm.import_vrma_via_file_handler"
    bl_label = "Import VRMA via FileHandler"

    filepath: StringProperty(  # type: ignore[valid-type]
        subtype="FILE_PATH",
        options={"SKIP_SAVE"},
    )

    @classmethod
    def poll(cls, _context: Context) -> bool:
        return True

    def execute(self, _context: Context) -> set[str]:
        return ops.import_scene.vrma(filepath=self.filepath)

    def invoke(self, context: Context, _event: Event) -> set[str]:
        return self.execute(context)

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        filepath: str  # type: ignore[no-redef]


if bpy.app.version >= (4, 1, 0):
    from bpy.types import FileHandler

    class VRM_FH_vrm_import(FileHandler):
        bl_idname = "VRM_FH_vrm_import"
        bl_label = "Import VRM"
        bl_import_operator = "vrm.import_vrm_via_file_handler"
        bl_export_operator = "export_scene.vrm"
        bl_file_extensions = ".vrm"

        @classmethod
        def poll_drop(cls, context: Context) -> bool:
            _ = context
            return True

    class VRM_FH_vrma_import(FileHandler):
        bl_idname = "VRM_FH_vrma_import"
        bl_label = "Import VRMA"
        bl_import_operator = "vrm.import_vrma_via_file_handler"
        bl_export_operator = "export_scene.vrma"
        bl_file_extensions = ".vrma"

        @classmethod
        def poll_drop(cls, context: Context) -> bool:
            _ = context
            return True
