import uuid
from typing import Any, Optional, Set

import bpy
from bpy.app.translations import pgettext

from ..common import human_bone_constants
from ..common.preferences import get_preferences
from . import (
    detail_mesh_maker,
    glsl_drawer,
    helper,
    make_armature,
    mesh_from_bone_envelopes,
    search,
    validation,
)
from .glsl_drawer import GlslDrawObj
from .migration import get_all_bone_property_groups, migrate


class ObjectPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    value: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Object Value", type=bpy.types.Object  # noqa: F722
    )


class StringPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    value: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="String Value"  # noqa: F722
    )


class FloatPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    value: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Float Value"  # noqa: F722
    )


class MeshPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    def get_value(self) -> str:
        if (
            not self.link_to_mesh
            or not self.link_to_mesh.name
            or not self.link_to_mesh.parent
            or self.link_to_mesh.parent.type != "MESH"
            or not self.link_to_mesh.parent.data
            or not self.link_to_mesh.parent.data.name
        ):
            return ""
        return str(self.link_to_mesh.parent.data.name)

    def set_value(self, value: Any) -> None:
        if not isinstance(value, str) or value not in bpy.data.meshes:
            return
        mesh = bpy.data.meshes[value]
        mesh_obj: Optional[bpy.types.Object] = None
        for obj in bpy.data.objects:
            if obj.data == mesh:
                mesh_obj = obj
                break
        if mesh_obj is None:
            return

        if not self.link_to_mesh or not self.link_to_mesh.name:
            uuid_str = uuid.uuid4().hex
            self.link_to_mesh = bpy.data.objects.new(
                name="VrmAddonLinkToMesh" + uuid_str, object_data=None
            )
        self.link_to_mesh.parent = mesh_obj

    value: bpy.props.StringProperty(  # type: ignore[valid-type]
        get=get_value, set=set_value
    )
    link_to_mesh: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Object  # noqa: F722
    )


class BonePropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    def refresh(self, armature: bpy.types.Object) -> None:
        if (
            self.link_to_bone
            and self.link_to_bone.parent
            and self.link_to_bone.parent == armature
        ):
            return

        value = self.value
        uuid_str = uuid.uuid4().hex
        self.link_to_bone = bpy.data.objects.new(
            name="VrmAddonLinkToBone" + uuid_str, object_data=None
        )
        self.link_to_bone.parent = armature
        self.value = value

    def get_value(self) -> str:
        if (
            self.link_to_bone
            and self.link_to_bone.parent_bone
            and self.link_to_bone.parent
            and self.link_to_bone.parent.name
            and self.link_to_bone.parent.type == "ARMATURE"
            and self.link_to_bone.parent_bone in self.link_to_bone.parent.data.bones
        ):
            return str(self.link_to_bone.parent_bone)
        return ""

    def set_value(self, value: Any) -> None:
        if not self.link_to_bone or not self.link_to_bone.parent:
            for armature in bpy.data.objects:
                if armature.type != "ARMATURE":
                    continue
                if all(
                    bone_property_group != self
                    for bone_property_group in get_all_bone_property_groups(armature)
                ):
                    continue
                self.refresh(armature)
                break
        if not self.link_to_bone.parent:
            print("WARNING: No armature found")
            return

        value_str = str(value)
        if not value_str or value_str not in self.link_to_bone.parent.data.bones:
            self.link_to_bone.parent_type = "OBJECT"
            self.link_to_bone.parent_bone = ""
        elif self.link_to_bone.parent_bone == value_str:
            return
        else:
            self.link_to_bone.parent_bone = value_str
            self.link_to_bone.parent_type = "BONE"

        for (
            collider_group
        ) in (
            self.link_to_bone.parent.data.vrm_addon_extension.vrm0.secondary_animation.collider_groups
        ):
            collider_group.refresh(self.link_to_bone.parent)

    value: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Bone",  # noqa: F821
        get=get_value,
        set=set_value,
    )
    link_to_bone: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Object  # noqa: F722
    )


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_Humanoid.cs#L70-L164
class Vrm0HumanoidBonePropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    bone: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="VRM Humanoid Bone Name"  # noqa: F722
    )
    node: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Bone Name", type=BonePropertyGroup  # noqa: F722
    )
    use_default_values: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Unity's HumanLimit.useDefaultValues", default=True  # noqa: F722
    )
    min: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3, name="Unity's HumanLimit.min"  # noqa: F722
    )
    max: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3, name="Unity's HumanLimit.max"  # noqa: F722
    )
    center: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3, name="Unity's HumanLimit.center"  # noqa: F722
    )
    axis_length: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Unity's HumanLimit.axisLength"  # noqa: F722
    )


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_Humanoid.cs#L166-L195
class Vrm0HumanoidPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    human_bones: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Human Bones", type=Vrm0HumanoidBonePropertyGroup  # noqa: F722
    )
    arm_stretch: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Arm Stretch", default=0.05  # noqa: F722
    )
    leg_stretch: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Leg Stretch", default=0.05  # noqa: F722
    )
    upper_arm_twist: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Upper Arm Twist", default=0.5  # noqa: F722
    )
    lower_arm_twist: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Lower Arm Twist", default=0.5  # noqa: F722
    )
    upper_leg_twist: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Upper Leg Twist", default=0.5  # noqa: F722
    )
    lower_leg_twist: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Lower Leg Twist", default=0.5  # noqa: F722
    )
    feet_spacing: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="Feet Spacing", default=0  # noqa: F722
    )
    has_translation_dof: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Has Translation DoF", default=False  # noqa: F722
    )


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_FirstPerson.cs#L10-L22
class Vrm0DegreeMapPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    curve: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=8, name="Curve", default=[0, 0, 0, 1, 1, 1, 1, 0]  # noqa: F821
    )
    x_range: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="X Range", default=90  # noqa: F722
    )
    y_range: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Y Range", default=10  # noqa: F722
    )


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_FirstPerson.cs#L32-L41
class Vrm0MeshAnnotationPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    mesh: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Mesh", type=MeshPropertyGroup  # noqa: F821
    )
    first_person_flag_items = [
        ("Auto", "Auto", "", 0),
        ("FirstPersonOnly", "FirstPersonOnly", "", 1),
        ("ThirdPersonOnly", "ThirdPersonOnly", "", 2),
        ("Both", "Both", "", 3),
    ]
    first_person_flag: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=first_person_flag_items, name="First Person Flag"  # noqa: F722
    )


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_FirstPerson.cs#L50-L91
class Vrm0FirstPersonPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    first_person_bone: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="First Person Bone", type=BonePropertyGroup  # noqa: F722
    )
    first_person_bone_offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        name="First Person Bone Offset",  # noqa: F722
        subtype="TRANSLATION",  # noqa: F821
        unit="LENGTH",  # noqa: F821
        default=(0, 0, 0),
    )
    mesh_annotations: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Mesh Annotations", type=Vrm0MeshAnnotationPropertyGroup  # noqa: F722
    )
    look_at_type_name_items = [
        ("Bone", "Bone", "Bone", "BONE_DATA", 0),
        ("BlendShape", "BlendShape", "BlendShape", "SHAPEKEY_DATA", 1),
    ]
    look_at_type_name: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=look_at_type_name_items, name="Look At Type Name"  # noqa: F722
    )
    look_at_horizontal_inner: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm0DegreeMapPropertyGroup, name="Look At Horizontal Inner"  # noqa: F722
    )
    look_at_horizontal_outer: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm0DegreeMapPropertyGroup, name="Look At Horizontal Outer"  # noqa: F722
    )
    look_at_vertical_down: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm0DegreeMapPropertyGroup, name="Look At Vertical Down"  # noqa: F722
    )
    look_at_vertical_up: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Vrm0DegreeMapPropertyGroup, name="lookAt Vertical Up"  # noqa: F722
    )


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_BlendShape.cs#L18-L30
class Vrm0BlendShapeBindPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    mesh: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Mesh", type=MeshPropertyGroup  # noqa: F821
    )
    index: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Index"  # noqa: F821
    )
    weight: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Weight", min=0, max=1  # noqa: F821
    )


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_BlendShape.cs#L9-L16
class Vrm0MaterialValueBindPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    material: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Material", type=bpy.types.Material  # noqa: F821
    )
    property_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Property Name"  # noqa: F722
    )
    target_value: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Target Value", type=FloatPropertyGroup  # noqa: F722
    )


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_BlendShape.cs#L62-L99
class Vrm0BlendShapeGroupPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    name: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Name"  # noqa: F821
    )
    preset_name_items = [
        ("unknown", "unknown", "", "NONE", 0),
        ("neutral", "neutral", "", "NONE", 1),
        ("a", "a", "", "EVENT_A", 2),
        ("i", "i", "", "EVENT_I", 3),
        ("u", "u", "", "EVENT_U", 4),
        ("e", "e", "", "EVENT_E", 5),
        ("o", "o", "", "EVENT_O", 6),
        ("blink", "blink", "", "HIDE_ON", 7),
        ("joy", "joy", "", "HEART", 8),
        ("angry", "angry", "", "ORPHAN_DATA", 9),
        ("sorrow", "sorrow", "", "MOD_FLUIDSIM", 10),
        ("fun", "fun", "", "LIGHT_SUN", 11),
        ("lookup", "lookup", "", "ANCHOR_TOP", 12),
        ("lookdown", "lookdown", "", "ANCHOR_BOTTOM", 13),
        ("lookleft", "lookleft", "", "ANCHOR_RIGHT", 14),
        ("lookright", "lookright", "", "ANCHOR_LEFT", 15),
        ("blink_l", "blink_l", "", "HIDE_ON", 16),
        ("blink_r", "blink_r", "", "HIDE_ON", 17),
    ]
    preset_name: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=preset_name_items, name="Preset"  # noqa: F821
    )
    binds: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=Vrm0BlendShapeBindPropertyGroup, name="Binds"  # noqa: F821
    )
    material_values: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=Vrm0MaterialValueBindPropertyGroup, name="Material Values"  # noqa: F722
    )
    is_binary: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Is Binary"  # noqa: F722
    )

    # for UI
    show_expanded_binds: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Binds"  # noqa: F821
    )
    show_expanded_material_values: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Material Values"  # noqa: F722
    )


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_SecondaryAnimation.cs#L10-L18
class Vrm0SecondaryAnimationCollider(bpy.types.PropertyGroup):  # type: ignore[misc]
    blender_object: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Object  # noqa: F722
    )

    def refresh(self, armature: bpy.types.Object, bone_name: str) -> None:
        if not self.blender_object or not self.blender_object.name:
            return

        self.blender_object.name = self.blender_object.name
        self.blender_object.parent = armature
        self.blender_object.empty_display_type = "SPHERE"
        if bone_name:
            self.blender_object.parent_type = "BONE"
            self.blender_object.parent_bone = bone_name
        else:
            self.blender_object.parent_type = "OBJECT"


