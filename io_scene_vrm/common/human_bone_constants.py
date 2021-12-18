"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

from typing import Dict


class HumanBone:
    center_req = ["hips", "spine", "chest", "neck", "head"]
    left_leg_req = ["leftUpperLeg", "leftLowerLeg", "leftFoot"]
    left_arm_req = ["leftUpperArm", "leftLowerArm", "leftHand"]
    right_leg_req = ["rightUpperLeg", "rightLowerLeg", "rightFoot"]
    right_arm_req = ["rightUpperArm", "rightLowerArm", "rightHand"]

    requires = [
        *center_req[:],
        *left_leg_req[:],
        *right_leg_req[:],
        *left_arm_req[:],
        *right_arm_req[:],
    ]

    left_arm_def = [
        "leftShoulder",
        "leftThumbProximal",
        "leftThumbIntermediate",
        "leftThumbDistal",
        "leftIndexProximal",
        "leftIndexIntermediate",
        "leftIndexDistal",
        "leftMiddleProximal",
        "leftMiddleIntermediate",
        "leftMiddleDistal",
        "leftRingProximal",
        "leftRingIntermediate",
        "leftRingDistal",
        "leftLittleProximal",
        "leftLittleIntermediate",
        "leftLittleDistal",
    ]

    right_arm_def = [
        "rightShoulder",
        "rightThumbProximal",
        "rightThumbIntermediate",
        "rightThumbDistal",
        "rightIndexProximal",
        "rightIndexIntermediate",
        "rightIndexDistal",
        "rightMiddleProximal",
        "rightMiddleIntermediate",
        "rightMiddleDistal",
        "rightRingProximal",
        "rightRingIntermediate",
        "rightRingDistal",
        "rightLittleProximal",
        "rightLittleIntermediate",
        "rightLittleDistal",
    ]
    center_def = ["upperChest", "jaw"]
    left_leg_def = ["leftToes"]
    right_leg_def = ["rightToes"]
    defines = [
        "leftEye",
        "rightEye",
        *center_def[:],
        *left_leg_def[:],
        *right_leg_def[:],
        *left_arm_def[:],
        *right_arm_def[:],
    ]
    # child:parent
    hierarchy: Dict[str, str] = {
        # 体幹
        "leftEye": "head",
        "rightEye": "head",
        "jaw": "head",
        "head": "neck",
        "neck": "upperChest",
        "upperChest": "chest",
        "chest": "spine",
        "spine": "hips",  # root
        # 右上
        "rightShoulder": "chest",
        "rightUpperArm": "rightShoulder",
        "rightLowerArm": "rightUpperArm",
        "rightHand": "rightLowerArm",
        "rightThumbProximal": "rightHand",
        "rightThumbIntermediate": "rightThumbProximal",
        "rightThumbDistal": "rightThumbIntermediate",
        "rightIndexProximal": "rightHand",
        "rightIndexIntermediate": "rightIndexProximal",
        "rightIndexDistal": "rightIndexIntermediate",
        "rightMiddleProximal": "rightHand",
        "rightMiddleIntermediate": "rightMiddleProximal",
        "rightMiddleDistal": "rightMiddleIntermediate",
        "rightRingProximal": "rightHand",
        "rightRingIntermediate": "rightRingProximal",
        "rightRingDistal": "rightRingIntermediate",
        "rightLittleProximal": "rightHand",
        "rightLittleIntermediate": "rightLittleProximal",
        "rightLittleDistal": "rightLittleIntermediate",
        # 左上
        "leftShoulder": "chest",
        "leftUpperArm": "leftShoulder",
        "leftLowerArm": "leftUpperArm",
        "leftHand": "leftLowerArm",
        "leftThumbProximal": "leftHand",
        "leftThumbIntermediate": "leftThumbProximal",
        "leftThumbDistal": "leftThumbIntermediate",
        "leftIndexProximal": "leftHand",
        "leftIndexIntermediate": "leftIndexProximal",
        "leftIndexDistal": "leftIndexIntermediate",
        "leftMiddleProximal": "leftHand",
        "leftMiddleIntermediate": "leftMiddleProximal",
        "leftMiddleDistal": "leftMiddleIntermediate",
        "leftRingProximal": "leftHand",
        "leftRingIntermediate": "leftRingProximal",
        "leftRingDistal": "leftRingIntermediate",
        "leftLittleProximal": "leftHand",
        "leftLittleIntermediate": "leftLittleProximal",
        "leftLittleDistal": "leftLittleIntermediate",
        # 左足
        "leftUpperLeg": "hips",
        "leftLowerLeg": "leftUpperLeg",
        "leftFoot": "leftLowerLeg",
        "leftToes": "leftFoot",
        # 右足
        "rightUpperLeg": "hips",
        "rightLowerLeg": "rightUpperLeg",
        "rightFoot": "rightLowerLeg",
        "rightToes": "rightFoot",
    }
