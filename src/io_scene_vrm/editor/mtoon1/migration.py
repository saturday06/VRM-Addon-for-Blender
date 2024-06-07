import functools

from bpy.types import (
    Context,
    Material,
    NodeReroute,
    ShaderNodeGroup,
    ShaderNodeTexImage,
)
from idprop.types import IDPropertyGroup

from ...common import convert
from ...common.gl import GL_LINEAR, GL_NEAREST
from .property_group import (
    GL_LINEAR_IMAGE_INTERPOLATIONS,
    IMAGE_INTERPOLATION_CLOSEST,
    IMAGE_INTERPOLATION_LINEAR,
    Mtoon1SamplerPropertyGroup,
    reset_shader_node_group,
)


def migrate(context: Context) -> None:
    for material in context.blend_data.materials:
        if not material:
            continue
        if not material.use_nodes:
            continue
        node_tree = material.node_tree
        if not node_tree:
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
            surface_node = node_tree.nodes.get(surface_node_name)
            if not isinstance(surface_node, NodeReroute):
                continue

            connected = False
            surface_socket = surface_node.outputs[0]
            for link in node_tree.links:
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
            group_node = node_tree.nodes.get("Mtoon1Material.Mtoon1Output")
            if not isinstance(group_node, ShaderNodeGroup):
                continue
            if not group_node.node_tree:
                continue
            if group_node.node_tree.name != "VRM Add-on MToon 1.0 Output Revision 1":
                continue

        if addon_version < (2, 20, 50):
            migrate_sampler_filter_node(material)

        if addon_version < (2, 20, 53):
            reset_shader_node_group(
                context, material, reset_node_tree=True, overwrite=True
            )


def migrate_sampler_filter_node(material: Material) -> None:
    node_tree = material.node_tree
    if not node_tree:
        return

    vrm_addon_extension = material.get("vrm_addon_extension")
    if not isinstance(vrm_addon_extension, IDPropertyGroup):
        return

    mtoon1 = vrm_addon_extension.get("mtoon1")
    if not mtoon1:
        return

    for node_name, attrs in [
        (
            "Mtoon1BaseColorTexture.Image",
            ("pbr_metallic_roughness", "base_color_texture"),
        ),
        ("Mtoon1EmissiveTexture.Image", ("emissive_texture",)),
        ("Mtoon1NormalTexture.Image", ("normal_texture",)),
        (
            "Mtoon1ShadeMultiplyTexture.Image",
            ("extensions", "vrmc_materials_mtoon", "shade_multiply_texture"),
        ),
        (
            "Mtoon1ShadingShiftTexture.Image",
            ("extensions", "vrmc_materials_mtoon", "shading_shift_texture"),
        ),
        (
            "Mtoon1OutlineWidthMultiplyTexture.Image",
            (
                "extensions",
                "vrmc_materials_mtoon",
                "outline_width_multiply_texture",
            ),
        ),
        (
            "Mtoon1UvAnimationMaskTexture.Image",
            ("extensions", "vrmc_materials_mtoon", "uv_animation_mask_texture"),
        ),
        (
            "Mtoon1MatcapTexture.Image",
            ("extensions", "vrmc_materials_mtoon", "matcap_texture"),
        ),
        (
            "Mtoon1RimMultiplyTexture.Image",
            ("extensions", "vrmc_materials_mtoon", "rim_multiply_texture"),
        ),
    ]:
        sampler = functools.reduce(
            lambda prop, attr: getattr(prop, attr, None),
            (*attrs, "index", "sampler"),
            mtoon1,
        )
        if not isinstance(sampler, IDPropertyGroup):
            continue

        mag_filter = sampler.get("mag_filter")
        if (
            not isinstance(mag_filter, int)
            or mag_filter not in Mtoon1SamplerPropertyGroup.MAG_FILTER_NUMBER_TO_ID
        ):
            continue

        node = node_tree.nodes.get(node_name)
        if not isinstance(node, ShaderNodeTexImage):
            continue

        if (
            mag_filter == GL_NEAREST
            and node.interpolation != IMAGE_INTERPOLATION_CLOSEST
        ):
            node.interpolation = IMAGE_INTERPOLATION_CLOSEST
        if (
            mag_filter == GL_LINEAR
            and node.interpolation not in GL_LINEAR_IMAGE_INTERPOLATIONS
        ):
            node.interpolation = IMAGE_INTERPOLATION_LINEAR