# https://github.com/vrm-c/vrm-specification/blob/f2d8f158297fc883aef9c3071ca68fbe46b03f45/specification/0.0/schema/vrm.secondaryanimation.collidergroup.schema.json
# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_SecondaryAnimation.cs#L21-L29
class Vrm0SecondaryAnimationColliderGroupPropertyGroup(
    bpy.types.PropertyGroup, bpy.types.ID  # type: ignore[misc]
):
    node: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Node", type=BonePropertyGroup  # noqa: F821
    )
    # offsetとradiusはコライダー自身のデータを用いる
    colliders: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Colliders", type=Vrm0SecondaryAnimationCollider  # noqa: F821
    )

    def refresh(self, armature: bpy.types.Object) -> None:
        self.name = (
            str(self.node.value) if self.node and self.node.value else ""
        ) + f"#{self.uuid}"
        for index, collider in reversed(list(enumerate(list(self.colliders)))):
            if not collider.blender_object or not collider.blender_object.name:
                self.colliders.remove(index)
            else:
                collider.refresh(armature, self.node.value)
        for (
            bone_group
        ) in armature.data.vrm_addon_extension.vrm0.secondary_animation.bone_groups:
            bone_group.refresh(armature)

    # for reference from Vrm0SecondaryAnimationGroupPropertyGroup
    name: bpy.props.StringProperty()  # type: ignore[valid-type]
    uuid: bpy.props.StringProperty()  # type: ignore[valid-type]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_SecondaryAnimation.cs#L32-L67
class Vrm0SecondaryAnimationGroupPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    comment: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Comment"  # noqa: F821
    )
    stiffiness: bpy.props.FloatProperty(  # type: ignore[valid-type] # noqa: SC200
        name="Stiffiness"  # noqa: F821
    )
    gravity_power: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Gravity Power"  # noqa: F722
    )
    gravity_dir: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3, name="Gravity Dir"  # noqa: F722
    )
    drag_force: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="DragForce"  # noqa: F821
    )
    center: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Center", type=BonePropertyGroup  # noqa: F821
    )
    hit_radius: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Hit Radius"  # noqa: F722
    )
    bones: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Bones", type=BonePropertyGroup  # noqa: F821
    )
    collider_groups: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Collider Group",  # noqa: F722
        type=StringPropertyGroup,
    )

    # for UI
    show_expanded_bones: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Bones"  # noqa: F821
    )
    show_expanded_collider_groups: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Collider Groups"  # noqa: F722
    )

    def refresh(self, armature: bpy.types.Object) -> None:
        collider_group_uuid_to_name = {
            collider_group.uuid: collider_group.name
            for collider_group in armature.data.vrm_addon_extension.vrm0.secondary_animation.collider_groups
        }
        for index, collider_group in reversed(list(enumerate(self.collider_groups))):
            uuid_str = collider_group.value.split("#")[-1:][0]
            name = collider_group_uuid_to_name.get(uuid_str)
            if name is None:
                self.collider_groups.remove(index)
            else:
                collider_group.value = name


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_Meta.cs#L33-L149
class Vrm0MetaPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc] # noqa: N801
    allowed_user_name_items = [
        ("OnlyAuthor", "OnlyAuthor", "", 0),
        ("ExplicitlyLicensedPerson", "ExplicitlyLicensedPerson", "", 1),
        ("Everyone", "Everyone", "", 2),
    ]
    violent_ussage_name_items = [  # noqa: SC200
        ("Disallow", "Disallow", "", 0),
        ("Allow", "Allow", "", 1),
    ]
    sexual_ussage_name_items = [  # noqa: SC200
        ("Disallow", "Disallow", "", 0),
        ("Allow", "Allow", "", 1),
    ]
    commercial_ussage_name_items = [  # noqa: SC200
        ("Disallow", "Disallow", "", 0),
        ("Allow", "Allow", "", 1),
    ]

    LICENSE_NAME_OTHER = "Other"
    license_name_items = [
        ("Redistribution_Prohibited", "Redistribution_Prohibited", "", 0),
        ("CC0", "CC0", "", 1),
        ("CC_BY", "CC_BY", "", 2),
        ("CC_BY_NC", "CC_BY_NC", "", 3),
        ("CC_BY_SA", "CC_BY_SA", "", 4),
        ("CC_BY_NC_SA", "CC_BY_NC_SA", "", 5),
        ("CC_BY_ND", "CC_BY_ND", "", 6),
        ("CC_BY_NC_ND", "CC_BY_NC_ND", "", 7),
        (LICENSE_NAME_OTHER, LICENSE_NAME_OTHER, "", 8),
    ]

    title: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Title"  # noqa: F821
    )
    version: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Version"  # noqa: F821
    )
    author: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Author"  # noqa: F821
    )
    contact_information: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Contact Information",  # noqa: F722
    )
    reference: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Reference"  # noqa: F821
    )
    allowed_user_name: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=allowed_user_name_items,
        name="Allowed User",  # noqa: F722
    )
    violent_ussage_name: bpy.props.EnumProperty(  # type: ignore[valid-type] # noqa: SC200
        items=violent_ussage_name_items,  # noqa: SC200
        name="Violent Usage",  # noqa: F722
    )
    sexual_ussage_name: bpy.props.EnumProperty(  # type: ignore[valid-type] # noqa: SC200
        items=sexual_ussage_name_items,  # noqa: SC200
        name="Sexual Usage",  # noqa: F722
    )
    commercial_ussage_name: bpy.props.EnumProperty(  # type: ignore[valid-type] # noqa: SC200
        items=commercial_ussage_name_items,  # noqa: SC200
        name="Commercial Usage",  # noqa: F722
    )
    other_permission_url: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Other Permission Url",  # noqa: F722
    )
    license_name: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=license_name_items,
        name="License",  # noqa: F821
    )
    other_license_url: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Other License Url",  # noqa: F722
    )
    texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Thumbnail", type=bpy.types.Image  # noqa: F821
    )


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_BlendShape.cs#L101-L106
class Vrm0BlendShapeMasterPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    blend_shape_groups: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="BlendShape Group", type=Vrm0BlendShapeGroupPropertyGroup  # noqa: F722
    )


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_SecondaryAnimation.cs#L69-L78
class Vrm0SecondaryAnimationPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    bone_groups: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Secondary Animation Groups",  # noqa: F722
        type=Vrm0SecondaryAnimationGroupPropertyGroup,
    )
    collider_groups: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Collider Groups",  # noqa: F722
        type=Vrm0SecondaryAnimationColliderGroupPropertyGroup,
    )


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_extensions.cs#L8-L48
class Vrm0PropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    meta: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="VRM Meta", type=Vrm0MetaPropertyGroup  # noqa: F722
    )
    humanoid: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="VRM Humanoid", type=Vrm0HumanoidPropertyGroup  # noqa: F722
    )
    first_person: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="VRM FirstPerson", type=Vrm0FirstPersonPropertyGroup  # noqa: F722
    )
    blend_shape_master: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="VRM BlendShapeMaster",  # noqa: F722
        type=Vrm0BlendShapeMasterPropertyGroup,
    )
    secondary_animation: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="VRM SecondaryAnimation",  # noqa: F722
        type=Vrm0SecondaryAnimationPropertyGroup,
    )


class VrmAddonArmatureExtensionPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    addon_version: bpy.props.IntVectorProperty(  # type: ignore[valid-type]
        size=3  # noqa: F722
    )

    vrm0: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="VRM 0.x", type=Vrm0PropertyGroup  # noqa: F722
    )

    armature_data_name: bpy.props.StringProperty()  # type: ignore[valid-type]


class VrmAddonBoneExtensionPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    uuid: bpy.props.StringProperty()  # type: ignore[valid-type]


class VrmAddonShapeKeyExtensionPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    uuid: bpy.props.StringProperty()  # type: ignore[valid-type]


class VRM_PT_vrm_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm_armature_object_property"
    bl_label = "VRM"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            context.active_object
            and context.active_object.type == "ARMATURE"
            and hasattr(context.active_object.data, "vrm_addon_extension")
            and isinstance(
                context.active_object.data.vrm_addon_extension,
                VrmAddonArmatureExtensionPropertyGroup,
            )
        )

    def draw(self, _context: bpy.types.Context) -> None:
        pass


def add_armature(
    add_armature_op: bpy.types.Operator, _context: bpy.types.Context
) -> None:
    add_armature_op.layout.operator(
        make_armature.ICYP_OT_make_armature.bl_idname,
        text="VRM Humanoid",
        icon="OUTLINER_OB_ARMATURE",
    )


def make_mesh(make_mesh_op: bpy.types.Operator, _context: bpy.types.Context) -> None:
    make_mesh_op.layout.separator()
    make_mesh_op.layout.operator(
        mesh_from_bone_envelopes.ICYP_OT_make_mesh_from_bone_envelopes.bl_idname,
        text="Mesh from selected armature",
        icon="PLUGIN",
    )
    make_mesh_op.layout.operator(
        detail_mesh_maker.ICYP_OT_detail_mesh_maker.bl_idname,
        text="(WIP)Face mesh from selected armature and bound mesh",
        icon="PLUGIN",
    )


