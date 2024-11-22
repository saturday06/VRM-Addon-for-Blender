# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from sys import float_info
from typing import Optional, Union

import bpy
from bpy.types import (
    Armature,
    Context,
    Object,
    PoseBone,
)
from mathutils import Quaternion, Vector

from ..common import ops
from ..common.vrm0.human_bone import HumanBoneName as Vrm0HumanBoneName
from ..common.vrm1.human_bone import HumanBoneName as Vrm1HumanBoneName
from ..common.workspace import save_workspace
from .extension import get_armature_extension
from .vrm0.property_group import Vrm0HumanoidPropertyGroup
from .vrm1.property_group import Vrm1HumanoidPropertyGroup


def set_bone_direction_to_align_child_bone(
    context: Context,
    armature: Object,
    direction: Vector,
    bone: PoseBone,
    child_bone: PoseBone,
) -> None:
    world_bone_matrix = armature.matrix_world @ bone.matrix
    world_child_bone_matrix = armature.matrix_world @ child_bone.matrix

    world_bone_length = (
        world_child_bone_matrix.translation - world_bone_matrix.translation
    ).length

    world_child_bone_from_translation = world_child_bone_matrix.translation
    world_child_bone_to_translation = (
        world_bone_matrix.translation + direction * world_bone_length
    )

    bone_local_child_bone_from_translation = (
        armature.matrix_world @ bone.matrix
    ).inverted_safe() @ world_child_bone_from_translation
    bone_local_child_bone_to_translation = (
        armature.matrix_world @ bone.matrix
    ).inverted_safe() @ world_child_bone_to_translation

    if bone_local_child_bone_from_translation.length_squared < float_info.epsilon:
        return
    if bone_local_child_bone_to_translation.length_squared < float_info.epsilon:
        return

    rotation = bone_local_child_bone_from_translation.rotation_difference(
        bone_local_child_bone_to_translation
    )

    if bone.rotation_mode != "QUATERNION":
        bone.rotation_mode = "QUATERNION"
    bone.rotation_quaternion = rotation @ bone.rotation_quaternion
    context.view_layer.update()


def set_bone_direction_to_align_z_world_location(
    context: Context,
    armature: Object,
    direction: Vector,
    bone: PoseBone,
    from_world_location: Vector,
) -> None:
    world_bone_translation = (armature.matrix_world @ bone.matrix).to_translation()
    aligned_from_world_location = Vector(
        (
            from_world_location.x,
            world_bone_translation.y,
            from_world_location.z,
        )
    )
    aligned_to_world_location = world_bone_translation + direction

    bone_local_aligned_from_world_location = (
        armature.matrix_world @ bone.matrix
    ).inverted_safe() @ aligned_from_world_location
    bone_local_aligned_to_world_location = (
        armature.matrix_world @ bone.matrix
    ).inverted_safe() @ aligned_to_world_location

    if bone_local_aligned_from_world_location.length_squared < float_info.epsilon:
        return
    if bone_local_aligned_to_world_location.length_squared < float_info.epsilon:
        return

    rotation = bone_local_aligned_from_world_location.rotation_difference(
        bone_local_aligned_to_world_location
    )

    if bone.rotation_mode != "QUATERNION":
        bone.rotation_mode = "QUATERNION"
    bone.rotation_quaternion = rotation @ bone.rotation_quaternion
    context.view_layer.update()


