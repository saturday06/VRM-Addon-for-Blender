# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import time
import contextlib
import bpy
from bpy.app.handlers import persistent
from ...common.logger import get_logger
from .property_group import (
    Vrm0BlendShapeGroupPropertyGroup,
)
from mathutils import Matrix, Quaternion, Vector
from sys import float_info
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional, Any, Union
from ...common.rotation import (
    get_rotation_as_quaternion,
    set_rotation_without_mode_change,
)
from bpy.types import Armature, Context, Object, PoseBone, WindowManager  # type: ignore[attr-defined]
from ..extension import get_armature_extension

_logger = get_logger(__name__)

# Global dictionaries for animation state and temporary bone tracking.
joint_animation_states: dict[
    str, "JointAnimationState"
] = {}  # Keys: "<object.name>:<pose_bone.name>"
temp_bones_created_dict: dict[
    str, dict[str, str]
] = {}  # Keys: object.name -> dict(original_bone_name: temp_bone_name)

# Global flag to track modal operator state (use lowercase for mutable state)
vrm0_modal_running: bool = False


# JointAnimationState mimics VRM1’s animation state structure.
class JointAnimationState:
    def __init__(self, world_translation: Vector) -> None:
        self.initialized_as_tail: bool = False
        self.previous_world_translation: list[float] = list(world_translation)
        self.current_world_translation: list[float] = list(world_translation)


def create_joint_animation_state(
    obj: Object, pose_bone: PoseBone
) -> JointAnimationState:
    world_translation = (obj.matrix_world @ pose_bone.matrix).to_translation()
    return JointAnimationState(world_translation)


# --- Collider Dataclasses ---
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
    offset_to_tail_diff: Vector
    offset_to_tail_diff_length_squared: float

    def calculate_collision(
        self, target: Vector, target_radius: float
    ) -> tuple[Vector, float]:
        offset_to_target_diff = target - self.offset
        ratio = (
            self.offset_to_tail_diff.dot(offset_to_target_diff)
            / self.offset_to_tail_diff_length_squared
        )
        ratio = max(0, min(1, ratio))
        nearest = self.offset + self.offset_to_tail_diff * ratio
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
    offset_to_tail_diff: Vector
    offset_to_tail_diff_length_squared: float

    def calculate_collision(
        self, target: Vector, target_radius: float
    ) -> tuple[Vector, float]:
        offset_to_target_diff = target - self.offset
        ratio = (
            self.offset_to_tail_diff.dot(offset_to_target_diff)
            / self.offset_to_tail_diff_length_squared
        )
        ratio = max(0, min(1, ratio))
        nearest = self.offset + self.offset_to_tail_diff * ratio
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


@persistent
def frame_change_pre(_unused: object) -> None:
    Vrm0BlendShapeGroupPropertyGroup.frame_change_post_shape_key_updates.clear()
    context = bpy.context
    fps = Decimal(context.scene.render.fps)
    fps_base = Decimal(context.scene.render.fps_base)
    if (fps_base - secondary_anim_state.last_fps_base).copy_abs() > Decimal(
        "0.00001"
    ) or fps != secondary_anim_state.last_fps:
        secondary_anim_state.reset(context)
    if context.screen.is_animation_playing:  # type: ignore[attr-defined]
        current_time = time.time()
        if secondary_anim_state.last_time is None:
            secondary_anim_state.last_time = current_time
            delta_time = 1.0 / 30.0
        else:
            delta_time = current_time - secondary_anim_state.last_time
            secondary_anim_state.last_time = current_time
        update_secondary_animation_bone_rotations(context, delta_time)
    else:
        secondary_anim_state.frame_count += 1
        frame_time = secondary_anim_state.frame_count * Decimal(60) * fps_base
        while True:
            next_update = (
                secondary_anim_state.secondary_anim_60_fps_update_count + Decimal(1)
            )
            if next_update * fps > frame_time:
                break
            next_time = next_update / Decimal(60)
            current_time_val = (
                secondary_anim_state.secondary_anim_60_fps_update_count / Decimal(60)
            )
            delta_time = float(next_time - current_time_val)
            update_secondary_animation_bone_rotations(context, delta_time)
            secondary_anim_state.secondary_anim_60_fps_update_count = next_update


