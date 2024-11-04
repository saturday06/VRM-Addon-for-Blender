# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import uuid
from collections.abc import Set as AbstractSet
from sys import float_info
from typing import TYPE_CHECKING

from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import Armature, Context, Operator

from ..extension import get_armature_extension
from .handler import reset_state, update_pose_bone_rotations


class VRM_OT_add_spring_bone1_collider(Operator):
    bl_idname = "vrm.add_spring_bone1_collider"
    bl_label = "Add Collider"
    bl_description = "Add VRM 1.0 Collider"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone = get_armature_extension(armature_data).spring_bone1
        collider = spring_bone.colliders.add()
        collider.uuid = uuid.uuid4().hex
        collider.shape.sphere.radius = 0.125
        collider.reset_bpy_object(context, armature)
        spring_bone.active_collider_index = len(spring_bone.colliders) - 1
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]


class VRM_OT_remove_spring_bone1_collider(Operator):
    bl_idname = "vrm.remove_spring_bone1_collider"
    bl_label = "Remove Collider"
    bl_description = "Remove VRM 0.x Collider"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    collider_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone = get_armature_extension(armature_data).spring_bone1
        if len(spring_bone.colliders) <= self.collider_index:
            return {"CANCELLED"}

        bpy_object = spring_bone.colliders[self.collider_index].bpy_object
        if bpy_object:
            remove_objects = [*bpy_object.children, bpy_object]
            for collection in context.blend_data.collections:
                for remove_object in remove_objects:
                    remove_object.parent = None
                    if remove_object.name in collection.objects:
                        collection.objects.unlink(remove_object)
            for remove_object in remove_objects:
                if remove_object.users <= 1:
                    context.blend_data.objects.remove(remove_object, do_unlink=True)

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
        armature_name: str  # type: ignore[no-redef]
        collider_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_spring_bone1_collider_group(Operator):
    bl_idname = "vrm.move_up_spring_bone1_collider_group"
    bl_label = "Move Up Collider Group"
    bl_description = "Move Up VRM 1.0 Collider Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    collider_group_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
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
        for collider_group in spring_bone.collider_groups:
            collider_group.fix_index(context)
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_spring_bone1_collider_group(Operator):
    bl_idname = "vrm.move_down_spring_bone1_collider_group"
    bl_label = "Move Down Collider Group"
    bl_description = "Move Down VRM 1.0 Collider Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    collider_group_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
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
        for collider_group in spring_bone.collider_groups:
            collider_group.fix_index(context)
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_add_spring_bone1_spring(Operator):
    bl_idname = "vrm.add_spring_bone1_spring"
    bl_label = "Add Spring"
    bl_description = "Add VRM 1.0 Spring"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone1 = get_armature_extension(armature_data).spring_bone1
        spring = spring_bone1.springs.add()
        spring.vrm_name = "Spring"
        spring_bone1.active_spring_index = len(spring_bone1.springs) - 1
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]


class VRM_OT_remove_spring_bone1_spring(Operator):
    bl_idname = "vrm.remove_spring_bone1_spring"
    bl_label = "Remove Spring"
    bl_description = "Remove VRM 1.0 Spring"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    spring_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
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
        armature_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_spring_bone1_spring(Operator):
    bl_idname = "vrm.move_up_spring_bone1_spring"
    bl_label = "Move Up Spring"
    bl_description = "Move Up VRM 1.0 Spring"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    spring_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
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
        armature_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_spring_bone1_spring(Operator):
    bl_idname = "vrm.move_down_spring_bone1_spring"
    bl_label = "Move Down Spring"
    bl_description = "Move Down VRM 1.0 Spring"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    spring_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
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
        armature_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]


class VRM_OT_add_spring_bone1_collider_group(Operator):
    bl_idname = "vrm.add_spring_bone1_collider_group"
    bl_label = "Add Collider Group"
    bl_description = "Add VRM 1.0 Spring Bone Collider Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        spring_bone = get_armature_extension(armature_data).spring_bone1
        collider_group = spring_bone.collider_groups.add()
        collider_group.uuid = uuid.uuid4().hex
        collider_group.vrm_name = "Collider Group"
        spring_bone.active_collider_group_index = len(spring_bone.collider_groups) - 1
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]


class VRM_OT_remove_spring_bone1_collider_group(Operator):
    bl_idname = "vrm.remove_spring_bone1_collider_group"
    bl_label = "Remove Collider Group"
    bl_description = "Remove VRM 1.0 Spring Bone Collider Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    collider_group_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
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
        for collider_group in collider_groups:
            collider_group.fix_index(context)

        spring_bone.active_collider_group_index = min(
            spring_bone.active_collider_group_index,
            max(0, len(spring_bone.collider_groups) - 1),
        )

        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_spring_bone1_collider(Operator):
    bl_idname = "vrm.move_up_spring_bone1_collider"
    bl_label = "Move Up Collider"
    bl_description = "Move Up VRM 1.0 Collider"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    collider_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
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
        armature_name: str  # type: ignore[no-redef]
        collider_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_spring_bone1_collider(Operator):
    bl_idname = "vrm.move_down_spring_bone1_collider"
    bl_label = "Move Down Collider"
    bl_description = "Move Down VRM 1.0 Collider"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    collider_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
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
        armature_name: str  # type: ignore[no-redef]
        collider_index: int  # type: ignore[no-redef]


