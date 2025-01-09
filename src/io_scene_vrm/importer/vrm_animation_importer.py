# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import itertools
import math
from dataclasses import dataclass
from pathlib import Path

from bpy.types import Armature, Context, Object
from mathutils import Matrix, Quaternion, Vector

from ..common import convert
from ..common.convert import Json
from ..common.debug import dump
from ..common.gltf import (
    parse_glb,
    read_accessor_as_animation_sampler_input,
    read_accessor_as_animation_sampler_rotation_output,
    read_accessor_as_animation_sampler_translation_output,
)
from ..common.logger import get_logger
from ..common.rotation import (
    get_rotation_as_quaternion,
    insert_rotation_keyframe,
    set_rotation_without_mode_change,
)
from ..common.vrm1.human_bone import HumanBoneName
from ..common.workspace import save_workspace
from ..editor.extension import get_armature_extension
from ..editor.t_pose import setup_humanoid_t_pose

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
        *,
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
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}

        humanoid = get_armature_extension(armature_data).vrm1.humanoid
        if not humanoid.human_bones.all_required_bones_are_assigned():
            return {"CANCELLED"}

        with (
            setup_humanoid_t_pose(context, armature),
            save_workspace(context, armature, mode="POSE"),
        ):
            return import_vrm_animation(context, path, armature)


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


def import_vrm_animation(context: Context, path: Path, armature: Object) -> set[str]:
    if not path.exists():
        return {"CANCELLED"}
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return {"CANCELLED"}
    humanoid = get_armature_extension(armature_data).vrm1.humanoid
    if not humanoid.human_bones.all_required_bones_are_assigned():
        return {"CANCELLED"}
    look_at = get_armature_extension(armature_data).vrm1.look_at

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

    humanoid_action = context.blend_data.actions.new(name="Humanoid")
    if not armature.animation_data:
        armature.animation_data_create()
    if not armature.animation_data:
        message = "armature.animation_data is None"
        raise ValueError(message)
    armature.animation_data.action = humanoid_action

    expression_action = context.blend_data.actions.new(name="Expressions")
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

    logger.debug(
        "first_timestamp=%s ... last_timestamp=%s",
        first_timestamp,
        last_timestamp,
    )

    look_at_target_object = None
    look_at_translation_keyframes = None
    look_at_dict = vrmc_vrm_animation_dict.get("lookAt")
    if isinstance(look_at_dict, dict):
        look_at_target_node_index = look_at_dict.get("node")
        if isinstance(
            look_at_target_node_index, int
        ) and 0 <= look_at_target_node_index < len(node_dicts):
            look_at_translation_keyframes = node_index_to_translation_keyframes.get(
                look_at_target_node_index
            )
            look_at_target_node_dict = node_dicts[look_at_target_node_index]
            if look_at_translation_keyframes and isinstance(
                look_at_target_node_dict, dict
            ):
                look_at_target_translation = convert.float3_or_none(
                    look_at_target_node_dict.get("translation")
                )
                look_at_target_name = look_at_target_node_dict.get("name")
                if not isinstance(look_at_target_name, str) or not look_at_target_name:
                    look_at_target_name = "LookAtTarget"
                if look_at_target_translation is not None:
                    look_at_target_object = context.blend_data.objects.new(
                        name=look_at_target_name, object_data=None
                    )
                    look_at_target_object.empty_display_size = 0.125
                    x, y, z = look_at_target_translation
                    look_at_target_object.location = Vector((x, -z, y))
                    context.scene.collection.objects.link(look_at_target_object)
                    look_at.enable_preview = True
                    look_at.preview_target_bpy_object = look_at_target_object

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
        if look_at_target_object and look_at_translation_keyframes:
            assign_look_at_keyframe(
                look_at_target_object,
                look_at_translation_keyframes,
                frame_count,
                timestamp,
            )

    return {"FINISHED"}


def assign_look_at_keyframe(
    look_at_target_object: Object,
    translation_keyframes: tuple[tuple[float, Vector], ...],
    frame_count: int,
    timestamp: float,
) -> None:
    if not translation_keyframes:
        return

    animation_translation = None
    begin_timestamp, begin_translation = translation_keyframes[0]
    for end_timestamp, end_translation in translation_keyframes:
        if end_timestamp >= timestamp:
            timestamp_duration = end_timestamp - begin_timestamp
            if timestamp_duration > 0:
                animation_translation = (
                    begin_translation
                    + (end_translation - begin_translation)
                    * (timestamp - begin_timestamp)
                    / timestamp_duration
                )
            else:
                animation_translation = begin_translation
            break
        begin_timestamp = end_timestamp
        begin_translation = end_translation
    if animation_translation is None:
        animation_translation = begin_translation

    current_location = look_at_target_object.location.copy()
    look_at_target_object.location = animation_translation
    look_at_target_object.keyframe_insert(data_path="location", frame=frame_count)
    look_at_target_object.location = current_location


