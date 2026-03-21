# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from bpy.types import Armature, Context, UILayout, UIList

from ...common import convert
from ...common.logger import get_logger
from .menu import (
    VRM_MT_spring_bone1_collider_group_collider,
    VRM_MT_spring_bone1_spring_collider_group,
)
from .property_group import (
    SpringBone1ColliderGroupPropertyGroup,
    SpringBone1ColliderGroupReferencePropertyGroup,
    SpringBone1ColliderPropertyGroup,
    SpringBone1ColliderReferencePropertyGroup,
    SpringBone1JointPropertyGroup,
    SpringBone1SpringPropertyGroup,
)

logger = get_logger(__name__)


class VRM_UL_spring_bone1_collider(UIList):
    bl_idname = "VRM_UL_spring_bone1_collider"

    def filter_items(
        self,
        _context: Context,
        data: object,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        items = convert.sequence_or_none(getattr(data, propname, None))
        if items is None:
            return ([], [])

        flt_flags: list[int] = [self.bitflag_filter_item] * len(items)
        flt_neworder: list[int] = []

        filter_name: str = self.filter_name.casefold()
        if not filter_name:
            return (flt_flags, flt_neworder)

        for index, item in enumerate(items):
            if (
                isinstance(item, SpringBone1ColliderPropertyGroup)
                and (bpy_object := item.bpy_object)
                and filter_name in bpy_object.name.casefold()
            ):
                continue
            flt_flags[index] = 0

        return (flt_flags, flt_neworder)

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        _data: object,
        collider: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(collider, SpringBone1ColliderPropertyGroup):
            return

        icon = "SPHERE"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        name = ""
        bpy_object = collider.bpy_object
        if bpy_object:
            name = bpy_object.name
        layout.label(text=name, translate=False, icon=icon)


class VRM_UL_spring_bone1_collider_group(UIList):
    bl_idname = "VRM_UL_spring_bone1_collider_group"

    def filter_items(
        self,
        _context: Context,
        data: object,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        items = convert.sequence_or_none(getattr(data, propname, None))
        if items is None:
            return ([], [])

        flt_flags: list[int] = [self.bitflag_filter_item] * len(items)
        flt_neworder: list[int] = []

        filter_name: str = self.filter_name.casefold()
        if not filter_name:
            return (flt_flags, flt_neworder)

        for index, item in enumerate(items):
            if (
                isinstance(item, SpringBone1ColliderGroupPropertyGroup)
                and filter_name in item.vrm_name.casefold()
            ):
                continue
            flt_flags[index] = 0

        return (flt_flags, flt_neworder)

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        _data: object,
        collider_group: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(collider_group, SpringBone1ColliderGroupPropertyGroup):
            return

        icon = "PIVOT_INDIVIDUAL"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        layout.label(text=collider_group.vrm_name, translate=False, icon=icon)


class VRM_UL_spring_bone1_collider_group_collider(UIList):
    bl_idname = "VRM_UL_spring_bone1_collider_group_collider"

    def filter_items(
        self,
        _context: Context,
        data: object,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        items = convert.sequence_or_none(getattr(data, propname, None))
        if items is None:
            return ([], [])

        flt_flags: list[int] = [self.bitflag_filter_item] * len(items)
        flt_neworder: list[int] = []

        filter_name: str = self.filter_name.casefold()
        if not filter_name:
            return (flt_flags, flt_neworder)

        for index, item in enumerate(items):
            if (
                isinstance(item, SpringBone1ColliderReferencePropertyGroup)
                and filter_name in item.collider_display_name.casefold()
            ):
                continue
            flt_flags[index] = 0

        return (flt_flags, flt_neworder)

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        collider_group: object,
        collider: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(collider_group, SpringBone1ColliderGroupPropertyGroup):
            return
        if not isinstance(collider, SpringBone1ColliderReferencePropertyGroup):
            return
        icon = "SPHERE"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        armature_data = collider_group.id_data
        if not isinstance(armature_data, Armature):
            logger.error("Failed to find armature")
            return

        if index == collider_group.active_collider_index:
            VRM_MT_spring_bone1_collider_group_collider.draw_input_layout(
                layout,
                collider,
                icon=icon,
            )
        else:
            layout.label(
                text=collider.collider_display_name, translate=False, icon=icon
            )


class VRM_UL_spring_bone1_spring(UIList):
    bl_idname = "VRM_UL_spring_bone1_spring"

    def filter_items(
        self,
        _context: Context,
        data: object,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        items = convert.sequence_or_none(getattr(data, propname, None))
        if items is None:
            return ([], [])

        flt_flags: list[int] = [self.bitflag_filter_item] * len(items)
        flt_neworder: list[int] = []

        filter_name: str = self.filter_name.casefold()
        if not filter_name:
            return (flt_flags, flt_neworder)

        for index, item in enumerate(items):
            if (
                isinstance(item, SpringBone1SpringPropertyGroup)
                and filter_name in item.vrm_name.casefold()
            ):
                continue
            flt_flags[index] = 0

        return (flt_flags, flt_neworder)

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        _data: object,
        spring: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(spring, SpringBone1SpringPropertyGroup):
            return

        icon = "PHYSICS"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        layout.label(text=spring.vrm_name, translate=False, icon=icon)


class VRM_UL_spring_bone1_joint(UIList):
    bl_idname = "VRM_UL_spring_bone1_joint"

    def filter_items(
        self,
        _context: Context,
        data: object,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        items = convert.sequence_or_none(getattr(data, propname, None))
        if items is None:
            return ([], [])

        flt_flags: list[int] = [self.bitflag_filter_item] * len(items)
        flt_neworder: list[int] = []

        filter_name: str = self.filter_name.casefold()
        if not filter_name:
            return (flt_flags, flt_neworder)

        for index, item in enumerate(items):
            if (
                isinstance(item, SpringBone1JointPropertyGroup)
                and filter_name in item.node.bone_name.casefold()
            ):
                continue
            flt_flags[index] = 0

        return (flt_flags, flt_neworder)

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        _data: object,
        joint: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(joint, SpringBone1JointPropertyGroup):
            return

        icon = "BONE_DATA"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        layout.label(text=joint.node.bone_name, translate=False, icon=icon)


class VRM_UL_spring_bone1_spring_collider_group(UIList):
    bl_idname = "VRM_UL_spring_bone1_spring_collider_group"

    def filter_items(
        self,
        _context: Context,
        data: object,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        items = convert.sequence_or_none(getattr(data, propname, None))
        if items is None:
            return ([], [])

        flt_flags: list[int] = [self.bitflag_filter_item] * len(items)
        flt_neworder: list[int] = []

        filter_name: str = self.filter_name.casefold()
        if not filter_name:
            return (flt_flags, flt_neworder)

        for index, item in enumerate(items):
            if (
                isinstance(item, SpringBone1ColliderGroupReferencePropertyGroup)
                and filter_name in item.collider_group_display_name.casefold()
            ):
                continue
            flt_flags[index] = 0

        return (flt_flags, flt_neworder)

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        spring: object,
        collider_group: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(spring, SpringBone1SpringPropertyGroup):
            return
        if not isinstance(
            collider_group, SpringBone1ColliderGroupReferencePropertyGroup
        ):
            return

        icon = "PIVOT_INDIVIDUAL"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        armature_data = spring.id_data
        if not isinstance(armature_data, Armature):
            logger.error("Failed to find armature")
            return
        if index == spring.active_collider_group_index:
            VRM_MT_spring_bone1_spring_collider_group.draw_input_layout(
                layout,
                collider_group,
                icon=icon,
            )
        else:
            layout.label(
                text=collider_group.collider_group_display_name,
                translate=False,
                icon=icon,
            )
