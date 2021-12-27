import json
import platform
import sys
import tempfile
from os.path import dirname

import bpy

sys.path.insert(0, dirname(dirname(__file__)))

# pylint: disable=wrong-import-position;
from io_scene_vrm.common import deep  # noqa: E402

# pylint: enable=wrong-import-position;


def test() -> None:
    bpy.ops.icyp.make_basic_armature()

    with tempfile.NamedTemporaryFile() as file:
        file.close()
        bpy.ops.vrm.save_human_bone_mappings(filepath=file.name)
        with open(file.name, "rb") as read_file:
            loaded_json = json.load(read_file)

    diffs = deep.diff(
        loaded_json,
        {
            "chest": "chest",
            "head": "head",
            "hips": "hips",
            "leftEye": "eye.L",
            "leftFoot": "foot.L",
            "leftHand": "hand.L",
            "leftIndexDistal": "index.distal.L",
            "leftIndexIntermediate": "index.intermediate.L",
            "leftIndexProximal": "index.proximal.L",
            "leftLittleDistal": "little.distal.L",
            "leftLittleIntermediate": "little.intermediate.L",
            "leftLittleProximal": "little.proximal.L",
            "leftLowerArm": "lower_arm.L",
            "leftLowerLeg": "lower_leg.L",
            "leftMiddleDistal": "middle.distal.L",
            "leftMiddleIntermediate": "middle.intermediate.L",
            "leftMiddleProximal": "middle.proximal.L",
            "leftRingDistal": "ring.distal.L",
            "leftRingIntermediate": "ring.intermediate.L",
            "leftRingProximal": "ring.proximal.L",
            "leftShoulder": "shoulder.L",
            "leftThumbDistal": "thumb.distal.L",
            "leftThumbIntermediate": "thumb.intermediate.L",
            "leftThumbProximal": "thumb.proximal.L",
            "leftToes": "toes.L",
            "leftUpperArm": "upper_arm.L",
            "leftUpperLeg": "upper_leg.L",
            "neck": "neck",
            "rightEye": "eye.R",
            "rightFoot": "foot.R",
            "rightHand": "hand.R",
            "rightIndexDistal": "index.distal.R",
            "rightIndexIntermediate": "index.intermediate.R",
            "rightIndexProximal": "index.proximal.R",
            "rightLittleDistal": "little.distal.R",
            "rightLittleIntermediate": "little.intermediate.R",
            "rightLittleProximal": "little.proximal.R",
            "rightLowerArm": "lower_arm.R",
            "rightLowerLeg": "lower_leg.R",
            "rightMiddleDistal": "middle.distal.R",
            "rightMiddleIntermediate": "middle.intermediate.R",
            "rightMiddleProximal": "middle.proximal.R",
            "rightRingDistal": "ring.distal.R",
            "rightRingIntermediate": "ring.intermediate.R",
            "rightRingProximal": "ring.proximal.R",
            "rightShoulder": "shoulder.R",
            "rightThumbDistal": "thumb.distal.R",
            "rightThumbIntermediate": "thumb.intermediate.R",
            "rightThumbProximal": "thumb.proximal.R",
            "rightToes": "toes.R",
            "rightUpperArm": "upper_arm.R",
            "rightUpperLeg": "upper_leg.R",
            "spine": "spine",
        },
    )
    if not diffs:
        return

    message = "\n".join(diffs)
    if platform.system() == "Windows":
        sys.stderr.buffer.write((message + "\n").encode())
        raise AssertionError
    raise AssertionError(message)


if __name__ == "__main__":
    test()
