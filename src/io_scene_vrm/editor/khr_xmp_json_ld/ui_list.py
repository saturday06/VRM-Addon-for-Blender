# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from bpy.types import Context, UILayout, UIList

from ...common import convert
from ...common.logger import get_logger
from ..property_group import StringPropertyGroup
from .property_group import KhrXmpJsonLdKhrCharacterPacketPropertyGroup

logger = get_logger(__name__)


class VRM_UL_khr_xmp_json_ld_packet_dc_creator(UIList):
    bl_idname = "VRM_UL_khr_xmp_json_ld_packet_dc_creator"

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
                isinstance(item, StringPropertyGroup)
                and filter_name in item.value.casefold()
            ):
                continue
            flt_flags[index] = 0

        return (flt_flags, flt_neworder)

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        packet: object,
        dc_creator_item: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(packet, KhrXmpJsonLdKhrCharacterPacketPropertyGroup):
            return
        if not isinstance(dc_creator_item, StringPropertyGroup):
            return

        icon = "USER"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        if index == packet.active_dc_creator_index:
            layout.prop(dc_creator_item, "value", icon=icon, text="", translate=False)
        else:
            layout.label(text=dc_creator_item.value, icon=icon, translate=False)


class VRM_UL_khr_xmp_json_ld_packet_dc_license(UIList):
    bl_idname = "VRM_UL_khr_xmp_json_ld_packet_dc_license"

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
                isinstance(item, StringPropertyGroup)
                and filter_name in item.value.casefold()
            ):
                continue
            flt_flags[index] = 0

        return (flt_flags, flt_neworder)

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        packet: object,
        dc_license_item: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(packet, KhrXmpJsonLdKhrCharacterPacketPropertyGroup):
            return
        if not isinstance(dc_license_item, StringPropertyGroup):
            return

        icon = "USER"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        if index == packet.active_dc_license_index:
            layout.prop(dc_license_item, "value", icon=icon, text="", translate=False)
        else:
            layout.label(text=dc_license_item.value, icon=icon, translate=False)


class VRM_UL_khr_xmp_json_ld_packet_dc_subject(UIList):
    bl_idname = "VRM_UL_khr_xmp_json_ld_packet_dc_subject"

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
                isinstance(item, StringPropertyGroup)
                and filter_name in item.value.casefold()
            ):
                continue
            flt_flags[index] = 0

        return (flt_flags, flt_neworder)

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        packet: object,
        dc_subject_item: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(packet, KhrXmpJsonLdKhrCharacterPacketPropertyGroup):
            return
        if not isinstance(dc_subject_item, StringPropertyGroup):
            return

        icon = "USER"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        if index == packet.active_dc_subject_index:
            layout.prop(dc_subject_item, "value", icon=icon, text="", translate=False)
        else:
            layout.label(text=dc_subject_item.value, icon=icon, translate=False)
