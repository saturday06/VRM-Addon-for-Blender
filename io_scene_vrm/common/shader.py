import math
from copy import deepcopy
from pathlib import Path
from sys import float_info
from typing import Optional

import bpy
from mathutils import Color

from . import convert
from .char import INTERNAL_NAME_PREFIX
from .gl import GL_CLAMP_TO_EDGE, GL_LINEAR, GL_NEAREST, GL_REPEAT
from .logging import get_logger

logger = get_logger(__name__)

BOOL_SOCKET_CLASSES = (bpy.types.NodeSocketBool,)
FLOAT_SOCKET_CLASSES = (
    bpy.types.NodeSocketFloat,
    bpy.types.NodeSocketFloatAngle,
    bpy.types.NodeSocketFloatFactor,
    bpy.types.NodeSocketFloatPercentage,
    bpy.types.NodeSocketFloatTime,
    bpy.types.NodeSocketFloatUnsigned,
)
INT_SOCKET_CLASSES = (
    bpy.types.NodeSocketInt,
    bpy.types.NodeSocketIntFactor,
    bpy.types.NodeSocketIntPercentage,
    bpy.types.NodeSocketIntUnsigned,
)
SCALAR_SOCKET_CLASSES = (
    *BOOL_SOCKET_CLASSES,
    *FLOAT_SOCKET_CLASSES,
    *INT_SOCKET_CLASSES,
)
VECTOR_SOCKET_CLASSES = (
    bpy.types.NodeSocketVector,
    bpy.types.NodeSocketVectorAcceleration,
    bpy.types.NodeSocketVectorDirection,
    bpy.types.NodeSocketVectorEuler,
    bpy.types.NodeSocketVectorTranslation,
    bpy.types.NodeSocketVectorVelocity,
    bpy.types.NodeSocketVectorXYZ,
)
COLOR_SOCKET_CLASSES = (bpy.types.NodeSocketColor,)
STRING_SOCKET_CLASSES = (bpy.types.NodeSocketString,)

file_names = [
    "mtoon0.blend",
]

OUTLINE_GEOMETRY_GROUP_NAME = "VRM Add-on MToon 1.0 Outline Geometry Revision 1"

UV_GROUP_NAME = "VRM Add-on MToon 1.0 UV Revision 1"
UV_ANIMATION_GROUP_NAME = "VRM Add-on MToon 1.0 UV Animation Revision 1"
NORMAL_GROUP_NAME = "VRM Add-on MToon 1.0 Normal Revision 1"
OUTPUT_GROUP_NAME = "VRM Add-on MToon 1.0 Output Revision 1"

shader_node_group_names = [
    UV_GROUP_NAME,
    UV_ANIMATION_GROUP_NAME,
    NORMAL_GROUP_NAME,
    OUTPUT_GROUP_NAME,
]


def template_name(name: str) -> str:
    return INTERNAL_NAME_PREFIX + name + " Template"


def add_shaders() -> None:
    for file_name in file_names:
        path = Path(__file__).with_name(file_name)
        with bpy.data.libraries.load(str(path), link=False) as (data_from, data_to):
            for node_group in data_from.node_groups:
                if node_group not in bpy.data.node_groups:
                    data_to.node_groups.append(node_group)


def load_mtoon1_outline_geometry_node_group(
    context: bpy.types.Context, overwrite: bool
) -> None:
    if bpy.app.version < (3, 3):
        return
    if not overwrite and OUTLINE_GEOMETRY_GROUP_NAME in bpy.data.node_groups:
        return

    old_template_outline_group = bpy.data.node_groups.get(
        template_name(OUTLINE_GEOMETRY_GROUP_NAME)
    )
    if old_template_outline_group:
        logger.error(
            f'Node Group "{template_name(OUTLINE_GEOMETRY_GROUP_NAME)}" already exists'
        )
        old_template_outline_group.name += ".old"

    outline_node_tree_path = (
        str(Path(__file__).with_name("mtoon1_outline.blend")) + "/NodeTree"
    )

    template_outline_group = None
    # https://projects.blender.org/blender/blender/src/tag/v2.93.18/source/blender/windowmanager/intern/wm_files_link.c#L85-L90
    if context.object is not None and context.object.mode == "EDIT":
        bpy.ops.object.mode_set(mode="OBJECT")
        edit_mode = True
    else:
        edit_mode = False
    try:
        outline_node_tree_append_result = bpy.ops.wm.append(
            filepath=(
                outline_node_tree_path
                + "/"
                + template_name(OUTLINE_GEOMETRY_GROUP_NAME)
            ),
            filename=template_name(OUTLINE_GEOMETRY_GROUP_NAME),
            directory=outline_node_tree_path,
        )

        if edit_mode:
            bpy.ops.object.mode_set(mode="EDIT")
            edit_mode = False

        if outline_node_tree_append_result != {"FINISHED"}:
            raise RuntimeError(
                "Failed to append MToon 1.0 outline template material: "
                + f"{outline_node_tree_append_result}"
            )
        template_outline_group = bpy.data.node_groups.get(
            template_name(OUTLINE_GEOMETRY_GROUP_NAME)
        )
        if not template_outline_group:
            raise ValueError("No " + template_name(OUTLINE_GEOMETRY_GROUP_NAME))

        outline_group = bpy.data.node_groups.get(OUTLINE_GEOMETRY_GROUP_NAME)
        if not outline_group:
            outline_group = bpy.data.node_groups.new(
                OUTLINE_GEOMETRY_GROUP_NAME, "GeometryNodeTree"
            )
            clear_node_tree(outline_group, clear_inputs_outputs=True)
            copy_node_tree(template_outline_group, outline_group)
        elif overwrite:
            copy_node_tree(template_outline_group, outline_group)
    finally:
        if template_outline_group and template_outline_group.users <= 1:
            bpy.data.node_groups.remove(template_outline_group)
        if edit_mode:
            bpy.ops.object.mode_set(mode="EDIT")


