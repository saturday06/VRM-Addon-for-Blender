import bpy
import bmesh
from collections.abc import Set as AbstractSet
from typing import TYPE_CHECKING, List, Tuple, Dict, Any, ClassVar

from bpy.props import IntProperty, StringProperty, BoolProperty
from bpy.types import Armature, Context, Operator

from ...common import ops
from ...common.human_bone_mapper.human_bone_mapper import create_human_bone_mapping
from ...common.logging import get_logger
from ...common.vrm0.human_bone import HumanBoneName as Vrm0HumanBoneName
from ...common.vrm1.human_bone import HumanBoneName, HumanBoneSpecifications
from ..extension import get_armature_extension
from ..vrm0.property_group import Vrm0HumanoidPropertyGroup
from .property_group import Vrm1HumanBonesPropertyGroup

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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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
        # `uv run tools/property_typing.py`
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

class VRM_OT_vrm1_texture_transform_preview(Operator):
    bl_idname = "vrm.texture_transform_preview"
    bl_label = "Preview Texture Transform"
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(options={"HIDDEN"})
    expression_name: StringProperty(options={"HIDDEN"})
    update_only: BoolProperty(default=False, options={"HIDDEN"})

    _timer: Any = None
    _temp_uv_maps: ClassVar[Dict[str, Dict[str, str]]] = {}
    _original_uv_positions: ClassVar[Dict[str, Dict[str, Dict[int, Any]]]] = {}
    _original_active_uv: ClassVar[Dict[str, str]] = {}
    is_modal_running: ClassVar[bool] = False
    is_paused: ClassVar[bool] = False

    preset_name_mapping: ClassVar[Dict[str, str]] = {
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
        "blinkLeft": "blink_left",
        "blinkRight": "blink_right",
        "lookUp": "look_up",
        "lookDown": "look_down",
        "lookLeft": "look_left",
        "lookRight": "look_right",
    }

    def modal(self, context: Context, event: Any) -> set[str]:
        if event.type == "ESC" or context.mode == "EDIT_MESH":
            self.cancel(context)
            return {"CANCELLED"}

        if event.type == "TIMER" and not self.is_paused:
            self.update_all_uv_maps(context)

        return {"PASS_THROUGH"}

    def execute(self, context: Context) -> set[str]:
        if self.update_only:
            if VRM_OT_vrm1_texture_transform_preview.is_modal_running:
                VRM_OT_vrm1_texture_transform_preview.is_paused = not VRM_OT_vrm1_texture_transform_preview.is_paused
                if VRM_OT_vrm1_texture_transform_preview.is_paused:
                    self.remove_temp_uv_maps()
                    self.reset_active_render_uv()
                else:
                    self.create_all_temp_uv_maps(context)
            else:
                self.update_all_uv_maps(context)
            return {"FINISHED"}

        if not VRM_OT_vrm1_texture_transform_preview.is_modal_running:
            self.create_all_temp_uv_maps(context)
            wm = context.window_manager
            self._timer = wm.event_timer_add(0.1, window=context.window)
            wm.modal_handler_add(self)
            VRM_OT_vrm1_texture_transform_preview.is_modal_running = True
            VRM_OT_vrm1_texture_transform_preview.is_paused = False
            return {"RUNNING_MODAL"}
        else:
            self.cancel(context)
            return {"FINISHED"}

    def cancel(self, context: Context) -> None:
        self.remove_temp_uv_maps()
        self.reset_active_render_uv()
        if self._timer is not None:
            wm = context.window_manager
            wm.event_timer_remove(self._timer)
        VRM_OT_vrm1_texture_transform_preview.is_modal_running = False
        VRM_OT_vrm1_texture_transform_preview.is_paused = False
        self._original_uv_positions.clear()
        self._original_active_uv.clear()

    def get_all_expressions(self, context: Context) -> List[Tuple[Any, str, str]]:
        armature = bpy.data.objects.get(self.armature_name)
        if not armature or armature.type != "ARMATURE":
            return []

        extension = armature.data.vrm_addon_extension
        expressions = extension.vrm1.expressions

        all_expressions = []
        for preset_name in self.preset_name_mapping.values():
            preset_expr = getattr(expressions.preset, preset_name, None)
            if preset_expr:
                all_expressions.append((preset_expr, 'preset', preset_name))
        for i, custom_expr in enumerate(expressions.custom):
            all_expressions.append((custom_expr, 'custom', str(i)))

        return all_expressions

    def create_all_temp_uv_maps(self, context: Context) -> None:
        armature = bpy.data.objects.get(self.armature_name)
        if not armature or armature.type != "ARMATURE":
            return

        for expression, _, _ in self.get_all_expressions(context):
            binds = expression.texture_transform_binds
            for bind in binds:
                if bind.material:
                    self.create_temp_uv_maps(bind)

    def create_temp_uv_maps(self, bind: Any) -> None:
        material = bind.material
        if not material:
            return

        for obj in bpy.data.objects:
            if obj.type == 'MESH' and material.name in obj.data.materials:
                mesh = obj.data
                temp_uv_name = f"temp_vrm_preview_{obj.name}_{material.name}"
                if temp_uv_name not in mesh.uv_layers:
                    temp_uv = mesh.uv_layers.new(name=temp_uv_name)
                    self._temp_uv_maps.setdefault(obj.name, {})[material.name] = temp_uv_name
                    self._original_active_uv[obj.name] = mesh.uv_layers.active.name
                    mesh.uv_layers.active = temp_uv
                    
                    for uv_layer in mesh.uv_layers:
                        uv_layer.active_render = (uv_layer == temp_uv)

                    bm = bmesh.new()
                    bm.from_mesh(mesh)
                    bm.faces.ensure_lookup_table()

                    uv_layer = bm.loops.layers.uv.verify()
                    temp_uv_layer = bm.loops.layers.uv[temp_uv_name]

                    self._original_uv_positions.setdefault(obj.name, {}).setdefault(material.name, {})

                    for face in bm.faces:
                        if face.material_index < len(obj.data.materials) and obj.data.materials[face.material_index] == material:
                            for loop in face.loops:
                                original_uv = loop[uv_layer].uv
                                loop_index = loop.index
                                self._original_uv_positions[obj.name][material.name][loop_index] = original_uv.copy()
                                loop[temp_uv_layer].uv = original_uv.copy()

                    bm.to_mesh(mesh)
                    bm.free()

    def update_all_uv_maps(self, context: Context) -> None:
        armature = bpy.data.objects.get(self.armature_name)
        if not armature or armature.type != "ARMATURE":
            return

        all_binds = []
        for expression, _, _ in self.get_all_expressions(context):
            preview_value = expression.preview
            is_binary = getattr(expression, 'is_binary', False)
            for bind in expression.texture_transform_binds:
                if bind.material:
                    all_binds.append((bind, preview_value, is_binary))

        self.update_uv_maps(all_binds)

    def update_uv_maps(self, all_binds: List[Tuple[Any, float, bool]]) -> None:
        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue

            mesh = obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            bm.faces.ensure_lookup_table()

            # Group binds by material
            material_binds = {}
            for bind, preview_value, is_binary in all_binds:
                if bind.material:
                    material_binds.setdefault(bind.material.name, []).append((bind, preview_value, is_binary))

            for material_name, binds in material_binds.items():
                if material_name not in obj.data.materials:
                    continue

                temp_uv_name = self._temp_uv_maps.get(obj.name, {}).get(material_name)
                if not temp_uv_name:
                    continue

                temp_uv_layer = bm.loops.layers.uv.get(temp_uv_name)
                if not temp_uv_layer:
                    continue

                for face in bm.faces:
                    if face.material_index < len(obj.data.materials) and obj.data.materials[face.material_index].name == material_name:
                        for loop in face.loops:
                            original_uv = self._original_uv_positions.get(obj.name, {}).get(material_name, {}).get(loop.index)
                            if not original_uv:
                                continue

                            # Start with the original UV coordinates
                            new_uv = original_uv.copy()

                            # Apply all binds for this material
                            for bind, preview_value, is_binary in binds:
                                actual_preview_value = 1.0 if is_binary and preview_value >= 0.5 else (0.0 if is_binary else preview_value)
                                new_uv.x += (original_uv.x * (bind.scale[0] - 1) + bind.offset[0]) * actual_preview_value
                                new_uv.y += (original_uv.y * (bind.scale[1] - 1) + bind.offset[1]) * actual_preview_value

                            # Set the new UV coordinates
                            loop[temp_uv_layer].uv = new_uv

            bm.to_mesh(mesh)
            bm.free()
            mesh.update()

    def remove_temp_uv_maps(self) -> None:
        for obj_name, material_dict in self._temp_uv_maps.items():
            obj = bpy.data.objects.get(obj_name)
            if obj and obj.type == 'MESH':
                mesh = obj.data
                for temp_uv_name in material_dict.values():
                    temp_uv = mesh.uv_layers.get(temp_uv_name)
                    if temp_uv:
                        mesh.uv_layers.remove(temp_uv)
        self._temp_uv_maps.clear()

    def reset_active_render_uv(self) -> None:
        for obj_name, original_uv_name in self._original_active_uv.items():
            obj = bpy.data.objects.get(obj_name)
            if obj and obj.type == 'MESH':
                mesh = obj.data
                original_uv = mesh.uv_layers.get(original_uv_name)
                if original_uv:
                    mesh.uv_layers.active = original_uv
                    for uv_layer in mesh.uv_layers:
                        uv_layer.active_render = (uv_layer == original_uv)

    @classmethod
    def poll(cls, context: Context) -> bool:
        return context.mode == "OBJECT"