class VRM_PT_current_selected_armature(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_current_selected_armature"
    bl_label = "Current selected armature"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.multiple_armatures_exist(context)

    def draw(self, context: bpy.types.Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        layout = self.layout
        layout.label(text=armature.name, icon="ARMATURE_DATA", translate=False)


class VRM_PT_controller(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "ICYP_PT_ui_controller"
    bl_label = "Operator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="OBJECT_DATA")

    def draw(self, context: bpy.types.Context) -> None:
        active_object = context.active_object
        mode = context.mode
        layout = self.layout
        object_type = active_object.type if active_object else None
        preferences = get_preferences(context)

        # region draw_main
        layout.operator(
            make_armature.ICYP_OT_make_armature.bl_idname,
            text=pgettext("Create VRM model"),
            icon="OUTLINER_OB_ARMATURE",
        )
        vrm_validator_prop = layout.operator(
            validation.WM_OT_vrm_validator.bl_idname,
            text=pgettext("Validate VRM model"),
            icon="VIEWZOOM",
        )
        vrm_validator_prop.show_successful_message = True
        if preferences:
            layout.prop(preferences, "export_invisibles")
            layout.prop(preferences, "export_only_selections")

        if mode == "OBJECT":
            if GlslDrawObj.draw_objs:
                layout.operator(
                    glsl_drawer.ICYP_OT_remove_draw_model.bl_idname,
                    icon="SHADING_RENDERED",
                    depress=True,
                )
            else:
                if [obj for obj in bpy.data.objects if obj.type == "LIGHT"]:
                    layout.operator(
                        glsl_drawer.ICYP_OT_draw_model.bl_idname,
                        icon="SHADING_RENDERED",
                        depress=False,
                    )
                else:
                    layout.label(text="Preview MToon")
                    layout.box().label(
                        icon="INFO",
                        text=pgettext("A light is required"),
                    )
            if object_type == "MESH":
                layout.operator(
                    helper.VRM_OT_vroid2vrc_lipsync_from_json_recipe.bl_idname,
                    icon="EXPERIMENTAL",
                )
        if mode == "EDIT_MESH":
            layout.operator(bpy.ops.mesh.symmetry_snap.idname_py(), icon="MOD_MIRROR")
        # endregion draw_main


def draw_vrm0_humanoid_layout(
    armature: bpy.types.Object,
    layout: bpy.types.UILayout,
    humanoid_props: Vrm0HumanoidPropertyGroup,
) -> None:
    migrate(armature, defer=True)
    data = armature.data

    def show_ui(parent: bpy.types.UILayout, bone_name: str, icon: str) -> None:
        props = None
        for human_bone_props in humanoid_props.human_bones:
            if human_bone_props.bone == bone_name:
                props = human_bone_props
                break
        if not props:
            return
        parent.prop_search(
            props.node, "value", data, "bones", text=bone_name, icon=icon
        )

    armature_box = layout
    armature_box.operator(
        helper.VRM_OT_save_human_bone_mappings.bl_idname, icon="EXPORT"
    )
    armature_box.operator(
        helper.VRM_OT_load_human_bone_mappings.bl_idname, icon="IMPORT"
    )

    layout.separator()
    requires_box = armature_box.box()
    requires_box.label(text="VRM Required Bones", icon="ARMATURE_DATA")
    for req in human_bone_constants.HumanBone.center_req[::-1]:
        icon = "USER"
        show_ui(requires_box, req, icon)
    row = requires_box.row()
    column = row.column()
    for req in human_bone_constants.HumanBone.right_arm_req:
        icon = "VIEW_PAN"
        show_ui(column, req, icon)
    column = row.column()
    for req in human_bone_constants.HumanBone.left_arm_req:
        icon = "VIEW_PAN"
        show_ui(column, req, icon)
    row = requires_box.row()
    column = row.column()
    for req in human_bone_constants.HumanBone.right_leg_req:
        icon = "MOD_DYNAMICPAINT"
        show_ui(column, req, icon)
    column = row.column()
    for req in human_bone_constants.HumanBone.left_leg_req:
        icon = "MOD_DYNAMICPAINT"
        show_ui(column, req, icon)
    defines_box = armature_box.box()
    defines_box.label(text="VRM Optional Bones", icon="BONE_DATA")
    row = defines_box.row()
    for defs in ["rightEye"]:
        icon = "HIDE_OFF"
        show_ui(row, defs, icon)
    for defs in ["leftEye"]:
        icon = "HIDE_OFF"
        show_ui(row, defs, icon)
    for defs in human_bone_constants.HumanBone.center_def[::-1]:
        icon = "USER"
        show_ui(defines_box, defs, icon)
    defines_box.separator()
    for defs in human_bone_constants.HumanBone.right_arm_def:
        icon = "VIEW_PAN"
        show_ui(defines_box, defs, icon)
    for defs in human_bone_constants.HumanBone.right_leg_def:
        icon = "MOD_DYNAMICPAINT"
        show_ui(defines_box, defs, icon)
    defines_box.separator()
    for defs in human_bone_constants.HumanBone.left_arm_def:
        icon = "VIEW_PAN"
        show_ui(defines_box, defs, icon)
    for defs in human_bone_constants.HumanBone.left_leg_def:
        icon = "MOD_DYNAMICPAINT"
        show_ui(defines_box, defs, icon)

    armature_box.separator()

    layout.label(text="Arm", icon="VIEW_PAN", translate=False)  # TODO: 翻訳
    layout.prop(
        humanoid_props,
        "arm_stretch",
    )
    layout.prop(humanoid_props, "upper_arm_twist")
    layout.prop(humanoid_props, "lower_arm_twist")
    layout.separator()
    layout.label(text="Leg", icon="MOD_DYNAMICPAINT")
    layout.prop(humanoid_props, "leg_stretch")
    layout.prop(humanoid_props, "upper_leg_twist")
    layout.prop(humanoid_props, "lower_leg_twist")
    layout.prop(humanoid_props, "feet_spacing")
    layout.separator()
    layout.prop(humanoid_props, "has_translation_dof")


class VRM_PT_vrm0_humanoid_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_humanoid_armature_object_property"
    bl_label = "VRM 0.x Humanoid"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            context.active_object
            and context.active_object.type == "ARMATURE"
            and hasattr(context.active_object.data, "vrm_addon_extension")
        )

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="ARMATURE_DATA")

    def draw(self, context: bpy.types.Context) -> None:
        ext = context.active_object.data.vrm_addon_extension
        if isinstance(ext, VrmAddonArmatureExtensionPropertyGroup):
            draw_vrm0_humanoid_layout(
                context.active_object, self.layout, ext.vrm0.humanoid
            )


class VRM_PT_vrm0_humanoid_ui(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_humanoid_ui"
    bl_label = "VRM 0.x Humanoid"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.armature_exists(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="USER")

    def draw(self, context: bpy.types.Context) -> None:
        armature = search.current_armature(context)
        if (
            armature
            and hasattr(armature.data, "vrm_addon_extension")
            and isinstance(
                armature.data.vrm_addon_extension,
                VrmAddonArmatureExtensionPropertyGroup,
            )
        ):
            draw_vrm0_humanoid_layout(
                armature, self.layout, armature.data.vrm_addon_extension.vrm0.humanoid
            )


def draw_vrm0_first_person_layout(
    armature: bpy.types.Object,
    context: bpy.types.Context,
    layout: bpy.types.UILayout,
    first_person_props: Vrm0FirstPersonPropertyGroup,
) -> None:
    migrate(armature, defer=True)
    blend_data = context.blend_data
    layout.prop_search(
        first_person_props.first_person_bone, "value", armature.data, "bones"
    )
    layout.prop(first_person_props, "first_person_bone_offset", icon="BONE_DATA")
    layout.prop(first_person_props, "look_at_type_name")
    box = layout.box()
    box.label(text="Mesh Annotations", icon="FULLSCREEN_EXIT")
    for mesh_annotation_index, mesh_annotation in enumerate(
        first_person_props.mesh_annotations
    ):
        row = box.row()
        row.prop_search(mesh_annotation.mesh, "value", blend_data, "meshes")
        row.prop(mesh_annotation, "first_person_flag")
        remove_mesh_annotation_op = row.operator(
            VRM_OT_remove_vrm0_first_person_mesh_annotation.bl_idname,
            text="Remove",
            icon="REMOVE",
        )
        remove_mesh_annotation_op.armature_name = armature.name
        remove_mesh_annotation_op.mesh_annotation_index = mesh_annotation_index
    add_mesh_annotation_op = box.operator(
        VRM_OT_add_vrm0_first_person_mesh_annotation.bl_idname
    )
    add_mesh_annotation_op.armature_name = armature.name
    box = layout.box()
    box.label(text="Look At Horizontal Inner", icon="FULLSCREEN_EXIT")
    box.prop(first_person_props.look_at_horizontal_inner, "curve")
    box.prop(first_person_props.look_at_horizontal_inner, "x_range")
    box.prop(first_person_props.look_at_horizontal_inner, "y_range")
    box = layout.box()
    box.label(text="Look At Horizontal Outer", icon="FULLSCREEN_ENTER")
    box.prop(first_person_props.look_at_horizontal_outer, "curve")
    box.prop(first_person_props.look_at_horizontal_outer, "x_range")
    box.prop(first_person_props.look_at_horizontal_outer, "y_range")
    box = layout.box()
    box.label(text="Look At Vertical Up", icon="ANCHOR_TOP")
    box.prop(first_person_props.look_at_vertical_up, "curve")
    box.prop(first_person_props.look_at_vertical_up, "x_range")
    box.prop(first_person_props.look_at_vertical_up, "y_range")
    box = layout.box()
    box.label(text="Look At Vertical Down", icon="ANCHOR_BOTTOM")
    box.prop(first_person_props.look_at_vertical_down, "curve")
    box.prop(first_person_props.look_at_vertical_down, "x_range")
    box.prop(first_person_props.look_at_vertical_down, "y_range")


class VRM_PT_vrm0_first_person_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_first_person_armature_object_property"
    bl_label = "VRM 0.x First Person"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            context.active_object
            and context.active_object.type == "ARMATURE"
            and hasattr(context.active_object.data, "vrm_addon_extension")
        )

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="HIDE_OFF")

    def draw(self, context: bpy.types.Context) -> None:
        ext = context.active_object.data.vrm_addon_extension
        if isinstance(ext, VrmAddonArmatureExtensionPropertyGroup):
            draw_vrm0_first_person_layout(
                context.active_object,
                context,
                self.layout,
                ext.vrm0.first_person,
            )