def load_mtoon1_shader(
    context: bpy.types.Context,
    material: bpy.types.Material,
    overwrite: bool,
) -> None:
    if not material.use_nodes:
        material.use_nodes = True

    load_mtoon1_outline_geometry_node_group(context, overwrite)

    material_name = INTERNAL_NAME_PREFIX + "VRM Add-on MToon 1.0 Template"
    old_material = bpy.data.materials.get(material_name)
    if old_material:
        logger.error(f'Material "{material_name}" already exists')
        old_material.name += ".old"

    for shader_node_group_name in shader_node_group_names:
        name = template_name(shader_node_group_name)
        old_template_group = bpy.data.node_groups.get(name)
        if old_template_group:
            logger.error(f'Node Group "{name}" already exists')
            old_template_group.name += ".old"

    material_path = str(Path(__file__).with_name("mtoon1.blend")) + "/Material"

    template_material = None

    # https://git.blender.org/gitweb/gitweb.cgi/blender.git/blob/v2.83:/source/blender/windowmanager/intern/wm_files_link.c#l84
    if context.object is not None and context.object.mode == "EDIT":
        bpy.ops.object.mode_set(mode="OBJECT")
        edit_mode = True
    else:
        edit_mode = False
    try:
        material_append_result = bpy.ops.wm.append(
            filepath=material_path + "/" + material_name,
            filename=material_name,
            directory=material_path,
        )

        if edit_mode:
            bpy.ops.object.mode_set(mode="EDIT")
            edit_mode = False

        if material_append_result != {"FINISHED"}:
            raise RuntimeError(
                "Failed to append MToon 1.0 template material: "
                + f"{material_append_result}"
            )

        template_material = bpy.data.materials.get(material_name)
        if not template_material:
            raise ValueError("No " + material_name)

        for shader_node_group_name in shader_node_group_names:
            shader_node_group_template_name = template_name(shader_node_group_name)
            template_group = bpy.data.node_groups.get(shader_node_group_template_name)
            if not template_group:
                raise ValueError("No " + shader_node_group_template_name)

            group = bpy.data.node_groups.get(shader_node_group_name)
            if not group:
                group = bpy.data.node_groups.new(
                    shader_node_group_name, "ShaderNodeTree"
                )
                clear_node_tree(group, clear_inputs_outputs=True)
                copy_node_tree(template_group, group)
            elif overwrite:
                copy_node_tree(template_group, group)

        template_material_node_tree = template_material.node_tree
        material_node_tree = material.node_tree
        if template_material_node_tree is None:
            logger.error("MToon template material node tree is None")
        elif material_node_tree is None:
            logger.error("MToon copy target material node tree is None")
        else:
            copy_node_tree(template_material_node_tree, material_node_tree)
    finally:
        if template_material and template_material.users <= 1:
            bpy.data.materials.remove(template_material)

        # reload and remove template groups
        for shader_node_group_name in shader_node_group_names:
            shader_node_group_template_name = template_name(shader_node_group_name)
            template_group = bpy.data.node_groups.get(shader_node_group_template_name)
            if template_group and template_group.users <= 1:
                bpy.data.node_groups.remove(template_group)

        if edit_mode:
            bpy.ops.object.mode_set(mode="EDIT")


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
    if to_socket.type != from_socket.type:
        to_socket.type = from_socket.type


def copy_socket_interface(
    from_socket: "bpy.types.NodeSocketInterface",
    to_socket: "bpy.types.NodeSocketInterface",
) -> None:
    if bpy.app.version >= (3, 0, 0):
        to_socket.attribute_domain = from_socket.attribute_domain
        to_socket.bl_label = from_socket.bl_label
    to_socket.description = from_socket.description
    to_socket.name = from_socket.name

    float_classes = (
        bpy.types.NodeSocketInterfaceFloat,
        bpy.types.NodeSocketInterfaceFloatAngle,
        bpy.types.NodeSocketInterfaceFloatDistance,
        bpy.types.NodeSocketInterfaceFloatFactor,
        bpy.types.NodeSocketInterfaceFloatPercentage,
        bpy.types.NodeSocketInterfaceFloatTime,
        bpy.types.NodeSocketInterfaceFloatUnsigned,
    )
    color_classes = (bpy.types.NodeSocketInterfaceColor,)
    vector_classes = (
        bpy.types.NodeSocketInterfaceVector,
        bpy.types.NodeSocketInterfaceVectorAcceleration,
        bpy.types.NodeSocketInterfaceVectorDirection,
        bpy.types.NodeSocketInterfaceVectorEuler,
        bpy.types.NodeSocketInterfaceVectorTranslation,
        bpy.types.NodeSocketInterfaceVectorVelocity,
        bpy.types.NodeSocketInterfaceVectorXYZ,
    )

    if isinstance(from_socket, float_classes) and isinstance(to_socket, float_classes):
        to_socket.default_value = from_socket.default_value
        to_socket.min_value = from_socket.min_value
        to_socket.max_value = from_socket.max_value
    elif isinstance(from_socket, color_classes) and isinstance(
        to_socket, color_classes
    ):
        to_socket.default_value = deepcopy(
            (
                from_socket.default_value[0],
                from_socket.default_value[1],
                from_socket.default_value[2],
                from_socket.default_value[3],
            )
        )
    elif isinstance(from_socket, vector_classes) and isinstance(
        to_socket, vector_classes
    ):
        to_socket.default_value = deepcopy(
            (
                from_socket.default_value[0],
                from_socket.default_value[1],
                from_socket.default_value[2],
            )
        )
        to_socket.min_value = from_socket.min_value
        to_socket.max_value = from_socket.max_value


