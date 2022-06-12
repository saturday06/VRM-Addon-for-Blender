import uuid
from typing import Any

import bpy

from ..property_group import BonePropertyGroup


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.shape.schema.json#L7-L27
class SpringBone1ColliderShapeSpherePropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="TRANSLATION",  # noqa: F821
        unit="LENGTH",  # noqa: F821
        default=(0, 0, 0),
    )
    radius: bpy.props.FloatProperty()  # type: ignore[valid-type]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.shape.schema.json#L28-L58
class SpringBone1ColliderShapeCapsulePropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="TRANSLATION",  # noqa: F821
        unit="LENGTH",  # noqa: F821
        default=(0, 0, 0),
    )
    radius: bpy.props.FloatProperty()  # type: ignore[valid-type]
    tail: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="TRANSLATION",  # noqa: F821
        unit="LENGTH",  # noqa: F821
        default=(0, 0, 0),
    )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.shape.schema.json
class SpringBone1ColliderShapePropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    sphere: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=SpringBone1ColliderShapeSpherePropertyGroup  # noqa: F722
    )
    capsule: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=SpringBone1ColliderShapeCapsulePropertyGroup  # noqa: F821
    )

    # for UI
    SHAPE_SPHERE = "Sphere"
    SHAPE_CAPSULE = "Capsule"
    shape_items = [
        (SHAPE_SPHERE, "Sphere", "", 0),
        (SHAPE_CAPSULE, "Capsule", "", 1),
    ]
    shape: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=shape_items, name="Shape"  # noqa: F821
    )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.collider.schema.json
class SpringBone1ColliderPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    def broadcast_bpy_object_name(self) -> None:
        if not self.bpy_object or not self.bpy_object.name:
            self.name = ""  # pylint: disable=attribute-defined-outside-init
            return
        if self.name == self.bpy_object.name:
            return
        self.name = (  # pylint: disable=attribute-defined-outside-init
            self.bpy_object.name
        )

        self.search_one_time_uuid = uuid.uuid4().hex
        for armature in bpy.data.armatures:
            if not hasattr(armature, "vrm_addon_extension"):
                continue

            spring_bone = armature.vrm_addon_extension.spring_bone1

            for collider in spring_bone.colliders:
                if collider.search_one_time_uuid != self.search_one_time_uuid:
                    continue

                for collider_group in spring_bone.collider_groups:
                    for collider_reference in collider_group.colliders:
                        if self.uuid != collider_reference.collider_uuid:
                            continue
                        collider_reference.collider_name = self.name

                return

    node: bpy.props.PointerProperty(type=BonePropertyGroup)  # type: ignore[valid-type]
    shape: bpy.props.PointerProperty(type=SpringBone1ColliderShapePropertyGroup)  # type: ignore[valid-type]

    # for UI
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]

    # for View3D
    bpy_object: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Object  # noqa: F722
    )

    # for references
    uuid: bpy.props.StringProperty()  # type: ignore[valid-type]
    search_one_time_uuid: bpy.props.StringProperty()  # type: ignore[valid-type]

    def refresh(self, armature: bpy.types.Object, bone_name: str) -> None:
        if not self.bpy_object or not self.bpy_object.name:
            return

        if self.bpy_object.parent != armature:
            self.bpy_object.parent = armature
        if self.bpy_object.empty_display_type != "SPHERE":
            self.bpy_object.empty_display_type = "SPHERE"

        if bone_name:
            if self.bpy_object.parent_type != "BONE":
                self.bpy_object.parent_type = "BONE"
            if self.bpy_object.parent_bone != bone_name:
                self.bpy_object.parent_bone = bone_name
        else:
            if self.bpy_object.parent_type != "OBJECT":
                self.bpy_object.parent_type = "OBJECT"

        self.node.refresh(armature)
        self.node.value = bone_name


class SpringBone1ColliderReferencePropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    def __get_collider_name(self) -> str:
        value = self.get("collider_name", "")
        return value if isinstance(value, str) else str(value)

    def __set_collider_name(self, value: Any) -> None:
        if not isinstance(value, str):
            value = str(value)
        self.name = value  # pylint: disable=attribute-defined-outside-init
        if self.get("collider_name") == value:
            return
        self["collider_name"] = value

        self.search_one_time_uuid = uuid.uuid4().hex
        for armature in bpy.data.armatures:
            spring_bone = armature.vrm_addon_extension.spring_bone1
            for collider_group in spring_bone.collider_groups:
                for collider_reference in collider_group.colliders:
                    if (
                        collider_reference.search_one_time_uuid
                        != self.search_one_time_uuid
                    ):
                        continue

                    for collider in spring_bone.colliders:
                        if collider.name == value:
                            self.collider_uuid = collider.uuid
                    return

    collider_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        get=__get_collider_name, set=__set_collider_name
    )
    collider_uuid: bpy.props.StringProperty()  # type: ignore[valid-type]
    search_one_time_uuid: bpy.props.StringProperty()  # type: ignore[valid-type]


