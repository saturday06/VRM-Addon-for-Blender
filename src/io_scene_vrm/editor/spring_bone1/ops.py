# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import uuid
from collections import deque
from sys import float_info
from typing import TYPE_CHECKING, ClassVar, Optional

from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import Armature, Bone, ChildOfConstraint, Context, Object, Operator

from ...common import convert, safe_removal
from ...common.logger import get_logger
from ..extension_accessor import get_armature_extension
from .handler import reset_state, update_pose_bone_rotations
from .property_group import (
    SpringBone1ColliderGroupPropertyGroup,
    SpringBone1ColliderGroupReferencePropertyGroup,
    SpringBone1ColliderReferencePropertyGroup,
)

logger = get_logger(__name__)


class VRM_OT_add_spring_bone1_collider(Operator):
    bl_idname = "vrm.add_spring_bone1_collider"
    bl_label = "Add Collider"
    bl_description = "Add VRM 1.0 Collider"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone1 = get_armature_extension(armature_data).spring_bone1
        spring_bone1.add_collider(context, armature)
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]


class VRM_OT_remove_spring_bone1_collider(Operator):
    bl_idname = "vrm.remove_spring_bone1_collider"
    bl_label = "Remove Collider"
    bl_description = "Remove VRM 0.x Collider"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    collider_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone = get_armature_extension(armature_data).spring_bone1
        if len(spring_bone.colliders) <= self.collider_index:
            return {"CANCELLED"}

        collider = spring_bone.colliders[self.collider_index]
        bpy_object = collider.bpy_object
        if bpy_object:
            collider.bpy_object = None
            for unnecessary_object in (*bpy_object.children, bpy_object):
                if not safe_removal.remove_object(context, unnecessary_object):
                    logger.warning(
                        'Failed to remove "%s" with %d users'
                        " while removing spring bone collider object",
                        unnecessary_object.name,
                        unnecessary_object.users,
                    )
        bpy_object = None

        collider_uuid = spring_bone.colliders[self.collider_index].uuid
        spring_bone.colliders.remove(self.collider_index)
        for collider_group in spring_bone.collider_groups:
            while True:
                removed = False
                for index, collider in enumerate(list(collider_group.colliders)):
                    if collider.collider_uuid != collider_uuid:
                        continue
                    collider_group.colliders.remove(index)
                    removed = True
                    break
                if not removed:
                    break

        spring_bone.active_collider_index = min(
            spring_bone.active_collider_index,
            max(0, len(spring_bone.colliders) - 1),
        )

        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        collider_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_spring_bone1_collider_group(Operator):
    bl_idname = "vrm.move_up_spring_bone1_collider_group"
    bl_label = "Move Up Collider Group"
    bl_description = "Move Up VRM 1.0 Collider Group"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    collider_group_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone = get_armature_extension(armature_data).spring_bone1
        if len(spring_bone.collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        new_index = (self.collider_group_index - 1) % len(spring_bone.collider_groups)
        spring_bone.collider_groups.move(self.collider_group_index, new_index)
        spring_bone.active_collider_group_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_spring_bone1_collider_group(Operator):
    bl_idname = "vrm.move_down_spring_bone1_collider_group"
    bl_label = "Move Down Collider Group"
    bl_description = "Move Down VRM 1.0 Collider Group"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    collider_group_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone = get_armature_extension(armature_data).spring_bone1
        if len(spring_bone.collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        new_index = (self.collider_group_index + 1) % len(spring_bone.collider_groups)
        spring_bone.collider_groups.move(self.collider_group_index, new_index)
        spring_bone.active_collider_group_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_add_spring_bone1_spring(Operator):
    bl_idname = "vrm.add_spring_bone1_spring"
    bl_label = "Add Spring"
    bl_description = "Add VRM 1.0 Spring"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone1 = get_armature_extension(armature_data).spring_bone1
        spring_bone1.add_spring()
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]


class VRM_OT_remove_spring_bone1_spring(Operator):
    bl_idname = "vrm.remove_spring_bone1_spring"
    bl_label = "Remove Spring"
    bl_description = "Remove VRM 1.0 Spring"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    spring_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone1 = get_armature_extension(armature_data).spring_bone1
        if len(spring_bone1.springs) <= self.spring_index:
            return {"CANCELLED"}
        spring_bone1.springs.remove(self.spring_index)
        spring_bone1.active_spring_index = min(
            spring_bone1.active_spring_index, max(0, len(spring_bone1.springs) - 1)
        )

        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_spring_bone1_spring(Operator):
    bl_idname = "vrm.move_up_spring_bone1_spring"
    bl_label = "Move Up Spring"
    bl_description = "Move Up VRM 1.0 Spring"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    spring_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone1 = get_armature_extension(armature_data).spring_bone1
        springs = spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        new_spring_index = (self.spring_index - 1) % len(springs)
        springs.move(self.spring_index, new_spring_index)
        spring_bone1.active_spring_index = new_spring_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_spring_bone1_spring(Operator):
    bl_idname = "vrm.move_down_spring_bone1_spring"
    bl_label = "Move Down Spring"
    bl_description = "Move Down VRM 1.0 Spring"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    spring_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone1 = get_armature_extension(armature_data).spring_bone1
        springs = spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        new_spring_index = (self.spring_index + 1) % len(springs)
        springs.move(self.spring_index, new_spring_index)
        spring_bone1.active_spring_index = new_spring_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]