def copy_socket_default_value(
    from_socket: bpy.types.NodeSocket,
    to_socket: bpy.types.NodeSocket,
) -> None:
    if isinstance(from_socket, SCALAR_SOCKET_CLASSES):
        if isinstance(to_socket, BOOL_SOCKET_CLASSES):
            to_socket.default_value = bool(from_socket.default_value)
        elif isinstance(to_socket, FLOAT_SOCKET_CLASSES):
            to_socket.default_value = float(from_socket.default_value)
        elif isinstance(to_socket, INT_SOCKET_CLASSES):
            to_socket.default_value = int(from_socket.default_value)
    elif isinstance(from_socket, VECTOR_SOCKET_CLASSES) and isinstance(
        to_socket, VECTOR_SOCKET_CLASSES
    ):
        to_socket.default_value = deepcopy(
            (
                from_socket.default_value[0],
                from_socket.default_value[1],
                from_socket.default_value[2],
            )
        )
    elif isinstance(from_socket, COLOR_SOCKET_CLASSES) and isinstance(
        to_socket, COLOR_SOCKET_CLASSES
    ):
        to_socket.default_value = deepcopy(
            (
                from_socket.default_value[0],
                from_socket.default_value[1],
                from_socket.default_value[2],
                from_socket.default_value[3],
            )
        )
    elif isinstance(from_socket, STRING_SOCKET_CLASSES) and isinstance(
        to_socket, STRING_SOCKET_CLASSES
    ):
        to_socket.default_value = deepcopy(from_socket.default_value)


def copy_node_socket_default_value(
    from_node: bpy.types.Node,
    to_node: bpy.types.Node,
) -> None:
    for index, from_input in enumerate(from_node.inputs):
        if 0 <= index < len(to_node.inputs):
            to_input = to_node.inputs[index]
            copy_socket_default_value(from_input, to_input)
    for index, from_output in enumerate(from_node.outputs):
        if 0 <= index < len(to_node.outputs):
            to_output = to_node.outputs[index]
            copy_socket_default_value(from_output, to_output)


def copy_shader_node_group(
    from_node: bpy.types.ShaderNodeGroup,
    to_node: bpy.types.ShaderNodeGroup,
) -> None:
    for shader_node_group_name in shader_node_group_names:
        shader_node_group_template_name = template_name(shader_node_group_name)
        if not from_node.node_tree.name.startswith(shader_node_group_template_name):
            continue

        group = bpy.data.node_groups.get(shader_node_group_name)
        if not group:
            logger.error(f'"{shader_node_group_name}" Not Found')
            continue

        to_node.node_tree = group
        return

    logger.error(
        "Importing ShaderNodeGroup doesn't be supported yet: "
        + f"{from_node.node_tree.name}"
    )


