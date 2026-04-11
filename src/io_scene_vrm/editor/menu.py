# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math
from typing import Final, Optional

from bpy.app.translations import pgettext
from bpy.types import Context, Menu, PointerProperty, PropertyGroup, UILayout

from ..common.logger import get_logger
from .ops import (
    VRM_OT_assign_bone_to_bone_property_group,
    VRM_OT_unassign_bone_to_bone_property_group,
    layout_operator,
)
from .property_group import BonePropertyGroup

_logger = get_logger(__name__)


class VRM_MT_bone_assignment(Menu):
    bl_label = "Bone Assignment Menu"
    bl_idname = "VRM_MT_bone_assignment"

    CONTEXT_POINTER_BONE_PROPERTY_GROUP: Final = bl_idname + "_bone_property_group"

    @classmethod
    def draw_input_layout(
        cls,
        layout: UILayout,
        bone_property_group: BonePropertyGroup,
        *,
        text: Optional[str] = None,
        icon: str = "BONE_DATA",
        simple: bool = False,
    ) -> UILayout:
        bone_name = bone_property_group.bone_name
        if (
            text is None
            and (path_components := bone_property_group.path_from_id().split("."))
            and (parent_path_components := path_components[:-1])
            and (property_name := path_components[-1])
            and (id_data := bone_property_group.id_data)
            and (parent_path := ".".join(parent_path_components))
            and (parent := id_data.path_resolve(parent_path, False))
            and isinstance(parent, PropertyGroup)
            and (pointer_property := parent.bl_rna.properties.get(property_name))
            and isinstance(pointer_property, PointerProperty)
        ):
            text = pointer_property.name

        if simple:
            label = pgettext(text) if text is not None else ""
            row = layout.row(align=True)
            row.prop_search(
                bone_property_group,
                "bone_name",
                bone_property_group.find_armature(),
                "bones",
                text=label,
                icon=icon,
                translate=False,
            )
            return row

        row = layout.row(align=True)
        if text:
            row = row.split(factor=0.24, align=True)
            row.label(text=pgettext(text) + ":", translate=False)
        row.context_pointer_set(
            cls.CONTEXT_POINTER_BONE_PROPERTY_GROUP, bone_property_group
        )
        row.menu(
            VRM_MT_bone_assignment.bl_idname,
            text=bone_name or " ",
            icon=icon,
            translate=False,
        )
        return row

    def draw(self, context: Context) -> None:
        layout = self.layout

        bone_property_group = getattr(
            context, self.CONTEXT_POINTER_BONE_PROPERTY_GROUP, None
        )
        if not isinstance(bone_property_group, BonePropertyGroup):
            return
        armature_data = bone_property_group.find_armature()
        bone_property_group_path = bone_property_group.path_from_id()

        bone_names = [
            bone_name
            for bone_name in bone_property_group.filter_bone_names(
                armature_data.bones.keys()
            )
            if bone_name != bone_property_group.bone_name
        ]
        # Include the search row in the total item count for column calculation
        all_items_count = len(bone_names) + 1

        row = layout.row()
        column = row.column()
        column.prop_search(
            bone_property_group,
            "bone_name",
            armature_data,
            "bones",
            text="",
            translate=False,
            icon="VIEWZOOM",
        )
        base_item_index = 1
        if bone_property_group.bone_name:
            unassign_op = layout_operator(
                column,
                VRM_OT_unassign_bone_to_bone_property_group,
                text="<Unassign>",
                translate=True,
                icon="REMOVE",
            )
            unassign_op.armature_data_name = armature_data.name
            unassign_op.bone_property_group_path = bone_property_group_path
            all_items_count += 1
            base_item_index = 2

        column_count_limit = 7
        column_items_count_soft_limit = 15
        column_count = min(
            math.ceil(all_items_count / column_items_count_soft_limit),
            column_count_limit,
        )
        column_items_count = math.ceil(all_items_count / column_count)

        for bone_index, bone_name in enumerate(bone_names):
            item_index = base_item_index + bone_index
            if item_index != 0 and item_index % column_items_count == 0:
                column = row.column()

            op = layout_operator(
                column,
                VRM_OT_assign_bone_to_bone_property_group,
                text=bone_name,
                translate=False,
                icon="BONE_DATA",
            )
            op.armature_data_name = armature_data.name
            op.bone_property_group_path = bone_property_group_path
            op.bone_name = bone_name