# https://github.com/vrm-c/vrm-specification/blob/f2d8f158297fc883aef9c3071ca68fbe46b03f45/specification/0.0/schema/vrm.secondaryanimation.collidergroup.schema.json
class SpringBone1ColliderGroupPropertyGroup(
    bpy.types.PropertyGroup, bpy.types.ID  # type: ignore[misc]
):
    def __get_vrm_name(self) -> str:
        value = self.get("vrm_name", "")
        return value if isinstance(value, str) else str(value)

    def __set_vrm_name(self, vrm_name: Any) -> None:
        if not isinstance(vrm_name, str):
            vrm_name = str(vrm_name)
        self["vrm_name"] = vrm_name
        self.fix_index()

    def fix_index(self) -> None:
        self.search_one_time_uuid = uuid.uuid4().hex
        for armature in bpy.data.armatures:
            spring_bone = armature.vrm_addon_extension.spring_bone1

            for (index, collider_group) in enumerate(spring_bone.collider_groups):
                if collider_group.search_one_time_uuid != self.search_one_time_uuid:
                    continue

                name = f"{index}: {self.vrm_name}"
                self.name = name  # pylint: disable=attribute-defined-outside-init

                for spring in spring_bone.springs:
                    for collider_group_reference in spring.collider_groups:
                        if collider_group_reference.collider_group_uuid == self.uuid:
                            collider_group_reference.collider_group_name = name

                return

    vrm_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Name", get=__get_vrm_name, set=__set_vrm_name  # noqa: F722, F821
    )

    colliders: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Colliders", type=SpringBone1ColliderReferencePropertyGroup  # noqa: F821
    )

    # for UI
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]

    # for reference
    # オブジェクトをコピーした場合同じuuidをもつオブジェクトが複数ある可能性があるのに注意する。
    uuid: bpy.props.StringProperty()  # type: ignore[valid-type]

    search_one_time_uuid: bpy.props.StringProperty()  # type: ignore[valid-type]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.joint.schema.json
class SpringBone1JointPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    node: bpy.props.PointerProperty(type=BonePropertyGroup)  # type: ignore[valid-type]
    hit_radius: bpy.props.FloatProperty()  # type: ignore[valid-type]
    stiffness: bpy.props.FloatProperty()  # type: ignore[valid-type]
    gravity_power: bpy.props.FloatProperty()  # type: ignore[valid-type]
    gravity_dir: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3, default=(0, -1, 0)  # noqa: F722
    )
    drag_force: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.5, min=0, max=1.0
    )

    # for UI
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]


class SpringBone1ColliderGroupReferencePropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    def __get_collider_group_name(self) -> str:
        value = self.get("collider_group_name", "")
        return value if isinstance(value, str) else str(value)

    def __set_collider_group_name(self, value: Any) -> None:
        if not isinstance(value, str):
            value = str(value)
        self.name = value  # pylint: disable=attribute-defined-outside-init
        if self.get("collider_group_name") == value:
            return
        self["collider_group_name"] = value

        self.search_one_time_uuid = uuid.uuid4().hex
        for armature in bpy.data.armatures:
            spring_bone = armature.vrm_addon_extension.spring_bone1
            for spring in spring_bone.springs:
                for collider_group_reference in spring.collider_groups:
                    if (
                        collider_group_reference.search_one_time_uuid
                        != self.search_one_time_uuid
                    ):
                        continue

                    for collider_group in spring_bone.collider_groups:
                        if collider_group.name == value:
                            self.collider_group_uuid = collider_group.uuid
                    return

    collider_group_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        get=__get_collider_group_name, set=__set_collider_group_name
    )
    collider_group_uuid: bpy.props.StringProperty()  # type: ignore[valid-type]
    search_one_time_uuid: bpy.props.StringProperty()  # type: ignore[valid-type]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.spring.schema.json
class SpringBone1SpringPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    vrm_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Name"  # noqa: F821
    )
    joints: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=SpringBone1JointPropertyGroup
    )
    collider_groups: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=SpringBone1ColliderGroupReferencePropertyGroup,
    )

    # for UI
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]
    show_expanded_bones: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Bones"  # noqa: F821
    )
    show_expanded_collider_groups: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Collider Groups"  # noqa: F722
    )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.schema.json
class SpringBone1SpringBonePropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    colliders: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=SpringBone1ColliderPropertyGroup,
    )
    collider_groups: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=SpringBone1ColliderGroupPropertyGroup,
    )
    springs: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=SpringBone1SpringPropertyGroup,
    )

    # for UI
    show_expanded_colliders: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Spring Bone Colliders"  # noqa: F722
    )
    show_expanded_collider_groups: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Spring Bone Collider Groups"  # noqa: F722
    )
    show_expanded_springs: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Spring Bone Springs"  # noqa: F722
    )
