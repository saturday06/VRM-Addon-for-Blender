# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Sequence
from typing import TYPE_CHECKING, TypeVar

from bpy.props import (
    EnumProperty,
    IntVectorProperty,
    PointerProperty,
)
from bpy.types import (
    Armature,
    Context,
    PropertyGroup,
)

from ..common.logger import get_logger
from .vrm1.property_group import Vrm1PropertyGroup

logger = get_logger(__name__)


class VrmAddonArmatureExtensionPropertyGroup(PropertyGroup):
    addon_version: IntVectorProperty(  # type: ignore[valid-type]
        size=3,
    )

    vrm1: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1PropertyGroup
    )

    SPEC_VERSION_VRM0 = "0.0"
    SPEC_VERSION_VRM1 = "1.0"
    spec_version_items = (
        (SPEC_VERSION_VRM0, "VRM 0.0", "", "NONE", 0),
        (SPEC_VERSION_VRM1, "VRM 1.0", "", "NONE", 1),
    )

    def update_spec_version(self, _context: Context) -> None:
        pass

    spec_version: EnumProperty(  # type: ignore[valid-type]
        items=spec_version_items,
        name="Spec Version",
        update=update_spec_version,
    )

    def is_vrm0(self) -> bool:
        return str(self.spec_version) == self.SPEC_VERSION_VRM0

    def is_vrm1(self) -> bool:
        return str(self.spec_version) == self.SPEC_VERSION_VRM1

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        addon_version: Sequence[int]  # type: ignore[no-redef]
        vrm1: Vrm1PropertyGroup  # type: ignore[no-redef]
        spec_version: str  # type: ignore[no-redef]


__Extension = TypeVar("__Extension")


def get_vrm_addon_extension_or_raise(
    obj: object, expected_type: type[__Extension]
) -> __Extension:
    extension = getattr(obj, "vrm_addon_extension", None)
    if isinstance(extension, expected_type):
        return extension

    message = f"{extension} is not a {expected_type} but {type(extension)}"
    raise TypeError(message)


def get_armature_extension(
    armature: Armature,
) -> VrmAddonArmatureExtensionPropertyGroup:
    return get_vrm_addon_extension_or_raise(
        armature, VrmAddonArmatureExtensionPropertyGroup
    )
