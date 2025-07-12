# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from sys import float_info
from typing import Optional, Union

import bpy
from bpy.app.handlers import persistent
from bpy.types import Armature, Context, Object, PoseBone
from mathutils import Matrix, Quaternion, Vector

from ...common.rotation import (
    get_rotation_as_quaternion,
    set_rotation_without_mode_change,
)
from ..extension import get_armature_extension
from ..property_group import CollectionPropertyProtocol
from .property_group import (
    SpringBone1JointPropertyGroup,
    SpringBone1SpringPropertyGroup,
)


@dataclass
class State:
    frame_count: Decimal = Decimal()
    spring_bone_60_fps_update_count: Decimal = Decimal()
    last_fps: Optional[Decimal] = None
    last_fps_base: Optional[Decimal] = None

    def reset(self, context: Context) -> None:
        self.frame_count = Decimal()
        self.spring_bone_60_fps_update_count = Decimal()
        self.last_fps_base = Decimal(context.scene.render.fps_base)
        self.last_fps = Decimal(context.scene.render.fps)


state = State()


def reset_state(context: Context) -> None:
    state.reset(context)


@dataclass(frozen=True)
class SphereWorldCollider:
    offset: Vector
    radius: float

    def calculate_collision(
        self, target: Vector, target_radius: float
    ) -> tuple[Vector, float]:
        diff = target - self.offset
        diff_length = diff.length
        if diff_length < float_info.epsilon:
            return Vector((0, 0, -1)), -0.01
        return diff / diff_length, diff_length - target_radius - self.radius


@dataclass(frozen=True)
class CapsuleWorldCollider:
    offset: Vector
    radius: float
    tail: Vector
    offset_to_tail_diff: Vector  # Must be non-zero vector
    offset_to_tail_diff_length_squared: float  # Must be non-negative value

    def calculate_collision(
        self, target: Vector, target_radius: float
    ) -> tuple[Vector, float]:
        offset_to_target_diff = target - self.offset

        # Find the shortest point on the line containing offset and tail to the target
        # self.offset + (self.tail - self.offset) * offset_to_tail_ratio_for_nearest
        # Calculate offset_to_tail_ratio_for_nearest to express it as the above formula
        offset_to_tail_ratio_for_nearest = (
            self.offset_to_tail_diff.dot(offset_to_target_diff)
            / self.offset_to_tail_diff_length_squared
        )

        # The line segment from offset to tail has start point 0 and end point 1,
        # so clamp outside ranges
        offset_to_tail_ratio_for_nearest = max(
            0, min(1, offset_to_tail_ratio_for_nearest)
        )

        # Calculate the shortest point to the target
        nearest = (
            self.offset + self.offset_to_tail_diff * offset_to_tail_ratio_for_nearest
        )

        # Collision detection
        diff = target - nearest
        diff_length = diff.length
        if diff_length < float_info.epsilon:
            return Vector((0, 0, -1)), -0.01
        return diff / diff_length, diff_length - target_radius - self.radius


@dataclass(frozen=True)
class SphereInsideWorldCollider:
    offset: Vector
    radius: float

    def calculate_collision(
        self, target: Vector, target_radius: float
    ) -> tuple[Vector, float]:
        diff = self.offset - target
        diff_length = diff.length
        if diff_length < float_info.epsilon:
            return Vector((0, 0, -1)), -0.01
        return diff / diff_length, -diff_length - target_radius + self.radius