def copy_node(
    from_node: bpy.types.Node,
    to_node: bpy.types.Node,
    from_to: dict[bpy.types.Node, bpy.types.Node],
) -> None:
    to_node.color = deepcopy(
        (
            from_node.color[0],
            from_node.color[1],
            from_node.color[2],
        )
    )
    to_node.height = from_node.height
    to_node.hide = from_node.hide
    for index, from_input in enumerate(from_node.inputs):
        if 0 <= index < len(to_node.inputs):
            to_input = to_node.inputs[index]
            copy_socket(from_input, to_input)
    to_node.label = from_node.label
    to_node.location = deepcopy(
        (
            from_node.location[0],
            from_node.location[1],
        )
    )
    to_node.mute = from_node.mute
    to_node.name = from_node.name
    for index, from_output in enumerate(from_node.outputs):
        if 0 <= index < len(to_node.outputs):
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

    if isinstance(from_node, bpy.types.NodeFrame) and isinstance(
        to_node, bpy.types.NodeFrame
    ):
        to_node.shrink = from_node.shrink
        to_node.label_size = from_node.label_size
        to_node.text = from_node.text
    if isinstance(from_node, bpy.types.NodeGroup):
        logger.error("Importing NodeGroup doesn't be supported yet")
    if isinstance(from_node, bpy.types.NodeGroupOutput) and isinstance(
        to_node, bpy.types.NodeGroupOutput
    ):
        to_node.is_active_output = from_node.is_active_output
    if isinstance(from_node, bpy.types.ShaderNodeWireframe) and isinstance(
        to_node, bpy.types.ShaderNodeWireframe
    ):
        to_node.use_pixel_size = from_node.use_pixel_size
    if isinstance(from_node, bpy.types.ShaderNodeVertexColor) and isinstance(
        to_node, bpy.types.ShaderNodeVertexColor
    ):
        to_node.layer_name = from_node.layer_name
    if isinstance(from_node, bpy.types.ShaderNodeVectorTransform) and isinstance(
        to_node, bpy.types.ShaderNodeVectorTransform
    ):
        to_node.convert_from = from_node.convert_from
        to_node.convert_to = from_node.convert_to
        to_node.vector_type = from_node.vector_type
    if isinstance(from_node, bpy.types.ShaderNodeVectorRotate) and isinstance(
        to_node, bpy.types.ShaderNodeVectorRotate
    ):
        to_node.invert = from_node.invert
        to_node.rotation_type = from_node.rotation_type
    if isinstance(from_node, bpy.types.ShaderNodeVectorMath) and isinstance(
        to_node, bpy.types.ShaderNodeVectorMath
    ):
        to_node.operation = from_node.operation
    if isinstance(from_node, bpy.types.ShaderNodeVectorDisplacement) and isinstance(
        to_node, bpy.types.ShaderNodeVectorDisplacement
    ):
        to_node.space = from_node.space
    if isinstance(from_node, bpy.types.ShaderNodeUVMap) and isinstance(
        to_node, bpy.types.ShaderNodeUVMap
    ):
        to_node.from_instancer = from_node.from_instancer
        to_node.uv_map = from_node.uv_map
    if isinstance(from_node, bpy.types.ShaderNodeUVAlongStroke) and isinstance(
        to_node, bpy.types.ShaderNodeUVAlongStroke
    ):
        to_node.use_tips = from_node.use_tips
    if isinstance(from_node, bpy.types.ShaderNodeTexWhiteNoise) and isinstance(
        to_node, bpy.types.ShaderNodeTexWhiteNoise
    ):
        to_node.noise_dimensions = from_node.noise_dimensions
    if isinstance(from_node, bpy.types.ShaderNodeTexWave) and isinstance(
        to_node, bpy.types.ShaderNodeTexWave
    ):
        # incomplete
        to_node.bands_direction = from_node.bands_direction
        to_node.color_mapping.blend_color = deepcopy(
            (
                from_node.color_mapping.blend_color[0],
                from_node.color_mapping.blend_color[1],
                from_node.color_mapping.blend_color[2],
            )
        )
        to_node.color_mapping.blend_type = from_node.color_mapping.blend_type
        to_node.color_mapping.brightness = from_node.color_mapping.brightness
        to_node.color_mapping.color_ramp.color_mode = (
            from_node.color_mapping.color_ramp.color_mode
        )
        to_node.color_mapping.contrast = from_node.color_mapping.contrast
        to_node.color_mapping.saturation = from_node.color_mapping.saturation
        to_node.color_mapping.use_color_ramp = from_node.color_mapping.use_color_ramp
        to_node.rings_direction = from_node.rings_direction
        to_node.wave_profile = from_node.wave_profile
        to_node.wave_type = from_node.wave_type
    if isinstance(from_node, bpy.types.ShaderNodeTexVoronoi) and isinstance(
        to_node, bpy.types.ShaderNodeTexVoronoi
    ):
        to_node.distance = from_node.distance
        to_node.feature = from_node.feature
        to_node.voronoi_dimensions = from_node.voronoi_dimensions
    if isinstance(from_node, bpy.types.ShaderNodeTexSky) and isinstance(
        to_node, bpy.types.ShaderNodeTexSky
    ):
        to_node.ground_albedo = from_node.ground_albedo
        to_node.sky_type = from_node.sky_type
        to_node.sun_direction = from_node.sun_direction[:]
        to_node.turbidity = from_node.turbidity
    if isinstance(from_node, bpy.types.ShaderNodeTexPointDensity) and isinstance(
        to_node, bpy.types.ShaderNodeTexPointDensity
    ):
        to_node.interpolation = from_node.interpolation
        to_node.object = from_node.object
        to_node.particle_color_source = from_node.particle_color_source
        to_node.point_source = from_node.point_source
        to_node.radius = from_node.radius
        to_node.resolution = from_node.resolution
        to_node.space = from_node.space
        to_node.vertex_attribute_name = from_node.vertex_attribute_name
        to_node.vertex_color_source = from_node.vertex_color_source
    if isinstance(from_node, bpy.types.ShaderNodeTexNoise) and isinstance(
        to_node, bpy.types.ShaderNodeTexNoise
    ):
        to_node.noise_dimensions = from_node.noise_dimensions
    if isinstance(from_node, bpy.types.ShaderNodeTexMusgrave) and isinstance(
        to_node, bpy.types.ShaderNodeTexMusgrave
    ):
        to_node.musgrave_dimensions = from_node.musgrave_dimensions
        to_node.musgrave_type = from_node.musgrave_type
    if isinstance(from_node, bpy.types.ShaderNodeTexMagic) and isinstance(
        to_node, bpy.types.ShaderNodeTexMagic
    ):
        to_node.turbulence_depth = from_node.turbulence_depth
    if isinstance(from_node, bpy.types.ShaderNodeTexImage) and isinstance(
        to_node, bpy.types.ShaderNodeTexImage
    ):
        to_node.extension = from_node.extension
        # to_node.image = from_node.image
        to_node.interpolation = from_node.interpolation
        to_node.projection = from_node.projection
        to_node.projection_blend = from_node.projection_blend
    if isinstance(from_node, bpy.types.ShaderNodeTexIES) and isinstance(
        to_node, bpy.types.ShaderNodeTexIES
    ):
        to_node.filepath = from_node.filepath
        to_node.ies = from_node.ies
        to_node.mode = from_node.mode
    if isinstance(from_node, bpy.types.ShaderNodeTexGradient) and isinstance(
        to_node, bpy.types.ShaderNodeTexGradient
    ):
        to_node.gradient_type = from_node.gradient_type
    if isinstance(from_node, bpy.types.ShaderNodeTexEnvironment) and isinstance(
        to_node, bpy.types.ShaderNodeTexEnvironment
    ):
        to_node.image = from_node.image
        to_node.interpolation = from_node.interpolation
        to_node.projection = from_node.projection
    if isinstance(from_node, bpy.types.ShaderNodeTexCoord) and isinstance(
        to_node, bpy.types.ShaderNodeTexCoord
    ):
        to_node.from_instancer = from_node.from_instancer
        to_node.object = from_node.object
    if isinstance(from_node, bpy.types.ShaderNodeTexBrick) and isinstance(
        to_node, bpy.types.ShaderNodeTexBrick
    ):
        to_node.offset = from_node.offset
        to_node.offset_frequency = from_node.offset_frequency
        to_node.squash = from_node.squash
        to_node.squash_frequency = from_node.squash_frequency
    if isinstance(from_node, bpy.types.ShaderNodeTangent) and isinstance(
        to_node, bpy.types.ShaderNodeTangent
    ):
        to_node.axis = from_node.axis
        to_node.direction_type = from_node.direction_type
        to_node.uv_map = from_node.uv_map
    if isinstance(from_node, bpy.types.ShaderNodeSubsurfaceScattering) and isinstance(
        to_node, bpy.types.ShaderNodeSubsurfaceScattering
    ):
        to_node.falloff = from_node.falloff
    if isinstance(from_node, bpy.types.ShaderNodeScript) and isinstance(
        to_node, bpy.types.ShaderNodeScript
    ):
        to_node.bytecode = from_node.bytecode
        to_node.bytecode_hash = from_node.bytecode_hash
        to_node.filepath = from_node.filepath
        to_node.mode = from_node.mode
        to_node.script = from_node.script
        to_node.use_auto_update = from_node.use_auto_update
    if isinstance(from_node, bpy.types.ShaderNodeOutputWorld) and isinstance(
        to_node, bpy.types.ShaderNodeOutputWorld
    ):
        to_node.is_active_output = from_node.is_active_output
        to_node.target = from_node.target
    if isinstance(from_node, bpy.types.ShaderNodeOutputMaterial) and isinstance(
        to_node, bpy.types.ShaderNodeOutputMaterial
    ):
        to_node.is_active_output = from_node.is_active_output
        to_node.target = from_node.target
    if isinstance(from_node, bpy.types.ShaderNodeOutputLineStyle) and isinstance(
        to_node, bpy.types.ShaderNodeOutputLineStyle
    ):
        to_node.blend_type = from_node.blend_type
        to_node.is_active_output = from_node.is_active_output
        to_node.target = from_node.target
        to_node.use_alpha = from_node.use_alpha
        to_node.use_clamp = from_node.use_clamp
    if isinstance(from_node, bpy.types.ShaderNodeOutputLight) and isinstance(
        to_node, bpy.types.ShaderNodeOutputLight
    ):
        to_node.is_active_output = from_node.is_active_output
        to_node.target = from_node.target
    if isinstance(from_node, bpy.types.ShaderNodeOutputAOV) and isinstance(
        to_node, bpy.types.ShaderNodeOutputAOV
    ):
        to_node.name = from_node.name
    if isinstance(from_node, bpy.types.ShaderNodeNormalMap) and isinstance(
        to_node, bpy.types.ShaderNodeNormalMap
    ):
        to_node.space = from_node.space
        to_node.uv_map = from_node.uv_map
    if isinstance(from_node, bpy.types.ShaderNodeMixRGB) and isinstance(
        to_node, bpy.types.ShaderNodeMixRGB
    ):
        to_node.blend_type = from_node.blend_type
        to_node.use_alpha = from_node.use_alpha
        to_node.use_clamp = from_node.use_clamp
    if isinstance(from_node, bpy.types.ShaderNodeMath) and isinstance(
        to_node, bpy.types.ShaderNodeMath
    ):
        to_node.operation = from_node.operation
        to_node.use_clamp = from_node.use_clamp
    if isinstance(from_node, bpy.types.ShaderNodeMapping) and isinstance(
        to_node, bpy.types.ShaderNodeMapping
    ):
        to_node.vector_type = from_node.vector_type
    if isinstance(from_node, bpy.types.ShaderNodeMapRange) and isinstance(
        to_node, bpy.types.ShaderNodeMapRange
    ):
        to_node.clamp = from_node.clamp
        to_node.interpolation_type = from_node.interpolation_type
    if isinstance(from_node, bpy.types.ShaderNodeGroup) and isinstance(
        to_node, bpy.types.ShaderNodeGroup
    ):
        copy_shader_node_group(from_node, to_node)
    if isinstance(from_node, bpy.types.ShaderNodeDisplacement) and isinstance(
        to_node, bpy.types.ShaderNodeDisplacement
    ):
        to_node.space = from_node.space
    if isinstance(from_node, bpy.types.ShaderNodeCustomGroup) and isinstance(
        to_node, bpy.types.ShaderNodeCustomGroup
    ):
        # to_node.node_tree = from_node.node_tree
        logger.error("Importing ShaderNodeCustomGroup doesn't be supported yet")
    if isinstance(from_node, bpy.types.ShaderNodeClamp) and isinstance(
        to_node, bpy.types.ShaderNodeClamp
    ):
        to_node.clamp_type = from_node.clamp_type
    if isinstance(from_node, bpy.types.ShaderNodeBump) and isinstance(
        to_node, bpy.types.ShaderNodeBump
    ):
        to_node.invert = from_node.invert
    if isinstance(from_node, bpy.types.ShaderNodeBsdfToon) and isinstance(
        to_node, bpy.types.ShaderNodeBsdfToon
    ):
        to_node.component = from_node.component
    if isinstance(from_node, bpy.types.ShaderNodeBsdfRefraction) and isinstance(
        to_node, bpy.types.ShaderNodeBsdfRefraction
    ):
        to_node.distribution = from_node.distribution
    if isinstance(from_node, bpy.types.ShaderNodeBsdfPrincipled) and isinstance(
        to_node, bpy.types.ShaderNodeBsdfPrincipled
    ):
        to_node.distribution = from_node.distribution
        to_node.subsurface_method = from_node.subsurface_method
    if isinstance(from_node, bpy.types.ShaderNodeBsdfHairPrincipled) and isinstance(
        to_node, bpy.types.ShaderNodeBsdfHairPrincipled
    ):
        to_node.parametrization = from_node.parametrization
    if isinstance(from_node, bpy.types.ShaderNodeBsdfHair) and isinstance(
        to_node, bpy.types.ShaderNodeBsdfHair
    ):
        to_node.component = from_node.component
    if isinstance(from_node, bpy.types.ShaderNodeBsdfGlass) and isinstance(
        to_node, bpy.types.ShaderNodeBsdfGlass
    ):
        to_node.distribution = from_node.distribution
    if isinstance(from_node, bpy.types.ShaderNodeBsdfAnisotropic) and isinstance(
        to_node, bpy.types.ShaderNodeBsdfAnisotropic
    ):
        to_node.distribution = from_node.distribution
    if isinstance(from_node, bpy.types.ShaderNodeBevel) and isinstance(
        to_node, bpy.types.ShaderNodeBevel
    ):
        to_node.samples = from_node.samples
    if isinstance(from_node, bpy.types.ShaderNodeAttribute) and isinstance(
        to_node, bpy.types.ShaderNodeAttribute
    ):
        to_node.attribute_name = from_node.attribute_name
    if isinstance(from_node, bpy.types.ShaderNodeAmbientOcclusion) and isinstance(
        to_node, bpy.types.ShaderNodeAmbientOcclusion
    ):
        to_node.inside = from_node.inside
        to_node.only_local = from_node.only_local
        to_node.samples = from_node.samples

    if bpy.app.version >= (3, 3):
        if isinstance(from_node, bpy.types.ShaderNodeCombineColor) and isinstance(
            to_node, bpy.types.ShaderNodeCombineColor
        ):
            to_node.mode = from_node.mode
        if isinstance(from_node, bpy.types.ShaderNodeSeparateColor) and isinstance(
            to_node, bpy.types.ShaderNodeSeparateColor
        ):
            to_node.mode = from_node.mode

        if isinstance(from_node, bpy.types.GeometryNodeSwitch) and isinstance(
            to_node, bpy.types.GeometryNodeSwitch
        ):
            to_node.input_type = from_node.input_type
        if isinstance(from_node, bpy.types.GeometryNodeExtrudeMesh) and isinstance(
            to_node, bpy.types.GeometryNodeExtrudeMesh
        ):
            to_node.mode = from_node.mode
        if isinstance(from_node, bpy.types.GeometryNodeDeleteGeometry) and isinstance(
            to_node, bpy.types.GeometryNodeDeleteGeometry
        ):
            to_node.domain = from_node.domain
            to_node.mode = from_node.mode
        if isinstance(from_node, bpy.types.GeometryNodeSeparateGeometry) and isinstance(
            to_node, bpy.types.GeometryNodeSeparateGeometry
        ):
            to_node.domain = from_node.domain

    if (
        bpy.app.version >= (3, 4)
        and isinstance(from_node, bpy.types.ShaderNodeMix)
        and isinstance(to_node, bpy.types.ShaderNodeMix)
    ):
        to_node.blend_type = from_node.blend_type
        to_node.clamp_factor = from_node.clamp_factor
        to_node.clamp_result = from_node.clamp_result
        to_node.data_type = from_node.data_type
        to_node.factor_mode = from_node.factor_mode

    if bpy.app.version < (4, 0):
        to_node.width_hidden = from_node.width_hidden
        if isinstance(from_node, bpy.types.ShaderNodeBsdfGlossy) and isinstance(
            to_node, bpy.types.ShaderNodeBsdfGlossy
        ):
            to_node.distribution = from_node.distribution


