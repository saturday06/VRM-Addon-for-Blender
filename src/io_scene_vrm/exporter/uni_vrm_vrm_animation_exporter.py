# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import itertools
import struct
from os import environ
from pathlib import Path
from typing import Optional

from bpy.types import (
    Armature,
    Context,
    Object,
    PoseBone,
)
from mathutils import Quaternion, Vector

from ..common import version
from ..common.convert import Json
from ..common.deep import make_json
from ..common.gl import GL_FLOAT
from ..common.gltf import pack_glb
from ..common.logger import get_logger
from ..common.rotation import (
    ROTATION_MODE_AXIS_ANGLE,
    ROTATION_MODE_EULER,
    ROTATION_MODE_QUATERNION,
    get_rotation_as_quaternion,
)
from ..common.vrm1.human_bone import HumanBoneName
from ..common.workspace import save_workspace
from ..editor.extension import get_armature_extension
from ..editor.t_pose import setup_humanoid_t_pose
from ..editor.vrm1.property_group import Vrm1PropertyGroup
from .vrm_animation_exporter import get_action_fcurves

logger = get_logger(__name__)


class UniVrmVrmAnimationExporter:
    """Export VRM animation. The export result is the same as UniVRM.

    https://github.com/vrm-c/UniVRM
    """

    @staticmethod
    def execute(context: Context, path: Path, armature: Object) -> set[str]:
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}

        with (
            setup_humanoid_t_pose(context, armature),
            save_workspace(context, armature, mode="POSE"),
        ):
            output_bytes = export_vrm_animation(context, armature)

        path.write_bytes(output_bytes)
        return {"FINISHED"}


def create_node_dicts(
    bone: PoseBone,
    parent_bone: Optional[PoseBone],
    node_dicts: list[dict[str, Json]],
    bone_name_to_node_index: dict[str, int],
) -> int:
    node_index = len(node_dicts)
    node_dict: dict[str, Json] = {"name": bone.name}
    node_dicts.append(node_dict)
    bone_name_to_node_index[bone.name] = node_index

    matrix = parent_bone.matrix.inverted() @ bone.matrix if parent_bone else bone.matrix
    translation = matrix.to_translation()
    rotation = matrix.to_quaternion()
    node_dict["translation"] = [
        translation.x,
        translation.z,
        -translation.y,
    ]
    node_dict["rotation"] = [
        rotation.x,
        rotation.z,
        -rotation.y,
        rotation.w,
    ]
    children = [
        create_node_dicts(child_bone, bone, node_dicts, bone_name_to_node_index)
        for child_bone in bone.children
    ]
    if children:
        node_dict["children"] = make_json(children)

    return node_index


