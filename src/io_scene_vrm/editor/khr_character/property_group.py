# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from typing import TYPE_CHECKING

from bpy.props import (
    PointerProperty,
)
from bpy.types import (
    Armature,
    PropertyGroup,
)

from ...common.logger import get_logger
from ..khr_xmp_json_ld.property_group import KhrXmpJsonLdKhrCharacterPacketPropertyGroup

logger = get_logger(__name__)


# https://github.com/Kjakubzak/glTF/blob/4a1f58a84aa5f9934b749779b89678727d3d2a5c/extensions/2.0/Khronos/KHR_character/README.md
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


def get_armature_extension(armature: Armature) -> KhrCharacterPropertyGroup:
    from ..extension import get_armature_extension

    khr_character = get_armature_extension(armature).khr_character
    return khr_character
