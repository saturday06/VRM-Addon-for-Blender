import bpy

from .vrm0.property_group import Vrm0PropertyGroup
from .vrm1.property_group import Vrm1PropertyGroup


class VrmAddonArmatureExtensionPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    addon_version: bpy.props.IntVectorProperty(  # type: ignore[valid-type]
        size=3  # noqa: F722
    )

    vrm0: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm0PropertyGroup  # noqa: F722
    )

    vrm1: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm1PropertyGroup  # noqa: F722
    )

    armature_data_name: bpy.props.StringProperty()  # type: ignore[valid-type]

    SPEC_VERSION_VRM0 = "0.0"
    SPEC_VERSION_VRM1 = "1.0-beta"
    spec_version_items = [
        (SPEC_VERSION_VRM0, "0.0", "", 0),
        (SPEC_VERSION_VRM1, "1.0 Beta (EXPERIMENTAL)", "", 1),
    ]

    spec_version: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=spec_version_items,
        name="Spec Version",  # noqa: F722
    )

    def is_vrm0(self) -> bool:
        return str(self.spec_version) == self.SPEC_VERSION_VRM0

    def is_vrm1(self) -> bool:
        return str(self.spec_version) == self.SPEC_VERSION_VRM1
