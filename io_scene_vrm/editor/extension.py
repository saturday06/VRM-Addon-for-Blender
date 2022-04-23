import bpy

from .spring_bone1.property_group import SpringBone1SpringBonePropertyGroup
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

    spring_bone1: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=SpringBone1SpringBonePropertyGroup  # noqa: F722
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


def __on_change_blender_object_name() -> None:
    for armature in bpy.data.armatures:
        if not hasattr(armature, "vrm_addon_extension") or not isinstance(
            armature.vrm_addon_extension, VrmAddonArmatureExtensionPropertyGroup
        ):
            continue

        # FIXME: Needs optimization!
        for collider_props in armature.vrm_addon_extension.spring_bone1.colliders:
            if collider_props.blender_object:
                name = collider_props.blender_object.name
            else:
                name = ""
            if collider_props.vrm_name != name:
                collider_props.vrm_name = name


__subscription_owner = object()


def setup() -> None:
    subscribe_to = (bpy.types.Object, "name")
    bpy.msgbus.subscribe_rna(
        key=subscribe_to,
        owner=__subscription_owner,
        args=(),
        notify=__on_change_blender_object_name,
    )
    bpy.msgbus.publish_rna(key=subscribe_to)
