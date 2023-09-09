import functools
from collections.abc import Sequence
from dataclasses import dataclass
from sys import float_info
from typing import TYPE_CHECKING, Optional

import bpy
from mathutils import Vector

from ...common.logging import get_logger
from ...common.vrm0.human_bone import (
    HumanBoneName,
    HumanBoneSpecification,
    HumanBoneSpecifications,
)
from ..property_group import (
    BonePropertyGroup,
    FloatPropertyGroup,
    MeshObjectPropertyGroup,
    StringPropertyGroup,
)

if TYPE_CHECKING:
    from ..property_group import CollectionPropertyProtocol


logger = get_logger(__name__)


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_Humanoid.cs#L70-L164
class Vrm0HumanoidBonePropertyGroup(bpy.types.PropertyGroup):
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
        bpy_bone_name_to_human_bone_specification: dict[str, HumanBoneSpecification],
    ) -> None:
        human_bone_name = HumanBoneName.from_str(self.bone)
        if human_bone_name is None:
            logger.warning(f"Bone name '{self.bone}' is invalid")
            return
        target = HumanBoneSpecifications.get(human_bone_name)
        new_candidates = BonePropertyGroup.find_bone_candidates(
            armature_data,
            target,
            bpy_bone_name_to_human_bone_specification,
        )
        if set(n.value for n in self.node_candidates) == new_candidates:
            return

        self.node_candidates.clear()
        # Preserving list order
        for bone_name in armature_data.bones.keys():
            if bone_name not in new_candidates:
                continue
            candidate = self.node_candidates.add()
            candidate.value = bone_name

    def specification(self) -> HumanBoneSpecification:
        name = HumanBoneName.from_str(self.bone)
        if name is None:
            raise ValueError(f'HumanBone "{self.bone}" is invalid')
        return HumanBoneSpecifications.get(name)

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        bone: str  # type: ignore[no-redef]
        node: BonePropertyGroup  # type: ignore[no-redef]
        use_default_values: bool  # type: ignore[no-redef]
        min: Sequence[float]  # type: ignore[no-redef]
        max: Sequence[float]  # type: ignore[no-redef]
        center: Sequence[float]  # type: ignore[no-redef]
        axis_length: float  # type: ignore[no-redef]
        node_candidates: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_Humanoid.cs#L166-L195
class Vrm0HumanoidPropertyGroup(bpy.types.PropertyGroup):
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
    feet_spacing: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Feet Spacing", default=0  # noqa: F722
    )
    has_translation_dof: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Has Translation DoF", default=False  # noqa: F722
    )

    # for T-Pose
    def update_pose_library(self, _context: bpy.types.Context) -> None:
        self.pose_marker_name = ""

    pose_library: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Action,
        name="Pose Library",  # noqa: F722
        description="Pose library for T Pose",  # noqa: F722
        update=update_pose_library,
    )
    pose_marker_name: bpy.props.StringProperty()  # type: ignore[valid-type]

    # for UI
    last_bone_names: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )
    initial_automatic_bone_assignment: bpy.props.BoolProperty(  # type: ignore[valid-type]
        default=True
    )

    def all_required_bones_are_assigned(self) -> bool:
        for name in HumanBoneSpecifications.required_names:
            for human_bone in self.human_bones:
                if human_bone.bone != name:
                    continue
                if human_bone.node.bone_name not in human_bone.node_candidates:
                    return False
        return True

    @staticmethod
    def check_last_bone_names_and_update(
        armature_data_name: str,
        defer: bool = True,
    ) -> None:
        armature_data = bpy.data.armatures.get(armature_data_name)
        if not armature_data:
            return
        bones = armature_data.bones.values()
        humanoid = armature_data.vrm_addon_extension.vrm0.humanoid
        bone_names = []
        for bone in sorted(bones, key=lambda b: str(b.name)):
            bone_names.append(bone.name)
            bone_names.append(bone.parent.name if bone.parent else "")
        up_to_date = bone_names == [str(n.value) for n in humanoid.last_bone_names]

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

        bpy_bone_name_to_human_bone_specification: dict[str, HumanBoneSpecification] = {
            human_bone.node.bone_name: HumanBoneSpecifications.get(
                HumanBoneName(human_bone.bone)
            )
            for human_bone in humanoid.human_bones
            if human_bone.node.bone_name
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
        if not isinstance(armature_data, bpy.types.Armature):
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
            found_node_bone_names = []
            for human_bone in humanoid.human_bones:
                if not human_bone.node.bone_name:
                    continue
                if human_bone.node.bone_name not in found_node_bone_names:
                    found_node_bone_names.append(human_bone.node.bone_name)
                    continue
                human_bone.node.bone_name = ""
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

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        human_bones: CollectionPropertyProtocol[  # type: ignore[no-redef]
            Vrm0HumanoidBonePropertyGroup
        ]
        arm_stretch: float  # type: ignore[no-redef]
        leg_stretch: float  # type: ignore[no-redef]
        upper_arm_twist: float  # type: ignore[no-redef]
        lower_arm_twist: float  # type: ignore[no-redef]
        upper_leg_twist: float  # type: ignore[no-redef]
        lower_leg_twist: float  # type: ignore[no-redef]
        feet_spacing: float  # type: ignore[no-redef]
        has_translation_dof: bool  # type: ignore[no-redef]
        pose_library: Optional[bpy.types.Action]  # type: ignore[no-redef]
        pose_marker_name: str  # type: ignore[no-redef]
        last_bone_names: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]
        initial_automatic_bone_assignment: bool  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_FirstPerson.cs#L10-L22
