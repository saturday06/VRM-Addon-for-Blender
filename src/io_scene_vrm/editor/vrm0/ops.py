# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import uuid
from collections.abc import Set as AbstractSet
from typing import TYPE_CHECKING

from bpy.props import IntProperty, StringProperty
from bpy.types import Armature, Context, Operator

from ...common.human_bone_mapper.human_bone_mapper import create_human_bone_mapping
from ..extension import get_armature_extension
from .property_group import Vrm0HumanoidPropertyGroup


class VRM_OT_add_vrm0_first_person_mesh_annotation(Operator):
    bl_idname = "vrm.add_vrm0_first_person_mesh_annotation"
    bl_label = "Add Mesh Annotation"
    bl_description = "Add VRM 0.x First Person Mesh Annotation"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        first_person = get_armature_extension(armature_data).vrm0.first_person
        first_person.mesh_annotations.add()
        first_person.active_mesh_annotation_index = (
            len(first_person.mesh_annotations) - 1
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]


class VRM_OT_remove_vrm0_first_person_mesh_annotation(Operator):
    bl_idname = "vrm.remove_vrm0_first_person_mesh_annotation"
    bl_label = "Remove Mesh Annotation"
    bl_description = "Remove VRM 0.x First Person Mesh Annotation"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    mesh_annotation_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        first_person = get_armature_extension(armature_data).vrm0.first_person
        if len(first_person.mesh_annotations) <= self.mesh_annotation_index:
            return {"CANCELLED"}
        first_person.mesh_annotations.remove(self.mesh_annotation_index)
        first_person.active_mesh_annotation_index = min(
            first_person.active_mesh_annotation_index,
            max(0, len(first_person.mesh_annotations) - 1),
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        mesh_annotation_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_vrm0_first_person_mesh_annotation(Operator):
    bl_idname = "vrm.move_up_vrm0_first_person_mesh_annotation"
    bl_label = "Move Up Mesh Annotation"
    bl_description = "Move Up VRM 0.x First Person Mesh Annotation"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    mesh_annotation_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        first_person = get_armature_extension(armature_data).vrm0.first_person
        if len(first_person.mesh_annotations) <= self.mesh_annotation_index:
            return {"CANCELLED"}
        if len(first_person.mesh_annotations) <= self.mesh_annotation_index:
            return {"CANCELLED"}
        new_index = (first_person.active_mesh_annotation_index - 1) % len(
            first_person.mesh_annotations
        )
        first_person.mesh_annotations.move(self.mesh_annotation_index, new_index)
        first_person.active_mesh_annotation_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        mesh_annotation_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_vrm0_first_person_mesh_annotation(Operator):
    bl_idname = "vrm.move_down_vrm0_first_person_mesh_annotation"
    bl_label = "Move Down Mesh Annotation"
    bl_description = "Move Down VRM 0.x First Person Mesh Annotation"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    mesh_annotation_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        first_person = get_armature_extension(armature_data).vrm0.first_person
        if len(first_person.mesh_annotations) <= self.mesh_annotation_index:
            return {"CANCELLED"}
        new_index = (first_person.active_mesh_annotation_index + 1) % len(
            first_person.mesh_annotations
        )
        first_person.mesh_annotations.move(self.mesh_annotation_index, new_index)
        first_person.active_mesh_annotation_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        mesh_annotation_index: int  # type: ignore[no-redef]


class VRM_OT_add_vrm0_material_value_bind(Operator):
    bl_idname = "vrm.add_vrm0_material_value_bind"
    bl_label = "Add Material Value Bind"
    bl_description = "Add VRM 0.x Blend Shape Material Value Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    blend_shape_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        blend_shape_groups = get_armature_extension(
            armature_data
        ).vrm0.blend_shape_master.blend_shape_groups
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        blend_shape_group = blend_shape_groups[self.blend_shape_group_index]
        blend_shape_group.material_values.add()
        blend_shape_group.active_material_value_index = (
            len(blend_shape_group.material_values) - 1
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        blend_shape_group_index: int  # type: ignore[no-redef]


class VRM_OT_remove_vrm0_material_value_bind(Operator):
    bl_idname = "vrm.remove_vrm0_material_value_bind"
    bl_label = "Remove Material Value Bind"
    bl_description = "Remove VRM 0.x Blend Shape Material Value Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    blend_shape_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    material_value_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        blend_shape_groups = get_armature_extension(
            armature_data
        ).vrm0.blend_shape_master.blend_shape_groups
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        blend_shape_group = blend_shape_groups[self.blend_shape_group_index]
        if len(blend_shape_group.material_values) <= self.material_value_index:
            return {"CANCELLED"}
        blend_shape_group.material_values.remove(self.material_value_index)
        blend_shape_group.active_material_value_index = min(
            blend_shape_group.active_material_value_index,
            max(0, len(blend_shape_group.material_values) - 1),
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        blend_shape_group_index: int  # type: ignore[no-redef]
        material_value_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_vrm0_material_value_bind(Operator):
    bl_idname = "vrm.move_up_vrm0_material_value_bind"
    bl_label = "Move Up Material Value Bind"
    bl_description = "Move Up VRM 0.x Blend Shape Material Value Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    blend_shape_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    material_value_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        blend_shape_groups = get_armature_extension(
            armature_data
        ).vrm0.blend_shape_master.blend_shape_groups
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        blend_shape_group = blend_shape_groups[self.blend_shape_group_index]
        if len(blend_shape_group.material_values) <= self.material_value_index:
            return {"CANCELLED"}
        new_index = (self.material_value_index - 1) % len(
            blend_shape_group.material_values
        )
        blend_shape_group.material_values.move(self.material_value_index, new_index)
        blend_shape_group.active_material_value_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        blend_shape_group_index: int  # type: ignore[no-redef]
        material_value_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_vrm0_material_value_bind(Operator):
    bl_idname = "vrm.move_down_vrm0_material_value_bind"
    bl_label = "Move Down Material Value Bind"
    bl_description = "Move Down VRM 0.x Blend Shape Material Value Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    blend_shape_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    material_value_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        blend_shape_groups = get_armature_extension(
            armature_data
        ).vrm0.blend_shape_master.blend_shape_groups
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        blend_shape_group = blend_shape_groups[self.blend_shape_group_index]
        if len(blend_shape_group.material_values) <= self.material_value_index:
            return {"CANCELLED"}
        new_index = (self.material_value_index + 1) % len(
            blend_shape_group.material_values
        )
        blend_shape_group.material_values.move(self.material_value_index, new_index)
        blend_shape_group.active_material_value_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        blend_shape_group_index: int  # type: ignore[no-redef]
        material_value_index: int  # type: ignore[no-redef]