@dataclass(frozen=True)
class CapsuleInsideWorldCollider:
    offset: Vector
    radius: float
    tail: Vector
    offset_to_tail_diff: Vector  # Must be non-zero vector
    offset_to_tail_diff_length_squared: float  # Must be non-negative value

    def calculate_collision(
        self, target: Vector, target_radius: float
    ) -> tuple[Vector, float]:
        offset_to_target_diff = target - self.offset

        # Find the shortest point on the line containing offset and tail to the target
        # self.offset + (self.tail - self.offset) * offset_to_tail_ratio_for_nearest
        # Calculate offset_to_tail_ratio_for_nearest to express it as the above formula
        offset_to_tail_ratio_for_nearest = (
            self.offset_to_tail_diff.dot(offset_to_target_diff)
            / self.offset_to_tail_diff_length_squared
        )

        # The line segment from offset to tail has start point 0 and end point 1,
        # so clamp outside ranges
        offset_to_tail_ratio_for_nearest = max(
            0, min(1, offset_to_tail_ratio_for_nearest)
        )

        # Calculate the shortest point to the target
        nearest = (
            self.offset + self.offset_to_tail_diff * offset_to_tail_ratio_for_nearest
        )

        # Collision detection
        diff = nearest - target
        diff_length = diff.length
        if diff_length < float_info.epsilon:
            return Vector((0, 0, -1)), -0.01
        return diff / diff_length, -diff_length - target_radius + self.radius


@dataclass(frozen=True)
class PlaneWorldCollider:
    offset: Vector
    normal: Vector

    def calculate_collision(
        self, target: Vector, target_radius: float
    ) -> tuple[Vector, float]:
        distance = (target - self.offset).dot(self.normal) - target_radius
        return self.normal, distance


# https://github.com/vrm-c/vrm-specification/tree/993a90a5bda9025f3d9e2923ad6dea7506f88553/specification/VRMC_springBone-1.0#update-procedure
def update_pose_bone_rotations(context: Context, delta_time: float) -> None:
    pose_bone_and_rotations: list[tuple[PoseBone, Quaternion]] = []

    for obj in context.blend_data.objects:
        calculate_object_pose_bone_rotations(delta_time, obj, pose_bone_and_rotations)

    for pose_bone, pose_bone_rotation in pose_bone_and_rotations:
        # Assigning rotation to pose_bone is expensive, so avoid it as much as possible
        angle_diff = pose_bone_rotation.rotation_difference(
            get_rotation_as_quaternion(pose_bone)
        ).angle
        if abs(angle_diff) < float_info.epsilon:
            continue
        set_rotation_without_mode_change(pose_bone, pose_bone_rotation)


