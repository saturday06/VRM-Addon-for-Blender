import base64
import itertools
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from sys import float_info
from typing import Optional, Union
from urllib.parse import urlparse

import bpy
from bpy.types import Armature, Context, Object
from mathutils import Matrix, Quaternion, Vector

from ..common import convert
from ..common.debug import dump
from ..common.deep import Json
from ..common.gl import (
    GL_BYTE,
    GL_FLOAT,
    GL_INT,
    GL_SHORT,
    GL_UNSIGNED_BYTE,
    GL_UNSIGNED_INT,
    GL_UNSIGNED_SHORT,
)
from ..common.gltf import parse_glb
from ..common.logging import get_logger
from ..common.vrm1.human_bone import HumanBoneName

logger = get_logger(__name__)


@dataclass(frozen=True)
class NodeRestPoseTree:
    node_index: int
    local_matrix: Matrix
    children: tuple["NodeRestPoseTree", ...]
    is_root: bool

    @staticmethod
    def build(
        node_dicts: list[Json],
        node_index: int,
        is_root: bool,
    ) -> list["NodeRestPoseTree"]:
        if not 0 <= node_index < len(node_dicts):
            return []
        node_dict = node_dicts[node_index]
        if not isinstance(node_dict, dict):
            return []

        translation_float3 = convert.float3_or_none(node_dict.get("translation"))
        if translation_float3:
            x, y, z = translation_float3
            translation = Vector((x, -z, y))
        else:
            translation = Vector((0.0, 0.0, 0.0))

        rotation_float4 = convert.float4_or_none(node_dict.get("rotation"))
        if rotation_float4:
            x, y, z, w = rotation_float4
            rotation = Quaternion((w, x, -z, y)).normalized()
        else:
            rotation = Quaternion()

        scale_float3 = convert.float3_or_none(node_dict.get("scale"))
        if scale_float3:
            x, y, z = scale_float3
            scale = Vector((x, z, y))
        else:
            scale = Vector((1, 1, 1))

        local_matrix = (
            Matrix.Translation(translation)
            @ rotation.to_matrix().to_4x4()
            @ Matrix.Diagonal(scale).to_4x4()
        )

        # TODO: 3要素の場合はオイラー角になるか?
        # TODO: Matrixだったら分解する

        child_indices = node_dict.get("children")
        if isinstance(child_indices, list):
            children = tuple(
                itertools.chain(
                    *(
                        NodeRestPoseTree.build(node_dicts, child_index, is_root=False)
                        for child_index in child_indices
                        if isinstance(child_index, int)
                    )
                )
            )
        else:
            children = ()

        return [
            NodeRestPoseTree(
                node_index=node_index,
                local_matrix=local_matrix,
                children=children,
                is_root=is_root,
            )
        ]


class VrmAnimationImporter:
    @staticmethod
    def execute(context: Context, path: Path, armature: Object) -> set[str]:
        return work_in_progress(context, path, armature)


def find_root_node_index(
    node_dicts: list[Json], node_index: int, skip_node_indices: set[int]
) -> int:
    for parent_node_index, node_dict in enumerate(node_dicts):
        if parent_node_index in skip_node_indices:
            continue
        if not isinstance(node_dict, dict):
            continue
        child_node_indices = node_dict.get("children")
        if not isinstance(child_node_indices, list):
            continue
        for child_node_index in child_node_indices:
            if child_node_index in skip_node_indices:
                continue
            if child_node_index != node_index:
                continue
            skip_node_indices.add(node_index)
            return find_root_node_index(
                node_dicts, parent_node_index, skip_node_indices
            )
    return node_index


