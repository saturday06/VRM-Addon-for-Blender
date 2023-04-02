import datetime
import logging
import math
from dataclasses import dataclass
from sys import float_info
from typing import Callable, Dict, List, Optional, Tuple, Union

import bpy
from bpy.app.handlers import persistent
from mathutils import Matrix, Quaternion, Vector

from ...common.logging import get_logger
from .property_group import (
    SpringBone1ColliderPropertyGroup,
    SpringBone1JointPropertyGroup,
    SpringBone1SpringPropertyGroup,
)

logger = get_logger(__name__)

if not persistent:  # for fake-bpy-modules

    def persistent(_func: Callable[[object], None]) -> Callable[[object], None]:
        raise NotImplementedError


@dataclass
class State:
    previous_datetime: Optional[datetime.datetime] = None


state = State()


@dataclass(frozen=True)
class SphereWorldCollider:
    offset: Vector
    radius: float

    def calculate_collision(
        self, target: Vector, target_radius: float
    ) -> Tuple[Vector, float]:
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

    def calculate_collision(
        self, target: Vector, target_radius: float
    ) -> Tuple[Vector, float]:
        fallback_result = (Vector((0, 0, -1)), -0.01)

        # offset側との球とターゲットが同一座標の場合
        offset_to_target_diff = target - self.offset
        offset_to_target_diff_length = offset_to_target_diff.length
        if offset_to_target_diff_length < float_info.epsilon:
            return fallback_result

        # tail側との球とターゲットが同一座標の場合
        tail_to_target_diff = target - self.tail
        tail_to_target_diff_length = tail_to_target_diff.length
        if tail_to_target_diff_length < float_info.epsilon:
            return fallback_result

        normalized_offset_to_target_diff = (
            offset_to_target_diff / offset_to_target_diff_length
        )

        # offsetとtailが同一座標の場合
        offset_to_tail_diff = self.tail - self.offset
        offset_to_tail_diff_length = offset_to_tail_diff.length
        if offset_to_tail_diff_length < float_info.epsilon:
            # 代わりにoffset側の球との衝突判定をする
            return (
                normalized_offset_to_target_diff,
                offset_to_target_diff_length - target_radius - self.radius,
            )

        normalized_offset_to_tail_diff = (
            offset_to_tail_diff / offset_to_tail_diff_length
        )

        # offset側の球との衝突判定
        offset_cos = normalized_offset_to_target_diff.dot(
            normalized_offset_to_tail_diff
        )
        if offset_cos < 0:
            return (
                normalized_offset_to_target_diff,
                offset_to_target_diff_length - target_radius - self.radius,
            )

        # tail側の球との衝突判定
        normalized_tail_to_target_diff = (
            tail_to_target_diff / tail_to_target_diff_length
        )
        tail_cos = normalized_tail_to_target_diff.dot(-normalized_offset_to_tail_diff)
        if tail_cos < 0:
            return (
                normalized_tail_to_target_diff,
                tail_to_target_diff_length - target_radius - self.radius,
            )

        # 線分との衝突判定
        offset_to_perpendicular = (
            normalized_offset_to_tail_diff * offset_to_target_diff_length * offset_cos
        )
        perpendicular_to_target = offset_to_target_diff - offset_to_perpendicular
        perpendicular_to_target_length = perpendicular_to_target.length
        if perpendicular_to_target_length < float_info.epsilon:
            return fallback_result

        return (
            perpendicular_to_target / perpendicular_to_target_length,
            perpendicular_to_target_length - target_radius - self.radius,
        )


def dump(v: Union[Matrix, Vector, Quaternion, float, int]) -> str:
    if logger.level > logging.DEBUG:
        return "(omit)"

    if isinstance(v, (float, int)):
        return str(v)

    if isinstance(v, Matrix):
        t, r, s = v.decompose()
        return f"Matrix(T={dump(t)},R={dump(r)},S={dump(s)})"

    if isinstance(v, Vector):
        return f"({v.x:.3f},{v.y:.3f},{v.z:.3f})"

    x, y, z = [round(math.degrees(xyz)) for xyz in v.to_euler("XYZ")[:]]
    return f"Euler({x},{y},{z})"