@persistent
def frame_change_post(_unused: object) -> None:
    context = bpy.context

    for (
        (
            shape_key_name,
            key_block_name,
        ),
        value,
    ) in Vrm0BlendShapeGroupPropertyGroup.frame_change_post_shape_key_updates.items():
        shape_key = context.blend_data.shape_keys.get(shape_key_name)
        if not shape_key:
            continue
        key_blocks = shape_key.key_blocks
        if not key_blocks:
            continue
        key_block = key_blocks.get(key_block_name)
        if not key_block:
            continue
        key_block.value = value
    Vrm0BlendShapeGroupPropertyGroup.frame_change_post_shape_key_updates.clear()


# --- Secondary Animation Simulation Code ---
@dataclass
class SecondaryAnimationState:
    frame_count: Decimal = Decimal()
    secondary_anim_60_fps_update_count: Decimal = Decimal()
    last_fps: Decimal = Decimal()
    last_fps_base: Decimal = Decimal()
    last_time: Optional[float] = None

    def reset(self, context: Context) -> None:
        scene = context.scene
        self.frame_count = Decimal(0)
        self.secondary_anim_60_fps_update_count = Decimal(0)
        self.last_fps = Decimal(scene.render.fps)
        self.last_fps_base = Decimal(scene.render.fps_base)
        self.last_time = None


secondary_anim_state = SecondaryAnimationState()


def update_secondary_animation_bone_rotations(
    context: Context, delta_time: float
) -> None:
    pose_bone_and_rotations: list[tuple[PoseBone, Quaternion]] = []
    calculate_object_pose_bone_rotations(delta_time, context, pose_bone_and_rotations)
    for pose_bone, new_rotation in pose_bone_and_rotations:
        angle_diff = new_rotation.rotation_difference(
            get_rotation_as_quaternion(pose_bone)
        ).angle
        if abs(angle_diff) < float_info.epsilon:
            continue
        set_rotation_without_mode_change(pose_bone, new_rotation)


# --- Temporary Bone Management ---
def create_temporary_bones_for_object(obj: Object, sec_anim: Any) -> None:
    global temp_bones_created_dict
    if obj.name in temp_bones_created_dict:
        return
    arm = obj.data
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = arm.edit_bones  # type: ignore[attr-defined]
    created: dict[str, str] = {}
    for group in sec_anim.bone_groups:
        for bone_prop in group.bones:
            if bone_prop.bone_name not in arm.bones:  # type: ignore[attr-defined]
                continue
            bone = arm.bones[bone_prop.bone_name]  # type: ignore[attr-defined]
            if len(bone.children) == 0:  # type: ignore[attr-defined]
                temp_name = "temp_" + bone.name  # type: ignore[attr-defined]
                if temp_name not in edit_bones:
                    new_bone = edit_bones.new(temp_name)  # type: ignore[attr-defined]
                    new_bone.head = bone.tail_local  # type: ignore[attr-defined]
                    new_bone.tail = new_bone.head + (Vector((0, 1, 0)) * bone.length)  # type: ignore[attr-defined]
                    new_bone.parent = edit_bones.get(bone.name)  # type: ignore[attr-defined]
                    new_bone.hide = True
                created[bone.name] = temp_name  # type: ignore[attr-defined]
    bpy.ops.object.mode_set(mode="POSE")
    temp_bones_created_dict[obj.name] = created


def delete_temporary_bones_for_object(obj: Object) -> None:
    global temp_bones_created_dict
    if obj.name not in temp_bones_created_dict:
        return
    arm = obj.data
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = arm.edit_bones  # type: ignore[attr-defined]
    created = temp_bones_created_dict[obj.name]
    for orig, temp_name in created.items():  # type: ignore[attr-defined]
        if temp_name in edit_bones:
            edit_bones.remove(edit_bones[temp_name])  # type: ignore[attr-defined]
    bpy.ops.object.mode_set(mode="POSE")
    del temp_bones_created_dict[obj.name]


