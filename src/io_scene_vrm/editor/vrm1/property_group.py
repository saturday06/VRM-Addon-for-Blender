# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import functools
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from sys import float_info
from typing import TYPE_CHECKING, ClassVar, Optional

import bpy
from bpy.app.translations import pgettext
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
from mathutils import Matrix, Quaternion, Vector

from ...common.char import DISABLE_TRANSLATION
from ...common.logger import get_logger
from ...common.rotation import set_rotation_without_mode_change
from ...common.vrm1.human_bone import (
    HumanBoneName,
    HumanBoneSpecification,
    HumanBoneSpecifications,
)
from ..property_group import (
    BonePropertyGroup,
    MaterialPropertyGroup,
    MeshObjectPropertyGroup,
    StringPropertyGroup,
    property_group_enum,
)

if TYPE_CHECKING:
    from ..property_group import CollectionPropertyProtocol


logger = get_logger(__name__)


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.humanoid.humanBones.humanBone.schema.json
class Vrm1HumanBonePropertyGroup(PropertyGroup):
    node: PointerProperty(  # type: ignore[valid-type]
        type=BonePropertyGroup
    )

    # for UI
    node_candidates: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )

    def update_node_candidates(
        self,
        armature_data: Armature,
        target: HumanBoneSpecification,
        bpy_bone_name_to_human_bone_specification: dict[str, HumanBoneSpecification],
    ) -> None:
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

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        node: BonePropertyGroup  # type: ignore[no-redef]
        node_candidates: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.humanoid.humanBones.schema.json
