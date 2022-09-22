import math
from collections import abc
from os.path import dirname, join
from sys import float_info
from typing import Any, Dict, Optional, Tuple

import bgl
import bpy

from .logging import get_logger

logger = get_logger(__name__)

__file_names = [
    "mtoon0.blend",
    "transparent_z_write.blend",
    "gltf.blend",
]


def add_shaders() -> None:
    for file_name in __file_names:
        path = join(dirname(__file__), file_name)
        with bpy.data.libraries.load(path, link=False) as (data_from, data_to):
            for node_group in data_from.node_groups:
                if node_group not in bpy.data.node_groups:
                    data_to.node_groups.append(node_group)


def load_mtoon1_shader(material: bpy.types.Material) -> None:
    material_name = "MToon1MaterialTemplate452495794"
    path = join(dirname(__file__), "mtoon1.blend") + "/Material"

    append_result = bpy.ops.wm.append(
        filepath=join(path, material_name),
        filename=material_name,
        directory=path,
    )
    if append_result != {"FINISHED"}:
        raise RuntimeError(
            f"Failed to append MToon 1.0 template material: {append_result}"
        )

    template_material = bpy.data.materials.get(material_name)
    try:
        copy_node_tree(template_material.node_tree, material.node_tree)
    finally:
        if template_material:
            bpy.data.materials.remove(template_material)


def copy_socket(
    from_socket: bpy.types.NodeSocket, to_socket: bpy.types.NodeSocket
) -> None:
    to_socket.display_shape = from_socket.display_shape
    to_socket.enabled = from_socket.enabled
    to_socket.hide = from_socket.hide
    to_socket.hide_value = from_socket.hide_value
    to_socket.link_limit = from_socket.link_limit
    to_socket.name = from_socket.name
    to_socket.show_expanded = from_socket.show_expanded
    to_socket.type = from_socket.type


def copy_socket_default_value(
    from_socket: bpy.types.NodeSocket,
    to_socket: bpy.types.NodeSocket,
) -> None:
    if isinstance(
        from_socket,
        (
            bpy.types.NodeSocketBool,
            bpy.types.NodeSocketColor,
            bpy.types.NodeSocketFloat,
            bpy.types.NodeSocketFloatAngle,
            bpy.types.NodeSocketFloatFactor,
            bpy.types.NodeSocketFloatPercentage,
            bpy.types.NodeSocketFloatTime,
            bpy.types.NodeSocketFloatUnsigned,
            bpy.types.NodeSocketInt,
            bpy.types.NodeSocketIntFactor,
            bpy.types.NodeSocketIntPercentage,
            bpy.types.NodeSocketIntUnsigned,
            bpy.types.NodeSocketString,
            bpy.types.NodeSocketVector,
            bpy.types.NodeSocketVectorAcceleration,
            bpy.types.NodeSocketVectorDirection,
            bpy.types.NodeSocketVectorEuler,
            bpy.types.NodeSocketVectorTranslation,
            bpy.types.NodeSocketVectorVelocity,
            bpy.types.NodeSocketVectorXYZ,
            bpy.types.NodeSocketIntUnsigned,
        ),
    ):
        to_socket.default_value = from_socket.default_value


def copy_node_socket_default_value(
    from_node: bpy.types.Node,
    to_node: bpy.types.Node,
) -> None:
    for index, from_input in enumerate(from_node.inputs):
        to_input = to_node.inputs[index]
        copy_socket_default_value(from_input, to_input)
    for index, from_output in enumerate(from_node.outputs):
        to_output = to_node.outputs[index]
        copy_socket_default_value(from_output, to_output)


