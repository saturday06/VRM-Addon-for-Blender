# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from bpy.types import Context, UILayout, UIList

from ...common.logger import get_logger
from ..property_group import StringPropertyGroup
from .property_group import KhrXmpJsonLdKhrCharacterPacketPropertyGroup

logger = get_logger(__name__)


class VRM_UL_khr_xmp_json_ld_packet_dc_creator(UIList):
    bl_idname = "VRM_UL_khr_xmp_json_ld_packet_dc_creator"

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