class Vrm1HumanBonesPropertyGroup(PropertyGroup):
    hips: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    spine: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    chest: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    upper_chest: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    neck: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    head: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_eye: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_eye: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    jaw: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_upper_leg: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_lower_leg: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_foot: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_toes: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_upper_leg: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_lower_leg: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_foot: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_toes: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_shoulder: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_upper_arm: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_lower_arm: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_hand: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_shoulder: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_upper_arm: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_lower_arm: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_hand: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_thumb_metacarpal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_thumb_proximal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_thumb_distal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_index_proximal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_index_intermediate: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_index_distal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_middle_proximal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_middle_intermediate: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_middle_distal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_ring_proximal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_ring_intermediate: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_ring_distal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_little_proximal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_little_intermediate: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    left_little_distal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_thumb_metacarpal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_thumb_proximal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_thumb_distal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_index_proximal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_index_intermediate: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_index_distal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_middle_proximal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_middle_intermediate: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_middle_distal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_ring_proximal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_ring_intermediate: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_ring_distal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_little_proximal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_little_intermediate: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )
    right_little_distal: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanBonePropertyGroup
    )

    # for UI
    last_bone_names: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )
    initial_automatic_bone_assignment: BoolProperty(  # type: ignore[valid-type]
        default=True
    )

    allow_non_humanoid_rig: BoolProperty(  # type: ignore[valid-type]
        name="Allow Non-Humanoid Rig",
    )

    def human_bone_name_to_human_bone(
        self,
    ) -> dict[HumanBoneName, Vrm1HumanBonePropertyGroup]:
        return {
            HumanBoneName.HIPS: self.hips,
            HumanBoneName.SPINE: self.spine,
            HumanBoneName.CHEST: self.chest,
            HumanBoneName.UPPER_CHEST: self.upper_chest,
            HumanBoneName.NECK: self.neck,
            HumanBoneName.HEAD: self.head,
            HumanBoneName.LEFT_EYE: self.left_eye,
            HumanBoneName.RIGHT_EYE: self.right_eye,
            HumanBoneName.JAW: self.jaw,
            HumanBoneName.LEFT_UPPER_LEG: self.left_upper_leg,
            HumanBoneName.LEFT_LOWER_LEG: self.left_lower_leg,
            HumanBoneName.LEFT_FOOT: self.left_foot,
            HumanBoneName.LEFT_TOES: self.left_toes,
            HumanBoneName.RIGHT_UPPER_LEG: self.right_upper_leg,
            HumanBoneName.RIGHT_LOWER_LEG: self.right_lower_leg,
            HumanBoneName.RIGHT_FOOT: self.right_foot,
            HumanBoneName.RIGHT_TOES: self.right_toes,
            HumanBoneName.LEFT_SHOULDER: self.left_shoulder,
            HumanBoneName.LEFT_UPPER_ARM: self.left_upper_arm,
            HumanBoneName.LEFT_LOWER_ARM: self.left_lower_arm,
            HumanBoneName.LEFT_HAND: self.left_hand,
            HumanBoneName.RIGHT_SHOULDER: self.right_shoulder,
            HumanBoneName.RIGHT_UPPER_ARM: self.right_upper_arm,
            HumanBoneName.RIGHT_LOWER_ARM: self.right_lower_arm,
            HumanBoneName.RIGHT_HAND: self.right_hand,
            HumanBoneName.LEFT_THUMB_METACARPAL: self.left_thumb_metacarpal,
            HumanBoneName.LEFT_THUMB_PROXIMAL: self.left_thumb_proximal,
            HumanBoneName.LEFT_THUMB_DISTAL: self.left_thumb_distal,
            HumanBoneName.LEFT_INDEX_PROXIMAL: self.left_index_proximal,
            HumanBoneName.LEFT_INDEX_INTERMEDIATE: self.left_index_intermediate,
            HumanBoneName.LEFT_INDEX_DISTAL: self.left_index_distal,
            HumanBoneName.LEFT_MIDDLE_PROXIMAL: self.left_middle_proximal,
            HumanBoneName.LEFT_MIDDLE_INTERMEDIATE: self.left_middle_intermediate,
            HumanBoneName.LEFT_MIDDLE_DISTAL: self.left_middle_distal,
            HumanBoneName.LEFT_RING_PROXIMAL: self.left_ring_proximal,
            HumanBoneName.LEFT_RING_INTERMEDIATE: self.left_ring_intermediate,
            HumanBoneName.LEFT_RING_DISTAL: self.left_ring_distal,
            HumanBoneName.LEFT_LITTLE_PROXIMAL: self.left_little_proximal,
            HumanBoneName.LEFT_LITTLE_INTERMEDIATE: self.left_little_intermediate,
            HumanBoneName.LEFT_LITTLE_DISTAL: self.left_little_distal,
            HumanBoneName.RIGHT_THUMB_METACARPAL: self.right_thumb_metacarpal,
            HumanBoneName.RIGHT_THUMB_PROXIMAL: self.right_thumb_proximal,
            HumanBoneName.RIGHT_THUMB_DISTAL: self.right_thumb_distal,
            HumanBoneName.RIGHT_INDEX_PROXIMAL: self.right_index_proximal,
            HumanBoneName.RIGHT_INDEX_INTERMEDIATE: self.right_index_intermediate,
            HumanBoneName.RIGHT_INDEX_DISTAL: self.right_index_distal,
            HumanBoneName.RIGHT_MIDDLE_PROXIMAL: self.right_middle_proximal,
            HumanBoneName.RIGHT_MIDDLE_INTERMEDIATE: self.right_middle_intermediate,
            HumanBoneName.RIGHT_MIDDLE_DISTAL: self.right_middle_distal,
            HumanBoneName.RIGHT_RING_PROXIMAL: self.right_ring_proximal,
            HumanBoneName.RIGHT_RING_INTERMEDIATE: self.right_ring_intermediate,
            HumanBoneName.RIGHT_RING_DISTAL: self.right_ring_distal,
            HumanBoneName.RIGHT_LITTLE_PROXIMAL: self.right_little_proximal,
            HumanBoneName.RIGHT_LITTLE_INTERMEDIATE: self.right_little_intermediate,
            HumanBoneName.RIGHT_LITTLE_DISTAL: self.right_little_distal,
        }

    def error_messages(self) -> list[str]:
        messages: list[str] = []
        human_bone_name_to_human_bone = self.human_bone_name_to_human_bone()

        for name, human_bone in human_bone_name_to_human_bone.items():
            specification = HumanBoneSpecifications.get(name)
            if not human_bone.node.bone_name:
                if specification.requirement:
                    messages.append(
                        pgettext('Please assign Required VRM Bone "{name}".').format(
                            name=specification.title
                        )
                    )
                continue
            if not specification.parent_requirement:
                continue
            if not specification.parent_name:
                logger.error("No parent for '%s' in spec", name)
                continue
            parent = human_bone_name_to_human_bone.get(specification.parent_name)
            if not parent:
                logger.error("No parent for '%s' in dict", name)
                continue
            parent_specification = specification.parent()
            if not parent_specification:
                logger.error("No parent specification for '%s'", name)
                continue
            if not parent.node.bone_name:
                messages.append(
                    pgettext(
                        'Please assign "{parent_name}"'
                        + ' because "{name}" requires it as its child bone.'
                    ).format(
                        name=specification.title,
                        parent_name=parent_specification.title,
                    )
                )

        return messages

    def all_required_bones_are_assigned(self) -> bool:
        return len(self.error_messages()) == 0

    @staticmethod
    def fixup_human_bones(obj: Object) -> None:
        armature_data = obj.data
        if (
            obj.type != "ARMATURE"
            or not isinstance(armature_data, Armature)
            or not hasattr(armature_data, "vrm_addon_extension")
        ):
            return

        human_bones = get_armature_vrm1_extension(armature_data).humanoid.human_bones

        # 複数のボーンマップに同一のBlenderのボーンが設定されていたら片方を削除
        fixup = True
        while fixup:
            fixup = False
            found_node_bone_names: list[str] = []
            for human_bone in human_bones.human_bone_name_to_human_bone().values():
                if not human_bone.node.bone_name:
                    continue
                if human_bone.node.bone_name not in found_node_bone_names:
                    found_node_bone_names.append(human_bone.node.bone_name)
                    continue
                human_bone.node.set_bone_name(None)
                fixup = True
                break

    @staticmethod
    def defer_update_all_node_candidates(
        armature_data_name: str,
        *,
        force: bool = False,
    ) -> None:
        bpy.app.timers.register(
            functools.partial(
                Vrm1HumanBonesPropertyGroup.update_all_node_candidates_timer_callback,
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
        Vrm1HumanBonesPropertyGroup.update_all_node_candidates(
            context, armature_object_name, force=force
        )

    @staticmethod
    def update_all_node_candidates(
        context: Optional[Context],
        armature_data_name: str,
        *,
        force: bool = False,
    ) -> None:
        if context is None:
            context = bpy.context
        armature_data = context.blend_data.armatures.get(armature_data_name)
        if not isinstance(armature_data, Armature):
            return
        human_bones = get_armature_vrm1_extension(armature_data).humanoid.human_bones
        bone_names: list[str] = []
        for bone in sorted(armature_data.bones.values(), key=lambda b: str(b.name)):
            bone_names.append(bone.name)
            bone_names.append(bone.parent.name if bone.parent else "")

        if not force:
            up_to_date = bone_names == [
                str(n.value) for n in human_bones.last_bone_names
            ]
            if up_to_date:
                return

        human_bones.last_bone_names.clear()
        for bone_name in bone_names:
            last_bone_name = human_bones.last_bone_names.add()
            last_bone_name.value = bone_name

        human_bone_name_to_human_bone = human_bones.human_bone_name_to_human_bone()
        bpy_bone_name_to_human_bone_specification: dict[str, HumanBoneSpecification] = {
            human_bone.node.bone_name: HumanBoneSpecifications.get(human_bone_name)
            for human_bone_name, human_bone in human_bone_name_to_human_bone.items()
            if human_bone.node.bone_name
        }

        for (
            human_bone_name,
            human_bone,
        ) in human_bone_name_to_human_bone.items():
            human_bone.update_node_candidates(
                armature_data,
                HumanBoneSpecifications.get(human_bone_name),
                bpy_bone_name_to_human_bone_specification,
            )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        hips: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        spine: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        chest: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        upper_chest: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        neck: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        head: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_eye: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_eye: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        jaw: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_upper_leg: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_lower_leg: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_foot: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_toes: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_upper_leg: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_lower_leg: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_foot: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_toes: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_shoulder: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_upper_arm: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_lower_arm: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_hand: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_shoulder: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_upper_arm: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_lower_arm: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_hand: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_thumb_metacarpal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_thumb_proximal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_thumb_distal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_index_proximal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_index_intermediate: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_index_distal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_middle_proximal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_middle_intermediate: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_middle_distal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_ring_proximal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_ring_intermediate: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_ring_distal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_little_proximal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_little_intermediate: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        left_little_distal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_thumb_metacarpal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_thumb_proximal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_thumb_distal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_index_proximal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_index_intermediate: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_index_distal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_middle_proximal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_middle_intermediate: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_middle_distal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_ring_proximal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_ring_intermediate: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_ring_distal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_little_proximal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_little_intermediate: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        right_little_distal: Vrm1HumanBonePropertyGroup  # type: ignore[no-redef]
        last_bone_names: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]
        initial_automatic_bone_assignment: bool  # type: ignore[no-redef]
        allow_non_humanoid_rig: bool  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.humanoid.schema.json
class Vrm1HumanoidPropertyGroup(PropertyGroup):
    human_bones: PointerProperty(type=Vrm1HumanBonesPropertyGroup)  # type: ignore[valid-type]

    # for T-Pose
    def update_pose_library(self, _context: Context) -> None:
        self.pose_marker_name = ""

    (
        pose_enum,
        (
            POSE_AUTO_POSE,
            POSE_REST_POSITION_POSE,
            POSE_CURRENT_POSE,
            POSE_CUSTOM_POSE,
        ),
    ) = property_group_enum(
        (
            "autoPose",
            "Auto",
            "Auto Pose",
            "ARMATURE_DATA",
            3,
        ),
        (
            "restPositionPose",
            "Rest Position",
            "Rest Position Pose",
            "ARMATURE_DATA",
            0,
        ),
        (
            "currentPose",
            "Current Pose",
            "Current Pose",
            "ARMATURE_DATA",
            1,
        ),
        (
            "customPose",
            "Custom Pose",
            "Custom Pose",
            "ARMATURE_DATA",
            2,
        ),
    )

    pose: EnumProperty(  # type: ignore[valid-type]
        items=pose_enum.items(),
        name="T-Pose",
        description="T-Pose",
        default=POSE_AUTO_POSE.identifier,
    )

    pose_library: PointerProperty(  # type: ignore[valid-type]
        type=Action,
        update=update_pose_library,
    )
    pose_marker_name: StringProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        human_bones: Vrm1HumanBonesPropertyGroup  # type: ignore[no-redef]
        pose: str  # type: ignore[no-redef]
        pose_library: Optional[Action]  # type: ignore[no-redef]
        pose_marker_name: str  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.lookAt.rangeMap.schema.json
class Vrm1LookAtRangeMapPropertyGroup(PropertyGroup):
    input_max_value: FloatProperty(  # type: ignore[valid-type]
        name="Input Max Value",
        min=0.0001,  # https://github.com/pixiv/three-vrm/issues/1197#issuecomment-1498492002
        default=90.0,
        max=180.0,
    )
    output_scale: FloatProperty(  # type: ignore[valid-type]
        name="Output Scale",
        default=10.0,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        input_max_value: float  # type: ignore[no-redef]
        output_scale: float  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.lookAt.schema.json
class Vrm1LookAtPropertyGroup(PropertyGroup):
    offset_from_head_bone: FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset From Head Bone",
        size=3,
        subtype="TRANSLATION",
        unit="LENGTH",
        default=(0, 0, 0),
    )

    (
        type_enum,
        (
            TYPE_BONE,
            TYPE_EXPRESSION,
        ),
    ) = property_group_enum(
        ("bone", "Bone", "Bone", "BONE_DATA", 0),
        (
            "expression",
            "Expression" + DISABLE_TRANSLATION,
            "Expression",
            "SHAPEKEY_DATA",
            1,
        ),
    )

    type: EnumProperty(  # type: ignore[valid-type]
        name="Type",
        items=type_enum.items(),
    )

    range_map_horizontal_inner: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1LookAtRangeMapPropertyGroup,
    )
    range_map_horizontal_outer: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1LookAtRangeMapPropertyGroup,
    )
    range_map_vertical_down: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1LookAtRangeMapPropertyGroup,
    )
    range_map_vertical_up: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1LookAtRangeMapPropertyGroup,
    )

    enable_preview: BoolProperty(  # type: ignore[valid-type]
        name="Enable Preview",
    )
    preview_target_bpy_object: PointerProperty(  # type: ignore[valid-type]
        type=Object,
        name="Preview Target",
    )
    previous_preview_target_bpy_object_location: FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
    )

    @staticmethod
    def update_all_previews(context: Context) -> None:
        for armature_object in context.blend_data.objects:
            if armature_object.type != "ARMATURE":
                continue
            armature_data = armature_object.data
            if not isinstance(armature_data, Armature):
                continue
            look_at = get_armature_vrm1_extension(armature_data).look_at
            look_at.update_preview(context, armature_object, armature_data)

    def update_preview(
        self,
        _context: Context,
        armature_object: Object,
        armature_data: Armature,
    ) -> None:
        vrm1 = get_armature_vrm1_extension(armature_data)
        preview_target_bpy_object = self.preview_target_bpy_object
        if not preview_target_bpy_object:
            return
        to_translation = preview_target_bpy_object.matrix_world.to_translation()
        if (
            Vector(self.previous_preview_target_bpy_object_location) - to_translation
        ).length_squared < float_info.epsilon:
            return
        self.previous_preview_target_bpy_object_location = to_translation
        head_bone_name = vrm1.humanoid.human_bones.head.node.bone_name
        head_pose_bone = armature_object.pose.bones.get(head_bone_name)
        if not head_pose_bone:
            return

        # TODO: Honor t-pose action
        rest_head_bone_matrix = (
            armature_object.matrix_world
            @ head_pose_bone.bone.convert_local_to_pose(
                Matrix(),
                head_pose_bone.bone.matrix_local,
            )
        )
        rest_head_bone_inverted_rotation = (
            rest_head_bone_matrix.to_quaternion().inverted()
        )

        head_parent_pose_bone = head_pose_bone.parent
        if not head_parent_pose_bone:
            return

        head_bone_without_rotation_matrix = (
            armature_object.matrix_world
            @ head_pose_bone.bone.convert_local_to_pose(
                Matrix(),
                head_pose_bone.bone.matrix_local,
                parent_matrix=head_parent_pose_bone.matrix,
                parent_matrix_local=head_parent_pose_bone.bone.matrix_local,
            )
        )

        local_target_translation = (
            head_bone_without_rotation_matrix
        ).inverted_safe() @ to_translation - Vector(self.offset_from_head_bone)
        forward_vector = rest_head_bone_inverted_rotation @ Vector((0, -1, 0))
        right_vector = rest_head_bone_inverted_rotation @ Vector((-1, 0, 0))
        up_vector = rest_head_bone_inverted_rotation @ Vector((0, 0, 1))

        # logger.warning(f"local_target_translation={dump(local_target_translation)}")
        # logger.warning(f"forward={dump(forward_vector)}")
        # logger.warning(f"right={dump(right_vector)}")
        # logger.warning(f"up={dump(up_vector)}")

        forward_length = local_target_translation.dot(forward_vector)
        right_length = local_target_translation.dot(right_vector)
        up_length = local_target_translation.dot(up_vector)

        # https://github.com/vrm-c/vrm-specification/blob/0861a66eb2f2b76835322d775678047d616536b3/specification/VRMC_vrm-1.0/lookAt.md?plain=1#L180
        if abs(forward_length) < float_info.epsilon:
            return

        yaw_degrees = math.degrees(math.atan2(right_length, forward_length))
        pitch_degrees = math.degrees(
            math.atan2(
                up_length,
                math.sqrt(math.pow(right_length, 2) + math.pow(forward_length, 2)),
            )
        )
        if vrm1.look_at.type == vrm1.look_at.TYPE_BONE.identifier:
            self.apply_eye_bone_preview(
                vrm1,
                yaw_degrees,
                pitch_degrees,
                armature_object,
                HumanBoneName.RIGHT_EYE,
            )
            self.apply_eye_bone_preview(
                vrm1,
                yaw_degrees,
                pitch_degrees,
                armature_object,
                HumanBoneName.LEFT_EYE,
            )
        elif vrm1.look_at.type == vrm1.look_at.TYPE_EXPRESSION.identifier:
            self.apply_expression_preview(vrm1, yaw_degrees, pitch_degrees)

    # https://github.com/vrm-c/vrm-specification/blob/0861a66eb2f2b76835322d775678047d616536b3/specification/VRMC_vrm-1.0/lookAt.md?plain=1#L230
    def apply_eye_bone_preview(
        self,
        vrm1: "Vrm1PropertyGroup",
        yaw_degrees: float,
        pitch_degrees: float,
        armature_object: Object,
        human_bone_name: HumanBoneName,
    ) -> None:
        if human_bone_name == HumanBoneName.RIGHT_EYE:
            range_map_horizontal_right = vrm1.look_at.range_map_horizontal_outer
            range_map_horizontal_left = vrm1.look_at.range_map_horizontal_inner
            pose_bone = armature_object.pose.bones.get(
                vrm1.humanoid.human_bones.right_eye.node.bone_name
            )
        elif human_bone_name == HumanBoneName.LEFT_EYE:
            range_map_horizontal_right = vrm1.look_at.range_map_horizontal_inner
            range_map_horizontal_left = vrm1.look_at.range_map_horizontal_outer
            pose_bone = armature_object.pose.bones.get(
                vrm1.humanoid.human_bones.left_eye.node.bone_name
            )
        else:
            return

        range_map_vertical_up = vrm1.look_at.range_map_vertical_up
        range_map_vertical_down = vrm1.look_at.range_map_vertical_down

        if not pose_bone:
            return

        parent_pose_bone = pose_bone.parent
        if not parent_pose_bone:
            return

        if yaw_degrees < 0:
            yaw_degrees = (
                -min(abs(yaw_degrees), range_map_horizontal_left.input_max_value)
                / range_map_horizontal_left.input_max_value
                * range_map_horizontal_left.output_scale
            )
        else:
            yaw_degrees = (
                min(abs(yaw_degrees), range_map_horizontal_right.input_max_value)
                / range_map_horizontal_right.input_max_value
                * range_map_horizontal_right.output_scale
            )

        if pitch_degrees < 0:
            # down
            pitch_degrees = (
                -min(abs(pitch_degrees), range_map_vertical_down.input_max_value)
                / range_map_vertical_down.input_max_value
                * range_map_vertical_down.output_scale
            )
        else:
            # up
            pitch_degrees = (
                min(abs(pitch_degrees), range_map_vertical_up.input_max_value)
                / range_map_vertical_up.input_max_value
                * range_map_vertical_up.output_scale
            )

        # TODO: Honor t-pose action
        rest_bone_matrix = (
            armature_object.matrix_world
            @ pose_bone.bone.convert_local_to_pose(
                Matrix(),
                pose_bone.bone.matrix_local,
            )
        )
        reset_bone_inverted_rotation = rest_bone_matrix.to_quaternion().inverted()

        forward_vector = reset_bone_inverted_rotation @ Vector((0, -1, 0))
        right_vector = reset_bone_inverted_rotation @ Vector((-1, 0, 0))
        up_vector = reset_bone_inverted_rotation @ Vector((0, 0, 1))

        # logger.warning(f"{yaw_degrees=} {pitch_degrees=}")
        # logger.warning(f"forward={dump(forward_vector)}")
        # logger.warning(f"right={dump(right_vector)}")
        # logger.warning(f"up={dump(up_vector)}")

        rotation = Quaternion(
            forward_vector.cross(right_vector), math.radians(yaw_degrees)
        ) @ Quaternion(forward_vector.cross(up_vector), math.radians(pitch_degrees))
        # logger.warning(f"rotation={dump(rotation)}")

        set_rotation_without_mode_change(pose_bone, rotation)

    # https://github.com/vrm-c/vrm-specification/blob/0861a66eb2f2b76835322d775678047d616536b3/specification/VRMC_vrm-1.0/lookAt.md?plain=1#L258
    def apply_expression_preview(
        self,
        vrm1: "Vrm1PropertyGroup",
        yaw_degrees: float,
        pitch_degrees: float,
    ) -> None:
        range_map_horizontal_outer = vrm1.look_at.range_map_horizontal_outer
        range_map_vertical_up = vrm1.look_at.range_map_vertical_up
        range_map_vertical_down = vrm1.look_at.range_map_vertical_down
        look_left = vrm1.expressions.preset.look_left
        look_right = vrm1.expressions.preset.look_right
        look_up = vrm1.expressions.preset.look_up
        look_down = vrm1.expressions.preset.look_down
        # horizontal
        if yaw_degrees < 0:
            # left
            yaw_weight = (
                min(abs(yaw_degrees), range_map_horizontal_outer.input_max_value)
                / range_map_horizontal_outer.input_max_value
                * range_map_horizontal_outer.output_scale
            )
            look_left.preview = yaw_weight
            look_right.preview = 0
        else:
            # right
            yaw_weight = (
                min(yaw_degrees, range_map_horizontal_outer.input_max_value)
                / range_map_horizontal_outer.input_max_value
                * range_map_horizontal_outer.output_scale
            )
            look_left.preview = 0
            look_right.preview = yaw_weight

        # vertical
        if pitch_degrees < 0:
            # down
            pitch_weight = (
                min(abs(pitch_degrees), range_map_vertical_down.input_max_value)
                / range_map_vertical_down.input_max_value
                * range_map_vertical_down.output_scale
            )
            look_down.preview = pitch_weight
            look_up.preview = 0
        else:
            # up
            pitch_weight = (
                min(pitch_degrees, range_map_vertical_up.input_max_value)
                / range_map_vertical_up.input_max_value
                * range_map_vertical_up.output_scale
            )
            look_down.preview = 0
            look_up.preview = pitch_weight

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        offset_from_head_bone: Sequence[float]  # type: ignore[no-redef]
        type: str  # type: ignore[no-redef]
        range_map_horizontal_inner: (  # type: ignore[no-redef]
            Vrm1LookAtRangeMapPropertyGroup
        )
        range_map_horizontal_outer: (  # type: ignore[no-redef]
            Vrm1LookAtRangeMapPropertyGroup
        )
        range_map_vertical_down: (  # type: ignore[no-redef]
            Vrm1LookAtRangeMapPropertyGroup
        )
        range_map_vertical_up: Vrm1LookAtRangeMapPropertyGroup  # type: ignore[no-redef]
        enable_preview: bool  # type: ignore[no-redef]
        preview_target_bpy_object: Optional[Object]  # type: ignore[no-redef]
        previous_preview_target_bpy_object_location: (  # type: ignore[no-redef]
            Sequence[float]
        )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.firstPerson.meshAnnotation.schema.json
