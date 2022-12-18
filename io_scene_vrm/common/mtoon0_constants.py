from typing import Dict, Optional


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


class MaterialMtoon0:
    # {key = MToonProp, val = ShaderNodeGroup_member_name}
    version = 32
    float_props_exchange_dict: Dict[str, Optional[str]] = {
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

    texture_kind_exchange_dict: Dict[str, str] = {
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
    vector_base_props_exchange_dict: Dict[str, str] = {
        "_Color": "DiffuseColor",
        "_ShadeColor": "ShadeColor",
        "_EmissionColor": "EmissionColor",
        "_RimColor": "RimColor",
        "_OutlineColor": "OutlineColor",
    }
    # texture offset and scaling props by texture
    vector_props_exchange_dict = {}
    vector_props_exchange_dict.update(vector_base_props_exchange_dict)
    vector_props_exchange_dict.update(texture_kind_exchange_dict)

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
