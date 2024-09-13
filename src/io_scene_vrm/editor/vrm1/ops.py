from collections.abc import Set as AbstractSet
from typing import TYPE_CHECKING, Protocol, ClassVar

import bmesh
import bpy
from bpy.props import IntProperty, StringProperty, CollectionProperty
from bpy.types import Armature, Context, Material, Operator, NodeTree

from ...common import ops
from ...common.human_bone_mapper.human_bone_mapper import create_human_bone_mapping
from ...common.logging import get_logger
from ...common.vrm0.human_bone import HumanBoneName as Vrm0HumanBoneName
from ...common.vrm1.human_bone import HumanBoneName, HumanBoneSpecifications
from ..extension import get_armature_extension
from ..vrm0.property_group import Vrm0HumanoidPropertyGroup
from .property_group import (
    Vrm1HumanBonesPropertyGroup,
    Vrm1ExpressionPropertyGroup,
    Vrm1TextureTransformBindPropertyGroup,
)

logger = get_logger(__name__)


class VRM_OT_add_vrm1_meta_author(Operator):
    bl_idname = "vrm.add_vrm1_meta_author"
    bl_label = "Add Author"
    bl_description = "Add VRM 1.0 Meta Author"
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
        meta = get_armature_extension(armature_data).vrm1.meta
        author = meta.authors.add()
        author.value = ""
        meta.active_author_index = len(meta.authors) - 1
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]