def copy_node(
    from_node: bpy.types.Node,
    to_node: bpy.types.Node,
    from_to: Dict[bpy.types.Node, bpy.types.Node],
) -> None:
    to_node.color = from_node.color
    to_node.height = from_node.height
    to_node.hide = from_node.hide
    for index, from_input in enumerate(from_node.inputs):
        to_input = to_node.inputs[index]
        copy_socket(from_input, to_input)
    to_node.label = from_node.label
    to_node.location = from_node.location
    to_node.mute = from_node.mute
    to_node.name = from_node.name
    for index, from_output in enumerate(from_node.outputs):
        to_output = to_node.outputs[index]
        copy_socket(from_output, to_output)
    if from_node.parent:
        to_node.parent = from_to.get(from_node.parent)
    to_node.select = from_node.select
    to_node.show_options = from_node.show_options
    to_node.show_preview = from_node.show_preview
    to_node.show_texture = from_node.show_texture
    to_node.use_custom_color = from_node.use_custom_color
    to_node.width = from_node.width
    to_node.width_hidden = from_node.width_hidden

    if isinstance(from_node, bpy.types.NodeFrame):
        to_node.shrink = from_node.shrink
        to_node.label_size = from_node.label_size
        to_node.text = from_node.text
    if isinstance(from_node, bpy.types.NodeGroup):
        # to_node.node_tree = from_node.node_tree
        logger.error("Importing NodeGroup doesn't be supported yet")
    if isinstance(from_node, bpy.types.NodeGroupOutput):
        to_node.is_active_output = from_node.is_active_output
    if isinstance(from_node, bpy.types.ShaderNodeWireframe):
        to_node.use_pixel_size = from_node.use_pixel_size
    if isinstance(from_node, bpy.types.ShaderNodeVertexColor):
        to_node.layer_name = from_node.layer_name
    if isinstance(from_node, bpy.types.ShaderNodeVectorTransform):
        to_node.convert_from = from_node.convert_from
        to_node.convert_to = from_node.convert_to
        to_node.vector_type = from_node.vector_type
        to_node.vector_type = from_node.vector_type
    if isinstance(from_node, bpy.types.ShaderNodeVectorRotate):
        to_node.invert = from_node.invert
        to_node.rotation_type = from_node.rotation_type
    if isinstance(from_node, bpy.types.ShaderNodeVectorMath):
        to_node.operation = from_node.operation
    if isinstance(from_node, bpy.types.ShaderNodeVectorDisplacement):
        to_node.space = from_node.space
    if isinstance(from_node, bpy.types.ShaderNodeUVMap):
        to_node.from_instancer = from_node.from_instancer
        to_node.uv_map = from_node.uv_map
    if isinstance(from_node, bpy.types.ShaderNodeUVAlongStroke):
        to_node.use_tips = from_node.use_tips
    if isinstance(from_node, bpy.types.ShaderNodeTexWhiteNoise):
        to_node.noise_dimensions = from_node.noise_dimensions
    if isinstance(from_node, bpy.types.ShaderNodeTexWave):
        to_node.bands_direction = from_node.bands_direction
        to_node.color_mapping = from_node.color_mapping
        to_node.rings_direction = from_node.rings_direction
        to_node.wave_profile = from_node.wave_profile
        to_node.wave_type = from_node.wave_type
    if isinstance(from_node, bpy.types.ShaderNodeTexVoronoi):
        to_node.distance = from_node.distance
        to_node.feature = from_node.feature
        to_node.voronoi_dimensions = from_node.voronoi_dimensions
    if isinstance(from_node, bpy.types.ShaderNodeTexSky):
        to_node.ground_albedo = from_node.ground_albedo
        to_node.sky_type = from_node.sky_type
        to_node.sun_direction = from_node.sun_direction
        to_node.turbidity = from_node.turbidity
    if isinstance(from_node, bpy.types.ShaderNodeTexPointDensity):
        to_node.interpolation = from_node.interpolation
        to_node.object = from_node.object
        to_node.particle_color_source = from_node.particle_color_source
        to_node.particle_system = from_node.particle_system
        to_node.point_source = from_node.point_source
        to_node.radius = from_node.radius
        to_node.resolution = from_node.resolution
        to_node.space = from_node.space
        to_node.vertex_attribute_name = from_node.vertex_attribute_name
        to_node.vertex_color_source = from_node.vertex_color_source
    if isinstance(from_node, bpy.types.ShaderNodeTexNoise):
        to_node.noise_dimensions = from_node.noise_dimensions
    if isinstance(from_node, bpy.types.ShaderNodeTexMusgrave):
        to_node.musgrave_dimensions = from_node.musgrave_dimensions
        to_node.musgrave_type = from_node.musgrave_type
    if isinstance(from_node, bpy.types.ShaderNodeTexMagic):
        to_node.turbulence_depth = from_node.turbulence_depth
    if isinstance(from_node, bpy.types.ShaderNodeTexImage):
        to_node.extension = from_node.extension
        # to_node.image = from_node.image
        to_node.interpolation = from_node.interpolation
        to_node.projection = from_node.projection
        to_node.projection_blend = from_node.projection_blend
    if isinstance(from_node, bpy.types.ShaderNodeTexIES):
        to_node.filepath = from_node.filepath
        to_node.ies = from_node.ies
        to_node.mode = from_node.mode
    if isinstance(from_node, bpy.types.ShaderNodeTexGradient):
        to_node.gradient_type = from_node.gradient_type
    if isinstance(from_node, bpy.types.ShaderNodeTexEnvironment):
        to_node.image = from_node.image
        to_node.interpolation = from_node.interpolation
        to_node.projection = from_node.projection
    if isinstance(from_node, bpy.types.ShaderNodeTexCoord):
        to_node.from_instancer = from_node.from_instancer
        to_node.object = from_node.object
    if isinstance(from_node, bpy.types.ShaderNodeTexBrick):
        to_node.offset = from_node.offset
        to_node.offset_frequency = from_node.offset_frequency
        to_node.squash = from_node.squash
        to_node.squash_frequency = from_node.squash_frequency
    if isinstance(from_node, bpy.types.ShaderNodeTangent):
        to_node.axis = from_node.axis
        to_node.direction_type = from_node.direction_type
        to_node.uv_map = from_node.uv_map
    if isinstance(from_node, bpy.types.ShaderNodeSubsurfaceScattering):
        to_node.falloff = from_node.falloff
    if isinstance(from_node, bpy.types.ShaderNodeScript):
        to_node.bytecode = from_node.bytecode
        to_node.bytecode_hash = from_node.bytecode_hash
        to_node.filepath = from_node.filepath
        to_node.mode = from_node.mode
        to_node.script = from_node.script
        to_node.use_auto_update = from_node.use_auto_update
    if isinstance(from_node, bpy.types.ShaderNodeOutputWorld):
        to_node.is_active_output = from_node.is_active_output
        to_node.target = from_node.target
    if isinstance(from_node, bpy.types.ShaderNodeOutputMaterial):
        to_node.is_active_output = from_node.is_active_output
        to_node.target = from_node.target
    if isinstance(from_node, bpy.types.ShaderNodeOutputLineStyle):
        to_node.blend_type = from_node.blend_type
        to_node.is_active_output = from_node.is_active_output
        to_node.target = from_node.target
        to_node.use_alpha = from_node.use_alpha
        to_node.use_clamp = from_node.use_clamp
    if isinstance(from_node, bpy.types.ShaderNodeOutputLight):
        to_node.is_active_output = from_node.is_active_output
        to_node.target = from_node.target
    if isinstance(from_node, bpy.types.ShaderNodeOutputAOV):
        to_node.name = from_node.name
    if isinstance(from_node, bpy.types.ShaderNodeNormalMap):
        to_node.space = from_node.space
        to_node.uv_map = from_node.uv_map
    if isinstance(from_node, bpy.types.ShaderNodeMixRGB):
        to_node.blend_type = from_node.blend_type
        to_node.use_alpha = from_node.use_alpha
        to_node.use_clamp = from_node.use_clamp
    if isinstance(from_node, bpy.types.ShaderNodeMath):
        to_node.operation = from_node.operation
        to_node.use_clamp = from_node.use_clamp
    if isinstance(from_node, bpy.types.ShaderNodeMapping):
        to_node.vector_type = from_node.vector_type
    if isinstance(from_node, bpy.types.ShaderNodeMapRange):
        to_node.clamp = from_node.clamp
        to_node.interpolation_type = from_node.interpolation_type
    if isinstance(from_node, bpy.types.ShaderNodeGroup):
        # to_node.node_tree = from_node.node_tree
        logger.error("Importing ShaderNodeGroup doesn't be supported yet")
    if isinstance(from_node, bpy.types.ShaderNodeDisplacement):
        to_node.space = from_node.space
    if isinstance(from_node, bpy.types.ShaderNodeCustomGroup):
        # to_node.node_tree = from_node.node_tree
        logger.error("Importing ShaderNodeCustomGroup doesn't be supported yet")
    if isinstance(from_node, bpy.types.ShaderNodeClamp):
        to_node.clamp_type = from_node.clamp_type
    if isinstance(from_node, bpy.types.ShaderNodeBump):
        to_node.invert = from_node.invert
    if isinstance(from_node, bpy.types.ShaderNodeBsdfToon):
        to_node.component = from_node.component
    if isinstance(from_node, bpy.types.ShaderNodeBsdfRefraction):
        to_node.distribution = from_node.distribution
    if isinstance(from_node, bpy.types.ShaderNodeBsdfPrincipled):
        to_node.distribution = from_node.distribution
        to_node.subsurface_method = from_node.subsurface_method
    if isinstance(from_node, bpy.types.ShaderNodeBsdfHairPrincipled):
        to_node.parametrization = from_node.parametrization
    if isinstance(from_node, bpy.types.ShaderNodeBsdfHair):
        to_node.component = from_node.component
    if isinstance(from_node, bpy.types.ShaderNodeBsdfGlossy):
        to_node.distribution = from_node.distribution
    if isinstance(from_node, bpy.types.ShaderNodeBsdfGlass):
        to_node.distribution = from_node.distribution
    if isinstance(from_node, bpy.types.ShaderNodeBsdfAnisotropic):
        to_node.distribution = from_node.distribution
    if isinstance(from_node, bpy.types.ShaderNodeBevel):
        to_node.samples = from_node.samples
    if isinstance(from_node, bpy.types.ShaderNodeAttribute):
        to_node.attribute_name = from_node.attribute_name
    if isinstance(from_node, bpy.types.ShaderNodeAmbientOcclusion):
        to_node.inside = from_node.inside
        to_node.only_local = from_node.only_local
        to_node.samples = from_node.samples


