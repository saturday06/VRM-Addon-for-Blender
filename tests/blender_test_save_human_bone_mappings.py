import json
import platform
import sys
import tempfile
from os.path import dirname

import bpy

sys.path.insert(0, dirname(dirname(__file__)))

# pylint: disable=wrong-import-position;
from io_scene_vrm.importer.py_model import json_dict_diff  # noqa: E402

# pylint: enable=wrong-import-position;


def test() -> None:
    bpy.ops.icyp.make_basic_armature()

    with tempfile.NamedTemporaryFile() as file:
        file.close()
        bpy.ops.vrm.save_human_bone_mappings(filepath=file.name)
        with open(file.name, "rb") as read_file:
            loaded_json = json.load(read_file)

    diffs = json_dict_diff(
        loaded_json,
        {
            "chest": "ChestBone",
            "head": "HeadBone",
            "hips": "HipsBone",
            "leftEye": "LeftEyeBone",
            "leftFoot": "LeftFootBone",
            "leftHand": "LeftHandBone",
            "leftIndexDistal": "LeftIndexDistalBone",
            "leftIndexIntermediate": "LeftIndexIntermediateBone",
            "leftIndexProximal": "LeftIndexProximalBone",
            "leftLittleDistal": "LeftLittleDistalBone",
            "leftLittleIntermediate": "LeftLittleIntermediateBone",
            "leftLittleProximal": "LeftLittleProximalBone",
            "leftLowerArm": "LeftLowerArmBone",
            "leftLowerLeg": "LeftLowerLegBone",
            "leftMiddleDistal": "LeftMiddleDistalBone",
            "leftMiddleIntermediate": "LeftMiddleIntermediateBone",
            "leftMiddleProximal": "LeftMiddleProximalBone",
            "leftRingDistal": "LeftRingDistalBone",
            "leftRingIntermediate": "LeftRingIntermediateBone",
            "leftRingProximal": "LeftRingProximalBone",
            "leftShoulder": "LeftShoulderBone",
            "leftThumbDistal": "LeftThumbDistalBone",
            "leftThumbIntermediate": "LeftThumbIntermediateBone",
            "leftThumbProximal": "LeftThumbProximalBone",
            "leftToes": "LeftToesBone",
            "leftUpperArm": "LeftUpperArmBone",
            "leftUpperLeg": "LeftUpperLegBone",
            "neck": "NeckBone",
            "rightEye": "RightEyeBone",
            "rightFoot": "RightFootBone",
            "rightHand": "RightHandBone",
            "rightIndexDistal": "RightIndexDistalBone",
            "rightIndexIntermediate": "RightIndexIntermediateBone",
            "rightIndexProximal": "RightIndexProximalBone",
            "rightLittleDistal": "RightLittleDistalBone",
            "rightLittleIntermediate": "RightLittleIntermediateBone",
            "rightLittleProximal": "RightLittleProximalBone",
            "rightLowerArm": "RightLowerArmBone",
            "rightLowerLeg": "RightLowerLegBone",
            "rightMiddleDistal": "RightMiddleDistalBone",
            "rightMiddleIntermediate": "RightMiddleIntermediateBone",
            "rightMiddleProximal": "RightMiddleProximalBone",
            "rightRingDistal": "RightRingDistalBone",
            "rightRingIntermediate": "RightRingIntermediateBone",
            "rightRingProximal": "RightRingProximalBone",
            "rightShoulder": "RightShoulderBone",
            "rightThumbDistal": "RightThumbDistalBone",
            "rightThumbIntermediate": "RightThumbIntermediateBone",
            "rightThumbProximal": "RightThumbProximalBone",
            "rightToes": "RightToesBone",
            "rightUpperArm": "RightUpperArmBone",
            "rightUpperLeg": "RightUpperLegBone",
            "spine": "SpineBone",
        },
    )
    if not diffs:
        return

    message = "\n".join(diffs[:50])
    if platform.system() == "Windows":
        sys.stderr.buffer.write((message + "\n").encode())
        raise AssertionError
    raise AssertionError(message)


if __name__ == "__main__":
    test()