class Vrm1MeshAnnotationPropertyGroup(PropertyGroup):
    node: PointerProperty(  # type: ignore[valid-type]
        type=MeshObjectPropertyGroup
    )
    type_enum, __types = property_group_enum(
        ("auto", "Auto", "", "NONE", 0),
        ("both", "Both", "", "NONE", 1),
        ("thirdPersonOnly", "Third-Person Only", "", "NONE", 2),
        ("firstPersonOnly", "First-Person Only", "", "NONE", 3),
    )
    type: EnumProperty(  # type: ignore[valid-type]
        items=type_enum.items(),
        name="First Person Type",
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        node: MeshObjectPropertyGroup  # type: ignore[no-redef]
        type: str  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.firstPerson.schema.json
class Vrm1FirstPersonPropertyGroup(PropertyGroup):
    mesh_annotations: CollectionProperty(  # type: ignore[valid-type]
        name="Mesh Annotations",
        type=Vrm1MeshAnnotationPropertyGroup,
    )

    # for UI
    active_mesh_annotation_index: IntProperty(min=0)  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        mesh_annotations: CollectionPropertyProtocol[  # type: ignore[no-redef]
            Vrm1MeshAnnotationPropertyGroup
        ]
        active_mesh_annotation_index: int  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.expressions.expression.morphTargetBind.schema.json
class Vrm1MorphTargetBindPropertyGroup(PropertyGroup):
    node: PointerProperty(  # type: ignore[valid-type]
        type=MeshObjectPropertyGroup
    )
    index: StringProperty(  # type: ignore[valid-type]
    )
    weight: FloatProperty(  # type: ignore[valid-type]
        min=0,
        default=1,
        max=1,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        node: MeshObjectPropertyGroup  # type: ignore[no-redef]
        index: str  # type: ignore[no-redef]
        weight: float  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.expressions.expression.materialColorBind.schema.json
class Vrm1MaterialColorBindPropertyGroup(PropertyGroup):
    material: PointerProperty(  # type: ignore[valid-type]
        name="Material",
        type=Material,
    )

    type_enum, __types = property_group_enum(
        ("color", "Color", "", "NONE", 0),
        ("emissionColor", "Emission Color", "", "NONE", 1),
        ("shadeColor", "Shade Color", "", "NONE", 2),
        ("matcapColor", "Matcap Color", "", "NONE", 5),
        ("rimColor", "Rim Color", "", "NONE", 3),
        ("outlineColor", "Outline Color", "", "NONE", 4),
    )
    type: EnumProperty(  # type: ignore[valid-type]
        name="Type",
        items=type_enum.items(),
    )
    target_value: FloatVectorProperty(  # type: ignore[valid-type]
        name="Target Value",
        size=4,
        subtype="COLOR",
        min=0,
        max=1,  # TODO: hdr emission color?
    )

    def get_target_value_as_rgb(self) -> tuple[float, float, float]:
        return (
            self.target_value[0],
            self.target_value[1],
            self.target_value[2],
        )

    def set_target_value_as_rgb(self, value: Sequence[float]) -> None:
        if len(value) < 3:
            return
        self.target_value = (
            value[0],
            value[1],
            value[2],
            self.target_value[3],
        )

    target_value_as_rgb: FloatVectorProperty(  # type: ignore[valid-type]
        name="Target Value",
        size=3,
        subtype="COLOR",
        get=get_target_value_as_rgb,
        set=set_target_value_as_rgb,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        material: Optional[Material]  # type: ignore[no-redef]
        type: str  # type: ignore[no-redef]
        target_value: Sequence[float]  # type: ignore[no-redef]
        target_value_as_rgb: Sequence[float]  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.expressions.expression.textureTransformBind.schema.json
class Vrm1TextureTransformBindPropertyGroup(PropertyGroup):
    material: PointerProperty(  # type: ignore[valid-type]
        name="Material",
        type=Material,
    )
    scale: FloatVectorProperty(  # type: ignore[valid-type]
        size=2,
        default=(1, 1),
    )
    offset: FloatVectorProperty(  # type: ignore[valid-type]
        size=2,
        default=(0, 0),
    )
    show_experimental_preview_feature: BoolProperty(  # type: ignore[valid-type]
        name="[Experimental] Show Preview Feature"
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        material: Optional[Material]  # type: ignore[no-redef]
        scale: Sequence[float]  # type: ignore[no-redef]
        offset: Sequence[float]  # type: ignore[no-redef]
        show_experimental_preview_feature: bool  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.expressions.expression.schema.json
class Vrm1ExpressionPropertyGroup(PropertyGroup):
    morph_target_binds: CollectionProperty(  # type: ignore[valid-type]
        type=Vrm1MorphTargetBindPropertyGroup
    )
    material_color_binds: CollectionProperty(  # type: ignore[valid-type]
        type=Vrm1MaterialColorBindPropertyGroup
    )
    texture_transform_binds: CollectionProperty(  # type: ignore[valid-type]
        type=Vrm1TextureTransformBindPropertyGroup
    )
    is_binary: BoolProperty(  # type: ignore[valid-type]
        name="Is Binary"
    )
    materials_to_update: CollectionProperty(  # type: ignore[valid-type]
        type=MaterialPropertyGroup, options={"HIDDEN"}
    )

    expression_override_type_enum, __expression_override_types = property_group_enum(
        ("none", "None", "", "NONE", 0),
        ("block", "Block", "", "NONE", 1),
        ("blend", "Blend", "", "NONE", 2),
    )

    def update_preview(self, context: Context) -> None:
        self.update_previews(self, context)

    @staticmethod
    def update_previews(
        triggered_expression: "Vrm1ExpressionPropertyGroup",
        context: Context,
    ) -> None:
        if not triggered_expression.name:
            logger.debug("Unnamed expression: %s", type(triggered_expression))
            return

        armature: Optional[Armature] = None
        for search_armature in context.blend_data.armatures:
            ext = get_armature_vrm1_extension(search_armature)
            if (
                triggered_expression
                == ext.expressions.all_name_to_expression_dict().get(
                    triggered_expression.name
                )
            ):
                armature = search_armature
                break

        if not armature:  # This is getting triggered after importing VRMA files
            logger.error("No armature for %s", triggered_expression.name)
            return

        expressions = get_armature_vrm1_extension(armature).expressions
        name_to_expression_dict = expressions.all_name_to_expression_dict()

        mouth_block_rate = 0.0
        blink_block_rate = 0.0
        look_at_block_rate = 0.0
        for expression in name_to_expression_dict.values():
            if expression.preview < float_info.epsilon:
                continue

            if expression.override_mouth == "blend":
                mouth_block_rate += expression.preview
            if expression.override_blink == "blend":
                blink_block_rate += expression.preview
            if expression.override_look_at == "blend":
                look_at_block_rate += expression.preview

            if expression.override_mouth == "block":
                mouth_block_rate = 1.0
            if expression.override_blink == "block":
                blink_block_rate = 1.0
            if expression.override_look_at == "block":
                look_at_block_rate = 1.0

        mouth_blend_factor = max(0, min(1 - mouth_block_rate, 1))
        blink_blend_factor = max(0, min(1 - blink_block_rate, 1))
        look_at_blend_factor = max(0, min(1 - look_at_block_rate, 1))

        shape_key_name_and_key_block_name_to_value: dict[tuple[str, str], float] = {}
        for name, expression in name_to_expression_dict.items():
            if expression.is_binary:
                preview = 0.0 if expression.preview < float_info.epsilon else 1.0
            else:
                preview = expression.preview

            if expressions.preset.is_mouth_expression(name):
                preview *= mouth_blend_factor
            elif expressions.preset.is_blink_expression(name):
                preview *= blink_blend_factor
            elif expressions.preset.is_look_at_expression(name):
                preview *= look_at_blend_factor

            for texture_transform_bind in expression.texture_transform_binds:
                material = texture_transform_bind.material
                if not material:
                    continue

            for material_color_bind in expression.material_color_binds:
                material = material_color_bind.material
                if not material:
                    continue

            for morph_target_bind in expression.morph_target_binds:
                mesh_object = context.blend_data.objects.get(
                    morph_target_bind.node.mesh_object_name
                )
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
                key_block = key_blocks.get(morph_target_bind.index)
                if not key_block:
                    continue

                value = morph_target_bind.weight * preview
                shape_key_name_and_key_block_name = (shape_key.name, key_block.name)
                shape_key_name_and_key_block_name_to_value[
                    shape_key_name_and_key_block_name
                ] = (
                    shape_key_name_and_key_block_name_to_value.get(
                        shape_key_name_and_key_block_name, 0.0
                    )
                    + value
                )

        for (
            shape_key_name,
            key_block_name,
        ), value in shape_key_name_and_key_block_name_to_value.items():
            shape_key = context.blend_data.shape_keys.get(shape_key_name)
            if not shape_key:
                continue
            key_blocks = shape_key.key_blocks
            if not key_blocks:
                continue
            key_block = key_blocks.get(key_block_name)
            if not key_block:
                continue
            key_block.value = value

        Vrm1ExpressionPropertyGroup.frame_change_post_shape_key_updates.update(
            shape_key_name_and_key_block_name_to_value
        )

    override_blink: EnumProperty(  # type: ignore[valid-type]
        name="Override Blink",
        items=expression_override_type_enum.items(),
        update=update_preview,
    )
    override_look_at: EnumProperty(  # type: ignore[valid-type]
        name="Override Look At",
        items=expression_override_type_enum.items(),
        update=update_preview,
    )
    override_mouth: EnumProperty(  # type: ignore[valid-type]
        name="Override Mouth",
        items=expression_override_type_enum.items(),
        update=update_preview,
    )

    # for UI
    show_expanded: BoolProperty()  # type: ignore[valid-type]
    show_expanded_morph_target_binds: BoolProperty(  # type: ignore[valid-type]
        name="Morph Target Binds"
    )
    show_expanded_material_color_binds: BoolProperty(  # type: ignore[valid-type]
        name="Material Color Binds"
    )
    show_expanded_texture_transform_binds: BoolProperty(  # type: ignore[valid-type]
        name="Texture Transform Binds"
    )

    # アニメーション再生中はframe_change_pre/frame_change_postでしかシェイプキーの値の
    # 変更ができないので、変更された値をここに保存しておく
    frame_change_post_shape_key_updates: ClassVar[dict[tuple[str, str], float]] = {}

    def get_preview(self) -> float:
        value = self.get("preview")
        if isinstance(value, (float, int)):
            return float(value)
        return 0.0

    def find_armature(self, context: Context) -> Armature:
        for armature in context.blend_data.armatures:
            ext = get_armature_vrm1_extension(armature)
            ext.expressions.all_name_to_expression_dict()

        message = f"No armature extension for {self.name}"
        raise ValueError(message)

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
        Vrm1ExpressionPropertyGroup.update_preview(self, context)

    preview: FloatProperty(  # type: ignore[valid-type]
        name="Expression",
        min=0,
        max=1,
        subtype="FACTOR",
        get=get_preview,
        set=set_preview,
    )

    @classmethod
    def update_materials(cls, context: Context) -> None:
        for armature in context.blend_data.armatures:
            ext = get_armature_vrm1_extension(armature)
            expressions = ext.expressions
            for expression in expressions.all_name_to_expression_dict().values():
                for material_property_group in expression.materials_to_update:
                    material = material_property_group.material
                    if not material:
                        continue
                    node_tree = material.node_tree
                    if not node_tree:
                        continue

                    # update()メソッドはドキュメントには存在するが、呼び出し失敗する
                    # https://docs.blender.org/api/4.2/bpy.types.NodeTree.html#bpy.types.NodeTree.update
                    # node_tree.update()
                expression.materials_to_update.clear()

    active_morph_target_bind_index: IntProperty(min=0)  # type: ignore[valid-type]
    active_material_color_bind_index: IntProperty(min=0)  # type: ignore[valid-type]
    active_texture_transform_bind_index: IntProperty(min=0)  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        morph_target_binds: CollectionPropertyProtocol[  # type: ignore[no-redef]
            Vrm1MorphTargetBindPropertyGroup
        ]
        material_color_binds: CollectionPropertyProtocol[  # type: ignore[no-redef]
            Vrm1MaterialColorBindPropertyGroup
        ]
        texture_transform_binds: CollectionPropertyProtocol[  # type: ignore[no-redef]
            Vrm1TextureTransformBindPropertyGroup
        ]
        is_binary: bool  # type: ignore[no-redef]
        materials_to_update: CollectionPropertyProtocol[  # type: ignore[no-redef]
            MaterialPropertyGroup
        ]
        override_blink: str  # type: ignore[no-redef]
        override_look_at: str  # type: ignore[no-redef]
        override_mouth: str  # type: ignore[no-redef]
        show_expanded: bool  # type: ignore[no-redef]
        show_expanded_morph_target_binds: bool  # type: ignore[no-redef]
        show_expanded_material_color_binds: bool  # type: ignore[no-redef]
        show_expanded_texture_transform_binds: bool  # type: ignore[no-redef]
        preview: float  # type: ignore[no-redef]
        active_morph_target_bind_index: int  # type: ignore[no-redef]
        active_material_color_bind_index: int  # type: ignore[no-redef]
        active_texture_transform_bind_index: int  # type: ignore[no-redef]


class Vrm1CustomExpressionPropertyGroup(Vrm1ExpressionPropertyGroup):
    def get_custom_name(self) -> str:
        return str(self.get("custom_name", ""))

    def set_custom_name(self, value: str) -> None:
        context = bpy.context

        if not value or self.get("custom_name") == value:
            return

        vrm1: Optional[Vrm1PropertyGroup] = None
        for search_armature in context.blend_data.armatures:
            for custom_expression in get_armature_vrm1_extension(
                search_armature
            ).expressions.custom:
                if custom_expression != self:
                    continue
                vrm1 = get_armature_vrm1_extension(search_armature)
                break
        if vrm1 is None:
            logger.error("No armature extension for %s", self)
            return

        expressions = vrm1.expressions
        all_expression_names = expressions.all_name_to_expression_dict().keys()
        custom_name = value
        for index in range(sys.maxsize):
            if index > 0:
                custom_name = f"{value}.{index:03}"
            if custom_name not in all_expression_names:
                break

        self["custom_name"] = custom_name
        self.name = custom_name

    custom_name: StringProperty(  # type: ignore[valid-type]
        name="Name",
        get=get_custom_name,
        set=set_custom_name,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        custom_name: str  # type: ignore[no-redef]


@dataclass(frozen=True)
class ExpressionPreset:
    name: str
    icon: str
    mouth: bool
    blink: bool
    look_at: bool


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.expressions.schema.json
class Vrm1ExpressionsPresetPropertyGroup(PropertyGroup):
    happy: PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    angry: PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    sad: PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    relaxed: PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    surprised: PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    neutral: PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    aa: PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    ih: PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    ou: PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    ee: PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    oh: PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    blink: PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    blink_left: PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    blink_right: PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    look_up: PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    look_down: PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    look_left: PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]
    look_right: PointerProperty(type=Vrm1ExpressionPropertyGroup)  # type: ignore[valid-type]

    def expression_preset_and_expressions(
        self,
    ) -> tuple[tuple[ExpressionPreset, Vrm1ExpressionPropertyGroup], ...]:
        return (
            (
                ExpressionPreset(
                    "happy", "HEART", mouth=False, blink=False, look_at=False
                ),
                self.happy,
            ),
            (
                ExpressionPreset(
                    "angry", "ORPHAN_DATA", mouth=False, blink=False, look_at=False
                ),
                self.angry,
            ),
            (
                ExpressionPreset(
                    "sad", "MOD_FLUIDSIM", mouth=False, blink=False, look_at=False
                ),
                self.sad,
            ),
            (
                ExpressionPreset(
                    "relaxed", "LIGHT_SUN", mouth=False, blink=False, look_at=False
                ),
                self.relaxed,
            ),
            (
                ExpressionPreset(
                    "surprised", "LIGHT_SUN", mouth=False, blink=False, look_at=False
                ),
                self.surprised,
            ),
            (
                ExpressionPreset(
                    "neutral", "VIEW_ORTHO", mouth=False, blink=False, look_at=False
                ),
                self.neutral,
            ),
            (
                ExpressionPreset(
                    "aa", "EVENT_A", mouth=True, blink=False, look_at=False
                ),
                self.aa,
            ),
            (
                ExpressionPreset(
                    "ih", "EVENT_I", mouth=True, blink=False, look_at=False
                ),
                self.ih,
            ),
            (
                ExpressionPreset(
                    "ou", "EVENT_U", mouth=True, blink=False, look_at=False
                ),
                self.ou,
            ),
            (
                ExpressionPreset(
                    "ee", "EVENT_E", mouth=True, blink=False, look_at=False
                ),
                self.ee,
            ),
            (
                ExpressionPreset(
                    "oh", "EVENT_O", mouth=True, blink=False, look_at=False
                ),
                self.oh,
            ),
            (
                ExpressionPreset(
                    "blink", "HIDE_ON", mouth=False, blink=True, look_at=False
                ),
                self.blink,
            ),
            (
                ExpressionPreset(
                    "blinkLeft", "HIDE_ON", mouth=False, blink=True, look_at=False
                ),
                self.blink_left,
            ),
            (
                ExpressionPreset(
                    "blinkRight", "HIDE_ON", mouth=False, blink=True, look_at=False
                ),
                self.blink_right,
            ),
            (
                ExpressionPreset(
                    "lookUp", "ANCHOR_TOP", mouth=False, blink=False, look_at=True
                ),
                self.look_up,
            ),
            (
                ExpressionPreset(
                    "lookDown", "ANCHOR_BOTTOM", mouth=False, blink=False, look_at=True
                ),
                self.look_down,
            ),
            (
                ExpressionPreset(
                    "lookLeft", "ANCHOR_RIGHT", mouth=False, blink=False, look_at=True
                ),
                self.look_left,
            ),
            (
                ExpressionPreset(
                    "lookRight", "ANCHOR_LEFT", mouth=False, blink=False, look_at=True
                ),
                self.look_right,
            ),
        )

    def name_to_expression_dict(self) -> Mapping[str, Vrm1ExpressionPropertyGroup]:
        return {
            preset.name: property_group
            for preset, property_group in self.expression_preset_and_expressions()
        }

    def is_mouth_expression(self, expression_name: str) -> bool:
        return next(
            (
                preset.mouth
                for preset, _ in self.expression_preset_and_expressions()
                if preset.name == expression_name
            ),
            False,
        )

    def is_blink_expression(self, expression_name: str) -> bool:
        return next(
            (
                preset.blink
                for preset, _ in self.expression_preset_and_expressions()
                if preset.name == expression_name
            ),
            False,
        )

    def get_icon(self, expression_name: str) -> Optional[str]:
        return next(
            (
                preset.icon
                for preset, _ in self.expression_preset_and_expressions()
                if preset.name == expression_name
            ),
            None,
        )

    def is_look_at_expression(self, expression_name: str) -> bool:
        return next(
            (
                preset.look_at
                for preset, _ in self.expression_preset_and_expressions()
                if preset.name == expression_name
            ),
            False,
        )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        happy: Vrm1ExpressionPropertyGroup  # type: ignore[no-redef]
        angry: Vrm1ExpressionPropertyGroup  # type: ignore[no-redef]
        sad: Vrm1ExpressionPropertyGroup  # type: ignore[no-redef]
        relaxed: Vrm1ExpressionPropertyGroup  # type: ignore[no-redef]
        surprised: Vrm1ExpressionPropertyGroup  # type: ignore[no-redef]
        neutral: Vrm1ExpressionPropertyGroup  # type: ignore[no-redef]
        aa: Vrm1ExpressionPropertyGroup  # type: ignore[no-redef]
        ih: Vrm1ExpressionPropertyGroup  # type: ignore[no-redef]
        ou: Vrm1ExpressionPropertyGroup  # type: ignore[no-redef]
        ee: Vrm1ExpressionPropertyGroup  # type: ignore[no-redef]
        oh: Vrm1ExpressionPropertyGroup  # type: ignore[no-redef]
        blink: Vrm1ExpressionPropertyGroup  # type: ignore[no-redef]
        blink_left: Vrm1ExpressionPropertyGroup  # type: ignore[no-redef]
        blink_right: Vrm1ExpressionPropertyGroup  # type: ignore[no-redef]
        look_up: Vrm1ExpressionPropertyGroup  # type: ignore[no-redef]
        look_down: Vrm1ExpressionPropertyGroup  # type: ignore[no-redef]
        look_left: Vrm1ExpressionPropertyGroup  # type: ignore[no-redef]
        look_right: Vrm1ExpressionPropertyGroup  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.expressions.schema.json
class Vrm1ExpressionsPropertyGroup(PropertyGroup):
    preset: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1ExpressionsPresetPropertyGroup,
    )

    custom: CollectionProperty(  # type: ignore[valid-type]
        type=Vrm1CustomExpressionPropertyGroup,
    )

    def all_name_to_expression_dict(self) -> Mapping[str, Vrm1ExpressionPropertyGroup]:
        result: dict[str, Vrm1ExpressionPropertyGroup] = dict(
            self.preset.name_to_expression_dict()
        )
        for custom_expression in self.custom:
            result[custom_expression.custom_name] = custom_expression
        return result

    # expressionのUIList表示のため、expressionの数だけ空の要素を持つ
    expression_ui_list_elements: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )
    active_expression_ui_list_element_index: IntProperty(min=0)  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        preset: Vrm1ExpressionsPresetPropertyGroup  # type: ignore[no-redef]
        custom: CollectionPropertyProtocol[  # type: ignore[no-redef]
            Vrm1CustomExpressionPropertyGroup
        ]
        expression_ui_list_elements: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]
        active_expression_ui_list_element_index: int  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.meta.schema.json
class Vrm1MetaPropertyGroup(PropertyGroup):
    avatar_permission_enum, __avatar_permissions = property_group_enum(
        ("onlyAuthor", "Only Author", "", "NONE", 0),
        (
            "onlySeparatelyLicensedPerson",
            "Only Separately Licensed Person",
            "",
            "NONE",
            1,
        ),
        ("everyone", "Everyone", "", "NONE", 2),
    )

    commercial_usage_enum, __commercial_usage = property_group_enum(
        ("personalNonProfit", "Personal Non-Profit", "", "NONE", 0),
        ("personalProfit", "Personal Profit", "", "NONE", 1),
        ("corporation", "Corporation", "", "NONE", 2),
    )

    credit_notation_enum, __credit_notation = property_group_enum(
        ("required", "Required", "", "NONE", 0),
        ("unnecessary", "Unnecessary", "", "NONE", 1),
    )

    modification_enum, __modification = property_group_enum(
        ("prohibited", "Prohibited", "", "NONE", 0),
        ("allowModification", "Allow Modification", "", "NONE", 1),
        (
            "allowModificationRedistribution",
            "Allow Modification Redistribution",
            "",
            "NONE",
            2,
        ),
    )

    vrm_name: StringProperty(  # type: ignore[valid-type]
        name="Name"
    )
    version: StringProperty(  # type: ignore[valid-type]
        name="Version"
    )
    authors: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )
    copyright_information: StringProperty(  # type: ignore[valid-type]
        name="Copyright Information"
    )
    contact_information: StringProperty(  # type: ignore[valid-type]
        name="Contact Information"
    )
    references: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )
    third_party_licenses: StringProperty(  # type: ignore[valid-type]
        name="Third Party Licenses"
    )
    thumbnail_image: PointerProperty(  # type: ignore[valid-type]
        name="Thumbnail Image",
        type=Image,
    )
    # license_url: StringProperty(  # type: ignore[valid-type]
    #     name="License URL"
    # )
    avatar_permission: EnumProperty(  # type: ignore[valid-type]
        name="Avatar Permission",
        items=avatar_permission_enum.items(),
    )
    allow_excessively_violent_usage: BoolProperty(  # type: ignore[valid-type]
        name="Allow Excessively Violent Usage"
    )
    allow_excessively_sexual_usage: BoolProperty(  # type: ignore[valid-type]
        name="Allow Excessively Sexual Usage"
    )
    commercial_usage: EnumProperty(  # type: ignore[valid-type]
        name="Commercial Usage",
        items=commercial_usage_enum.items(),
    )
    allow_political_or_religious_usage: BoolProperty(  # type: ignore[valid-type]
        name="Allow Political or Religious Usage"
    )
    allow_antisocial_or_hate_usage: BoolProperty(  # type: ignore[valid-type]
        name="Allow Antisocial or Hate Usage"
    )
    credit_notation: EnumProperty(  # type: ignore[valid-type]
        name="Credit Notation",
        items=credit_notation_enum.items(),
    )
    allow_redistribution: BoolProperty(  # type: ignore[valid-type]
        name="Allow Redistribution"
    )
    modification: EnumProperty(  # type: ignore[valid-type]
        name="Modification",
        items=modification_enum.items(),
    )
    other_license_url: StringProperty(  # type: ignore[valid-type]
        name="Other License URL"
    )

    # for UI
    active_author_index: IntProperty(min=0)  # type: ignore[valid-type]
    active_reference_index: IntProperty(min=0)  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        vrm_name: str  # type: ignore[no-redef]
        version: str  # type: ignore[no-redef]
        authors: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]
        copyright_information: str  # type: ignore[no-redef]
        contact_information: str  # type: ignore[no-redef]
        references: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]
        third_party_licenses: str  # type: ignore[no-redef]
        thumbnail_image: Optional[Image]  # type: ignore[no-redef]
        avatar_permission: str  # type: ignore[no-redef]
        allow_excessively_violent_usage: bool  # type: ignore[no-redef]
        allow_excessively_sexual_usage: bool  # type: ignore[no-redef]
        commercial_usage: str  # type: ignore[no-redef]
        allow_political_or_religious_usage: bool  # type: ignore[no-redef]
        allow_antisocial_or_hate_usage: bool  # type: ignore[no-redef]
        credit_notation: str  # type: ignore[no-redef]
        allow_redistribution: bool  # type: ignore[no-redef]
        modification: str  # type: ignore[no-redef]
        other_license_url: str  # type: ignore[no-redef]
        active_author_index: int  # type: ignore[no-redef]
        active_reference_index: int  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.schema.json
class Vrm1PropertyGroup(PropertyGroup):
    meta: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1MetaPropertyGroup
    )
    humanoid: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanoidPropertyGroup
    )
    first_person: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1FirstPersonPropertyGroup
    )
    look_at: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1LookAtPropertyGroup
    )
    expressions: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1ExpressionsPropertyGroup
    )
    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        meta: Vrm1MetaPropertyGroup  # type: ignore[no-redef]
        humanoid: Vrm1HumanoidPropertyGroup  # type: ignore[no-redef]
        first_person: Vrm1FirstPersonPropertyGroup  # type: ignore[no-redef]
        look_at: Vrm1LookAtPropertyGroup  # type: ignore[no-redef]
        expressions: Vrm1ExpressionsPropertyGroup  # type: ignore[no-redef]


def get_armature_vrm1_extension(armature: Armature) -> Vrm1PropertyGroup:
    from ..extension import get_armature_extension

    vrm1: Vrm1PropertyGroup = get_armature_extension(armature).vrm1
    return vrm1
