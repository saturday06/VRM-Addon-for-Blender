# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from bpy.types import Context, Object, UILayout

from ...common.logger import get_logger
from ..migration import defer_migrate
from ..panel import draw_template_list
from .ops import (
    VRM_OT_add_khr_xmp_json_ld_packet_dc_creator,
    VRM_OT_add_khr_xmp_json_ld_packet_dc_license,
    VRM_OT_add_khr_xmp_json_ld_packet_dc_subject,
    VRM_OT_move_down_khr_xmp_json_ld_packet_dc_creator,
    VRM_OT_move_down_khr_xmp_json_ld_packet_dc_license,
    VRM_OT_move_down_khr_xmp_json_ld_packet_dc_subject,
    VRM_OT_move_up_khr_xmp_json_ld_packet_dc_creator,
    VRM_OT_move_up_khr_xmp_json_ld_packet_dc_license,
    VRM_OT_move_up_khr_xmp_json_ld_packet_dc_subject,
    VRM_OT_remove_khr_xmp_json_ld_packet_dc_creator,
    VRM_OT_remove_khr_xmp_json_ld_packet_dc_license,
    VRM_OT_remove_khr_xmp_json_ld_packet_dc_subject,
)
from .property_group import (
    KhrXmpJsonLdKhrCharacterPacketPropertyGroup,
)
from .ui_list import (
    VRM_UL_khr_xmp_json_ld_packet_dc_creator,
    VRM_UL_khr_xmp_json_ld_packet_dc_license,
    VRM_UL_khr_xmp_json_ld_packet_dc_subject,
)

logger = get_logger(__name__)


def draw_khr_xmp_json_ld_packet_layout(
    armature: Object,
    _context: Context,
    layout: UILayout,
    packet: KhrXmpJsonLdKhrCharacterPacketPropertyGroup,
) -> None:
    defer_migrate(armature.name)

    thumbnail_image_column = layout.column()
    thumbnail_image_column.label(text="Thumbnail Image:")
    thumbnail_image_column.template_ID_preview(packet, "khr_thumbnail_image")

    layout.prop(packet, "dc_title", icon="FILE_BLEND")

    dc_creator_column = layout.column()
    dc_creator_column.label(text="Creator:")
    (
        dc_creator_collection_ops,
        dc_creator_collection_item_ops,
        dc_creator_index,
        _,
        _,
    ) = draw_template_list(
        dc_creator_column,
        VRM_UL_khr_xmp_json_ld_packet_dc_creator,
        packet,
        "dc_creator",
        "active_dc_creator_index",
        VRM_OT_add_khr_xmp_json_ld_packet_dc_creator,
        VRM_OT_remove_khr_xmp_json_ld_packet_dc_creator,
        VRM_OT_move_up_khr_xmp_json_ld_packet_dc_creator,
        VRM_OT_move_down_khr_xmp_json_ld_packet_dc_creator,
        can_remove=lambda _: len(packet.dc_creator) >= 2,
        compact=True,
    )
    for dc_creator_collection_op in dc_creator_collection_ops:
        dc_creator_collection_op.armature_object_name = armature.name

    for dc_creator_collection_item_op in dc_creator_collection_item_ops:
        dc_creator_collection_item_op.dc_creator_index = dc_creator_index

    dc_license_column = layout.column()
    dc_license_column.label(text="License:")
    (
        dc_license_collection_ops,
        dc_license_collection_item_ops,
        dc_license_index,
        _,
        _,
    ) = draw_template_list(
        dc_license_column,
        VRM_UL_khr_xmp_json_ld_packet_dc_license,
        packet,
        "dc_license",
        "active_dc_license_index",
        VRM_OT_add_khr_xmp_json_ld_packet_dc_license,
        VRM_OT_remove_khr_xmp_json_ld_packet_dc_license,
        VRM_OT_move_up_khr_xmp_json_ld_packet_dc_license,
        VRM_OT_move_down_khr_xmp_json_ld_packet_dc_license,
        can_remove=lambda _: len(packet.dc_license) >= 2,
        compact=True,
    )
    for dc_license_collection_op in dc_license_collection_ops:
        dc_license_collection_op.armature_object_name = armature.name

    for dc_license_collection_item_op in dc_license_collection_item_ops:
        dc_license_collection_item_op.dc_license_index = dc_license_index

    layout.prop(packet, "dc_created", icon="FILE_BLEND")
    layout.prop(packet, "dc_rights", icon="FILE_BLEND")
    layout.prop(packet, "dc_publisher", icon="FILE_BLEND")
    layout.prop(packet, "dc_description", icon="FILE_BLEND")

    dc_subject_column = layout.column()
    dc_subject_column.label(text="Subject:")
    (
        dc_subject_collection_ops,
        dc_subject_collection_item_ops,
        dc_subject_index,
        _,
        _,
    ) = draw_template_list(
        dc_subject_column,
        VRM_UL_khr_xmp_json_ld_packet_dc_subject,
        packet,
        "dc_subject",
        "active_dc_subject_index",
        VRM_OT_add_khr_xmp_json_ld_packet_dc_subject,
        VRM_OT_remove_khr_xmp_json_ld_packet_dc_subject,
        VRM_OT_move_up_khr_xmp_json_ld_packet_dc_subject,
        VRM_OT_move_down_khr_xmp_json_ld_packet_dc_subject,
        can_remove=lambda _: len(packet.dc_subject) >= 2,
        compact=True,
    )
    for dc_subject_collection_op in dc_subject_collection_ops:
        dc_subject_collection_op.armature_object_name = armature.name

    for dc_subject_collection_item_op in dc_subject_collection_item_ops:
        dc_subject_collection_item_op.dc_subject_index = dc_subject_index

    layout.prop(packet, "dc_source", icon="FILE_BLEND")
    layout.prop(packet, "khr_version", icon="FILE_BLEND")