class Vrm0DegreeMapPropertyGroup(bpy.types.PropertyGroup):
    curve: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=8, name="Curve", default=(0, 0, 0, 1, 1, 1, 1, 0)  # noqa: F821
    )
    x_range: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="X Range", default=90  # noqa: F722
    )
    y_range: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Y Range", default=10  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        curve: Sequence[float]  # type: ignore[no-redef]
        x_range: float  # type: ignore[no-redef]
        y_range: float  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_FirstPerson.cs#L32-L41
class Vrm0MeshAnnotationPropertyGroup(bpy.types.PropertyGroup):
    mesh: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Mesh",  # noqa: F821
        type=MeshObjectPropertyGroup,  # noqa: F821
        description="Mesh on restrict render in the first person camera",  # noqa: F722
    )
    first_person_flag_items = [
        ("Auto", "Auto", "Auto restrict render", 0),
        (
            "FirstPersonOnly",
            "First-Person Only",
            "(Maybe needless) Restrict render in the third person camera",
            1,
        ),
        (
            "ThirdPersonOnly",
            "Third-Person Only",
            "Restrict render in the first person camera for face, hairs or hat",
            2,
        ),
        ("Both", "Both", "No restrict render for body, arms or legs", 3),
    ]
    FIRST_PERSON_FLAG_VALUES = [
        first_person_flag_item[0] for first_person_flag_item in first_person_flag_items
    ]
    first_person_flag: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=first_person_flag_items,
        name="First Person Flag",  # noqa: F722
        description="Restrict render in the first person camera",  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        mesh: MeshObjectPropertyGroup  # type: ignore[no-redef]
        first_person_flag: str  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_FirstPerson.cs#L50-L91
