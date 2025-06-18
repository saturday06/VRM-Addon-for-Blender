# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import json
import sys
import tempfile
from pathlib import Path
from unittest import main

import bpy
from bpy.types import Armature
from mathutils import Vector

from io_scene_vrm.common import deep, ops, version
from io_scene_vrm.common.debug import assert_vector3_equals
from io_scene_vrm.common.test_helper import AddonTestCase
from io_scene_vrm.editor.extension import (
    VrmAddonArmatureExtensionPropertyGroup,
    get_armature_extension,
)

addon_version = version.get_addon_version()


class TestSimplifyVroidBones(AddonTestCase):
    def test_bones_rename(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armatures = [
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        ]
        self.assertEqual(len(armatures), 1)
        armature = armatures[0]
        if not isinstance(armature.data, Armature):
            raise TypeError

        head = armature.data.bones["head"]
        head.name = "J_Bip_C_Head"
        eye_l = armature.data.bones["eye.L"]
        eye_l.name = "J_Adj_L_FaceEye"
        upper_arm_r = armature.data.bones["upper_arm.R"]
        upper_arm_r.name = "J_Sec_R_UpperArm"

        ops.vrm.bones_rename(armature_object_name=armature.name)

        self.assertEqual(head, armature.data.bones["Head"])
        self.assertEqual(eye_l, armature.data.bones["FaceEye_L"])
        self.assertEqual(upper_arm_r, armature.data.bones["UpperArm_R"])


class TestSaveHumanBoneMappings(AddonTestCase):
    def test(self) -> None:
        ops.icyp.make_basic_armature()

        with tempfile.NamedTemporaryFile() as file:
            file.close()
            ops.vrm.save_human_bone_mappings(filepath=file.name)
            loaded_json = json.loads(Path(file.name).read_text(encoding="UTF-8"))

        diffs = deep.diff(
            loaded_json,
            {
                "chest": "chest",
                "head": "head",
                "hips": "hips",
                "leftEye": "eye.L",
                "leftFoot": "foot.L",
                "leftHand": "hand.L",
                "leftIndexDistal": "index_distal.L",
                "leftIndexIntermediate": "index_intermediate.L",
                "leftIndexProximal": "index_proximal.L",
                "leftLittleDistal": "little_distal.L",
                "leftLittleIntermediate": "little_intermediate.L",
                "leftLittleProximal": "little_proximal.L",
                "leftLowerArm": "lower_arm.L",
                "leftLowerLeg": "lower_leg.L",
                "leftMiddleDistal": "middle_distal.L",
                "leftMiddleIntermediate": "middle_intermediate.L",
                "leftMiddleProximal": "middle_proximal.L",
                "leftRingDistal": "ring_distal.L",
                "leftRingIntermediate": "ring_intermediate.L",
                "leftRingProximal": "ring_proximal.L",
                "leftShoulder": "shoulder.L",
                "leftThumbDistal": "thumb_distal.L",
                "leftThumbIntermediate": "thumb_intermediate.L",
                "leftThumbProximal": "thumb_proximal.L",
                "leftToes": "toes.L",
                "leftUpperArm": "upper_arm.L",
                "leftUpperLeg": "upper_leg.L",
                "neck": "neck",
                "rightEye": "eye.R",
                "rightFoot": "foot.R",
                "rightHand": "hand.R",
                "rightIndexDistal": "index_distal.R",
                "rightIndexIntermediate": "index_intermediate.R",
                "rightIndexProximal": "index_proximal.R",
                "rightLittleDistal": "little_distal.R",
                "rightLittleIntermediate": "little_intermediate.R",
                "rightLittleProximal": "little_proximal.R",
                "rightLowerArm": "lower_arm.R",
                "rightLowerLeg": "lower_leg.R",
                "rightMiddleDistal": "middle_distal.R",
                "rightMiddleIntermediate": "middle_intermediate.R",
                "rightMiddleProximal": "middle_proximal.R",
                "rightRingDistal": "ring_distal.R",
                "rightRingIntermediate": "ring_intermediate.R",
                "rightRingProximal": "ring_proximal.R",
                "rightShoulder": "shoulder.R",
                "rightThumbDistal": "thumb_distal.R",
                "rightThumbIntermediate": "thumb_intermediate.R",
                "rightThumbProximal": "thumb_proximal.R",
                "rightToes": "toes.R",
                "rightUpperArm": "upper_arm.R",
                "rightUpperLeg": "upper_leg.R",
                "spine": "spine",
            },
        )
        if not diffs:
            return

        message = "\n".join(diffs)
        if sys.platform == "win32":
            sys.stderr.buffer.write((message + "\n").encode())
            raise AssertionError
        raise AssertionError(message)


class TestLoadHumanBoneMappings(AddonTestCase):
    def test(self) -> None:
        context = bpy.context
        ops.icyp.make_basic_armature()

        new_head_name = "root"
        with tempfile.NamedTemporaryFile(delete=False) as file:
            file.write(json.dumps({"head": new_head_name}).encode())
            file.close()
            ops.vrm.load_human_bone_mappings(filepath=file.name)
        active_object = context.view_layer.objects.active
        if not active_object:
            raise AssertionError
        data = active_object.data
        if not isinstance(data, Armature):
            raise TypeError

        b = next(
            human_bone
            for human_bone in get_armature_extension(data).vrm0.humanoid.human_bones
            if human_bone.bone == "head"
        )
        self.assertEqual(
            b.node.bone_name,
            new_head_name,
            (f"head is expected to {new_head_name} but {b.node.bone_name}"),
        )


class TestMakeEstimatedHumanoidTPose(AddonTestCase):
    spec_version = VrmAddonArmatureExtensionPropertyGroup.SPEC_VERSION_VRM1

    def test_right_upper_arm_a(self) -> None:
        context = bpy.context

        self.assertEqual(ops.icyp.make_basic_armature(), {"FINISHED"})
        armature = context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError

        ext = get_armature_extension(armature.data)
        ext.addon_version = addon_version
        ext.spec_version = self.spec_version

        bpy.ops.object.mode_set(mode="EDIT")
        right_lower_arm = armature.data.edit_bones["lower_arm.R"]
        right_lower_arm.use_connect = True
        right_upper_arm = armature.data.edit_bones["upper_arm.R"]
        right_upper_arm.tail = Vector((-0.5, 0, 1))
        bpy.ops.object.mode_set(mode="OBJECT")
        self.assertEqual(
            ops.vrm.make_estimated_humanoid_t_pose(armature_object_name=armature.name),
            {"FINISHED"},
        )

        assert_vector3_equals(
            Vector((-1.2638283967971802, -0.029882915318012238, 1.4166666269302368)),
            armature.pose.bones["index_distal.R"].head,
            "index_distal.R head doesn't match",
        )

    def right_upper_arm_a_not_connected(self) -> None:
        context = bpy.context

        self.assertEqual(ops.icyp.make_basic_armature(), {"FINISHED"})
        armature = context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError

        ext = get_armature_extension(armature.data)
        ext.addon_version = addon_version
        ext.spec_version = self.spec_version

        bpy.ops.object.mode_set(mode="EDIT")
        right_lower_arm = armature.data.edit_bones["lower_arm.R"]
        right_lower_arm.use_connect = False
        right_upper_arm = armature.data.edit_bones["upper_arm.R"]
        right_upper_arm.tail = Vector((-0.5, 0.0, 1.0))
        bpy.ops.object.mode_set(mode="OBJECT")
        self.assertEqual(
            ops.vrm.make_estimated_humanoid_t_pose(armature_object_name=armature.name),
            {"FINISHED"},
        )

        assert_vector3_equals(
            Vector((-0.8100490570068359, -0.02988283522427082, 1.4166666269302368)),
            armature.pose.bones["index_distal.R"].head,
            "index_distal.R head doesn't match",
        )


if __name__ == "__main__":
    main()