class VRM_PT_vrm0_first_person_ui(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_first_person_ui"
    bl_label = "VRM 0.x First Person"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.armature_exists(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="HIDE_OFF")

    def draw(self, context: bpy.types.Context) -> None:
        armature = search.current_armature(context)
        if (
            armature
            and hasattr(armature.data, "vrm_addon_extension")
            and isinstance(
                armature.data.vrm_addon_extension,
                VrmAddonArmatureExtensionPropertyGroup,
            )
        ):
            draw_vrm0_first_person_layout(
                armature,
                context,
                self.layout,
                armature.data.vrm_addon_extension.vrm0.first_person,
            )


def draw_vrm0_blend_shape_master_layout(
    armature: bpy.types.Object,
    context: bpy.types.Context,
    layout: bpy.types.UILayout,
    blend_shape_master_props: Vrm0BlendShapeMasterPropertyGroup,
) -> None:
    migrate(armature, defer=True)
    blend_data = context.blend_data
    for blend_shape_group_index, blend_shape_group_props in enumerate(
        blend_shape_master_props.blend_shape_groups
    ):
        box = layout.box()
        box.prop(blend_shape_group_props, "name")
        box.prop(blend_shape_group_props, "preset_name")

        box.prop(blend_shape_group_props, "is_binary", icon="IPO_CONSTANT")
        box.separator()
        row = box.row()
        row.alignment = "LEFT"
        row.prop(
            blend_shape_group_props,
            "show_expanded_binds",
            icon="TRIA_DOWN"
            if blend_shape_group_props.show_expanded_binds
            else "TRIA_RIGHT",
            emboss=False,
        )
        if blend_shape_group_props.show_expanded_binds:
            for bind_index, bind_props in enumerate(blend_shape_group_props.binds):
                bind_box = box.box()
                bind_box.prop_search(
                    bind_props.mesh, "value", blend_data, "meshes", text="Mesh"
                )
                if (
                    bind_props.mesh.value
                    and bind_props.mesh.value in blend_data.meshes
                    and blend_data.meshes[bind_props.mesh.value]
                    and blend_data.meshes[bind_props.mesh.value].shape_keys
                    and blend_data.meshes[bind_props.mesh.value].shape_keys.key_blocks
                    and blend_data.meshes[
                        bind_props.mesh.value
                    ].shape_keys.key_blocks.keys()
                ):
                    bind_box.prop_search(
                        bind_props,
                        "index",
                        blend_data.meshes[bind_props.mesh.value].shape_keys,
                        "key_blocks",
                        text="Shape key",
                    )
                bind_box.prop(bind_props, "weight")
                remove_blend_shape_bind_op = bind_box.operator(
                    VRM_OT_remove_vrm0_blend_shape_bind.bl_idname, icon="REMOVE"
                )
                remove_blend_shape_bind_op.armature_name = armature.name
                remove_blend_shape_bind_op.blend_shape_group_index = (
                    blend_shape_group_index
                )
                remove_blend_shape_bind_op.bind_index = bind_index
            add_blend_shape_bind_op = box.operator(
                VRM_OT_add_vrm0_blend_shape_bind.bl_idname, icon="ADD"
            )
            add_blend_shape_bind_op.armature_name = armature.name
            add_blend_shape_bind_op.blend_shape_group_index = blend_shape_group_index

        row = box.row()
        row.alignment = "LEFT"
        row.prop(
            blend_shape_group_props,
            "show_expanded_material_values",
            icon="TRIA_DOWN"
            if blend_shape_group_props.show_expanded_material_values
            else "TRIA_RIGHT",
            emboss=False,
        )
        if blend_shape_group_props.show_expanded_material_values:
            for material_value_index, material_value_props in enumerate(
                blend_shape_group_props.material_values
            ):
                material_value_box = box.box()
                material_value_box.prop_search(
                    material_value_props, "material", blend_data, "materials"
                )
                material_value_box.prop(material_value_props, "property_name")
                for (
                    target_value_index,
                    target_value_props,
                ) in enumerate(material_value_props.target_value):
                    target_value_row = material_value_box.split(align=True, factor=0.7)
                    target_value_row.prop(
                        target_value_props, "value", text=f"Value {target_value_index}"
                    )
                    remove_target_value_op = target_value_row.operator(
                        VRM_OT_remove_vrm0_material_value_bind_target_value.bl_idname,
                        text="Remove",
                        icon="REMOVE",
                    )
                    remove_target_value_op.armature_name = armature.name
                    remove_target_value_op.blend_shape_group_index = (
                        blend_shape_group_index
                    )
                    remove_target_value_op.material_value_index = material_value_index
                    remove_target_value_op.target_value_index = target_value_index
                add_target_value_op = material_value_box.operator(
                    VRM_OT_add_vrm0_material_value_bind_target_value.bl_idname,
                    icon="ADD",
                )
                add_target_value_op.armature_name = armature.name
                add_target_value_op.blend_shape_group_index = blend_shape_group_index
                add_target_value_op.material_value_index = material_value_index

                remove_material_value_op = material_value_box.operator(
                    VRM_OT_remove_vrm0_material_value_bind.bl_idname, icon="REMOVE"
                )
                remove_material_value_op.armature_name = armature.name
                remove_material_value_op.blend_shape_group_index = (
                    blend_shape_group_index
                )
                remove_material_value_op.material_value_index = material_value_index
            add_material_value_op = box.operator(
                VRM_OT_add_vrm0_material_value_bind.bl_idname, icon="ADD"
            )
            add_material_value_op.armature_name = armature.name
            add_material_value_op.blend_shape_group_index = blend_shape_group_index

        remove_blend_shape_group_op = box.operator(
            VRM_OT_remove_vrm0_blend_shape_group.bl_idname, icon="REMOVE"
        )
        remove_blend_shape_group_op.armature_name = armature.name
        remove_blend_shape_group_op.blend_shape_group_index = blend_shape_group_index
    add_blend_shape_group_op = layout.operator(
        VRM_OT_add_vrm0_blend_shape_group.bl_idname, icon="ADD"
    )
    add_blend_shape_group_op.armature_name = armature.name


class VRM_PT_vrm0_blend_shape_master_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_blend_shape_master_armature_object_property"
    bl_label = "VRM 0.x Blend Shape Proxy"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            context.active_object
            and context.active_object.type == "ARMATURE"
            and hasattr(context.active_object.data, "vrm_addon_extension")
        )

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="SHAPEKEY_DATA")

    def draw(self, context: bpy.types.Context) -> None:
        ext = context.active_object.data.vrm_addon_extension
        if isinstance(ext, VrmAddonArmatureExtensionPropertyGroup):
            draw_vrm0_blend_shape_master_layout(
                context.active_object, context, self.layout, ext.vrm0.blend_shape_master
            )