class Vrm0FirstPersonPropertyGroup(bpy.types.PropertyGroup):
    first_person_bone: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="First Person Bone",  # noqa: F722
        type=BonePropertyGroup,
        description="Bone to follow the first person camera",  # noqa: F722
    )
    first_person_bone_offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        name="First Person Bone Offset",  # noqa: F722
        description="Offset from the first person bone to follow the first person camera",  # noqa: F722
        subtype="TRANSLATION",  # noqa: F821
        unit="LENGTH",  # noqa: F821
        default=(0, 0, 0),
    )
    mesh_annotations: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Mesh Annotations", type=Vrm0MeshAnnotationPropertyGroup  # noqa: F722
    )
    look_at_type_name_items = [
        ("Bone", "Bone", "Use bones to eye movement", "BONE_DATA", 0),
        (
            "BlendShape",
            "Blend Shape",
            "Use blend Shapes of VRM Blend Shape Proxy to eye movement.",
            "SHAPEKEY_DATA",
            1,
        ),
    ]
    LOOK_AT_TYPE_NAME_VALUES = [
        look_at_type_name_item[0] for look_at_type_name_item in look_at_type_name_items
    ]
    look_at_type_name: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=look_at_type_name_items,
        name="Look At Type Name",  # noqa: F722
        description="How to eye movement",  # noqa: F722
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

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        first_person_bone: BonePropertyGroup  # type: ignore[no-redef]
        first_person_bone_offset: Sequence[float]  # type: ignore[no-redef]
        mesh_annotations: CollectionPropertyProtocol[  # type: ignore[no-redef]
            Vrm0MeshAnnotationPropertyGroup
        ]
        look_at_type_name: str  # type: ignore[no-redef]
        look_at_horizontal_inner: Vrm0DegreeMapPropertyGroup  # type: ignore[no-redef]
        look_at_horizontal_outer: Vrm0DegreeMapPropertyGroup  # type: ignore[no-redef]
        look_at_vertical_down: Vrm0DegreeMapPropertyGroup  # type: ignore[no-redef]
        look_at_vertical_up: Vrm0DegreeMapPropertyGroup  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_BlendShape.cs#L18-L30
class Vrm0BlendShapeBindPropertyGroup(bpy.types.PropertyGroup):
    mesh: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Mesh", type=MeshObjectPropertyGroup  # noqa: F821
    )
    index: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Index"  # noqa: F821
    )
    weight: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Weight",  # noqa: F821
        min=0,
        default=1,
        max=1,  # noqa: F821
        subtype="FACTOR",  # noqa: F821
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        mesh: MeshObjectPropertyGroup  # type: ignore[no-redef]
        index: str  # type: ignore[no-redef]
        weight: float  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_BlendShape.cs#L9-L16
class Vrm0MaterialValueBindPropertyGroup(bpy.types.PropertyGroup):
    material: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Material", type=bpy.types.Material  # noqa: F821
    )
    property_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Property Name"  # noqa: F722
    )
    target_value: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Target Value", type=FloatPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        material: Optional[bpy.types.Material]  # type: ignore[no-redef]
        property_name: str  # type: ignore[no-redef]
        target_value: CollectionPropertyProtocol[  # type: ignore[no-redef]
            FloatPropertyGroup
        ]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_BlendShape.cs#L62-L99