class VRM_OT_add_spring_bone1_collider_group(Operator):
    bl_idname = "vrm.add_spring_bone1_collider_group"
    bl_label = "Add Collider Group"
    bl_description = "Add VRM 1.0 Spring Bone Collider Group"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone = get_armature_extension(armature_data).spring_bone1
        spring_bone.add_collider_group()
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]


class VRM_OT_remove_spring_bone1_collider_group(Operator):
    bl_idname = "vrm.remove_spring_bone1_collider_group"
    bl_label = "Remove Collider Group"
    bl_description = "Remove VRM 1.0 Spring Bone Collider Group"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    collider_group_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone = get_armature_extension(armature_data).spring_bone1
        collider_groups = spring_bone.collider_groups
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_group_uuid = collider_groups[self.collider_group_index].uuid
        collider_groups.remove(self.collider_group_index)
        for spring in spring_bone.springs:
            while True:
                removed = False
                for index, collider_group in enumerate(list(spring.collider_groups)):
                    if collider_group.collider_group_uuid != collider_group_uuid:
                        continue
                    spring.collider_groups.remove(index)
                    removed = True
                    break
                if not removed:
                    break

        spring_bone.active_collider_group_index = min(
            spring_bone.active_collider_group_index,
            max(0, len(spring_bone.collider_groups) - 1),
        )

        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_spring_bone1_collider(Operator):
    bl_idname = "vrm.move_up_spring_bone1_collider"
    bl_label = "Move Up Collider"
    bl_description = "Move Up VRM 1.0 Collider"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    collider_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone1 = get_armature_extension(armature_data).spring_bone1
        colliders = spring_bone1.colliders
        if len(colliders) <= self.collider_index:
            return {"CANCELLED"}
        new_collider_index = (self.collider_index - 1) % len(colliders)
        colliders.move(self.collider_index, new_collider_index)
        spring_bone1.active_collider_index = new_collider_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        collider_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_spring_bone1_collider(Operator):
    bl_idname = "vrm.move_down_spring_bone1_collider"
    bl_label = "Move Down Collider"
    bl_description = "Move Down VRM 1.0 Collider"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    collider_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone1 = get_armature_extension(armature_data).spring_bone1
        colliders = spring_bone1.colliders
        if len(colliders) <= self.collider_index:
            return {"CANCELLED"}
        new_collider_index = (self.collider_index + 1) % len(colliders)
        colliders.move(self.collider_index, new_collider_index)
        spring_bone1.active_collider_index = new_collider_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        collider_index: int  # type: ignore[no-redef]