def copy_node_tree(
    from_node_tree: bpy.types.NodeTree, to_node_tree: bpy.types.NodeTree
) -> None:
    to_node_tree.links.clear()
    to_node_tree.nodes.clear()
    to_node_tree.inputs.clear()
    to_node_tree.outputs.clear()

    from_to: Dict[bpy.types.Node, bpy.types.Node] = {}

    for from_node in from_node_tree.nodes:
        to_node = to_node_tree.nodes.new(from_node.bl_idname)
        from_to[from_node] = to_node

    for from_node, to_node in from_to.items():
        copy_node(from_node, to_node, from_to)

    for from_link in from_node_tree.links:
        if not from_link.is_valid:
            continue

        input_socket_index = {
            0: i
            for i, s in enumerate(from_link.to_node.inputs)
            if s == from_link.to_socket
        }.get(0)
        if input_socket_index is None:
            continue
        input_node = from_to.get(from_link.to_node)
        if input_node is None:
            continue
        input_socket = input_node.inputs[input_socket_index]
        if not input_socket:
            logger.error(f"No input socket: {from_link.to_socket.name}")
            continue

        output_socket_index = {
            0: i
            for i, s in enumerate(from_link.from_node.outputs)
            if s == from_link.from_socket
        }.get(0)
        if output_socket_index is None:
            continue
        output_node = from_to.get(from_link.from_node)
        if output_node is None:
            continue
        output_socket = output_node.outputs[output_socket_index]
        if not output_socket:
            logger.error(f"No output socket: {from_link.from_socket.name}")
            continue

        to_node_tree.links.new(input_socket, output_socket)

    for from_node, to_node in from_to.items():
        copy_node_socket_default_value(from_node, to_node)

    # 親子関係の辻褄が合った状態でもう一度場所を設定することで完全にノードの位置を復元できる
    for from_node, to_node in from_to.items():
        to_node.location = from_node.location