def clear_node_tree(
    node_tree: Optional[bpy.types.NodeTree], clear_inputs_outputs: bool = False
) -> None:
    if node_tree is None:
        return

    # node_tree.links.clear()
    while node_tree.links:
        node_tree.links.remove(node_tree.links[0])

    # node_tree.nodes.clear()
    while node_tree.nodes:
        node_tree.nodes.remove(node_tree.nodes[0])

    if not clear_inputs_outputs:
        return

    if bpy.app.version < (4, 0):
        # node_tree.inputs.clear()
        while node_tree.inputs:
            node_tree.inputs.remove(node_tree.inputs[0])

        # node_tree.outputs.clear()
        while node_tree.outputs:
            node_tree.outputs.remove(node_tree.outputs[0])

        return

    node_tree.interface.clear()


def copy_node_tree_inputs_outputs(
    from_node_tree: bpy.types.NodeTree, to_node_tree: bpy.types.NodeTree
) -> None:
    while len(to_node_tree.inputs) > len(from_node_tree.inputs):
        to_node_tree.inputs.remove(to_node_tree.inputs[-1])
    for index, from_input in enumerate(from_node_tree.inputs):
        to_input = None
        if isinstance(
            from_input, bpy.types.NodeSocketInterfaceStandard
        ) and 0 <= index < len(to_node_tree.inputs):
            to_input = to_node_tree.inputs[index]
            if (
                isinstance(to_input, bpy.types.NodeSocketInterfaceStandard)
                and to_input.type != from_input.type
            ):
                to_input = None
                while len(to_node_tree.inputs) > index:
                    to_node_tree.inputs.remove(to_node_tree.inputs[-1])
        if not to_input:
            to_input = to_node_tree.inputs.new(
                from_input.bl_socket_idname, from_input.name
            )
        copy_socket_interface(from_input, to_input)

    while len(to_node_tree.outputs) > len(from_node_tree.outputs):
        to_node_tree.outputs.remove(to_node_tree.outputs[-1])
    for index, from_output in enumerate(from_node_tree.outputs):
        to_output = None
        if isinstance(
            from_output, bpy.types.NodeSocketInterfaceStandard
        ) and 0 <= index < len(to_node_tree.outputs):
            to_output = to_node_tree.outputs[index]
            if (
                isinstance(to_output, bpy.types.NodeSocketInterfaceStandard)
                and to_output.type != from_output.type
            ):
                to_output = None
                while len(to_node_tree.outputs) > index:
                    to_node_tree.outputs.remove(to_node_tree.outputs[-1])
        if not to_output:
            to_output = to_node_tree.outputs.new(
                from_output.bl_socket_idname, from_output.name
            )
        copy_socket_interface(from_output, to_output)


