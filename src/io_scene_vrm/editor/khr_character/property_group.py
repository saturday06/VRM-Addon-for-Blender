# SPDX-License-Identifier: MIT OR GPL-3.0-or-later


from typing import TYPE_CHECKING

from bpy.props import (
    PointerProperty,
)
from bpy.types import PropertyGroup

from ...common.logger import get_logger
from ..khr_xmp_json_ld.property_group import KhrXmpJsonLdKhrCharacterPacketPropertyGroup

logger = get_logger(__name__)


# https://github.com/Kjakubzak/glTF/blob/ee572d4e3148d2f21bb469f3d0575d6701f91b2e/extensions/2.0/Khronos/KHR_character/README.md
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
