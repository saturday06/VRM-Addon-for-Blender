from typing import TYPE_CHECKING

import bpy

from ...common.human_bone_mapper.human_bone_mapper import create_human_bone_mapping
from ...common.logging import get_logger
from ...common.vrm0.human_bone import HumanBoneName as Vrm0HumanBoneName
from ...common.vrm1.human_bone import HumanBoneName, HumanBoneSpecifications
from ..vrm0.property_group import Vrm0HumanoidPropertyGroup
from .property_group import Vrm1HumanBonesPropertyGroup

logger = get_logger(__name__)


class VRM_OT_add_vrm1_meta_author(bpy.types.Operator):
    bl_idname = "vrm.add_vrm1_meta_author"
    bl_label = "Add Author"
    bl_description = "Add VRM 1.0 Meta Author"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        armature_data.vrm_addon_extension.vrm1.meta.authors.add()
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]


class VRM_OT_remove_vrm1_meta_author(bpy.types.Operator):
    bl_idname = "vrm.remove_vrm1_meta_author"
    bl_label = "Remove Author"
    bl_description = "Remove VRM 1.0 Meta Author"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    author_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        authors = armature_data.vrm_addon_extension.vrm1.meta.authors
        if len(authors) <= self.author_index:
            return {"CANCELLED"}
        authors.remove(self.author_index)
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        author_index: int  # type: ignore[no-redef]


class VRM_OT_add_vrm1_meta_reference(bpy.types.Operator):
    bl_idname = "vrm.add_vrm1_meta_reference"
    bl_label = "Add Reference"
    bl_description = "Add VRM 1.0 Meta Reference"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        armature_data.vrm_addon_extension.vrm1.meta.references.add()
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]


class VRM_OT_remove_vrm1_meta_reference(bpy.types.Operator):
    bl_idname = "vrm.remove_vrm1_meta_reference"
    bl_label = "Remove Reference"
    bl_description = "Remove VRM 1.0 Meta Reference"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    reference_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        references = armature_data.vrm_addon_extension.vrm1.meta.references
        if len(references) <= self.reference_index:
            return {"CANCELLED"}
        references.remove(self.reference_index)
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        reference_index: int  # type: ignore[no-redef]


class VRM_OT_add_vrm1_expressions_custom_expression(bpy.types.Operator):
    bl_idname = "vrm.add_vrm1_expressions_custom_expression"
    bl_label = "Add Custom Expression"
    bl_description = "Add VRM 1.0 Custom Expression"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    custom_expression_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        expressions = armature_data.vrm_addon_extension.vrm1.expressions
        new_last_custom_index = len(expressions.custom)
        new_active_custom_index = min(
            max(
                0,
                expressions.active_expression_ui_list_element_index
                - len(expressions.preset.name_to_expression_dict())
                + 1,
            ),
            new_last_custom_index,
        )
        custom_expression = expressions.custom.add()
        custom_expression.custom_name = self.custom_expression_name
        expressions.active_expression_ui_list_element_index = (
            len(expressions.preset.name_to_expression_dict()) + new_active_custom_index
        )
        if new_last_custom_index != new_active_custom_index:
            expressions.custom.move(new_last_custom_index, new_active_custom_index)
        return bpy.ops.vrm.update_vrm1_expression_ui_list_elements()

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        custom_expression_name: str  # type: ignore[no-redef]