class Vrm0BlendShapeGroupPropertyGroup(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Name",  # noqa: F821
        description="Name of the blendshape group",  # noqa: F722
    )

    @dataclass(frozen=True)
    class Preset:
        identifier: str
        name: str
        description: str
        icon: str
        number: int
        default_blend_shape_group_name: str

    presets = [
        Preset("unknown", "Unknown", "", "SHAPEKEY_DATA", 0, "Unknown"),
        Preset("neutral", "Neutral", "", "VIEW_ORTHO", 1, "Neutral"),
        Preset("a", "A", "", "EVENT_A", 2, "A"),
        Preset("i", "I", "", "EVENT_I", 3, "I"),
        Preset("u", "U", "", "EVENT_U", 4, "U"),
        Preset("e", "E", "", "EVENT_E", 5, "E"),
        Preset("o", "O", "", "EVENT_O", 6, "O"),
        Preset("blink", "Blink", "", "HIDE_ON", 7, "Blink"),
        Preset("joy", "Joy", "", "HEART", 8, "Joy"),
        Preset("angry", "Angry", "", "ORPHAN_DATA", 9, "Angry"),
        Preset("sorrow", "Sorrow", "", "MOD_FLUIDSIM", 10, "Sorrow"),
        Preset("fun", "Fun", "", "LIGHT_SUN", 11, "Fun"),
        Preset("lookup", "Look Up", "", "ANCHOR_TOP", 12, "LookUp"),
        Preset("lookdown", "Look Down", "", "ANCHOR_BOTTOM", 13, "LookDown"),
        Preset("lookleft", "Look Left", "", "ANCHOR_RIGHT", 14, "LookLeft"),
        Preset("lookright", "Look Right", "", "ANCHOR_LEFT", 15, "LookRight"),
        Preset("blink_l", "Blink_L", "", "HIDE_ON", 16, "Blink_L"),
        Preset("blink_r", "Blink_R", "", "HIDE_ON", 17, "Blink_R"),
    ]

    preset_name_items = [
        (preset.identifier, preset.name, preset.description, preset.icon, preset.number)
        for preset in presets
    ]

    PRESET_NAME_VALUES = [preset.identifier for preset in presets]

    preset_name: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=preset_name_items,
        name="Preset",  # noqa: F821
        description="Preset name in VRM avatar",  # noqa: F722
    )
    binds: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=Vrm0BlendShapeBindPropertyGroup, name="Binds"  # noqa: F821
    )
    material_values: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=Vrm0MaterialValueBindPropertyGroup, name="Material Values"  # noqa: F722
    )
    is_binary: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Is Binary",  # noqa: F722
        description="Use binary change in the blendshape group",  # noqa: F722
    )

    # for UI
    active_bind_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="Active Bind Index", default=0  # noqa: F722
    )
    active_material_value_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="Active Material Value Index", default=0  # noqa: F722
    )

    # アニメーション再生中はframe_change_pre/frame_change_postでしかシェイプキーの値の変更ができないので、
    # 変更された値をここに保存しておく
    frame_change_post_shape_key_updates: dict[tuple[str, str], float] = {}

    def get_preview(self) -> float:
        value = self.get("preview")
        if isinstance(value, (float, int)):
            return float(value)
        return 0.0

    def set_preview(self, value: object) -> None:
        if not isinstance(value, (int, float)):
            return

        current_value = self.get("preview")
        if (
            isinstance(current_value, (int, float))
            and abs(current_value - value) < float_info.epsilon
        ):
            return

        self["preview"] = float(value)

        blend_data = bpy.data
        for bind in self.binds:
            mesh_object = blend_data.objects.get(bind.mesh.mesh_object_name)
            if not mesh_object or mesh_object.type != "MESH":
                continue
            mesh = mesh_object.data
            if not isinstance(mesh, bpy.types.Mesh):
                continue
            mesh_shape_keys = mesh.shape_keys
            if not mesh_shape_keys:
                continue
            shape_key = blend_data.shape_keys.get(mesh_shape_keys.name)
            if not shape_key:
                continue
            key_blocks = shape_key.key_blocks
            if not key_blocks:
                continue
            if bind.index not in key_blocks:
                continue
            if self.is_binary:
                preview = 1.0 if self.preview > 0.0 else 0.0
            else:
                preview = self.preview
            key_block_value = bind.weight * preview  # Lerp 0.0 * (1 - a) + weight * a
            key_blocks[bind.index].value = key_block_value
            Vrm0BlendShapeGroupPropertyGroup.frame_change_post_shape_key_updates[
                (shape_key.name, bind.index)
            ] = key_block_value

    preview: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Blend Shape Proxy",  # noqa: F722
        min=0,
        max=1,
        subtype="FACTOR",  # noqa: F821
        get=get_preview,  # noqa: F821
        set=set_preview,  # noqa: F821
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        name: str  # type: ignore[no-redef]
        preset_name: str  # type: ignore[no-redef]
        binds: CollectionPropertyProtocol[  # type: ignore[no-redef]
            Vrm0BlendShapeBindPropertyGroup
        ]
        material_values: CollectionPropertyProtocol[  # type: ignore[no-redef]
            Vrm0MaterialValueBindPropertyGroup
        ]
        is_binary: bool  # type: ignore[no-redef]
        active_bind_index: int  # type: ignore[no-redef]
        active_material_value_index: int  # type: ignore[no-redef]
        preview: float  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_SecondaryAnimation.cs#L10-L18