def read_accessor_as_bytes(
    accessor_dict: dict[str, Json],
    buffer_view_dicts: list[Json],
    buffer_dicts: list[Json],
    buffer0_bytes: bytes,
) -> Optional[bytes]:
    buffer_view_index = accessor_dict.get("bufferView")
    if not isinstance(buffer_view_index, int):
        return None
    if not 0 <= buffer_view_index < len(buffer_view_dicts):
        return None
    buffer_view_dict = buffer_view_dicts[buffer_view_index]
    if not isinstance(buffer_view_dict, dict):
        return None
    buffer_index = buffer_view_dict.get("buffer")
    if not isinstance(buffer_index, int):
        return None
    if not 0 <= buffer_index < len(buffer_dicts):
        return None

    if buffer_index == 0:
        buffer_bytes = buffer0_bytes
    else:
        prefix = "application/gltf-buffer;base64,"

        buffer_dict = buffer_dicts[buffer_index]
        if not isinstance(buffer_dict, dict):
            return None
        uri = buffer_dict.get("uri")

        if not isinstance(uri, str):
            return None
        try:
            parsed_url = urlparse(uri)
        except ValueError:
            return None
        if parsed_url.scheme != "data":
            return None
        if not parsed_url.path.startswith(prefix):  # TODO: all variants
            return None
        buffer_base64 = parsed_url.path.removeprefix(prefix)
        buffer_bytes = base64.b64decode(buffer_base64)

    byte_offset = buffer_view_dict.get("byteOffset", 0)
    if not isinstance(byte_offset, int):
        return None
    if not 0 <= byte_offset < len(buffer_bytes):
        return None
    byte_length = buffer_view_dict.get("byteLength")
    if not isinstance(byte_length, int):
        return None
    if not 0 <= byte_offset + byte_length <= len(buffer_bytes):
        return None
    return buffer_bytes[slice(byte_offset, byte_offset + byte_length)]


def read_accessor_as_animation_sampler_input(
    accessor_dict: dict[str, Json],
    buffer_view_dicts: list[Json],
    buffer_dicts: list[Json],
    buffer0_bytes: bytes,
) -> Optional[list[float]]:
    if accessor_dict.get("type") != "SCALAR":
        return None
    if accessor_dict.get("componentType") != GL_FLOAT:
        return None
    buffer_bytes = read_accessor_as_bytes(
        accessor_dict, buffer_view_dicts, buffer_dicts, buffer0_bytes
    )
    if buffer_bytes is None:
        return None
    count = accessor_dict.get("count")
    if not isinstance(count, int):
        return None
    if count == 0:
        return []
    if not 1 <= count * 4 <= len(buffer_bytes):
        return None
    floats = struct.unpack("<" + "f" * count, buffer_bytes)
    return list(floats)


def unpack_component(
    component_type: int, unpack_count: int, buffer_bytes: bytes
) -> Optional[Union[tuple[int, ...], tuple[float, ...]]]:
    for search_component_type, component_count, unpack_symbol in [
        (GL_BYTE, 1, "b"),
        (GL_UNSIGNED_BYTE, 1, "B"),
        (GL_SHORT, 2, "h"),
        (GL_UNSIGNED_SHORT, 2, "H"),
        (GL_INT, 4, "i"),
        (GL_UNSIGNED_INT, 4, "I"),
        (GL_FLOAT, 4, "f"),
    ]:
        if search_component_type != component_type:
            continue
        if unpack_count == 0:
            return ()
        if not 1 <= unpack_count * component_count <= len(buffer_bytes):
            return None
        return struct.unpack("<" + unpack_symbol * unpack_count, buffer_bytes)
    return None


def unpack_vector_accessor(
    accessor_dict: dict[str, Json], buffer_bytes: bytes
) -> Union[tuple[tuple[int, ...], ...], tuple[tuple[float, ...], ...], None]:
    if accessor_dict.get("type") == "VEC2":
        vector_dimension = 2
    elif accessor_dict.get("type") == "VEC3":
        vector_dimension = 3
    elif accessor_dict.get("type") == "VEC4":
        vector_dimension = 4
    else:
        return None
    vector_count = accessor_dict.get("count")
    if not isinstance(vector_count, int):
        return None
    component_type = accessor_dict.get("componentType")
    if not isinstance(component_type, int):
        return None
    unpack_count = vector_dimension * vector_count
    unpacked_values = unpack_component(component_type, unpack_count, buffer_bytes)
    if unpacked_values is None:
        return None
    return tuple(
        unpacked_values[slice(i, i + vector_dimension)]
        for i in range(0, unpack_count, vector_dimension)
    )