def export_vrm_animation(context: Context, armature: Object) -> bytes:
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        message = "Armature data is not an Armature"
        raise TypeError(message)
    vrm1 = get_armature_extension(armature_data).vrm1
    human_bones = vrm1.humanoid.human_bones

    node_dicts: list[dict[str, Json]] = []
    bone_name_to_node_index: dict[str, int] = {}
    bone_name_to_base_quaternion: dict[str, Quaternion] = {}
    scene_node_indices: list[int] = [0]
    data_path_to_bone_and_property_name: dict[str, tuple[PoseBone, str]] = {}
    root_node_translation = armature.matrix_world.to_translation()
    root_node_rotation = armature.matrix_world.to_quaternion()
    root_node_scale = armature.matrix_world.to_scale()
    root_node_dict: dict[str, Json] = {
        "name": armature.name,
        "translation": [
            root_node_translation.x,
            root_node_translation.z,
            -root_node_translation.y,
        ],
        "rotation": [
            root_node_rotation.x,
            root_node_rotation.z,
            -root_node_rotation.y,
            root_node_rotation.w,
        ],
        "scale": [
            root_node_scale.x,
            root_node_scale.z,
            root_node_scale.y,
        ],
    }
    root_node_child_indices: list[int] = []
    node_dicts.append(root_node_dict)
    for bone in armature.pose.bones:
        if not bone.parent:
            root_node_child_indices.append(
                create_node_dicts(
                    bone,
                    None,
                    node_dicts,
                    bone_name_to_node_index,
                )
            )

        base_quaternion: Optional[Quaternion] = None
        if bone.parent:
            base_quaternion = (
                bone.parent.matrix.inverted_safe() @ bone.matrix
            ).to_quaternion()
        else:
            base_quaternion = bone.matrix.to_quaternion()
        bone_name_to_base_quaternion[bone.name] = (
            base_quaternion @ get_rotation_as_quaternion(bone).inverted()
        )

        if bone.rotation_mode == ROTATION_MODE_QUATERNION:
            data_path_to_bone_and_property_name[
                bone.path_from_id("rotation_quaternion")
            ] = (bone, "rotation_quaternion")
        elif bone.rotation_mode == ROTATION_MODE_AXIS_ANGLE:
            data_path_to_bone_and_property_name[
                bone.path_from_id("rotation_axis_angle")
            ] = (bone, "rotation_axis_angle")
        elif bone.rotation_mode in ROTATION_MODE_EULER:
            data_path_to_bone_and_property_name[bone.path_from_id("rotation_euler")] = (
                bone,
                "rotation_euler",
            )
        else:
            logger.error(
                "Unexpected rotation mode for bone %s: %s",
                bone.name,
                bone.rotation_mode,
            )

        if human_bones.hips.node.bone_name == bone.name:
            data_path_to_bone_and_property_name[bone.path_from_id("location")] = (
                bone,
                "location",
            )

    if root_node_child_indices:
        root_node_dict["children"] = make_json(root_node_child_indices)

    frame_to_timestamp_factor = context.scene.render.fps_base / float(
        context.scene.render.fps
    )

    buffer0_bytearray = bytearray()
    accessor_dicts: list[dict[str, Json]] = []
    buffer_view_dicts: list[dict[str, Json]] = []
    animation_sampler_dicts: list[dict[str, Json]] = []
    animation_channel_dicts: list[dict[str, Json]] = []
    preset_expression_dict: dict[str, dict[str, Json]] = {}
    custom_expression_dict: dict[str, dict[str, Json]] = {}

    frame_start = context.scene.frame_start
    frame_end = context.scene.frame_end

    create_expression_animation(
        context,
        vrm1,
        frame_start=frame_start,
        frame_end=frame_end,
        frame_to_timestamp_factor=frame_to_timestamp_factor,
        armature_data=armature_data,
        node_dicts=node_dicts,
        accessor_dicts=accessor_dicts,
        buffer_view_dicts=buffer_view_dicts,
        animation_channel_dicts=animation_channel_dicts,
        animation_sampler_dicts=animation_sampler_dicts,
        scene_node_indices=scene_node_indices,
        buffer0_bytearray=buffer0_bytearray,
        preset_expression_dict=preset_expression_dict,
        custom_expression_dict=custom_expression_dict,
    )

    create_node_animation(
        context,
        vrm1,
        frame_start=frame_start,
        frame_end=frame_end,
        frame_to_timestamp_factor=frame_to_timestamp_factor,
        armature=armature,
        bone_name_to_node_index=bone_name_to_node_index,
        buffer0_bytearray=buffer0_bytearray,
        buffer_view_dicts=buffer_view_dicts,
        accessor_dicts=accessor_dicts,
        animation_channel_dicts=animation_channel_dicts,
        animation_sampler_dicts=animation_sampler_dicts,
    )

    look_at_target_node_index = create_look_at_animation(
        context,
        vrm1,
        frame_start=frame_start,
        frame_end=frame_end,
        frame_to_timestamp_factor=frame_to_timestamp_factor,
        node_dicts=node_dicts,
        accessor_dicts=accessor_dicts,
        buffer_view_dicts=buffer_view_dicts,
        animation_channel_dicts=animation_channel_dicts,
        animation_sampler_dicts=animation_sampler_dicts,
        buffer0_bytearray=buffer0_bytearray,
    )

    buffer_dicts: list[dict[str, Json]] = [{"byteLength": len(buffer0_bytearray)}]

    human_bones_dict: dict[str, Json] = {}
    human_bone_name_to_human_bone = human_bones.human_bone_name_to_human_bone()
    for human_bone_name, human_bone in human_bone_name_to_human_bone.items():
        bone_name = human_bone.node.bone_name
        node_index = bone_name_to_node_index.get(bone_name)
        if not isinstance(node_index, int):
            continue
        human_bones_dict[human_bone_name.value] = {"node": node_index}

    addon_version = version.get_addon_version()
    if environ.get("BLENDER_VRM_USE_TEST_EXPORTER_VERSION") == "true":
        addon_version = (999, 999, 999)

    vrmc_vrm_animation_dict: dict[str, Json] = {
        "specVersion": "1.0",
        "humanoid": {
            "humanBones": human_bones_dict,
        },
        "expressions": make_json(
            {
                "preset": preset_expression_dict,
                "custom": custom_expression_dict,
            }
        ),
    }
    if look_at_target_node_index is not None:
        vrmc_vrm_animation_dict["lookAt"] = {
            "node": look_at_target_node_index,
            "offsetFromHeadBone": list(vrm1.look_at.offset_from_head_bone),
        }

    vrma_dict = make_json(
        {
            "asset": {
                "version": "2.0",
                "generator": "VRM Add-on for Blender v"
                + ".".join(map(str, addon_version)),
            },
            "nodes": node_dicts,
            "scenes": [{"nodes": scene_node_indices}],
            "buffers": buffer_dicts,
            "bufferViews": buffer_view_dicts,
            "accessors": accessor_dicts,
            "animations": [
                {
                    "channels": animation_channel_dicts,
                    "samplers": animation_sampler_dicts,
                }
            ],
            "extensionsUsed": ["VRMC_vrm_animation"],
            "extensions": {
                "VRMC_vrm_animation": vrmc_vrm_animation_dict,
            },
        }
    )

    if not isinstance(vrma_dict, dict):
        message = "vrma_dict is not a dict"
        raise TypeError(message)

    return pack_glb(vrma_dict, buffer0_bytearray)