class VRM_OT_add_spring_bone1_collider_group_collider(Operator):
    bl_idname = "vrm.add_spring_bone1_collider_group_collider"
    bl_label = "Add Collider"
    bl_description = "Add VRM 1.0 Spring Bone Collider Group Collider"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    collider_group_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        collider_groups = get_armature_extension(
            armature_data
        ).spring_bone1.collider_groups
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_group = collider_groups[self.collider_group_index]
        collider_group.add_collider()
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_assign_spring_bone1_collider_group_collider(Operator):
    bl_idname = "vrm.assign_spring_bone1_collider_group_collider"
    bl_label = "Assign Collider"
    bl_description = "Assign VRM 1.0 Spring Bone Collider Group Collider"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_data_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    collider_reference_path: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    collider_uuid: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature_data = context.blend_data.armatures.get(self.armature_data_name)
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}

        collider_reference = armature_data.path_resolve(
            self.collider_reference_path,
            False,
        )
        if not isinstance(
            collider_reference, SpringBone1ColliderReferencePropertyGroup
        ):
            return {"CANCELLED"}

        if not self.collider_uuid:
            collider_reference.collider_uuid = ""
            return {"FINISHED"}

        spring_bone1 = get_armature_extension(armature_data).spring_bone1
        for collider in spring_bone1.colliders:
            if collider.uuid != self.collider_uuid:
                continue
            collider_reference.collider_uuid = collider.uuid
            return {"FINISHED"}

        return {"CANCELLED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_data_name: str  # type: ignore[no-redef]
        collider_reference_path: str  # type: ignore[no-redef]
        collider_uuid: str  # type: ignore[no-redef]


class VRM_OT_unassign_spring_bone1_collider_group_collider(Operator):
    bl_idname = "vrm.unassign_spring_bone1_collider_group_collider"
    bl_label = "Unassign Collider"
    bl_description = "Unassign VRM 1.0 Spring Bone Collider Group Collider"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_data_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    collider_reference_path: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature_data = context.blend_data.armatures.get(self.armature_data_name)
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}

        collider_reference = armature_data.path_resolve(
            self.collider_reference_path,
            False,
        )
        if not isinstance(
            collider_reference, SpringBone1ColliderReferencePropertyGroup
        ):
            return {"CANCELLED"}

        collider_reference.collider_uuid = ""
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_data_name: str  # type: ignore[no-redef]
        collider_reference_path: str  # type: ignore[no-redef]


class VRM_OT_remove_spring_bone1_collider_group_collider(Operator):
    bl_idname = "vrm.remove_spring_bone1_collider_group_collider"
    bl_label = "Remove Collider"
    bl_description = "Remove VRM 1.0 Spring Bone Collider Group Collider"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    collider_group_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )
    collider_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        collider_groups = get_armature_extension(
            armature_data
        ).spring_bone1.collider_groups
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_group = collider_groups[self.collider_group_index]
        if len(collider_group.colliders) <= self.collider_index:
            return {"CANCELLED"}
        collider_group.colliders.remove(self.collider_index)
        collider_group.active_collider_index = min(
            collider_group.active_collider_index,
            max(0, len(collider_group.colliders) - 1),
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]
        collider_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_spring_bone1_collider_group_collider(Operator):
    bl_idname = "vrm.move_up_spring_bone1_collider_group_collider"
    bl_label = "Move Up Collider"
    bl_description = "Move Up VRM 1.0 Collider Group Collider"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    collider_group_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )
    collider_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone1 = get_armature_extension(armature_data).spring_bone1
        if len(spring_bone1.collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_group = spring_bone1.collider_groups[self.collider_group_index]
        if len(collider_group.colliders) <= self.collider_index:
            return {"CANCELLED"}
        new_collider_index = (self.collider_index - 1) % len(collider_group.colliders)
        collider_group.colliders.move(self.collider_index, new_collider_index)
        collider_group.active_collider_index = new_collider_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]
        collider_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_spring_bone1_collider_group_collider(Operator):
    bl_idname = "vrm.move_down_spring_bone1_collider_group_collider"
    bl_label = "Move Down Collider"
    bl_description = "Move Down VRM 1.0 Collider Group Collider"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    collider_group_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )
    collider_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone1 = get_armature_extension(armature_data).spring_bone1
        if len(spring_bone1.collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_group = spring_bone1.collider_groups[self.collider_group_index]
        if len(collider_group.colliders) <= self.collider_index:
            return {"CANCELLED"}
        new_collider_index = (self.collider_index + 1) % len(collider_group.colliders)
        collider_group.colliders.move(self.collider_index, new_collider_index)
        collider_group.active_collider_index = new_collider_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]
        collider_index: int  # type: ignore[no-redef]


class VRM_OT_add_spring_bone1_spring_collider_group(Operator):
    bl_idname = "vrm.add_spring_bone1_spring_collider_group"
    bl_label = "Add Collider Group"
    bl_description = "Add VRM 1.0 Spring Bone Spring Collider Group"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    spring_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        springs = get_armature_extension(armature_data).spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        spring = springs[self.spring_index]
        spring.add_collider_group()
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]