class Vrm0SecondaryAnimationColliderPropertyGroup(bpy.types.PropertyGroup):
    bpy_object: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Object  # noqa: F722
    )

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

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        bpy_object: Optional[bpy.types.Object]  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/f2d8f158297fc883aef9c3071ca68fbe46b03f45/specification/0.0/schema/vrm.secondaryanimation.collidergroup.schema.json
# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_SecondaryAnimation.cs#L21-L29
class Vrm0SecondaryAnimationColliderGroupPropertyGroup(bpy.types.PropertyGroup):
    node: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Node", type=BonePropertyGroup  # noqa: F821
    )
    # offsetとradiusはコライダー自身のデータを用いる
    colliders: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Colliders", type=Vrm0SecondaryAnimationColliderPropertyGroup  # noqa: F821
    )

    def refresh(self, armature: bpy.types.Object) -> None:
        self.name = (
            str(self.node.bone_name) if self.node and self.node.bone_name else ""
        ) + f"#{self.uuid}"
        for index, collider in reversed(list(enumerate(list(self.colliders)))):
            if not collider.bpy_object or not collider.bpy_object.name:
                self.colliders.remove(index)
            else:
                collider.refresh(armature, self.node.bone_name)
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return
        for (
            bone_group
        ) in armature_data.vrm_addon_extension.vrm0.secondary_animation.bone_groups:
            bone_group.refresh(armature)

    # for UI
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]

    # for reference from Vrm0SecondaryAnimationGroupPropertyGroup
    name: bpy.props.StringProperty()  # type: ignore[valid-type]
    uuid: bpy.props.StringProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        node: BonePropertyGroup  # type: ignore[no-redef]
        colliders: CollectionPropertyProtocol[  # type: ignore[no-redef]
            Vrm0SecondaryAnimationColliderPropertyGroup
        ]
        show_expanded: bool  # type: ignore[no-redef]
        name: str  # type: ignore[no-redef]
        uuid: str  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_SecondaryAnimation.cs#L32-L67
class Vrm0SecondaryAnimationGroupPropertyGroup(bpy.types.PropertyGroup):
    comment: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Comment",  # noqa: F821
        description="Comment about the purpose of the springs",  # noqa: F722
    )
    stiffiness: bpy.props.FloatProperty(  # type: ignore[valid-type] # noqa: SC200
        name="Stiffness",  # noqa: F821
        min=0.0,
        soft_max=4.0,
        subtype="FACTOR",  # noqa: F821
        description="Stiffness of the springs",  # noqa: F722
    )
    gravity_power: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Gravity Power",  # noqa: F722
        min=0.0,
        soft_max=2.0,
        subtype="FACTOR",  # noqa: F821
        description="Gravity power of the springs",  # noqa: F722
    )

    def update_gravity_dir(self, _context: bpy.types.Context) -> None:
        gravity_dir = Vector(self.gravity_dir)
        normalized_gravity_dir = gravity_dir.normalized()
        if (gravity_dir - normalized_gravity_dir).length > 0.0001:
            self.gravity_dir = normalized_gravity_dir

    gravity_dir: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        min=-1,
        max=1,
        subtype="XYZ",  # noqa: F821
        name="Gravity Direction",  # noqa: F722
        description="Gravity direction of the springs",  # noqa: F722
        update=update_gravity_dir,
    )
    drag_force: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Drag Force",  # noqa: F722
        min=0.0,
        max=1.0,
        subtype="FACTOR",  # noqa: F821
        description="Drag Force of the springs",  # noqa: F722
    )
    center: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Center",  # noqa: F821
        type=BonePropertyGroup,
        description="Origin of Physics simulation to stop the springs on moving",  # noqa: F722
    )
    hit_radius: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Hit Radius",  # noqa: F722
        min=0.0,
        soft_max=0.5,
        subtype="DISTANCE",  # noqa: F821
        description="Hit Radius of the springs",  # noqa: F722
    )
    bones: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Bones",  # noqa: F821
        type=BonePropertyGroup,
        description="Bones of the spring roots",  # noqa: F722
    )
    collider_groups: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Collider Group",  # noqa: F722
        type=StringPropertyGroup,
        description="Enabled collider Groups of the springs",  # noqa: F722
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
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return
        collider_group_uuid_to_name = {
            collider_group.uuid: collider_group.name
            for collider_group in armature_data.vrm_addon_extension.vrm0.secondary_animation.collider_groups
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

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        comment: str  # type: ignore[no-redef]
        stiffiness: float  # type: ignore[no-redef]  # noqa: SC200
        gravity_power: float  # type: ignore[no-redef]
        gravity_dir: Sequence[float]  # type: ignore[no-redef]
        drag_force: float  # type: ignore[no-redef]
        center: BonePropertyGroup  # type: ignore[no-redef]
        hit_radius: float  # type: ignore[no-redef]
        bones: CollectionPropertyProtocol[BonePropertyGroup]  # type: ignore[no-redef]
        collider_groups: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]
        show_expanded: bool  # type: ignore[no-redef]
        show_expanded_bones: bool  # type: ignore[no-redef]
        show_expanded_collider_groups: bool  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_Meta.cs#L33-L149