class VRM_OT_remove_vrm1_expressions_custom_expression(bpy.types.Operator):
    bl_idname = "vrm.remove_vrm1_expressions_custom_expression"
    bl_label = "Remove Custom Expression"
    bl_description = "Remove VRM 1.0 Custom Expression"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    custom_expression_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        expressions = armature_data.vrm_addon_extension.vrm1.expressions
        for custom_index, custom_expression in enumerate(
            list(expressions.custom.values())
        ):
            if custom_expression.custom_name == self.custom_expression_name:
                expressions.custom.remove(custom_index)
                expressions.active_expression_ui_list_element_index = min(
                    expressions.active_expression_ui_list_element_index,
                    len(expressions.all_name_to_expression_dict()) - 1,
                )
                return bpy.ops.vrm.update_vrm1_expression_ui_list_elements()
        return {"CANCELLED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        custom_expression_name: str  # type: ignore[no-redef]


class VRM_OT_move_up_vrm1_expressions_custom_expression(bpy.types.Operator):
    bl_idname = "vrm.move_up_vrm1_expressions_custom_expression"
    bl_label = "Move Up Custom Expression"
    bl_description = "Move Up VRM 1.0 Custom Expression"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    custom_expression_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        expressions = armature_data.vrm_addon_extension.vrm1.expressions
        expression_index = {
            0: i
            for i, expression in enumerate(expressions.custom)
            if expression.custom_name == self.custom_expression_name
        }.get(0)
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
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        custom_expression_name: str  # type: ignore[no-redef]


class VRM_OT_move_down_vrm1_expressions_custom_expression(bpy.types.Operator):
    bl_idname = "vrm.move_down_vrm1_expressions_custom_expression"
    bl_label = "Move Down Custom Expression"
    bl_description = "Move Down VRM 1.0 Custom Expression"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    custom_expression_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        expressions = armature_data.vrm_addon_extension.vrm1.expressions
        expression_index = {
            0: i
            for i, expression in enumerate(expressions.custom)
            if expression.custom_name == self.custom_expression_name
        }.get(0)
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
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        custom_expression_name: str  # type: ignore[no-redef]


class VRM_OT_add_vrm1_first_person_mesh_annotation(bpy.types.Operator):
    bl_idname = "vrm.add_vrm1_first_person_mesh_annotation"
    bl_label = "Add Mesh Annotation"
    bl_description = "Add VRM 1.0 First Person Mesh Annotation"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        armature_data.vrm_addon_extension.vrm1.first_person.mesh_annotations.add()
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]


class VRM_OT_remove_vrm1_first_person_mesh_annotation(bpy.types.Operator):
    bl_idname = "vrm.remove_vrm1_first_person_mesh_annotation"
    bl_label = "Remove Mesh Annotation"
    bl_description = "Remove VRM 1.0 First Person Mesh Annotation"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    mesh_annotation_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        mesh_annotations = (
            armature_data.vrm_addon_extension.vrm1.first_person.mesh_annotations
        )
        if len(mesh_annotations) <= self.mesh_annotation_index:
            return {"CANCELLED"}
        mesh_annotations.remove(self.mesh_annotation_index)
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        mesh_annotation_index: int  # type: ignore[no-redef]


class VRM_OT_add_vrm1_expression_morph_target_bind(bpy.types.Operator):
    bl_idname = "vrm.add_vrm1_expression_morph_target_bind"
    bl_label = "Add Morph Target Bind"
    bl_description = "Add VRM 1.0 Expression Morph Target Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    expression_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        expressions = armature_data.vrm_addon_extension.vrm1.expressions
        expression = expressions.all_name_to_expression_dict().get(self.expression_name)
        if expression is None:
            return {"CANCELLED"}
        expression.morph_target_binds.add()
        expression.active_morph_target_bind_index = min(
            max(0, expression.active_morph_target_bind_index + 1),
            len(expression.morph_target_binds) - 1,
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]