def create_look_at_animation(
    context: Context,
    vrm1: Vrm1PropertyGroup,
    *,
    frame_start: int,
    frame_end: int,
    frame_to_timestamp_factor: float,
    node_dicts: list[dict[str, Json]],
    accessor_dicts: list[dict[str, Json]],
    buffer_view_dicts: list[dict[str, Json]],
    animation_channel_dicts: list[dict[str, Json]],
    animation_sampler_dicts: list[dict[str, Json]],
    buffer0_bytearray: bytearray,
) -> Optional[int]:
    look_at_target_object = vrm1.look_at.preview_target_bpy_object
    if not look_at_target_object:
        return None

    look_at_translations: list[Vector] = []
    for frame in range(frame_start, frame_end + 1):
        context.scene.frame_set(frame)
        look_at_translations.append(look_at_target_object.matrix_world.to_translation())

    if not look_at_translations:
        return None

    look_at_target_node_index = len(node_dicts)
    node_dicts.append(
        {
            "name": look_at_target_object.name,
            "translation": [
                look_at_translations[0].x,
                look_at_translations[0].z,
                -look_at_translations[0].y,
            ],
        }
    )

    input_byte_offset = len(buffer0_bytearray)
    input_floats = [
        frame * frame_to_timestamp_factor
        for frame, _ in enumerate(look_at_translations)
    ]
    input_bytes = struct.pack("<" + "f" * len(input_floats), *input_floats)
    buffer0_bytearray.extend(input_bytes)
    while len(buffer0_bytearray) % 32 != 0:  # TODO: 正しいアラインメントを調べる
        buffer0_bytearray.append(0)
    input_buffer_view_index = len(buffer_view_dicts)
    input_buffer_view_dict: dict[str, Json] = {
        "buffer": 0,
        "byteLength": len(input_bytes),
    }
    if input_byte_offset > 0:
        input_buffer_view_dict["byteOffset"] = input_byte_offset
    buffer_view_dicts.append(input_buffer_view_dict)

    output_byte_offset = len(buffer0_bytearray)
    gltf_translations = [
        (
            translation.x,
            translation.z,
            -translation.y,
        )
        for translation in look_at_translations
    ]
    translation_floats = list(itertools.chain(*gltf_translations))
    translation_bytes = struct.pack(
        "<" + "f" * len(translation_floats), *translation_floats
    )
    buffer0_bytearray.extend(translation_bytes)
    while len(buffer0_bytearray) % 32 != 0:  # TODO: 正しいアラインメントを調べる
        buffer0_bytearray.append(0)
    output_buffer_view_index = len(buffer_view_dicts)
    output_buffer_view_dict: dict[str, Json] = {
        "buffer": 0,
        "byteLength": len(translation_bytes),
    }
    if output_byte_offset > 0:
        output_buffer_view_dict["byteOffset"] = output_byte_offset
    buffer_view_dicts.append(output_buffer_view_dict)

    input_accessor_index = len(accessor_dicts)
    accessor_dicts.append(
        {
            "bufferView": input_buffer_view_index,
            "componentType": GL_FLOAT,
            "count": len(input_floats),
            "type": "SCALAR",
            "min": [min(input_floats)],
            "max": [max(input_floats)],
        }
    )

    output_accessor_index = len(accessor_dicts)
    gltf_translation_x_values = [t[0] for t in gltf_translations]
    gltf_translation_y_values = [t[1] for t in gltf_translations]
    gltf_translation_z_values = [t[2] for t in gltf_translations]
    accessor_dicts.append(
        {
            "bufferView": output_buffer_view_index,
            "componentType": GL_FLOAT,
            "count": len(look_at_translations),
            "type": "VEC3",
            "min": [
                min(gltf_translation_x_values),
                min(gltf_translation_y_values),
                min(gltf_translation_z_values),
            ],
            "max": [
                max(gltf_translation_x_values),
                max(gltf_translation_y_values),
                max(gltf_translation_z_values),
            ],
        }
    )

    animation_sampler_index = len(animation_sampler_dicts)
    animation_sampler_dicts.append(
        {
            "input": input_accessor_index,
            "output": output_accessor_index,
        }
    )
    animation_channel_dicts.append(
        {
            "sampler": animation_sampler_index,
            "target": {
                "node": look_at_target_node_index,
                "path": "translation",
            },
        }
    )

    return None


