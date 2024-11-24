# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Set as AbstractSet
from typing import Callable, Optional, Protocol, TypeVar, Union, runtime_checkable

from bpy.app.translations import pgettext
from bpy.types import (
    AnyType,
    Armature,
    Context,
    Operator,
    Panel,
    UILayout,
)

from ..common import version
from ..common.preferences import get_preferences
from . import make_armature, search, validation
from .extension import get_armature_extension
from .ops import layout_operator

__AddOperator = TypeVar("__AddOperator", bound=Operator)
__RemoveOperator = TypeVar("__RemoveOperator", bound=Operator)
__MoveUpOperator = TypeVar("__MoveUpOperator", bound=Operator)
__MoveDownOperator = TypeVar("__MoveDownOperator", bound=Operator)


@runtime_checkable
class TemplateListCollectionProtocol(Protocol):
    def __len__(self) -> int: ...
    def __getitem__(self, index: int) -> object: ...


def draw_template_list(
    layout: UILayout,
    template_list_idname: str,
    base_object: AnyType,
    collection_attribue_name: str,
    active_index_attribute_name: str,
    add_operator_type: type[__AddOperator],
    remove_operator_type: type[__RemoveOperator],
    move_up_operator_type: type[__MoveUpOperator],
    move_down_operator_type: type[__MoveDownOperator],
    *,
    can_remove: Callable[[int], bool] = lambda _: True,
    can_move: Callable[[int], bool] = lambda _: True,
    compact: bool = False,
) -> tuple[
    list[Union[__AddOperator, __RemoveOperator, __MoveUpOperator, __MoveDownOperator]],
    list[Union[__RemoveOperator, __MoveUpOperator, __MoveDownOperator]],
    int,
    object,
    tuple[
        __AddOperator,
        __RemoveOperator,
        Optional[__MoveUpOperator],
        Optional[__MoveDownOperator],
    ],
]:
    collection = getattr(base_object, collection_attribue_name, None)
    if not isinstance(collection, TemplateListCollectionProtocol):
        message = (
            f"{collection}.{collection_attribue_name}"
            + " is not a Template List Collection Protocol."
        )
        raise TypeError(message)

    active_index = getattr(base_object, active_index_attribute_name, None)
    if not isinstance(active_index, int):
        message = f"{base_object}.{active_index_attribute_name} is not an int."
        raise TypeError(message)

    if 0 <= active_index < len(collection):
        active_object = collection[active_index]
    else:
        active_object = None

    length = len(collection)
    list_row_len = 4 if length > int(compact) else 2

    list_row = layout.row()
    list_row.template_list(
        template_list_idname,
        "",
        base_object,
        collection_attribue_name,
        base_object,
        active_index_attribute_name,
        rows=list_row_len,
    )
    list_side_column = list_row.column(align=True)
    add_operator = layout_operator(
        list_side_column, add_operator_type, icon="ADD", text="", translate=False
    )

    if length >= 1 and 0 <= active_index < length and can_remove(active_index):
        remove_operator_parent = list_side_column
    else:
        remove_operator_parent = list_side_column.column(align=True)
        remove_operator_parent.enabled = False

    remove_operator = layout_operator(
        remove_operator_parent,
        remove_operator_type,
        icon="REMOVE",
        text="",
        translate=False,
    )

    if length >= 2 and 0 <= active_index < length and can_move(active_index):
        move_operator_parent = list_side_column
    else:
        move_operator_parent = list_side_column.column(align=True)
        move_operator_parent.enabled = False

    collection_ops: list[
        Union[__AddOperator, __RemoveOperator, __MoveUpOperator, __MoveDownOperator]
    ] = [add_operator]
    collection_item_ops: list[
        Union[__RemoveOperator, __MoveUpOperator, __MoveDownOperator]
    ] = [remove_operator]

    if length > int(compact):
        move_operator_parent.separator()
        move_up_operator = layout_operator(
            move_operator_parent,
            move_up_operator_type,
            icon="TRIA_UP",
            text="",
            translate=False,
        )
        collection_item_ops.append(move_up_operator)
        move_down_operator = layout_operator(
            move_operator_parent,
            move_down_operator_type,
            icon="TRIA_DOWN",
            text="",
            translate=False,
        )
        collection_item_ops.append(move_down_operator)
    else:
        move_up_operator = None
        move_down_operator = None

    collection_ops.extend(collection_item_ops)

    return (
        collection_ops,
        collection_item_ops,
        active_index,
        active_object,
        (add_operator, remove_operator, move_up_operator, move_down_operator),
    )


class VRM_PT_vrm_armature_object_property(Panel):
    bl_idname = "VRM_PT_vrm_armature_object_property"
    bl_label = "VRM"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context: Context) -> bool:
        active_object = context.active_object
        if not active_object:
            return False
        armature_data = active_object.data
        return isinstance(armature_data, Armature)

    def draw(self, _context: Context) -> None:
        warning_message = version.panel_warning_message()
        if not warning_message:
            return

        box = self.layout.box()
        warning_column = box.column()
        for index, warning_line in enumerate(warning_message.splitlines()):
            warning_column.label(
                text=warning_line,
                translate=False,
                icon="NONE" if index else "ERROR",
            )


def add_armature(add_armature_op: Operator, _context: Context) -> None:
    layout_operator(
        add_armature_op.layout,
        make_armature.ICYP_OT_make_armature,
        text="VRM Humanoid",
        icon="OUTLINER_OB_ARMATURE",
    ).skip_heavy_armature_setup = True


class VRM_PT_current_selected_armature(Panel):
    bl_idname = "VRM_PT_current_selected_armature"
    bl_label = "Current selected armature"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options: AbstractSet[str] = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return search.multiple_armatures_exist(context)

    def draw(self, context: Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        layout = self.layout
        layout.label(text=armature.name, icon="ARMATURE_DATA", translate=False)


class VRM_PT_controller(Panel):
    bl_idname = "ICYP_PT_ui_controller"
    bl_label = "Operator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="TOOL_SETTINGS")

    def draw(self, context: Context) -> None:
        layout = self.layout
        preferences = get_preferences(context)

        # draw_main
        layout_operator(
            layout,
            make_armature.ICYP_OT_make_armature,
            text=pgettext("Create VRM Model"),
            icon="OUTLINER_OB_ARMATURE",
        ).skip_heavy_armature_setup = True
        vrm_validator_op = layout_operator(
            layout,
            validation.WM_OT_vrm_validator,
            text=pgettext("Check as VRM Model"),
            icon="VIEWZOOM",
        )
        vrm_validator_op.show_successful_message = True
        layout.prop(preferences, "export_invisibles")
        layout.prop(preferences, "export_only_selections")

        armature = search.current_armature(context)
        if armature:
            vrm_validator_op.armature_object_name = armature.name
            armature_data = armature.data
            if isinstance(armature_data, Armature):
                layout.prop(
                    get_armature_extension(armature_data),
                    "spec_version",
                    text="",
                    translate=False,
                )


class VRM_PT_controller_unsupported_blender_version_warning(Panel):
    bl_idname = "VRM_PT_controller_unsupported_blender_version_warning"
    bl_label = "Unsupported Blender Version Warning"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options: AbstractSet[str] = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, _context: Context) -> bool:
        return bool(version.panel_warning_message())

    def draw(self, _context: Context) -> None:
        warning_message = version.panel_warning_message()
        if warning_message is None:
            return
        box = self.layout.box()
        warning_column = box.column()
        for index, warning_line in enumerate(warning_message.splitlines()):
            warning_column.label(
                text=warning_line,
                translate=False,
                icon="NONE" if index else "ERROR",
            )