def calculate_object_pose_bone_rotations(
    delta_time: float,
    obj: Object,
    pose_bone_and_rotations: list[tuple[PoseBone, Quaternion]],
) -> None:
    if obj.type != "ARMATURE":
        return
    armature_data = obj.data
    if not isinstance(armature_data, Armature):
        return
    ext = get_armature_extension(armature_data)
    if not ext.is_vrm1():
        return
    spring_bone1 = ext.spring_bone1
    if not spring_bone1.enable_animation:
        return

    obj_matrix_world = obj.matrix_world
    obj_matrix_world_inverted = obj_matrix_world.inverted_safe()
    obj_matrix_world_quaternion = obj_matrix_world.to_quaternion()

    collider_uuid_to_world_collider: dict[
        str,
        Union[
            SphereWorldCollider,
            CapsuleWorldCollider,
            SphereInsideWorldCollider,
            CapsuleInsideWorldCollider,
            PlaneWorldCollider,
        ],
    ] = {}
    for collider in spring_bone1.colliders:
        pose_bone = obj.pose.bones.get(collider.node.bone_name)
        if not pose_bone:
            continue
        pose_bone_world_matrix = obj_matrix_world @ pose_bone.matrix

        extended_collider = collider.extensions.vrmc_spring_bone_extended_collider
        world_collider: Union[
            None,
            SphereWorldCollider,
            CapsuleWorldCollider,
            SphereInsideWorldCollider,
            CapsuleInsideWorldCollider,
            PlaneWorldCollider,
        ] = None
        if extended_collider.enabled:
            if (
                extended_collider.shape_type
                == extended_collider.SHAPE_TYPE_EXTENDED_SPHERE.identifier
            ):
                offset = pose_bone_world_matrix @ Vector(
                    extended_collider.shape.sphere.offset
                )
                radius = extended_collider.shape.sphere.radius
                if extended_collider.shape.sphere.inside:
                    world_collider = SphereInsideWorldCollider(
                        offset=offset, radius=radius
                    )
                else:
                    world_collider = SphereWorldCollider(offset=offset, radius=radius)
            elif (
                extended_collider.shape_type
                == extended_collider.SHAPE_TYPE_EXTENDED_CAPSULE.identifier
            ):
                offset = pose_bone_world_matrix @ Vector(
                    extended_collider.shape.capsule.offset
                )
                tail = pose_bone_world_matrix @ Vector(
                    extended_collider.shape.capsule.tail
                )
                radius = extended_collider.shape.sphere.radius
                offset_to_tail_diff = tail - offset
                offset_to_tail_diff_length_squared = offset_to_tail_diff.length_squared
                if offset_to_tail_diff_length_squared < float_info.epsilon:
                    # If offset and tail positions are the same, use as sphere collider
                    if extended_collider.shape.capsule.inside:
                        world_collider = SphereInsideWorldCollider(
                            offset=offset, radius=radius
                        )
                    else:
                        world_collider = SphereWorldCollider(
                            offset=offset, radius=radius
                        )
                elif extended_collider.shape.capsule.inside:
                    world_collider = CapsuleInsideWorldCollider(
                        offset=offset,
                        radius=radius,
                        tail=tail,
                        offset_to_tail_diff=offset_to_tail_diff,
                        offset_to_tail_diff_length_squared=offset_to_tail_diff_length_squared,
                    )
                else:
                    world_collider = CapsuleWorldCollider(
                        offset=offset,
                        radius=radius,
                        tail=tail,
                        offset_to_tail_diff=offset_to_tail_diff,
                        offset_to_tail_diff_length_squared=offset_to_tail_diff_length_squared,
                    )
            elif (
                extended_collider.shape_type
                == extended_collider.SHAPE_TYPE_EXTENDED_PLANE.identifier
            ):
                offset = pose_bone_world_matrix @ Vector(
                    extended_collider.shape.plane.offset
                )
                normal = pose_bone_world_matrix.to_quaternion() @ Vector(
                    extended_collider.shape.plane.normal
                )
                world_collider = PlaneWorldCollider(
                    offset=offset,
                    normal=normal,
                )
        elif collider.shape_type == collider.SHAPE_TYPE_SPHERE.identifier:
            offset = pose_bone_world_matrix @ Vector(collider.shape.sphere.offset)
            radius = collider.shape.sphere.radius
            world_collider = SphereWorldCollider(
                offset=offset,
                radius=radius,
            )
        elif collider.shape_type == collider.SHAPE_TYPE_CAPSULE.identifier:
            offset = pose_bone_world_matrix @ Vector(collider.shape.capsule.offset)
            tail = pose_bone_world_matrix @ Vector(collider.shape.capsule.tail)
            radius = collider.shape.sphere.radius
            offset_to_tail_diff = tail - offset
            offset_to_tail_diff_length_squared = offset_to_tail_diff.length_squared
            if offset_to_tail_diff_length_squared < float_info.epsilon:
                # If offset and tail positions are the same, use as sphere collider
                world_collider = SphereWorldCollider(
                    offset=offset,
                    radius=radius,
                )
            else:
                world_collider = CapsuleWorldCollider(
                    offset=offset,
                    radius=radius,
                    tail=tail,
                    offset_to_tail_diff=offset_to_tail_diff,
                    offset_to_tail_diff_length_squared=offset_to_tail_diff_length_squared,
                )

        if world_collider:
            collider_uuid_to_world_collider[collider.uuid] = world_collider

    collider_group_uuid_to_world_colliders: dict[
        str,
        list[
            Union[
                SphereWorldCollider,
                CapsuleWorldCollider,
                SphereInsideWorldCollider,
                CapsuleInsideWorldCollider,
                PlaneWorldCollider,
            ]
        ],
    ] = {}
    for collider_group in spring_bone1.collider_groups:
        for collider_reference in collider_group.colliders:
            world_collider = collider_uuid_to_world_collider.get(
                collider_reference.collider_uuid
            )
            if world_collider is None:
                continue
            world_colliders = collider_group_uuid_to_world_colliders.get(
                collider_group.uuid
            )
            if world_colliders is None:
                world_colliders = []
                collider_group_uuid_to_world_colliders[collider_group.uuid] = (
                    world_colliders
                )
            world_colliders.append(world_collider)

    for spring in spring_bone1.springs:
        joints = spring.joints
        if not joints:
            continue

        calculate_spring_pose_bone_rotations(
            delta_time,
            obj,
            obj_matrix_world,
            obj_matrix_world_inverted,
            obj_matrix_world_quaternion,
            spring,
            pose_bone_and_rotations,
            collider_group_uuid_to_world_colliders,
        )


