import bpy

from ...common.shader import load_mtoon1_outline_geometry_node_group
from ...common.version import addon_version


def migrate(context: bpy.types.Context) -> None:
    outline_geometry_node_group_overwrite = True
    for material in context.blend_data.materials:
        if not material:
            continue

        if not material.vrm_addon_extension.mtoon1.enabled:
            continue

        if tuple(material.vrm_addon_extension.mtoon1.addon_version) < (2, 19, 0):
            load_mtoon1_outline_geometry_node_group(
                context, overwrite=outline_geometry_node_group_overwrite
            )
            outline_geometry_node_group_overwrite = False
            bpy.ops.vrm.refresh_mtoon1_outline(material_name=material.name)

        material.vrm_addon_extension.mtoon1.addon_version = addon_version()