class Vrm0MetaPropertyGroup(bpy.types.PropertyGroup):
    allowed_user_name_items = [
        ("OnlyAuthor", "Only Author", "", 0),
        ("ExplicitlyLicensedPerson", "Explicitly Licensed Person", "", 1),
        ("Everyone", "Everyone", "", 2),
    ]
    ALLOWED_USER_NAME_VALUES = [
        allowed_user_name_item[0] for allowed_user_name_item in allowed_user_name_items
    ]

    violent_ussage_name_items = [  # noqa: SC200
        ("Disallow", "Disallow", "", 0),
        ("Allow", "Allow", "", 1),
    ]
    VIOLENT_USSAGE_NAME_VALUES = [  # noqa: SC200
        violent_ussage_name_item[0]  # noqa: SC200
        for violent_ussage_name_item in violent_ussage_name_items  # noqa: SC200
    ]

    sexual_ussage_name_items = [  # noqa: SC200
        ("Disallow", "Disallow", "", 0),
        ("Allow", "Allow", "", 1),
    ]
    SEXUAL_USSAGE_NAME_VALUES = [  # noqa: SC200
        sexual_ussage_name_item[0]  # noqa: SC200
        for sexual_ussage_name_item in sexual_ussage_name_items  # noqa: SC200
    ]

    commercial_ussage_name_items = [  # noqa: SC200
        ("Disallow", "Disallow", "", 0),
        ("Allow", "Allow", "", 1),
    ]
    COMMERCIAL_USSAGE_NAME_VALUES = [  # noqa: SC200
        commercial_ussage_name_item[0]  # noqa: SC200
        for commercial_ussage_name_item in commercial_ussage_name_items  # noqa: SC200
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
    LICENSE_NAME_VALUES = [
        license_name_item[0] for license_name_item in license_name_items
    ]

    title: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Title",  # noqa: F821
        description="Title of the avatar",  # noqa: F722
    )
    version: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Version",  # noqa: F821
        description="Version of the avatar",  # noqa: F722
    )
    author: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Author",  # noqa: F821
        description="Author of the avatar",  # noqa: F722
    )
    contact_information: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Contact Information",  # noqa: F722
        description="Contact Information about the avatar",  # noqa: F722
    )
    reference: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Reference",  # noqa: F821
        description="Referenced works about the avatar",  # noqa: F722
    )
    allowed_user_name: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=allowed_user_name_items,
        name="Allowed User",  # noqa: F722
        description="Allowed user of the avatar",  # noqa: F722
    )
    violent_ussage_name: bpy.props.EnumProperty(  # type: ignore[valid-type] # noqa: SC200
        items=violent_ussage_name_items,  # noqa: SC200
        name="Violent Usage",  # noqa: F722
        description="Violent usage of the avatar",  # noqa: F722
    )
    sexual_ussage_name: bpy.props.EnumProperty(  # type: ignore[valid-type] # noqa: SC200
        items=sexual_ussage_name_items,  # noqa: SC200
        name="Sexual Usage",  # noqa: F722
        description="Sexual Usage of the avatar",  # noqa: F722
    )
    commercial_ussage_name: bpy.props.EnumProperty(  # type: ignore[valid-type] # noqa: SC200
        items=commercial_ussage_name_items,  # noqa: SC200
        name="Commercial Usage",  # noqa: F722
        description="Commercial Usage of the avatar",  # noqa: F722
    )
    other_permission_url: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Other Permission URL",  # noqa: F722
        description="URL about other permissions of the avatar",  # noqa: F722
    )
    license_name: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=license_name_items,
        name="License",  # noqa: F821
        description="License of the avatar",  # noqa: F722
    )
    other_license_url: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Other License URL",  # noqa: F722
        description="URL about other License of the avatar",  # noqa: F722
    )
    texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Thumbnail",  # noqa: F821
        type=bpy.types.Image,
        description="Thumbnail of the avatar",  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        title: str  # type: ignore[no-redef]
        version: str  # type: ignore[no-redef]
        author: str  # type: ignore[no-redef]
        contact_information: str  # type: ignore[no-redef]
        reference: str  # type: ignore[no-redef]
        allowed_user_name: str  # type: ignore[no-redef]
        violent_ussage_name: str  # type: ignore[no-redef]  # noqa: SC200
        sexual_ussage_name: str  # type: ignore[no-redef]  # noqa: SC200
        commercial_ussage_name: str  # type: ignore[no-redef]  # noqa: SC200
        other_permission_url: str  # type: ignore[no-redef]
        license_name: str  # type: ignore[no-redef]
        other_license_url: str  # type: ignore[no-redef]
        texture: Optional[bpy.types.Image]  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_BlendShape.cs#L101-L106
