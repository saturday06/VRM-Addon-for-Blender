# SPDX-License-Identifier: MIT OR GPL-3.0-or-later


from typing import TYPE_CHECKING

from bpy.props import (
    PointerProperty,
)
from bpy.types import PropertyGroup

from ...common.logger import get_logger
from ..khr_xmp_json_ld.property_group import KhrXmpJsonLdKhrCharacterPacketPropertyGroup

logger = get_logger(__name__)


class KhrCharacterPropertyGroup(PropertyGroup):
    khr_xmp_json_ld_packet: PointerProperty(  # type: ignore[valid-type]
        type=KhrXmpJsonLdKhrCharacterPacketPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        khr_xmp_json_ld_packet: (  # type: ignore[no-redef]
            KhrXmpJsonLdKhrCharacterPacketPropertyGroup
        )