def read_accessor_as_animation_sampler_translation_output(
    accessor_dict: dict[str, Json],
    buffer_view_dicts: list[Json],
    buffer_dicts: list[Json],
    buffer0_bytes: bytes,
) -> Optional[list[Vector]]:
    if accessor_dict.get("type") != "VEC3":
        return None
    buffer_bytes = read_accessor_as_bytes(
        accessor_dict, buffer_view_dicts, buffer_dicts, buffer0_bytes
    )
    if buffer_bytes is None:
        return None
    unpacked_values = unpack_vector_accessor(accessor_dict, buffer_bytes)
    if unpacked_values is None:
        return None
    return [Vector((x, -z, y)) for x, y, z in unpacked_values]


def read_accessor_as_animation_sampler_rotation_output(
    accessor_dict: dict[str, Json],
    buffer_view_dicts: list[Json],
    buffer_dicts: list[Json],
    buffer0_bytes: bytes,
) -> Optional[list[Quaternion]]:
    if accessor_dict.get("type") != "VEC4":
        return None
    buffer_bytes = read_accessor_as_bytes(
        accessor_dict, buffer_view_dicts, buffer_dicts, buffer0_bytes
    )
    if buffer_bytes is None:
        return None
    unpacked_values = unpack_vector_accessor(accessor_dict, buffer_bytes)
    if not unpacked_values:
        return None
    return [Quaternion((w, x, -z, y)).normalized() for x, y, z, w in unpacked_values]


def work_in_progress(context: Context, path: Path, armature: Object) -> set[str]:
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return {"CANCELLED"}
    humanoid = armature_data.vrm_addon_extension.vrm1.humanoid
    if not humanoid.human_bones.all_required_bones_are_assigned():
        return {"CANCELLED"}

    saved_pose_position = armature_data.pose_position
    vrm1 = armature_data.vrm_addon_extension.vrm1

    # TODO: 現状restがTポーズの時しか動作しない
    # TODO: 自動でTポーズを作成する
    # TODO: Tポーズ取得処理、共通化
    try:
        if context.view_layer.objects.active is not None:
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode="POSE")

        armature_data.pose_position = "POSE"

        t_pose_action = vrm1.humanoid.pose_library
        t_pose_pose_marker_name = vrm1.humanoid.pose_marker_name
        pose_marker_frame = 0
        if t_pose_action and t_pose_pose_marker_name:
            for search_pose_marker in t_pose_action.pose_markers.values():
                if search_pose_marker.name == t_pose_pose_marker_name:
                    pose_marker_frame = search_pose_marker.frame
                    break

        bpy.context.view_layer.update()

        if t_pose_action:
            armature.pose.apply_pose_from_action(
                t_pose_action, evaluation_time=pose_marker_frame
            )
        else:
            for bone in armature.pose.bones:
                bone.location = Vector((0, 0, 0))
                bone.scale = Vector((1, 1, 1))
                if bone.rotation_mode != "QUATERNION":
                    bone.rotation_mode = "QUATERNION"
                bone.rotation_quaternion = Quaternion()

        bpy.context.view_layer.update()

        return work_in_progress_2(context, path, armature)
    finally:
        # TODO: リストア処理、共通化
        if armature_data.pose_position != "POSE":
            armature_data.pose_position = "POSE"
        if context.view_layer.objects.active is not None:
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        context.view_layer.objects.active = armature
        bpy.context.view_layer.update()

        if saved_pose_position:
            armature_data.pose_position = saved_pose_position
        bpy.ops.object.mode_set(mode="OBJECT")


