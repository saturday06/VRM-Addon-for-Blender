# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import bpy

from .abstract_base_vrm_exporter import AbstractBaseVrmExporter


class glTF2ExportUserExtension:
    def __init__(self) -> None:
        context = bpy.context

        self.object_name_to_modifier_names = (
            AbstractBaseVrmExporter.enter_hide_mtoon1_outline_geometry_nodes(context)
        )

    # 3 arguments in Blender 2.93.0
    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/709630548cdc184af6ea50b2ff3ddc5450bc0af3/addons/io_scene_gltf2/blender/exp/gltf2_blender_export.py#L68
    # 5 arguments in Blender 3.6.0
    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/78c9556942e0780b471c9985e83e39e8c8d8f85a/addons/io_scene_gltf2/blender/exp/gltf2_blender_export.py#L84
    def gather_gltf_hook(
        self,
        # The number of arguments and specifications vary widely from version to version
        # of the glTF 2.0 add-on.
        _a: object,
        _b: object,
        _c: object,
        _d: object,
    ) -> None:
        context = bpy.context

        AbstractBaseVrmExporter.exit_hide_mtoon1_outline_geometry_nodes(
            context, self.object_name_to_modifier_names
        )
        self.object_name_to_modifier_names.clear()