def copy_node_tree_interface_socket(
    from_socket: "bpy.types.NodeTreeInterfaceSocket",
    to_socket: "bpy.types.NodeTreeInterfaceSocket",
) -> None:
    float_classes = (
        bpy.types.NodeTreeInterfaceSocketFloat,
        bpy.types.NodeTreeInterfaceSocketFloatAngle,
        bpy.types.NodeTreeInterfaceSocketFloatDistance,
        bpy.types.NodeTreeInterfaceSocketFloatFactor,
        bpy.types.NodeTreeInterfaceSocketFloatPercentage,
        bpy.types.NodeTreeInterfaceSocketFloatTime,
        bpy.types.NodeTreeInterfaceSocketFloatTimeAbsolute,
        bpy.types.NodeTreeInterfaceSocketFloatUnsigned,
    )
    color_classes = (bpy.types.NodeTreeInterfaceSocketColor,)
    vector_classes = (
        bpy.types.NodeTreeInterfaceSocketVector,
        bpy.types.NodeTreeInterfaceSocketVectorAcceleration,
        bpy.types.NodeTreeInterfaceSocketVectorDirection,
        bpy.types.NodeTreeInterfaceSocketVectorEuler,
        bpy.types.NodeTreeInterfaceSocketVectorTranslation,
        bpy.types.NodeTreeInterfaceSocketVectorVelocity,
        bpy.types.NodeTreeInterfaceSocketVectorXYZ,
    )

    to_socket.attribute_domain = from_socket.attribute_domain
    to_socket.default_attribute_name = from_socket.default_attribute_name

    if isinstance(from_socket, float_classes) and isinstance(to_socket, float_classes):
        to_socket.default_value = from_socket.default_value
        to_socket.min_value = from_socket.min_value
        to_socket.max_value = from_socket.max_value
    elif isinstance(from_socket, color_classes) and isinstance(
        to_socket, color_classes
    ):
        to_socket.default_value = deepcopy(from_socket.default_value[0:4])
    elif isinstance(from_socket, vector_classes) and isinstance(
        to_socket, vector_classes
    ):
        to_socket.min_value = from_socket.min_value
        to_socket.max_value = from_socket.max_value