class VRM_OT_add_vrm0_material_value_bind_target_value(Operator):
    bl_idname = "vrm.add_vrm0_material_value_bind_target_value"
    bl_label = "Add Value"
    bl_description = "Add VRM 0.x Blend Shape Material Value Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    blend_shape_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    material_value_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        blend_shape_groups = get_armature_extension(
            armature_data
        ).vrm0.blend_shape_master.blend_shape_groups
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        material_values = blend_shape_groups[
            self.blend_shape_group_index
        ].material_values
        if len(material_values) <= self.material_value_index:
            return {"CANCELLED"}
        material_values[self.material_value_index].target_value.add()
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        blend_shape_group_index: int  # type: ignore[no-redef]
        material_value_index: int  # type: ignore[no-redef]


class VRM_OT_remove_vrm0_material_value_bind_target_value(Operator):
    bl_idname = "vrm.remove_vrm0_material_value_bind_target_value"
    bl_label = "Remove Value"
    bl_description = "Remove VRM 0.x Blend Shape Material Value Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    blend_shape_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    material_value_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    target_value_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        blend_shape_groups = get_armature_extension(
            armature_data
        ).vrm0.blend_shape_master.blend_shape_groups
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        material_values = blend_shape_groups[
            self.blend_shape_group_index
        ].material_values
        if len(material_values) <= self.material_value_index:
            return {"CANCELLED"}
        target_value = material_values[self.material_value_index].target_value
        if len(target_value) <= self.target_value_index:
            return {"CANCELLED"}
        target_value.remove(self.target_value_index)
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        blend_shape_group_index: int  # type: ignore[no-redef]
        material_value_index: int  # type: ignore[no-redef]
        target_value_index: int  # type: ignore[no-redef]