# https://github.com/vrm-c/vrm-specification/tree/993a90a5bda9025f3d9e2923ad6dea7506f88553/specification/VRMC_springBone-1.0#update-procedure
def update_pose_bone_rotations(delta_time: float) -> None:
    pose_bone_and_rotation_differences: List[Tuple[bpy.types.PoseBone, Quaternion]] = []

    for obj in bpy.data.objects:
        calculate_object_pose_bone_rotation_differences(
            delta_time, obj, pose_bone_and_rotation_differences
        )

    for pose_bone, pose_bone_rotation_difference in pose_bone_and_rotation_differences:
        if pose_bone.rotation_mode != "QUATERNION":
            pose_bone.rotation_mode = "QUATERNION"
        _axis, angle = pose_bone_rotation_difference.to_axis_angle()
        if abs(angle) < float_info.epsilon:
            continue
        pose_bone.rotation_quaternion.rotate(pose_bone_rotation_difference)


def calculate_object_pose_bone_rotation_differences(
    delta_time: float,
    obj: bpy.types.Object,
    pose_bone_and_rotation_differences: List[Tuple[bpy.types.PoseBone, Quaternion]],
) -> None:
    if obj.type != "ARMATURE":
        return
    ext = obj.data.vrm_addon_extension
    if not ext.is_vrm1():
        return
    spring_bone1 = ext.spring_bone1
    if not spring_bone1.enable_animation:
        return

    collider_uuid_to_world_collider: Dict[
        str, Union[SphereWorldCollider, CapsuleWorldCollider]
    ] = {}
    for collider in spring_bone1.colliders:
        pose_bone = obj.pose.bones.get(collider.node.value)
        if not pose_bone:
            continue
        pose_bone_world_matrix = obj.matrix_world @ pose_bone.matrix

        if collider.shape_type == SpringBone1ColliderPropertyGroup.SHAPE_TYPE_SPHERE:
            offset = pose_bone_world_matrix @ Vector(collider.shape.sphere.offset)
            radius = collider.shape.sphere.radius
            collider_uuid_to_world_collider[collider.uuid] = SphereWorldCollider(
                offset=offset,
                radius=radius,
            )
        elif collider.shape_type == SpringBone1ColliderPropertyGroup.SHAPE_TYPE_CAPSULE:
            offset = pose_bone_world_matrix @ Vector(collider.shape.capsule.offset)
            tail = pose_bone_world_matrix @ Vector(collider.shape.capsule.tail)
            radius = collider.shape.sphere.radius
            collider_uuid_to_world_collider[collider.uuid] = CapsuleWorldCollider(
                offset=offset,
                radius=radius,
                tail=tail,
            )

    collider_group_uuid_to_world_colliders: Dict[
        str, List[Union[SphereWorldCollider, CapsuleWorldCollider]]
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
                collider_group_uuid_to_world_colliders[
                    collider_group.uuid
                ] = world_colliders
            world_colliders.append(world_collider)

    for spring in spring_bone1.springs:
        calculate_spring_pose_bone_rotation_differences(
            delta_time,
            obj,
            spring,
            pose_bone_and_rotation_differences,
            collider_group_uuid_to_world_colliders,
        )


def calculate_spring_pose_bone_rotation_differences(
    delta_time: float,
    obj: bpy.types.Object,
    spring: SpringBone1SpringPropertyGroup,
    pose_bone_and_rotation_differences: List[Tuple[bpy.types.PoseBone, Quaternion]],
    collider_group_uuid_to_world_colliders: Dict[
        str, List[Union[SphereWorldCollider, CapsuleWorldCollider]]
    ],
) -> None:
    inputs: List[
        Tuple[
            SpringBone1JointPropertyGroup,
            bpy.types.PoseBone,
            SpringBone1JointPropertyGroup,
            bpy.types.PoseBone,
        ]
    ] = []
    for head_joint, tail_joint in zip(spring.joints, spring.joints[1:]):
        head_bone_name = head_joint.node.value
        head_pose_bone = obj.pose.bones.get(head_bone_name)
        if not head_pose_bone:
            continue

        tail_bone_name = tail_joint.node.value
        tail_pose_bone = obj.pose.bones.get(tail_bone_name)
        if not tail_pose_bone:
            continue

        head_tail_parented = False
        searching_tail_parent = tail_pose_bone.parent
        while searching_tail_parent:
            if searching_tail_parent.name == head_bone_name:
                head_tail_parented = True
                break
            searching_tail_parent = searching_tail_parent.parent
        if not head_tail_parented:
            logger.error(f'"{head_bone_name}" and "{tail_bone_name}" are not parented')
            return

        inputs.append((head_joint, head_pose_bone, tail_joint, tail_pose_bone))

    world_colliders: List[Union[SphereWorldCollider, CapsuleWorldCollider]] = []
    for collider_group_reference in spring.collider_groups:
        collider_group_world_colliders = collider_group_uuid_to_world_colliders.get(
            collider_group_reference.collider_group_uuid
        )
        if not collider_group_world_colliders:
            continue
        world_colliders.extend(collider_group_world_colliders)

    next_head_pose_bone_before_rotation_matrix = None
    for head_joint, head_pose_bone, tail_joint, tail_pose_bone in inputs:
        if next_head_pose_bone_before_rotation_matrix is None:
            next_head_pose_bone_before_rotation_matrix = head_pose_bone.matrix

        (
            head_pose_bone_rotation_difference,
            next_head_pose_bone_before_rotation_matrix,
        ) = calculate_joint_pair_head_pose_bone_rotation_differences(
            delta_time,
            obj,
            head_joint,
            head_pose_bone,
            tail_joint,
            tail_pose_bone,
            next_head_pose_bone_before_rotation_matrix,
            head_pose_bone.matrix,
            tail_pose_bone.matrix,
            world_colliders,
        )
        pose_bone_and_rotation_differences.append(
            (head_pose_bone, head_pose_bone_rotation_difference)
        )


def calculate_joint_pair_head_pose_bone_rotation_differences(
    delta_time: float,
    obj: bpy.types.Object,
    head_joint: SpringBone1JointPropertyGroup,
    head_pose_bone: bpy.types.PoseBone,
    tail_joint: SpringBone1JointPropertyGroup,
    tail_pose_bone: bpy.types.PoseBone,
    next_head_pose_bone_before_rotation_matrix: Matrix,
    current_head_pose_bone_matrix: Matrix,
    current_tail_pose_bone_matrix: Matrix,
    world_colliders: List[Union[SphereWorldCollider, CapsuleWorldCollider]],
) -> Tuple[Quaternion, Matrix]:
    logger.debug(f"=== {head_pose_bone.name} -> {tail_pose_bone.name} ===")
    logger.debug(f"delta time={delta_time}")

    next_head_world_translation = (
        obj.matrix_world @ next_head_pose_bone_before_rotation_matrix.to_translation()
    )

    if not tail_joint.state.initialized_as_tail:
        initial_tail_world_translation = (
            obj.matrix_world @ current_tail_pose_bone_matrix
        ).to_translation()
        tail_joint.state.initialized_as_tail = True
        tail_joint.state.previous_world_translation = list(
            initial_tail_world_translation
        )
        tail_joint.state.current_world_translation = list(
            initial_tail_world_translation
        )

    previous_tail_world_translation = Vector(
        tail_joint.state.previous_world_translation
    )
    current_tail_world_translation = Vector(tail_joint.state.current_world_translation)

    inertia = (current_tail_world_translation - previous_tail_world_translation) * (
        1.0 - head_joint.drag_force
    )

    current_head_rest_object_matrix = head_pose_bone.bone.convert_local_to_pose(
        Matrix(), head_pose_bone.bone.matrix_local
    )
    logger.debug(
        f"headのconvert_local_to_poseの結果={dump(current_head_rest_object_matrix)}"
    )
    current_tail_rest_object_matrix = tail_pose_bone.bone.convert_local_to_pose(
        Matrix(), tail_pose_bone.bone.matrix_local
    )
    logger.debug(
        f"tailのconvert_local_to_poseの結果={dump(current_tail_rest_object_matrix)}"
    )
    current_head_to_tail_rest_object_translation = (
        current_tail_rest_object_matrix.to_translation()
        - current_head_rest_object_matrix.to_translation()
    )
    logger.debug(
        f"head=>tailのconvert_local_to_poseの結果={dump(current_head_to_tail_rest_object_translation)}"
    )
    stiffness_direction = (
        obj.matrix_world.to_quaternion() @ current_head_to_tail_rest_object_translation
    ).normalized()
    stiffness = stiffness_direction * delta_time * head_joint.stiffness
    logger.debug(f"オブジェクトワールド位置={dump(obj.matrix_world.to_translation())}")
    logger.debug(f"オブジェクト回転={dump(obj.matrix_world.to_quaternion())}")
    logger.debug(f"Headボーンまでの回転={dump(head_pose_bone.matrix.to_quaternion())}")
    logger.debug(f"Stiffness Direction={dump(stiffness_direction)}")
    logger.debug(f"Stiffness Force={dump(stiffness)}")
    external = delta_time * Vector(head_joint.gravity_dir) * head_joint.gravity_power

    next_tail_world_translation = (
        current_tail_world_translation + inertia + stiffness + external
    )
    logger.debug(f"ワールド重力={dump(external)}")
    logger.debug(
        f"前のTailのワールド位置={dump(Vector(tail_joint.state.previous_world_translation))}"
    )
    logger.debug(
        f"現在のTailのワールド位置={dump(Vector(tail_joint.state.current_world_translation))}"
    )
    logger.debug(f"慣性力系数={dump(1.0 - head_joint.drag_force)}")
    logger.debug(f"慣性力={dump(inertia)}")
    logger.debug(f"次のTailの重力増加分ワールド位置={dump(next_tail_world_translation)}")
    head_tail_world_distance = (
        current_head_pose_bone_matrix.to_translation()
        - current_tail_pose_bone_matrix.to_translation()
    ).length
    logger.debug(f"HeadとTailの距離={dump(head_tail_world_distance)}")
    logger.debug(f"次のHeadのワールド位置={dump(next_head_world_translation)}")

    # 次のTailに距離の制約を適用
    next_tail_world_translation = (
        next_head_world_translation
        + (next_tail_world_translation - next_head_world_translation).normalized()
        * head_tail_world_distance
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
            * head_tail_world_distance
        )

    logger.debug(f"次のTailのワールド座標={dump(next_tail_world_translation)}")
    next_tail_object_local_translation = (
        obj.matrix_world.inverted_safe() @ next_tail_world_translation
    )
    logger.debug(f"次のTailのオブジェクト座標={dump(next_tail_object_local_translation)}")
    next_head_rotation_start_target_local_translation = (
        current_head_pose_bone_matrix.inverted_safe()
        @ current_tail_pose_bone_matrix.to_translation()
    )
    logger.debug(
        f"次のHeadの回転前ターゲットローカル座標={dump(next_head_rotation_start_target_local_translation)}"
    )
    next_head_rotation_end_target_local_translation = (
        next_head_pose_bone_before_rotation_matrix.inverted_safe()
        @ next_tail_object_local_translation
    )
    logger.debug(
        f"次のHeadの回転後ターゲットローカル座標={dump(next_head_rotation_end_target_local_translation)}"
    )

    head_pose_bone_rotation_difference = Quaternion(
        next_head_rotation_start_target_local_translation.cross(
            next_head_rotation_end_target_local_translation
        ),
        next_head_rotation_start_target_local_translation.angle(
            next_head_rotation_end_target_local_translation, 0
        ),
    )
    logger.debug(f"q={dump(head_pose_bone_rotation_difference)}")
    next_head_pose_bone_matrix = (
        next_head_pose_bone_before_rotation_matrix
        @ head_pose_bone_rotation_difference.to_matrix().to_4x4()
    )

    next_tail_pose_bone_before_rotation_matrix = (
        next_head_pose_bone_matrix
        @ current_head_pose_bone_matrix.inverted_safe()
        @ current_tail_pose_bone_matrix
    )
    logger.debug(f"現在のTailポーズボーン行列={dump(current_tail_pose_bone_matrix)}")
    logger.debug(
        f"次の未回転Tailポーズボーン行列={dump(next_tail_pose_bone_before_rotation_matrix)}"
    )
    logger.debug(f"次のHeadポーズボーン行列={dump(next_head_pose_bone_matrix)}")

    tail_joint.state.previous_world_translation = list(
        tail_joint.state.current_world_translation
    )
    tail_joint.state.current_world_translation = list(
        obj.matrix_world @ next_tail_pose_bone_before_rotation_matrix.to_translation()
    )

    return (
        head_pose_bone_rotation_difference,
        next_tail_pose_bone_before_rotation_matrix,
    )


@persistent  # type: ignore[misc]
def depsgraph_update_pre(_dummy: object) -> None:
    state.previous_datetime = None


@persistent  # type: ignore[misc]
def frame_change_pre(_dummy: object) -> None:
    now = datetime.datetime.now()
    previous_datetime = state.previous_datetime
    if previous_datetime is None:
        delta_time = float(bpy.context.scene.render.fps_base) / float(
            bpy.context.scene.render.fps
        )
    else:
        delta_time = (now - previous_datetime).total_seconds()
    state.previous_datetime = now

    update_pose_bone_rotations(delta_time)
