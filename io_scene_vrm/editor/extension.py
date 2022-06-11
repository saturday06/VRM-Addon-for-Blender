import functools

import bpy

from .node_constraint1.property_group import NodeConstraint1NodeConstraintPropertyGroup
from .property_group import StringPropertyGroup
from .spring_bone1.property_group import SpringBone1SpringBonePropertyGroup
from .vrm0.property_group import Vrm0HumanoidPropertyGroup, Vrm0PropertyGroup
from .vrm1.property_group import Vrm1HumanBonesPropertyGroup, Vrm1PropertyGroup


class VrmAddonSceneExtensionPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    mesh_object_names: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )

    @staticmethod
    def check_mesh_object_names_and_update(
        defer: bool = True,
    ) -> None:
        mesh_object_names = [obj.name for obj in bpy.data.objects if obj.type == "MESH"]

        up_to_date = (
            mesh_object_names
            == bpy.context.scene.vrm_addon_extension.mesh_object_names[:]
        )

        if up_to_date:
            return

        if defer:
            bpy.app.timers.register(
                functools.partial(
                    VrmAddonSceneExtensionPropertyGroup.check_mesh_object_names_and_update,
                    False,
                )
            )
            return

        bpy.context.scene.vrm_addon_extension.mesh_object_names.clear()
        for mesh_object_name in mesh_object_names:
            n = bpy.context.scene.vrm_addon_extension.mesh_object_names.add()
            n.value = mesh_object_name
            n.name = mesh_object_name  # for UI


class VrmAddonBoneExtensionPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    uuid: bpy.props.StringProperty()  # type: ignore[valid-type]


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

    node_constraint1: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=NodeConstraint1NodeConstraintPropertyGroup  # noqa: F722
    )

    armature_data_name: bpy.props.StringProperty()  # type: ignore[valid-type]

    SPEC_VERSION_VRM0 = "0.0"
    SPEC_VERSION_VRM1 = "1.0-beta"
    spec_version_items = [
        (SPEC_VERSION_VRM0, "VRM 0.0", "", "NONE", 0),
        (SPEC_VERSION_VRM1, "VRM 1.0 Beta (EXPERIMENTAL)", "", "EXPERIMENTAL", 1),
    ]

    spec_version: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=spec_version_items,
        name="Spec Version",  # noqa: F722
    )

    def is_vrm0(self) -> bool:
        return str(self.spec_version) == self.SPEC_VERSION_VRM0

    def is_vrm1(self) -> bool:
        return str(self.spec_version) == self.SPEC_VERSION_VRM1


def update_internal_cache() -> None:
    VrmAddonSceneExtensionPropertyGroup.check_mesh_object_names_and_update(defer=False)
    for armature in bpy.data.armatures:
        Vrm0HumanoidPropertyGroup.check_last_bone_names_and_update(
            armature.name, defer=False
        )
        Vrm1HumanBonesPropertyGroup.check_last_bone_names_and_update(
            armature.name, defer=False
        )
