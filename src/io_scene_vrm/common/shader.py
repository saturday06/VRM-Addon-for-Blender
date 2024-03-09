import math
import random
import string
from copy import deepcopy
from pathlib import Path
from sys import float_info
from typing import Optional

import bpy
from bpy.types import (
    Context,
    Material,
    Node,
    NodeFrame,
    NodeGroup,
    NodeGroupOutput,
    NodeSocket,
    NodeSocketBool,
    NodeSocketColor,
    NodeSocketFloat,
    NodeSocketFloatAngle,
    NodeSocketFloatFactor,
    NodeSocketFloatPercentage,
    NodeSocketFloatTime,
    NodeSocketFloatUnsigned,
    NodeSocketInt,
    NodeSocketIntFactor,
    NodeSocketIntPercentage,
    NodeSocketIntUnsigned,
    NodeSocketString,
    NodeSocketVector,
    NodeSocketVectorAcceleration,
    NodeSocketVectorDirection,
    NodeSocketVectorEuler,
    NodeSocketVectorTranslation,
    NodeSocketVectorVelocity,
    NodeSocketVectorXYZ,
    NodeTree,
    ShaderNodeAmbientOcclusion,
    ShaderNodeAttribute,
    ShaderNodeBevel,
    ShaderNodeBsdfAnisotropic,
    ShaderNodeBsdfGlass,
    ShaderNodeBsdfHair,
    ShaderNodeBsdfHairPrincipled,
    ShaderNodeBsdfPrincipled,
    ShaderNodeBsdfRefraction,
    ShaderNodeBsdfToon,
    ShaderNodeBump,
    ShaderNodeClamp,
    ShaderNodeCustomGroup,
    ShaderNodeDisplacement,
    ShaderNodeGroup,
    ShaderNodeMapping,
    ShaderNodeMapRange,
    ShaderNodeMath,
    ShaderNodeMixRGB,
    ShaderNodeNormalMap,
    ShaderNodeOutputAOV,
    ShaderNodeOutputLight,
    ShaderNodeOutputLineStyle,
    ShaderNodeOutputMaterial,
    ShaderNodeOutputWorld,
    ShaderNodeScript,
    ShaderNodeSubsurfaceScattering,
    ShaderNodeTangent,
    ShaderNodeTexBrick,
    ShaderNodeTexCoord,
    ShaderNodeTexEnvironment,
    ShaderNodeTexGradient,
    ShaderNodeTexIES,
    ShaderNodeTexImage,
    ShaderNodeTexMagic,
    ShaderNodeTexNoise,
    ShaderNodeTexPointDensity,
    ShaderNodeTexSky,
    ShaderNodeTexVoronoi,
    ShaderNodeTexWave,
    ShaderNodeTexWhiteNoise,
    ShaderNodeUVAlongStroke,
    ShaderNodeUVMap,
    ShaderNodeVectorDisplacement,
    ShaderNodeVectorMath,
    ShaderNodeVectorRotate,
    ShaderNodeVectorTransform,
    ShaderNodeVertexColor,
    ShaderNodeWireframe,
)
from mathutils import Color

from . import convert
from .char import INTERNAL_NAME_PREFIX
from .gl import GL_CLAMP_TO_EDGE, GL_LINEAR, GL_NEAREST, GL_REPEAT
from .logging import get_logger

logger = get_logger(__name__)