def calculate_spring_pose_bone_rotations(
    delta_time: float,
    obj: Object,
    obj_matrix_world: Matrix,
    obj_matrix_world_inverted: Matrix,
    obj_matrix_world_quaternion: Quaternion,
    spring: SpringBone1SpringPropertyGroup,
    pose_bone_and_rotations: list[tuple[PoseBone, Quaternion]],
    collider_group_uuid_to_world_colliders: dict[
        str,
        list[
            Union[
                SphereWorldCollider,
                CapsuleWorldCollider,
                SphereInsideWorldCollider,
                CapsuleInsideWorldCollider,
                PlaneWorldCollider,
            ]
        ],
    ],
) -> None:
    world_collider_groups: Sequence[
        Sequence[
            Union[
                SphereWorldCollider,
                CapsuleWorldCollider,
                SphereInsideWorldCollider,
                CapsuleInsideWorldCollider,
                PlaneWorldCollider,
            ]
        ]
    ] = [
        collider_group_world_colliders
        for collider_group_reference in spring.collider_groups
        if (
            collider_group_world_colliders
            := collider_group_uuid_to_world_colliders.get(
                collider_group_reference.collider_group_uuid
            )
        )
        and collider_group_world_colliders
    ]

    center_pose_bone = obj.pose.bones.get(spring.center.bone_name)
    if center_pose_bone:
        current_center_world_translation = (
            obj_matrix_world @ center_pose_bone.matrix
        ).to_translation()
        previous_center_world_translation = Vector(
            spring.animation_state.previous_center_world_translation
        )
        previous_to_current_center_world_translation = (
            current_center_world_translation - previous_center_world_translation
        )
        if not spring.animation_state.use_center_space:
            spring.animation_state.previous_center_world_translation = (
                current_center_world_translation.copy()
            )
            spring.animation_state.use_center_space = True
    else:
        current_center_world_translation = Vector((0, 0, 0))
        previous_to_current_center_world_translation = Vector((0, 0, 0))
        if spring.animation_state.use_center_space:
            spring.animation_state.use_center_space = False

    for sorted_joint_and_bones in sort_spring_bone_joints(obj, spring.joints):
        joints: list[
            tuple[
                SpringBone1JointPropertyGroup,
                PoseBone,
                Matrix,
            ]
        ] = [
            (
                joint,
                pose_bone,
                pose_bone.bone.convert_local_to_pose(
                    Matrix(), pose_bone.bone.matrix_local
                ),
            )
            for joint, pose_bone in sorted_joint_and_bones
        ]

        # https://github.com/vrm-c/vrm-specification/blob/7279e169ac0dcf37e7d81b2adcad9107101d7e25/specification/VRMC_springBone-1.0/README.md#center-space
        enable_center_space = False
        if center_pose_bone:
            first_pose_bone = next((pose_bone for (_, pose_bone, _) in joints), None)
            ancestor_of_first_pose_bone: Optional[PoseBone] = first_pose_bone
            while ancestor_of_first_pose_bone:
                if center_pose_bone == ancestor_of_first_pose_bone:
                    enable_center_space = True
                    break
                ancestor_of_first_pose_bone = ancestor_of_first_pose_bone.parent

        next_head_pose_bone_before_rotation_matrix = None
        for (
            head_joint,
            head_pose_bone,
            head_rest_object_matrix,
        ), (
            tail_joint,
            tail_pose_bone,
            tail_rest_object_matrix,
        ) in zip(joints, joints[1:]):
            head_tail_parented = False
            searching_tail_parent = tail_pose_bone.parent
            while searching_tail_parent:
                if searching_tail_parent.name == head_pose_bone.name:
                    head_tail_parented = True
                    break
                searching_tail_parent = searching_tail_parent.parent
            if not head_tail_parented:
                break

            (
                head_pose_bone_rotation,
                next_head_pose_bone_before_rotation_matrix,
            ) = calculate_joint_pair_head_pose_bone_rotations(
                delta_time,
                obj_matrix_world,
                obj_matrix_world_inverted,
                obj_matrix_world_quaternion,
                head_joint,
                head_pose_bone,
                head_rest_object_matrix,
                tail_joint,
                tail_pose_bone,
                tail_rest_object_matrix,
                next_head_pose_bone_before_rotation_matrix,
                world_collider_groups,
                previous_to_current_center_world_translation
                if enable_center_space
                else Vector((0, 0, 0)),
            )
            pose_bone_and_rotations.append((head_pose_bone, head_pose_bone_rotation))

    spring.animation_state.previous_center_world_translation = (
        current_center_world_translation
    )


