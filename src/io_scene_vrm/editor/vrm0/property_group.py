# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import functools
from collections.abc import Sequence
from sys import float_info
from typing import TYPE_CHECKING, ClassVar, Optional

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import (
    Action,
    Armature,
    Context,
    Image,
    Material,
    Mesh,
    Object,
    PropertyGroup,
)
from mathutils import Vector

from ...common.logger import get_logger
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
    property_group_enum,
)
from ..vrm1.property_group import Vrm1HumanoidPropertyGroup

if TYPE_CHECKING:
    from ..property_group import CollectionPropertyProtocol


logger = get_logger(__name__)


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_Humanoid.cs#L70-L164
class Vrm0HumanoidBonePropertyGroup(PropertyGroup):
    bone: StringProperty(  # type: ignore[valid-type]
        name="VRM Humanoid Bone Name"
    )
    node: PointerProperty(  # type: ignore[valid-type]
        name="Bone Name",
        type=BonePropertyGroup,
    )
    use_default_values: BoolProperty(  # type: ignore[valid-type]
        name="Unity's HumanLimit.useDefaultValues",
        default=True,
    )
    min: FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        name="Unity's HumanLimit.min",
    )
    max: FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        name="Unity's HumanLimit.max",
    )
    center: FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        name="Unity's HumanLimit.center",
    )
    axis_length: FloatProperty(  # type: ignore[valid-type]
        name="Unity's HumanLimit.axisLength"
    )

    # for UI
    node_candidates: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )

    def update_node_candidates(
        self,
        armature_data: Armature,
        bpy_bone_name_to_human_bone_specification: dict[str, HumanBoneSpecification],
    ) -> None:
        human_bone_name = HumanBoneName.from_str(self.bone)
        if human_bone_name is None:
            logger.warning("Bone name '%s' is invalid", self.bone)
            return
        target = HumanBoneSpecifications.get(human_bone_name)
        new_candidates = BonePropertyGroup.find_bone_candidates(
            armature_data,
            target,
            bpy_bone_name_to_human_bone_specification,
        )
        if {n.value for n in self.node_candidates} == new_candidates:
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
            message = f'HumanBone "{self.bone}" is invalid'
            raise ValueError(message)
        return HumanBoneSpecifications.get(name)

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
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
class Vrm0HumanoidPropertyGroup(PropertyGroup):
    human_bones: CollectionProperty(  # type: ignore[valid-type]
        name="Human Bones",
        type=Vrm0HumanoidBonePropertyGroup,
    )
    arm_stretch: FloatProperty(  # type: ignore[valid-type]
        name="Arm Stretch",
        default=0.05,
    )
    leg_stretch: FloatProperty(  # type: ignore[valid-type]
        name="Leg Stretch",
        default=0.05,
    )
    upper_arm_twist: FloatProperty(  # type: ignore[valid-type]
        name="Upper Arm Twist",
        default=0.5,
    )
    lower_arm_twist: FloatProperty(  # type: ignore[valid-type]
        name="Lower Arm Twist",
        default=0.5,
    )
    upper_leg_twist: FloatProperty(  # type: ignore[valid-type]
        name="Upper Leg Twist",
        default=0.5,
    )
    lower_leg_twist: FloatProperty(  # type: ignore[valid-type]
        name="Lower Leg Twist",
        default=0.5,
    )
    feet_spacing: FloatProperty(  # type: ignore[valid-type]
        name="Feet Spacing",
        default=0,
    )
    has_translation_dof: BoolProperty(  # type: ignore[valid-type]
        name="Has Translation DoF",
        default=False,
    )

    POSE_AUTO_POSE = Vrm1HumanoidPropertyGroup.POSE_AUTO_POSE
    POSE_REST_POSITION_POSE = Vrm1HumanoidPropertyGroup.POSE_REST_POSITION_POSE
    POSE_CURRENT_POSE = Vrm1HumanoidPropertyGroup.POSE_CURRENT_POSE
    POSE_CUSTOM_POSE = Vrm1HumanoidPropertyGroup.POSE_CUSTOM_POSE

    pose: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Vrm1HumanoidPropertyGroup.pose_enum.items(),
        name="T-Pose",
        description="T-Pose",
        default=POSE_AUTO_POSE.identifier,
    )

    # for T-Pose
    def update_pose_library(self, _context: Context) -> None:
        self.pose_marker_name = ""

    pose_library: PointerProperty(  # type: ignore[valid-type]
        type=Action,
        name="Pose Library",
        description="Pose library for T Pose",
        update=update_pose_library,
    )
    pose_marker_name: StringProperty()  # type: ignore[valid-type]

    # for UI
    last_bone_names: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )
    initial_automatic_bone_assignment: BoolProperty(  # type: ignore[valid-type]
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
    def defer_update_all_node_candidates(
        armature_data_name: str,
        *,
        force: bool = False,
    ) -> None:
        bpy.app.timers.register(
            functools.partial(
                Vrm0HumanoidPropertyGroup.update_all_node_candidates_timer_callback,
                armature_data_name,
                force=force,
            )
        )

    @staticmethod
    def update_all_node_candidates_timer_callback(
        armature_object_name: str, *, force: bool = False
    ) -> None:
        """update_all_node_candidates()の型をbpy.app.timers.registerに合わせるためのラッパー."""
        context = bpy.context  # Contextはフレームを跨げないので新たに取得する
        Vrm0HumanoidPropertyGroup.update_all_node_candidates(
            context, armature_object_name, force=force
        )

    @staticmethod
    def update_all_node_candidates(
        context: Optional[Context],
        armature_data_name: str,
        *,
        force: bool = False,
    ) -> None:
        from ..extension import get_armature_extension

        if context is None:
            context = bpy.context

        armature_data = context.blend_data.armatures.get(armature_data_name)
        if not armature_data:
            return
        bones = armature_data.bones.values()
        humanoid = get_armature_extension(armature_data).vrm0.humanoid
        bone_names: list[str] = []
        for bone in sorted(bones, key=lambda b: str(b.name)):
            bone_names.append(bone.name)
            bone_names.append(bone.parent.name if bone.parent else "")

        if not force:
            up_to_date = bone_names == [str(n.value) for n in humanoid.last_bone_names]
            if up_to_date:
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
    def fixup_human_bones(obj: Object) -> None:
        from ..extension import get_armature_extension

        armature_data = obj.data
        if not isinstance(armature_data, Armature):
            return

        humanoid = get_armature_extension(armature_data).vrm0.humanoid

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
            found_bones: list[str] = []
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
            found_node_bone_names: list[str] = []
            for human_bone in humanoid.human_bones:
                if not human_bone.node.bone_name:
                    continue
                if human_bone.node.bone_name not in found_node_bone_names:
                    found_node_bone_names.append(human_bone.node.bone_name)
                    continue
                human_bone.node.set_bone_name(None)
                refresh = True
                fixup = True
                break

        if not refresh:
            return

        secondary_animation = get_armature_extension(
            armature_data
        ).vrm0.secondary_animation
        for collider_group in secondary_animation.collider_groups:
            collider_group.refresh(obj)
        for bone_group in secondary_animation.bone_groups:
            bone_group.refresh(obj)

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
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
        pose: str  # type: ignore[no-redef]
        pose_library: Optional[Action]  # type: ignore[no-redef]
        pose_marker_name: str  # type: ignore[no-redef]
        last_bone_names: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]
        initial_automatic_bone_assignment: bool  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_FirstPerson.cs#L10-L22