def shader_node_group_import(shader_node_group_name: str) -> None:
    if shader_node_group_name in bpy.data.node_groups:
        return
    for file_name in __file_names:
        path = join(
            dirname(__file__),
            file_name,
            "NodeTree",
        )
        bpy.ops.wm.append(
            filepath=join(path, shader_node_group_name),
            filename=shader_node_group_name,
            directory=path,
        )


def get_image_name_and_sampler_type(
    shader_node: bpy.types.Node, input_socket_name: str
) -> Optional[Tuple[str, int, int]]:
    if (
        input_socket_name == "NormalmapTexture"
        and "NormalmapTexture" not in shader_node.inputs
        and "NomalmapTexture" in shader_node.inputs
    ):
        input_socket_name = "NomalmapTexture"

    socket = shader_node.inputs.get(input_socket_name)
    if not socket:
        return None

    links = socket.links
    if not links:
        return None

    from_node = links[0].from_node
    if not from_node:
        return None

    image = from_node.image
    if not image:
        return None

    image_name = image.name
    if not image_name:
        return None

    # blender is ('Linear', 'Closest', 'Cubic', 'Smart') glTF is Linear, Closest
    if from_node.interpolation == "Closest":
        filter_type = bgl.GL_NEAREST
    else:
        filter_type = bgl.GL_LINEAR

    # blender is ('REPEAT', 'EXTEND', 'CLIP') glTF is CLAMP_TO_EDGE,MIRRORED_REPEAT,REPEAT
    if from_node.extension == "REPEAT":
        wrap_type = bgl.GL_REPEAT
    else:
        wrap_type = bgl.GL_CLAMP_TO_EDGE

    return image_name, wrap_type, filter_type