def work_in_progress_2(context: Context, path: Path, armature: Object) -> set[str]:
    if not path.exists():
        return {"CANCELLED"}
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return {"CANCELLED"}
    humanoid = armature_data.vrm_addon_extension.vrm1.humanoid
    if not humanoid.human_bones.all_required_bones_are_assigned():
        return {"CANCELLED"}

    vrma_dict, buffer0_bytes = parse_glb(path.read_bytes())

    node_dicts = vrma_dict.get("nodes")
    if not isinstance(node_dicts, list) or not node_dicts:
        return {"CANCELLED"}

    animation_dicts = vrma_dict.get("animations")
    if not isinstance(animation_dicts, list) or not animation_dicts:
        return {"CANCELLED"}
    animation_dict = animation_dicts[0]
    if not isinstance(animation_dict, dict):
        return {"CANCELLED"}
    animation_channel_dicts = animation_dict.get("channels")
    if not isinstance(animation_channel_dicts, list) or not animation_channel_dicts:
        return {"CANCELLED"}
    animation_sampler_dicts = animation_dict.get("samplers")
    if not isinstance(animation_sampler_dicts, list) or not animation_sampler_dicts:
        return {"CANCELLED"}

    extensions_dict = vrma_dict.get("extensions")
    if not isinstance(extensions_dict, dict):
        return {"CANCELLED"}
    vrmc_vrm_animation_dict = extensions_dict.get("VRMC_vrm_animation")
    if not isinstance(vrmc_vrm_animation_dict, dict):
        return {"CANCELLED"}
    humanoid_dict = vrmc_vrm_animation_dict.get("humanoid")
    if not isinstance(humanoid_dict, dict):
        return {"CANCELLED"}
    human_bones_dict = humanoid_dict.get("humanBones")
    if not isinstance(human_bones_dict, dict):
        return {"CANCELLED"}
    hips_dict = human_bones_dict.get("hips")
    if not isinstance(hips_dict, dict):
        return {"CANCELLED"}
    hips_node_index = hips_dict.get("node")
    if not isinstance(hips_node_index, int):
        return {"CANCELLED"}
    if not 0 <= hips_node_index < len(node_dicts):
        return {"CANCELLED"}
    hips_node_dict = node_dicts[hips_node_index]
    if not isinstance(hips_node_dict, dict):
        return {"CANCELLED"}

    expression_name_to_node_index: dict[str, int] = {}
    expressions_dict = vrmc_vrm_animation_dict.get("expressions")
    if isinstance(expressions_dict, dict):
        preset_dict = expressions_dict.get("preset")
        if isinstance(preset_dict, dict):
            for name, node_dict in preset_dict.items():
                if not isinstance(node_dict, dict):
                    continue
                node_index = node_dict.get("node")
                if not isinstance(node_index, int):
                    continue
                expression_name_to_node_index[name] = node_index

        custom_dict = expressions_dict.get("custom")
        if isinstance(custom_dict, dict):
            for name, node_dict in custom_dict.items():
                if not isinstance(node_dict, dict):
                    continue
                if name in expression_name_to_node_index:
                    continue
                node_index = node_dict.get("node")
                if not isinstance(node_index, int):
                    continue
                expression_name_to_node_index[name] = node_index

    node_index_to_human_bone_name: dict[int, HumanBoneName] = {}
    for human_bone_name_str, human_bone_dict in human_bones_dict.items():
        if not isinstance(human_bone_dict, dict):
            continue
        node_index = human_bone_dict.get("node")
        if not isinstance(node_index, int):
            continue
        if not 0 <= node_index < len(node_dicts):
            continue
        human_bone_name = HumanBoneName.from_str(human_bone_name_str)
        if not human_bone_name:
            continue
        node_index_to_human_bone_name[node_index] = human_bone_name

    root_node_index = find_root_node_index(node_dicts, hips_node_index, set())
    node_rest_pose_trees = NodeRestPoseTree.build(
        node_dicts, root_node_index, is_root=True
    )
    if len(node_rest_pose_trees) != 1:
        return {"CANCELLED"}
    node_rest_pose_tree = node_rest_pose_trees[0]

    accessor_dicts = vrma_dict.get("accessors")
    if not isinstance(accessor_dicts, list):
        return {"CANCELLED"}
    buffer_view_dicts = vrma_dict.get("bufferViews")
    if not isinstance(buffer_view_dicts, list):
        return {"CANCELLED"}
    buffer_dicts = vrma_dict.get("buffers")
    if not isinstance(buffer_dicts, list):
        return {"CANCELLED"}

    humanoid_action = bpy.data.actions.new(name="Humanoid")
    if not armature.animation_data:
        armature.animation_data_create()
    if not armature.animation_data:
        message = "armature.animation_data is None"
        raise ValueError(message)
    armature.animation_data.action = humanoid_action

    expression_action = bpy.data.actions.new(name="Expressions")
    if not armature_data.animation_data:
        armature_data.animation_data_create()
    if not armature_data.animation_data:
        message = "armature_data.animation_data is None"
        raise ValueError(message)
    armature_data.animation_data.action = expression_action

    node_index_to_translation_keyframes: dict[
        int, tuple[tuple[float, Vector], ...]
    ] = {}
    node_index_to_rotation_keyframes: dict[
        int, tuple[tuple[float, Quaternion], ...]
    ] = {}

    for animation_channel_dict in animation_channel_dicts:
        if not isinstance(animation_channel_dict, dict):
            continue
        target_dict = animation_channel_dict.get("target")
        if not isinstance(target_dict, dict):
            continue
        node_index = target_dict.get("node")
        if not isinstance(node_index, int):
            continue
        if not 0 <= node_index < len(node_dicts):
            continue
        animation_path = target_dict.get("path")
        animation_sampler_index = animation_channel_dict.get("sampler")
        if not isinstance(animation_sampler_index, int):
            continue
        if not 0 <= animation_sampler_index < len(animation_sampler_dicts):
            continue
        animation_sampler_dict = animation_sampler_dicts[animation_sampler_index]
        if not isinstance(animation_sampler_dict, dict):
            continue

        input_index = animation_sampler_dict.get("input")
        if not isinstance(input_index, int):
            continue
        if not 0 <= input_index < len(accessor_dicts):
            continue
        input_accessor_dict = accessor_dicts[input_index]
        if not isinstance(input_accessor_dict, dict):
            continue

        output_index = animation_sampler_dict.get("output")
        if not isinstance(output_index, int):
            continue
        if not 0 <= output_index < len(accessor_dicts):
            continue
        output_accessor_dict = accessor_dicts[output_index]
        if not isinstance(output_accessor_dict, dict):
            continue

        if animation_path == "translation":
            timestamps = read_accessor_as_animation_sampler_input(
                input_accessor_dict, buffer_view_dicts, buffer_dicts, buffer0_bytes
            )
            if timestamps is None:
                continue
            translations = read_accessor_as_animation_sampler_translation_output(
                output_accessor_dict, buffer_view_dicts, buffer_dicts, buffer0_bytes
            )
            if translations is None:
                continue
            translation_keyframes = tuple(sorted(zip(timestamps, translations)))
            node_index_to_translation_keyframes[node_index] = translation_keyframes
        elif animation_path == "rotation":
            timestamps = read_accessor_as_animation_sampler_input(
                input_accessor_dict, buffer_view_dicts, buffer_dicts, buffer0_bytes
            )
            if timestamps is None:
                continue
            rotations = read_accessor_as_animation_sampler_rotation_output(
                output_accessor_dict, buffer_view_dicts, buffer_dicts, buffer0_bytes
            )
            if rotations is None:
                continue
            rotation_keyframes = tuple(sorted(zip(timestamps, rotations)))
            node_index_to_rotation_keyframes[node_index] = rotation_keyframes

    expression_name_to_default_preview_value: dict[str, float] = {}
    expression_name_to_translation_keyframes: dict[
        str, tuple[tuple[float, Vector], ...]
    ] = {}
    for expression_name, node_index in expression_name_to_node_index.items():
        if not 0 <= node_index < len(node_dicts):
            continue
        node_dict = node_dicts[node_index]
        if not isinstance(node_dict, dict):
            continue

        translation = node_dict.get("translation")
        if isinstance(translation, list) and translation:
            default_preview_value = translation[0]  # TODO: Matrixだった場合
            if not isinstance(default_preview_value, (float, int)):
                default_preview_value = 0.0
        else:
            default_preview_value = 0.0
        expression_name_to_default_preview_value[expression_name] = (
            default_preview_value
        )

        expression_translation_keyframes = node_index_to_translation_keyframes.get(
            node_index
        )
        if expression_translation_keyframes is None:
            continue
        expression_name_to_translation_keyframes[expression_name] = (
            expression_translation_keyframes
        )

    timestamps = [
        timestamp
        for keyframes in itertools.chain(
            node_index_to_translation_keyframes.values(),
            node_index_to_rotation_keyframes.values(),
        )
        for (timestamp, _) in keyframes
    ]
    timestamps.sort()
    if not timestamps:
        return {"CANCELLED"}

    first_timestamp = timestamps[0]
    last_timestamp = timestamps[-1]

    logger.debug(f"{first_timestamp=} ... {last_timestamp=}")

    first_zero_origin_frame_count: int = math.floor(
        first_timestamp * context.scene.render.fps / context.scene.render.fps_base
    )
    if abs(last_timestamp - first_timestamp) > 0:
        last_zero_origin_frame_count: int = math.ceil(
            last_timestamp * context.scene.render.fps / context.scene.render.fps_base
        )
    else:
        last_zero_origin_frame_count = first_zero_origin_frame_count
    for zero_origin_frame_count in range(
        first_zero_origin_frame_count, last_zero_origin_frame_count + 1
    ):
        timestamp = (
            zero_origin_frame_count
            * context.scene.render.fps_base
            / context.scene.render.fps
        )
        frame_count = zero_origin_frame_count + 1

        assign_humanoid_keyframe(
            armature,
            node_rest_pose_tree,
            node_index_to_human_bone_name,
            node_index_to_translation_keyframes,
            node_index_to_rotation_keyframes,
            frame_count,
            timestamp,
            humanoid_parent_rest_world_matrix=Matrix(),
            intermediate_rest_local_matrix=Matrix(),
            intermediate_pose_local_matrix=Matrix(),
            parent_node_rest_pose_world_matrix=Matrix(),
        )
        assign_expression_keyframe(
            armature_data,
            expression_name_to_default_preview_value,
            expression_name_to_translation_keyframes,
            frame_count,
            timestamp,
        )

    return {"FINISHED"}