class VRM_OT_assign_spring_bone1_spring_collider_group(Operator):
    bl_idname = "vrm.assign_spring_bone1_spring_collider_group"
    bl_label = "Assign Collider Group"
    bl_description = "Assign VRM 1.0 Spring Bone Spring Collider Group"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_data_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    collider_group_reference_path: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    collider_group_uuid: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature_data = context.blend_data.armatures.get(self.armature_data_name)
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}

        collider_group_reference = armature_data.path_resolve(
            self.collider_group_reference_path,
            False,
        )
        if not isinstance(
            collider_group_reference,
            SpringBone1ColliderGroupReferencePropertyGroup,
        ):
            return {"CANCELLED"}

        if not self.collider_group_uuid:
            collider_group_reference.collider_group_uuid = ""
            return {"FINISHED"}

        spring_bone1 = get_armature_extension(armature_data).spring_bone1
        for collider_group in spring_bone1.collider_groups:
            if collider_group.uuid != self.collider_group_uuid:
                continue
            collider_group_reference.collider_group_uuid = collider_group.uuid
            return {"FINISHED"}

        return {"CANCELLED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_data_name: str  # type: ignore[no-redef]
        collider_group_reference_path: str  # type: ignore[no-redef]
        collider_group_uuid: str  # type: ignore[no-redef]


class VRM_OT_unassign_spring_bone1_spring_collider_group(Operator):
    bl_idname = "vrm.unassign_spring_bone1_spring_collider_group"
    bl_label = "Unassign Collider Group"
    bl_description = "Unassign VRM 1.0 Spring Bone Spring Collider Group"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_data_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    collider_group_reference_path: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature_data = context.blend_data.armatures.get(self.armature_data_name)
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}

        collider_group_reference = armature_data.path_resolve(
            self.collider_group_reference_path,
            False,
        )
        if not isinstance(
            collider_group_reference,
            SpringBone1ColliderGroupReferencePropertyGroup,
        ):
            return {"CANCELLED"}

        collider_group_reference.collider_group_uuid = ""
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_data_name: str  # type: ignore[no-redef]
        collider_group_reference_path: str  # type: ignore[no-redef]


class VRM_OT_remove_spring_bone1_spring_collider_group(Operator):
    bl_idname = "vrm.remove_spring_bone1_spring_collider_group"
    bl_label = "Remove Collider Group"
    bl_description = "Remove VRM 1.0 Spring Bone Spring Collider Group"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    spring_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )
    collider_group_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        springs = get_armature_extension(armature_data).spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        spring = springs[self.spring_index]
        if len(spring.collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        spring.collider_groups.remove(self.collider_group_index)
        spring.active_collider_group_index = min(
            spring.active_collider_group_index, max(0, len(spring.collider_groups) - 1)
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_spring_bone1_spring_collider_group(Operator):
    bl_idname = "vrm.move_up_spring_bone1_spring_collider_group"
    bl_label = "Move Up Collider Group"
    bl_description = "Move Up VRM 1.0 Spring Collider Group"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    spring_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )
    collider_group_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone1 = get_armature_extension(armature_data).spring_bone1
        springs = spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        spring = springs[self.spring_index]
        if len(spring.collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        new_collider_group_index = (self.collider_group_index - 1) % len(
            spring.collider_groups
        )
        spring.collider_groups.move(self.collider_group_index, new_collider_group_index)
        spring.active_collider_group_index = new_collider_group_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_spring_bone1_spring_collider_group(Operator):
    bl_idname = "vrm.move_down_spring_bone1_spring_collider_group"
    bl_label = "Move Down Collider Group"
    bl_description = "Move Down VRM 1.0 Spring Collider Group"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    spring_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )
    collider_group_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone1 = get_armature_extension(armature_data).spring_bone1
        springs = spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        spring = springs[self.spring_index]
        if len(spring.collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        new_collider_group_index = (self.collider_group_index + 1) % len(
            spring.collider_groups
        )
        spring.collider_groups.move(self.collider_group_index, new_collider_group_index)
        spring.active_collider_group_index = new_collider_group_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_add_spring_bone1_joint(Operator):
    bl_idname = "vrm.add_spring_bone1_spring_joint"
    bl_label = "Add Joint"
    bl_description = "Add VRM 1.0 Spring Bone Spring Joint"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    spring_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )
    guess_properties: BoolProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        springs = get_armature_extension(armature_data).spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        spring = springs[self.spring_index]
        spring.add_joint()
        if not self.guess_properties:
            return {"FINISHED"}

        if len(spring.joints) < 2:
            return {"FINISHED"}
        parent_joint, joint = spring.joints[-2:]
        parent_bone = armature_data.bones.get(parent_joint.node.bone_name)
        if parent_bone and parent_bone.children:
            joint.node.bone_name = parent_bone.children[0].name
        joint.hit_radius = parent_joint.hit_radius
        joint.stiffness = parent_joint.stiffness
        joint.gravity_power = parent_joint.gravity_power
        joint.gravity_dir = list(parent_joint.gravity_dir)
        joint.drag_force = parent_joint.drag_force
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]
        guess_properties: bool  # type: ignore[no-redef]


