# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum, auto
from typing import Final, Optional


class MaterialPropertyType(Enum):
    RGB = auto()
    RGBA = auto()
    UV = auto()
    UV_S = auto()
    UV_T = auto()


class MaterialPropertyTarget(Enum):
    COLOR = auto()
    SHADE_COLOR = auto()
    MAIN_TEX = auto()
    SHADE_TEXTURE = auto()
    BUMP_MAP = auto()
    RIM_COLOR = auto()
    RIM_TEXTURE = auto()
    SPHERE_ADD = auto()
    EMISSION_COLOR = auto()
    EMISSION_MAP = auto()
    OUTLINE_WIDTH_TEXTURE = auto()
    OUTLINE_COLOR = auto()
    UV_ANIM_MASK_TEXTURE = auto()


@dataclass(frozen=True)
class MaterialProperty:
    name: str
    type: Optional[MaterialPropertyType]
    target: Optional[MaterialPropertyTarget] = None


GLTF_PROPERTIES: Final[Mapping[str, MaterialProperty]] = {
    material_property.name: material_property
    for material_property in (
        MaterialProperty(
            "_Color",
            MaterialPropertyType.RGBA,
            MaterialPropertyTarget.COLOR,
        ),
        MaterialProperty(
            "_MainTex_ST",
            MaterialPropertyType.UV,
            MaterialPropertyTarget.MAIN_TEX,
        ),
        MaterialProperty(
            "_MainTex_ST_S",
            MaterialPropertyType.UV_S,
            MaterialPropertyTarget.MAIN_TEX,
        ),
        MaterialProperty(
            "_MainTex_ST_T",
            MaterialPropertyType.UV_T,
            MaterialPropertyTarget.MAIN_TEX,
        ),
        MaterialProperty(
            "_MetallicGlossMap_ST",
            MaterialPropertyType.UV,
        ),
        MaterialProperty(
            "_MetallicGlossMap_ST_S",
            MaterialPropertyType.UV_S,
        ),
        MaterialProperty(
            "_MetallicGlossMap_ST_T",
            MaterialPropertyType.UV_T,
        ),
        MaterialProperty(
            "_BumpMap_ST",
            MaterialPropertyType.UV,
            MaterialPropertyTarget.BUMP_MAP,
        ),
        MaterialProperty(
            "_BumpMap_ST_S",
            MaterialPropertyType.UV_S,
            MaterialPropertyTarget.BUMP_MAP,
        ),
        MaterialProperty(
            "_BumpMap_ST_T",
            MaterialPropertyType.UV_T,
            MaterialPropertyTarget.BUMP_MAP,
        ),
        MaterialProperty(
            "_ParallaxMap_ST",
            MaterialPropertyType.UV,
        ),
        MaterialProperty(
            "_ParallaxMap_ST_S",
            MaterialPropertyType.UV_S,
        ),
        MaterialProperty(
            "_ParallaxMap_ST_T",
            MaterialPropertyType.UV_T,
        ),
        MaterialProperty(
            "_OcclusionMap_ST",
            MaterialPropertyType.UV,
        ),
        MaterialProperty(
            "_OcclusionMap_ST_S",
            MaterialPropertyType.UV_S,
        ),
        MaterialProperty(
            "_OcclusionMap_ST_T",
            MaterialPropertyType.UV_T,
        ),
        MaterialProperty(
            "_EmissionColor",
            MaterialPropertyType.RGB,
            MaterialPropertyTarget.EMISSION_COLOR,
        ),
        MaterialProperty(
            "_EmissionMap_ST",
            MaterialPropertyType.UV,
            MaterialPropertyTarget.EMISSION_MAP,
        ),
        MaterialProperty(
            "_EmissionMap_ST_S",
            MaterialPropertyType.UV_S,
            MaterialPropertyTarget.EMISSION_MAP,
        ),
        MaterialProperty(
            "_EmissionMap_ST_T",
            MaterialPropertyType.UV_T,
            MaterialPropertyTarget.EMISSION_MAP,
        ),
        MaterialProperty(
            "_DetailMask_ST",
            MaterialPropertyType.UV,
        ),
        MaterialProperty(
            "_DetailMask_ST_S",
            MaterialPropertyType.UV_S,
        ),
        MaterialProperty(
            "_DetailMask_ST_T",
            MaterialPropertyType.UV_T,
        ),
        MaterialProperty(
            "_DetailAlbedoMap_ST",
            MaterialPropertyType.UV,
        ),
        MaterialProperty(
            "_DetailAlbedoMap_ST_S",
            MaterialPropertyType.UV_S,
        ),
        MaterialProperty(
            "_DetailAlbedoMap_ST_T",
            MaterialPropertyType.UV_T,
        ),
        MaterialProperty(
            "_DetailNormalMap_ST",
            MaterialPropertyType.UV,
        ),
        MaterialProperty(
            "_DetailNormalMap_ST_S",
            MaterialPropertyType.UV_S,
        ),
        MaterialProperty(
            "_DetailNormalMap_ST_T",
            MaterialPropertyType.UV_T,
        ),
    )
}

