# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import json
import sys
import tempfile
from pathlib import Path

from io_scene_vrm.common import deep, ops


def test() -> None:
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


if __name__ == "__main__":
    test()
