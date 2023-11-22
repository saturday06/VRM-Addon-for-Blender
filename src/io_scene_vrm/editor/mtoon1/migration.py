import bpy

from .property_group import reset_shader_node_group


def migrate(context: bpy.types.Context) -> None:
    for material in context.blend_data.materials:
        if not material:
            continue

        if not material.vrm_addon_extension.mtoon1.enabled:
            continue

        if tuple(material.vrm_addon_extension.mtoon1.addon_version) < (2, 20, 8):
            reset_shader_node_group(
                context, material, reset_node_tree=True, overwrite=True
            )