class VRM_PT_vrm0_blend_shape_master_ui(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_blend_shape_master_ui"
    bl_label = "VRM 0.x Blend Shape Proxy"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.armature_exists(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="SHAPEKEY_DATA")

    def draw(self, context: bpy.types.Context) -> None:
        armature = search.current_armature(context)
        if (
            armature
            and hasattr(armature.data, "vrm_addon_extension")
            and isinstance(
                armature.data.vrm_addon_extension,
                VrmAddonArmatureExtensionPropertyGroup,
            )
        ):
            draw_vrm0_blend_shape_master_layout(
                armature,
                context,
                self.layout,
                armature.data.vrm_addon_extension.vrm0.blend_shape_master,
            )


def draw_vrm0_secondary_animation_layout(
    armature: bpy.types.Object,
    layout: bpy.types.UILayout,
    secondary_animation: Vrm0SecondaryAnimationPropertyGroup,
) -> None:
    migrate(armature, defer=True)
    data = armature.data

    for bone_group_index, bone_group_props in enumerate(
        secondary_animation.bone_groups
    ):
        box = layout.box()
        row = box.row()
        box.prop(bone_group_props, "comment", icon="BOOKMARKS")
        box.prop(bone_group_props, "stiffiness", icon="RIGID_BODY_CONSTRAINT")
        box.prop(bone_group_props, "drag_force", icon="FORCE_DRAG")
        box.separator()
        box.prop(bone_group_props, "gravity_power", icon="OUTLINER_OB_FORCE_FIELD")
        box.prop(bone_group_props, "gravity_dir", icon="OUTLINER_OB_FORCE_FIELD")
        box.separator()
        box.prop_search(
            bone_group_props.center,
            "value",
            data,
            "bones",
            icon="PIVOT_MEDIAN",
            text="Center Bone",
        )
        box.prop(
            bone_group_props,
            "hit_radius",
            icon="MOD_PHYSICS",
        )
        box.separator()
        row = box.row()
        row.alignment = "LEFT"
        row.prop(
            bone_group_props,
            "show_expanded_bones",
            icon="TRIA_DOWN" if bone_group_props.show_expanded_bones else "TRIA_RIGHT",
            emboss=False,
        )
        if bone_group_props.show_expanded_bones:
            for bone_index, bone in enumerate(bone_group_props.bones):
                bone_row = box.split(align=True, factor=0.7)
                bone_row.prop_search(bone, "value", data, "bones", text="")
                remove_bone_op = bone_row.operator(
                    VRM_OT_remove_vrm0_secondary_animation_group_bone.bl_idname,
                    icon="REMOVE",
                    text="Remove",
                )
                remove_bone_op.armature_name = armature.name
                remove_bone_op.bone_group_index = bone_group_index
                remove_bone_op.bone_index = bone_index
            add_bone_op = box.operator(
                VRM_OT_add_vrm0_secondary_animation_group_bone.bl_idname, icon="ADD"
            )
            add_bone_op.armature_name = armature.name
            add_bone_op.bone_group_index = bone_group_index

        row = box.row()
        row.alignment = "LEFT"
        row.prop(
            bone_group_props,
            "show_expanded_collider_groups",
            icon="TRIA_DOWN"
            if bone_group_props.show_expanded_collider_groups
            else "TRIA_RIGHT",
            emboss=False,
        )
        if bone_group_props.show_expanded_collider_groups:
            for collider_group_index, collider_group in enumerate(
                bone_group_props.collider_groups
            ):
                collider_group_row = box.split(align=True, factor=0.7)
                collider_group_row.prop_search(
                    collider_group,
                    "value",
                    secondary_animation,
                    "collider_groups",
                    text="",
                )
                remove_collider_group_op = collider_group_row.operator(
                    VRM_OT_remove_vrm0_secondary_animation_group_collider_group.bl_idname,
                    icon="REMOVE",
                    text="Remove",
                )
                remove_collider_group_op.armature_name = armature.name
                remove_collider_group_op.bone_group_index = bone_group_index
                remove_collider_group_op.collider_group_index = collider_group_index
            add_collider_group_op = box.operator(
                VRM_OT_add_vrm0_secondary_animation_group_collider_group.bl_idname,
                icon="ADD",
            )
            add_collider_group_op.armature_name = armature.name
            add_collider_group_op.bone_group_index = bone_group_index

        remove_bone_group_op = box.operator(
            VRM_OT_remove_vrm0_secondary_animation_group.bl_idname, icon="REMOVE"
        )
        remove_bone_group_op.armature_name = armature.name
        remove_bone_group_op.bone_group_index = bone_group_index
    add_bone_group_op = layout.operator(
        VRM_OT_add_vrm0_secondary_animation_group.bl_idname, icon="ADD"
    )
    add_bone_group_op.armature_name = armature.name

    for collider_group_index, collider_group_props in enumerate(
        secondary_animation.collider_groups
    ):
        box = layout.box()
        row = box.row()
        box.label(text=collider_group_props.name)
        box.prop_search(collider_group_props.node, "value", armature.data, "bones")

        for collider_index, collider_props in enumerate(collider_group_props.colliders):
            collider_row = box.split(align=True, factor=0.5)
            collider_row.prop(
                collider_props.blender_object, "name", icon="MESH_UVSPHERE", text=""
            )
            collider_row.prop(
                collider_props.blender_object, "empty_display_size", text=""
            )
            remove_collider_op = collider_row.operator(
                VRM_OT_remove_vrm0_secondary_animation_collider_group_collider.bl_idname,
                icon="REMOVE",
                text="Remove",
            )
            remove_collider_op.armature_name = armature.name
            remove_collider_op.collider_group_index = collider_group_index
            remove_collider_op.collider_index = collider_index
        add_collider_op = box.operator(
            VRM_OT_add_vrm0_secondary_animation_collider_group_collider.bl_idname,
            icon="ADD",
        )
        add_collider_op.armature_name = armature.name
        add_collider_op.collider_group_index = collider_group_index
        add_collider_op.bone_name = collider_group_props.node.value

        remove_collider_group_op = box.operator(
            VRM_OT_remove_vrm0_secondary_animation_collider_group.bl_idname,
            icon="REMOVE",
        )
        remove_collider_group_op.armature_name = armature.name
        remove_collider_group_op.collider_group_index = collider_group_index
    add_collider_group_op = layout.operator(
        VRM_OT_add_vrm0_secondary_animation_collider_group.bl_idname, icon="ADD"
    )
    add_collider_group_op.armature_name = armature.name


class VRM_PT_vrm0_secondary_animation_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_secondary_animation_armature_object_property"
    bl_label = "VRM 0.x Spring Bone"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            context.active_object
            and context.active_object.type == "ARMATURE"
            and hasattr(context.active_object.data, "vrm_addon_extension")
        )

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="PHYSICS")

    def draw(self, context: bpy.types.Context) -> None:
        ext = context.active_object.data.vrm_addon_extension
        if isinstance(ext, VrmAddonArmatureExtensionPropertyGroup):
            draw_vrm0_secondary_animation_layout(
                context.active_object, self.layout, ext.vrm0.secondary_animation
            )