def calculate_joint_pair_head_pose_bone_rotations(
    delta_time: float,
    obj_matrix_world: Matrix,
    obj_matrix_world_inverted: Matrix,
    obj_matrix_world_quaternion: Quaternion,
    head_joint: SpringBone1JointPropertyGroup,
    head_pose_bone: PoseBone,
    current_head_rest_object_matrix: Matrix,
    tail_joint: SpringBone1JointPropertyGroup,
    tail_pose_bone: PoseBone,
    current_tail_rest_object_matrix: Matrix,
    next_head_pose_bone_before_rotation_matrix: Optional[Matrix],
    world_collider_groups: Sequence[
        Sequence[
            Union[
                SphereWorldCollider,
                CapsuleWorldCollider,
                SphereInsideWorldCollider,
                CapsuleInsideWorldCollider,
                PlaneWorldCollider,
            ]
        ]
    ],
    previous_to_current_center_world_translation: Vector,
) -> tuple[Quaternion, Matrix]:
    current_head_pose_bone_matrix = head_pose_bone.matrix
    current_tail_pose_bone_matrix = tail_pose_bone.matrix

    if next_head_pose_bone_before_rotation_matrix is None:
        if head_pose_bone_parent := head_pose_bone.parent:
            current_head_parent_matrix = head_pose_bone_parent.matrix
            current_head_parent_rest_object_matrix = (
                head_pose_bone_parent.bone.convert_local_to_pose(
                    Matrix(), head_pose_bone_parent.bone.matrix_local
                )
            )
            next_head_pose_bone_before_rotation_matrix = current_head_parent_matrix @ (
                current_head_parent_rest_object_matrix.inverted_safe()
                @ current_head_rest_object_matrix
            )
        else:
            next_head_pose_bone_before_rotation_matrix = (
                current_head_rest_object_matrix.copy()
            )
    (
        next_head_pose_bone_translation,
        next_head_parent_pose_bone_object_rotation,
        next_head_pose_bone_scale,
    ) = next_head_pose_bone_before_rotation_matrix.decompose()

    next_head_world_translation = obj_matrix_world @ next_head_pose_bone_translation

    if not tail_joint.animation_state.initialized_as_tail:
        initial_tail_world_translation = (
            obj_matrix_world @ current_tail_pose_bone_matrix
        ).to_translation()
        tail_joint.animation_state.initialized_as_tail = True
        tail_joint.animation_state.previous_world_translation = list(
            initial_tail_world_translation
        )
        tail_joint.animation_state.current_world_translation = list(
            initial_tail_world_translation
        )

    previous_tail_world_translation = (
        Vector(tail_joint.animation_state.previous_world_translation)
        + previous_to_current_center_world_translation
    )
    current_tail_world_translation = (
        Vector(tail_joint.animation_state.current_world_translation)
        + previous_to_current_center_world_translation
    )

    inertia = (current_tail_world_translation - previous_tail_world_translation) * (
        1.0 - head_joint.drag_force
    )

    current_head_rest_object_matrix_inverted = (
        current_head_rest_object_matrix.inverted_safe()
    )
    next_head_rotation_start_target_local_translation = (
        current_head_rest_object_matrix_inverted
        @ current_tail_rest_object_matrix.to_translation()
    )
    stiffness_direction = (
        obj_matrix_world_quaternion
        @ next_head_parent_pose_bone_object_rotation
        @ next_head_rotation_start_target_local_translation
    ).normalized()
    stiffness = stiffness_direction * delta_time * head_joint.stiffness
    external = Vector(head_joint.gravity_dir) * delta_time * head_joint.gravity_power

    next_tail_world_translation = (
        current_tail_world_translation + inertia + stiffness + external
    )

    head_to_tail_world_distance = (
        obj_matrix_world @ current_head_pose_bone_matrix.to_translation()
        - (obj_matrix_world @ current_tail_pose_bone_matrix.to_translation())
    ).length

    # Apply distance constraint to next Tail
    next_tail_world_translation = (
        next_head_world_translation
        + (next_tail_world_translation - next_head_world_translation).normalized()
        * head_to_tail_world_distance
    )
    # Calculate collider collision
    for world_colliders in world_collider_groups:
        for world_collider in world_colliders:
            direction, distance = world_collider.calculate_collision(
                next_tail_world_translation,
                head_joint.hit_radius,
            )
            if distance >= 0:
                continue
            # Push away
            next_tail_world_translation = (
                next_tail_world_translation - direction * distance
            )
            # Apply distance constraint to next Tail
            next_tail_world_translation = (
                next_head_world_translation
                + (
                    next_tail_world_translation - next_head_world_translation
                ).normalized()
                * head_to_tail_world_distance
            )

    next_tail_object_local_translation = (
        obj_matrix_world_inverted @ next_tail_world_translation
    )
    next_head_rotation_end_target_local_translation = (
        next_head_pose_bone_before_rotation_matrix.inverted_safe()
        @ next_tail_object_local_translation
    )

    next_head_pose_bone_rotation = Quaternion(
        next_head_rotation_start_target_local_translation.cross(
            next_head_rotation_end_target_local_translation
        ),
        next_head_rotation_start_target_local_translation.angle(
            next_head_rotation_end_target_local_translation, 0
        ),
    )

    next_head_pose_bone_object_rotation = (
        next_head_parent_pose_bone_object_rotation @ next_head_pose_bone_rotation
    )
    next_head_pose_bone_matrix = (
        Matrix.Translation(next_head_pose_bone_translation)
        @ next_head_pose_bone_object_rotation.to_matrix().to_4x4()
        @ Matrix.Diagonal(next_head_pose_bone_scale).to_4x4()
    )

    next_tail_pose_bone_before_rotation_matrix = (
        next_head_pose_bone_matrix
        @ current_head_rest_object_matrix_inverted
        @ current_tail_rest_object_matrix
    )

    tail_joint.animation_state.previous_world_translation = list(
        current_tail_world_translation
    )
    tail_joint.animation_state.current_world_translation = list(
        next_tail_world_translation
    )

    return (
        next_head_pose_bone_rotation
        if head_pose_bone.bone.use_inherit_rotation
        else next_head_pose_bone_object_rotation,
        next_tail_pose_bone_before_rotation_matrix,
    )