class VRM_OT_add_vrm0_blend_shape_bind(Operator):
    bl_idname = "vrm.add_vrm0_blend_shape_bind"
    bl_label = "Add Blend Shape Bind"
    bl_description = "Add VRM 0.x Blend Shape Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    blend_shape_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        blend_shape_groups = get_armature_extension(
            armature_data
        ).vrm0.blend_shape_master.blend_shape_groups
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        blend_shape_group = blend_shape_groups[self.blend_shape_group_index]
        blend_shape_group.binds.add()
        blend_shape_group.active_bind_index = len(blend_shape_group.binds) - 1
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        blend_shape_group_index: int  # type: ignore[no-redef]


class VRM_OT_remove_vrm0_blend_shape_bind(Operator):
    bl_idname = "vrm.remove_vrm0_blend_shape_bind"
    bl_label = "Remove Blend Shape Bind"
    bl_description = "Remove VRM 0.x Blend Shape Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    blend_shape_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    bind_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        blend_shape_groups = get_armature_extension(
            armature_data
        ).vrm0.blend_shape_master.blend_shape_groups
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        blend_shape_group = blend_shape_groups[self.blend_shape_group_index]
        if len(blend_shape_group.binds) <= self.bind_index:
            return {"CANCELLED"}
        blend_shape_group.binds.remove(self.bind_index)
        blend_shape_group.active_bind_index = min(
            blend_shape_group.active_bind_index,
            max(0, len(blend_shape_group.binds) - 1),
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        blend_shape_group_index: int  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_vrm0_blend_shape_bind(Operator):
    bl_idname = "vrm.move_up_vrm0_blend_shape_bind"
    bl_label = "Move Up Blend Shape Bind"
    bl_description = "Move Up VRM 0.x Blend Shape Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    blend_shape_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    bind_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        blend_shape_groups = get_armature_extension(
            armature_data
        ).vrm0.blend_shape_master.blend_shape_groups
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        blend_shape_group = blend_shape_groups[self.blend_shape_group_index]
        if len(blend_shape_group.binds) <= self.bind_index:
            return {"CANCELLED"}
        new_index = (self.bind_index - 1) % len(blend_shape_group.binds)
        blend_shape_group.binds.move(self.bind_index, new_index)
        blend_shape_group.active_bind_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        blend_shape_group_index: int  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_vrm0_blend_shape_bind(Operator):
    bl_idname = "vrm.move_down_vrm0_blend_shape_bind"
    bl_label = "Move Down Blend Shape Bind"
    bl_description = "Move Up VRM 0.x Blend Shape Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    blend_shape_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    bind_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        blend_shape_groups = get_armature_extension(
            armature_data
        ).vrm0.blend_shape_master.blend_shape_groups
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        blend_shape_group = blend_shape_groups[self.blend_shape_group_index]
        if len(blend_shape_group.binds) <= self.bind_index:
            return {"CANCELLED"}
        new_index = (self.bind_index + 1) % len(blend_shape_group.binds)
        blend_shape_group.binds.move(self.bind_index, new_index)
        blend_shape_group.active_bind_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        blend_shape_group_index: int  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_add_vrm0_secondary_animation_collider_group_collider(Operator):
    bl_idname = "vrm.add_vrm0_secondary_animation_collider_group_collider"
    bl_label = "Add Collider"
    bl_description = "Add VRM 0.x Collider"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    collider_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    bone_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
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
        ).vrm0.secondary_animation.collider_groups
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_group = collider_groups[self.collider_group_index]
        collider = collider_group.colliders.add()

        bone_name = self.bone_name
        if not bone_name:
            bone_name = collider_group.node.bone_name
        if bone_name:
            collider_name = f"{bone_name}_collider"
        else:
            collider_name = f"{self.armature_name}_collider"

        obj = context.blend_data.objects.new(name=collider_name, object_data=None)
        collider.bpy_object = obj
        obj.parent = armature
        obj.empty_display_type = "SPHERE"
        obj.empty_display_size = 0.25
        if bone_name:
            obj.parent_type = "BONE"
            obj.parent_bone = bone_name
        else:
            obj.parent_type = "OBJECT"
        context.scene.collection.objects.link(obj)
        collider_group.active_collider_index = len(collider_group.colliders) - 1
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]
        bone_name: str  # type: ignore[no-redef]


