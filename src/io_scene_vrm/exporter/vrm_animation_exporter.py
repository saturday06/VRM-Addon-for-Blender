import itertools
import struct
from os import environ
from pathlib import Path
from typing import Optional

import bpy
from bpy.types import Armature, Context, Object, PoseBone
from mathutils import Euler, Matrix, Quaternion, Vector

from ..common import version
from ..common.deep import Json, make_json
from ..common.gl import GL_FLOAT
from ..common.gltf import pack_glb
from ..common.logging import get_logger
from ..common.vrm1.human_bone import (
    HumanBoneName,
    HumanBoneSpecification,
    HumanBoneSpecifications,
)
from ..common.workspace import save_workspace

logger = get_logger(__name__)


class VrmAnimationExporter:
    @staticmethod
    def execute(context: Context, path: Path, armature: Object) -> set[str]:
        return work_in_progress(context, path, armature)


def connect_humanoid_node_dicts(
    human_bone_specification: HumanBoneSpecification,
    human_bone_name_to_node_dict: dict[HumanBoneName, dict[str, Json]],
    parent_node_dict: Optional[dict[str, Json]],
    node_dicts: list[dict[str, Json]],
    human_bone_name_to_node_index: dict[HumanBoneName, int],
) -> None:
    current_node_dict = human_bone_name_to_node_dict.get(human_bone_specification.name)
    if isinstance(current_node_dict, dict):
        node_index = len(node_dicts)
        human_bone_name_to_node_index[human_bone_specification.name] = node_index
        node_dicts.append(current_node_dict)
        if parent_node_dict is not None:
            children = parent_node_dict.get("children")
            if not isinstance(children, list):
                children = []
                parent_node_dict["children"] = children
            children.append(node_index)
        parent_node_dict = current_node_dict
    for child in human_bone_specification.children():
        connect_humanoid_node_dicts(
            child,
            human_bone_name_to_node_dict,
            parent_node_dict,
            node_dicts,
            human_bone_name_to_node_index,
        )


