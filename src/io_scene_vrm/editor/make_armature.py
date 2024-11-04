# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Set as AbstractSet
from math import radians
from sys import float_info
from typing import TYPE_CHECKING, Optional

import bpy
from bpy.props import BoolProperty, FloatProperty, StringProperty
from bpy.types import Armature, Context, EditBone, Object, Operator
from mathutils import Matrix, Vector

from ..common.version import get_addon_version
from ..common.workspace import save_workspace
from . import migration
from .extension import get_armature_extension
from .vrm0.property_group import (
    Vrm0BlendShapeGroupPropertyGroup,
    Vrm0HumanoidPropertyGroup,
)

MIN_BONE_LENGTH = 0.00001  # 10μm
AUTO_BONE_CONNECTION_DISTANCE = 0.000001  # 1μm


class ICYP_OT_make_armature(Operator):
    bl_idname = "icyp.make_basic_armature"
    bl_label = "Add VRM Humanoid"
    bl_description = "make armature and simple setup for VRM export"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    skip_heavy_armature_setup: BoolProperty(  # type: ignore[valid-type]
        default=False,
        options={"HIDDEN"},
    )

    wip_with_template_mesh: BoolProperty(  # type: ignore[valid-type]
        default=False
    )

    # 身長 at meter
    tall: FloatProperty(  # type: ignore[valid-type]
        default=1.70,
        min=0.3,
        step=1,
        name="Bone tall",
    )

    # 頭身
    head_ratio: FloatProperty(  # type: ignore[valid-type]
        default=8.0,
        min=4,
        step=5,
        description="height per heads",
    )

    head_width_ratio: FloatProperty(  # type: ignore[valid-type]
        default=2 / 3,
        min=0.3,
        max=1.2,
        step=5,
        description="height per heads",
    )

    # 足-胴比率:0:子供、1:大人 に近くなる(低等身で有効)
    aging_ratio: FloatProperty(  # type: ignore[valid-type]
        default=0.5, min=0, max=1, step=10
    )

    # 目の奥み
    eye_depth: FloatProperty(  # type: ignore[valid-type]
        default=-0.03, min=-0.1, max=0, step=1
    )

    # 肩幅
    shoulder_in_width: FloatProperty(  # type: ignore[valid-type]
        default=0.05,
        min=0.01,
        step=1,
        description="Inner shoulder position",
    )

    shoulder_width: FloatProperty(  # type: ignore[valid-type]
        default=0.08,
        min=0.01,
        step=1,
        description="shoulder roll position",
    )

    # 腕長さ率
    arm_length_ratio: FloatProperty(  # type: ignore[valid-type]
        default=1, min=0.5, step=1
    )

    # 手
    hand_ratio: FloatProperty(  # type: ignore[valid-type]
        default=1, min=0.5, max=2.0, step=5
    )

    finger_1_2_ratio: FloatProperty(  # type: ignore[valid-type]
        default=0.75,
        min=0.5,
        max=1,
        step=1,
        description="proximal / intermediate",
    )

    finger_2_3_ratio: FloatProperty(  # type: ignore[valid-type]
        default=0.75,
        min=0.5,
        max=1,
        step=1,
        description="intermediate / distal",
    )

    nail_bone: BoolProperty(  # type: ignore[valid-type]
        default=False,
        description="may need for finger collider",
    )  # 指先の当たり判定として必要

    # 足
    leg_length_ratio: FloatProperty(  # type: ignore[valid-type]
        default=0.5,
        min=0.3,
        max=0.6,
        step=1,
        description="upper body/lower body",
    )

    leg_width_ratio: FloatProperty(  # type: ignore[valid-type]
        default=1, min=0.01, step=1
    )

    leg_size: FloatProperty(  # type: ignore[valid-type]
        default=0.26, min=0.05, step=1
    )

    custom_property_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )

    armature_obj: Optional[Object] = None

    def execute(self, context: Context) -> set[str]:
        with save_workspace(context):
            self.armature_obj, compare_dict = self.make_armature(context)
            self.setup_as_vrm(context, self.armature_obj, compare_dict)
            if self.custom_property_name:
                self.armature_obj[self.custom_property_name] = True
        context.view_layer.objects.active = self.armature_obj
        return {"FINISHED"}

    def float_prop(self, name: str) -> float:
        prop = getattr(self, name)
        if not isinstance(prop, float):
            message = f"prop {name} is not float"
            raise TypeError(message)
        return prop

    def head_size(self) -> float:
        return self.float_prop("tall") / self.float_prop("head_ratio")

    def hand_size(self) -> float:
        return self.head_size() * 0.75 * self.float_prop("hand_ratio")

    def make_armature(self, context: Context) -> tuple[Object, dict[str, str]]:
        bpy.ops.object.add(type="ARMATURE", enter_editmode=True, location=(0, 0, 0))
        armature = context.object
        if not armature:
            message = "armature is not created"
            raise ValueError(message)
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            message = "armature data is not an Armature"
            raise TypeError(message)
        get_armature_extension(armature_data).addon_version = get_addon_version()

        bone_dict: dict[str, EditBone] = {}

        def bone_add(
            name: str,
            head_pos: Vector,
            tail_pos: Vector,
            parent_bone: Optional[EditBone] = None,
            radius: float = 0.1,
            roll: float = 0,
        ) -> EditBone:
            armature_data = armature.data
            if not isinstance(armature_data, Armature):
                message = "armature data is not an Armature"
                raise TypeError(message)
            added_bone = armature_data.edit_bones.new(name)
            added_bone.head = head_pos
            added_bone.tail = tail_pos
            added_bone.head_radius = radius
            added_bone.tail_radius = radius
            added_bone.envelope_distance = 0.01
            added_bone.roll = radians(roll)
            if parent_bone is not None:
                added_bone.parent = parent_bone
            bone_dict.update({name: added_bone})
            return added_bone

        # bone_type = "leg" or "arm" for roll setting
        def x_mirror_bones_add(
            base_name: str,
            right_head_pos: Vector,
            right_tail_pos: Vector,
            parent_bones: tuple[EditBone, EditBone],
            radius: float = 0.1,
            bone_type: str = "other",
        ) -> tuple[EditBone, EditBone]:
            right_roll = 0
            left_roll = 0
            if bone_type == "arm":
                right_roll = 0
            elif bone_type == "leg":
                right_roll = 0
                left_roll = 0
            left_bone = bone_add(
                base_name + ".L",
                right_head_pos,
                right_tail_pos,
                parent_bones[0],
                radius=radius,
                roll=left_roll,
            )

            head_pos = [pos * axis for pos, axis in zip(right_head_pos, (-1, 1, 1))]
            tail_pos = [pos * axis for pos, axis in zip(right_tail_pos, (-1, 1, 1))]
            right_bone = bone_add(
                base_name + ".R",
                Vector((head_pos[0], head_pos[1], head_pos[2])),
                Vector((tail_pos[0], tail_pos[1], tail_pos[2])),
                parent_bones[1],
                radius=radius,
                roll=right_roll,
            )

            return left_bone, right_bone

        def x_add(pos_a: Vector, add_x: float) -> Vector:
            pos = [p_a + _add for p_a, _add in zip(pos_a, [add_x, 0, 0])]
            return Vector((pos[0], pos[1], pos[2]))

        def y_add(pos_a: Vector, add_y: float) -> Vector:
            pos = [p_a + _add for p_a, _add in zip(pos_a, [0, add_y, 0])]
            return Vector((pos[0], pos[1], pos[2]))

        def z_add(pos_a: Vector, add_z: float) -> Vector:
            pos = [p_a + _add for p_a, _add in zip(pos_a, [0, 0, add_z])]
            return Vector((pos[0], pos[1], pos[2]))

        head_size = self.head_size()
        # down side (前は8頭身の時の股上/股下の股下側割合、
        # 後ろは4頭身のときの〃を年齢具合で線形補完)(股上高めにすると破綻する)
        eight_upside_ratio, four_upside_ratio = (
            1 - self.leg_length_ratio,
            (2.5 / 4) * (1 - self.aging_ratio)
            + (1 - self.leg_length_ratio) * self.aging_ratio,
        )
        hip_up_down_ratio = (
            eight_upside_ratio * (1 - (8 - self.head_ratio) / 4)
            + four_upside_ratio * (8 - self.head_ratio) / 4
        )
        # 体幹
        # 股間
        body_separate = self.tall * (1 - hip_up_down_ratio)
        # 首の長さ
        neck_len = head_size * 2 / 3
        # 仙骨(骨盤脊柱基部)
        hips_tall = body_separate + head_size * 3 / 4
        # 胸椎・spineの全長 #首の1/3は顎の後ろに隠れてる
        backbone_len = self.tall - hips_tall - head_size - neck_len / 2
        # TODO: 胸椎と脊椎の割合の確認
        # 脊椎の基部に位置する主となる屈曲点と、胸郭基部に位置するもうひとつの屈曲点
        # by Humanoid Doc
        spine_len = backbone_len * 5 / 17

        root = bone_add("root", Vector((0, 0, 0)), Vector((0, 0, 0.3)))
        # 仙骨基部
        hips = bone_add(
            "hips",
            Vector((0, 0, body_separate)),
            Vector((0, 0, hips_tall)),
            root,
            roll=0,
        )
        # 骨盤基部->胸郭基部
        spine = bone_add("spine", hips.tail, z_add(hips.tail, spine_len), hips, roll=0)
        # 胸郭基部->首元
        chest = bone_add(
            "chest", spine.tail, z_add(hips.tail, backbone_len), spine, roll=0
        )
        neck = bone_add(
            "neck",
            Vector((0, 0, self.tall - head_size - neck_len / 2)),
            Vector((0, 0, self.tall - head_size + neck_len / 2)),
            chest,
            roll=0,
        )
        # 首の1/2は顎の後ろに隠れてる
        head = bone_add(
            "head",
            Vector((0, 0, self.tall - head_size + neck_len / 2)),
            Vector((0, 0, self.tall)),
            neck,
            roll=0,
        )

        # 目
        eye_depth = self.eye_depth
        eyes = x_mirror_bones_add(
            "eye",
            Vector(
                (head_size * self.head_width_ratio / 5, 0, self.tall - head_size / 2)
            ),
            Vector(
                (
                    head_size * self.head_width_ratio / 5,
                    eye_depth,
                    self.tall - head_size / 2,
                )
            ),
            (head, head),
        )
        # 足
        leg_width = head_size / 4 * self.leg_width_ratio
        leg_size = self.leg_size

        leg_bone_length = (body_separate + head_size * 3 / 8 - self.tall * 0.05) / 2
        upside_legs = x_mirror_bones_add(
            "upper_leg",
            x_add(Vector((0, 0, body_separate + head_size * 3 / 8)), leg_width),
            x_add(
                Vector(
                    z_add(
                        Vector((0, 0, body_separate + head_size * 3 / 8)),
                        -leg_bone_length,
                    )
                ),
                leg_width,
            ),
            (hips, hips),
            radius=leg_width * 0.9,
            bone_type="leg",
        )
        lower_legs = x_mirror_bones_add(
            "lower_leg",
            upside_legs[0].tail,
            Vector((leg_width, 0, self.tall * 0.05)),
            upside_legs,
            radius=leg_width * 0.9,
            bone_type="leg",
        )
        foots = x_mirror_bones_add(
            "foot",
            lower_legs[0].tail,
            Vector((leg_width, -leg_size * (2 / 3), 0)),
            lower_legs,
            radius=leg_width * 0.9,
            bone_type="leg",
        )
        toes = x_mirror_bones_add(
            "toes",
            foots[0].tail,
            Vector((leg_width, -leg_size, 0)),
            foots,
            radius=leg_width * 0.5,
            bone_type="leg",
        )

        # 肩~指
        shoulder_in_pos = self.shoulder_in_width / 2

        shoulder_parent = chest
        shoulders = x_mirror_bones_add(
            "shoulder",
            x_add(shoulder_parent.tail, shoulder_in_pos),
            x_add(shoulder_parent.tail, shoulder_in_pos + self.shoulder_width),
            (shoulder_parent, shoulder_parent),
            radius=self.hand_size() * 0.4,
            bone_type="arm",
        )

        arm_length = (
            head_size
            * (1 * (1 - (self.head_ratio - 6) / 2) + 1.5 * ((self.head_ratio - 6) / 2))
            * self.arm_length_ratio
        )
        arms = x_mirror_bones_add(
            "upper_arm",
            shoulders[0].tail,
            x_add(shoulders[0].tail, arm_length),
            shoulders,
            radius=self.hand_size() * 0.4,
            bone_type="arm",
        )

        # グーにするとパーの半分くらいになる、グーのとき手を含む下腕の長さと上腕の長さが
        # 概ね一緒、けど手がでかすぎると破綻する
        forearm_length = max(arm_length - self.hand_size() / 2, arm_length * 0.8)
        forearms = x_mirror_bones_add(
            "lower_arm",
            arms[0].tail,
            x_add(arms[0].tail, forearm_length),
            arms,
            radius=self.hand_size() * 0.4,
            bone_type="arm",
        )
        hands = x_mirror_bones_add(
            "hand",
            forearms[0].tail,
            x_add(forearms[0].tail, self.hand_size() / 2),
            forearms,
            radius=self.hand_size() / 4,
            bone_type="arm",
        )

        def fingers(
            finger_name: str,
            proximal_pos: Vector,
            finger_len_sum: float,
        ) -> tuple[
            tuple[EditBone, EditBone],
            tuple[EditBone, EditBone],
            tuple[EditBone, EditBone],
        ]:
            finger_normalize = 1 / (
                self.finger_1_2_ratio * self.finger_2_3_ratio
                + self.finger_1_2_ratio
                + 1
            )
            proximal_finger_len = finger_len_sum * finger_normalize
            intermediate_finger_len = (
                finger_len_sum * finger_normalize * self.finger_1_2_ratio
            )
            distal_finger_len = (
                finger_len_sum
                * finger_normalize
                * self.finger_1_2_ratio
                * self.finger_2_3_ratio
            )
            proximal_bones = x_mirror_bones_add(
                f"{finger_name}_proximal",
                proximal_pos,
                x_add(proximal_pos, proximal_finger_len),
                hands,
                self.hand_size() / 18,
                bone_type="arm",
            )
            intermediate_bones = x_mirror_bones_add(
                f"{finger_name}_intermediate",
                proximal_bones[0].tail,
                x_add(proximal_bones[0].tail, intermediate_finger_len),
                proximal_bones,
                self.hand_size() / 18,
                bone_type="arm",
            )
            distal_bones = x_mirror_bones_add(
                f"{finger_name}_distal",
                intermediate_bones[0].tail,
                x_add(intermediate_bones[0].tail, distal_finger_len),
                intermediate_bones,
                self.hand_size() / 18,
                bone_type="arm",
            )
            if self.nail_bone:
                x_mirror_bones_add(
                    f"{finger_name}_nail",
                    distal_bones[0].tail,
                    x_add(distal_bones[0].tail, distal_finger_len),
                    distal_bones,
                    self.hand_size() / 20,
                    bone_type="arm",
                )
            return proximal_bones, intermediate_bones, distal_bones

        finger_y_offset = -self.hand_size() / 16
        thumbs = fingers(
            "thumb",
            y_add(hands[0].head, finger_y_offset * 3),
            self.hand_size() / 2,
        )

        mats = [
            Matrix.Translation(vec)
            for vec in [thumbs[0][i].matrix.translation for i in [0, 1]]
        ]
        for j in range(3):
            for n, angle in enumerate([-45, 45]):
                thumbs[j][n].transform(mats[n].inverted(), scale=False, roll=False)
                thumbs[j][n].transform(Matrix.Rotation(radians(angle), 4, "Z"))
                thumbs[j][n].transform(mats[n], scale=False, roll=False)
                thumbs[j][n].roll = 0

        index_fingers = fingers(
            "index",
            y_add(hands[0].tail, finger_y_offset * 3),
            (self.hand_size() / 2) - (1 / 2.3125) * (self.hand_size() / 2) / 3,
        )
        middle_fingers = fingers(
            "middle", y_add(hands[0].tail, finger_y_offset), self.hand_size() / 2
        )
        ring_fingers = fingers(
            "ring",
            y_add(hands[0].tail, -finger_y_offset),
            (self.hand_size() / 2) - (1 / 2.3125) * (self.hand_size() / 2) / 3,
        )
        little_fingers = fingers(
            "little",
            y_add(hands[0].tail, -finger_y_offset * 3),
            ((self.hand_size() / 2) - (1 / 2.3125) * (self.hand_size() / 2) / 3)
            * ((1 / 2.3125) + (1 / 2.3125) * 0.75),
        )

        body_dict = {
            "hips": hips.name,
            "spine": spine.name,
            "chest": chest.name,
            "neck": neck.name,
            "head": head.name,
        }

        left_right_body_dict = {
            f"{left_right}{bone_name}": bones[lr].name
            for bone_name, bones in {
                "Eye": eyes,
                "UpperLeg": upside_legs,
                "LowerLeg": lower_legs,
                "Foot": foots,
                "Toes": toes,
                "Shoulder": shoulders,
                "UpperArm": arms,
                "LowerArm": forearms,
                "Hand": hands,
            }.items()
            for lr, left_right in enumerate(["left", "right"])
        }

        # VRM finger like name key
        fingers_dict = {
            f"{left_right}{finger_name}{position}": finger[i][lr].name
            for finger_name, finger in zip(
                ["Thumb", "Index", "Middle", "Ring", "Little"],
                [thumbs, index_fingers, middle_fingers, ring_fingers, little_fingers],
            )
            for i, position in enumerate(["Proximal", "Intermediate", "Distal"])
            for lr, left_right in enumerate(["left", "right"])
        }

        # VRM bone name : blender bone name
        bone_name_all_dict: dict[str, str] = {}
        bone_name_all_dict.update(body_dict)
        bone_name_all_dict.update(left_right_body_dict)
        bone_name_all_dict.update(fingers_dict)

        armature_data = armature.data
        if isinstance(armature_data, Armature):
            connect_parent_tail_and_child_head_if_very_close_position(armature_data)

        context.scene.view_layers.update()
        bpy.ops.object.mode_set(mode="OBJECT")
        context.scene.view_layers.update()
        return armature, bone_name_all_dict

    def setup_as_vrm(
        self, context: Context, armature: Object, compare_dict: dict[str, str]
    ) -> None:
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            message = "armature data is not an Armature"
            raise TypeError(message)
        Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
        ext = get_armature_extension(armature_data)
        vrm0_humanoid = ext.vrm0.humanoid
        vrm1_humanoid = ext.vrm1.humanoid
        if not self.skip_heavy_armature_setup:
            for vrm_bone_name, bpy_bone_name in compare_dict.items():
                for human_bone in vrm0_humanoid.human_bones:
                    if human_bone.bone == vrm_bone_name:
                        human_bone.node.set_bone_name(bpy_bone_name)
                        break
        vrm0_humanoid.pose = vrm0_humanoid.POSE_REST_POSITION_POSE.identifier
        vrm1_humanoid.pose = vrm1_humanoid.POSE_REST_POSITION_POSE.identifier
        self.make_extension_setting_and_metas(
            armature,
            offset_from_head_bone=(-self.eye_depth, self.head_size() / 6, 0),
        )
        if not self.skip_heavy_armature_setup:
            migration.migrate(context, armature.name)

    @classmethod
    def make_extension_setting_and_metas(
        cls,
        armature: Object,
        offset_from_head_bone: tuple[float, float, float] = (0, 0, 0),
    ) -> None:
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        vrm0 = get_armature_extension(armature_data).vrm0
        vrm1 = get_armature_extension(armature_data).vrm1
        vrm0.first_person.first_person_bone.set_bone_name("head")
        vrm0.first_person.first_person_bone_offset = (0, 0, 0.06)
        vrm1.look_at.offset_from_head_bone = offset_from_head_bone
        vrm0.first_person.look_at_horizontal_inner.y_range = 8
        vrm0.first_person.look_at_horizontal_outer.y_range = 12
        vrm0.meta.author = "undefined"
        vrm0.meta.contact_information = "undefined"
        vrm0.meta.other_license_url = "undefined"
        vrm0.meta.other_permission_url = "undefined"
        vrm0.meta.reference = "undefined"
        vrm0.meta.title = "undefined"
        vrm0.meta.version = "undefined"
        for preset in Vrm0BlendShapeGroupPropertyGroup.preset_name_enum:
            if (
                preset.identifier
                == Vrm0BlendShapeGroupPropertyGroup.PRESET_NAME_UNKNOWN.identifier
            ):
                continue
            blend_shape_group = vrm0.blend_shape_master.blend_shape_groups.add()
            blend_shape_group.name = preset.name.replace(" ", "")
            blend_shape_group.preset_name = preset.identifier

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        skip_heavy_armature_setup: bool  # type: ignore[no-redef]
        wip_with_template_mesh: bool  # type: ignore[no-redef]
        tall: float  # type: ignore[no-redef]
        head_ratio: float  # type: ignore[no-redef]
        head_width_ratio: float  # type: ignore[no-redef]
        aging_ratio: float  # type: ignore[no-redef]
        eye_depth: float  # type: ignore[no-redef]
        shoulder_in_width: float  # type: ignore[no-redef]
        shoulder_width: float  # type: ignore[no-redef]
        arm_length_ratio: float  # type: ignore[no-redef]
        hand_ratio: float  # type: ignore[no-redef]
        finger_1_2_ratio: float  # type: ignore[no-redef]
        finger_2_3_ratio: float  # type: ignore[no-redef]
        nail_bone: bool  # type: ignore[no-redef]
        leg_length_ratio: float  # type: ignore[no-redef]
        leg_width_ratio: float  # type: ignore[no-redef]
        leg_size: float  # type: ignore[no-redef]
        custom_property_name: str  # type: ignore[no-redef]


def connect_parent_tail_and_child_head_if_very_close_position(
    armature: Armature,
) -> None:
    bones = [bone for bone in armature.edit_bones if not bone.parent]
    while bones:
        bone = bones.pop()

        children_by_distance = sorted(
            bone.children,
            key=lambda child: (child.parent.tail - child.head).length_squared
            if child.parent
            else 0.0,
        )
        for child in children_by_distance:
            if (bone.tail - child.head).length < AUTO_BONE_CONNECTION_DISTANCE and (
                bone.head - child.head
            ).length >= MIN_BONE_LENGTH:
                bone.tail = child.head
            break

        bones.extend(bone.children)

    bones = [bone for bone in armature.edit_bones if not bone.parent]
    while bones:
        bone = bones.pop()
        for child in bone.children:
            if (bone.tail - child.head).length < float_info.epsilon:
                child.use_connect = True
            bones.append(child)