class VRM_OT_remove_vrm0_secondary_animation_collider_group_collider(Operator):
    bl_idname = "vrm.remove_vrm0_secondary_animation_collider_group_collider"
    bl_label = "Remove Collider"
    bl_description = "Remove VRM 0.x Collider"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    collider_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    collider_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
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
        ).vrm0.secondary_animation.collider_groups
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_group = collider_groups[self.collider_group_index]
        if len(collider_group.colliders) <= self.collider_index:
            return {"CANCELLED"}
        bpy_object = collider_group.colliders[self.collider_index].bpy_object
        if bpy_object and bpy_object.name in context.scene.collection.objects:
            bpy_object.parent_type = "OBJECT"
            context.scene.collection.objects.unlink(bpy_object)
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


class VRM_OT_move_up_vrm0_secondary_animation_collider_group_collider(Operator):
    bl_idname = "vrm.move_up_vrm0_secondary_animation_collider_group_coll"
    bl_label = "Move Up Collider"
    bl_description = "Move Up VRM 0.x Collider"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    collider_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    collider_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
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
        ).vrm0.secondary_animation.collider_groups
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_group = collider_groups[self.collider_group_index]
        if len(collider_group.colliders) <= self.collider_index:
            return {"CANCELLED"}
        new_index = (self.collider_index - 1) % len(collider_group.colliders)
        collider_group.colliders.move(self.collider_index, new_index)
        collider_group.active_collider_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]
        collider_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_vrm0_secondary_animation_collider_group_collider(Operator):
    bl_idname = "vrm.move_down_vrm0_secondary_animation_collider_group_coll"
    bl_label = "Move Down Collider"
    bl_description = "Move Down VRM 0.x Collider"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    collider_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    collider_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
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
        ).vrm0.secondary_animation.collider_groups
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_group = collider_groups[self.collider_group_index]
        if len(collider_group.colliders) <= self.collider_index:
            return {"CANCELLED"}
        new_index = (self.collider_index + 1) % len(collider_group.colliders)
        collider_group.colliders.move(self.collider_index, new_index)
        collider_group.active_collider_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]
        collider_index: int  # type: ignore[no-redef]