def assign_expression_keyframe(
    armature_data: Armature,
    expression_name_to_default_preview_value: dict[str, float],
    expression_name_to_translation_keyframes: dict[
        str, tuple[tuple[float, Vector], ...]
    ],
    frame_count: int,
    timestamp: float,
) -> None:
    expressions = get_armature_extension(armature_data).vrm1.expressions
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
        keyframe_translation = None
        begin_timestamp, begin_translation = translation_keyframes[0]
        for end_timestamp, end_translation in translation_keyframes:
            if end_timestamp >= timestamp:
                timestamp_duration = end_timestamp - begin_timestamp
                if timestamp_duration > 0:
                    keyframe_translation = begin_translation.lerp(
                        end_translation,
                        (timestamp - begin_timestamp) / timestamp_duration,
                    )
                else:
                    keyframe_translation = begin_translation
                break
            begin_timestamp = end_timestamp
            begin_translation = end_translation
        if keyframe_translation is None:
            keyframe_translation = begin_translation
    else:
        keyframe_translation = node_rest_pose_tree.local_matrix.to_translation()

    rotation_keyframes = node_index_to_rotation_keyframes.get(
        node_rest_pose_tree.node_index
    )
    if rotation_keyframes:
        keyframe_rotation = None
        begin_timestamp, begin_rotation = rotation_keyframes[0]
        for end_timestamp, end_rotation in rotation_keyframes:
            if end_timestamp >= timestamp:
                timestamp_duration = end_timestamp - begin_timestamp
                if timestamp_duration > 0:
                    keyframe_rotation = begin_rotation.slerp(
                        end_rotation, (timestamp - begin_timestamp) / timestamp_duration
                    )
                else:
                    keyframe_rotation = begin_rotation
                break
            begin_timestamp = end_timestamp
            begin_rotation = end_rotation
        if keyframe_rotation is None:
            keyframe_rotation = begin_rotation
    else:
        keyframe_rotation = node_rest_pose_tree.local_matrix.to_quaternion()

    humanoid_rest_world_matrix = humanoid_parent_rest_world_matrix
    rest_local_matrix = (
        intermediate_rest_local_matrix @ node_rest_pose_tree.local_matrix
    )
    pose_local_matrix = (
        intermediate_pose_local_matrix
        @ Matrix.Translation(keyframe_translation)
        @ keyframe_rotation.to_matrix().to_4x4()
        @ Matrix.Diagonal(node_rest_pose_tree.local_matrix.to_scale()).to_4x4()
    )

    human_bone_name = node_index_to_human_bone_name.get(node_rest_pose_tree.node_index)
    human_bones = get_armature_extension(armature_data).vrm1.humanoid.human_bones
    if (
        human_bone_name
        and human_bone_name not in [HumanBoneName.LEFT_EYE, HumanBoneName.RIGHT_EYE]
        and (
            human_bone := human_bones.human_bone_name_to_human_bone().get(
                human_bone_name
            )
        )
        and (bone := armature.pose.bones.get(human_bone.node.bone_name))
    ):
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

        if rotation_keyframes:
            logger.debug(
                "================= %s =================", human_bone_name.value
            )
            logger.debug("humanoid world matrix = %s", dump(humanoid_rest_world_matrix))
            logger.debug("rest_local_matrix     = %s", dump(rest_local_matrix))
            logger.debug("pose_local_matrix     = %s", dump(pose_local_matrix))
            logger.debug("rest_world_matrix     = %s", dump(rest_world_matrix))
            logger.debug("pose_world_matrix     = %s", dump(pose_world_matrix))
            logger.debug("rest_to_pose_matrix  = %s", dump(rest_to_pose_matrix))
            logger.debug(
                "rest_to_pose_world_rotation = %s",
                dump(rest_to_pose_world_rotation),
            )
            logger.debug(
                "rest_to_pose_target_local_rotation = %s",
                dump(rest_to_pose_target_local_rotation),
            )

            backup_rotation_quaternion = get_rotation_as_quaternion(bone)

            # logger.debug("parent bone matrix  = %s", dump(parent_matrix))
            logger.debug("       bone matrix  = %s", dump(bone.matrix))
            logger.debug("current bone rotation = %s", dump(backup_rotation_quaternion))

            set_rotation_without_mode_change(
                bone, backup_rotation_quaternion @ rest_to_pose_target_local_rotation
            )
            insert_rotation_keyframe(bone, frame=frame_count)
            set_rotation_without_mode_change(bone, backup_rotation_quaternion)

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