@dataclass(frozen=True)
class ChainSingleChild:
    direction: Vector
    vrm0_human_bone_names: tuple[Vrm0HumanBoneName, ...]
    vrm1_human_bone_names: tuple[Vrm1HumanBoneName, ...]

    def execute(self, context: Context, armature: Object) -> None:
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            raise TypeError

        ext = get_armature_extension(armature_data)
        if ext.is_vrm0():
            humanoid = ext.vrm0.humanoid
            bones: list[PoseBone] = []
            for human_bone in humanoid.human_bones:
                human_bone_name = Vrm0HumanBoneName.from_str(human_bone.bone)
                if not human_bone_name:
                    continue
                if human_bone_name not in self.vrm0_human_bone_names:
                    continue
                bone = armature.pose.bones.get(human_bone.node.bone_name)
                if not bone:
                    continue
                bones.append(bone)
        else:
            human_bones = ext.vrm1.humanoid.human_bones
            human_bone_name_to_human_bone = human_bones.human_bone_name_to_human_bone()
            bones = [
                bone
                for bone in [
                    armature.pose.bones.get(human_bone.node.bone_name)
                    for human_bone in [
                        human_bone_name_to_human_bone.get(human_bone_name)
                        for human_bone_name in self.vrm1_human_bone_names
                    ]
                    if human_bone
                ]
                if bone
            ]

        if len(bones) < 2:
            return

        root_bone = bones[0]
        tip_bone = bones[-1]

        chained_bones: list[PoseBone] = []
        searching_bone: Optional[PoseBone] = tip_bone
        while True:
            if not searching_bone:
                return
            chained_bones.insert(0, searching_bone)
            if searching_bone == root_bone:
                break
            searching_bone = searching_bone.parent

        for bone, child_bone in zip(chained_bones, chained_bones[1:]):
            set_bone_direction_to_align_child_bone(
                context, armature, self.direction, bone, child_bone
            )


@dataclass(frozen=True)
class ChainHorizontalMultipleChildren:
    direction: Vector
    vrm0_parent_human_bone_name: Vrm0HumanBoneName
    vrm0_human_bone_names: tuple[Vrm0HumanBoneName, ...]
    vrm1_parent_human_bone_name: Vrm1HumanBoneName
    vrm1_human_bone_names: tuple[Vrm1HumanBoneName, ...]

    def execute(self, context: Context, armature: Object) -> None:
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            raise TypeError

        ext = get_armature_extension(armature_data)
        if ext.is_vrm0():
            humanoid = ext.vrm0.humanoid
            bones: list[PoseBone] = []
            parent_bone: Optional[PoseBone] = None
            for human_bone in humanoid.human_bones:
                human_bone_name = Vrm0HumanBoneName.from_str(human_bone.bone)
                if not human_bone_name:
                    continue
                if human_bone_name == self.vrm0_parent_human_bone_name:
                    parent_bone = armature.pose.bones.get(human_bone.node.bone_name)
                elif human_bone_name in self.vrm0_human_bone_names:
                    bone = armature.pose.bones.get(human_bone.node.bone_name)
                    if bone:
                        bones.append(bone)
        else:
            human_bones = ext.vrm1.humanoid.human_bones
            human_bone_name_to_human_bone = human_bones.human_bone_name_to_human_bone()
            bones = [
                bone
                for bone in [
                    armature.pose.bones.get(human_bone.node.bone_name)
                    for human_bone in [
                        human_bone_name_to_human_bone.get(human_bone_name)
                        for human_bone_name in self.vrm1_human_bone_names
                    ]
                    if human_bone
                ]
                if bone
            ]
            parent_human_bone = human_bone_name_to_human_bone.get(
                self.vrm1_parent_human_bone_name
            )
            parent_bone = None
            if parent_human_bone:
                parent_bone = armature.pose.bones.get(parent_human_bone.node.bone_name)
        if not bones:
            return
        world_location = Vector((0, 0, 0))
        for bone in bones:
            world_location += (armature.matrix_world @ bone.matrix).to_translation()
        world_location /= len(bones)

        if not parent_bone:
            return

        set_bone_direction_to_align_z_world_location(
            context, armature, self.direction, parent_bone, world_location
        )


