# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from bpy.types import Context, FileHandler

from .import_scene import (
    VRM_OT_import_vrm_via_file_handler,
    VRM_OT_import_vrma_via_file_handler,
)


class VRM_FH_vrm_import(FileHandler):
    bl_idname = "VRM_FH_vrm_import"
    bl_label = "Import VRM"
    bl_import_operator = VRM_OT_import_vrm_via_file_handler.bl_idname
    bl_export_operator = "export_scene.vrm"
    bl_file_extensions = ".vrm"

    @classmethod
    def poll_drop(cls, context: Context) -> bool:
        _ = context
        return True


class VRM_FH_vrma_import(FileHandler):
    bl_idname = "VRM_FH_vrma_import"
    bl_label = "Import VRMA"
    bl_import_operator = VRM_OT_import_vrma_via_file_handler.bl_idname
    bl_export_operator = "export_scene.vrma"
    bl_file_extensions = ".vrma"

    @classmethod
    def poll_drop(cls, context: Context) -> bool:
        _ = context
        return True