class VRM_OT_remove_spring_bone1_joint(Operator):
    bl_idname = "vrm.remove_spring_bone1_spring_joint"
    bl_label = "Remove Joint"
    bl_description = "Remove VRM 1.0 Spring Bone Spring Joint"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    spring_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )
    joint_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        springs = get_armature_extension(armature_data).spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        spring = springs[self.spring_index]
        if len(spring.joints) <= self.joint_index:
            return {"CANCELLED"}
        spring.joints.remove(self.joint_index)
        spring.active_joint_index = min(
            spring.active_joint_index, max(0, len(spring.joints) - 1)
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]
        joint_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_spring_bone1_joint(Operator):
    bl_idname = "vrm.move_up_spring_bone1_joint"
    bl_label = "Move Up Joint"
    bl_description = "Move Up VRM 1.0 Joint"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    spring_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )
    joint_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone1 = get_armature_extension(armature_data).spring_bone1
        springs = spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        spring = springs[self.spring_index]
        if len(spring.joints) <= self.joint_index:
            return {"CANCELLED"}
        new_joint_index = (self.joint_index - 1) % len(spring.joints)
        spring.joints.move(self.joint_index, new_joint_index)
        spring.active_joint_index = new_joint_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]
        joint_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_spring_bone1_joint(Operator):
    bl_idname = "vrm.move_down_spring_bone1_joint"
    bl_label = "Move Down Joint"
    bl_description = "Move Down VRM 1.0 Joint"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    spring_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )
    joint_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone1 = get_armature_extension(armature_data).spring_bone1
        springs = spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        spring = springs[self.spring_index]
        if len(spring.joints) <= self.joint_index:
            return {"CANCELLED"}
        new_joint_index = (self.joint_index + 1) % len(spring.joints)
        spring.joints.move(self.joint_index, new_joint_index)
        spring.active_joint_index = new_joint_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]
        joint_index: int  # type: ignore[no-redef]


class VRM_OT_reset_spring_bone1_animation_state(Operator):
    bl_idname = "vrm.reset_spring_bone1_animation_state"
    bl_label = "Reset SpringBone Animation State"
    bl_description = "Reset SpringBone Animation State"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        for spring in get_armature_extension(armature_data).spring_bone1.springs:
            for joint in spring.joints:
                joint.animation_state.initialized_as_tail = False
        reset_state(context)
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]


class VRM_OT_update_spring_bone1_animation(Operator):
    bl_idname = "vrm.update_spring_bone1_animation"
    bl_label = "Update SpringBone Animation"
    bl_description = "Update SpringBone Animation"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    delta_time: FloatProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        delta_time = self.delta_time
        if abs(delta_time) < float_info.epsilon:
            delta_time = context.scene.render.fps_base / float(context.scene.render.fps)
        update_pose_bone_rotations(context, delta_time)
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        delta_time: float  # type: ignore[no-redef]


