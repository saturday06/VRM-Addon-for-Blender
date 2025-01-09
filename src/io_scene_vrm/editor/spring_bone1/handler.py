# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
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
    offset_to_tail_diff: Vector  # ゼロベクトル以外の値にする必要がある
    offset_to_tail_diff_length_squared: float  # ゼロ以上の値にする必要がある

    def calculate_collision(
        self, target: Vector, target_radius: float
    ) -> tuple[Vector, float]:
        offset_to_target_diff = target - self.offset

        # offsetとtailを含む直線上で、targetまでの最短の点を
        # self.offset + (self.tail - self.offset) * offset_to_tail_ratio_for_nearest
        # という式で表すためのoffset_to_tail_ratio_for_nearestを求める
        offset_to_tail_ratio_for_nearest = (
            self.offset_to_tail_diff.dot(offset_to_target_diff)
            / self.offset_to_tail_diff_length_squared
        )

        # offsetからtailまでの線分の始点が0で終点が1なので、範囲外は切り取る
        offset_to_tail_ratio_for_nearest = max(
            0, min(1, offset_to_tail_ratio_for_nearest)
        )

        # targetまでの最短の点を計算
        nearest = (
            self.offset + self.offset_to_tail_diff * offset_to_tail_ratio_for_nearest
        )

        # 衝突判定
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
    offset_to_tail_diff: Vector  # ゼロベクトル以外の値にする必要がある
    offset_to_tail_diff_length_squared: float  # ゼロ以上の値にする必要がある

    def calculate_collision(
        self, target: Vector, target_radius: float
    ) -> tuple[Vector, float]:
        offset_to_target_diff = target - self.offset

        # offsetとtailを含む直線上で、targetまでの最短の点を
        # self.offset + (self.tail - self.offset) * offset_to_tail_ratio_for_nearest
        # という式で表すためのoffset_to_tail_ratio_for_nearestを求める
        offset_to_tail_ratio_for_nearest = (
            self.offset_to_tail_diff.dot(offset_to_target_diff)
            / self.offset_to_tail_diff_length_squared
        )

        # offsetからtailまでの線分の始点が0で終点が1なので、範囲外は切り取る
        offset_to_tail_ratio_for_nearest = max(
            0, min(1, offset_to_tail_ratio_for_nearest)
        )

        # targetまでの最短の点を計算
        nearest = (
            self.offset + self.offset_to_tail_diff * offset_to_tail_ratio_for_nearest
        )

        # 衝突判定
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
        # pose_boneへの回転の代入は負荷が高いのでできるだけ実行しない
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
        pose_bone_world_matrix = obj.matrix_world @ pose_bone.matrix

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
                    # offsetとtailの位置が同じ場合はスフィアコライダーにする
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
                # offsetとtailの位置が同じ場合はスフィアコライダーにする
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
        first_joint = joints[0]
        first_pose_bone = obj.pose.bones.get(first_joint.node.bone_name)
        if not first_pose_bone:
            continue

        center_pose_bone = obj.pose.bones.get(spring.center.bone_name)

        # https://github.com/vrm-c/vrm-specification/blob/7279e169ac0dcf37e7d81b2adcad9107101d7e25/specification/VRMC_springBone-1.0/README.md#center-space
        center_pose_bone_is_ancestor_of_first_pose_bone = False
        ancestor_of_first_pose_bone: Optional[PoseBone] = first_pose_bone
        while ancestor_of_first_pose_bone:
            if center_pose_bone == ancestor_of_first_pose_bone:
                center_pose_bone_is_ancestor_of_first_pose_bone = True
                break
            ancestor_of_first_pose_bone = ancestor_of_first_pose_bone.parent
        if not center_pose_bone_is_ancestor_of_first_pose_bone:
            center_pose_bone = None

        if center_pose_bone:
            current_center_world_translation = (
                obj.matrix_world @ center_pose_bone.matrix
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

        calculate_spring_pose_bone_rotations(
            delta_time,
            obj,
            spring,
            pose_bone_and_rotations,
            collider_group_uuid_to_world_colliders,
            previous_to_current_center_world_translation,
        )

        spring.animation_state.previous_center_world_translation = (
            current_center_world_translation
        )


def calculate_spring_pose_bone_rotations(
    delta_time: float,
    obj: Object,
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
    previous_to_current_center_world_translation: Vector,
) -> None:
    inputs: list[
        tuple[
            SpringBone1JointPropertyGroup,
            PoseBone,
            Matrix,
            SpringBone1JointPropertyGroup,
            PoseBone,
            Matrix,
        ]
    ] = []

    joints: list[
        tuple[
            SpringBone1JointPropertyGroup,
            PoseBone,
            Matrix,
        ]
    ] = []
    for joint in spring.joints:
        bone_name = joint.node.bone_name
        pose_bone = obj.pose.bones.get(bone_name)
        if not pose_bone:
            continue
        rest_object_matrix = pose_bone.bone.convert_local_to_pose(
            Matrix(), pose_bone.bone.matrix_local
        )
        joints.append((joint, pose_bone, rest_object_matrix))

    for (head_joint, head_pose_bone, head_rest_object_matrix), (
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

        inputs.append(
            (
                head_joint,
                head_pose_bone,
                head_rest_object_matrix,
                tail_joint,
                tail_pose_bone,
                tail_rest_object_matrix,
            )
        )

    world_colliders: list[
        Union[
            SphereWorldCollider,
            CapsuleWorldCollider,
            SphereInsideWorldCollider,
            CapsuleInsideWorldCollider,
            PlaneWorldCollider,
        ]
    ] = []
    for collider_group_reference in spring.collider_groups:
        collider_group_world_colliders = collider_group_uuid_to_world_colliders.get(
            collider_group_reference.collider_group_uuid
        )
        if not collider_group_world_colliders:
            continue
        world_colliders.extend(collider_group_world_colliders)

    next_head_pose_bone_before_rotation_matrix = None
    for (
        head_joint,
        head_pose_bone,
        head_rest_object_matrix,
        tail_joint,
        tail_pose_bone,
        tail_rest_object_matrix,
    ) in inputs:
        (
            head_pose_bone_rotation,
            next_head_pose_bone_before_rotation_matrix,
        ) = calculate_joint_pair_head_pose_bone_rotations(
            delta_time,
            obj,
            head_joint,
            head_pose_bone,
            head_rest_object_matrix,
            tail_joint,
            tail_pose_bone,
            tail_rest_object_matrix,
            next_head_pose_bone_before_rotation_matrix,
            world_colliders,
            previous_to_current_center_world_translation,
        )
        pose_bone_and_rotations.append((head_pose_bone, head_pose_bone_rotation))


def calculate_joint_pair_head_pose_bone_rotations(
    delta_time: float,
    obj: Object,
    head_joint: SpringBone1JointPropertyGroup,
    head_pose_bone: PoseBone,
    current_head_rest_object_matrix: Matrix,
    tail_joint: SpringBone1JointPropertyGroup,
    tail_pose_bone: PoseBone,
    current_tail_rest_object_matrix: Matrix,
    next_head_pose_bone_before_rotation_matrix: Optional[Matrix],
    world_colliders: list[
        Union[
            SphereWorldCollider,
            CapsuleWorldCollider,
            SphereInsideWorldCollider,
            CapsuleInsideWorldCollider,
            PlaneWorldCollider,
        ]
    ],
    previous_to_current_center_world_translation: Vector,
) -> tuple[Quaternion, Matrix]:
    current_head_pose_bone_matrix = head_pose_bone.matrix
    current_tail_pose_bone_matrix = tail_pose_bone.matrix

    if next_head_pose_bone_before_rotation_matrix is None:
        if head_pose_bone.parent:
            current_head_parent_matrix = head_pose_bone.parent.matrix
            current_head_parent_rest_object_matrix = (
                head_pose_bone.parent.bone.convert_local_to_pose(
                    Matrix(), head_pose_bone.parent.bone.matrix_local
                )
            )
        else:
            current_head_parent_matrix = Matrix()
            current_head_parent_rest_object_matrix = Matrix()
        next_head_pose_bone_before_rotation_matrix = current_head_parent_matrix @ (
            current_head_parent_rest_object_matrix.inverted_safe()
            @ current_head_rest_object_matrix
        )

    next_head_world_translation = (
        obj.matrix_world @ next_head_pose_bone_before_rotation_matrix.to_translation()
    )

    if not tail_joint.animation_state.initialized_as_tail:
        initial_tail_world_translation = (
            obj.matrix_world @ current_tail_pose_bone_matrix
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

    next_head_rotation_start_target_local_translation = (
        current_head_rest_object_matrix.inverted_safe()
        @ current_tail_rest_object_matrix.to_translation()
    )
    stiffness_direction = (
        obj.matrix_world.to_quaternion()
        @ next_head_pose_bone_before_rotation_matrix.to_quaternion()
        @ next_head_rotation_start_target_local_translation
    ).normalized()
    stiffness = stiffness_direction * delta_time * head_joint.stiffness
    external = Vector(head_joint.gravity_dir) * delta_time * head_joint.gravity_power

    next_tail_world_translation = (
        current_tail_world_translation + inertia + stiffness + external
    )

    head_to_tail_world_distance = (
        obj.matrix_world @ current_head_pose_bone_matrix.to_translation()
        - (obj.matrix_world @ current_tail_pose_bone_matrix.to_translation())
    ).length

    # 次のTailに距離の制約を適用
    next_tail_world_translation = (
        next_head_world_translation
        + (next_tail_world_translation - next_head_world_translation).normalized()
        * head_to_tail_world_distance
    )
    # コライダーの衝突を計算
    for world_collider in world_colliders:
        direction, distance = world_collider.calculate_collision(
            next_tail_world_translation,
            head_joint.hit_radius,
        )
        if distance >= 0:
            continue
        # 押しのける
        next_tail_world_translation = next_tail_world_translation - direction * distance
        # 次のTailに距離の制約を適用
        next_tail_world_translation = (
            next_head_world_translation
            + (next_tail_world_translation - next_head_world_translation).normalized()
            * head_to_tail_world_distance
        )

    next_tail_object_local_translation = (
        obj.matrix_world.inverted_safe() @ next_tail_world_translation
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

    (
        next_head_pose_bone_translation,
        next_head_parent_pose_bone_object_rotation,
        next_head_pose_bone_scale,
    ) = next_head_pose_bone_before_rotation_matrix.decompose()
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
        @ current_head_rest_object_matrix.inverted_safe()
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

    # 現在時刻が次回のSpringBoneの計算時刻よりも未来なら、SpringBoneを動かす
    # 浮動小数点の丸め誤差を最小限にするため、共通の分母を分子に掛け算することで
    # 少数の扱いを最小限にしている
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

        # floatの丸め誤差の積算を行うため、delta_timeは 1.0/60.0 を決め打ちせず
        # 前後の時刻の差分を使う
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