MTOON0_PROPERTIES: Final[Mapping[str, MaterialProperty]] = {
    material_property.name: material_property
    for material_property in (
        MaterialProperty(
            "_Color",
            MaterialPropertyType.RGBA,
            MaterialPropertyTarget.COLOR,
        ),
        MaterialProperty(
            "_ShadeColor",
            MaterialPropertyType.RGB,
            MaterialPropertyTarget.SHADE_COLOR,
        ),
        MaterialProperty(
            "_MainTex_ST",
            MaterialPropertyType.UV,
            MaterialPropertyTarget.MAIN_TEX,
        ),
        MaterialProperty(
            "_MainTex_ST_S",
            MaterialPropertyType.UV_S,
            MaterialPropertyTarget.MAIN_TEX,
        ),
        MaterialProperty(
            "_MainTex_ST_T",
            MaterialPropertyType.UV_T,
            MaterialPropertyTarget.MAIN_TEX,
        ),
        MaterialProperty(
            "_ShadeTexture_ST",
            MaterialPropertyType.UV,
            MaterialPropertyTarget.SHADE_TEXTURE,
        ),
        MaterialProperty(
            "_ShadeTexture_ST_S",
            MaterialPropertyType.UV_S,
            MaterialPropertyTarget.SHADE_TEXTURE,
        ),
        MaterialProperty(
            "_ShadeTexture_ST_T",
            MaterialPropertyType.UV_T,
            MaterialPropertyTarget.SHADE_TEXTURE,
        ),
        MaterialProperty(
            "_BumpMap_ST",
            MaterialPropertyType.UV,
            MaterialPropertyTarget.BUMP_MAP,
        ),
        MaterialProperty(
            "_BumpMap_ST_S",
            MaterialPropertyType.UV_S,
            MaterialPropertyTarget.BUMP_MAP,
        ),
        MaterialProperty(
            "_BumpMap_ST_T",
            MaterialPropertyType.UV_T,
            MaterialPropertyTarget.BUMP_MAP,
        ),
        MaterialProperty(
            "_ReceiveShadowTexture_ST",
            MaterialPropertyType.UV,
        ),
        MaterialProperty(
            "_ReceiveShadowTexture_ST_S",
            MaterialPropertyType.UV_S,
        ),
        MaterialProperty(
            "_ReceiveShadowTexture_ST_T",
            MaterialPropertyType.UV_T,
        ),
        MaterialProperty(
            "_ShadingGradeTexture_ST",
            MaterialPropertyType.UV,
        ),
        MaterialProperty(
            "_ShadingGradeTexture_ST_S",
            MaterialPropertyType.UV_S,
        ),
        MaterialProperty(
            "_ShadingGradeTexture_ST_T",
            MaterialPropertyType.UV_T,
        ),
        MaterialProperty(
            "_RimColor",
            MaterialPropertyType.RGB,
            MaterialPropertyTarget.RIM_COLOR,
        ),
        MaterialProperty(
            "_RimTexture_ST",
            MaterialPropertyType.UV,
            MaterialPropertyTarget.RIM_TEXTURE,
        ),
        MaterialProperty(
            "_RimTexture_ST_S",
            MaterialPropertyType.UV_S,
            MaterialPropertyTarget.RIM_TEXTURE,
        ),
        MaterialProperty(
            "_RimTexture_ST_T",
            MaterialPropertyType.UV_T,
            MaterialPropertyTarget.RIM_TEXTURE,
        ),
        MaterialProperty(
            "_SphereAdd_ST",
            MaterialPropertyType.UV,
            MaterialPropertyTarget.SPHERE_ADD,
        ),
        MaterialProperty(
            "_SphereAdd_ST_S",
            MaterialPropertyType.UV_S,
            MaterialPropertyTarget.SPHERE_ADD,
        ),
        MaterialProperty(
            "_SphereAdd_ST_T",
            MaterialPropertyType.UV_T,
            MaterialPropertyTarget.SPHERE_ADD,
        ),
        MaterialProperty(
            "_EmissionColor",
            MaterialPropertyType.RGB,
            MaterialPropertyTarget.EMISSION_COLOR,
        ),
        MaterialProperty(
            "_EmissionMap_ST",
            MaterialPropertyType.UV,
            MaterialPropertyTarget.EMISSION_MAP,
        ),
        MaterialProperty(
            "_EmissionMap_ST_S",
            MaterialPropertyType.UV_S,
            MaterialPropertyTarget.EMISSION_MAP,
        ),
        MaterialProperty(
            "_EmissionMap_ST_T",
            MaterialPropertyType.UV_T,
            MaterialPropertyTarget.EMISSION_MAP,
        ),
        MaterialProperty(
            "_OutlineWidthTexture_ST",
            MaterialPropertyType.UV,
            MaterialPropertyTarget.OUTLINE_WIDTH_TEXTURE,
        ),
        MaterialProperty(
            "_OutlineWidthTexture_ST_S",
            MaterialPropertyType.UV_S,
            MaterialPropertyTarget.OUTLINE_WIDTH_TEXTURE,
        ),
        MaterialProperty(
            "_OutlineWidthTexture_ST_T",
            MaterialPropertyType.UV_T,
            MaterialPropertyTarget.OUTLINE_WIDTH_TEXTURE,
        ),
        MaterialProperty(
            "_OutlineColor",
            MaterialPropertyType.RGB,
            MaterialPropertyTarget.OUTLINE_COLOR,
        ),
        MaterialProperty(
            "_UvAnimMaskTexture_ST",
            MaterialPropertyType.UV,
            MaterialPropertyTarget.UV_ANIM_MASK_TEXTURE,
        ),
        MaterialProperty(
            "_UvAnimMaskTexture_ST_S",
            MaterialPropertyType.UV_S,
            MaterialPropertyTarget.UV_ANIM_MASK_TEXTURE,
        ),
        MaterialProperty(
            "_UvAnimMaskTexture_ST_T",
            MaterialPropertyType.UV_T,
            MaterialPropertyTarget.UV_ANIM_MASK_TEXTURE,
        ),
    )
}