def _assign_spring_bone1_from_vrm0(
    context: Context,
    armature_object_name: str,
) -> set[str]:
    armature = context.blend_data.objects.get(armature_object_name)
    if armature is None or armature.type != "ARMATURE":
        return {"CANCELLED"}
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return {"CANCELLED"}

    ext = get_armature_extension(armature_data)
    vrm0_secondary_animation = ext.vrm0.secondary_animation
    spring_bone1 = ext.spring_bone1

    if (
        not vrm0_secondary_animation.collider_groups
        and not vrm0_secondary_animation.bone_groups
    ):
        return {"FINISHED"}

    if spring_bone1.colliders or spring_bone1.springs:
        return {"FINISHED"}

    vrm0_collider_group_uuid_to_collider_group: dict[
        str, SpringBone1ColliderGroupPropertyGroup
    ] = {}
    for vrm0_collider_group in vrm0_secondary_animation.collider_groups:
        if not vrm0_collider_group.uuid:
            continue
        collider_group = spring_bone1.add_collider_group()
        collider_group_name = vrm0_collider_group.node.bone_name
        if collider_group_name:
            collider_group_name += "-"
        collider_group_name += vrm0_collider_group.uuid
        collider_group.vrm_name = collider_group_name
        for vrm0_collider in vrm0_collider_group.colliders:
            vrm0_collider_bpy_object = vrm0_collider.bpy_object
            if not vrm0_collider_bpy_object:
                continue

            collider = spring_bone1.add_collider(context, armature)
            collider.node.bone_name = vrm0_collider_group.node.bone_name
            collider.shape_type = collider.SHAPE_TYPE_SPHERE.identifier
            collider_bpy_object = collider.bpy_object
            if collider_bpy_object:
                collider_bpy_object.name = vrm0_collider_bpy_object.name + ".1"
                collider_bpy_object.matrix_world = vrm0_collider_bpy_object.matrix_world
            vrm0_scale = vrm0_collider_bpy_object.scale
            vrm0_mean_abs_scale = (
                abs(vrm0_scale[0]) + abs(vrm0_scale[1]) + abs(vrm0_scale[2])
            ) / 3.0
            effective_radius = (
                vrm0_collider_bpy_object.empty_display_size * vrm0_mean_abs_scale
            )
            collider.shape.sphere.radius = effective_radius

            collider_group_collider = collider_group.add_collider()
            collider_group_collider.collider_uuid = collider.uuid
        vrm0_collider_group_uuid_to_collider_group[vrm0_collider_group.uuid] = (
            collider_group
        )

    assigned_bone_names: set[str] = set()
    for vrm0_bone_group in vrm0_secondary_animation.bone_groups:
        root_bones: list[Bone] = []
        for vrm0_bone_group_bone in vrm0_bone_group.bones:
            bone_name = vrm0_bone_group_bone.bone_name
            if not bone_name:
                continue
            bone = armature_data.bones.get(bone_name)
            if not bone:
                continue
            if bone.name in assigned_bone_names:
                continue
            traversing_bone = bone
            while traversing_bone:
                if traversing_bone in root_bones:
                    break
                traversing_bone = traversing_bone.parent
            if traversing_bone:
                continue

            children = list(bone.children)
            while children:
                child_bone = children.pop()
                if child_bone in root_bones:
                    root_bones.remove(child_bone)
                children.extend(child_bone.children)

            root_bones.append(bone)

        bone_chains: list[list[str]] = []

        start_bones = deque[Bone](root_bones)
        while start_bones:
            start_bone = start_bones.popleft()
            bone_chain = [start_bone.name]
            child_bones = deque[Bone](start_bone.children)
            while child_bones:
                first_child_bone = child_bones.popleft()
                bone_chain.append(first_child_bone.name)
                start_bones.extend(child_bones)
                child_bones = deque[Bone](first_child_bone.children)
            bone_chains.append(bone_chain)

        assigned_bone_names.update(
            bone_name for bone_chain in bone_chains for bone_name in bone_chain
        )

        for bone_chain in bone_chains:
            spring = spring_bone1.add_spring()
            spring_vrm_name = vrm0_bone_group.comment
            if not spring_vrm_name:
                spring_vrm_name = "Spring"
            spring_vrm_name += "-" + uuid.uuid4().hex
            spring.vrm_name = spring_vrm_name
            spring.center.bone_name = vrm0_bone_group.center.bone_name

            for bone_name in bone_chain:
                joint = spring.add_joint()
                joint.node.bone_name = bone_name
                joint.stiffness = vrm0_bone_group.stiffiness
                joint.gravity_power = vrm0_bone_group.gravity_power
                joint.gravity_dir = list(vrm0_bone_group.gravity_dir)
                joint.drag_force = vrm0_bone_group.drag_force
                joint.hit_radius = vrm0_bone_group.hit_radius

            for vrm0_bone_group_collider_group in vrm0_bone_group.collider_groups:
                vrm0_collider_group_uuid = (
                    vrm0_bone_group_collider_group.collider_group_uuid
                )
                if not vrm0_collider_group_uuid:
                    continue
                collider_group = vrm0_collider_group_uuid_to_collider_group.get(
                    vrm0_collider_group_uuid
                )
                if not collider_group:
                    continue
                spring_collider_group = spring.add_collider_group()
                spring_collider_group.collider_group_uuid = collider_group.uuid
    return {"FINISHED"}