class VRM_OT_add_vrm0_secondary_animation_group_bone(Operator):
    bl_idname = "vrm.add_vrm0_secondary_animation_group_bone"
    bl_label = "Add Bone"
    bl_description = "Add VRM 0.x Secondary Animation Group Bone"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    bone_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        bone_groups = get_armature_extension(
            armature_data
        ).vrm0.secondary_animation.bone_groups
        if len(bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        bone_group = bone_groups[self.bone_group_index]
        bone = bone_group.bones.add()
        bone.armature_data_name = armature_data.name
        bone_group.active_bone_index = len(bone_group.bones) - 1
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        bone_group_index: int  # type: ignore[no-redef]


class VRM_OT_remove_vrm0_secondary_animation_group_bone(Operator):
    bl_idname = "vrm.remove_vrm0_secondary_animation_group_bone"
    bl_label = "Remove Bone"
    bl_description = "Remove VRM 0.x Secondary Animation Group Bone"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    bone_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    bone_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        bone_groups = get_armature_extension(
            armature_data
        ).vrm0.secondary_animation.bone_groups
        if len(bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        bone_group = bone_groups[self.bone_group_index]
        if len(bone_group.bones) <= self.bone_index:
            return {"CANCELLED"}
        bone_group.bones.remove(self.bone_index)
        bone_group.active_bone_index = min(
            bone_group.active_bone_index, max(0, len(bone_group.bones) - 1)
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        bone_group_index: int  # type: ignore[no-redef]
        bone_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_vrm0_secondary_animation_group_bone(Operator):
    bl_idname = "vrm.move_up_vrm0_secondary_animation_group_bone"
    bl_label = "Move Up Bone"
    bl_description = "Move Up VRM 0.x Secondary Animation Group Bone"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    bone_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    bone_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        bone_groups = get_armature_extension(
            armature_data
        ).vrm0.secondary_animation.bone_groups
        if len(bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        bone_group = bone_groups[self.bone_group_index]
        if len(bone_group.bones) <= self.bone_index:
            return {"CANCELLED"}
        new_index = (self.bone_index - 1) % len(bone_group.bones)
        bone_group.bones.move(self.bone_index, new_index)
        bone_group.active_bone_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        bone_group_index: int  # type: ignore[no-redef]
        bone_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_vrm0_secondary_animation_group_bone(Operator):
    bl_idname = "vrm.move_down_vrm0_secondary_animation_group_bone"
    bl_label = "Move Down Bone"
    bl_description = "Move Down VRM 0.x Secondary Animation Group Bone"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    bone_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    bone_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        bone_groups = get_armature_extension(
            armature_data
        ).vrm0.secondary_animation.bone_groups
        if len(bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        bone_group = bone_groups[self.bone_group_index]
        if len(bone_group.bones) <= self.bone_index:
            return {"CANCELLED"}
        new_index = (self.bone_index + 1) % len(bone_group.bones)
        bone_group.bones.move(self.bone_index, new_index)
        bone_group.active_bone_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        bone_group_index: int  # type: ignore[no-redef]
        bone_index: int  # type: ignore[no-redef]


class VRM_OT_add_vrm0_secondary_animation_group_collider_group(Operator):
    bl_idname = "vrm.add_vrm0_secondary_animation_group_collider_group"
    bl_label = "Add Collider Group"
    bl_description = "Add VRM 0.x Secondary Animation Group Collider Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    bone_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        bone_groups = get_armature_extension(
            armature_data
        ).vrm0.secondary_animation.bone_groups
        if len(bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        bone_group = bone_groups[self.bone_group_index]
        collider_group = bone_group.collider_groups.add()
        collider_group.value = ""
        bone_group.active_collider_group_index = len(bone_group.collider_groups) - 1
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        bone_group_index: int  # type: ignore[no-redef]


class VRM_OT_remove_vrm0_secondary_animation_group_collider_group(Operator):
    bl_idname = "vrm.remove_vrm0_secondary_animation_group_collider_group"
    bl_label = "Remove Collider Group"
    bl_description = "Remove VRM 0.x Secondary Animation Group Collider Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    bone_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    collider_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        bone_groups = get_armature_extension(
            armature_data
        ).vrm0.secondary_animation.bone_groups
        if len(bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        bone_group = bone_groups[self.bone_group_index]
        if len(bone_group.collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        bone_group.collider_groups.remove(self.collider_group_index)
        bone_group.active_collider_group_index = min(
            bone_group.active_collider_group_index,
            max(0, len(bone_group.collider_groups) - 1),
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        bone_group_index: int  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_vrm0_secondary_animation_group_collider_group(Operator):
    bl_idname = "vrm.move_up_vrm0_secondary_animation_group_collider_group"
    bl_label = "Move Up Collider Group"
    bl_description = "Move Up VRM 0.x Secondary Animation Group Collider Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    bone_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    collider_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        bone_groups = get_armature_extension(
            armature_data
        ).vrm0.secondary_animation.bone_groups
        if len(bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        bone_group = bone_groups[self.bone_group_index]
        if len(bone_group.collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        new_index = (self.collider_group_index - 1) % len(bone_group.collider_groups)
        bone_group.collider_groups.move(self.collider_group_index, new_index)
        bone_group.active_collider_group_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        bone_group_index: int  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_vrm0_secondary_animation_group_collider_group(Operator):
    bl_idname = "vrm.move_down_vrm0_secondary_animation_group_collider_group"
    bl_label = "Move Down Collider Group"
    bl_description = "Move Down VRM 0.x Secondary Animation Group Collider Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    bone_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )
    collider_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        bone_groups = get_armature_extension(
            armature_data
        ).vrm0.secondary_animation.bone_groups
        if len(bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        bone_group = bone_groups[self.bone_group_index]
        if len(bone_group.collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        new_index = (self.collider_group_index + 1) % len(bone_group.collider_groups)
        bone_group.collider_groups.move(self.collider_group_index, new_index)
        bone_group.active_collider_group_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        bone_group_index: int  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_add_vrm0_blend_shape_group(Operator):
    bl_idname = "vrm.add_vrm0_blend_shape_group"
    bl_label = "Add Blend Shape Group"
    bl_description = "Add VRM 0.x Blend Shape Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        blend_shape_master = get_armature_extension(
            armature_data
        ).vrm0.blend_shape_master
        blend_shape_group = blend_shape_master.blend_shape_groups.add()
        blend_shape_group.name = self.name
        blend_shape_master.active_blend_shape_group_index = (
            len(blend_shape_master.blend_shape_groups) - 1
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        name: str  # type: ignore[no-redef]


class VRM_OT_remove_vrm0_blend_shape_group(Operator):
    bl_idname = "vrm.remove_vrm0_blend_shape_group"
    bl_label = "Remove Blend Shape Group"
    bl_description = "Remove VRM 0.x Blend Shape Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    blend_shape_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        blend_shape_master = get_armature_extension(
            armature_data
        ).vrm0.blend_shape_master
        if len(blend_shape_master.blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        blend_shape_master.blend_shape_groups.remove(self.blend_shape_group_index)
        blend_shape_master.active_blend_shape_group_index = min(
            blend_shape_master.active_blend_shape_group_index,
            max(0, len(blend_shape_master.blend_shape_groups) - 1),
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        blend_shape_group_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_vrm0_blend_shape_group(Operator):
    bl_idname = "vrm.move_up_vrm0_blend_shape_group"
    bl_label = "Move Up Blend Shape Group"
    bl_description = "Move Up VRM 0.x Blend Shape Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    blend_shape_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        blend_shape_master = get_armature_extension(
            armature_data
        ).vrm0.blend_shape_master
        if len(blend_shape_master.blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        new_index = (self.blend_shape_group_index - 1) % len(
            blend_shape_master.blend_shape_groups
        )
        blend_shape_master.blend_shape_groups.move(
            self.blend_shape_group_index, new_index
        )
        blend_shape_master.active_blend_shape_group_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        blend_shape_group_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_vrm0_blend_shape_group(Operator):
    bl_idname = "vrm.move_down_vrm0_blend_shape_group"
    bl_label = "Move Down Blend Shape Group"
    bl_description = "Move Down VRM 0.x Blend Shape Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    blend_shape_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        blend_shape_master = get_armature_extension(
            armature_data
        ).vrm0.blend_shape_master
        if len(blend_shape_master.blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        new_index = (self.blend_shape_group_index + 1) % len(
            blend_shape_master.blend_shape_groups
        )
        blend_shape_master.blend_shape_groups.move(
            self.blend_shape_group_index, new_index
        )
        blend_shape_master.active_blend_shape_group_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        blend_shape_group_index: int  # type: ignore[no-redef]


class VRM_OT_add_vrm0_secondary_animation_group(Operator):
    bl_idname = "vrm.add_vrm0_secondary_animation_group"
    bl_label = "Add Spring Bone"
    bl_description = "Add VRM 0.x Secondary Animation Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )

    # Unnecessary property. Please do not use.
    blend_shape_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        secondary_animation = get_armature_extension(
            armature_data
        ).vrm0.secondary_animation
        secondary_animation.bone_groups.add()
        secondary_animation.active_bone_group_index = (
            len(secondary_animation.bone_groups) - 1
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        blend_shape_group_index: int  # type: ignore[no-redef]


class VRM_OT_remove_vrm0_secondary_animation_group(Operator):
    bl_idname = "vrm.remove_vrm0_secondary_animation_group"
    bl_label = "Remove Spring Bone"
    bl_description = "Remove VRM 0.x Secondary Animation Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    bone_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        secondary_animation = get_armature_extension(
            armature_data
        ).vrm0.secondary_animation
        if len(secondary_animation.bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        secondary_animation.bone_groups.remove(self.bone_group_index)
        secondary_animation.active_bone_group_index = min(
            secondary_animation.active_bone_group_index,
            max(0, len(secondary_animation.bone_groups) - 1),
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        bone_group_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_vrm0_secondary_animation_group(Operator):
    bl_idname = "vrm.move_up_vrm0_secondary_animation_group"
    bl_label = "Move Up Spring Bone"
    bl_description = "Move Up VRM 0.x Secondary Animation Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    bone_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        secondary_animation = get_armature_extension(
            armature_data
        ).vrm0.secondary_animation
        if len(secondary_animation.bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        new_index = (self.bone_group_index - 1) % len(secondary_animation.bone_groups)
        secondary_animation.bone_groups.move(self.bone_group_index, new_index)
        secondary_animation.active_bone_group_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        bone_group_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_vrm0_secondary_animation_group(Operator):
    bl_idname = "vrm.move_down_vrm0_secondary_animation_group"
    bl_label = "Move Down Spring Bone"
    bl_description = "Move Down VRM 0.x Secondary Animation Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    bone_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        secondary_animation = get_armature_extension(
            armature_data
        ).vrm0.secondary_animation
        if len(secondary_animation.bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        new_index = (self.bone_group_index + 1) % len(secondary_animation.bone_groups)
        secondary_animation.bone_groups.move(self.bone_group_index, new_index)
        secondary_animation.active_bone_group_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        bone_group_index: int  # type: ignore[no-redef]


class VRM_OT_add_vrm0_secondary_animation_collider_group(Operator):
    bl_idname = "vrm.add_vrm0_secondary_animation_collider_group"
    bl_label = "Add Collider Group"
    bl_description = "Add VRM 0.x Secondary Animation Collider Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        ext = get_armature_extension(armature_data)
        secondary_animation = ext.vrm0.secondary_animation
        collider_group = secondary_animation.collider_groups.add()
        collider_group.uuid = uuid.uuid4().hex
        collider_group.refresh(armature)
        secondary_animation.active_collider_group_index = (
            len(secondary_animation.collider_groups) - 1
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]


class VRM_OT_remove_vrm0_secondary_animation_collider_group(Operator):
    bl_idname = "vrm.remove_vrm0_secondary_animation_collider_group"
    bl_label = "Remove Collider Group"
    bl_description = "Remove VRM 0.x Secondary Animation Collider Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    collider_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        secondary_animation = get_armature_extension(
            armature_data
        ).vrm0.secondary_animation
        if len(secondary_animation.collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        secondary_animation.collider_groups.remove(self.collider_group_index)

        for bone_group in get_armature_extension(
            armature_data
        ).vrm0.secondary_animation.bone_groups:
            bone_group.refresh(armature)

        secondary_animation.active_collider_group_index = min(
            secondary_animation.active_collider_group_index,
            max(0, len(secondary_animation.collider_groups) - 1),
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_vrm0_secondary_animation_collider_group(Operator):
    bl_idname = "vrm.move_up_vrm0_secondary_animation_collider_group"
    bl_label = "Move Up Collider Group"
    bl_description = "Move Up VRM 0.x Secondary Animation Collider Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    collider_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        secondary_animation = get_armature_extension(
            armature_data
        ).vrm0.secondary_animation
        if len(secondary_animation.collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        new_index = (self.collider_group_index - 1) % len(
            secondary_animation.collider_groups
        )
        secondary_animation.collider_groups.move(self.collider_group_index, new_index)
        secondary_animation.active_collider_group_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_vrm0_secondary_animation_collider_group(Operator):
    bl_idname = "vrm.move_down_vrm0_secondary_animation_collider_group"
    bl_label = "Move Down Collider Group"
    bl_description = "Move Down VRM 0.x Secondary Animation Collider Group"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    collider_group_index: IntProperty(  # type: ignore[valid-type]
        min=0,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        secondary_animation = get_armature_extension(
            armature_data
        ).vrm0.secondary_animation
        if len(secondary_animation.collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        new_index = (self.collider_group_index + 1) % len(
            secondary_animation.collider_groups
        )
        secondary_animation.collider_groups.move(self.collider_group_index, new_index)
        secondary_animation.active_collider_group_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        collider_group_index: int  # type: ignore[no-redef]


class VRM_OT_assign_vrm0_humanoid_human_bones_automatically(Operator):
    bl_idname = "vrm.assign_vrm0_humanoid_human_bones_automatically"
    bl_label = "Automatic Bone Assignment"
    bl_description = "Assign VRM 0.x Humanoid Human Bones"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}

        Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
        humanoid = get_armature_extension(armature_data).vrm0.humanoid
        bones = armature_data.bones
        for (
            bone_name,
            vrm1_specification,
        ) in create_human_bone_mapping(armature).items():
            bone = bones.get(bone_name)
            if not bone:
                continue
            human_bone_name = vrm1_specification.vrm0_name

            for human_bone in humanoid.human_bones:
                if (
                    human_bone.bone != human_bone_name.value
                    or human_bone.node.bone_name in human_bone.node_candidates
                    or bone_name not in human_bone.node_candidates
                ):
                    continue
                human_bone.node.set_bone_name(bone_name)
                break

        Vrm0HumanoidPropertyGroup.update_all_node_candidates(
            context, armature_data.name, force=True
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
