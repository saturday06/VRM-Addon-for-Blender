from typing import Dict

from ..vrm1.human_bone import HumanBoneSpecification, HumanBoneSpecifications

mapping: Dict[str, HumanBoneSpecification] = {
    "mixamorig:Head": HumanBoneSpecifications.HEAD,
    "mixamorig:Neck": HumanBoneSpecifications.NECK,
    "mixamorig:Spine2": HumanBoneSpecifications.UPPER_CHEST,
    "mixamorig:Spine1": HumanBoneSpecifications.CHEST,
    "mixamorig:Spine": HumanBoneSpecifications.SPINE,
    "mixamorig:Hips": HumanBoneSpecifications.HIPS,
    "mixamorig:RightShoulder": HumanBoneSpecifications.RIGHT_SHOULDER,
    "mixamorig:RightArm": HumanBoneSpecifications.RIGHT_UPPER_ARM,
    "mixamorig:RightForeArm": HumanBoneSpecifications.RIGHT_LOWER_ARM,
    "mixamorig:RightHand": HumanBoneSpecifications.RIGHT_HAND,
    "mixamorig:LeftShoulder": HumanBoneSpecifications.LEFT_SHOULDER,
    "mixamorig:LeftArm": HumanBoneSpecifications.LEFT_UPPER_ARM,
    "mixamorig:LeftForeArm": HumanBoneSpecifications.LEFT_LOWER_ARM,
    "mixamorig:LeftHand": HumanBoneSpecifications.LEFT_HAND,
    "mixamorig:RightUpLeg": HumanBoneSpecifications.RIGHT_UPPER_LEG,
    "mixamorig:RightLeg": HumanBoneSpecifications.RIGHT_LOWER_LEG,
    "mixamorig:RightFoot": HumanBoneSpecifications.RIGHT_FOOT,
    "mixamorig:RightToeBase": HumanBoneSpecifications.RIGHT_TOES,
    "mixamorig:LeftUpLeg": HumanBoneSpecifications.LEFT_UPPER_LEG,
    "mixamorig:LeftLeg": HumanBoneSpecifications.LEFT_LOWER_LEG,
    "mixamorig:LeftFoot": HumanBoneSpecifications.LEFT_FOOT,
    "mixamorig:LeftToeBase": HumanBoneSpecifications.LEFT_TOES,
    "mixamorig:RightHandThumb1": HumanBoneSpecifications.RIGHT_THUMB_METACARPAL,
    "mixamorig:RightHandThumb2": HumanBoneSpecifications.RIGHT_THUMB_PROXIMAL,
    "mixamorig:RightHandThumb3": HumanBoneSpecifications.RIGHT_THUMB_DISTAL,
    "mixamorig:RightHandIndex1": HumanBoneSpecifications.RIGHT_INDEX_PROXIMAL,
    "mixamorig:RightHandIndex2": HumanBoneSpecifications.RIGHT_INDEX_INTERMEDIATE,
    "mixamorig:RightHandIndex3": HumanBoneSpecifications.RIGHT_INDEX_DISTAL,
    "mixamorig:RightHandMiddle1": HumanBoneSpecifications.RIGHT_MIDDLE_PROXIMAL,
    "mixamorig:RightHandMiddle2": HumanBoneSpecifications.RIGHT_MIDDLE_INTERMEDIATE,
    "mixamorig:RightHandMiddle3": HumanBoneSpecifications.RIGHT_MIDDLE_DISTAL,
    "mixamorig:RightHandRing1": HumanBoneSpecifications.RIGHT_RING_PROXIMAL,
    "mixamorig:RightHandRing2": HumanBoneSpecifications.RIGHT_RING_INTERMEDIATE,
    "mixamorig:RightHandRing3": HumanBoneSpecifications.RIGHT_RING_DISTAL,
    "mixamorig:RightHandPinky1": HumanBoneSpecifications.RIGHT_LITTLE_PROXIMAL,
    "mixamorig:RightHandPinky2": HumanBoneSpecifications.RIGHT_LITTLE_INTERMEDIATE,
    "mixamorig:RightHandPinky3": HumanBoneSpecifications.RIGHT_LITTLE_DISTAL,
    "mixamorig:LeftHandThumb1": HumanBoneSpecifications.LEFT_THUMB_METACARPAL,
    "mixamorig:LeftHandThumb2": HumanBoneSpecifications.LEFT_THUMB_PROXIMAL,
    "mixamorig:LeftHandThumb3": HumanBoneSpecifications.LEFT_THUMB_DISTAL,
    "mixamorig:LeftHandIndex1": HumanBoneSpecifications.LEFT_INDEX_PROXIMAL,
    "mixamorig:LeftHandIndex2": HumanBoneSpecifications.LEFT_INDEX_INTERMEDIATE,
    "mixamorig:LeftHandIndex3": HumanBoneSpecifications.LEFT_INDEX_DISTAL,
    "mixamorig:LeftHandMiddle1": HumanBoneSpecifications.LEFT_MIDDLE_PROXIMAL,
    "mixamorig:LeftHandMiddle2": HumanBoneSpecifications.LEFT_MIDDLE_INTERMEDIATE,
    "mixamorig:LeftHandMiddle3": HumanBoneSpecifications.LEFT_MIDDLE_DISTAL,
    "mixamorig:LeftHandRing1": HumanBoneSpecifications.LEFT_RING_PROXIMAL,
    "mixamorig:LeftHandRing2": HumanBoneSpecifications.LEFT_RING_INTERMEDIATE,
    "mixamorig:LeftHandRing3": HumanBoneSpecifications.LEFT_RING_DISTAL,
    "mixamorig:LeftHandPinky1": HumanBoneSpecifications.LEFT_LITTLE_PROXIMAL,
    "mixamorig:LeftHandPinky2": HumanBoneSpecifications.LEFT_LITTLE_INTERMEDIATE,
    "mixamorig:LeftHandPinky3": HumanBoneSpecifications.LEFT_LITTLE_DISTAL,
}

config = ("Mixamo", mapping)