def work_in_progress_2(context: Context, armature: Object) -> bytes:
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        message = "Armature data is not an Armature"
        raise TypeError(message)
    vrm1 = armature_data.vrm_addon_extension.vrm1
    human_bone_name_to_node_dict: dict[HumanBoneName, dict[str, Json]] = {}
    human_bone_name_to_node_index: dict[HumanBoneName, int] = {}
    human_bone_name_to_human_bone = (
        vrm1.humanoid.human_bones.human_bone_name_to_human_bone()
    )
    bone_name_to_parent_bone_name_without_non_human_bone: dict[str, str] = {}
    bone_name_to_base_quaternion: dict[str, Quaternion] = {}

    data_path_to_bone_and_property_name: dict[str, tuple[PoseBone, str]] = {}
    frame_to_timestamp_factor = context.scene.render.fps_base / float(
        context.scene.render.fps
    )

    for human_bone_name, human_bone in human_bone_name_to_human_bone.items():
        if human_bone_name in [HumanBoneName.LEFT_EYE, HumanBoneName.RIGHT_EYE]:
            continue
        # 現在注目しているヒューマンボーンに対応するポーズボーンを探す
        human_bone_specification = HumanBoneSpecifications.get(human_bone_name)
        bone = armature.pose.bones.get(human_bone.node.bone_name)
        if not bone:
            continue

        if bone.rotation_mode == "QUATERNION":
            data_path_to_bone_and_property_name[
                bone.path_from_id("rotation_quaternion")
            ] = (bone, "rotation_quaternion")
        elif bone.rotation_mode == "AXIS_ANGLE":
            data_path_to_bone_and_property_name[
                bone.path_from_id("rotation_axis_angle")
            ] = (bone, "rotation_axis_angle")
        elif bone.rotation_mode in ["XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX"]:
            data_path_to_bone_and_property_name[bone.path_from_id("rotation_euler")] = (
                bone,
                "rotation_euler",
            )
        else:
            logger.error(
                f"Unexpected rotation mode for bone {bone.name}: {bone.rotation_mode}"
            )

        if human_bone_name == HumanBoneName.HIPS:
            data_path_to_bone_and_property_name[bone.path_from_id("location")] = (
                bone,
                "location",
            )

        # 親ヒューマンボーンに対応するポーズボーンを探す。
        # 親がいない場合は再帰的に祖先を探す
        parent_bone = None
        parent_human_bone_specification = human_bone_specification
        while True:
            parent_human_bone_specification_or_none = (
                parent_human_bone_specification.parent()
            )
            if not parent_human_bone_specification_or_none:
                break
            parent_human_bone_specification = parent_human_bone_specification_or_none
            parent_human_bone = human_bone_name_to_human_bone.get(
                parent_human_bone_specification.name
            )
            if not parent_human_bone:
                continue
            parent_bone = armature.pose.bones.get(parent_human_bone.node.bone_name)
            if parent_bone:
                break
        if parent_bone:
            bone_name_to_parent_bone_name_without_non_human_bone[parent_bone.name] = (
                bone.name
            )
            matrix = parent_bone.matrix.inverted_safe() @ bone.matrix
        else:
            matrix = bone.matrix

        # 親ヒューマンボーンに対する相対回転を保存する。ただしスケールは保存しない
        # "children" は後で付与する
        translation = matrix.to_translation()
        rotation = matrix.to_quaternion()
        bone_name_to_base_quaternion[bone.name] = rotation.copy()
        human_bone_name_to_node_dict[human_bone_name] = {
            "name": human_bone_specification.name.value,
            "translation": [
                translation.x,
                translation.z,
                -translation.y,
            ],
            "rotation": [
                rotation.x,
                rotation.z,
                -rotation.y,
                rotation.w,
            ],
        }

    node_dicts: list[dict[str, Json]] = []
    connect_humanoid_node_dicts(
        HumanBoneSpecifications.HIPS,
        human_bone_name_to_node_dict,
        None,
        node_dicts,
        human_bone_name_to_node_index,
    )
    human_bones_dict: dict[str, Json] = {
        human_bone_name.value: {"node": node_index}
        for human_bone_name, node_index in human_bone_name_to_node_index.items()
    }

    buffer0_bytearray = bytearray()
    accessor_dicts: list[dict[str, Json]] = []
    buffer_view_dicts: list[dict[str, Json]] = []
    animation_sampler_dicts: list[dict[str, Json]] = []
    animation_channel_dicts: list[dict[str, Json]] = []
    preset_expression_dict: dict[str, dict[str, Json]] = {}
    custom_expression_dict: dict[str, dict[str, Json]] = {}

    scene_node_indices: list[int] = [human_bone_name_to_node_index[HumanBoneName.HIPS]]

    frame_start = context.scene.frame_start
    frame_end = context.scene.frame_end

    expression_animation_data = armature_data.animation_data
    if expression_animation_data and expression_animation_data.action:
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

        action = expression_animation_data.action
        expression_export_index = 0
        for fcurve in action.fcurves:
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
            while (
                len(buffer0_bytearray) % 32 != 0
            ):  # TODO: 正しいアラインメントを調べる
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
            while (
                len(buffer0_bytearray) % 32 != 0
            ):  # TODO: 正しいアラインメントを調べる
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

    if armature.animation_data and armature.animation_data.action:
        bone_name_to_quaternion_offsets: dict[str, list[Quaternion]] = {}
        bone_name_to_euler_offsets: dict[str, list[Euler]] = {}
        bone_name_to_axis_angle_offsets: dict[str, list[list[float]]] = {}
        hips_translation_offsets: list[Vector] = []
        action = armature.animation_data.action
        for fcurve in action.fcurves:
            if fcurve.mute:
                continue
            if not fcurve.is_valid:
                continue

            bone_and_property_name = data_path_to_bone_and_property_name.get(
                fcurve.data_path
            )
            if not bone_and_property_name:
                continue
            bone, property_name = bone_and_property_name
            for frame in range(frame_start, frame_end + 1):
                offset = frame - frame_start
                value = float(fcurve.evaluate(frame))
                if property_name == "rotation_quaternion":
                    quaternion_offsets = bone_name_to_quaternion_offsets.get(bone.name)
                    if quaternion_offsets is None:
                        quaternion_offsets = []
                        bone_name_to_quaternion_offsets[bone.name] = quaternion_offsets
                    if offset < len(quaternion_offsets):
                        quaternion_offset = quaternion_offsets[offset]
                    else:
                        quaternion_offset = Quaternion()
                        quaternion_offsets.append(quaternion_offset)
                    quaternion_offset[fcurve.array_index] = value
                elif property_name == "rotation_axis_angle":
                    axis_angle_offsets = bone_name_to_axis_angle_offsets.get(bone.name)
                    if axis_angle_offsets is None:
                        axis_angle_offsets = []
                        bone_name_to_axis_angle_offsets[bone.name] = axis_angle_offsets
                    if offset < len(axis_angle_offsets):
                        axis_angle_offset = axis_angle_offsets[offset]
                    else:
                        axis_angle_offset = [0.0, 0.0, 0.0, 0.0]
                        axis_angle_offsets.append(axis_angle_offset)
                    axis_angle_offset[fcurve.array_index] = value
                elif property_name == "rotation_euler":
                    euler_offsets = bone_name_to_euler_offsets.get(bone.name)
                    if euler_offsets is None:
                        euler_offsets = []
                        bone_name_to_euler_offsets[bone.name] = euler_offsets
                    if offset < len(euler_offsets):
                        euler_offset = euler_offsets[offset]
                    else:
                        euler_offset = Euler((0, 0, 0))
                        euler_offsets.append(euler_offset)
                    indices = {
                        "XYZ": [0, 1, 2],
                        "XZY": [0, 2, 1],
                        "YXZ": [1, 0, 2],
                        "YZX": [1, 2, 0],
                        "ZXY": [2, 0, 1],
                        "ZYX": [2, 1, 0],
                    }
                    index = indices.get(bone.rotation_mode)
                    if index is None:
                        continue
                    euler_offset[index[fcurve.array_index]] = value
                elif property_name == "location":
                    if offset < len(hips_translation_offsets):
                        translation_offset = hips_translation_offsets[offset]
                    else:
                        translation_offset = Vector((0.0, 0.0, 0.0))
                        hips_translation_offsets.append(translation_offset)
                    translation_offset[fcurve.array_index] = value

        bone_name_to_quaternions: dict[str, list[Quaternion]] = {}
        for bone_name, quaternion_offsets in bone_name_to_quaternion_offsets.items():
            base_quaternion = bone_name_to_base_quaternion.get(bone_name)
            if base_quaternion is None:
                continue
            bone_name_to_quaternions[bone_name] = [
                # ミュートされている項目とかあるとクオータニオンの値がノーマライズされて
                # いないのでノーマライズしておく
                base_quaternion @ quaternion_offset.normalized()
                for quaternion_offset in quaternion_offsets
            ]
        for bone_name, euler_offsets in bone_name_to_euler_offsets.items():
            base_quaternion = bone_name_to_base_quaternion.get(bone_name)
            if base_quaternion is None:
                continue
            bone_name_to_quaternions[bone_name] = [
                base_quaternion @ euler.to_quaternion() for euler in euler_offsets
            ]
        for bone_name, axis_angle_offsets in bone_name_to_axis_angle_offsets.items():
            base_quaternion = bone_name_to_base_quaternion.get(bone_name)
            if base_quaternion is None:
                continue
            bone_name_to_quaternions[bone_name] = [
                base_quaternion
                @ Quaternion(
                    (axis_angle_offset[0], axis_angle_offset[1], axis_angle_offset[2]),
                    axis_angle_offset[3],
                ).normalized()
                for axis_angle_offset in axis_angle_offsets
            ]

        # hipsの位置をアーマチュアオブジェクトの原点からの相対座標に変換
        hips_bone = armature.pose.bones[
            human_bone_name_to_human_bone[HumanBoneName.HIPS].node.bone_name
        ]
        hips_translations = [
            hips_bone.matrix @ hips_translation_offset
            for hips_translation_offset in hips_translation_offsets
        ]

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
                logger.error(f"Failed to find human bone name for bone {bone_name}")
                continue
            if human_bone_name in [HumanBoneName.RIGHT_EYE, HumanBoneName.LEFT_EYE]:
                continue
            human_bone_node_index = human_bone_name_to_node_index.get(human_bone_name)
            if not isinstance(human_bone_node_index, int):
                logger.error(f"Failed to find node index for bone {bone_name}")
                continue

            input_byte_offset = len(buffer0_bytearray)
            input_floats = [
                frame * frame_to_timestamp_factor for frame, _ in enumerate(quaternions)
            ]
            input_bytes = struct.pack("<" + "f" * len(input_floats), *input_floats)
            buffer0_bytearray.extend(input_bytes)
            while (
                len(buffer0_bytearray) % 32 != 0
            ):  # TODO: 正しいアラインメントを調べる
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
            while (
                len(buffer0_bytearray) % 32 != 0
            ):  # TODO: 正しいアラインメントを調べる
                buffer0_bytearray.append(0)
            output_buffer_view_index = len(buffer_view_dicts)
            output_buffer_view_dict = {
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
                    "target": {"node": human_bone_node_index, "path": "rotation"},
                }
            )

        # hipsの平行移動のエクスポート
        if hips_translations:
            human_bone_node_index = human_bone_name_to_node_index[HumanBoneName.HIPS]

            input_byte_offset = len(buffer0_bytearray)
            input_floats = [
                frame * frame_to_timestamp_factor
                for frame, _ in enumerate(hips_translations)
            ]
            input_bytes = struct.pack("<" + "f" * len(input_floats), *input_floats)
            buffer0_bytearray.extend(input_bytes)
            while (
                len(buffer0_bytearray) % 32 != 0
            ):  # TODO: 正しいアラインメントを調べる
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
            while (
                len(buffer0_bytearray) % 32 != 0
            ):  # TODO: 正しいアラインメントを調べる
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
                    "target": {"node": human_bone_node_index, "path": "translation"},
                }
            )

    look_at_target_node_index: Optional[int] = None
    look_at_target_object = vrm1.look_at.preview_target_bpy_object
    if (
        look_at_target_object
        and look_at_target_object.animation_data
        and look_at_target_object.animation_data.action
    ):
        look_at_translation_offsets: list[Vector] = []
        action = look_at_target_object.animation_data.action
        data_path = look_at_target_object.path_from_id("location")
        for fcurve in action.fcurves:
            if fcurve.mute:
                continue
            if not fcurve.is_valid:
                continue
            if fcurve.data_path != data_path:
                continue
            for frame in range(frame_start, frame_end + 1):
                offset = frame - frame_start
                value = float(fcurve.evaluate(frame))
                if offset < len(look_at_translation_offsets):
                    translation_offset = look_at_translation_offsets[offset]
                else:
                    translation_offset = Vector((0.0, 0.0, 0.0))
                    look_at_translation_offsets.append(translation_offset)
                translation_offset[fcurve.array_index] = value

        look_at_default_node_translation, look_at_rotation, look_at_scale = (
            look_at_target_object.matrix_world.decompose()
        )
        look_at_rotation_and_scale_matrix = (
            look_at_rotation.to_matrix().to_4x4()
            @ Matrix.Diagonal(look_at_scale).to_4x4()
        )
        look_at_translations = [
            look_at_translation_offset @ look_at_rotation_and_scale_matrix
            for look_at_translation_offset in look_at_translation_offsets
        ]
        if look_at_translations:
            look_at_target_node_index = len(node_dicts)
            node_dicts.append(
                {
                    "name": look_at_target_object.name,
                    "translation": [
                        look_at_default_node_translation.x,
                        look_at_default_node_translation.z,
                        -look_at_default_node_translation.y,
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
            while (
                len(buffer0_bytearray) % 32 != 0
            ):  # TODO: 正しいアラインメントを調べる
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
                for translation in look_at_translations
            ]
            translation_floats = list(itertools.chain(*gltf_translations))
            translation_bytes = struct.pack(
                "<" + "f" * len(translation_floats), *translation_floats
            )
            buffer0_bytearray.extend(translation_bytes)
            while (
                len(buffer0_bytearray) % 32 != 0
            ):  # TODO: 正しいアラインメントを調べる
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

    buffer_dicts: list[dict[str, Json]] = [{"byteLength": len(buffer0_bytearray)}]

    addon_version = version.addon_version()
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
        message = "vrma_dict is not dict"
        raise TypeError(message)

    return pack_glb(vrma_dict, buffer0_bytearray)


def work_in_progress(context: Context, path: Path, armature: Object) -> set[str]:
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return {"CANCELLED"}
    humanoid = armature_data.vrm_addon_extension.vrm1.humanoid
    if not humanoid.human_bones.all_required_bones_are_assigned():
        return {"CANCELLED"}

    # saved_current_pose_matrix_basis_dict = {}
    # saved_current_pose_matrix_dict = {}
    saved_pose_position = armature_data.pose_position
    # vrm1 = armature.data.vrm_addon_extension.vrm1
    output_bytes = None

    # TODO: 現状restがTポーズの時しか動作しない
    # TODO: 自動でTポーズを作成する
    # TODO: Tポーズ取得処理、共通化
    with save_workspace(context, armature):
        try:
            bpy.ops.object.select_all(action="DESELECT")
            bpy.ops.object.mode_set(mode="POSE")

            armature_data.pose_position = "POSE"

            # t_pose_action = vrm1.humanoid.pose_library
            # t_pose_pose_marker_name = vrm1.humanoid.pose_marker_name
            # pose_marker_frame = 0
            # if t_pose_pose_marker_name:
            #     for search_pose_marker in t_pose_action.pose_markers.values():
            #         if search_pose_marker.name == t_pose_pose_marker_name:
            #             pose_marker_frame = search_pose_marker.frame
            #             break
            #
            # context.view_layer.update()
            # saved_current_pose_matrix_basis_dict = {
            #     bone.name: bone.matrix_basis.copy() for bone in armature.pose.bones
            # }
            # saved_current_pose_matrix_dict = {
            #     bone.name: bone.matrix.copy() for bone in armature.pose.bones
            # }

            # if t_pose_action:
            #     armature.pose.apply_pose_from_action(
            #         t_pose_action, evaluation_time=pose_marker_frame
            #     )
            # else:

            # TODO: ここのロジックはちゃんと考える
            armature_data.pose_position = "REST"

            context.view_layer.update()

            output_bytes = work_in_progress_2(context, armature)
        finally:
            # TODO: リストア処理、共通化
            if armature_data.pose_position != saved_pose_position:
                armature_data.pose_position = saved_pose_position

        # bones = [bone for bone in armature.pose.bones if not bone.parent]
        # while bones:
        #     bone = bones.pop()
        #     matrix_basis = saved_current_pose_matrix_basis_dict.get(bone.name)
        #     if matrix_basis is not None:
        #         bone.matrix_basis = matrix_basis
        #     bones.extend(bone.children)
        # context.view_layer.update()
        #
        # bones = [bone for bone in armature.pose.bones if not bone.parent]
        # while bones:
        #     bone = bones.pop()
        #     matrix = saved_current_pose_matrix_dict.get(bone.name)
        #     if matrix is not None:
        #         bone.matrix = matrix
        #     bones.extend(bone.children)

    path.write_bytes(output_bytes)
    return {"FINISHED"}
