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
from ..khr_xmp_json_ld.property_group import KhrXmpJsonLdKhrAvatarPacketPropertyGroup

logger = get_logger(__name__)


# https://github.com/Kjakubzak/glTF/blob/4a1f58a84aa5f9934b749779b89678727d3d2a5c/extensions/2.0/Khronos/KHR_avatar/README.md
class KhrAvatarPropertyGroup(PropertyGroup):
    khr_xmp_json_ld_packet: PointerProperty(  # type: ignore[valid-type]
        type=KhrXmpJsonLdKhrAvatarPacketPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        khr_xmp_json_ld_packet: (  # type: ignore[no-redef]
            KhrXmpJsonLdKhrAvatarPacketPropertyGroup
        )


def get_armature_khr_avatar_extension(armature: Armature) -> KhrAvatarPropertyGroup:
    from ..extension import get_armature_extension

    khr_avatar = get_armature_extension(armature).khr_avatar
    return khr_avatar
