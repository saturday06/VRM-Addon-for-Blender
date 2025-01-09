# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import re
from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet
from typing import TYPE_CHECKING, ClassVar, Optional, Protocol

import bpy
from bpy.props import IntProperty, StringProperty
from bpy.types import (
    ID,
    Armature,
    Context,
    FCurve,
    Material,
    Node,
    NodeSocket,
    NodeTree,
    Object,
    Operator,
    ShaderNodeGroup,
    ShaderNodeMapping,
    ShaderNodeTexImage,
    ShaderNodeTree,
    ShaderNodeValue,
    ShaderNodeVectorMath,
)

from ...common import ops, shader
from ...common.human_bone_mapper.human_bone_mapper import create_human_bone_mapping
from ...common.logger import get_logger
from ...common.vrm0.human_bone import HumanBoneName as Vrm0HumanBoneName
from ...common.vrm1.human_bone import HumanBoneName, HumanBoneSpecifications
from ..extension import get_armature_extension
from ..vrm0.property_group import Vrm0HumanoidPropertyGroup
from .property_group import (
    Vrm1ExpressionPropertyGroup,
    Vrm1HumanBonesPropertyGroup,
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
    bl_label = "Update VRM 1.0 Expression UI list Elements"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    def execute(self, context: Context) -> set[str]:
        for armature in context.blend_data.armatures:
            expressions = get_armature_extension(armature).vrm1.expressions

            # Set the number of elements equal to the number of elements wanted to show
            # in the UIlist.
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
        all_expressions = self.get_all_expressions()

        materials_to_update: set[Material] = set()
        expression = None
        for expression, _expr_type, _expr_name in all_expressions:
            for bind in expression.texture_transform_binds:
                if bind.material:
                    materials_to_update.add(bind.material)
        if not expression:
            return {"FINISHED"}

        for material in materials_to_update:
            self.setup_uv_offset_nodes(context, armature, material, all_expressions)
            new_item = expression.materials_to_update.add()
            new_item.material = material
            material.update_tag()

        return {"FINISHED"}

    def get_all_expressions(self) -> list[tuple[Vrm1ExpressionPropertyGroup, str, str]]:
        armature = bpy.data.objects.get(self.armature_name)
        if not armature or armature.type != "ARMATURE":
            return []

        extension = getattr(armature.data, "vrm_addon_extension", None)
        if (
            extension is not None
            and extension.vrm1 is not None
            and extension.vrm1.expressions is not None
        ):
            expressions = extension.vrm1.expressions
        else:
            return []

        all_expressions: list[tuple[Vrm1ExpressionPropertyGroup, str, str]] = []
        if expressions is not None:
            for preset_name in self.preset_name_mapping.values():
                preset_expr = getattr(expressions.preset, preset_name, None)
                if preset_expr:
                    all_expressions.append((preset_expr, "preset", preset_name))
            for i, custom_expr in enumerate(expressions.custom):
                all_expressions.append((custom_expr, "custom", str(i)))

        return all_expressions

    def setup_uv_offset_nodes(
        self,
        context: Context,
        armature: Object,
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
        _group_input = node_group.nodes.new("NodeGroupInput")
        group_output = node_group.nodes.new("NodeGroupOutput")

        # Create a single UV Map node
        uv_map_node = node_group.nodes.new(type="ShaderNodeUVMap")
        uv_map_node.name = "VRM_TextureTransform_UVMap"

        # Setup drivers and create mapping nodes
        mapping_nodes = self.setup_drivers(
            context, armature, node_group, material, all_expressions
        )

        # Link the UV Map node to all mapping nodes
        for mapping_node in mapping_nodes.values():
            node_group.links.new(uv_map_node.outputs[0], mapping_node.inputs[0])

        # Create blocking multiply chains
        multiply_chains = self.create_blocking_multiply_chains(
            node_group, all_expressions, armature, mapping_nodes
        )

        # Create the final add chain
        final_add_node = self.create_final_add_chain(
            node_group, mapping_nodes, multiply_chains, all_expressions
        )

        # Connect the final add node to the group output
        if final_add_node:
            node_group.links.new(final_add_node.outputs[0], group_output.inputs[0])

        # Add the group node to the material
        group_node = node_tree.nodes.new(type="ShaderNodeGroup")
        if not isinstance(group_node, ShaderNodeGroup):
            raise TypeError
        group_node.node_tree = node_group
        group_node.name = "VRM_TextureTransform_Group"

        # Connect the group node to texture nodes
        for node in node_tree.nodes:
            if node.type == "TEX_IMAGE":
                if not isinstance(node, ShaderNodeTexImage):
                    raise TypeError
                self.connect_group_to_image_node(node_tree, group_node, node)

    def setup_drivers(
        self,
        _context: Context,
        armature: Object,
        node_group: NodeTree,
        material: Material,
        all_expressions: Sequence[tuple[Vrm1ExpressionPropertyGroup, str, str]],
    ) -> Mapping[str, ShaderNodeMapping]:
        mapping_nodes = self.create_mapping_nodes(
            node_group, all_expressions, armature, material
        )
        return mapping_nodes

    def create_mapping_nodes(
        self,
        node_group: NodeTree,
        all_expressions: Sequence[tuple[Vrm1ExpressionPropertyGroup, str, str]],
        armature: Object,
        material: Material,
    ) -> Mapping[str, ShaderNodeMapping]:
        mapping_nodes: dict[str, ShaderNodeMapping] = {}
        for expression, expr_type, expr_name in all_expressions:
            for bind_index, bind in enumerate(expression.texture_transform_binds):
                if bind.material == material:
                    mapping_node = node_group.nodes.new(type="ShaderNodeMapping")
                    if not isinstance(mapping_node, ShaderNodeMapping):
                        raise TypeError
                    mapping_node.name = (
                        f"VRM_TextureTransform_Mapping_{expr_type}_{expr_name}"
                    )
                    scale_input_node = mapping_node.inputs["Scale"]
                    if not isinstance(scale_input_node, shader.VECTOR_SOCKET_CLASSES):
                        raise TypeError
                    scale_input_node.default_value = (1, 1, 1)
                    mapping_nodes[f"{expr_type}_{expr_name}"] = mapping_node

                    self.setup_mapping_node_drivers(
                        mapping_node,
                        expression,
                        expr_type,
                        expr_name,
                        bind_index,
                        armature,
                    )

        return mapping_nodes

    def setup_mapping_node_drivers(
        self,
        mapping_node: ShaderNodeMapping,
        _expression: Vrm1ExpressionPropertyGroup,
        expr_type: str,
        expr_name: str,
        bind_index: int,
        armature: Object,
    ) -> None:
        base_path = f"vrm_addon_extension.vrm1.expressions.{expr_type}"
        custom_index = f"[{expr_name}]" if expr_type == "custom" else f".{expr_name}"

        # Set all scale values to 0.0
        scale_input_socket = mapping_node.inputs["Scale"]
        if not isinstance(scale_input_socket, shader.VECTOR_SOCKET_CLASSES):
            raise TypeError
        scale_input_socket.default_value = (0.0, 0.0, 0.0)

        for i, axis in enumerate(["X", "Y"]):
            for input_name, property_name in [
                ("Location", "offset"),
                ("Scale", "scale"),
            ]:
                fcurve = mapping_node.inputs[input_name].driver_add("default_value", i)
                if not isinstance(fcurve, FCurve):
                    raise TypeError
                driver = fcurve.driver
                if not driver:
                    raise TypeError
                driver.type = "SCRIPTED"

                var = driver.variables.new()
                var.name = f"{property_name}_{axis.lower()}"
                var.type = "SINGLE_PROP"
                var.targets[0].id_type = "ARMATURE"
                armature_data = armature.data
                if not isinstance(armature_data, ID):
                    raise TypeError
                var.targets[0].id = armature_data
                data_path = (
                    f"{base_path}{custom_index}"
                    f".texture_transform_binds[{bind_index}].{property_name}[{i}]"
                )
                var.targets[0].data_path = data_path

                preview_var = driver.variables.new()
                preview_var.name = "preview"
                preview_var.type = "SINGLE_PROP"
                preview_var.targets[0].id_type = "ARMATURE"
                preview_var.targets[0].id = armature_data
                preview_var.targets[0].data_path = f"{base_path}{custom_index}.preview"

                is_binary_var = driver.variables.new()
                is_binary_var.name = "is_binary"
                is_binary_var.type = "SINGLE_PROP"
                is_binary_var.targets[0].id_type = "ARMATURE"
                is_binary_var.targets[0].id = armature_data
                is_binary_var.targets[
                    0
                ].data_path = f"{base_path}{custom_index}.is_binary"

                if input_name == "Location":
                    if axis == "X":  # Offset UV as expected
                        driver.expression = (
                            f"{property_name}_{axis.lower()} * (1.0 if is_binary and "
                            " preview >= 0.5 else (0.0 if is_binary else preview))"
                        )
                    else:
                        # Offset UV in the opposite direction
                        # (this is a quirk of VRM standard)
                        driver.expression = (
                            f"(-{property_name}_{axis.lower()} "
                            "  + ( "
                            "      0 if scale_y == 1 "
                            "      else (1 - scale_y) "
                            "    ) "
                            " ) "
                            " * (1.0 if is_binary and preview >= 0.5 "
                            "    else (0.0 if is_binary else preview) "
                            " ) "
                            " - (0 if scale_y == 1 else 1)"
                        )
                elif axis == "X":
                    driver.expression = (
                        f"({property_name}_{axis.lower()} - 1) * "
                        "  ( "
                        "    1.0 if is_binary and preview >= 0.5 "
                        "    else (0.0 if is_binary else preview) "
                        "  )"
                    )
                else:
                    driver.expression = (
                        f"-(2 - {property_name}_{axis.lower()} - 1) "
                        " * (1.0 if is_binary and preview >= 0.5 "
                        "    else (0.0 if is_binary else preview) "
                        "   )"
                    )

                # Add scale_y variable for Y offset calculation
                if input_name == "Location" and axis == "Y":
                    scale_y_var = driver.variables.new()
                    scale_y_var.name = "scale_y"
                    scale_y_var.type = "SINGLE_PROP"
                    scale_y_var.targets[0].id_type = "ARMATURE"
                    scale_y_var.targets[0].id = armature_data
                    data_path = (
                        f"{base_path}{custom_index}"
                        f".texture_transform_binds[{bind_index}].scale[1]"
                    )
                    scale_y_var.targets[0].data_path = data_path

    def create_blocking_multiply_chains(
        self,
        node_group: NodeTree,
        all_expressions: Sequence[tuple[Vrm1ExpressionPropertyGroup, str, str]],
        armature: Object,
        mapping_nodes: Mapping[str, ShaderNodeMapping],
    ) -> Mapping[str, Optional[ShaderNodeVectorMath]]:
        multiply_chains: dict[str, Optional[ShaderNodeVectorMath]] = {}
        blockable_types = ["blink", "look", "mouth"]

        for blockable_type in blockable_types:
            chain = self.create_blocking_multiply_chain(
                node_group, blockable_type, all_expressions, armature, mapping_nodes
            )
            multiply_chains[blockable_type] = chain

        return multiply_chains

    def create_blocking_multiply_chain(
        self,
        node_group: NodeTree,
        blockable_type: str,
        all_expressions: Sequence[tuple[Vrm1ExpressionPropertyGroup, str, str]],
        armature: Object,
        mapping_nodes: Mapping[str, ShaderNodeMapping],
    ) -> Optional[ShaderNodeVectorMath]:
        blockable_expressions = self.get_blockable_expressions(blockable_type)

        # Add blockable expressions together
        blockable_add_node = self.add_blockable_expressions(
            node_group, blockable_expressions, mapping_nodes
        )

        # Create blocking value nodes
        value_nodes = self.create_blocking_value_nodes(
            node_group, blockable_type, all_expressions, armature
        )

        # Create and link multiply nodes
        last_multiply = None
        for i, value_node in enumerate(value_nodes):
            multiply_node = node_group.nodes.new(type="ShaderNodeVectorMath")
            if not isinstance(multiply_node, ShaderNodeVectorMath):
                raise TypeError
            multiply_node.operation = "MULTIPLY"
            multiply_node.name = (
                f"VRM_TextureTransform_BlockingMultiply_{blockable_type}_{i}"
            )

            if last_multiply:
                node_group.links.new(last_multiply.outputs[0], multiply_node.inputs[0])
            elif blockable_add_node:
                # Connect the blockable add node to the first multiply node
                node_group.links.new(
                    blockable_add_node.outputs[0], multiply_node.inputs[0]
                )

            node_group.links.new(value_node.outputs[0], multiply_node.inputs[1])
            last_multiply = multiply_node

        return (
            last_multiply or blockable_add_node
        )  # Return blockable_add_node if no multiply nodes were created

    def add_blockable_expressions(
        self,
        node_group: NodeTree,
        blockable_expressions: Sequence[str],
        mapping_nodes: Mapping[str, ShaderNodeMapping],
    ) -> Optional[ShaderNodeVectorMath]:
        add_node = None
        for _i, expr_name in enumerate(blockable_expressions):
            mapping_node = mapping_nodes.get(f"preset_{expr_name}")
            if mapping_node:
                if add_node is None:
                    node = node_group.nodes.new(type="ShaderNodeVectorMath")
                    if not isinstance(node, ShaderNodeVectorMath):
                        raise TypeError
                    add_node = node
                    add_node.operation = "ADD"
                    add_node.name = f"VRM_TextureTransform_BlockableAdd_{expr_name}"
                    node_group.links.new(mapping_node.outputs[0], add_node.inputs[0])
                else:
                    new_add_node = node_group.nodes.new(type="ShaderNodeVectorMath")
                    if not isinstance(new_add_node, ShaderNodeVectorMath):
                        raise TypeError
                    new_add_node.operation = "ADD"
                    new_add_node.name = f"VRM_TextureTransform_BlockableAdd_{expr_name}"
                    node_group.links.new(add_node.outputs[0], new_add_node.inputs[0])
                    node_group.links.new(
                        mapping_node.outputs[0], new_add_node.inputs[1]
                    )
                    add_node = new_add_node

        return add_node

    def create_blocking_value_nodes(
        self,
        node_group: NodeTree,
        blockable_type: str,
        all_expressions: Sequence[tuple[object, str, str]],
        armature: Object,
    ) -> Sequence[ShaderNodeValue]:
        value_nodes: list[ShaderNodeValue] = []
        for _expr, expr_type, expr_name in all_expressions:
            if (
                expr_type == "preset"
                and expr_name not in self.get_blockable_expressions(blockable_type)
            ):
                armature_data = armature.data
                if not isinstance(armature_data, Armature):
                    raise TypeError
                override_blockable_type = getattr(
                    getattr(
                        get_armature_extension(armature_data).vrm1.expressions.preset,
                        expr_name,
                        None,
                    ),
                    "override_{blockable_type}",
                    None,
                )
                include_expression = override_blockable_type != "none"
                if include_expression:
                    value_node = node_group.nodes.new(type="ShaderNodeValue")
                    if not isinstance(value_node, ShaderNodeValue):
                        raise TypeError
                    value_node.name = (
                        "VRM_TextureTransform_BlockingValue_"
                        f"{blockable_type}_{expr_name}"
                    )
                    value_nodes.append(value_node)

                    fcurve = value_node.outputs[0].driver_add("default_value")
                    if not isinstance(fcurve, FCurve):
                        raise TypeError
                    driver = fcurve.driver
                    if not driver:
                        raise TypeError
                    driver.type = "SCRIPTED"
                    preview_var = driver.variables.new()
                    preview_var.name = "preview"
                    preview_var.type = "SINGLE_PROP"
                    preview_var.targets[0].id_type = "ARMATURE"
                    armature_data = armature.data
                    if not isinstance(armature_data, ID):
                        raise TypeError
                    preview_var.targets[0].id = armature_data
                    data_path = (
                        "vrm_addon_extension.vrm1.expressions.preset"
                        f".{expr_name}.preview"
                    )
                    preview_var.targets[0].data_path = data_path
                    driver.expression = "0 if preview >= 0.5 else 1"

        return value_nodes

    def create_add_node(
        self,
        node_group: NodeTree,
        input_node: Node,
        previous_add_node: Optional[ShaderNodeVectorMath],
    ) -> ShaderNodeVectorMath:
        add_node = node_group.nodes.new(type="ShaderNodeVectorMath")
        if not isinstance(add_node, ShaderNodeVectorMath):
            raise TypeError
        add_node.operation = "ADD"
        add_node.name = f"VRM_TextureTransform_Add_{input_node.name}"

        node_group.links.new(input_node.outputs[0], add_node.inputs[0])
        if previous_add_node:
            node_group.links.new(previous_add_node.outputs[0], add_node.inputs[1])

        return add_node

    def create_final_add_chain(
        self,
        node_group: NodeTree,
        mapping_nodes: Mapping[str, Node],
        multiply_chains: Mapping[str, Optional[ShaderNodeVectorMath]],
        all_expressions: Sequence[tuple[object, str, str]],
    ) -> Optional[ShaderNodeVectorMath]:
        add_nodes: list[ShaderNodeVectorMath] = []
        last_add = None

        # Add non-blockable mapping nodes
        for _expr, expr_type, expr_name in all_expressions:
            if not self.is_blockable_expression(expr_name):
                mapping_node = mapping_nodes.get(f"{expr_type}_{expr_name}")
                if mapping_node:
                    add_node = self.create_add_node(node_group, mapping_node, last_add)
                    last_add = add_node
                    add_nodes.append(add_node)

        # Add results from multiply chains
        for last_multiply in multiply_chains.values():
            if last_multiply:
                add_node = self.create_add_node(node_group, last_multiply, last_add)
                last_add = add_node
                add_nodes.append(add_node)

        return last_add

    def is_blockable_expression(self, expr_name: str) -> bool:
        blockable_types = ["blink", "look", "mouth"]
        return any(
            expr_name in self.get_blockable_expressions(bt) for bt in blockable_types
        )

    def get_property_value(self, armature: Object, data_path: str) -> object:
        prop: object = armature
        for prop_name in data_path.split("."):
            if not re.match(prop_name, "^[a-zA-Z_][a-zA-Z0-9_]*$"):
                message = f'Invalid prop name: "{prop_name}"'
                raise AssertionError(message)
            prop = getattr(prop, prop_name)
        return prop

    def get_blockable_expressions(self, blockable_type: str) -> Sequence[str]:
        if blockable_type == "blink":
            return ["blink", "blink_left", "blink_right"]
        if blockable_type == "look":
            return ["look_up", "look_down", "look_left", "look_right"]
        if blockable_type == "mouth":
            return ["aa", "ih", "ee", "oh", "ou"]
        return []

    def remove_existing_nodes(self, node_tree: ShaderNodeTree) -> None:
        nodes_to_remove: list[Node] = []
        links_to_restore: list[tuple[NodeSocket, NodeSocket]] = []

        for node in node_tree.nodes:
            if node.name.startswith("VRM_TextureTransform_"):
                nodes_to_remove.append(node)
                # Store information about links to restore
                for output in node.outputs:
                    for link in output.links:
                        if not link.to_node.name.startswith("VRM_TextureTransform_"):
                            # Find the first input that doesn't start
                            # with VRM_TextureTransform_
                            for input_socket in node.inputs:
                                if input_socket.is_linked and not input_socket.links[
                                    0
                                ].from_node.name.startswith("VRM_TextureTransform_"):
                                    links_to_restore.append(
                                        (
                                            input_socket.links[0].from_socket,
                                            link.to_socket,
                                        )
                                    )
                                    break
            elif (
                node.type == "GROUP"
                and isinstance(node, ShaderNodeGroup)
                and node.node_tree
                and node.node_tree.name.startswith("VRM_TextureTransform_")
            ):
                nodes_to_remove.append(node)
                # Handle links for group nodes
                for output in node.outputs:
                    links_to_restore.extend(
                        (node.inputs[0].links[0].from_socket, link.to_socket)
                        for link in output.links
                        if not link.to_node.name.startswith("VRM_TextureTransform_")
                    )

        # Remove nodes
        for node in nodes_to_remove:
            node_tree.nodes.remove(node)

        # Restore links
        for from_socket, to_socket in links_to_restore:
            node_tree.links.new(from_socket, to_socket)

        # Remove orphaned node groups
        for group in bpy.data.node_groups:
            if group.name.startswith("VRM_TextureTransform_") and group.users == 0:
                bpy.data.node_groups.remove(group)

    def connect_group_to_image_node(
        self,
        node_tree: ShaderNodeTree,
        group_node: ShaderNodeGroup,
        image_node: ShaderNodeTexImage,
    ) -> None:
        vector_input = image_node.inputs["Vector"]
        existing_links = vector_input.links

        if not existing_links:
            node_tree.links.new(group_node.outputs[0], vector_input)
        else:
            vector_math_node = node_tree.nodes.new(type="ShaderNodeVectorMath")
            if not isinstance(vector_math_node, ShaderNodeVectorMath):
                raise TypeError
            vector_math_node.name = f"VRM_TextureTransform_VectorMath_{image_node.name}"
            vector_math_node.operation = "ADD"

            node_tree.links.new(group_node.outputs[0], vector_math_node.inputs[0])
            node_tree.links.new(
                existing_links[0].from_socket, vector_math_node.inputs[1]
            )
            node_tree.links.remove(existing_links[0])
            node_tree.links.new(vector_math_node.outputs[0], vector_input)

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