@persistent
def depsgraph_update_pre(_unused: object) -> None:
    context = bpy.context

    state.reset(context)


@persistent
def frame_change_pre(_unused: object) -> None:
    context = bpy.context

    fps = Decimal(context.scene.render.fps)
    last_fps = state.last_fps
    fps_base = Decimal(context.scene.render.fps_base)
    last_fps_base = state.last_fps_base
    if (
        last_fps_base is None
        or (fps_base - last_fps_base).copy_abs() > 0.00001
        or fps != last_fps
    ):
        state.reset(context)

    state.frame_count += 1

    # If the current time is future than the next SpringBone calculation
    # time, move the SpringBone
    # To minimize floating-point rounding errors, multiply numerator by
    # common denominator to minimize decimal handling
    frame_time_x_60_x_fps = state.frame_count * Decimal(60) * fps_base
    while True:
        next_spring_bone_60_fps_update_count = (
            state.spring_bone_60_fps_update_count + Decimal(1)
        )

        next_spring_bone_update_time_x_60_x_fps = (
            next_spring_bone_60_fps_update_count * fps
        )
        if next_spring_bone_update_time_x_60_x_fps > frame_time_x_60_x_fps:
            break

        # To accumulate float rounding errors, don't hardcode delta_time as 1.0/60.0
        # Use the difference between previous and next times
        next_spring_bone_update_time = next_spring_bone_60_fps_update_count / Decimal(
            60
        )
        current_spring_bone_update_time = (
            state.spring_bone_60_fps_update_count / Decimal(60)
        )
        delta_time = float(next_spring_bone_update_time) - float(
            current_spring_bone_update_time
        )
        update_pose_bone_rotations(context, delta_time)

        state.spring_bone_60_fps_update_count += 1