def update_temporary_bones(context: Context) -> None:
    for obj in context.blend_data.objects:
        if obj.type != "ARMATURE":
            continue
        armature_data = obj.data
        if not isinstance(armature_data, Armature):
            continue
        ext = get_armature_extension(armature_data)
        if not hasattr(ext, "vrm0") or not hasattr(ext.vrm0, "secondary_animation"):
            continue
        sec_anim = ext.vrm0.secondary_animation
        if getattr(sec_anim, "enable_animation", False):
            create_temporary_bones_for_object(obj, sec_anim)
        else:
            delete_temporary_bones_for_object(obj)


# --- Recursive Chain Builder ---
def build_chains_from_bone(
    bone_prop: Any, pose_bone: PoseBone, obj: Object
) -> list[list[tuple[Any, PoseBone, Matrix]]]:
    rest_object_matrix = pose_bone.bone.convert_local_to_pose(
        Matrix(), pose_bone.bone.matrix_local
    )
    triple = (bone_prop, pose_bone, rest_object_matrix)
    chains: list[list[tuple[Any, PoseBone, Matrix]]] = []
    if not pose_bone.children:
        chains.append([triple])
    else:
        for child in pose_bone.children:
            child_chains = build_chains_from_bone(bone_prop, child, obj)
            for chain in child_chains:
                chains.append([triple] + chain)
    return chains