class VRM_OT_remove_vrm1_expression_morph_target_bind(bpy.types.Operator):
    bl_idname = "vrm.remove_vrm1_expression_morph_target_bind"
    bl_label = "Remove Morph Target Bind"
    bl_description = "Remove VRM 1.0 Expression Morph Target Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    expression_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    bind_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        expressions = armature_data.vrm_addon_extension.vrm1.expressions
        expression = expressions.all_name_to_expression_dict().get(self.expression_name)
        if expression is None:
            return {"CANCELLED"}
        if len(expression.morph_target_binds) <= self.bind_index:
            return {"CANCELLED"}
        expression.morph_target_binds.remove(self.bind_index)
        expression.active_morph_target_bind_index = min(
            expression.active_morph_target_bind_index,
            len(expression.morph_target_binds) - 1,
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_vrm1_expression_morph_target_bind(bpy.types.Operator):
    bl_idname = "vrm.move_up_vrm1_expression_morph_target_bind"
    bl_label = "Move Up Morph Target Bind"
    bl_description = "Move Up VRM 1.0 Expression Morph Target Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    expression_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    bind_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        expressions = armature_data.vrm_addon_extension.vrm1.expressions
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
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_vrm1_expression_morph_target_bind(bpy.types.Operator):
    bl_idname = "vrm.move_down_vrm1_expression_morph_target_bind"
    bl_label = "Move Down Morph Target Bind"
    bl_description = "Move Down VRM 1.0 Expression Morph Target Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    expression_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    bind_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        expressions = armature_data.vrm_addon_extension.vrm1.expressions
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
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_add_vrm1_expression_material_color_bind(bpy.types.Operator):
    bl_idname = "vrm.add_vrm1_expression_material_color_bind"
    bl_label = "Add Material Color Bind"
    bl_description = "Add VRM 1.0 Expression Material Value Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    expression_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        expression = armature_data.vrm_addon_extension.vrm1.expressions.all_name_to_expression_dict().get(
            self.expression_name
        )
        if expression is None:
            return {"CANCELLED"}
        new_active_index = len(expression.material_color_binds)
        expression.material_color_binds.add()
        expression.active_material_color_bind_index = new_active_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]


class VRM_OT_remove_vrm1_expression_material_color_bind(bpy.types.Operator):
    bl_idname = "vrm.remove_vrm1_expression_material_color_bind"
    bl_label = "Remove Material Color Bind"
    bl_description = "Remove VRM 1.0 Expression Material Color Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    expression_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    bind_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        expressions = armature_data.vrm_addon_extension.vrm1.expressions
        expression = expressions.all_name_to_expression_dict().get(self.expression_name)
        if expression is None:
            return {"CANCELLED"}
        if len(expression.material_color_binds) <= self.bind_index:
            return {"CANCELLED"}
        expression.material_color_binds.remove(self.bind_index)
        expression.active_material_color_bind_index = max(
            0, len(expression.material_color_binds) - 1
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_vrm1_expression_material_color_bind(bpy.types.Operator):
    bl_idname = "vrm.move_up_vrm1_expression_material_color_bind"
    bl_label = "Move Up Material Color Bind"
    bl_description = "Move Up VRM 1.0 Expression Material Color Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    expression_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    bind_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        expressions = armature_data.vrm_addon_extension.vrm1.expressions
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
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_vrm1_expression_material_color_bind(bpy.types.Operator):
    bl_idname = "vrm.move_down_vrm1_expression_material_color_bind"
    bl_label = "Move Down Material Color Bind"
    bl_description = "Move Down VRM 1.0 Expression Material Color Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    expression_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    bind_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        expressions = armature_data.vrm_addon_extension.vrm1.expressions
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
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_add_vrm1_expression_texture_transform_bind(bpy.types.Operator):
    bl_idname = "vrm.add_vrm1_expression_texture_transform_bind"
    bl_label = "Add Texture Transform Bind"
    bl_description = "Add VRM 1.0 Expression Texture Transform Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    expression_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        expressions = armature_data.vrm_addon_extension.vrm1.expressions
        expression = expressions.all_name_to_expression_dict().get(self.expression_name)
        if expression is None:
            return {"CANCELLED"}
        active_index = len(expression.texture_transform_binds)
        expression.texture_transform_binds.add()
        expression.active_texture_transform_bind_index = active_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]


