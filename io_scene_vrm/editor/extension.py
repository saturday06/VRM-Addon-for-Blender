import bpy

from .vrm0.property_group import Vrm0PropertyGroup


class VrmAddonArmatureExtensionPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    addon_version: bpy.props.IntVectorProperty(  # type: ignore[valid-type]
        size=3  # noqa: F722
    )

    vrm0: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="VRM 0.x", type=Vrm0PropertyGroup  # noqa: F722
    )

    armature_data_name: bpy.props.StringProperty()  # type: ignore[valid-type]

    spec_version_items = [  # noqa: SC200
        ("0.0", "0.0", "", 0),
        ("1.0-beta", "1.0-beta", "", 1),
    ]

    spec_version: bpy.props.EnumProperty(  # type: ignore[valid-type] # noqa: SC200
        items=spec_version_items,  # noqa: SC200
        name="Spec Version",  # noqa: F722
    )