class VRM_PT_vrm0_secondary_animation_ui(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_secondary_animation_ui"
    bl_label = "VRM 0.x Spring Bone"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.armature_exists(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="PHYSICS")

    def draw(self, context: bpy.types.Context) -> None:
        armature = search.current_armature(context)
        if (
            armature
            and hasattr(armature.data, "vrm_addon_extension")
            and isinstance(
                armature.data.vrm_addon_extension,
                VrmAddonArmatureExtensionPropertyGroup,
            )
        ):
            draw_vrm0_secondary_animation_layout(
                armature,
                self.layout,
                armature.data.vrm_addon_extension.vrm0.secondary_animation,
            )


def draw_vrm0_meta_layout(
    armature: bpy.types.Object,
    context: bpy.types.Context,
    layout: bpy.types.UILayout,
    meta_props: Vrm0MetaPropertyGroup,
) -> None:
    migrate(armature, defer=True)
    blend_data = context.blend_data

    layout.prop_search(meta_props, "texture", blend_data, "images", text="Thumbnail")

    layout.prop(meta_props, "title", icon="FILE_BLEND")
    layout.prop(meta_props, "version", icon="LINENUMBERS_ON")
    layout.prop(meta_props, "author", icon="USER")
    layout.prop(meta_props, "contact_information", icon="URL")
    layout.prop(meta_props, "reference", icon="URL")
    layout.prop(meta_props, "allowed_user_name", icon="MATCLOTH")
    layout.prop(
        meta_props,
        "violent_ussage_name",
        icon="ORPHAN_DATA",
    )
    layout.prop(meta_props, "sexual_ussage_name", icon="HEART")
    layout.prop(
        meta_props,
        "commercial_ussage_name",
        icon="SOLO_OFF",
    )
    layout.prop(meta_props, "other_permission_url", icon="URL")
    layout.prop(meta_props, "license_name", icon="COMMUNITY")
    if meta_props.license_name == Vrm0MetaPropertyGroup.LICENSE_NAME_OTHER:
        layout.prop(meta_props, "other_license_url", icon="URL")


class VRM_PT_vrm0_meta_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_meta_armature_object_property"
    bl_label = "VRM 0.x Meta"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            context.active_object
            and context.active_object.type == "ARMATURE"
            and hasattr(context.active_object.data, "vrm_addon_extension")
        )

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="FILE_BLEND")

    def draw(self, context: bpy.types.Context) -> None:
        ext = context.active_object.data.vrm_addon_extension
        if isinstance(ext, VrmAddonArmatureExtensionPropertyGroup):
            draw_vrm0_meta_layout(
                context.active_object, context, self.layout, ext.vrm0.meta
            )


