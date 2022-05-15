import functools
from typing import Dict, List, Union

import bpy

from ...common.human_bone import (
    HumanBoneName,
    HumanBoneSpecification,
    HumanBoneSpecifications,
)
from ..property_group import (
    BonePropertyGroup,
    FloatPropertyGroup,
    MeshPropertyGroup,
    StringPropertyGroup,
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

    # for UI
    node_candidates: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )

    def update_node_candidates(
        self,
        armature_data: bpy.types.Armature,
        bpy_bone_name_to_human_bone_specification: Dict[str, HumanBoneSpecification],
    ) -> None:
        human_bone_name = HumanBoneName.from_str(self.bone)
        if human_bone_name is None:
            print(f"WARNING: bone name '{self.bone}' is invalid")
            return
        target = HumanBoneSpecifications.get(human_bone_name)
        new_candidates = BonePropertyGroup.find_bone_candidates(
            armature_data,
            target,
            bpy_bone_name_to_human_bone_specification,
        )
        if set(map(lambda n: n.value, self.node_candidates)) == new_candidates:
            return

        self.node_candidates.clear()
        # Preserving list order
        if armature_data.is_editmode:
            bone_names = armature_data.edit_bones.keys()
        else:
            bone_names = armature_data.bones.keys()
        for bone_name in bone_names:
            if bone_name not in new_candidates:
                continue
            candidate = self.node_candidates.add()
            candidate.value = bone_name  # for logic
            candidate.name = bone_name  # for view

    def specification(self) -> HumanBoneSpecification:
        name = HumanBoneName.from_str(self.bone)
        if name is None:
            raise Exception(f'HumanBone "{self.bone}" is invalid')
        return HumanBoneSpecifications.get(name)


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

    # for T-Pose
    pose_library: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Action, name="Pose Library", description='Pose library for T Pose'
    )
    pose_marker_name: bpy.props.StringProperty()  # type: ignore[valid-type]

    # for UI
    last_bone_names: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )
    page_items = [
        ("page1", "Page 1", "", "NONE", 0),
        ("page2", "Page 2", "", "NONE", 1)
    ]
    page: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=page_items,
        name="Page"  # noqa: F821
    )

    @staticmethod
    def check_last_bone_names_and_update(
        armature_data_name: str,
        defer: bool = True,
    ) -> None:
        armature_data = bpy.data.armatures.get(armature_data_name)
        if not armature_data:
            return
        bones: Union[List[bpy.types.Bone], List[bpy.types.EditBone]] = []
        if armature_data.is_editmode:
            bones = armature_data.edit_bones.values()
        else:
            bones = armature_data.bones.values()
        humanoid = armature_data.vrm_addon_extension.vrm0.humanoid
        bone_names = []
        for bone in sorted(bones, key=lambda b: str(b.name)):
            bone_names.append(bone.name)
            bone_names.append(bone.parent.name if bone.parent else "")
        up_to_date = bone_names == list(
            map(lambda n: str(n.value), humanoid.last_bone_names)
        )

        if up_to_date:
            return

        if defer:
            bpy.app.timers.register(
                functools.partial(
                    Vrm0HumanoidPropertyGroup.check_last_bone_names_and_update,
                    armature_data_name,
                    False,
                )
            )
            return

        humanoid.last_bone_names.clear()
        for bone_name in bone_names:
            last_bone_name = humanoid.last_bone_names.add()
            last_bone_name.value = bone_name

        bpy_bone_name_to_human_bone_specification: Dict[str, HumanBoneSpecification] = {
            human_bone.node.value: HumanBoneSpecifications.get(
                HumanBoneName(human_bone.bone)
            )
            for human_bone in humanoid.human_bones
            if human_bone.node.value
            and HumanBoneName.from_str(human_bone.bone) is not None
        }

        for human_bone in humanoid.human_bones:
            human_bone.update_node_candidates(
                armature_data,
                bpy_bone_name_to_human_bone_specification,
            )

    @staticmethod
    def fixup_human_bones(obj: bpy.types.Object) -> None:
        armature_data = obj.data
        if (
            obj.type != "ARMATURE"
            or not isinstance(armature_data, bpy.types.Armature)
            or not hasattr(armature_data, "vrm_addon_extension")
        ):
            return

        humanoid = armature_data.vrm_addon_extension.vrm0.humanoid

        # 存在していないボーンマップを追加
        refresh = False
        for human_bone_name in HumanBoneSpecifications.all_names:
            if any(
                human_bone.bone == human_bone_name
                for human_bone in humanoid.human_bones
            ):
                continue
            human_bone = humanoid.human_bones.add()
            human_bone.bone = human_bone_name
            refresh = True

        # 二重に入っているボーンマップを削除
        fixup = True
        while fixup:
            fixup = False
            found_bones = []
            for i, human_bone in enumerate(list(humanoid.human_bones)):
                if (
                    human_bone.bone in HumanBoneSpecifications.all_names
                    and human_bone.bone not in found_bones
                ):
                    found_bones.append(human_bone.bone)
                    continue
                humanoid.human_bones.remove(i)
                refresh = True
                fixup = True
                break

        # 複数のボーンマップに同一のBlenderのボーンが設定されていたら片方を削除
        fixup = True
        while fixup:
            fixup = False
            found_node_values = []
            for human_bone in humanoid.human_bones:
                if not human_bone.node.value:
                    continue
                if human_bone.node.value not in found_node_values:
                    found_node_values.append(human_bone.node.value)
                    continue
                human_bone.node.value = ""
                refresh = True
                fixup = True
                break

        if not refresh:
            return

        secondary_animation = armature_data.vrm_addon_extension.vrm0.secondary_animation
        for collider_group in secondary_animation.collider_groups:
            collider_group.refresh(obj)
        for bone_group in secondary_animation.bone_groups:
            bone_group.refresh(obj)


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
        name="Mesh", type=MeshPropertyGroup,
        description='Mesh on restrict render in the first person camera'  # noqa: F821
    )
    first_person_flag_items = [
        ("Auto", "Auto", "Auto restrict render", 0),
        ("FirstPersonOnly", "First-Person Only", "(Maybe needless) Restrict render in the third person camera", 1),
        ("ThirdPersonOnly", "Third-Person Only", "Restrict render in the first person camera for face, hairs or hat", 2),
        ("Both", "Both", "No restrict render for body, arms or legs", 3),
    ]
    first_person_flag: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=first_person_flag_items, name="First Person Flag",
        description='Restrict render in the first person camera'  # noqa: F722
    )


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_FirstPerson.cs#L50-L91
class Vrm0FirstPersonPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    first_person_bone: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="First Person Bone", type=BonePropertyGroup,
        description='Bone to follow the first person camera'  # noqa: F722
    )
    first_person_bone_offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        name="First Person Bone Offset",
        description='Offset from the first person bone to follow the first person camera',  # noqa: F722
        subtype="TRANSLATION",  # noqa: F821
        unit="LENGTH",  # noqa: F821
        default=(0, 0, 0),
    )
    mesh_annotations: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Mesh Annotations", type=Vrm0MeshAnnotationPropertyGroup  # noqa: F722
    )
    look_at_type_name_items = [
        ("Bone", "Bone", "Use bones to eye movement", "BONE_DATA", 0),
        ("BlendShape", "Blend Shape", "Use blend Shapes of VRM Blend Shape Proxy to eye movement.", "SHAPEKEY_DATA", 1),
    ]
    look_at_type_name: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=look_at_type_name_items, name="Look At Type Name",
        description='How to eye movement'  # noqa: F722
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

    # For UI
    page_items = [
        ("page1", "Page 1", "", "NONE", 0),
        ("page2", "Page 2", "", "NONE", 1)
    ]
    page: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=page_items,
        name="Page"  # noqa: F821
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
        name="Weight", min=0, max=1,
        subtype="FACTOR"  # noqa: F821
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
        name="Name",
        description='Name of the blendshape group'  # noqa: F821
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
        items=preset_name_items, name="Preset",
        description='Preset name in VRM avatar'  # noqa: F821
    )
    binds: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=Vrm0BlendShapeBindPropertyGroup, name="Binds"  # noqa: F821
    )
    material_values: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=Vrm0MaterialValueBindPropertyGroup, name="Material Values"  # noqa: F722
    )
    is_binary: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Is Binary",
        description='Use binary change in the blendshape group'  # noqa: F722
    )

    # for UI
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]
    show_expanded_binds: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Binds"  # noqa: F821
    )
    show_expanded_material_values: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Material Values"  # noqa: F722
    )
    active_bind_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="Active Bind Index", default=0  # noqa: F722
    )
    active_material_value_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="Active Material Value Index", default=0  # noqa: F722
    )

    def update_preview(self, context):
        for bind in self.binds:
            if bind.mesh.link_to_mesh is None:
                continue
            if bind.mesh.link_to_mesh.parent is None:
                continue
            if bind.mesh.link_to_mesh.parent.data is None:
                continue
            mesh = bind.mesh.link_to_mesh.parent.data
            index = bind.index
            weight = bind.weight
            ret = weight * self.preview # Lerp 0.0 * (1 - a) + weight * a
            mesh.shape_keys.key_blocks[index].value = ret

    preview: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Preview", min=0, max=1,
        subtype="FACTOR",
        update=update_preview  # noqa: F821
    )



# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_SecondaryAnimation.cs#L10-L18
class Vrm0SecondaryAnimationColliderPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    blender_object: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Object  # noqa: F722
    )

    def refresh(self, armature: bpy.types.Object, bone_name: str) -> None:
        if not self.blender_object or not self.blender_object.name:
            return

        if self.blender_object.parent != armature:
            self.blender_object.parent = armature
        if self.blender_object.empty_display_type != "SPHERE":
            self.blender_object.empty_display_type = "SPHERE"

        if bone_name:
            if self.blender_object.parent_type != "BONE":
                self.blender_object.parent_type = "BONE"
            if self.blender_object.parent_bone != bone_name:
                self.blender_object.parent_bone = bone_name
        else:
            if self.blender_object.parent_type != "OBJECT":
                self.blender_object.parent_type = "OBJECT"


# https://github.com/vrm-c/vrm-specification/blob/f2d8f158297fc883aef9c3071ca68fbe46b03f45/specification/0.0/schema/vrm.secondaryanimation.collidergroup.schema.json
# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_SecondaryAnimation.cs#L21-L29
class Vrm0SecondaryAnimationColliderGroupPropertyGroup(
    bpy.types.PropertyGroup  # type: ignore[misc]
):
    node: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Node", type=BonePropertyGroup  # noqa: F821
    )
    # offsetとradiusはコライダー自身のデータを用いる
    colliders: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Colliders", type=Vrm0SecondaryAnimationColliderPropertyGroup  # noqa: F821
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

    # for UI
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]

    # for reference from Vrm0SecondaryAnimationGroupPropertyGroup
    name: bpy.props.StringProperty()  # type: ignore[valid-type]
    uuid: bpy.props.StringProperty()  # type: ignore[valid-type]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_SecondaryAnimation.cs#L32-L67
class Vrm0SecondaryAnimationGroupPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    comment: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Comment",
        description='Comment about the purpose of the springs'  # noqa: F821
    )
    stiffiness: bpy.props.FloatProperty(  # type: ignore[valid-type] # noqa: SC200
        name="Stiffness", min=0.0, max=4.0, subtype='FACTOR',
        description='Stiffness of the springs'  # noqa: F821
    )
    gravity_power: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Gravity Power", min=0.0, max=2.0, subtype='FACTOR',
        description='Gravity power of the springs'  # noqa: F722
    )
    gravity_dir: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3, name="Gravity Direction",
        subtype='XYZ',
        description='Gravity direction of the springs'  # noqa: F722
    )
    drag_force: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Drag Force", min=0.0, max=1.0, subtype='FACTOR',
        description='Drag Force of the springs'  # noqa: F722
    )
    center: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Center", type=BonePropertyGroup,
        description='Origin of Physics simulation to stop the springs on moving'  # noqa: F821
    )
    hit_radius: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Hit Radius", min=0.0, max=0.5, subtype='DISTANCE',
        description='Hit Radius of the springs'  # noqa: F722
    )
    bones: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Bones", type=BonePropertyGroup,
        description='Bones of the spring roots'  # noqa: F821
    )
    collider_groups: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Collider Group",  
        type=StringPropertyGroup,
        description='Enabled collider Groups of the springs'  # noqa: F722
    )

    # for UI
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]
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
            if not uuid_str:
                self.collider_groups.remove(index)
                continue

            name = collider_group_uuid_to_name.get(uuid_str)
            if not name:
                self.collider_groups.remove(index)
                continue

            collider_group.value = name


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_Meta.cs#L33-L149
class Vrm0MetaPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc] # noqa: N801
    allowed_user_name_items = [
        ("OnlyAuthor", "Only Author", "", 0),
        ("ExplicitlyLicensedPerson", "Explicitly Licensed Person", "", 1),
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
        ("Redistribution_Prohibited", "Redistribution Prohibited", "", 0),
        ("CC0", "CC0", "", 1),
        ("CC_BY", "CC BY", "", 2),
        ("CC_BY_NC", "CC BY NC", "", 3),
        ("CC_BY_SA", "CC BY SA", "", 4),
        ("CC_BY_NC_SA", "CC BY NC SA", "", 5),
        ("CC_BY_ND", "CC BY ND", "", 6),
        ("CC_BY_NC_ND", "CC BY NC ND", "", 7),
        (LICENSE_NAME_OTHER, "Other", "", 8),
    ]

    title: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Title",
        description='Title of the avatar'  # noqa: F821
    )
    version: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Version",
        description='Version of the avatar'  # noqa: F821
    )
    author: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Author",
        description='Author of the avatar'  # noqa: F821
    )
    contact_information: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Contact Information",
        description='Contact Information about the avatar'  # noqa: F722
    )
    reference: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Reference",
        description='Referenced works about the avatar'  # noqa: F821
    )
    allowed_user_name: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=allowed_user_name_items,
        name="Allowed User",
        description='Allowed user of the avatar'  # noqa: F722
    )
    violent_ussage_name: bpy.props.EnumProperty(  # type: ignore[valid-type] # noqa: SC200
        items=violent_ussage_name_items,  # noqa: SC200
        name="Violent Usage",
        description='Violent usage of the avatar'  # noqa: F722
    )
    sexual_ussage_name: bpy.props.EnumProperty(  # type: ignore[valid-type] # noqa: SC200
        items=sexual_ussage_name_items,  # noqa: SC200
        name="Sexual Usage",
        description='Sexual Usage of the avatar'  # noqa: F722
    )
    commercial_ussage_name: bpy.props.EnumProperty(  # type: ignore[valid-type] # noqa: SC200
        items=commercial_ussage_name_items,  # noqa: SC200
        name="Commercial Usage",
        description='Commercial Usage of the avatar'  # noqa: F722
    )
    other_permission_url: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Other Permission URL",
        description='URL about other permissions of the avatar'  # noqa: F722
    )
    license_name: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=license_name_items,
        name="License",
        description='License of the avatar'  # noqa: F821
    )
    other_license_url: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Other License URL",
        description='URL about other License of the avatar'  # noqa: F722
    )
    texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Thumbnail", type=bpy.types.Image,
        description='Thumbnail of the avatar'  # noqa: F821
    )


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_BlendShape.cs#L101-L106
class Vrm0BlendShapeMasterPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    blend_shape_groups: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Blend Shape Group", type=Vrm0BlendShapeGroupPropertyGroup  # noqa: F722
    )

    # for UI
    active_blend_shape_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="Active Blend Shape Group Index", default=0  # noqa: F722
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

    # for UI    
    active_bone_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="Active Bone Group Index", default=0  # noqa: F722
    )
    active_collider_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="Active Collider Group Index", default=0  # noqa: F722
    )
    page_items = [
        ("page1", "Page 1", "", "NONE", 0),
        ("page2", "Page 2", "", "NONE", 1)
    ]
    page: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=page_items,
        name="Page"  # noqa: F821
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
        name="VRM First Person", type=Vrm0FirstPersonPropertyGroup  # noqa: F722
    )
    blend_shape_master: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="VRM Blend Shape Master",  # noqa: F722
        type=Vrm0BlendShapeMasterPropertyGroup,
    )
    secondary_animation: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="VRM Secondary Animation",  # noqa: F722
        type=Vrm0SecondaryAnimationPropertyGroup,
    )