class Vrm0DegreeMapPropertyGroup(PropertyGroup):
    curve: FloatVectorProperty(  # type: ignore[valid-type]
        size=8,
        name="Curve",
        default=(0, 0, 0, 1, 1, 1, 1, 0),
    )
    x_range: FloatProperty(  # type: ignore[valid-type]
        name="X Range",
        default=90,
    )
    y_range: FloatProperty(  # type: ignore[valid-type]
        name="Y Range",
        default=10,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        curve: Sequence[float]  # type: ignore[no-redef]
        x_range: float  # type: ignore[no-redef]
        y_range: float  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_FirstPerson.cs#L32-L41
class Vrm0MeshAnnotationPropertyGroup(PropertyGroup):
    mesh: PointerProperty(  # type: ignore[valid-type]
        name="Mesh",
        type=MeshObjectPropertyGroup,
        description="Mesh on restrict render in the first person camera",
    )

    first_person_flag_enum, *__first_person_flags = property_group_enum(
        ("Auto", "Auto", "Auto restrict render", "NONE", 0),
        (
            "FirstPersonOnly",
            "First-Person Only",
            "(Maybe needless) Restrict render in the third person camera",
            "NONE",
            1,
        ),
        (
            "ThirdPersonOnly",
            "Third-Person Only",
            "Restrict render in the first person camera for face, hairs or hat",
            "NONE",
            2,
        ),
        ("Both", "Both", "No restrict render for body, arms or legs", "NONE", 3),
    )

    first_person_flag: EnumProperty(  # type: ignore[valid-type]
        items=first_person_flag_enum.items(),
        name="First Person Flag",
        description="Restrict render in the first person camera",
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        mesh: MeshObjectPropertyGroup  # type: ignore[no-redef]
        first_person_flag: str  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_FirstPerson.cs#L50-L91
class Vrm0FirstPersonPropertyGroup(PropertyGroup):
    first_person_bone: PointerProperty(  # type: ignore[valid-type]
        name="First Person Bone",
        type=BonePropertyGroup,
        description="Bone to follow the first person camera",
    )
    first_person_bone_offset: FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        name="First Person Bone Offset",
        description=(
            "Offset from the first person bone to follow the first person camera"
        ),
        subtype="TRANSLATION",
        unit="LENGTH",
        default=(0, 0, 0),
    )
    mesh_annotations: CollectionProperty(  # type: ignore[valid-type]
        name="Mesh Annotations",
        type=Vrm0MeshAnnotationPropertyGroup,
    )
    look_at_type_name_enum, *__look_at_types = property_group_enum(
        ("Bone", "Bone", "Use bones to eye movement", "BONE_DATA", 0),
        (
            "BlendShape",
            "Blend Shape",
            "Use blend Shapes of VRM Blend Shape Proxy to eye movement.",
            "SHAPEKEY_DATA",
            1,
        ),
    )
    look_at_type_name: EnumProperty(  # type: ignore[valid-type]
        items=look_at_type_name_enum.items(),
        name="Look At Type Name",
        description="How to eye movement",
    )
    look_at_horizontal_inner: PointerProperty(  # type: ignore[valid-type]
        type=Vrm0DegreeMapPropertyGroup,
        name="Look At Horizontal Inner",
    )
    look_at_horizontal_outer: PointerProperty(  # type: ignore[valid-type]
        type=Vrm0DegreeMapPropertyGroup,
        name="Look At Horizontal Outer",
    )
    look_at_vertical_down: PointerProperty(  # type: ignore[valid-type]
        type=Vrm0DegreeMapPropertyGroup,
        name="Look At Vertical Down",
    )
    look_at_vertical_up: PointerProperty(  # type: ignore[valid-type]
        type=Vrm0DegreeMapPropertyGroup,
        name="lookAt Vertical Up",
    )

    # for UI
    active_mesh_annotation_index: IntProperty(min=0)  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
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
        active_mesh_annotation_index: int  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_BlendShape.cs#L18-L30
class Vrm0BlendShapeBindPropertyGroup(PropertyGroup):
    mesh: PointerProperty(  # type: ignore[valid-type]
        name="Mesh",
        type=MeshObjectPropertyGroup,
    )
    index: StringProperty(  # type: ignore[valid-type]
        name="Index"
    )
    weight: FloatProperty(  # type: ignore[valid-type]
        name="Weight",
        min=0,
        default=1,
        max=1,
        subtype="FACTOR",
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        mesh: MeshObjectPropertyGroup  # type: ignore[no-redef]
        index: str  # type: ignore[no-redef]
        weight: float  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_BlendShape.cs#L9-L16
class Vrm0MaterialValueBindPropertyGroup(PropertyGroup):
    material: PointerProperty(  # type: ignore[valid-type]
        name="Material",
        type=Material,
    )

    # property_nameはEnumPropertyではなくStringPropertyを使う。
    # これは任意の値を入力できるようにする必要があるため。
    property_name: StringProperty(  # type: ignore[valid-type]
        name="Property Name"
    )

    target_value: CollectionProperty(  # type: ignore[valid-type]
        name="Target Value",
        type=FloatPropertyGroup,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        material: Optional[Material]  # type: ignore[no-redef]
        property_name: str  # type: ignore[no-redef]
        target_value: CollectionPropertyProtocol[  # type: ignore[no-redef]
            FloatPropertyGroup
        ]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_BlendShape.cs#L62-L99
class Vrm0BlendShapeGroupPropertyGroup(PropertyGroup):
    name: StringProperty(  # type: ignore[valid-type]
        name="Name",
        description="Name of the blendshape group",
    )

    preset_name_enum, (PRESET_NAME_UNKNOWN, *__preset_names) = property_group_enum(
        ("unknown", "Unknown", "", "SHAPEKEY_DATA", 0),
        ("neutral", "Neutral", "", "VIEW_ORTHO", 1),
        ("a", "A", "", "EVENT_A", 2),
        ("i", "I", "", "EVENT_I", 3),
        ("u", "U", "", "EVENT_U", 4),
        ("e", "E", "", "EVENT_E", 5),
        ("o", "O", "", "EVENT_O", 6),
        ("blink", "Blink", "", "HIDE_ON", 7),
        ("joy", "Joy", "", "HEART", 8),
        ("angry", "Angry", "", "ORPHAN_DATA", 9),
        ("sorrow", "Sorrow", "", "MOD_FLUIDSIM", 10),
        ("fun", "Fun", "", "LIGHT_SUN", 11),
        ("lookup", "Look Up", "", "ANCHOR_TOP", 12),
        ("lookdown", "Look Down", "", "ANCHOR_BOTTOM", 13),
        ("lookleft", "Look Left", "", "ANCHOR_RIGHT", 14),
        ("lookright", "Look Right", "", "ANCHOR_LEFT", 15),
        ("blink_l", "Blink_L", "", "HIDE_ON", 16),
        ("blink_r", "Blink_R", "", "HIDE_ON", 17),
    )

    preset_name: EnumProperty(  # type: ignore[valid-type]
        items=preset_name_enum.items(),
        name="Preset",
        description="Preset name in VRM avatar",
    )
    binds: CollectionProperty(  # type: ignore[valid-type]
        type=Vrm0BlendShapeBindPropertyGroup,
        name="Binds",
    )
    material_values: CollectionProperty(  # type: ignore[valid-type]
        type=Vrm0MaterialValueBindPropertyGroup,
        name="Material Values",
    )
    is_binary: BoolProperty(  # type: ignore[valid-type]
        name="Is Binary",
        description="Use binary change in the blendshape group",
    )

    # for UI
    active_bind_index: IntProperty(min=0)  # type: ignore[valid-type]
    active_material_value_index: IntProperty(min=0)  # type: ignore[valid-type]

    # アニメーション再生中はframe_change_pre/frame_change_postでしか
    # シェイプキーの値の変更ができないので、変更された値をここに保存しておく
    frame_change_post_shape_key_updates: ClassVar[dict[tuple[str, str], float]] = {}

    def get_preview(self) -> float:
        value = self.get("preview")
        if isinstance(value, (float, int)):
            return float(value)
        return 0.0

    def set_preview(self, value: object) -> None:
        context = bpy.context

        if not isinstance(value, (int, float)):
            return

        current_value = self.get("preview")
        if (
            isinstance(current_value, (int, float))
            and abs(current_value - value) < float_info.epsilon
        ):
            return

        self["preview"] = float(value)

        for bind in self.binds:
            mesh_object = context.blend_data.objects.get(bind.mesh.mesh_object_name)
            if not mesh_object or mesh_object.type != "MESH":
                continue
            mesh = mesh_object.data
            if not isinstance(mesh, Mesh):
                continue
            mesh_shape_keys = mesh.shape_keys
            if not mesh_shape_keys:
                continue
            shape_key = context.blend_data.shape_keys.get(mesh_shape_keys.name)
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

    preview: FloatProperty(  # type: ignore[valid-type]
        name="Blend Shape Proxy",
        min=0,
        max=1,
        subtype="FACTOR",
        get=get_preview,
        set=set_preview,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
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
class Vrm0SecondaryAnimationColliderPropertyGroup(PropertyGroup):
    bpy_object: PointerProperty(  # type: ignore[valid-type]
        type=Object
    )

    def refresh(self, armature: Object, bone_name: str) -> None:
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
        elif self.bpy_object.parent_type != "OBJECT":
            self.bpy_object.parent_type = "OBJECT"

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        bpy_object: Optional[Object]  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/f2d8f158297fc883aef9c3071ca68fbe46b03f45/specification/0.0/schema/vrm.secondaryanimation.collidergroup.schema.json
# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_SecondaryAnimation.cs#L21-L29
class Vrm0SecondaryAnimationColliderGroupPropertyGroup(PropertyGroup):
    node: PointerProperty(  # type: ignore[valid-type]
        name="Node",
        type=BonePropertyGroup,
    )
    # offsetとradiusはコライダー自身のデータを用いる
    colliders: CollectionProperty(  # type: ignore[valid-type]
        name="Colliders",
        type=Vrm0SecondaryAnimationColliderPropertyGroup,
    )

    def refresh(self, armature: Object) -> None:
        from ..extension import get_armature_extension

        self.name = (
            str(self.node.bone_name) if self.node and self.node.bone_name else ""
        ) + f"#{self.uuid}"
        for index, collider in reversed(
            tuple((index, collider) for index, collider in enumerate(self.colliders))
        ):
            if not collider.bpy_object or not collider.bpy_object.name:
                self.colliders.remove(index)
            else:
                collider.refresh(armature, self.node.bone_name)
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        for bone_group in get_armature_extension(
            armature_data
        ).vrm0.secondary_animation.bone_groups:
            bone_group.refresh(armature)

    # for UI
    show_expanded: BoolProperty()  # type: ignore[valid-type]

    active_collider_index: IntProperty(min=0)  # type: ignore[valid-type]

    # for reference from Vrm0SecondaryAnimationGroupPropertyGroup
    name: StringProperty()  # type: ignore[valid-type]
    uuid: StringProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        node: BonePropertyGroup  # type: ignore[no-redef]
        colliders: CollectionPropertyProtocol[  # type: ignore[no-redef]
            Vrm0SecondaryAnimationColliderPropertyGroup
        ]
        show_expanded: bool  # type: ignore[no-redef]
        active_collider_index: int  # type: ignore[no-redef]
        name: str  # type: ignore[no-redef]
        uuid: str  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_SecondaryAnimation.cs#L32-L67
class Vrm0SecondaryAnimationGroupPropertyGroup(PropertyGroup):
    comment: StringProperty(  # type: ignore[valid-type]
        name="Comment",
        description="Comment about the purpose of springs",
    )

    # typo in VRM 0.0 specification
    # https://github.com/vrm-c/vrm-specification/blob/1723a45abfb4f12ac5d3635a3f66dc45e2f93c83/specification/0.0/schema/vrm.secondaryanimation.spring.schema.json#L9-L12
    stiffiness: FloatProperty(  # type: ignore[valid-type]
        name="Stiffness",
        min=0.0,
        soft_max=4.0,
        subtype="FACTOR",
        description="Stiffness of springs",
    )

    gravity_power: FloatProperty(  # type: ignore[valid-type]
        name="Gravity Power",
        min=0.0,
        soft_max=2.0,
        subtype="FACTOR",
        description="Gravity power of springs",
    )

    def update_gravity_dir(self, _context: Context) -> None:
        gravity_dir = Vector(self.gravity_dir)
        normalized_gravity_dir = gravity_dir.normalized()
        if (gravity_dir - normalized_gravity_dir).length > 0.0001:
            self.gravity_dir = normalized_gravity_dir

    gravity_dir: FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        min=-1,
        max=1,
        subtype="XYZ",
        name="Gravity Direction",
        description="Gravity direction of springs",
        update=update_gravity_dir,
    )
    drag_force: FloatProperty(  # type: ignore[valid-type]
        name="Drag Force",
        min=0.0,
        max=1.0,
        subtype="FACTOR",
        description="Drag Force of springs",
    )
    center: PointerProperty(  # type: ignore[valid-type]
        name="Center",
        type=BonePropertyGroup,
        description="Origin of Physics simulation to stop springs on moving",
    )
    hit_radius: FloatProperty(  # type: ignore[valid-type]
        name="Hit Radius",
        min=0.0,
        soft_max=0.5,
        subtype="DISTANCE",
        description="Hit Radius of springs",
    )
    bones: CollectionProperty(  # type: ignore[valid-type]
        name="Bones",
        type=BonePropertyGroup,
        description="Bones of the spring roots",
    )
    collider_groups: CollectionProperty(  # type: ignore[valid-type]
        name="Collider Group",
        type=StringPropertyGroup,
        description="Enabled collider Groups of springs",
    )

    # for UI
    show_expanded: BoolProperty()  # type: ignore[valid-type]
    show_expanded_bones: BoolProperty(  # type: ignore[valid-type]
        name="Bones"
    )
    show_expanded_collider_groups: BoolProperty(  # type: ignore[valid-type]
        name="Collider Groups"
    )

    active_bone_index: IntProperty(min=0)  # type: ignore[valid-type]
    active_collider_group_index: IntProperty(min=0)  # type: ignore[valid-type]

    def refresh(self, armature: Object) -> None:
        from ..extension import get_armature_extension

        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        ext = get_armature_extension(armature_data)
        collider_group_uuid_to_name = {
            collider_group.uuid: collider_group.name
            for collider_group in ext.vrm0.secondary_animation.collider_groups
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
        # To regenerate, run the `uv run tools/property_typing.py` command.
        comment: str  # type: ignore[no-redef]
        stiffiness: float  # type: ignore[no-redef]
        gravity_power: float  # type: ignore[no-redef]
        gravity_dir: Sequence[float]  # type: ignore[no-redef]
        drag_force: float  # type: ignore[no-redef]
        center: BonePropertyGroup  # type: ignore[no-redef]
        hit_radius: float  # type: ignore[no-redef]
        bones: CollectionPropertyProtocol[  # type: ignore[no-redef]
            BonePropertyGroup
        ]
        collider_groups: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]
        show_expanded: bool  # type: ignore[no-redef]
        show_expanded_bones: bool  # type: ignore[no-redef]
        show_expanded_collider_groups: bool  # type: ignore[no-redef]
        active_bone_index: int  # type: ignore[no-redef]
        active_collider_group_index: int  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_Meta.cs#L33-L149
class Vrm0MetaPropertyGroup(PropertyGroup):
    allowed_user_name_enum, __allowed_user_names = property_group_enum(
        ("OnlyAuthor", "Only Author", "", "NONE", 0),
        ("ExplicitlyLicensedPerson", "Explicitly Licensed Person", "", "NONE", 1),
        ("Everyone", "Everyone", "", "NONE", 2),
    )

    violent_ussage_name_enum, __violent_ussage_names = property_group_enum(
        ("Disallow", "Disallow", "", "NONE", 0),
        ("Allow", "Allow", "", "NONE", 1),
    )

    sexual_ussage_name_enum, __sexual_ussage_names = property_group_enum(
        ("Disallow", "Disallow", "", "NONE", 0),
        ("Allow", "Allow", "", "NONE", 1),
    )

    commercial_ussage_name_enum, __commercial_ussage_names = property_group_enum(
        ("Disallow", "Disallow", "", "NONE", 0),
        ("Allow", "Allow", "", "NONE", 1),
    )

    (
        license_name_enum,
        (
            LICENSE_NAME_REDISTRIBUTION_PROHIBITED,
            LICENSE_NAME_CC0,
            LICENSE_NAME_CC_BY,
            LICENSE_NAME_CC_BY_NC,
            LICENSE_NAME_CC_BY_SA,
            LICENSE_NAME_CC_BY_NC_SA,
            LICENSE_NAME_CC_BY_ND,
            LICENSE_NAME_CC_BY_NC_ND,
            LICENSE_NAME_OTHER,
        ),
    ) = property_group_enum(
        ("Redistribution_Prohibited", "Redistribution Prohibited", "", "NONE", 0),
        ("CC0", "CC0", "", "NONE", 1),
        ("CC_BY", "CC BY", "", "NONE", 2),
        ("CC_BY_NC", "CC BY NC", "", "NONE", 3),
        ("CC_BY_SA", "CC BY SA", "", "NONE", 4),
        ("CC_BY_NC_SA", "CC BY NC SA", "", "NONE", 5),
        ("CC_BY_ND", "CC BY ND", "", "NONE", 6),  # codespell-ignore
        ("CC_BY_NC_ND", "CC BY NC ND", "", "NONE", 7),  # codespell-ignore
        ("Other", "Other", "", "NONE", 8),
    )

    title: StringProperty(  # type: ignore[valid-type]
        name="Title",
        description="Title of the avatar",
    )
    version: StringProperty(  # type: ignore[valid-type]
        name="Version",
        description="Version of the avatar",
    )
    author: StringProperty(  # type: ignore[valid-type]
        name="Author",
        description="Author of the avatar",
    )
    contact_information: StringProperty(  # type: ignore[valid-type]
        name="Contact Information",
        description="Contact Information about the avatar",
    )
    reference: StringProperty(  # type: ignore[valid-type]
        name="Reference",
        description="Referenced works about the avatar",
    )
    allowed_user_name: EnumProperty(  # type: ignore[valid-type]
        items=allowed_user_name_enum.items(),
        name="Allowed User",
        description="Allowed user of the avatar",
    )
    violent_ussage_name: EnumProperty(  # type: ignore[valid-type]
        items=violent_ussage_name_enum.items(),
        name="Violent Usage",
        description="Violent usage of the avatar",
    )
    sexual_ussage_name: EnumProperty(  # type: ignore[valid-type]
        items=sexual_ussage_name_enum.items(),
        name="Sexual Usage",
        description="Sexual Usage of the avatar",
    )
    commercial_ussage_name: EnumProperty(  # type: ignore[valid-type]
        items=commercial_ussage_name_enum.items(),
        name="Commercial Usage",
        description="Commercial Usage of the avatar",
    )
    other_permission_url: StringProperty(  # type: ignore[valid-type]
        name="Other Permission URL",
        description="URL about other permissions of the avatar",
    )
    license_name: EnumProperty(  # type: ignore[valid-type]
        items=license_name_enum.items(),
        name="License",
        description="License of the avatar",
    )
    other_license_url: StringProperty(  # type: ignore[valid-type]
        name="Other License URL",
        description="URL about other License of the avatar",
    )
    texture: PointerProperty(  # type: ignore[valid-type]
        name="Thumbnail",
        type=Image,
        description="Thumbnail of the avatar",
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        title: str  # type: ignore[no-redef]
        version: str  # type: ignore[no-redef]
        author: str  # type: ignore[no-redef]
        contact_information: str  # type: ignore[no-redef]
        reference: str  # type: ignore[no-redef]
        allowed_user_name: str  # type: ignore[no-redef]
        violent_ussage_name: str  # type: ignore[no-redef]
        sexual_ussage_name: str  # type: ignore[no-redef]
        commercial_ussage_name: str  # type: ignore[no-redef]
        other_permission_url: str  # type: ignore[no-redef]
        license_name: str  # type: ignore[no-redef]
        other_license_url: str  # type: ignore[no-redef]
        texture: Optional[Image]  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_BlendShape.cs#L101-L106
class Vrm0BlendShapeMasterPropertyGroup(PropertyGroup):
    blend_shape_groups: CollectionProperty(  # type: ignore[valid-type]
        name="Blend Shape Group",
        type=Vrm0BlendShapeGroupPropertyGroup,
    )

    # for UI
    active_blend_shape_group_index: IntProperty(min=0)  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        blend_shape_groups: CollectionPropertyProtocol[  # type: ignore[no-redef]
            Vrm0BlendShapeGroupPropertyGroup
        ]
        active_blend_shape_group_index: int  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_SecondaryAnimation.cs#L69-L78
class Vrm0SecondaryAnimationPropertyGroup(PropertyGroup):
    bone_groups: CollectionProperty(  # type: ignore[valid-type]
        name="Secondary Animation Groups",
        type=Vrm0SecondaryAnimationGroupPropertyGroup,
    )
    collider_groups: CollectionProperty(  # type: ignore[valid-type]
        name="Collider Groups",
        type=Vrm0SecondaryAnimationColliderGroupPropertyGroup,
    )

    # for UI
    show_expanded_bone_groups: BoolProperty(  # type: ignore[valid-type]
        name="Spring Bone Groups",
    )
    show_expanded_collider_groups: BoolProperty(  # type: ignore[valid-type]
        name="Collider Groups",
    )

    active_bone_group_index: IntProperty(min=0)  # type: ignore[valid-type]
    active_collider_group_index: IntProperty(min=0)  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        bone_groups: CollectionPropertyProtocol[  # type: ignore[no-redef]
            Vrm0SecondaryAnimationGroupPropertyGroup
        ]
        collider_groups: CollectionPropertyProtocol[  # type: ignore[no-redef]
            Vrm0SecondaryAnimationColliderGroupPropertyGroup
        ]
        show_expanded_bone_groups: bool  # type: ignore[no-redef]
        show_expanded_collider_groups: bool  # type: ignore[no-redef]
        active_bone_group_index: int  # type: ignore[no-redef]
        active_collider_group_index: int  # type: ignore[no-redef]


# https://github.com/vrm-c/UniVRM/blob/v0.91.1/Assets/VRM/Runtime/Format/glTF_VRM_extensions.cs#L8-L48
class Vrm0PropertyGroup(PropertyGroup):
    meta: PointerProperty(  # type: ignore[valid-type]
        name="VRM Meta",
        type=Vrm0MetaPropertyGroup,
    )
    humanoid: PointerProperty(  # type: ignore[valid-type]
        name="VRM Humanoid",
        type=Vrm0HumanoidPropertyGroup,
    )
    first_person: PointerProperty(  # type: ignore[valid-type]
        name="VRM First Person",
        type=Vrm0FirstPersonPropertyGroup,
    )
    blend_shape_master: PointerProperty(  # type: ignore[valid-type]
        name="VRM Blend Shape Master",
        type=Vrm0BlendShapeMasterPropertyGroup,
    )
    secondary_animation: PointerProperty(  # type: ignore[valid-type]
        name="VRM Secondary Animation",
        type=Vrm0SecondaryAnimationPropertyGroup,
    )
    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        meta: Vrm0MetaPropertyGroup  # type: ignore[no-redef]
        humanoid: Vrm0HumanoidPropertyGroup  # type: ignore[no-redef]
        first_person: Vrm0FirstPersonPropertyGroup  # type: ignore[no-redef]
        blend_shape_master: Vrm0BlendShapeMasterPropertyGroup  # type: ignore[no-redef]
        secondary_animation: (  # type: ignore[no-redef]
            Vrm0SecondaryAnimationPropertyGroup
        )