def assign_expression_keyframe(
    armature_data: Armature,
    expression_name_to_default_preview_value: dict[str, float],
    expression_name_to_translation_keyframes: dict[
        str, tuple[tuple[float, Vector], ...]
    ],
    frame_count: int,
    timestamp: float,
) -> None:
    expressions = armature_data.vrm_addon_extension.vrm1.expressions
    expression_name_to_expression = expressions.all_name_to_expression_dict()
    for (
        expression_name,
        translation_keyframes,
    ) in expression_name_to_translation_keyframes.items():
        if expression_name in [
            "lookUp",
            "lookDown",
            "lookLeft",
            "lookRight",
        ]:
            continue
        expression = expression_name_to_expression.get(expression_name)
        if not expression:
            continue

        if translation_keyframes:
            preview = None
            begin_timestamp, begin_translation = translation_keyframes[0]
            for end_timestamp, end_translation in translation_keyframes:
                if end_timestamp >= timestamp:
                    timestamp_duration = end_timestamp - begin_timestamp
                    if timestamp_duration > 0:
                        preview = (
                            begin_translation.x
                            + (end_translation.x - begin_translation.x)
                            * (timestamp - begin_timestamp)
                            / timestamp_duration
                        )
                    else:
                        preview = begin_translation.x
                    break
                begin_timestamp = end_timestamp
                begin_translation = end_translation
            if preview is None:
                preview = begin_translation.x
        else:
            preview = (
                expression_name_to_default_preview_value.get(expression_name) or 0.0
            )

        current_preview = expression.preview
        expression.preview = preview
        expression.keyframe_insert(data_path="preview", frame=frame_count)
        expression.preview = current_preview