def copy_node_tree_interface(
    from_node_tree: bpy.types.NodeTree, to_node_tree: bpy.types.NodeTree
) -> None:
    # TODO: differential update
    to_node_tree.interface.clear()

    for item in from_node_tree.interface.items_tree:
        if item.item_type != "SOCKET" or not isinstance(
            item, bpy.types.NodeTreeInterfaceSocket
        ):
            continue
        socket_type = item.socket_type
        if not socket_type:
            logger.error(
                f"{item.name} has empty socket_type. type={type(item).__name__}"
            )
            if isinstance(item, bpy.types.NodeTreeInterfaceSocketFloatFactor):
                socket_type = "NodeSocketFloat"
            else:
                continue
        to_socket = to_node_tree.interface.new_socket(
            item.name,
            description=item.description,
            in_out=item.in_out,
            socket_type=socket_type,
        )
        copy_node_tree_interface_socket(item, to_socket)


def copy_node_tree(
    from_node_tree: bpy.types.NodeTree, to_node_tree: bpy.types.NodeTree
) -> None:
    clear_node_tree(to_node_tree, clear_inputs_outputs=False)

    if bpy.app.version < (4, 0):
        copy_node_tree_inputs_outputs(from_node_tree, to_node_tree)
    else:
        copy_node_tree_interface(from_node_tree, to_node_tree)

    from_to: dict[bpy.types.Node, bpy.types.Node] = {}

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
        if not 0 <= input_socket_index < len(input_node.inputs):
            logger.error(
                "Input socket out of range: "
                + f"{input_socket_index} < {len(input_node.inputs)}"
            )
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
        if not 0 <= output_socket_index < len(output_node.outputs):
            logger.error(
                "Output socket out of range: "
                + f"{output_socket_index} < {len(output_node.outputs)}"
            )
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
        to_node.location = deepcopy(
            (
                from_node.location[0],
                from_node.location[1],
            )
        )