BOOL_SOCKET_CLASSES = (NodeSocketBool,)
FLOAT_SOCKET_CLASSES = (
    NodeSocketFloat,
    NodeSocketFloatAngle,
    NodeSocketFloatFactor,
    NodeSocketFloatPercentage,
    NodeSocketFloatTime,
    NodeSocketFloatUnsigned,
)
INT_SOCKET_CLASSES = (
    NodeSocketInt,
    NodeSocketIntFactor,
    NodeSocketIntPercentage,
    NodeSocketIntUnsigned,
)
SCALAR_SOCKET_CLASSES = (
    *BOOL_SOCKET_CLASSES,
    *FLOAT_SOCKET_CLASSES,
    *INT_SOCKET_CLASSES,
)
VECTOR_SOCKET_CLASSES = (
    NodeSocketVector,
    NodeSocketVectorAcceleration,
    NodeSocketVectorDirection,
    NodeSocketVectorEuler,
    NodeSocketVectorTranslation,
    NodeSocketVectorVelocity,
    NodeSocketVectorXYZ,
)
COLOR_SOCKET_CLASSES = (NodeSocketColor,)
STRING_SOCKET_CLASSES = (NodeSocketString,)

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


def backup_name(name: str, backup_suffix: str) -> str:
    return name.removesuffix(" Template") + backup_suffix


def generate_backup_suffix() -> str:
    # 極々稀に重複する可能性があるが、長すぎる名前が使えないので悩ましい。
    return " " + "".join(
        random.SystemRandom().choice(string.ascii_letters + string.digits)
        for _ in range(8)
    )


def add_shaders() -> None:
    for file_name in file_names:
        path = Path(__file__).with_name(file_name)
        with bpy.data.libraries.load(str(path), link=False) as (data_from, data_to):
            for node_group in data_from.node_groups:
                if node_group not in bpy.data.node_groups:
                    data_to.node_groups.append(node_group)


def load_mtoon1_outline_geometry_node_group(context: Context, overwrite: bool) -> None:
    if bpy.app.version < (3, 3):
        return
    if not overwrite and OUTLINE_GEOMETRY_GROUP_NAME in bpy.data.node_groups:
        return

    backup_suffix = generate_backup_suffix()

    template_outline_group_name = template_name(OUTLINE_GEOMETRY_GROUP_NAME)
    old_template_outline_group = bpy.data.node_groups.get(template_outline_group_name)
    if old_template_outline_group:
        logger.error(f'Node Group "{template_outline_group_name}" already exists')
        old_template_outline_group.name = backup_name(
            old_template_outline_group.name, backup_suffix
        )

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
            filepath=(outline_node_tree_path + "/" + template_outline_group_name),
            filename=template_outline_group_name,
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
        template_outline_group = bpy.data.node_groups.get(template_outline_group_name)
        if not template_outline_group:
            raise ValueError("No " + template_outline_group_name)

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

        old_template_outline_group = bpy.data.node_groups.get(
            backup_name(template_outline_group_name, backup_suffix)
        )
        if old_template_outline_group:
            old_template_outline_group.name = template_outline_group_name


def load_mtoon1_shader(
    context: Context,
    material: Material,
    overwrite: bool,
) -> None:
    if not material.use_nodes:
        material.use_nodes = True

    load_mtoon1_outline_geometry_node_group(context, overwrite)

    backup_suffix = generate_backup_suffix()

    template_material_name = template_name("VRM Add-on MToon 1.0")
    old_material = bpy.data.materials.get(template_material_name)
    if old_material:
        logger.error(f'Material "{template_material_name}" already exists')
        old_material.name = backup_name(old_material.name, backup_suffix)

    for shader_node_group_name in shader_node_group_names:
        name = template_name(shader_node_group_name)
        old_template_group = bpy.data.node_groups.get(name)
        if old_template_group:
            logger.error(f'Node Group "{name}" already exists')
            old_template_group.name = backup_name(
                old_template_group.name, backup_suffix
            )

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
            filepath=material_path + "/" + template_material_name,
            filename=template_material_name,
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

        template_material = bpy.data.materials.get(template_material_name)
        if not template_material:
            raise ValueError("No " + template_material_name)

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

        old_material = bpy.data.materials.get(
            backup_name(template_material_name, backup_suffix)
        )
        if old_material:
            old_material.name = template_material_name

        for shader_node_group_name in shader_node_group_names:
            name = template_name(shader_node_group_name)
            old_template_group = bpy.data.node_groups.get(
                backup_name(name, backup_suffix)
            )
            if old_template_group:
                old_template_group.name = name


