from bpy.types import Context, NodeReroute, ShaderNodeGroup
from idprop.types import IDPropertyGroup

from ...common import convert
from .property_group import reset_shader_node_group


def migrate(context: Context) -> None:
    for material in context.blend_data.materials:
        if not material:
            continue
        if not material.use_nodes:
            continue
        if not material.node_tree:
            continue

        vrm_addon_extension = material.get("vrm_addon_extension")
        if not isinstance(vrm_addon_extension, IDPropertyGroup):
            continue

        mtoon1 = vrm_addon_extension.get("mtoon1")
        if not isinstance(mtoon1, IDPropertyGroup):
            continue

        if not mtoon1.get("enabled"):
            continue

        extensions = mtoon1.get("extensions")
        if not isinstance(extensions, IDPropertyGroup):
            continue

        vrmc_materials_mtoon = extensions.get("vrmc_materials_mtoon")
        if not isinstance(vrmc_materials_mtoon, IDPropertyGroup):
            continue

        if vrmc_materials_mtoon.get("is_outline_material"):
            continue

        addon_version = convert.float3_or(mtoon1.get("addon_version"), (0, 0, 0))
        if addon_version < (2, 16, 4):
            # https://github.com/saturday06/VRM-Addon-for-Blender/blob/2_10_0/io_scene_vrm/editor/mtoon1/property_group.py#L1658-L1683
            surface_node_name = "Mtoon1Material.MaterialOutputSurfaceIn"
            surface_node = material.node_tree.nodes.get(surface_node_name)
            if not isinstance(surface_node, NodeReroute):
                continue

            connected = False
            surface_socket = surface_node.outputs[0]
            for link in material.node_tree.links:
                if (
                    link.from_socket == surface_socket
                    and link.to_socket
                    and link.to_socket.node
                    and link.to_socket.node.type == "OUTPUT_MATERIAL"
                ):
                    connected = True
                    break
            if not connected:
                continue
        else:
            # https://github.com/saturday06/VRM-Addon-for-Blender/blob/2_16_4/io_scene_vrm/editor/mtoon1/property_group.py#L1913-L1929
            group_node = material.node_tree.nodes.get("Mtoon1Material.Mtoon1Output")
            if not isinstance(group_node, ShaderNodeGroup):
                continue
            if not group_node.node_tree:
                continue
            if group_node.node_tree.name != "VRM Add-on MToon 1.0 Output Revision 1":
                continue

        if addon_version < (2, 20, 47):
            reset_shader_node_group(
                context, material, reset_node_tree=True, overwrite=True
            )