def create_expression_animation(
    _context: Context,
    vrm1: Vrm1PropertyGroup,
    *,
    frame_start: int,
    frame_end: int,
    frame_to_timestamp_factor: float,
    armature_data: Armature,
    node_dicts: list[dict[str, Json]],
    accessor_dicts: list[dict[str, Json]],
    buffer_view_dicts: list[dict[str, Json]],
    animation_channel_dicts: list[dict[str, Json]],
    animation_sampler_dicts: list[dict[str, Json]],
    scene_node_indices: list[int],
    buffer0_bytearray: bytearray,
    preset_expression_dict: dict[str, dict[str, Json]],
    custom_expression_dict: dict[str, dict[str, Json]],
) -> None:
    expression_animation_data = armature_data.animation_data
    if not expression_animation_data:
        return

    action = expression_animation_data.action
    if not action:
        return

    data_path_to_expression_name: dict[str, str] = {}
    for (
        expression_name,
        expression,
    ) in vrm1.expressions.all_name_to_expression_dict().items():
        if expression_name in [
            "lookUp",
            "lookDown",
            "lookLeft",
            "lookRight",
        ]:
            continue
        data_path_to_expression_name[expression.path_from_id("preview")] = (
            expression.name
        )

    expression_name_to_expression_values: dict[
        str, list[tuple[float, float, float]]
    ] = {}

    expression_export_index = 0
    for fcurve in get_action_fcurves(action):
        if fcurve.mute:
            continue
        if not fcurve.is_valid:
            continue
        expression_name = data_path_to_expression_name.get(fcurve.data_path)
        if not expression_name:
            continue
        for frame in range(frame_start, frame_end + 1):
            expression_values = expression_name_to_expression_values.get(
                expression_name
            )
            if not expression_values:
                expression_values = []
                expression_name_to_expression_values[expression_name] = (
                    expression_values
                )
            expression_values.append(
                (
                    max(0, min(fcurve.evaluate(frame), 1)),
                    0,
                    expression_export_index / 8.0,
                )
            )
        expression_export_index += 1

    node_index: Optional[int] = None
    for (
        expression_name,
        expression_translations,
    ) in expression_name_to_expression_values.items():
        node_index = len(node_dicts)
        node_dicts.append(
            {
                "name": expression_name,
            }
        )

        if expression_name in vrm1.expressions.preset.name_to_expression_dict():
            preset_expression_dict[expression_name] = {
                "node": node_index,
            }
        else:
            custom_expression_dict[expression_name] = {
                "node": node_index,
            }
        scene_node_indices.append(node_index)

        input_byte_offset = len(buffer0_bytearray)
        input_floats = [
            frame * frame_to_timestamp_factor
            for frame, _ in enumerate(expression_translations)
        ]
        input_bytes = struct.pack("<" + "f" * len(input_floats), *input_floats)
        buffer0_bytearray.extend(input_bytes)
        while len(buffer0_bytearray) % 32 != 0:  # TODO: 正しいアラインメントを調べる
            buffer0_bytearray.append(0)
        input_buffer_view_index = len(buffer_view_dicts)
        input_buffer_view_dict: dict[str, Json] = {
            "buffer": 0,
            "byteLength": len(input_bytes),
        }
        if input_byte_offset > 0:
            input_buffer_view_dict["byteOffset"] = input_byte_offset
        buffer_view_dicts.append(input_buffer_view_dict)

        output_byte_offset = len(buffer0_bytearray)
        expression_translation_floats: list[float] = list(
            itertools.chain(*expression_translations)
        )
        translation_bytes = struct.pack(
            "<" + "f" * len(expression_translation_floats),
            *expression_translation_floats,
        )
        buffer0_bytearray.extend(translation_bytes)
        while len(buffer0_bytearray) % 32 != 0:  # TODO: 正しいアラインメントを調べる
            buffer0_bytearray.append(0)
        output_buffer_view_index = len(buffer_view_dicts)
        output_buffer_view_dict: dict[str, Json] = {
            "buffer": 0,
            "byteLength": len(translation_bytes),
        }
        if output_byte_offset > 0:
            output_buffer_view_dict["byteOffset"] = output_byte_offset
        buffer_view_dicts.append(output_buffer_view_dict)

        input_accessor_index = len(accessor_dicts)
        accessor_dicts.append(
            {
                "bufferView": input_buffer_view_index,
                "componentType": GL_FLOAT,
                "count": len(input_floats),
                "type": "SCALAR",
                "min": [min(input_floats)],
                "max": [max(input_floats)],
            }
        )

        output_accessor_index = len(accessor_dicts)
        accessor_dicts.append(
            {
                "bufferView": output_buffer_view_index,
                "componentType": GL_FLOAT,
                "count": len(expression_translations),
                "type": "VEC3",
                "min": [
                    min(values)
                    for values in [
                        [
                            gltf_translation[i]
                            for gltf_translation in expression_translations
                        ]
                        for i in range(3)
                    ]
                ],
                "max": [
                    max(values)
                    for values in [
                        [
                            gltf_translation[i]
                            for gltf_translation in expression_translations
                        ]
                        for i in range(3)
                    ]
                ],
            }
        )

        animation_sampler_index = len(animation_sampler_dicts)
        animation_sampler_dicts.append(
            {
                "input": input_accessor_index,
                "output": output_accessor_index,
            }
        )
        animation_channel_dicts.append(
            {
                "sampler": animation_sampler_index,
                "target": {"node": node_index, "path": "translation"},
            }
        )