def copy_socket(from_socket: NodeSocket, to_socket: NodeSocket) -> None:
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
    # bpy.app.version < (4,)
    from bpy.types import (
        NodeSocketInterfaceColor,
        NodeSocketInterfaceFloat,
        NodeSocketInterfaceFloatAngle,
        NodeSocketInterfaceFloatDistance,
        NodeSocketInterfaceFloatFactor,
        NodeSocketInterfaceFloatPercentage,
        NodeSocketInterfaceFloatTime,
        NodeSocketInterfaceFloatUnsigned,
        NodeSocketInterfaceVector,
        NodeSocketInterfaceVectorAcceleration,
        NodeSocketInterfaceVectorDirection,
        NodeSocketInterfaceVectorEuler,
        NodeSocketInterfaceVectorTranslation,
        NodeSocketInterfaceVectorVelocity,
        NodeSocketInterfaceVectorXYZ,
    )

    if bpy.app.version >= (3, 0, 0):
        to_socket.attribute_domain = from_socket.attribute_domain
        to_socket.bl_label = from_socket.bl_label
    to_socket.description = from_socket.description
    to_socket.name = from_socket.name

    float_classes = (
        NodeSocketInterfaceFloat,
        NodeSocketInterfaceFloatAngle,
        NodeSocketInterfaceFloatDistance,
        NodeSocketInterfaceFloatFactor,
        NodeSocketInterfaceFloatPercentage,
        NodeSocketInterfaceFloatTime,
        NodeSocketInterfaceFloatUnsigned,
    )
    color_classes = (NodeSocketInterfaceColor,)
    vector_classes = (
        NodeSocketInterfaceVector,
        NodeSocketInterfaceVectorAcceleration,
        NodeSocketInterfaceVectorDirection,
        NodeSocketInterfaceVectorEuler,
        NodeSocketInterfaceVectorTranslation,
        NodeSocketInterfaceVectorVelocity,
        NodeSocketInterfaceVectorXYZ,
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
    from_socket: NodeSocket,
    to_socket: NodeSocket,
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
    from_node: Node,
    to_node: Node,
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
    from_node: ShaderNodeGroup,
    to_node: ShaderNodeGroup,
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
    from_node: Node,
    to_node: Node,
    from_to: dict[Node, Node],
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

    if isinstance(from_node, NodeFrame) and isinstance(to_node, NodeFrame):
        to_node.shrink = from_node.shrink
        to_node.label_size = from_node.label_size
        to_node.text = from_node.text
    if isinstance(from_node, NodeGroup):
        logger.error("Importing NodeGroup doesn't be supported yet")
    if isinstance(from_node, NodeGroupOutput) and isinstance(to_node, NodeGroupOutput):
        to_node.is_active_output = from_node.is_active_output
    if isinstance(from_node, ShaderNodeWireframe) and isinstance(
        to_node, ShaderNodeWireframe
    ):
        to_node.use_pixel_size = from_node.use_pixel_size
    if isinstance(from_node, ShaderNodeVertexColor) and isinstance(
        to_node, ShaderNodeVertexColor
    ):
        to_node.layer_name = from_node.layer_name
    if isinstance(from_node, ShaderNodeVectorTransform) and isinstance(
        to_node, ShaderNodeVectorTransform
    ):
        to_node.convert_from = from_node.convert_from
        to_node.convert_to = from_node.convert_to
        to_node.vector_type = from_node.vector_type
    if isinstance(from_node, ShaderNodeVectorRotate) and isinstance(
        to_node, ShaderNodeVectorRotate
    ):
        to_node.invert = from_node.invert
        to_node.rotation_type = from_node.rotation_type
    if isinstance(from_node, ShaderNodeVectorMath) and isinstance(
        to_node, ShaderNodeVectorMath
    ):
        to_node.operation = from_node.operation
    if isinstance(from_node, ShaderNodeVectorDisplacement) and isinstance(
        to_node, ShaderNodeVectorDisplacement
    ):
        to_node.space = from_node.space
    if isinstance(from_node, ShaderNodeUVMap) and isinstance(to_node, ShaderNodeUVMap):
        to_node.from_instancer = from_node.from_instancer
        to_node.uv_map = from_node.uv_map
    if isinstance(from_node, ShaderNodeUVAlongStroke) and isinstance(
        to_node, ShaderNodeUVAlongStroke
    ):
        to_node.use_tips = from_node.use_tips
    if isinstance(from_node, ShaderNodeTexWhiteNoise) and isinstance(
        to_node, ShaderNodeTexWhiteNoise
    ):
        to_node.noise_dimensions = from_node.noise_dimensions
    if isinstance(from_node, ShaderNodeTexWave) and isinstance(
        to_node, ShaderNodeTexWave
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
    if isinstance(from_node, ShaderNodeTexVoronoi) and isinstance(
        to_node, ShaderNodeTexVoronoi
    ):
        to_node.distance = from_node.distance
        to_node.feature = from_node.feature
        to_node.voronoi_dimensions = from_node.voronoi_dimensions
    if isinstance(from_node, ShaderNodeTexSky) and isinstance(
        to_node, ShaderNodeTexSky
    ):
        to_node.ground_albedo = from_node.ground_albedo
        to_node.sky_type = from_node.sky_type
        to_node.sun_direction = from_node.sun_direction[:]
        to_node.turbidity = from_node.turbidity
    if isinstance(from_node, ShaderNodeTexPointDensity) and isinstance(
        to_node, ShaderNodeTexPointDensity
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
    if isinstance(from_node, ShaderNodeTexNoise) and isinstance(
        to_node, ShaderNodeTexNoise
    ):
        to_node.noise_dimensions = from_node.noise_dimensions
    if isinstance(from_node, ShaderNodeTexMagic) and isinstance(
        to_node, ShaderNodeTexMagic
    ):
        to_node.turbulence_depth = from_node.turbulence_depth
    if isinstance(from_node, ShaderNodeTexImage) and isinstance(
        to_node, ShaderNodeTexImage
    ):
        to_node.extension = from_node.extension
        # to_node.image = from_node.image
        to_node.interpolation = from_node.interpolation
        to_node.projection = from_node.projection
        to_node.projection_blend = from_node.projection_blend
    if isinstance(from_node, ShaderNodeTexIES) and isinstance(
        to_node, ShaderNodeTexIES
    ):
        to_node.filepath = from_node.filepath
        to_node.ies = from_node.ies
        to_node.mode = from_node.mode
    if isinstance(from_node, ShaderNodeTexGradient) and isinstance(
        to_node, ShaderNodeTexGradient
    ):
        to_node.gradient_type = from_node.gradient_type
    if isinstance(from_node, ShaderNodeTexEnvironment) and isinstance(
        to_node, ShaderNodeTexEnvironment
    ):
        to_node.image = from_node.image
        to_node.interpolation = from_node.interpolation
        to_node.projection = from_node.projection
    if isinstance(from_node, ShaderNodeTexCoord) and isinstance(
        to_node, ShaderNodeTexCoord
    ):
        to_node.from_instancer = from_node.from_instancer
        to_node.object = from_node.object
    if isinstance(from_node, ShaderNodeTexBrick) and isinstance(
        to_node, ShaderNodeTexBrick
    ):
        to_node.offset = from_node.offset
        to_node.offset_frequency = from_node.offset_frequency
        to_node.squash = from_node.squash
        to_node.squash_frequency = from_node.squash_frequency
    if isinstance(from_node, ShaderNodeTangent) and isinstance(
        to_node, ShaderNodeTangent
    ):
        to_node.axis = from_node.axis
        to_node.direction_type = from_node.direction_type
        to_node.uv_map = from_node.uv_map
    if isinstance(from_node, ShaderNodeSubsurfaceScattering) and isinstance(
        to_node, ShaderNodeSubsurfaceScattering
    ):
        to_node.falloff = from_node.falloff
    if isinstance(from_node, ShaderNodeScript) and isinstance(
        to_node, ShaderNodeScript
    ):
        to_node.bytecode = from_node.bytecode
        to_node.bytecode_hash = from_node.bytecode_hash
        to_node.filepath = from_node.filepath
        to_node.mode = from_node.mode
        to_node.script = from_node.script
        to_node.use_auto_update = from_node.use_auto_update
    if isinstance(from_node, ShaderNodeOutputWorld) and isinstance(
        to_node, ShaderNodeOutputWorld
    ):
        to_node.is_active_output = from_node.is_active_output
        to_node.target = from_node.target
    if isinstance(from_node, ShaderNodeOutputMaterial) and isinstance(
        to_node, ShaderNodeOutputMaterial
    ):
        to_node.is_active_output = from_node.is_active_output
        to_node.target = from_node.target
    if isinstance(from_node, ShaderNodeOutputLineStyle) and isinstance(
        to_node, ShaderNodeOutputLineStyle
    ):
        to_node.blend_type = from_node.blend_type
        to_node.is_active_output = from_node.is_active_output
        to_node.target = from_node.target
        to_node.use_alpha = from_node.use_alpha
        to_node.use_clamp = from_node.use_clamp
    if isinstance(from_node, ShaderNodeOutputLight) and isinstance(
        to_node, ShaderNodeOutputLight
    ):
        to_node.is_active_output = from_node.is_active_output
        to_node.target = from_node.target
    if isinstance(from_node, ShaderNodeOutputAOV) and isinstance(
        to_node, ShaderNodeOutputAOV
    ):
        to_node.name = from_node.name
    if isinstance(from_node, ShaderNodeNormalMap) and isinstance(
        to_node, ShaderNodeNormalMap
    ):
        to_node.space = from_node.space
        to_node.uv_map = from_node.uv_map
    if isinstance(from_node, ShaderNodeMixRGB) and isinstance(
        to_node, ShaderNodeMixRGB
    ):
        to_node.blend_type = from_node.blend_type
        to_node.use_alpha = from_node.use_alpha
        to_node.use_clamp = from_node.use_clamp
    if isinstance(from_node, ShaderNodeMath) and isinstance(to_node, ShaderNodeMath):
        to_node.operation = from_node.operation
        to_node.use_clamp = from_node.use_clamp
    if isinstance(from_node, ShaderNodeMapping) and isinstance(
        to_node, ShaderNodeMapping
    ):
        to_node.vector_type = from_node.vector_type
    if isinstance(from_node, ShaderNodeMapRange) and isinstance(
        to_node, ShaderNodeMapRange
    ):
        to_node.clamp = from_node.clamp
        to_node.interpolation_type = from_node.interpolation_type
    if isinstance(from_node, ShaderNodeGroup) and isinstance(to_node, ShaderNodeGroup):
        copy_shader_node_group(from_node, to_node)
    if isinstance(from_node, ShaderNodeDisplacement) and isinstance(
        to_node, ShaderNodeDisplacement
    ):
        to_node.space = from_node.space
    if isinstance(from_node, ShaderNodeCustomGroup) and isinstance(
        to_node, ShaderNodeCustomGroup
    ):
        # to_node.node_tree = from_node.node_tree
        logger.error("Importing ShaderNodeCustomGroup doesn't be supported yet")
    if isinstance(from_node, ShaderNodeClamp) and isinstance(to_node, ShaderNodeClamp):
        to_node.clamp_type = from_node.clamp_type
    if isinstance(from_node, ShaderNodeBump) and isinstance(to_node, ShaderNodeBump):
        to_node.invert = from_node.invert
    if isinstance(from_node, ShaderNodeBsdfToon) and isinstance(
        to_node, ShaderNodeBsdfToon
    ):
        to_node.component = from_node.component
    if isinstance(from_node, ShaderNodeBsdfRefraction) and isinstance(
        to_node, ShaderNodeBsdfRefraction
    ):
        to_node.distribution = from_node.distribution
    if isinstance(from_node, ShaderNodeBsdfPrincipled) and isinstance(
        to_node, ShaderNodeBsdfPrincipled
    ):
        to_node.distribution = from_node.distribution
        to_node.subsurface_method = from_node.subsurface_method
    if isinstance(from_node, ShaderNodeBsdfHairPrincipled) and isinstance(
        to_node, ShaderNodeBsdfHairPrincipled
    ):
        to_node.parametrization = from_node.parametrization
    if isinstance(from_node, ShaderNodeBsdfHair) and isinstance(
        to_node, ShaderNodeBsdfHair
    ):
        to_node.component = from_node.component
    if isinstance(from_node, ShaderNodeBsdfGlass) and isinstance(
        to_node, ShaderNodeBsdfGlass
    ):
        to_node.distribution = from_node.distribution
    if isinstance(from_node, ShaderNodeBsdfAnisotropic) and isinstance(
        to_node, ShaderNodeBsdfAnisotropic
    ):
        to_node.distribution = from_node.distribution
    if isinstance(from_node, ShaderNodeBevel) and isinstance(to_node, ShaderNodeBevel):
        to_node.samples = from_node.samples
    if isinstance(from_node, ShaderNodeAttribute) and isinstance(
        to_node, ShaderNodeAttribute
    ):
        to_node.attribute_name = from_node.attribute_name
    if isinstance(from_node, ShaderNodeAmbientOcclusion) and isinstance(
        to_node, ShaderNodeAmbientOcclusion
    ):
        to_node.inside = from_node.inside
        to_node.only_local = from_node.only_local
        to_node.samples = from_node.samples

    if bpy.app.version >= (3, 3):
        from bpy.types import (
            GeometryNodeDeleteGeometry,
            GeometryNodeExtrudeMesh,
            GeometryNodeSeparateGeometry,
            GeometryNodeSwitch,
            ShaderNodeCombineColor,
            ShaderNodeSeparateColor,
        )

        if isinstance(from_node, ShaderNodeCombineColor) and isinstance(
            to_node, ShaderNodeCombineColor
        ):
            to_node.mode = from_node.mode
        if isinstance(from_node, ShaderNodeSeparateColor) and isinstance(
            to_node, ShaderNodeSeparateColor
        ):
            to_node.mode = from_node.mode

        if isinstance(from_node, GeometryNodeSwitch) and isinstance(
            to_node, GeometryNodeSwitch
        ):
            to_node.input_type = from_node.input_type
        if isinstance(from_node, GeometryNodeExtrudeMesh) and isinstance(
            to_node, GeometryNodeExtrudeMesh
        ):
            to_node.mode = from_node.mode
        if isinstance(from_node, GeometryNodeDeleteGeometry) and isinstance(
            to_node, GeometryNodeDeleteGeometry
        ):
            to_node.domain = from_node.domain
            to_node.mode = from_node.mode
        if isinstance(from_node, GeometryNodeSeparateGeometry) and isinstance(
            to_node, GeometryNodeSeparateGeometry
        ):
            to_node.domain = from_node.domain

    if bpy.app.version >= (3, 4):
        from bpy.types import ShaderNodeMix

        if isinstance(from_node, ShaderNodeMix) and isinstance(to_node, ShaderNodeMix):
            to_node.blend_type = from_node.blend_type
            to_node.clamp_factor = from_node.clamp_factor
            to_node.clamp_result = from_node.clamp_result
            to_node.data_type = from_node.data_type
            to_node.factor_mode = from_node.factor_mode

    if bpy.app.version < (4, 0):
        from bpy.types import ShaderNodeBsdfGlossy

        to_node.width_hidden = from_node.width_hidden
        if isinstance(from_node, ShaderNodeBsdfGlossy) and isinstance(
            to_node, ShaderNodeBsdfGlossy
        ):
            to_node.distribution = from_node.distribution

    if bpy.app.version < (4, 1):
        from bpy.types import ShaderNodeTexMusgrave

        if isinstance(from_node, ShaderNodeTexMusgrave) and isinstance(
            to_node, ShaderNodeTexMusgrave
        ):
            to_node.musgrave_dimensions = from_node.musgrave_dimensions
            to_node.musgrave_type = from_node.musgrave_type


def clear_node_tree(
    node_tree: Optional[NodeTree], clear_inputs_outputs: bool = False
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
    from_node_tree: NodeTree, to_node_tree: NodeTree
) -> None:
    # bpy.app.version < (4,)
    from bpy.types import NodeSocketInterfaceStandard

    while len(to_node_tree.inputs) > len(from_node_tree.inputs):
        to_node_tree.inputs.remove(to_node_tree.inputs[-1])
    for index, from_input in enumerate(from_node_tree.inputs):
        to_input = None
        if isinstance(from_input, NodeSocketInterfaceStandard) and 0 <= index < len(
            to_node_tree.inputs
        ):
            to_input = to_node_tree.inputs[index]
            if (
                isinstance(to_input, NodeSocketInterfaceStandard)
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
        if isinstance(from_output, NodeSocketInterfaceStandard) and 0 <= index < len(
            to_node_tree.outputs
        ):
            to_output = to_node_tree.outputs[index]
            if (
                isinstance(to_output, NodeSocketInterfaceStandard)
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
    from bpy.types import (
        NodeTreeInterfaceSocketColor,
        NodeTreeInterfaceSocketFloat,
        NodeTreeInterfaceSocketFloatAngle,
        NodeTreeInterfaceSocketFloatDistance,
        NodeTreeInterfaceSocketFloatFactor,
        NodeTreeInterfaceSocketFloatPercentage,
        NodeTreeInterfaceSocketFloatTime,
        NodeTreeInterfaceSocketFloatTimeAbsolute,
        NodeTreeInterfaceSocketFloatUnsigned,
        NodeTreeInterfaceSocketVector,
        NodeTreeInterfaceSocketVectorAcceleration,
        NodeTreeInterfaceSocketVectorDirection,
        NodeTreeInterfaceSocketVectorEuler,
        NodeTreeInterfaceSocketVectorTranslation,
        NodeTreeInterfaceSocketVectorVelocity,
        NodeTreeInterfaceSocketVectorXYZ,
    )

    float_classes = (
        NodeTreeInterfaceSocketFloat,
        NodeTreeInterfaceSocketFloatAngle,
        NodeTreeInterfaceSocketFloatDistance,
        NodeTreeInterfaceSocketFloatFactor,
        NodeTreeInterfaceSocketFloatPercentage,
        NodeTreeInterfaceSocketFloatTime,
        NodeTreeInterfaceSocketFloatTimeAbsolute,
        NodeTreeInterfaceSocketFloatUnsigned,
    )
    color_classes = (NodeTreeInterfaceSocketColor,)
    vector_classes = (
        NodeTreeInterfaceSocketVector,
        NodeTreeInterfaceSocketVectorAcceleration,
        NodeTreeInterfaceSocketVectorDirection,
        NodeTreeInterfaceSocketVectorEuler,
        NodeTreeInterfaceSocketVectorTranslation,
        NodeTreeInterfaceSocketVectorVelocity,
        NodeTreeInterfaceSocketVectorXYZ,
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
        to_socket.min_value = from_socket.min_value
        to_socket.max_value = from_socket.max_value


def copy_node_tree_interface(from_node_tree: NodeTree, to_node_tree: NodeTree) -> None:
    from bpy.types import NodeTreeInterfaceSocket, NodeTreeInterfaceSocketFloatFactor

    to_items_index = 0

    for from_item in from_node_tree.interface.items_tree:
        if from_item.item_type != "SOCKET" or not isinstance(
            from_item, NodeTreeInterfaceSocket
        ):
            continue
        from_socket_type = from_item.socket_type
        if not from_socket_type:
            logger.error(
                f"{from_item.name} has empty socket_type."
                + f" type={type(from_item).__name__}"
            )
            if isinstance(from_item, NodeTreeInterfaceSocketFloatFactor):
                from_socket_type = "NodeSocketFloat"
            else:
                continue

        to_socket: Optional[NodeTreeInterfaceSocket] = None
        while len(to_node_tree.interface.items_tree) > to_items_index:
            to_item = list(to_node_tree.interface.items_tree.values())[to_items_index]
            if (
                to_item.item_type != "SOCKET"
                or not isinstance(to_item, NodeTreeInterfaceSocket)
                or to_item.in_out != from_item.in_out
                or to_item.socket_type != from_socket_type
            ):
                to_node_tree.interface.remove(to_item)
                continue
            if to_item.name != from_item.name:
                to_item.name = from_item.name
            if to_item.description != from_item.description:
                to_item.description = from_item.description
            to_socket = to_item
            break

        if to_socket is None:
            to_socket = to_node_tree.interface.new_socket(
                from_item.name,
                description=from_item.description,
                in_out=from_item.in_out,
                socket_type=from_socket_type,
            )

        copy_node_tree_interface_socket(from_item, to_socket)
        to_items_index += 1

    while len(to_node_tree.interface.items_tree) > to_items_index:
        to_node_tree.interface.remove(
            list(to_node_tree.interface.items_tree.values())[-1]
        )


def copy_node_tree(from_node_tree: NodeTree, to_node_tree: NodeTree) -> None:
    clear_node_tree(to_node_tree, clear_inputs_outputs=False)

    if bpy.app.version < (4, 0):
        copy_node_tree_inputs_outputs(from_node_tree, to_node_tree)
    else:
        copy_node_tree_interface(from_node_tree, to_node_tree)

    from_to: dict[Node, Node] = {}

    for from_node in from_node_tree.nodes:
        to_node = to_node_tree.nodes.new(from_node.bl_idname)
        from_to[from_node] = to_node

    for from_node, to_node in from_to.items():
        copy_node(from_node, to_node, from_to)

    for from_link in from_node_tree.links:
        if not from_link.is_valid:
            continue

        input_socket_index = next(
            (
                i
                for i, s in enumerate(from_link.to_node.inputs)
                if s == from_link.to_socket
            ),
            None,
        )
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

        output_socket_index = next(
            (
                i
                for i, s in enumerate(from_link.from_node.outputs)
                if s == from_link.from_socket
            ),
            None,
        )
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

    # 親子関係の辻褄が合った状態でもう一度場所を設定することで
    # 完全にノードの位置を復元できる
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
    shader_node: Node, input_socket_name: str
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

    if not isinstance(from_node, ShaderNodeTexImage):
        return None

    image = from_node.image
    if not image:
        return None

    image_name = image.name
    if not image_name:
        return None

    # blender is ('Linear', 'Closest', 'Cubic', 'Smart')
    # glTF is Linear, Closest
    filter_type = GL_NEAREST if from_node.interpolation == "Closest" else GL_LINEAR

    # blender is ('REPEAT', 'EXTEND', 'CLIP')
    # glTF is CLAMP_TO_EDGE, MIRRORED_REPEAT, REPEAT
    wrap_type = GL_REPEAT if from_node.extension == "REPEAT" else GL_CLAMP_TO_EDGE

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
    shader_node: Node,
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
    shader_node: Node,
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
    shader_node: Node,
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