class VRM_OT_remove_vrm1_expression_texture_transform_bind(bpy.types.Operator):
    bl_idname = "vrm.remove_vrm1_expression_texture_transform_bind"
    bl_label = "Remove Texture Transform Bind"
    bl_description = "Remove VRM 1.0 Expression Texture Transform Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    expression_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    bind_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        expressions = armature_data.vrm_addon_extension.vrm1.expressions
        expression = expressions.all_name_to_expression_dict().get(self.expression_name)
        if expression is None:
            return {"CANCELLED"}
        if len(expression.texture_transform_binds) <= self.bind_index:
            return {"CANCELLED"}
        expression.texture_transform_binds.remove(self.bind_index)
        expression.active_texture_transform_bind_index = max(
            0, len(expression.texture_transform_binds) - 1
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_vrm1_expression_texture_transform_bind(bpy.types.Operator):
    bl_idname = "vrm.move_up_vrm1_expression_texture_transform_bind"
    bl_label = "Move Up Texture Transform Bind"
    bl_description = "Move Up VRM 1.0 Expression Texture Transform Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    expression_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    bind_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        expressions = armature_data.vrm_addon_extension.vrm1.expressions
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
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_vrm1_expression_texture_transform_bind(bpy.types.Operator):
    bl_idname = "vrm.move_down_vrm1_expression_texture_transform_bind"
    bl_label = "Move Down Morph Target Bind"
    bl_description = "Move Down VRM 1.0 Expression Morph Target Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    expression_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    bind_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        expressions = armature_data.vrm_addon_extension.vrm1.expressions
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
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        expression_name: str  # type: ignore[no-redef]
        bind_index: int  # type: ignore[no-redef]


vrm0_human_bone_name_to_vrm1_human_bone_name: dict[Vrm0HumanBoneName, HumanBoneName] = {
    specification.vrm0_name: specification.name
    for specification in HumanBoneSpecifications.all_human_bones
}


class VRM_OT_assign_vrm1_humanoid_human_bones_automatically(bpy.types.Operator):
    bl_idname = "vrm.assign_vrm1_humanoid_human_bones_automatically"
    bl_label = "Automatic Bone Assignment"
    bl_description = "Assign VRM 1.0 Humanoid Human Bones"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        Vrm1HumanBonesPropertyGroup.fixup_human_bones(armature)
        Vrm1HumanBonesPropertyGroup.check_last_bone_names_and_update(
            armature_data.name, defer=False
        )
        human_bone_name_to_human_bone = (
            armature_data.vrm_addon_extension.vrm1.humanoid.human_bones.human_bone_name_to_human_bone()
        )
        bones = armature_data.bones

        Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
        Vrm0HumanoidPropertyGroup.check_last_bone_names_and_update(
            armature_data.name, defer=False
        )
        vrm0_humanoid = armature_data.vrm_addon_extension.vrm0.humanoid
        if vrm0_humanoid.all_required_bones_are_assigned():
            for vrm0_human_bone in vrm0_humanoid.human_bones:
                if (
                    vrm0_human_bone.node.bone_name
                    not in vrm0_human_bone.node_candidates
                ):
                    continue
                vrm0_name = Vrm0HumanBoneName.from_str(vrm0_human_bone.bone)
                if not vrm0_name:
                    logger.error(f"Invalid VRM0 bone name str: {vrm0_human_bone.bone}")
                    continue
                vrm1_name = vrm0_human_bone_name_to_vrm1_human_bone_name.get(vrm0_name)
                if vrm1_name is None:
                    logger.error(f"Invalid VRM0 bone name: {vrm0_name}")
                    continue
                human_bone = human_bone_name_to_human_bone.get(vrm1_name)
                if not human_bone:
                    continue
                if vrm0_human_bone.node.bone_name not in human_bone.node_candidates:
                    continue
                human_bone.node.bone_name = vrm0_human_bone.node.bone_name

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
                human_bone.node.bone_name = bone_name
                break

        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        armature_name: str  # type: ignore[no-redef]


class VRM_OT_update_vrm1_expression_ui_list_elements(bpy.types.Operator):
    bl_idname = "vrm.update_vrm1_expression_ui_list_elements"
    bl_label = "Update VRM 1.0 Expression UI List Elements"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, _context: bpy.types.Context) -> set[str]:
        for armature in bpy.data.armatures:
            expressions = armature.vrm_addon_extension.vrm1.expressions

            # UIList用のダミー要素を設定する
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
