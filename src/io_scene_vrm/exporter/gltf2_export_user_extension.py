# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import bpy
from io_scene_gltf2.io.com import gltf2_io

from .abstract_base_vrm_exporter import AbstractBaseVrmExporter


class glTF2ExportUserExtension:
    def __init__(self) -> None:
        context = bpy.context

        self.object_name_to_modifier_names = (
            AbstractBaseVrmExporter.enter_hide_mtoon1_outline_geometry_nodes(context)
        )

    def cleanup(self) -> None:
        context = bpy.context

        AbstractBaseVrmExporter.exit_hide_mtoon1_outline_geometry_nodes(
            context, self.object_name_to_modifier_names
        )
        self.object_name_to_modifier_names.clear()

    # https://projects.blender.org/blender/blender-addons/src/tag/v3.1.0/io_scene_gltf2/blender/exp/gltf2_blender_export.py#L83
    def gather_gltf_hook_3_1(
        self,
        _active_scene_index: int,
        _scenes: list[gltf2_io.Scene],
        _animations: list[gltf2_io.Animation],
        _export_settings: dict[str, object],
    ) -> None:
        self.cleanup()

    # https://projects.blender.org/blender/blender-addons/src/tag/v2.93.0/io_scene_gltf2/blender/exp/gltf2_blender_export.py#L68
    def gather_gltf_hook_2_93(
        self,
        _gltf: object,
        _export_settings: dict[str, object],
    ) -> None:
        self.cleanup()

    if bpy.app.version >= (3, 3):
        gather_gltf_hook = gather_gltf_hook_3_1
    else:
        gather_gltf_hook = gather_gltf_hook_2_93