def shader_node_group_import(shader_node_group_name: str) -> None:
    if shader_node_group_name in bpy.data.node_groups:
        return
    for file_name in file_names:
        path = str(Path(__file__).with_name(file_name)) + "/NodeTree"
        bpy.ops.wm.append(
            filepath=path + "/" + shader_node_group_name,
            filename=shader_node_group_name,
            directory=path,
        )


def get_image_name_and_sampler_type(
    shader_node: bpy.types.Node, input_socket_name: str
) -> Optional[tuple[str, int, int]]:
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

    if not isinstance(from_node, bpy.types.ShaderNodeTexImage):
        return None

    image = from_node.image
    if not image:
        return None

    image_name = image.name
    if not image_name:
        return None

    # blender is ('Linear', 'Closest', 'Cubic', 'Smart') glTF is Linear, Closest
    if from_node.interpolation == "Closest":
        filter_type = GL_NEAREST
    else:
        filter_type = GL_LINEAR

    # blender is ('REPEAT', 'EXTEND', 'CLIP') glTF is CLAMP_TO_EDGE,MIRRORED_REPEAT,REPEAT
    if from_node.extension == "REPEAT":
        wrap_type = GL_REPEAT
    else:
        wrap_type = GL_CLAMP_TO_EDGE

    return image_name, wrap_type, filter_type


def float_or_none(
    v: object, min_value: float = -float_info.max, max_value: float = float_info.max
) -> Optional[float]:
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

    default_value = float_or_none(
        getattr(socket, "default_value", None), min_value, max_value
    )

    links = socket.links
    if not links:
        return default_value

    from_node = links[0].from_node
    if not from_node:
        return default_value

    outputs = from_node.outputs
    if not outputs:
        return default_value

    return float_or_none(
        getattr(outputs[0], "default_value", None), min_value, max_value
    )


def rgba_or_none(
    vs: object, min_value: float = -float_info.max, max_value: float = float_info.max
) -> Optional[tuple[float, float, float, float]]:
    default_alpha_value = max(min_value, min(1.0, max_value))
    if isinstance(vs, Color):
        return (
            max(min_value, min(vs.r, max_value)),
            max(min_value, min(vs.g, max_value)),
            max(min_value, min(vs.b, max_value)),
            default_alpha_value,
        )

    iterator = convert.iterator_or_none(vs)
    if iterator is None:
        return None

    rgba: list[float] = []
    for v in iterator:
        f = float_or_none(v, min_value, max_value)
        if f is None:
            return None
        rgba.append(f)
        if len(rgba) > 4:
            return None

    if len(rgba) == 3:
        rgba.append(default_alpha_value)
    if len(rgba) != 4:
        return None

    return (rgba[0], rgba[1], rgba[2], rgba[3])


def get_rgba_value(
    shader_node: bpy.types.Node,
    input_socket_name: str,
    min_value: float = -float_info.max,
    max_value: float = float_info.max,
) -> Optional[tuple[float, float, float, float]]:
    socket = shader_node.inputs.get(input_socket_name)
    if not socket:
        return None

    default_value = rgba_or_none(
        getattr(socket, "default_value", None), min_value, max_value
    )

    links = socket.links
    if not links:
        return default_value

    from_node = links[0].from_node
    if not from_node:
        return default_value

    outputs = from_node.outputs
    if not outputs:
        return default_value

    return rgba_or_none(
        getattr(outputs[0], "default_value", None), min_value, max_value
    )


def rgb_or_none(
    vs: object, min_value: float = -float_info.max, max_value: float = float_info.max
) -> Optional[tuple[float, float, float]]:
    if isinstance(vs, Color):
        return (
            max(min_value, min(vs.r, max_value)),
            max(min_value, min(vs.g, max_value)),
            max(min_value, min(vs.b, max_value)),
        )

    iterator = convert.iterator_or_none(vs)
    if iterator is None:
        return None

    rgb: list[float] = []
    for v in iterator:
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


def get_rgb_value(
    shader_node: bpy.types.Node,
    input_socket_name: str,
    min_value: float = -float_info.max,
    max_value: float = float_info.max,
) -> Optional[tuple[float, float, float]]:
    socket = shader_node.inputs.get(input_socket_name)
    if not socket:
        return None

    default_value = rgb_or_none(
        getattr(socket, "default_value", None), min_value, max_value
    )

    links = socket.links
    if not links:
        return default_value

    from_node = links[0].from_node
    if not from_node:
        return default_value

    outputs = from_node.outputs
    if not outputs:
        return default_value

    return rgb_or_none(getattr(outputs[0], "default_value", None), min_value, max_value)