def assign_humanoid_keyframe(
    armature: Object,
    node_rest_pose_tree: NodeRestPoseTree,
    node_index_to_human_bone_name: dict[int, HumanBoneName],
    node_index_to_translation_keyframes: dict[int, tuple[tuple[float, Vector], ...]],
    node_index_to_rotation_keyframes: dict[int, tuple[tuple[float, Quaternion], ...]],
    frame_count: int,
    timestamp: float,
    humanoid_parent_rest_world_matrix: Matrix,
    intermediate_rest_local_matrix: Matrix,
    intermediate_pose_local_matrix: Matrix,
    parent_node_rest_pose_world_matrix: Matrix,
) -> None:
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return

    translation_keyframes = node_index_to_translation_keyframes.get(
        node_rest_pose_tree.node_index
    )

    if translation_keyframes:
        pose_local_translation = None
        begin_timestamp, begin_translation = translation_keyframes[0]
        for end_timestamp, end_translation in translation_keyframes:
            if end_timestamp >= timestamp:
                timestamp_duration = end_timestamp - begin_timestamp
                if timestamp_duration > 0:
                    pose_local_translation = begin_translation.lerp(
                        end_translation,
                        (timestamp - begin_timestamp) / timestamp_duration,
                    )
                else:
                    pose_local_translation = begin_translation
                break
            begin_timestamp = end_timestamp
            begin_translation = end_translation
        if pose_local_translation is None:
            pose_local_translation = begin_translation

        parent_world_scale = parent_node_rest_pose_world_matrix.to_scale()
        if parent_world_scale.length_squared >= float_info.epsilon:
            if node_rest_pose_tree.is_root:
                node_rest_pose_local_translation = Vector((0, 0, 0))
            else:
                node_rest_pose_local_translation = (
                    node_rest_pose_tree.local_matrix.to_translation()
                )
            # これはもっと便利な方法がありそう
            pose_local_translation = Vector(
                (
                    (pose_local_translation.x - node_rest_pose_local_translation.x)
                    / parent_world_scale.x,
                    (pose_local_translation.y - node_rest_pose_local_translation.y)
                    / parent_world_scale.y,
                    (pose_local_translation.z - node_rest_pose_local_translation.z)
                    / parent_world_scale.z,
                )
            )
    else:
        pose_local_translation = node_rest_pose_tree.local_matrix.to_translation()

    rotation_keyframes = node_index_to_rotation_keyframes.get(
        node_rest_pose_tree.node_index
    )
    if rotation_keyframes:
        pose_local_rotation = None
        begin_timestamp, begin_rotation = rotation_keyframes[0]
        for end_timestamp, end_rotation in rotation_keyframes:
            if end_timestamp >= timestamp:
                timestamp_duration = end_timestamp - begin_timestamp
                if timestamp_duration > 0:
                    pose_local_rotation = begin_rotation.slerp(
                        end_rotation, (timestamp - begin_timestamp) / timestamp_duration
                    )
                else:
                    pose_local_rotation = begin_rotation
                break
            begin_timestamp = end_timestamp
            begin_rotation = end_rotation
        if pose_local_rotation is None:
            pose_local_rotation = (
                node_rest_pose_tree.local_matrix.to_quaternion().inverted()
                @ begin_rotation
            )
    else:
        pose_local_rotation = Quaternion()

    humanoid_rest_world_matrix = humanoid_parent_rest_world_matrix
    rest_local_matrix = (
        intermediate_rest_local_matrix @ node_rest_pose_tree.local_matrix
    )
    pose_local_matrix = (
        intermediate_pose_local_matrix
        @ Matrix.Translation(pose_local_translation)
        @ pose_local_rotation.to_matrix().to_4x4()
        @ Matrix.Diagonal(node_rest_pose_tree.local_matrix.to_scale()).to_4x4()
    )

    human_bone_name = node_index_to_human_bone_name.get(node_rest_pose_tree.node_index)
    if human_bone_name and human_bone_name not in [
        HumanBoneName.LEFT_EYE,
        HumanBoneName.RIGHT_EYE,
    ]:
        human_bones = armature_data.vrm_addon_extension.vrm1.humanoid.human_bones
        human_bone = human_bones.human_bone_name_to_human_bone().get(human_bone_name)
        if human_bone:
            bone = armature.pose.bones.get(human_bone.node.bone_name)
            if bone:
                humanoid_rest_world_matrix = humanoid_parent_rest_world_matrix
                rest_world_matrix = humanoid_rest_world_matrix @ rest_local_matrix
                pose_world_matrix = humanoid_rest_world_matrix @ pose_local_matrix
                # rest_to_pose_matrix = rest_world_matrix.inverted() @ pose_world_matrix
                # rest_to_pose_matrix = rest_local_matrix.inverted() @ pose_local_matrix
                rest_to_pose_matrix = rest_local_matrix.inverted() @ pose_local_matrix
                axis, angle = rest_to_pose_matrix.to_quaternion().to_axis_angle()
                axis.rotate(rest_world_matrix.to_quaternion())
                rest_to_pose_world_rotation = Quaternion(axis, angle).copy()

                target_axis, target_angle = rest_to_pose_world_rotation.to_axis_angle()
                target_axis.rotate(bone.matrix.to_quaternion().inverted())

                rest_to_pose_target_local_rotation = Quaternion(
                    target_axis, target_angle
                ).copy()

                if bone.rotation_mode != "QUATERNION":
                    bone.rotation_mode = "QUATERNION"

                if rotation_keyframes:
                    logger.debug(
                        f"================= {human_bone_name.value} ================="
                    )
                    logger.debug(
                        f"humanoid world matrix = {dump(humanoid_rest_world_matrix)}"
                    )
                    logger.debug(f"rest_local_matrix     = {dump(rest_local_matrix)}")
                    logger.debug(f"pose_local_matrix     = {dump(pose_local_matrix)}")
                    logger.debug(f"rest_world_matrix     = {dump(rest_world_matrix)}")
                    logger.debug(f"pose_world_matrix     = {dump(pose_world_matrix)}")
                    logger.debug(f"rest_to_pose_matrix  = {dump(rest_to_pose_matrix)}")
                    logger.debug(
                        "rest_to_pose_world_rotation = "
                        + dump(rest_to_pose_world_rotation)
                    )
                    logger.debug(
                        "rest_to_pose_target_local_rotation = "
                        + dump(rest_to_pose_target_local_rotation)
                    )

                    # logger.debug(f"parent bone matrix  = {dump(parent_matrix)}")
                    logger.debug(f"       bone matrix  = {dump(bone.matrix)}")
                    logger.debug(
                        f"current bone rotation = {dump(bone.rotation_quaternion)}"
                    )

                    backup_rotation_quaternion = bone.rotation_quaternion.copy()
                    bone.rotation_quaternion = (
                        bone.rotation_quaternion @ rest_to_pose_target_local_rotation
                    )
                    bone.keyframe_insert(
                        data_path="rotation_quaternion", frame=frame_count
                    )
                    bone.rotation_quaternion = backup_rotation_quaternion

                if human_bone_name == HumanBoneName.HIPS and translation_keyframes:
                    translation = (
                        bone.matrix.to_quaternion().inverted()
                        @ humanoid_rest_world_matrix.to_quaternion()
                        @ (
                            pose_local_matrix.to_translation()
                            - rest_local_matrix.to_translation()
                        )
                    )
                    # logger.debug(f"translation           = {dump(translation)}")
                    backup_translation = bone.location.copy()
                    bone.location = translation
                    bone.keyframe_insert(data_path="location", frame=frame_count)
                    bone.location = backup_translation

                humanoid_rest_world_matrix = (
                    humanoid_parent_rest_world_matrix @ rest_local_matrix
                )
                rest_local_matrix = Matrix()
                pose_local_matrix = Matrix()

    for child in node_rest_pose_tree.children:
        assign_humanoid_keyframe(
            armature,
            child,
            node_index_to_human_bone_name,
            node_index_to_translation_keyframes,
            node_index_to_rotation_keyframes,
            frame_count,
            timestamp,
            humanoid_rest_world_matrix,
            rest_local_matrix,
            pose_local_matrix,
            parent_node_rest_pose_world_matrix @ node_rest_pose_tree.local_matrix,
        )