def create_node_animation(
    context: Context,
    vrm1: Vrm1PropertyGroup,
    *,
    frame_start: int,
    frame_end: int,
    frame_to_timestamp_factor: float,
    armature: Object,
    bone_name_to_node_index: dict[str, int],
    buffer0_bytearray: bytearray,
    buffer_view_dicts: list[dict[str, Json]],
    accessor_dicts: list[dict[str, Json]],
    animation_channel_dicts: list[dict[str, Json]],
    animation_sampler_dicts: list[dict[str, Json]],
) -> None:
    human_bones = vrm1.humanoid.human_bones
    human_bone_name_to_human_bone = human_bones.human_bone_name_to_human_bone()

    bone_name_to_quaternions: dict[str, list[Quaternion]] = {}
    bone_name_to_translations: dict[str, list[Vector]] = {}
    for frame in range(frame_start, frame_end + 1):
        context.scene.frame_set(frame)
        for bone_name in bone_name_to_node_index.keys():
            bone = armature.pose.bones.get(bone_name)
            if not bone:
                continue
            if bone_name not in bone_name_to_quaternions:
                bone_name_to_quaternions[bone_name] = []
            if bone_name not in bone_name_to_translations:
                bone_name_to_translations[bone_name] = []
            bone_name_to_quaternions[bone_name].append(bone.matrix.to_quaternion())
            bone_name_to_translations[bone_name].append(bone.matrix.to_translation())

    # 回転のエクスポート
    for bone_name, quaternions in bone_name_to_quaternions.items():
        human_bone_name = next(
            (
                n
                for n, human_bone in human_bone_name_to_human_bone.items()
                if human_bone.node.bone_name == bone_name
            ),
            None,
        )
        if human_bone_name is None:
            logger.error("Failed to find human bone name for bone %s", bone_name)
            continue
        if human_bone_name in [HumanBoneName.RIGHT_EYE, HumanBoneName.LEFT_EYE]:
            continue
        node_index = bone_name_to_node_index.get(bone_name)
        if not isinstance(node_index, int):
            logger.error("Failed to find node index for bone %s", bone_name)
            continue

        input_byte_offset = len(buffer0_bytearray)
        input_floats = [
            frame * frame_to_timestamp_factor for frame, _ in enumerate(quaternions)
        ]
        input_bytes = struct.pack("<" + "f" * len(input_floats), *input_floats)
        buffer0_bytearray.extend(input_bytes)
        while len(buffer0_bytearray) % 32 != 0:  # TODO: 正しいアラインメントを調べる
            buffer0_bytearray.append(0)
        input_buffer_view_index = len(buffer_view_dicts)
        input_buffer_view_dict: dict[str, Json] = {
            "buffer": 0,
            "byteLength": len(input_bytes),
        }
        if input_byte_offset > 0:
            input_buffer_view_dict["byteOffset"] = input_byte_offset
        buffer_view_dicts.append(input_buffer_view_dict)

        output_byte_offset = len(buffer0_bytearray)
        gltf_quaternions = [
            (
                quaternion.x,
                quaternion.z,
                -quaternion.y,
                quaternion.w,
            )
            for quaternion in quaternions
        ]
        quaternion_floats: list[float] = list(itertools.chain(*gltf_quaternions))
        quaternion_bytes = struct.pack(
            "<" + "f" * len(quaternion_floats), *quaternion_floats
        )
        buffer0_bytearray.extend(quaternion_bytes)
        while len(buffer0_bytearray) % 32 != 0:  # TODO: 正しいアラインメントを調べる
            buffer0_bytearray.append(0)
        output_buffer_view_index = len(buffer_view_dicts)
        output_buffer_view_dict: dict[str, Json] = {
            "buffer": 0,
            "byteLength": len(quaternion_bytes),
        }
        if output_byte_offset > 0:
            output_buffer_view_dict["byteOffset"] = output_byte_offset
        buffer_view_dicts.append(output_buffer_view_dict)

        input_accessor_index = len(accessor_dicts)
        accessor_dicts.append(
            {
                "bufferView": input_buffer_view_index,
                "componentType": GL_FLOAT,
                "count": len(input_floats),
                "type": "SCALAR",
                "min": [min(input_floats)],
                "max": [max(input_floats)],
            }
        )

        output_accessor_index = len(accessor_dicts)
        accessor_dicts.append(
            {
                "bufferView": output_buffer_view_index,
                "componentType": GL_FLOAT,
                "count": len(quaternions),
                "type": "VEC4",
                "min": [
                    min(values)
                    for values in [
                        [gltf_quaternion[i] for gltf_quaternion in gltf_quaternions]
                        for i in range(4)
                    ]
                ],
                "max": [
                    max(values)
                    for values in [
                        [gltf_quaternion[i] for gltf_quaternion in gltf_quaternions]
                        for i in range(4)
                    ]
                ],
            }
        )

        animation_sampler_index = len(animation_sampler_dicts)
        animation_sampler_dicts.append(
            {
                "input": input_accessor_index,
                "output": output_accessor_index,
            }
        )
        animation_channel_dicts.append(
            {
                "sampler": animation_sampler_index,
                "target": {"node": node_index, "path": "rotation"},
            }
        )

    # hipsの平行移動のエクスポート
    hips_bone_name = human_bones.hips.node.bone_name

    hips_bone = armature.pose.bones.get(hips_bone_name)
    if not hips_bone:
        return

    hips_node_index = bone_name_to_node_index.get(hips_bone_name)
    if not isinstance(hips_node_index, int):
        return

    hips_translations = bone_name_to_translations.get(hips_bone_name, [])

    if not hips_translations:
        return

    input_byte_offset = len(buffer0_bytearray)
    input_floats = [
        frame * frame_to_timestamp_factor for frame, _ in enumerate(hips_translations)
    ]
    input_bytes = struct.pack("<" + "f" * len(input_floats), *input_floats)
    buffer0_bytearray.extend(input_bytes)
    while len(buffer0_bytearray) % 32 != 0:  # TODO: 正しいアラインメントを調べる
        buffer0_bytearray.append(0)
    input_buffer_view_index = len(buffer_view_dicts)
    input_buffer_view_dict = {
        "buffer": 0,
        "byteLength": len(input_bytes),
    }
    if input_byte_offset > 0:
        input_buffer_view_dict["byteOffset"] = input_byte_offset
    buffer_view_dicts.append(input_buffer_view_dict)

    output_byte_offset = len(buffer0_bytearray)
    gltf_translations = [
        (
            translation.x,
            translation.z,
            -translation.y,
        )
        for translation in hips_translations
    ]
    translation_floats: list[float] = list(itertools.chain(*gltf_translations))
    translation_bytes = struct.pack(
        "<" + "f" * len(translation_floats), *translation_floats
    )
    buffer0_bytearray.extend(translation_bytes)
    while len(buffer0_bytearray) % 32 != 0:  # TODO: 正しいアラインメントを調べる
        buffer0_bytearray.append(0)
    output_buffer_view_index = len(buffer_view_dicts)
    output_buffer_view_dict = {
        "buffer": 0,
        "byteLength": len(translation_bytes),
    }
    if output_byte_offset > 0:
        output_buffer_view_dict["byteOffset"] = output_byte_offset
    buffer_view_dicts.append(output_buffer_view_dict)

    input_accessor_index = len(accessor_dicts)
    accessor_dicts.append(
        {
            "bufferView": input_buffer_view_index,
            "componentType": GL_FLOAT,
            "count": len(input_floats),
            "type": "SCALAR",
            "min": [min(input_floats)],
            "max": [max(input_floats)],
        }
    )

    output_accessor_index = len(accessor_dicts)
    gltf_translation_x_values = [t[0] for t in gltf_translations]
    gltf_translation_y_values = [t[1] for t in gltf_translations]
    gltf_translation_z_values = [t[2] for t in gltf_translations]
    accessor_dicts.append(
        {
            "bufferView": output_buffer_view_index,
            "componentType": GL_FLOAT,
            "count": len(hips_translations),
            "type": "VEC3",
            "min": [
                min(gltf_translation_x_values),
                min(gltf_translation_y_values),
                min(gltf_translation_z_values),
            ],
            "max": [
                max(gltf_translation_x_values),
                max(gltf_translation_y_values),
                max(gltf_translation_z_values),
            ],
        }
    )

    animation_sampler_index = len(animation_sampler_dicts)
    animation_sampler_dicts.append(
        {
            "input": input_accessor_index,
            "output": output_accessor_index,
        }
    )
    animation_channel_dicts.append(
        {
            "sampler": animation_sampler_index,
            "target": {"node": hips_node_index, "path": "translation"},
        }
    )
