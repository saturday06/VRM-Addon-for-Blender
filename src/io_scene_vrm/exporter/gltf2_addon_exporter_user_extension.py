# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import bpy

from .abstract_base_vrm_exporter import AbstractBaseVrmExporter


class Gltf2AddonExporterUserExtension:
    def __init__(self) -> None:
        context = bpy.context

        self.object_name_to_modifier_names = (
            AbstractBaseVrmExporter.enter_hide_mtoon1_outline_geometry_nodes(context)
        )

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