def sort_spring_bone_joints(
    obj: Object, joints: CollectionPropertyProtocol[SpringBone1JointPropertyGroup]
) -> Sequence[Iterable[tuple[SpringBone1JointPropertyGroup, PoseBone]]]:
    bones = obj.pose.bones

    # Check if it's sorted and return as-is if already sorted.
    # This is logically unnecessary but done for simulation efficiency.
    already_sorted = True
    sorted_pose_bones: list[PoseBone] = []
    for joint in joints:
        joint_bone = bones.get(joint.node.bone_name)
        if not joint_bone:
            already_sorted = False
            break
        if not sorted_pose_bones:
            sorted_pose_bones.append(joint_bone)
            continue
        parent_bone = sorted_pose_bones[-1]
        sorted_pose_bones.append(joint_bone)

        traversing_bone = joint_bone.parent
        connected = False
        while traversing_bone:
            if traversing_bone == parent_bone:
                connected = True
                break
            traversing_bone = traversing_bone.parent
        if not connected:
            already_sorted = False
            break

    if already_sorted:
        return [zip(joints, sorted_pose_bones)]

    # Perform sorting
    chains = list[list[tuple[SpringBone1JointPropertyGroup, PoseBone]]]()
    for joint in joints:
        joint_bone = bones.get(joint.node.bone_name)
        if not joint_bone:
            continue

        if not chains:
            chains.append([(joint, joint_bone)])
            continue

        # Skip if already registered in chain
        if any(joint_bone == bone for chain in chains for _, bone in chain):
            continue

        # If ancestor of chain head, or descendant of chain tail,
        # or descendant of chain head and ancestor of chain tail,
        # add to that chain
        # Otherwise, create a new chain
        assigned = False
        for chain in chains:
            if not chain:
                # This should not happen
                continue

            # Check if it's an ancestor of the chain head
            _, chain_head_bone = chain[0]
            traversing_bone = chain_head_bone.parent
            assigned = False
            while traversing_bone:
                if traversing_bone == joint_bone:
                    chain.insert(0, (joint, joint_bone))
                    assigned = True
                    break
                traversing_bone = traversing_bone.parent
            if assigned:
                break

            # Check if it's an ancestor of the chain tail
            _, chain_tail_bone = chain[-1]
            traversing_bone = joint_bone.parent
            assigned = False
            while traversing_bone:
                if traversing_bone == chain_tail_bone:
                    chain.append((joint, joint_bone))
                    assigned = True
                    break
                traversing_bone = traversing_bone.parent
            if assigned:
                break

            # Check if it's a descendant of the chain head and ancestor of
            # the chain tail
            assigned = False
            for i in range(len(chain) - 1):
                _, chain_parent_bone = chain[i]
                _, chain_child_bone = chain[i + 1]

                traversing_bone = chain_child_bone.parent
                while traversing_bone:
                    if traversing_bone == joint_bone:
                        chain.insert(i + 1, (joint, joint_bone))
                        assigned = True
                        break
                    if traversing_bone == chain_parent_bone:
                        break
                    traversing_bone = traversing_bone.parent
                if assigned:
                    break
            if assigned:
                break

        if not assigned:
            chains.append([(joint, joint_bone)])

    return chains