class VRM_OT_add_spring_bone1_collider_group_collider(Operator):
    bl_idname = "vrm.add_spring_bone1_collider_group_collider"
    bl_label = "Add Collider"
    bl_description = "Add VRM 1.0 Spring Bone Collider Group Collider"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    collider_group_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
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
        collider_group.colliders.add()
        collider_group.active_collider_index = len(collider_group.colliders) - 1
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_remove_spring_bone1_collider_group_collider(Operator):
    bl_idname = "vrm.remove_spring_bone1_collider_group_collider"
    bl_label = "Remove Collider"
    bl_description = "Remove VRM 1.0 Spring Bone Collider Group Collider"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
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
        armature = context.blend_data.objects.get(self.armature_name)
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
        armature_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]
        collider_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_spring_bone1_collider_group_collider(Operator):
    bl_idname = "vrm.move_up_spring_bone1_collider_group_collider"
    bl_label = "Move Up Collider"
    bl_description = "Move Up VRM 1.0 Collider Group Collider"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
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
        armature = context.blend_data.objects.get(self.armature_name)
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
        armature_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]
        collider_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_spring_bone1_collider_group_collider(Operator):
    bl_idname = "vrm.move_down_spring_bone1_collider_group_collider"
    bl_label = "Move Down Collider"
    bl_description = "Move Down VRM 1.0 Collider Group Collider"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
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
        armature = context.blend_data.objects.get(self.armature_name)
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
        armature_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]
        collider_index: int  # type: ignore[no-redef]


class VRM_OT_add_spring_bone1_spring_collider_group(Operator):
    bl_idname = "vrm.add_spring_bone1_spring_collider_group"
    bl_label = "Add Collider Group"
    bl_description = "Add VRM 1.0 Spring Bone Spring Collider Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    spring_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        springs = get_armature_extension(armature_data).spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        spring = springs[self.spring_index]
        spring.collider_groups.add()
        spring.active_collider_group_index = len(spring.collider_groups) - 1
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]


class VRM_OT_remove_spring_bone1_spring_collider_group(Operator):
    bl_idname = "vrm.remove_spring_bone1_spring_collider_group"
    bl_label = "Remove Collider Group"
    bl_description = "Remove VRM 1.0 Spring Bone Spring Collider Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
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
        armature = context.blend_data.objects.get(self.armature_name)
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
        armature_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_spring_bone1_spring_collider_group(Operator):
    bl_idname = "vrm.move_up_spring_bone1_spring_collider_group"
    bl_label = "Move Up Collider Group"
    bl_description = "Move Up VRM 1.0 Spring Collider Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
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
        armature = context.blend_data.objects.get(self.armature_name)
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
        armature_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_spring_bone1_spring_collider_group(Operator):
    bl_idname = "vrm.move_down_spring_bone1_spring_collider_group"
    bl_label = "Move Down Collider Group"
    bl_description = "Move Down VRM 1.0 Spring Collider Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
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
        armature = context.blend_data.objects.get(self.armature_name)
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
        armature_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_add_spring_bone1_joint(Operator):
    bl_idname = "vrm.add_spring_bone1_spring_joint"
    bl_label = "Add Joint"
    bl_description = "Add VRM 1.0 Spring Bone Spring Joint"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
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
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        springs = get_armature_extension(armature_data).spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        spring = springs[self.spring_index]
        spring.joints.add()
        spring.active_joint_index = len(spring.joints) - 1
        if not self.guess_properties:
            return {"FINISHED"}

        if len(spring.joints) < 2:
            return {"FINISHED"}
        parent_joint, joint = spring.joints[-2:]
        parent_bone = armature_data.bones.get(parent_joint.node.bone_name)
        if parent_bone and parent_bone.children:
            joint.node.set_bone_name(parent_bone.children[0].name)
        joint.hit_radius = parent_joint.hit_radius
        joint.stiffness = parent_joint.stiffness
        joint.gravity_power = parent_joint.gravity_power
        joint.gravity_dir = list(parent_joint.gravity_dir)
        joint.drag_force = parent_joint.drag_force
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]
        guess_properties: bool  # type: ignore[no-redef]


class VRM_OT_remove_spring_bone1_joint(Operator):
    bl_idname = "vrm.remove_spring_bone1_spring_joint"
    bl_label = "Remove Joint"
    bl_description = "Remove VRM 1.0 Spring Bone Spring Joint"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
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
        armature = context.blend_data.objects.get(self.armature_name)
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
        armature_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]
        joint_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_spring_bone1_joint(Operator):
    bl_idname = "vrm.move_up_spring_bone1_joint"
    bl_label = "Move Up Joint"
    bl_description = "Move Up VRM 1.0 Joint"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
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
        armature = context.blend_data.objects.get(self.armature_name)
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
        armature_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]
        joint_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_spring_bone1_joint(Operator):
    bl_idname = "vrm.move_down_spring_bone1_joint"
    bl_label = "Move Down Joint"
    bl_description = "Move Down VRM 1.0 Joint"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
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
        armature = context.blend_data.objects.get(self.armature_name)
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
        armature_name: str  # type: ignore[no-redef]
        spring_index: int  # type: ignore[no-redef]
        joint_index: int  # type: ignore[no-redef]


class VRM_OT_reset_spring_bone1_animation_state(Operator):
    bl_idname = "vrm.reset_spring_bone1_animation_state"
    bl_label = "Reset SpringBone Animation State"
    bl_description = "Reset SpringBone Animation State"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
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
        armature_name: str  # type: ignore[no-redef]


class VRM_OT_update_spring_bone1_animation(Operator):
    bl_idname = "vrm.update_spring_bone1_animation"
    bl_label = "Update SpringBone Animation"
    bl_description = "Update SpringBone Animation"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

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