def calculate_object_pose_bone_rotations(
    delta_time: float,
    context: Context,
    pose_bone_and_rotations: list[tuple[PoseBone, Quaternion]],
) -> None:
    for obj in context.blend_data.objects:
        if obj.type != "ARMATURE":
            continue
        armature_data = obj.data
        if not isinstance(armature_data, Armature):
            continue
        ext = get_armature_extension(armature_data)
        if not hasattr(ext, "vrm0") or not hasattr(ext.vrm0, "secondary_animation"):
            continue
        sec_anim = ext.vrm0.secondary_animation
        if not getattr(sec_anim, "enable_animation", False):
            continue

        collider_group_to_world_colliders: dict[  # type: ignore[attr-defined]
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
        if hasattr(sec_anim, "collider_groups"):
            for collider_group in sec_anim.collider_groups:
                group_colliders: list[Any] = []  # type: ignore[attr-defined]
                for collider in collider_group.colliders:
                    if not collider.bpy_object or not collider.bpy_object.name:
                        continue
                    collider_obj = collider.bpy_object
                    world_matrix = collider_obj.matrix_world
                    offset = world_matrix.to_translation()
                    extended = getattr(collider, "extensions", None)
                    if extended is not None and hasattr(
                        extended, "vrmc_spring_bone_extended_collider"
                    ):
                        ext_col = extended.vrmc_spring_bone_extended_collider
                        if ext_col.enabled:
                            if (
                                ext_col.shape_type
                                == ext_col.SHAPE_TYPE_EXTENDED_SPHERE.identifier
                            ):
                                radius = ext_col.shape.sphere.radius
                                if getattr(ext_col.shape.sphere, "inside", False):
                                    world_coll = SphereInsideWorldCollider(
                                        offset=offset, radius=radius
                                    )
                                else:
                                    world_coll = SphereWorldCollider(
                                        offset=offset, radius=radius
                                    )
                            elif (
                                ext_col.shape_type
                                == ext_col.SHAPE_TYPE_EXTENDED_CAPSULE.identifier
                            ):
                                tail = world_matrix @ Vector(ext_col.shape.capsule.tail)
                                radius = ext_col.shape.sphere.radius
                                offset_to_tail_diff = tail - offset
                                length_sq = offset_to_tail_diff.length_squared
                                if length_sq < float_info.epsilon:
                                    if getattr(ext_col.shape.capsule, "inside", False):
                                        world_coll = SphereInsideWorldCollider(
                                            offset=offset, radius=radius
                                        )
                                    else:
                                        world_coll = SphereWorldCollider(
                                            offset=offset, radius=radius
                                        )
                                else:
                                    if getattr(ext_col.shape.capsule, "inside", False):
                                        world_coll = CapsuleInsideWorldCollider(
                                            offset=offset,
                                            radius=radius,
                                            tail=tail,
                                            offset_to_tail_diff=offset_to_tail_diff,
                                            offset_to_tail_diff_length_squared=length_sq,
                                        )
                                    else:
                                        world_coll = CapsuleWorldCollider(
                                            offset=offset,
                                            radius=radius,
                                            tail=tail,
                                            offset_to_tail_diff=offset_to_tail_diff,
                                            offset_to_tail_diff_length_squared=length_sq,
                                        )
                            elif (
                                ext_col.shape_type
                                == ext_col.SHAPE_TYPE_EXTENDED_PLANE.identifier
                            ):
                                normal = world_matrix.to_quaternion() @ Vector(
                                    ext_col.shape.plane.normal
                                )
                                world_coll = PlaneWorldCollider(
                                    offset=offset, normal=normal
                                )
                            else:
                                if collider_obj.type == "EMPTY":
                                    radius = collider_obj.empty_display_size
                                else:
                                    radius = sum(collider_obj.scale) / 3.0
                                world_coll = SphereWorldCollider(
                                    offset=offset, radius=radius
                                )
                        else:
                            if collider_obj.type == "EMPTY":
                                radius = collider_obj.empty_display_size
                            else:
                                radius = sum(collider_obj.scale) / 3.0
                            world_coll = SphereWorldCollider(
                                offset=offset, radius=radius
                            )
                    else:
                        if collider_obj.type == "EMPTY":
                            radius = collider_obj.empty_display_size
                        else:
                            radius = sum(collider_obj.scale) / 3.0
                        world_coll = SphereWorldCollider(offset=offset, radius=radius)
                    group_colliders.append(world_coll)  # type: ignore[attr-defined]
                if group_colliders:
                    collider_group_to_world_colliders[collider_group.name] = (
                        group_colliders
                    )

        chains_all: list[tuple[Any, list[tuple[Any, PoseBone, Matrix]]]] = []  # type: ignore[attr-defined]
        for group in sec_anim.bone_groups:
            for bone_prop in group.bones:
                pose_bone = obj.pose.bones.get(bone_prop.bone_name)
                if not pose_bone:
                    continue
                built_chains = build_chains_from_bone(bone_prop, pose_bone, obj)  # type: ignore[attr-defined]
                for chain in built_chains:  # type: ignore[attr-defined]
                    chains_all.append((group, chain))  # type: ignore[attr-defined]
        for group in sec_anim.bone_groups:
            if hasattr(group, "center") and group.center:
                center_pose_bone = obj.pose.bones.get(group.center.bone_name)
            else:
                center_pose_bone = None
            if center_pose_bone:
                current_center_world_translation = (
                    obj.matrix_world @ center_pose_bone.matrix
                ).to_translation()
            else:
                current_center_world_translation = Vector((0, 0, 0))
            previous_to_current_center_world_translation = Vector((0, 0, 0))
            if hasattr(group.animation_state, "previous_center_world_translation"):  # type: ignore[attr-defined]
                previous_center = Vector(
                    group.animation_state.previous_center_world_translation  # type: ignore[attr-defined]
                )
                previous_to_current_center_world_translation = (
                    current_center_world_translation - previous_center
                )
            group.animation_state.previous_center_world_translation = (  # type: ignore[attr-defined]
                current_center_world_translation.copy()
            )

            world_colliders: list[Any] = []  # type: ignore[attr-defined]
            if hasattr(group, "collider_groups"):
                for collider_group in group.collider_groups:
                    colliders = collider_group_to_world_colliders.get(  # type: ignore[attr-defined]
                        collider_group.name
                    )
                    if colliders:
                        world_colliders.extend(colliders)  # type: ignore[attr-defined]

            for grp, chain in [entry for entry in chains_all if entry[0] == group]:  # type: ignore[attr-defined]
                if len(chain) == 1:  # type: ignore[attr-defined]
                    head_joint, head_pose_bone, head_rest_object_matrix = chain[0]  # type: ignore[attr-defined]
                    if (
                        obj.name in temp_bones_created_dict
                        and head_pose_bone.name in temp_bones_created_dict[obj.name]  # type: ignore[attr-defined]
                    ):
                        temp_name = temp_bones_created_dict[obj.name][
                            head_pose_bone.name
                        ]
                        temp_pose_bone = obj.pose.bones.get(temp_name)
                        temp_rest_object_matrix = (
                            temp_pose_bone.bone.convert_local_to_pose(  # type: ignore[attr-defined]
                                Matrix(),
                                temp_pose_bone.bone.matrix_local,  # type: ignore[attr-defined]
                            )
                        )
                        chain = [  # type: ignore[attr-defined]
                            chain[0],
                            (None, temp_pose_bone, temp_rest_object_matrix),
                        ]
                    else:
                        continue
                if len(chain) < 2:  # type: ignore[attr-defined]
                    continue
                next_head_pose_bone_before_rotation_matrix: Optional[Matrix] = None
                for i in range(len(chain) - 1):  # type: ignore[attr-defined]
                    head_joint, head_pose_bone, head_rest_object_matrix = chain[i]  # type: ignore[attr-defined]
                    tail_joint, tail_pose_bone, tail_rest_object_matrix = chain[i + 1]  # type: ignore[attr-defined]
                    key_head = f"{obj.name}:{head_pose_bone.name}"  # type: ignore[attr-defined]
                    key_tail = f"{obj.name}:{tail_pose_bone.name}"  # type: ignore[attr-defined]
                    if key_head not in joint_animation_states:
                        joint_animation_states[key_head] = create_joint_animation_state(
                            obj,
                            head_pose_bone,  # type: ignore[attr-defined]
                        )
                    if key_tail not in joint_animation_states:
                        joint_animation_states[key_tail] = create_joint_animation_state(
                            obj,
                            tail_pose_bone,  # type: ignore[attr-defined]
                        )
                    head_joint.animation_state = joint_animation_states[key_head]  # type: ignore[attr-defined]
                    tail_joint.animation_state = joint_animation_states[key_tail]  # type: ignore[attr-defined]
                    head_joint.drag_force = group.drag_force  # type: ignore[attr-defined]
                    head_joint.stiffness = group.stiffiness  # type: ignore[attr-defined]
                    head_joint.gravity_dir = group.gravity_dir  # type: ignore[attr-defined]
                    head_joint.gravity_power = group.gravity_power  # type: ignore[attr-defined]
                    head_joint.hit_radius = group.hit_radius  # type: ignore[attr-defined]
                    tail_joint.drag_force = group.drag_force  # type: ignore[attr-defined]
                    tail_joint.stiffness = group.stiffiness  # type: ignore[attr-defined]
                    tail_joint.gravity_dir = group.gravity_dir  # type: ignore[attr-defined]
                    tail_joint.gravity_power = group.gravity_power  # type: ignore[attr-defined]
                    tail_joint.hit_radius = group.hit_radius  # type: ignore[attr-defined]

                    rotation, next_head_pose_bone_before_rotation_matrix = (
                        calculate_joint_pair_head_pose_bone_rotations(
                            delta_time,
                            obj,
                            head_joint,
                            head_pose_bone,  # type: ignore[attr-defined]
                            head_rest_object_matrix,  # type: ignore[attr-defined]
                            tail_joint,
                            tail_pose_bone,  # type: ignore[attr-defined]
                            tail_rest_object_matrix,  # type: ignore[attr-defined]
                            next_head_pose_bone_before_rotation_matrix,
                            world_colliders,  # type: ignore[attr-defined]
                            previous_to_current_center_world_translation,
                        )
                    )
                    pose_bone_and_rotations.append((head_pose_bone, rotation))  # type: ignore[attr-defined]


def calculate_joint_pair_head_pose_bone_rotations(
    delta_time: float,
    obj: Object,
    head_joint: Any,  # noqa: ANN401
    head_pose_bone: PoseBone,
    current_head_rest_object_matrix: Matrix,
    tail_joint: Any,  # noqa: ANN401
    tail_pose_bone: PoseBone,
    current_tail_rest_object_matrix: Matrix,
    next_head_pose_bone_before_rotation_matrix: Optional[Matrix],
    world_colliders: list,  # type: ignore[attr-defined]
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
        Vector(tail_joint.animation_state.previous_world_translation)  # type: ignore[attr-defined]
        + previous_to_current_center_world_translation
    )
    current_tail_world_translation = (
        Vector(tail_joint.animation_state.current_world_translation)  # type: ignore[attr-defined]
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
        (obj.matrix_world @ current_head_pose_bone_matrix.to_translation())
        - (obj.matrix_world @ current_tail_pose_bone_matrix.to_translation())
    ).length

    next_tail_world_translation = (
        next_head_world_translation
        + (next_tail_world_translation - next_head_world_translation).normalized()
        * head_to_tail_world_distance
    )

    for world_collider in world_colliders:  # type: ignore[attr-defined]
        direction, distance = world_collider.calculate_collision(  # type: ignore[attr-defined]
            next_tail_world_translation, head_joint.hit_radius
        )
        if distance >= 0:
            continue
        next_tail_world_translation = next_tail_world_translation - direction * distance  # type: ignore[attr-defined]
        next_tail_world_translation = (  # type: ignore[attr-defined]
            next_head_world_translation
            + (next_tail_world_translation - next_head_world_translation).normalized()  # type: ignore[attr-defined]
            * head_to_tail_world_distance
        )

    next_tail_object_local_translation = (  # type: ignore[attr-defined]
        obj.matrix_world.inverted_safe() @ next_tail_world_translation
    )
    next_head_rotation_end_target_local_translation = (  # type: ignore[attr-defined]
        next_head_pose_bone_before_rotation_matrix.inverted_safe()
        @ next_tail_object_local_translation
    )

    next_head_pose_bone_rotation = Quaternion(
        next_head_rotation_start_target_local_translation.cross(
            next_head_rotation_end_target_local_translation  # type: ignore[attr-defined]
        ),
        next_head_rotation_start_target_local_translation.angle(
            next_head_rotation_end_target_local_translation,  # type: ignore[attr-defined]
            0,  # type: ignore[attr-defined]
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
        next_tail_world_translation  # type: ignore[attr-defined]
    )

    result_rotation = (
        next_head_pose_bone_rotation
        if head_pose_bone.bone.use_inherit_rotation
        else next_head_pose_bone_object_rotation
    )
    return result_rotation, next_tail_pose_bone_before_rotation_matrix


@persistent
def depsgraph_update_pre(_unused: object) -> None:
    context = bpy.context
    secondary_anim_state.reset(context)


# Modal Operator for secondary animation viewport modal update.
class VRM0OTSecondaryAnimationViewportModalUpdate(bpy.types.Operator):
    bl_idname = "vrm.vrm0_secondary_animation_viewport_modal_update"
    bl_label = "VRM 0.x Secondary Animation Viewport Modal Update Operator"

    _timer: Optional[Any] = None
    _last_time: Optional[float] = None

    def modal(self, context: Context, event: Any) -> set[str]:  # noqa: ANN401
        if event.type == "TIMER":
            current_time = time.time()
            if self._last_time is None:
                self._last_time = current_time
                delta_time = 1.0 / 30.0
            else:
                # Clamp delta time to 1/30 sec to match animation playback.
                raw_dt = current_time - self._last_time
                delta_time = min(raw_dt, 1.0 / 30.0)
                self._last_time = current_time
            update_secondary_animation_bone_rotations(context, delta_time)
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == "VIEW_3D":
                        area.tag_redraw()  # type: ignore[valid-type]
        return {"PASS_THROUGH"}

    def execute(self, context: Context) -> set[str]:
        global vrm0_modal_running
        vrm0_modal_running = True
        update_temporary_bones(context)
        self._last_time = None
        self._timer = context.window_manager.event_timer_add(
            1.0 / 30.0, window=context.window
        )
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def cancel(self, context: Context) -> set[str]:
        global vrm0_modal_running
        vrm0_modal_running = False
        update_temporary_bones(
            context
        )  # Deletes temporary bones if Enable Simulation is now false.
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)  # type: ignore[attr-defined]
        return {"CANCELLED"}


@persistent  # type: ignore[attr-defined]
def vrm0_secondary_animation_delayed_start(dummy: Any) -> float:
    if not bpy.context.screen.is_animation_playing:  # type: ignore[attr-defined]
        with contextlib.suppress(RuntimeError):
            bpy.ops.vrm.vrm0_secondary_animation_viewport_modal_update("INVOKE_DEFAULT")  # type: ignore[attr-defined]
    return 1.0


secondary_animation_frame_change_pre = frame_change_pre

spring_bone1_handler_modal = type(
    "spring_bone1_handler_modal",
    (),
    {"springbone_delayed_start": vrm0_secondary_animation_delayed_start},
)