def set_estimated_humanoid_t_pose(context: Context, armature: Object) -> bool:
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return False

    ext = get_armature_extension(armature_data)
    if ext.is_vrm0():
        if not ext.vrm0.humanoid.all_required_bones_are_assigned():
            return False
    else:
        human_bones = ext.vrm1.humanoid.human_bones
        if not human_bones.all_required_bones_are_assigned():
            return False

    for bone in armature.pose.bones:
        bone.rotation_mode = "QUATERNION"
        bone.rotation_quaternion = Quaternion()
    context.view_layer.update()

    # https://github.com/vrm-c/vrm-specification/blob/73855bb77d431a3374212551a4fa48e043be3ced/specification/VRMC_vrm-1.0/tpose.md
    chains: tuple[Union[ChainSingleChild, ChainHorizontalMultipleChildren], ...] = (
        ChainSingleChild(
            Vector((-1, 0, 0)),
            (
                Vrm0HumanBoneName.RIGHT_UPPER_ARM,
                Vrm0HumanBoneName.RIGHT_LOWER_ARM,
                Vrm0HumanBoneName.RIGHT_HAND,
            ),
            (
                Vrm1HumanBoneName.RIGHT_UPPER_ARM,
                Vrm1HumanBoneName.RIGHT_LOWER_ARM,
                Vrm1HumanBoneName.RIGHT_HAND,
            ),
        ),
        ChainHorizontalMultipleChildren(
            Vector((-1, 0, 0)),
            Vrm0HumanBoneName.RIGHT_HAND,
            (
                Vrm0HumanBoneName.RIGHT_INDEX_PROXIMAL,
                Vrm0HumanBoneName.RIGHT_MIDDLE_PROXIMAL,
                Vrm0HumanBoneName.RIGHT_RING_PROXIMAL,
                Vrm0HumanBoneName.RIGHT_LITTLE_PROXIMAL,
            ),
            Vrm1HumanBoneName.RIGHT_HAND,
            (
                Vrm1HumanBoneName.RIGHT_INDEX_PROXIMAL,
                Vrm1HumanBoneName.RIGHT_MIDDLE_PROXIMAL,
                Vrm1HumanBoneName.RIGHT_RING_PROXIMAL,
                Vrm1HumanBoneName.RIGHT_LITTLE_PROXIMAL,
            ),
        ),
        ChainSingleChild(
            Vector((-math.sqrt(0.5), -math.sqrt(0.5), 0)),
            (
                Vrm0HumanBoneName.RIGHT_THUMB_PROXIMAL,
                Vrm0HumanBoneName.RIGHT_THUMB_INTERMEDIATE,
                Vrm0HumanBoneName.RIGHT_THUMB_DISTAL,
            ),
            (
                Vrm1HumanBoneName.RIGHT_THUMB_METACARPAL,
                Vrm1HumanBoneName.RIGHT_THUMB_PROXIMAL,
                Vrm1HumanBoneName.RIGHT_THUMB_DISTAL,
            ),
        ),
        ChainSingleChild(
            Vector((-1, 0, 0)),
            (
                Vrm0HumanBoneName.RIGHT_INDEX_PROXIMAL,
                Vrm0HumanBoneName.RIGHT_INDEX_INTERMEDIATE,
                Vrm0HumanBoneName.RIGHT_INDEX_DISTAL,
            ),
            (
                Vrm1HumanBoneName.RIGHT_INDEX_PROXIMAL,
                Vrm1HumanBoneName.RIGHT_INDEX_INTERMEDIATE,
                Vrm1HumanBoneName.RIGHT_INDEX_DISTAL,
            ),
        ),
        ChainSingleChild(
            Vector((-1, 0, 0)),
            (
                Vrm0HumanBoneName.RIGHT_MIDDLE_PROXIMAL,
                Vrm0HumanBoneName.RIGHT_MIDDLE_INTERMEDIATE,
                Vrm0HumanBoneName.RIGHT_MIDDLE_DISTAL,
            ),
            (
                Vrm1HumanBoneName.RIGHT_MIDDLE_PROXIMAL,
                Vrm1HumanBoneName.RIGHT_MIDDLE_INTERMEDIATE,
                Vrm1HumanBoneName.RIGHT_MIDDLE_DISTAL,
            ),
        ),
        ChainSingleChild(
            Vector((-1, 0, 0)),
            (
                Vrm0HumanBoneName.RIGHT_RING_PROXIMAL,
                Vrm0HumanBoneName.RIGHT_RING_INTERMEDIATE,
                Vrm0HumanBoneName.RIGHT_RING_DISTAL,
            ),
            (
                Vrm1HumanBoneName.RIGHT_RING_PROXIMAL,
                Vrm1HumanBoneName.RIGHT_RING_INTERMEDIATE,
                Vrm1HumanBoneName.RIGHT_RING_DISTAL,
            ),
        ),
        ChainSingleChild(
            Vector((-1, 0, 0)),
            (
                Vrm0HumanBoneName.RIGHT_LITTLE_PROXIMAL,
                Vrm0HumanBoneName.RIGHT_LITTLE_INTERMEDIATE,
                Vrm0HumanBoneName.RIGHT_LITTLE_DISTAL,
            ),
            (
                Vrm1HumanBoneName.RIGHT_LITTLE_PROXIMAL,
                Vrm1HumanBoneName.RIGHT_LITTLE_INTERMEDIATE,
                Vrm1HumanBoneName.RIGHT_LITTLE_DISTAL,
            ),
        ),
        ChainSingleChild(
            Vector((0, 0, -1)),
            (
                Vrm0HumanBoneName.RIGHT_UPPER_LEG,
                Vrm0HumanBoneName.RIGHT_LOWER_LEG,
                Vrm0HumanBoneName.RIGHT_FOOT,
            ),
            (
                Vrm1HumanBoneName.RIGHT_UPPER_LEG,
                Vrm1HumanBoneName.RIGHT_LOWER_LEG,
                Vrm1HumanBoneName.RIGHT_FOOT,
            ),
        ),
        ChainSingleChild(
            Vector((1, 0, 0)),
            (
                Vrm0HumanBoneName.LEFT_UPPER_ARM,
                Vrm0HumanBoneName.LEFT_LOWER_ARM,
                Vrm0HumanBoneName.LEFT_HAND,
            ),
            (
                Vrm1HumanBoneName.LEFT_UPPER_ARM,
                Vrm1HumanBoneName.LEFT_LOWER_ARM,
                Vrm1HumanBoneName.LEFT_HAND,
            ),
        ),
        ChainHorizontalMultipleChildren(
            Vector((1, 0, 0)),
            Vrm0HumanBoneName.LEFT_HAND,
            (
                Vrm0HumanBoneName.LEFT_INDEX_PROXIMAL,
                Vrm0HumanBoneName.LEFT_MIDDLE_PROXIMAL,
                Vrm0HumanBoneName.LEFT_RING_PROXIMAL,
                Vrm0HumanBoneName.LEFT_LITTLE_PROXIMAL,
            ),
            Vrm1HumanBoneName.LEFT_HAND,
            (
                Vrm1HumanBoneName.LEFT_INDEX_PROXIMAL,
                Vrm1HumanBoneName.LEFT_MIDDLE_PROXIMAL,
                Vrm1HumanBoneName.LEFT_RING_PROXIMAL,
                Vrm1HumanBoneName.LEFT_LITTLE_PROXIMAL,
            ),
        ),
        ChainSingleChild(
            Vector((math.sqrt(0.5), -math.sqrt(0.5), 0)),
            (
                Vrm0HumanBoneName.LEFT_THUMB_PROXIMAL,
                Vrm0HumanBoneName.LEFT_THUMB_INTERMEDIATE,
                Vrm0HumanBoneName.LEFT_THUMB_DISTAL,
            ),
            (
                Vrm1HumanBoneName.LEFT_THUMB_METACARPAL,
                Vrm1HumanBoneName.LEFT_THUMB_PROXIMAL,
                Vrm1HumanBoneName.LEFT_THUMB_DISTAL,
            ),
        ),
        ChainSingleChild(
            Vector((1, 0, 0)),
            (
                Vrm0HumanBoneName.LEFT_INDEX_PROXIMAL,
                Vrm0HumanBoneName.LEFT_INDEX_INTERMEDIATE,
                Vrm0HumanBoneName.LEFT_INDEX_DISTAL,
            ),
            (
                Vrm1HumanBoneName.LEFT_INDEX_PROXIMAL,
                Vrm1HumanBoneName.LEFT_INDEX_INTERMEDIATE,
                Vrm1HumanBoneName.LEFT_INDEX_DISTAL,
            ),
        ),
        ChainSingleChild(
            Vector((1, 0, 0)),
            (
                Vrm0HumanBoneName.LEFT_MIDDLE_PROXIMAL,
                Vrm0HumanBoneName.LEFT_MIDDLE_INTERMEDIATE,
                Vrm0HumanBoneName.LEFT_MIDDLE_DISTAL,
            ),
            (
                Vrm1HumanBoneName.LEFT_MIDDLE_PROXIMAL,
                Vrm1HumanBoneName.LEFT_MIDDLE_INTERMEDIATE,
                Vrm1HumanBoneName.LEFT_MIDDLE_DISTAL,
            ),
        ),
        ChainSingleChild(
            Vector((1, 0, 0)),
            (
                Vrm0HumanBoneName.LEFT_RING_PROXIMAL,
                Vrm0HumanBoneName.LEFT_RING_INTERMEDIATE,
                Vrm0HumanBoneName.LEFT_RING_DISTAL,
            ),
            (
                Vrm1HumanBoneName.LEFT_RING_PROXIMAL,
                Vrm1HumanBoneName.LEFT_RING_INTERMEDIATE,
                Vrm1HumanBoneName.LEFT_RING_DISTAL,
            ),
        ),
        ChainSingleChild(
            Vector((1, 0, 0)),
            (
                Vrm0HumanBoneName.LEFT_LITTLE_PROXIMAL,
                Vrm0HumanBoneName.LEFT_LITTLE_INTERMEDIATE,
                Vrm0HumanBoneName.LEFT_LITTLE_DISTAL,
            ),
            (
                Vrm1HumanBoneName.LEFT_LITTLE_PROXIMAL,
                Vrm1HumanBoneName.LEFT_LITTLE_INTERMEDIATE,
                Vrm1HumanBoneName.LEFT_LITTLE_DISTAL,
            ),
        ),
        ChainSingleChild(
            Vector((0, 0, -1)),
            (
                Vrm0HumanBoneName.LEFT_UPPER_LEG,
                Vrm0HumanBoneName.LEFT_LOWER_LEG,
                Vrm0HumanBoneName.LEFT_FOOT,
            ),
            (
                Vrm1HumanBoneName.LEFT_UPPER_LEG,
                Vrm1HumanBoneName.LEFT_LOWER_LEG,
                Vrm1HumanBoneName.LEFT_FOOT,
            ),
        ),
    )
    for chain in chains:
        chain.execute(context, armature)

    return True