class VRM_PT_vrm0_meta_ui(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_meta_ui"
    bl_label = "VRM 0.x Meta"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.armature_exists(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="FILE_BLEND")

    def draw(self, context: bpy.types.Context) -> None:
        armature = search.current_armature(context)
        if (
            armature
            and hasattr(armature.data, "vrm_addon_extension")
            and isinstance(
                armature.data.vrm_addon_extension,
                VrmAddonArmatureExtensionPropertyGroup,
            )
        ):
            draw_vrm0_meta_layout(
                armature,
                context,
                self.layout,
                armature.data.vrm_addon_extension.vrm0.meta,
            )


class VRM_OT_add_vrm0_first_person_mesh_annotation(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm0_first_person_mesh_annotation"
    bl_label = "Add mesh annotation"
    bl_description = "Add VRM 0.x First Person Mesh Annotation"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature.data.vrm_addon_extension.vrm0.first_person.mesh_annotations.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm0_first_person_mesh_annotation(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_vrm0_first_person_mesh_annotation"
    bl_label = "Remove mesh annotation"
    bl_description = "Remove VRM 0.x First Person Mesh Annotation"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    mesh_annotation_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        mesh_annotations = (
            armature.data.vrm_addon_extension.vrm0.first_person.mesh_annotations
        )
        if len(mesh_annotations) <= self.mesh_annotation_index:
            return {"CANCELLED"}
        mesh_annotations.remove(self.mesh_annotation_index)
        return {"FINISHED"}


class VRM_OT_add_vrm0_material_value_bind(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm0_material_value_bind"
    bl_label = "Add material value bind"
    bl_description = "Add VRM 0.x BlendShape Material Value Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    blend_shape_group_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        blend_shape_groups = (
            armature.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups
        )
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        blend_shape_groups[self.blend_shape_group_index].material_values.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm0_material_value_bind(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_vrm0_material_value_bind"
    bl_label = "Remove material value bind"
    bl_description = "Remove VRM 0.x BlendShape Material Value Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    blend_shape_group_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]
    material_value_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        blend_shape_groups = (
            armature.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups
        )
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        material_values = blend_shape_groups[
            self.blend_shape_group_index
        ].material_values
        if len(material_values) <= self.material_value_index:
            return {"CANCELLED"}
        material_values.remove(self.material_value_index)
        return {"FINISHED"}


class VRM_OT_add_vrm0_material_value_bind_target_value(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm0_material_value_bind_target_value"
    bl_label = "Add value"
    bl_description = "Add VRM 0.x BlendShape Material Value Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    blend_shape_group_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]
    material_value_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        blend_shape_groups = (
            armature.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups
        )
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        material_values = blend_shape_groups[
            self.blend_shape_group_index
        ].material_values
        if len(material_values) <= self.material_value_index:
            return {"CANCELLED"}
        material_values[self.material_value_index].target_value.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm0_material_value_bind_target_value(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_vrm0_material_value_bind_target_value"
    bl_label = "Remove value"
    bl_description = "Remove VRM 0.x BlendShape Material Value Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    blend_shape_group_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]
    material_value_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]
    target_value_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        blend_shape_groups = (
            armature.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups
        )
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        material_values = blend_shape_groups[
            self.blend_shape_group_index
        ].material_values
        if len(material_values) <= self.material_value_index:
            return {"CANCELLED"}
        target_value = material_values[self.material_value_index].target_value
        if len(target_value) <= self.target_value_index:
            return {"CANCELLED"}
        target_value.remove(self.target_value_index)
        return {"FINISHED"}


class VRM_OT_add_vrm0_blend_shape_bind(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm0_blend_shape_bind"
    bl_label = "Add blendshape bind"
    bl_description = "Add VRM 0.x BlendShape Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    blend_shape_group_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        blend_shape_groups = (
            armature.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups
        )
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        blend_shape_groups[self.blend_shape_group_index].binds.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm0_blend_shape_bind(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_vrm0_blend_shape_bind"
    bl_label = "Remove blendshape bind"
    bl_description = "Remove VRM 0.x BlendShape Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    blend_shape_group_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]
    bind_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        blend_shape_groups = (
            armature.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups
        )
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        binds = blend_shape_groups[self.blend_shape_group_index].binds
        if len(binds) <= self.bind_index:
            return {"CANCELLED"}
        binds.remove(self.bind_index)
        return {"FINISHED"}


class VRM_OT_add_vrm0_secondary_animation_collider_group_collider(  # noqa: N801
    bpy.types.Operator  # type: ignore[misc]
):
    bl_idname = "vrm.add_vrm0_secondary_animation_collider_group_collider"
    bl_label = "Add collider"
    bl_description = "Add VRM 0.x Collider"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    collider_group_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]
    bone_name: bpy.props.StringProperty()  # type: ignore[valid-type]

    def execute(self, context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        collider_groups = (
            armature.data.vrm_addon_extension.vrm0.secondary_animation.collider_groups
        )
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider = collider_groups[self.collider_group_index].colliders.add()
        obj = bpy.data.objects.new(
            name=f"{self.armature_name}_{self.bone_name}_collider", object_data=None
        )
        collider.blender_object = obj
        obj.parent = armature
        obj.empty_display_type = "SPHERE"
        obj.empty_display_size = 0.25
        if self.bone_name:
            obj.parent_type = "BONE"
            obj.parent_bone = self.bone_name
        else:
            obj.parent_type = "OBJECT"
        context.scene.collection.objects.link(obj)
        return {"FINISHED"}


class VRM_OT_remove_vrm0_secondary_animation_collider_group_collider(  # noqa: N801
    bpy.types.Operator  # type: ignore[misc]
):
    bl_idname = "vrm.remove_vrm0_secondary_animation_collider_group_collider"
    bl_label = "Remove collider"
    bl_description = "Remove VRM 0.x Collider"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    collider_group_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]
    collider_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]

    def execute(self, context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        collider_groups = (
            armature.data.vrm_addon_extension.vrm0.secondary_animation.collider_groups
        )
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        colliders = collider_groups[self.collider_group_index].colliders
        if len(colliders) <= self.collider_index:
            return {"CANCELLED"}
        blender_object = colliders[self.collider_index].blender_object
        if blender_object and blender_object.name in context.scene.collection.objects:
            blender_object.parent_type = "OBJECT"
            context.scene.collection.objects.unlink(blender_object)
        colliders.remove(self.collider_index)
        return {"FINISHED"}


class VRM_OT_add_vrm0_secondary_animation_group_bone(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm0_secondary_animation_group_bone"
    bl_label = "Add bone"
    bl_description = "Add VRM 0.x Secondary Animation Group Bone"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    bone_group_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        bone_groups = (
            armature.data.vrm_addon_extension.vrm0.secondary_animation.bone_groups
        )
        if len(bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        bone_groups[self.bone_group_index].bones.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm0_secondary_animation_group_bone(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_vrm0_secondary_animation_group_bone"
    bl_label = "Remove bone"
    bl_description = "Remove VRM 0.x Secondary Animation Group Bone"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    bone_group_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]
    bone_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        bone_groups = (
            armature.data.vrm_addon_extension.vrm0.secondary_animation.bone_groups
        )
        if len(bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        bones = bone_groups[self.bone_group_index].bones
        if len(bones) <= self.bone_index:
            return {"CANCELLED"}
        bones.remove(self.bone_index)
        return {"FINISHED"}


class VRM_OT_add_vrm0_secondary_animation_group_collider_group(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm0_secondary_animation_group_collider_group"
    bl_label = "Add collider group"
    bl_description = "Add VRM 0.x Secondary Animation Group Collider Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    bone_group_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        bone_groups = (
            armature.data.vrm_addon_extension.vrm0.secondary_animation.bone_groups
        )
        if len(bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        bone_groups[self.bone_group_index].collider_groups.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm0_secondary_animation_group_collider_group(  # noqa: N801
    bpy.types.Operator  # type: ignore[misc]
):
    bl_idname = "vrm.remove_vrm0_secondary_animation_group_collider_group"
    bl_label = "Remove collider group"
    bl_description = "Remove VRM 0.x Secondary Animation Group Collider Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    bone_group_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]
    collider_group_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        bone_groups = (
            armature.data.vrm_addon_extension.vrm0.secondary_animation.bone_groups
        )
        if len(bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        collider_groups = bone_groups[self.bone_group_index].collider_groups
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_groups.remove(self.collider_group_index)
        return {"FINISHED"}


class VRM_OT_add_vrm0_blend_shape_group(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm0_blend_shape_group"
    bl_label = "Add blendshape group"
    bl_description = "Add VRM 0.x Blend Shape Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm0_blend_shape_group(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_vrm0_blend_shape_group"
    bl_label = "Remove blendshape group"
    bl_description = "Remove VRM 0.x Blend Shape Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    blend_shape_group_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        blend_shape_groups = (
            armature.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups
        )
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        blend_shape_groups.remove(self.blend_shape_group_index)
        return {"FINISHED"}


class VRM_OT_add_vrm0_secondary_animation_group(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm0_secondary_animation_group"
    bl_label = "Add spring bone"
    bl_description = "Add VRM 0.x Secondary Animation Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    blend_shape_group_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature.data.vrm_addon_extension.vrm0.secondary_animation.bone_groups.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm0_secondary_animation_group(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_vrm0_secondary_animation_group"
    bl_label = "Remove spring bone"
    bl_description = "Remove VRM 0.x Secondary Animation Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    bone_group_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        bone_groups = (
            armature.data.vrm_addon_extension.vrm0.secondary_animation.bone_groups
        )
        if len(bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        bone_groups.remove(self.bone_group_index)
        return {"FINISHED"}


class VRM_OT_add_vrm0_secondary_animation_collider_group(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm0_secondary_animation_collider_group"
    bl_label = "Add collider group"
    bl_description = "Add VRM 0.x Secondary Animation Collider Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        collider_group = (
            armature.data.vrm_addon_extension.vrm0.secondary_animation.collider_groups.add()
        )
        collider_group.uuid = uuid.uuid4().hex
        collider_group.refresh(armature)
        return {"FINISHED"}


class VRM_OT_remove_vrm0_secondary_animation_collider_group(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_vrm0_secondary_animation_collider_group"
    bl_label = "Remove collider group"
    bl_description = "Remove VRM 0.x Secondary Animation Collider Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    collider_group_index: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        collider_groups = (
            armature.data.vrm_addon_extension.vrm0.secondary_animation.collider_groups
        )
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_groups.remove(self.collider_group_index)

        for (
            bone_group
        ) in armature.data.vrm_addon_extension.vrm0.secondary_animation.bone_groups:
            bone_group.refresh(armature)
        return {"FINISHED"}
