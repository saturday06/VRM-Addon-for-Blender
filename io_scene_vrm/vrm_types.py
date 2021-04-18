"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

from typing import Any, Dict, List, Optional, Union


class Gltf:
    TEXTURE_INPUT_NAMES = [
        "color_texture",
        "normal",
        "emissive_texture",
        "occlusion_texture",
    ]
    VAL_INPUT_NAMES = ["metallic", "roughness", "unlit"]
    RGBA_INPUT_NAMES = ["base_Color", "emissive_color"]


class Vrm0:
    METAS = [
        "version",  # model version (not VRMspec etc)
        "author",
        "contactInformation",
        "reference",
        "title",
        "otherPermissionUrl",
        "otherLicenseUrl",
    ]
    REQUIRED_METAS = {
        "allowedUserName": "OnlyAuthor",
        "violentUssageName": "Disallow",
        "sexualUssageName": "Disallow",
        "commercialUssageName": "Disallow",
        "licenseName": "Redistribution_Prohibited",
    }
    HUMANOID_DEFAULT_PARAMS: Dict[str, Union[float, bool]] = {
        "armStretch": 0.05,
        "legStretch": 0.05,
        "upperArmTwist": 0.5,
        "lowerArmTwist": 0.5,
        "upperLegTwist": 0.5,
        "lowerLegTwist": 0.5,
        "feetSpacing": 0,
        "hasTranslationDoF": False,
    }
    FIRST_PERSON_DEFAULT_LOOK_AT_PARAMS = {
        "curve": [0, 0, 0, 1, 1, 1, 1, 0],
        "xRange": 90,
        "yRange": 10,
    }
    FIRST_PERSON_DEFAULT_PARAMS: Dict[str, Any] = {
        "firstPersonBone": -1,
        "firstPersonBoneOffset": {"x": 0, "y": 0.06, "z": 0},
        "lookAtHorizontalInner": FIRST_PERSON_DEFAULT_LOOK_AT_PARAMS,
        "lookAtHorizontalOuter": FIRST_PERSON_DEFAULT_LOOK_AT_PARAMS,
        "lookAtTypeName": "Bone",
        "lookAtVerticalDown": FIRST_PERSON_DEFAULT_LOOK_AT_PARAMS,
        "lookAtVerticalUp": FIRST_PERSON_DEFAULT_LOOK_AT_PARAMS,
        "meshAnnotations": [],
    }


class Vrm1:
    METAS: List[str] = []
    REQUIRED_METAS: Dict[str, str] = {}


class HumanBones:
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


class MaterialTransparentZWrite:
    float_props = [
        "_MainTex",
        "_Cutoff",
        "_BlendMode",
        "_CullMode",
        "_VColBlendMode",
        "_SrcBlend",
        "_DstBlend",
        "_ZWrite",
    ]
    texture_index_list = ["_MainTex"]
    vector_props = ["_Color"]


class MaterialMtoon:
    # {key = MToonProp, val = ShaderNodeGroup_member_name}
    version = 32
    float_props_exchange_dic: Dict[str, Optional[str]] = {
        "_MToonVersion": None,
        "_Cutoff": "CutoffRate",
        "_BumpScale": "BumpScale",
        "_ReceiveShadowRate": "ReceiveShadowRate",
        "_ShadeShift": "ShadeShift",
        "_ShadeToony": "ShadeToony",
        "_RimLightingMix": "RimLightingMix",
        "_RimFresnelPower": "RimFresnelPower",
        "_RimLift": "RimLift",
        "_ShadingGradeRate": "ShadingGradeRate",
        "_LightColorAttenuation": "LightColorAttenuation",
        "_IndirectLightIntensity": "IndirectLightIntensity",
        "_OutlineWidth": "OutlineWidth",
        "_OutlineScaledMaxDistance": "OutlineScaleMaxDistance",
        "_OutlineLightingMix": "OutlineLightingMix",
        "_UvAnimScrollX": "UV_Scroll_X",  # TODO #####
        "_UvAnimScrollY": "UV_Scroll_Y",  # TODO #####
        "_UvAnimRotation": "UV_Scroll_Rotation",  # TODO #####
        "_DebugMode": None,
        "_BlendMode": None,
        "_OutlineWidthMode": "OutlineWidthMode",
        "_OutlineColorMode": "OutlineColorMode",
        "_CullMode": None,
        "_OutlineCullMode": None,
        "_SrcBlend": None,
        "_DstBlend": None,
        "_ZWrite": None,
        "_IsFirstSetup": None,
    }

    texture_kind_exchange_dic: Dict[str, str] = {
        "_MainTex": "MainTexture",
        "_ShadeTexture": "ShadeTexture",
        "_BumpMap": "NormalmapTexture",
        "_ReceiveShadowTexture": "ReceiveShadow_Texture",
        "_ShadingGradeTexture": "ShadingGradeTexture",
        "_EmissionMap": "Emission_Texture",
        "_SphereAdd": "SphereAddTexture",
        "_RimTexture": "RimTexture",
        "_OutlineWidthTexture": "OutlineWidthTexture",
        "_UvAnimMaskTexture": "UV_Animation_Mask_Texture",  # TODO ####
    }
    vector_base_props_exchange_dic: Dict[str, str] = {
        "_Color": "DiffuseColor",
        "_ShadeColor": "ShadeColor",
        "_EmissionColor": "EmissionColor",
        "_RimColor": "RimColor",
        "_OutlineColor": "OutlineColor",
    }
    # texture offset and scaling props by texture
    vector_props_exchange_dic = {}
    vector_props_exchange_dic.update(vector_base_props_exchange_dic)
    vector_props_exchange_dic.update(texture_kind_exchange_dic)

    keyword_list = [
        "_NORMALMAP",
        "_ALPHATEST_ON",
        "_ALPHABLEND_ON",
        "_ALPHAPREMULTIPLY_ON",
        "MTOON_OUTLINE_WIDTH_WORLD",
        "MTOON_OUTLINE_WIDTH_SCREEN",
        "MTOON_OUTLINE_COLOR_FIXED",
        "MTOON_OUTLINE_COLOR_MIXED",
        "MTOON_DEBUG_NORMAL",
        "MTOON_DEBUG_LITSHADERATE",
    ]
    tagmap_list = ["RenderType"]


if __name__ == "__main__":
    pass