def float_or_none(v: Any, min_value: float, max_value: float) -> Optional[float]:
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, (float, int)):
        return max(min_value, min(float(v), max_value))
    return None


def get_float_value(
    shader_node: bpy.types.Node,
    input_socket_name: str,
    min_value: float = -float_info.max,
    max_value: float = float_info.max,
) -> Optional[float]:
    socket = shader_node.inputs.get(input_socket_name)
    if not socket:
        return None

    default_value = float_or_none(socket.default_value, min_value, max_value)

    links = socket.links
    if not links:
        return default_value

    from_node = links[0].from_node
    if not from_node:
        return default_value

    outputs = from_node.outputs
    if not outputs:
        return default_value

    return float_or_none(outputs[0].default_value, min_value, max_value)


def rgba_or_none(
    vs: Any, min_value: float = -float_info.max, max_value: float = float_info.max
) -> Optional[Tuple[float, float, float, float]]:
    if not isinstance(vs, abc.Iterable):
        return None

    rgba = []
    for v in vs:
        f = float_or_none(v, min_value, max_value)
        if f is None:
            return None
        rgba.append(f)
        if len(rgba) > 4:
            return None

    if len(rgba) == 3:
        rgba.append(max(min_value, min(1.0, max_value)))
    if len(rgba) != 4:
        return None

    return (rgba[0], rgba[1], rgba[2], rgba[3])


def get_rgba_val(
    shader_node: bpy.types.Node,
    input_socket_name: str,
    min_value: float = -float_info.max,
    max_value: float = float_info.max,
) -> Optional[Tuple[float, float, float, float]]:
    socket = shader_node.inputs.get(input_socket_name)
    if not socket:
        return None

    default_value = rgba_or_none(socket.default_value, min_value, max_value)

    links = socket.links
    if not links:
        return default_value

    from_node = links[0].from_node
    if not from_node:
        return default_value

    outputs = from_node.outputs
    if not outputs:
        return default_value

    return rgba_or_none(outputs[0].default_value, min_value, max_value)


def rgb_or_none(
    vs: Any, min_value: float = -float_info.max, max_value: float = float_info.max
) -> Optional[Tuple[float, float, float]]:
    if not isinstance(vs, abc.Iterable):
        return None

    rgb = []
    for v in vs:
        f = float_or_none(v, min_value, max_value)
        if f is None:
            return None
        rgb.append(f)
        if len(rgb) > 4:
            return None

    if len(rgb) == 4:
        rgb.pop()
    if len(rgb) != 3:
        return None

    return (rgb[0], rgb[1], rgb[2])


def get_rgb_val(
    shader_node: bpy.types.Node,
    input_socket_name: str,
    min_value: float = -float_info.max,
    max_value: float = float_info.max,
) -> Optional[Tuple[float, float, float]]:
    socket = shader_node.inputs.get(input_socket_name)
    if not socket:
        return None

    default_value = rgb_or_none(socket.default_value, min_value, max_value)

    links = socket.links
    if not links:
        return default_value

    from_node = links[0].from_node
    if not from_node:
        return default_value

    outputs = from_node.outputs
    if not outputs:
        return default_value

    return rgb_or_none(outputs[0].default_value, min_value, max_value)
