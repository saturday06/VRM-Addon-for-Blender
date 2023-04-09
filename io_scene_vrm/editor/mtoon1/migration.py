import bpy

from ...common.shader import load_mtoon1_outline_geometry_node_group
from ...common.version import addon_version


def migrate(context: bpy.types.Context) -> None:
    outline_geometry_node_group_overwrite = True
    for material in context.blend_data.materials:
        if not material:
            continue

        root = material.vrm_addon_extension.mtoon1
        if not root.enabled:
            continue

        if tuple(root.addon_version) < (2, 15, 18):
            load_mtoon1_outline_geometry_node_group(
                context, overwrite=outline_geometry_node_group_overwrite
            )
            outline_geometry_node_group_overwrite = False
            bpy.ops.vrm.refresh_mtoon1_outline(material_name=material.name)

        root.addon_version = addon_version()