class VRM_OT_assign_spring_bone1_from_vrm0(Operator):
    bl_idname = "vrm.assign_spring_bone1_from_vrm0"
    bl_label = "Copy VRM 0.0 Spring Bone"
    bl_description = "Copy VRM 0.0 Spring Bone data to VRM 1.0 Spring Bone"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        return _assign_spring_bone1_from_vrm0(context, self.armature_object_name)

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]


def _assign_spring_bone1_from_mmd(
    context: Context,
    armature_object_name: str,
) -> set[str]:
    armature = context.blend_data.objects.get(armature_object_name)
    if armature is None or armature.type != "ARMATURE":
        return {"CANCELLED"}

    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return {"CANCELLED"}

    ext = get_armature_extension(armature_data)
    spring_bone1 = ext.spring_bone1
    if spring_bone1.colliders or spring_bone1.springs:
        return {"FINISHED"}

    # Collect MMD rigid bodies associated with this armature.
    # mmd_rigid.type: '0' = kinematic (collider), '1' or '2' = dynamic (springy bone).
    # https://github.com/MMD-Blender/blender_mmd_tools/blob/v4.5.9/mmd_tools/core/rigid_body.py
    # https://github.com/MMD-Blender/blender_mmd_tools/blob/v4.5.9/mmd_tools/properties/rigid_body.py
    static_rigid_bone_name_to_obj: dict[str, Object] = {}
    dynamic_rigid_bone_names: list[str] = []

    for obj in context.blend_data.objects:
        mmd_type: object = getattr(obj, "mmd_type", None)
        if mmd_type != "RIGID_BODY":
            continue

        mmd_rigid: object = getattr(obj, "mmd_rigid", None)
        if mmd_rigid is None:
            continue

        # The bone linkage is stored in a 'mmd_tools_rigid_parent' CHILD_OF constraint.
        rigid_parent_constraint = obj.constraints.get("mmd_tools_rigid_parent")
        if not isinstance(rigid_parent_constraint, ChildOfConstraint):
            continue

        if rigid_parent_constraint.target != armature:
            continue

        bone_name = rigid_parent_constraint.subtarget
        if not bone_name:
            continue

        if bone_name not in armature_data.bones:
            continue

        rigid_type: object = getattr(mmd_rigid, "type", None)
        if rigid_type == "0":
            # MODE_STATIC
            static_rigid_bone_name_to_obj[bone_name] = obj
        elif rigid_type in ("1", "2") and bone_name not in dynamic_rigid_bone_names:
            # MODE_DYNAMIC, MODE_DYNAMIC_BONE
            dynamic_rigid_bone_names.append(bone_name)

    if not dynamic_rigid_bone_names:
        return {"FINISHED"}

    # Create sphere colliders from kinematic (non-physics) rigid bodies.
    static_rigid_bone_to_collider_group: dict[
        str, SpringBone1ColliderGroupPropertyGroup
    ] = {}
    for bone_name, mmd_obj in static_rigid_bone_name_to_obj.items():
        collider = spring_bone1.add_collider(context, armature)
        collider.node.bone_name = bone_name

        mmd_rigid = getattr(mmd_obj, "mmd_rigid", None)
        shape: object = getattr(mmd_rigid, "shape", None)
        # Estimate size from the object's bounding-box dimensions.
        dimensions = convert.float3_or_none(getattr(mmd_obj, "dimensions", None))
        if dimensions:
            dim_x, dim_y, dim_z = dimensions
        else:
            dim_x, dim_y, dim_z = 0.25, 0.25, 0.25

        if shape == "CAPSULE":
            collider.shape_type = collider.SHAPE_TYPE_CAPSULE.identifier
            radius = max(dim_x, dim_y) / 2
            height = max(dim_z - radius * 2, 0.0)
            collider.shape.capsule.radius = max(radius, 0.0001)
            half_h = height / 2
            collider.shape.capsule.offset = (0, 0, -half_h)
            collider.shape.capsule.tail = (0, 0, half_h)
        else:
            collider.shape_type = collider.SHAPE_TYPE_SPHERE.identifier
            radius = max(dim_x, dim_y, dim_z) / 2
            collider.shape.sphere.radius = max(radius, 0.0001)

        collider_bpy_object = collider.bpy_object
        if collider_bpy_object:
            collider_bpy_object.matrix_world = mmd_obj.matrix_world

        collider_group = spring_bone1.add_collider_group()
        collider_group.vrm_name = bone_name + "-mmd-colliders"
        collider_group_collider = collider_group.add_collider()
        collider_group_collider.collider_uuid = collider.uuid
        static_rigid_bone_to_collider_group[bone_name] = collider_group

    # Build bone chains from physics bones.
    # Root physics bones are those whose direct bone parent is NOT a physics bone.
    root_physics_bones: list[Bone] = []
    for bone_name in dynamic_rigid_bone_names:
        bone = armature_data.bones.get(bone_name)
        if not bone:
            continue
        parent = bone.parent
        if parent is None or parent.name not in dynamic_rigid_bone_names:
            root_physics_bones.append(bone)

    assigned_bone_names: set[str] = set()
    bone_chains: list[list[str]] = []

    start_bones = deque[Bone](root_physics_bones)
    while start_bones:
        start_bone = start_bones.popleft()
        if start_bone.name in assigned_bone_names:
            continue
        bone_chain = [start_bone.name]
        child_bones = deque[Bone](
            child
            for child in start_bone.children
            if child.name in dynamic_rigid_bone_names
        )
        while child_bones:
            first_child_bone = child_bones.popleft()
            bone_chain.append(first_child_bone.name)
            start_bones.extend(child_bones)
            child_bones = deque[Bone](
                child
                for child in first_child_bone.children
                if child.name in dynamic_rigid_bone_names
            )
        bone_chains.append(bone_chain)
        assigned_bone_names.update(bone_chain)

    for bone_chain in bone_chains:
        if not bone_chain:
            continue
        first_bone_name = bone_chain[0]

        spring = spring_bone1.add_spring()

        spring_vrm_name = ""
        root_pose_bone = armature.pose.bones.get(first_bone_name)
        if root_pose_bone is not None:
            mmd_bone: object = getattr(root_pose_bone, "mmd_bone", None)
            if mmd_bone is not None:
                name_j = getattr(mmd_bone, "name_j", None)
                if isinstance(name_j, str) and name_j:
                    spring_vrm_name = name_j
        if not spring_vrm_name:
            spring_vrm_name = first_bone_name
        spring.vrm_name = spring_vrm_name + "-" + uuid.uuid4().hex

        for bone_name in bone_chain:
            joint = spring.add_joint()
            joint.node.bone_name = bone_name

        # Associate collider groups whose bone is an ancestor of the root physics bone.
        root_bone = armature_data.bones.get(first_bone_name)
        if root_bone:
            traversing: Optional[Bone] = root_bone.parent
            while traversing:
                collider_group = static_rigid_bone_to_collider_group.get(
                    traversing.name
                )
                if collider_group:
                    spring_collider_group = spring.add_collider_group()
                    spring_collider_group.collider_group_uuid = collider_group.uuid
                traversing = traversing.parent

    return {"FINISHED"}