class VRM_OT_remove_vrm1_meta_author(Operator):
    bl_idname = "vrm.remove_vrm1_meta_author"
    bl_label = "Remove Author"
    bl_description = "Remove VRM 1.0 Meta Author"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    author_index: IntProperty(  # type: ignore[valid-type]
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
        meta = get_armature_extension(armature_data).vrm1.meta
        if len(meta.authors) <= self.author_index:
            return {"CANCELLED"}
        meta.authors.remove(self.author_index)
        meta.active_author_index = min(
            meta.active_author_index,
            max(0, len(meta.authors) - 1),
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        author_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_vrm1_meta_author(Operator):
    bl_idname = "vrm.move_up_vrm1_meta_author"
    bl_label = "Move Up Author"
    bl_description = "Move Up VRM 1.0 Meta Author"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    author_index: IntProperty(  # type: ignore[valid-type]
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
        meta = get_armature_extension(armature_data).vrm1.meta
        if len(meta.authors) <= self.author_index:
            return {"CANCELLED"}
        new_index = (self.author_index - 1) % len(meta.authors)
        meta.authors.move(self.author_index, new_index)
        meta.active_author_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        author_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_vrm1_meta_author(Operator):
    bl_idname = "vrm.move_down_vrm1_meta_author"
    bl_label = "Move Down Author"
    bl_description = "Move Down VRM 1.0 Meta Author"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    author_index: IntProperty(  # type: ignore[valid-type]
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
        meta = get_armature_extension(armature_data).vrm1.meta
        if len(meta.authors) <= self.author_index:
            return {"CANCELLED"}
        new_index = (self.author_index + 1) % len(meta.authors)
        meta.authors.move(self.author_index, new_index)
        meta.active_author_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        author_index: int  # type: ignore[no-redef]


class VRM_OT_add_vrm1_meta_reference(Operator):
    bl_idname = "vrm.add_vrm1_meta_reference"
    bl_label = "Add Reference"
    bl_description = "Add VRM 1.0 Meta Reference"
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
        meta = get_armature_extension(armature_data).vrm1.meta
        reference = meta.references.add()
        reference.value = ""
        meta.active_reference_index = len(meta.references) - 1
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]


class VRM_OT_remove_vrm1_meta_reference(Operator):
    bl_idname = "vrm.remove_vrm1_meta_reference"
    bl_label = "Remove Reference"
    bl_description = "Remove VRM 1.0 Meta Reference"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    reference_index: IntProperty(  # type: ignore[valid-type]
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
        meta = get_armature_extension(armature_data).vrm1.meta
        if len(meta.references) <= self.reference_index:
            return {"CANCELLED"}
        meta.references.remove(self.reference_index)
        meta.active_reference_index = min(
            meta.active_reference_index,
            max(0, len(meta.references) - 1),
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        reference_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_vrm1_meta_reference(Operator):
    bl_idname = "vrm.move_up_vrm1_meta_reference"
    bl_label = "Move Up Reference"
    bl_description = "Move Up VRM 1.0 Meta Reference"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    reference_index: IntProperty(  # type: ignore[valid-type]
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
        meta = get_armature_extension(armature_data).vrm1.meta
        if len(meta.references) <= self.reference_index:
            return {"CANCELLED"}
        new_index = (self.reference_index - 1) % len(meta.references)
        meta.references.move(self.reference_index, new_index)
        meta.active_reference_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        reference_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_vrm1_meta_reference(Operator):
    bl_idname = "vrm.move_down_vrm1_meta_reference"
    bl_label = "Move Down Reference"
    bl_description = "Move Down VRM 1.0 Meta Reference"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    reference_index: IntProperty(  # type: ignore[valid-type]
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
        meta = get_armature_extension(armature_data).vrm1.meta
        if len(meta.references) <= self.reference_index:
            return {"CANCELLED"}
        new_index = (self.reference_index + 1) % len(meta.references)
        meta.references.move(self.reference_index, new_index)
        meta.active_reference_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        reference_index: int  # type: ignore[no-redef]


class VRM_OT_add_vrm1_expressions_custom_expression(Operator):
    bl_idname = "vrm.add_vrm1_expressions_custom_expression"
    bl_label = "Add Custom Expression"
    bl_description = "Add VRM 1.0 Custom Expression"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    custom_expression_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        expressions = get_armature_extension(armature_data).vrm1.expressions
        new_last_custom_index = len(expressions.custom)
        custom_expression = expressions.custom.add()
        custom_expression.custom_name = self.custom_expression_name
        expressions.active_expression_ui_list_element_index = (
            len(expressions.preset.name_to_expression_dict()) + new_last_custom_index
        )
        return ops.vrm.update_vrm1_expression_ui_list_elements()

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        custom_expression_name: str  # type: ignore[no-redef]


class VRM_OT_remove_vrm1_expressions_custom_expression(Operator):
    bl_idname = "vrm.remove_vrm1_expressions_custom_expression"
    bl_label = "Remove Custom Expression"
    bl_description = "Remove VRM 1.0 Custom Expression"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    custom_expression_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        expressions = get_armature_extension(armature_data).vrm1.expressions
        for custom_index, custom_expression in enumerate(
            list(expressions.custom.values())
        ):
            if custom_expression.custom_name == self.custom_expression_name:
                expressions.custom.remove(custom_index)
                expressions.active_expression_ui_list_element_index = min(
                    expressions.active_expression_ui_list_element_index,
                    len(expressions.all_name_to_expression_dict()) - 1,
                )
                return ops.vrm.update_vrm1_expression_ui_list_elements()
        return {"CANCELLED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        custom_expression_name: str  # type: ignore[no-redef]


class VRM_OT_move_up_vrm1_expressions_custom_expression(Operator):
    bl_idname = "vrm.move_up_vrm1_expressions_custom_expression"
    bl_label = "Move Up Custom Expression"
    bl_description = "Move Up VRM 1.0 Custom Expression"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    custom_expression_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        expressions = get_armature_extension(armature_data).vrm1.expressions
        expression_index = next(
            (
                i
                for i, expression in enumerate(expressions.custom)
                if expression.custom_name == self.custom_expression_name
            ),
            None,
        )
        if expression_index is None:
            return {"CANCELLED"}
        new_expression_index = (expression_index - 1) % len(expressions.custom)
        expressions.custom.move(expression_index, new_expression_index)
        expressions.active_expression_ui_list_element_index = (
            len(expressions.preset.name_to_expression_dict()) + new_expression_index
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        custom_expression_name: str  # type: ignore[no-redef]


class VRM_OT_move_down_vrm1_expressions_custom_expression(Operator):
    bl_idname = "vrm.move_down_vrm1_expressions_custom_expression"
    bl_label = "Move Down Custom Expression"
    bl_description = "Move Down VRM 1.0 Custom Expression"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    custom_expression_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        expressions = get_armature_extension(armature_data).vrm1.expressions
        expression_index = next(
            (
                i
                for i, expression in enumerate(expressions.custom)
                if expression.custom_name == self.custom_expression_name
            ),
            None,
        )
        if expression_index is None:
            return {"CANCELLED"}
        new_expression_index = (expression_index + 1) % len(expressions.custom)
        expressions.custom.move(expression_index, new_expression_index)
        expressions.active_expression_ui_list_element_index = (
            len(expressions.preset.name_to_expression_dict()) + new_expression_index
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        custom_expression_name: str  # type: ignore[no-redef]


class VRM_OT_add_vrm1_first_person_mesh_annotation(Operator):
    bl_idname = "vrm.add_vrm1_first_person_mesh_annotation"
    bl_label = "Add Mesh Annotation"
    bl_description = "Add VRM 1.0 First Person Mesh Annotation"
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
        first_person = get_armature_extension(armature_data).vrm1.first_person
        first_person.mesh_annotations.add()
        first_person.active_mesh_annotation_index = (
            len(first_person.mesh_annotations) - 1
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]


class VRM_OT_remove_vrm1_first_person_mesh_annotation(Operator):
    bl_idname = "vrm.remove_vrm1_first_person_mesh_annotation"
    bl_label = "Remove Mesh Annotation"
    bl_description = "Remove VRM 1.0 First Person Mesh Annotation"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    mesh_annotation_index: IntProperty(  # type: ignore[valid-type]
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
        first_person = get_armature_extension(armature_data).vrm1.first_person
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


class VRM_OT_move_up_vrm1_first_person_mesh_annotation(Operator):
    bl_idname = "vrm.move_up_vrm1_first_person_mesh_annotation"
    bl_label = "Move Up Mesh Annotation"
    bl_description = "Move Up VRM 1.0 First Person Mesh Annotation"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    mesh_annotation_index: IntProperty(  # type: ignore[valid-type]
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
        first_person = get_armature_extension(armature_data).vrm1.first_person
        if len(first_person.mesh_annotations) <= self.mesh_annotation_index:
            return {"CANCELLED"}
        new_index = (self.mesh_annotation_index - 1) % len(
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


class VRM_OT_move_down_vrm1_first_person_mesh_annotation(Operator):
    bl_idname = "vrm.move_down_vrm1_first_person_mesh_annotation"
    bl_label = "Move Down Mesh Annotation"
    bl_description = "Move Down VRM 1.0 First Person Mesh Annotation"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    mesh_annotation_index: IntProperty(  # type: ignore[valid-type]
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
        first_person = get_armature_extension(armature_data).vrm1.first_person
        if len(first_person.mesh_annotations) <= self.mesh_annotation_index:
            return {"CANCELLED"}
        new_index = (self.mesh_annotation_index + 1) % len(
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


class VRM_OT_add_vrm1_expression_morph_target_bind(Operator):
    bl_idname = "vrm.add_vrm1_expression_morph_target_bind"
    bl_label = "Add Morph Target Bind"
    bl_description = "Add VRM 1.0 Expression Morph Target Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    expression_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        expressions = get_armature_extension(armature_data).vrm1.expressions
        expression = expressions.all_name_to_expression_dict().get(self.expression_name)
        if expression is None:
            return {"CANCELLED"}
        expression.morph_target_binds.add()
        expression.active_morph_target_bind_index = (
            len(expression.morph_target_binds) - 1
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]


class VRM_OT_remove_vrm1_expression_morph_target_bind(Operator):
    bl_idname = "vrm.remove_vrm1_expression_morph_target_bind"
    bl_label = "Remove Morph Target Bind"
    bl_description = "Remove VRM 1.0 Expression Morph Target Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    expression_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    bind_index: IntProperty(  # type: ignore[valid-type]
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
        expressions = get_armature_extension(armature_data).vrm1.expressions
        expression = expressions.all_name_to_expression_dict().get(self.expression_name)
        if expression is None:
            return {"CANCELLED"}
        if len(expression.morph_target_binds) <= self.bind_index:
            return {"CANCELLED"}
        expression.morph_target_binds.remove(self.bind_index)
        expression.active_morph_target_bind_index = min(
            expression.active_morph_target_bind_index,
            max(0, len(expression.morph_target_binds) - 1),
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_vrm1_expression_morph_target_bind(Operator):
    bl_idname = "vrm.move_up_vrm1_expression_morph_target_bind"
    bl_label = "Move Up Morph Target Bind"
    bl_description = "Move Up VRM 1.0 Expression Morph Target Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    expression_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    bind_index: IntProperty(  # type: ignore[valid-type]
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
        expressions = get_armature_extension(armature_data).vrm1.expressions
        expression = expressions.all_name_to_expression_dict().get(self.expression_name)
        if expression is None:
            return {"CANCELLED"}
        if len(expression.morph_target_binds) <= self.bind_index:
            return {"CANCELLED"}
        new_bind_index = (self.bind_index - 1) % len(expression.morph_target_binds)
        expression.morph_target_binds.move(self.bind_index, new_bind_index)
        expression.active_morph_target_bind_index = new_bind_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_vrm1_expression_morph_target_bind(Operator):
    bl_idname = "vrm.move_down_vrm1_expression_morph_target_bind"
    bl_label = "Move Down Morph Target Bind"
    bl_description = "Move Down VRM 1.0 Expression Morph Target Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    expression_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    bind_index: IntProperty(  # type: ignore[valid-type]
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
        expressions = get_armature_extension(armature_data).vrm1.expressions
        expression = expressions.all_name_to_expression_dict().get(self.expression_name)
        if expression is None:
            return {"CANCELLED"}
        if len(expression.morph_target_binds) <= self.bind_index:
            return {"CANCELLED"}
        new_bind_index = (self.bind_index + 1) % len(expression.morph_target_binds)
        expression.morph_target_binds.move(self.bind_index, new_bind_index)
        expression.active_morph_target_bind_index = new_bind_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_add_vrm1_expression_material_color_bind(Operator):
    bl_idname = "vrm.add_vrm1_expression_material_color_bind"
    bl_label = "Add Material Color Bind"
    bl_description = "Add VRM 1.0 Expression Material Value Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    expression_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        ext = get_armature_extension(armature_data)
        expression = ext.vrm1.expressions.all_name_to_expression_dict().get(
            self.expression_name
        )
        if expression is None:
            return {"CANCELLED"}
        expression.material_color_binds.add()
        expression.active_material_color_bind_index = (
            len(expression.material_color_binds) - 1
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]


class VRM_OT_remove_vrm1_expression_material_color_bind(Operator):
    bl_idname = "vrm.remove_vrm1_expression_material_color_bind"
    bl_label = "Remove Material Color Bind"
    bl_description = "Remove VRM 1.0 Expression Material Color Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    expression_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    bind_index: IntProperty(  # type: ignore[valid-type]
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
        expressions = get_armature_extension(armature_data).vrm1.expressions
        expression = expressions.all_name_to_expression_dict().get(self.expression_name)
        if expression is None:
            return {"CANCELLED"}
        if len(expression.material_color_binds) <= self.bind_index:
            return {"CANCELLED"}
        expression.material_color_binds.remove(self.bind_index)
        expression.active_material_color_bind_index = min(
            expression.active_material_color_bind_index,
            max(0, len(expression.material_color_binds) - 1),
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_vrm1_expression_material_color_bind(Operator):
    bl_idname = "vrm.move_up_vrm1_expression_material_color_bind"
    bl_label = "Move Up Material Color Bind"
    bl_description = "Move Up VRM 1.0 Expression Material Color Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    expression_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    bind_index: IntProperty(  # type: ignore[valid-type]
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
        expressions = get_armature_extension(armature_data).vrm1.expressions
        expression = expressions.all_name_to_expression_dict().get(self.expression_name)
        if expression is None:
            return {"CANCELLED"}
        if len(expression.material_color_binds) <= self.bind_index:
            return {"CANCELLED"}
        new_bind_index = (self.bind_index - 1) % len(expression.material_color_binds)
        expression.material_color_binds.move(self.bind_index, new_bind_index)
        expression.active_material_color_bind_index = new_bind_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_vrm1_expression_material_color_bind(Operator):
    bl_idname = "vrm.move_down_vrm1_expression_material_color_bind"
    bl_label = "Move Down Material Color Bind"
    bl_description = "Move Down VRM 1.0 Expression Material Color Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    expression_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    bind_index: IntProperty(  # type: ignore[valid-type]
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
        expressions = get_armature_extension(armature_data).vrm1.expressions
        expression = expressions.all_name_to_expression_dict().get(self.expression_name)
        if expression is None:
            return {"CANCELLED"}
        if len(expression.material_color_binds) <= self.bind_index:
            return {"CANCELLED"}
        new_bind_index = (self.bind_index + 1) % len(expression.material_color_binds)
        expression.material_color_binds.move(self.bind_index, new_bind_index)
        expression.active_material_color_bind_index = new_bind_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_add_vrm1_expression_texture_transform_bind(Operator):
    bl_idname = "vrm.add_vrm1_expression_texture_transform_bind"
    bl_label = "Add Texture Transform Bind"
    bl_description = "Add VRM 1.0 Expression Texture Transform Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    expression_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        expressions = get_armature_extension(armature_data).vrm1.expressions
        expression = expressions.all_name_to_expression_dict().get(self.expression_name)
        if expression is None:
            return {"CANCELLED"}
        expression.texture_transform_binds.add()
        expression.active_texture_transform_bind_index = (
            len(expression.texture_transform_binds) - 1
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]


class VRM_OT_remove_vrm1_expression_texture_transform_bind(Operator):
    bl_idname = "vrm.remove_vrm1_expression_texture_transform_bind"
    bl_label = "Remove Texture Transform Bind"
    bl_description = "Remove VRM 1.0 Expression Texture Transform Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    expression_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    bind_index: IntProperty(  # type: ignore[valid-type]
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
        expressions = get_armature_extension(armature_data).vrm1.expressions
        expression = expressions.all_name_to_expression_dict().get(self.expression_name)
        if expression is None:
            return {"CANCELLED"}
        if len(expression.texture_transform_binds) <= self.bind_index:
            return {"CANCELLED"}
        expression.texture_transform_binds.remove(self.bind_index)
        expression.active_texture_transform_bind_index = min(
            expression.active_texture_transform_bind_index,
            max(0, len(expression.texture_transform_binds) - 1),
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_vrm1_expression_texture_transform_bind(Operator):
    bl_idname = "vrm.move_up_vrm1_expression_texture_transform_bind"
    bl_label = "Move Up Texture Transform Bind"
    bl_description = "Move Up VRM 1.0 Expression Texture Transform Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    expression_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    bind_index: IntProperty(  # type: ignore[valid-type]
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
        expressions = get_armature_extension(armature_data).vrm1.expressions
        expression = expressions.all_name_to_expression_dict().get(self.expression_name)
        if expression is None:
            return {"CANCELLED"}
        if len(expression.texture_transform_binds) <= self.bind_index:
            return {"CANCELLED"}
        new_bind_index = (self.bind_index - 1) % len(expression.texture_transform_binds)
        expression.texture_transform_binds.move(self.bind_index, new_bind_index)
        expression.active_texture_transform_bind_index = new_bind_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_vrm1_expression_texture_transform_bind(Operator):
    bl_idname = "vrm.move_down_vrm1_expression_texture_transform_bind"
    bl_label = "Move Down Morph Target Bind"
    bl_description = "Move Down VRM 1.0 Expression Morph Target Bind"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    expression_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    bind_index: IntProperty(  # type: ignore[valid-type]
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
        expressions = get_armature_extension(armature_data).vrm1.expressions
        expression = expressions.all_name_to_expression_dict().get(self.expression_name)
        if expression is None:
            return {"CANCELLED"}
        if len(expression.texture_transform_binds) <= self.bind_index:
            return {"CANCELLED"}
        new_bind_index = (self.bind_index + 1) % len(expression.texture_transform_binds)
        expression.texture_transform_binds.move(self.bind_index, new_bind_index)
        expression.active_texture_transform_bind_index = new_bind_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


vrm0_human_bone_name_to_vrm1_human_bone_name: dict[Vrm0HumanBoneName, HumanBoneName] = {
    specification.vrm0_name: specification.name
    for specification in HumanBoneSpecifications.all_human_bones
}


class VRM_OT_assign_vrm1_humanoid_human_bones_automatically(Operator):
    bl_idname = "vrm.assign_vrm1_humanoid_human_bones_automatically"
    bl_label = "Automatic Bone Assignment"
    bl_description = "Assign VRM 1.0 Humanoid Human Bones"
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
        Vrm1HumanBonesPropertyGroup.fixup_human_bones(armature)
        Vrm1HumanBonesPropertyGroup.update_all_node_candidates(
            context, armature_data.name
        )
        human_bones = get_armature_extension(armature_data).vrm1.humanoid.human_bones
        human_bone_name_to_human_bone = human_bones.human_bone_name_to_human_bone()
        bones = armature_data.bones

        Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
        Vrm0HumanoidPropertyGroup.update_all_node_candidates(
            context, armature_data.name
        )
        vrm0_humanoid = get_armature_extension(armature_data).vrm0.humanoid
        if vrm0_humanoid.all_required_bones_are_assigned():
            for vrm0_human_bone in vrm0_humanoid.human_bones:
                if (
                    vrm0_human_bone.node.bone_name
                    not in vrm0_human_bone.node_candidates
                ):
                    continue
                vrm0_name = Vrm0HumanBoneName.from_str(vrm0_human_bone.bone)
                if not vrm0_name:
                    logger.error("Invalid VRM0 bone name str: %s", vrm0_human_bone.bone)
                    continue
                vrm1_name = vrm0_human_bone_name_to_vrm1_human_bone_name.get(vrm0_name)
                if vrm1_name is None:
                    logger.error("Invalid VRM0 bone name: %s", vrm0_name)
                    continue
                human_bone = human_bone_name_to_human_bone.get(vrm1_name)
                if not human_bone:
                    continue
                if vrm0_human_bone.node.bone_name not in human_bone.node_candidates:
                    continue
                human_bone.node.set_bone_name(vrm0_human_bone.node.bone_name)

        for (
            bone_name,
            specification,
        ) in create_human_bone_mapping(armature).items():
            bone = bones.get(bone_name)
            if not bone:
                continue

            for search_name, human_bone in human_bone_name_to_human_bone.items():
                if (
                    specification.name != search_name
                    or human_bone.node.bone_name in human_bone.node_candidates
                    or bone_name not in human_bone.node_candidates
                ):
                    continue
                human_bone.node.set_bone_name(bone_name)
                break

        Vrm1HumanBonesPropertyGroup.update_all_node_candidates(
            context, armature_data.name, force=True
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]


class VRM_OT_update_vrm1_expression_ui_list_elements(Operator):
    bl_idname = "vrm.update_vrm1_expression_ui_list_elements"
    bl_label = "Update VRM 1.0 Expression UI List Elements"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    def execute(self, context: Context) -> set[str]:
        for armature in context.blend_data.armatures:
            expressions = get_armature_extension(armature).vrm1.expressions

            # Set the number of elements equal to the number of elements wanted to show
            # in the UIList.
            ui_len = len(expressions.expression_ui_list_elements)
            all_len = len(expressions.all_name_to_expression_dict())
            if ui_len == all_len:
                continue
            if ui_len > all_len:
                for _ in range(ui_len - all_len):
                    expressions.expression_ui_list_elements.remove(0)
            if all_len > ui_len:
                for _ in range(all_len - ui_len):
                    expressions.expression_ui_list_elements.add()
        return {"FINISHED"}


class TextureTransformBind(Protocol):
    material: Material
    scale: tuple[float, float]
    offset: tuple[float, float]


class VRM_OT_refresh_vrm1_expression_texture_transform_bind_preview(Operator):
    bl_idname = "vrm.refresh_vrm1_expression_texture_transform_bind_preview"
    bl_label = "Refresh Texture Transform Bind Preview"
    bl_description = "Refresh VRM 1.0 Expression Texture Transform Bind Preview"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    expression_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )

    preset_name_mapping: ClassVar[dict[str, str]] = {
        "neutral": "neutral",
        "aa": "aa",
        "ih": "ih",
        "ou": "ou",
        "ee": "ee",
        "oh": "oh",
        "blink": "blink",
        "joy": "happy",
        "angry": "angry",
        "sorrow": "sad",
        "fun": "surprised",
        "relaxed": "relaxed",
        "blinkLeft": "blink_left",
        "blinkRight": "blink_right",
        "lookUp": "look_up",
        "lookDown": "look_down",
        "lookLeft": "look_left",
        "lookRight": "look_right",
    }

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        expressions = get_armature_extension(armature_data).vrm1.expressions
        all_expressions = self.get_all_expressions(expressions)

        materials_to_update = set()
        for expression, expr_type, expr_name in all_expressions:
            for bind in expression.texture_transform_binds:
                if bind.material:
                    materials_to_update.add(bind.material)

        for material in materials_to_update:
            self.setup_uv_offset_nodes(context, armature, material, all_expressions)
            new_item = expression.materials_to_update.add()
            new_item.name = material.name
            material.update_tag()

        return {"FINISHED"}

    def get_all_expressions(
        self, expressions
    ) -> list[tuple[Vrm1ExpressionPropertyGroup, str, str]]:
        all_expressions: list[tuple[Vrm1ExpressionPropertyGroup, str, str]] = []
        if expressions is not None:
            for preset_name in self.preset_name_mapping.values():
                preset_expr = getattr(expressions.preset, preset_name, None)
                if preset_expr and any(
                    bind.material for bind in preset_expr.texture_transform_binds
                ):
                    all_expressions.append((preset_expr, "preset", preset_name))
            for i, custom_expr in enumerate(expressions.custom):
                if any(bind.material for bind in custom_expr.texture_transform_binds):
                    all_expressions.append((custom_expr, "custom", str(i)))
        return all_expressions

    def setup_uv_offset_nodes(
        self,
        context: Context,
        armature: bpy.types.Object,
        material: Material,
        all_expressions: list[tuple[Vrm1ExpressionPropertyGroup, str, str]],
    ) -> None:
        if not material.use_nodes:
            material.use_nodes = True

        node_tree = material.node_tree
        if not isinstance(node_tree, bpy.types.ShaderNodeTree):
            return

        self.remove_existing_nodes(node_tree)

        # Create a new node group
        group_name = f"VRM_TextureTransform_{material.name}"
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=group_name)

        # Create input and output sockets for the node group
        node_group.interface.new_socket(
            name="UV", in_out="INPUT", socket_type="NodeSocketVector"
        )
        node_group.interface.new_socket(
            name="Vector", in_out="OUTPUT", socket_type="NodeSocketVector"
        )

        # Add nodes to the group
        group_input = node_group.nodes.new("NodeGroupInput")
        group_output = node_group.nodes.new("NodeGroupOutput")

        # Create a single UV Map node
        uv_map_node = node_group.nodes.new(type="ShaderNodeUVMap")
        uv_map_node.name = "VRM_TextureTransform_UVMap"

        mapping_nodes = self.setup_drivers(
            context, armature, node_group, material, all_expressions
        )

        # Create cascading vector math add nodes
        last_add_node = None
        for i, mapping_node in enumerate(mapping_nodes):
            add_node = node_group.nodes.new(type="ShaderNodeVectorMath")
            add_node.operation = "ADD"
            node_group.links.new(uv_map_node.outputs[0], mapping_node.inputs["Vector"])
            node_group.links.new(mapping_node.outputs[0], add_node.inputs[0])
            if last_add_node:
                node_group.links.new(last_add_node.outputs[0], add_node.inputs[1])
            elif i == 0:  # Only for the first add node, connect it to the group input
                node_group.links.new(group_input.outputs[0], add_node.inputs[1])
            last_add_node = add_node

        # Connect the last add node to the group output
        if last_add_node:
            node_group.links.new(last_add_node.outputs[0], group_output.inputs[0])
        else:
            node_group.links.new(group_input.outputs[0], group_output.inputs[0])

        # Add the group node to the material
        group_node = node_tree.nodes.new(type="ShaderNodeGroup")
        group_node.node_tree = node_group
        group_node.name = "VRM_TextureTransform_Group"

        # Connect the group node to texture nodes
        for node in node_tree.nodes:
            if node.type == "TEX_IMAGE":
                self.connect_group_to_image_node(node_tree, group_node, node)

    def setup_drivers(
        self,
        context: Context,
        armature: bpy.types.Object,
        node_group: bpy.types.ShaderNodeTree,
        material: Material,
        all_expressions: list[tuple[Vrm1ExpressionPropertyGroup, str, str]],
    ) -> list[bpy.types.ShaderNodeMapping]:
        base_path = "vrm_addon_extension.vrm1.expressions"
        mapping_nodes = []

        for i, axis in enumerate(["X", "Y"]):
            expressions_data = []
            for expression, expr_type, expr_name in all_expressions:
                for bind_index, bind in enumerate(expression.texture_transform_binds):
                    if bind.material == material:
                        offset_var_name = (
                            f"offset_{axis.lower()}_{expr_type}_{expr_name}"
                        )
                        scale_var_name = f"scale_{axis.lower()}_{expr_type}_{expr_name}"
                        preview_var_name = f"preview_{expr_type}_{expr_name}"
                        is_binary_var_name = f"is_binary_{expr_type}_{expr_name}"

                        if axis.lower() == "x":
                            location_term = f"({offset_var_name} * (1.0 if {is_binary_var_name} and {preview_var_name} >= 0.5 else (0.0 if {is_binary_var_name} else {preview_var_name})))"
                        else:
                            location_term = f"(-{offset_var_name} * (1.0 if {is_binary_var_name} and {preview_var_name} >= 0.5 else (0.0 if {is_binary_var_name} else {preview_var_name})))"
                        scale_term = f"(({scale_var_name} - 1) * (1.0 if {is_binary_var_name} and {preview_var_name} >= 0.5 else (0.0 if {is_binary_var_name} else {preview_var_name})))"

                        custom_index = (
                            f"[{expr_name}]"
                            if expr_type == "custom"
                            else f".{expr_name}"
                        )
                        variables = [
                            (
                                offset_var_name,
                                f"{base_path}.{expr_type}{custom_index}.texture_transform_binds[{bind_index}].offset[{i}]",
                            ),
                            (
                                scale_var_name,
                                f"{base_path}.{expr_type}{custom_index}.texture_transform_binds[{bind_index}].scale[{i}]",
                            ),
                            (
                                preview_var_name,
                                f"{base_path}.{expr_type}{custom_index}.preview",
                            ),
                            (
                                is_binary_var_name,
                                f"{base_path}.{expr_type}{custom_index}.is_binary",
                            ),
                        ]
                        expressions_data.append((location_term, scale_term, variables))

            current_mapping_node = None
            location_expression = ""
            scale_expression = ""
            current_variables = []

            for location_term, scale_term, variables in expressions_data:
                temp_location_expr = (
                    location_expression
                    + (" + " if location_expression else "")
                    + location_term
                )
                temp_scale_expr = (
                    scale_expression + (" + " if scale_expression else "") + scale_term
                )
                temp_variables = current_variables + variables

                if (
                    len(temp_location_expr) <= 255
                    and len(temp_scale_expr) <= 255
                    and len(temp_variables) <= 32
                ):
                    location_expression = temp_location_expr
                    scale_expression = temp_scale_expr
                    current_variables = temp_variables
                else:
                    if current_mapping_node:
                        self.finalize_mapping_node(
                            current_mapping_node,
                            i,
                            location_expression,
                            scale_expression,
                            current_variables,
                            armature,
                        )

                    current_mapping_node = node_group.nodes.new(
                        type="ShaderNodeMapping"
                    )
                    current_mapping_node.name = (
                        f"VRM_TextureTransform_Mapping_{len(mapping_nodes)}"
                    )
                    current_mapping_node.inputs["Scale"].default_value = (0, 0, 0)
                    mapping_nodes.append(current_mapping_node)

                    location_expression = location_term
                    scale_expression = scale_term
                    current_variables = variables

            if current_mapping_node:
                self.finalize_mapping_node(
                    current_mapping_node,
                    i,
                    location_expression,
                    scale_expression,
                    current_variables,
                    armature,
                )

        return mapping_nodes

    def finalize_mapping_node(
        self,
        mapping_node,
        axis_index,
        location_expression,
        scale_expression,
        variables,
        armature,
    ):
        location_driver = (
            mapping_node.inputs["Location"]
            .driver_add("default_value", axis_index)
            .driver
        )
        scale_driver = (
            mapping_node.inputs["Scale"].driver_add("default_value", axis_index).driver
        )

        for driver in [location_driver, scale_driver]:
            driver.type = "SCRIPTED"
            driver.use_self = True
            for var_name, data_path in variables:
                self.create_driver_variable(driver, var_name, armature, data_path)

        location_driver.expression = location_expression
        scale_driver.expression = scale_expression

    def create_driver_variable(self, driver, var_name, armature, data_path):
        var = driver.variables.new()
        var.name = var_name
        var.type = "SINGLE_PROP"
        var.targets[0].id_type = "ARMATURE"
        var.targets[0].id = armature.data
        var.targets[0].data_path = data_path
        var.targets[0].use_fallback_value = True
        return var

    def remove_existing_nodes(self, node_tree: bpy.types.ShaderNodeTree) -> None:
        nodes_to_remove = [
            node
            for node in node_tree.nodes
            if node.type
            in [
                "ShaderNodeUVMap",
                "ShaderNodeMapping",
                "ShaderNodeVectorMath",
                "ShaderNodeGroup",
            ]
            and node.name.startswith("VRM_TextureTransform_")
        ]
        for node in nodes_to_remove:
            node_tree.nodes.remove(node)

    def connect_group_to_image_node(
        self,
        node_tree: bpy.types.ShaderNodeTree,
        group_node: bpy.types.ShaderNodeGroup,
        image_node: bpy.types.ShaderNodeTexImage,
    ) -> None:
        vector_input = image_node.inputs["Vector"]
        existing_links = vector_input.links

        if not existing_links:
            node_tree.links.new(group_node.outputs[0], vector_input)
        else:
            vector_math_node = node_tree.nodes.new(type="ShaderNodeVectorMath")
            vector_math_node.name = f"VRM_TextureTransform_VectorMath_{image_node.name}"
            vector_math_node.operation = "ADD"

            node_tree.links.new(group_node.outputs[0], vector_math_node.inputs[0])
            node_tree.links.new(
                existing_links[0].from_socket, vector_math_node.inputs[1]
            )
            node_tree.links.remove(existing_links[0])
            node_tree.links.new(vector_math_node.outputs[0], vector_input)


def update_materials_handler(scene) -> None:
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        for material in space.shading.materials_to_update:
                            material.update_tag()
                        space.shading.materials_to_update.clear()