class Vrm0BlendShapeMasterPropertyGroup(bpy.types.PropertyGroup):
    blend_shape_groups: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Blend Shape Group", type=Vrm0BlendShapeGroupPropertyGroup  # noqa: F722
    )

    # for UI
    active_blend_shape_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="Active Blend Shape Group Index", default=0  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        blend_shape_groups: CollectionPropertyProtocol[  # type: ignore[no-redef]
            Vrm0BlendShapeGroupPropertyGroup
        ]
        active_blend_shape_group_index: int  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_SecondaryAnimation.cs#L69-L78
class Vrm0SecondaryAnimationPropertyGroup(bpy.types.PropertyGroup):
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

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        bone_groups: CollectionPropertyProtocol[  # type: ignore[no-redef]
            Vrm0SecondaryAnimationGroupPropertyGroup
        ]
        collider_groups: CollectionPropertyProtocol[  # type: ignore[no-redef]
            Vrm0SecondaryAnimationColliderGroupPropertyGroup
        ]
        active_bone_group_index: int  # type: ignore[no-redef]
        active_collider_group_index: int  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_extensions.cs#L8-L48
class Vrm0PropertyGroup(bpy.types.PropertyGroup):
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
    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        meta: Vrm0MetaPropertyGroup  # type: ignore[no-redef]
        humanoid: Vrm0HumanoidPropertyGroup  # type: ignore[no-redef]
        first_person: Vrm0FirstPersonPropertyGroup  # type: ignore[no-redef]
        blend_shape_master: Vrm0BlendShapeMasterPropertyGroup  # type: ignore[no-redef]
        secondary_animation: Vrm0SecondaryAnimationPropertyGroup  # type: ignore[no-redef]