class VRM_OT_assign_spring_bone1_from_mmd(Operator):
    bl_idname = "vrm.assign_spring_bone1_from_mmd"
    bl_label = "Copy MMD Spring Bone"
    bl_description = "Copy MMD spring bone data to VRM 1.0 Spring Bone"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        return _assign_spring_bone1_from_mmd(context, self.armature_object_name)

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]


def assign_spring_bone1_automatically(
    context: Context, armature_object_name: str
) -> set[str]:
    armature = context.blend_data.objects.get(armature_object_name)
    if armature is None or armature.type != "ARMATURE":
        return {"CANCELLED"}
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return {"CANCELLED"}

    ext = get_armature_extension(armature_data)
    spring_bone1 = ext.spring_bone1

    if spring_bone1.colliders or spring_bone1.springs:
        return {"FINISHED"}

    _assign_spring_bone1_from_vrm0(context, armature_object_name)
    _assign_spring_bone1_from_mmd(context, armature_object_name)

    return {"FINISHED"}


class VRM_OT_assign_spring_bone1_automatically(Operator):
    bl_idname = "vrm.assign_spring_bone1_automatically"
    bl_label = "Assign Auto-Detected Spring Bones"
    bl_description = "Assign Spring Bones automatically"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        return assign_spring_bone1_automatically(context, self.armature_object_name)

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