@contextmanager
def setup_humanoid_t_pose(
    context: Context,
    armature: Object,
) -> Iterator[None]:
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        raise TypeError
    ext = get_armature_extension(armature_data)
    if ext.is_vrm0():
        humanoid: Union[Vrm0HumanoidPropertyGroup, Vrm1HumanoidPropertyGroup] = (
            ext.vrm0.humanoid
        )
    else:
        humanoid = ext.vrm1.humanoid
    pose = humanoid.pose
    action = humanoid.pose_library
    pose_marker_name = humanoid.pose_marker_name

    if pose != humanoid.POSE_CUSTOM_POSE.identifier:
        action = None
        pose_marker_name = ""

    if (
        pose == humanoid.POSE_CURRENT_POSE.identifier
        and armature_data.pose_position == "REST"
    ):
        yield
        return

    if pose == humanoid.POSE_REST_POSITION_POSE.identifier or (
        pose == humanoid.POSE_CUSTOM_POSE.identifier
        and not (action and action.name in context.blend_data.actions)
    ):
        saved_pose_position = armature_data.pose_position
        armature_data.pose_position = "REST"
        try:
            yield
        finally:
            armature_data.pose_position = saved_pose_position
        return

    with save_workspace(context, armature):
        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="POSE")

        saved_pose_position = armature_data.pose_position
        if armature_data.pose_position != "POSE":
            armature_data.pose_position = "POSE"

        context.view_layer.update()
        saved_current_pose_matrix_basis_dict = {
            bone.name: bone.matrix_basis.copy() for bone in armature.pose.bones
        }
        saved_current_pose_matrix_dict = {
            bone.name: bone.matrix.copy() for bone in armature.pose.bones
        }

        ext = get_armature_extension(armature_data)
        saved_vrm1_look_at_preview = ext.vrm1.look_at.enable_preview
        if ext.is_vrm1() and ext.vrm1.look_at.enable_preview:
            # TODO: エクスポート時にここに到達する場合は事前に警告をすると親切
            ext.vrm1.look_at.enable_preview = False
            if ext.vrm1.look_at.type == ext.vrm1.look_at.TYPE_BONE.identifier:
                human_bones = ext.vrm1.humanoid.human_bones

                left_eye_bone_name = human_bones.left_eye.node.bone_name
                left_eye_bone = armature.pose.bones.get(left_eye_bone_name)
                if left_eye_bone:
                    if left_eye_bone.rotation_mode != "QUATERNION":
                        left_eye_bone.rotation_mode = "QUATERNION"
                    left_eye_bone.rotation_quaternion = Quaternion()

                right_eye_bone_name = human_bones.right_eye.node.bone_name
                right_eye_bone = armature.pose.bones.get(right_eye_bone_name)
                if right_eye_bone:
                    if right_eye_bone.rotation_mode != "QUATERNION":
                        right_eye_bone.rotation_mode = "QUATERNION"
                    right_eye_bone.rotation_quaternion = Quaternion()

        if pose == humanoid.POSE_AUTO_POSE.identifier:
            ops.vrm.make_estimated_humanoid_t_pose(armature_name=armature.name)
        elif pose == humanoid.POSE_CUSTOM_POSE.identifier:
            if action and action.name in context.blend_data.actions:
                pose_marker_frame = 0
                if pose_marker_name:
                    for search_pose_marker in action.pose_markers.values():
                        if search_pose_marker.name == pose_marker_name:
                            pose_marker_frame = search_pose_marker.frame
                            break
                armature.pose.apply_pose_from_action(
                    action, evaluation_time=pose_marker_frame
                )
            else:
                # TODO: エクスポート時にここに到達する場合は事前に警告をすると親切
                ops.vrm.make_estimated_humanoid_t_pose(armature_name=armature.name)

    context.view_layer.update()

    try:
        yield
    finally:
        with save_workspace(context, armature):
            bpy.ops.object.select_all(action="DESELECT")
            bpy.ops.object.mode_set(mode="POSE")

            bones = [bone for bone in armature.pose.bones if not bone.parent]
            while bones:
                bone = bones.pop()
                matrix_basis = saved_current_pose_matrix_basis_dict.get(bone.name)
                if matrix_basis is not None:
                    bone.matrix_basis = matrix_basis
                bones.extend(bone.children)
            context.view_layer.update()

            bones = [bone for bone in armature.pose.bones if not bone.parent]
            while bones:
                bone = bones.pop()
                matrix = saved_current_pose_matrix_dict.get(bone.name)
                if matrix is not None:
                    bone.matrix = matrix
                bones.extend(bone.children)
            context.view_layer.update()

            armature_data.pose_position = saved_pose_position
            bpy.ops.object.mode_set(mode="OBJECT")

            ext = get_armature_extension(armature_data)
            if (
                ext.is_vrm1()
                and ext.vrm1.look_at.enable_preview != saved_vrm1_look_at_preview
            ):
                ext.vrm1.look_at.enable_preview = saved_vrm1_look_at_preview