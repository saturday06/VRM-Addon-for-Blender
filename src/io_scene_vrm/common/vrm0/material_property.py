# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum, auto
from typing import Final, Optional


class MaterialPropertyType(Enum):
    RGB = auto()
    RGBA = auto()
    UV_SCALE_TRANSLATION = auto()
    UV_SCALE = auto()
    UV_TRANSLATION = auto()


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

    @property
    def dimension(self) -> int:
        if self.type == MaterialPropertyType.RGBA:
            return 4
        if self.type == MaterialPropertyType.RGB:
            return 3
        if self.type == MaterialPropertyType.UV_SCALE_TRANSLATION:
            return 4
        if self.type == MaterialPropertyType.UV_SCALE:
            return 2
        if self.type == MaterialPropertyType.UV_TRANSLATION:
            return 2
        message = f"Unknown MaterialPropertyType: {self.type}"
        raise ValueError(message)


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
            MaterialPropertyType.UV_SCALE_TRANSLATION,
            MaterialPropertyTarget.MAIN_TEX,
        ),
        MaterialProperty(
            "_MainTex_ST_S",
            MaterialPropertyType.UV_SCALE,
            MaterialPropertyTarget.MAIN_TEX,
        ),
        MaterialProperty(
            "_MainTex_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
            MaterialPropertyTarget.MAIN_TEX,
        ),
        MaterialProperty(
            "_MetallicGlossMap_ST",
            MaterialPropertyType.UV_SCALE_TRANSLATION,
        ),
        MaterialProperty(
            "_MetallicGlossMap_ST_S",
            MaterialPropertyType.UV_SCALE,
        ),
        MaterialProperty(
            "_MetallicGlossMap_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
        ),
        MaterialProperty(
            "_BumpMap_ST",
            MaterialPropertyType.UV_SCALE_TRANSLATION,
            MaterialPropertyTarget.BUMP_MAP,
        ),
        MaterialProperty(
            "_BumpMap_ST_S",
            MaterialPropertyType.UV_SCALE,
            MaterialPropertyTarget.BUMP_MAP,
        ),
        MaterialProperty(
            "_BumpMap_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
            MaterialPropertyTarget.BUMP_MAP,
        ),
        MaterialProperty(
            "_ParallaxMap_ST",
            MaterialPropertyType.UV_SCALE_TRANSLATION,
        ),
        MaterialProperty(
            "_ParallaxMap_ST_S",
            MaterialPropertyType.UV_SCALE,
        ),
        MaterialProperty(
            "_ParallaxMap_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
        ),
        MaterialProperty(
            "_OcclusionMap_ST",
            MaterialPropertyType.UV_SCALE_TRANSLATION,
        ),
        MaterialProperty(
            "_OcclusionMap_ST_S",
            MaterialPropertyType.UV_SCALE,
        ),
        MaterialProperty(
            "_OcclusionMap_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
        ),
        MaterialProperty(
            "_EmissionColor",
            MaterialPropertyType.RGB,
            MaterialPropertyTarget.EMISSION_COLOR,
        ),
        MaterialProperty(
            "_EmissionMap_ST",
            MaterialPropertyType.UV_SCALE_TRANSLATION,
            MaterialPropertyTarget.EMISSION_MAP,
        ),
        MaterialProperty(
            "_EmissionMap_ST_S",
            MaterialPropertyType.UV_SCALE,
            MaterialPropertyTarget.EMISSION_MAP,
        ),
        MaterialProperty(
            "_EmissionMap_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
            MaterialPropertyTarget.EMISSION_MAP,
        ),
        MaterialProperty(
            "_DetailMask_ST",
            MaterialPropertyType.UV_SCALE_TRANSLATION,
        ),
        MaterialProperty(
            "_DetailMask_ST_S",
            MaterialPropertyType.UV_SCALE,
        ),
        MaterialProperty(
            "_DetailMask_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
        ),
        MaterialProperty(
            "_DetailAlbedoMap_ST",
            MaterialPropertyType.UV_SCALE_TRANSLATION,
        ),
        MaterialProperty(
            "_DetailAlbedoMap_ST_S",
            MaterialPropertyType.UV_SCALE,
        ),
        MaterialProperty(
            "_DetailAlbedoMap_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
        ),
        MaterialProperty(
            "_DetailNormalMap_ST",
            MaterialPropertyType.UV_SCALE_TRANSLATION,
        ),
        MaterialProperty(
            "_DetailNormalMap_ST_S",
            MaterialPropertyType.UV_SCALE,
        ),
        MaterialProperty(
            "_DetailNormalMap_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
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
            MaterialPropertyType.UV_SCALE_TRANSLATION,
            MaterialPropertyTarget.MAIN_TEX,
        ),
        MaterialProperty(
            "_MainTex_ST_S",
            MaterialPropertyType.UV_SCALE,
            MaterialPropertyTarget.MAIN_TEX,
        ),
        MaterialProperty(
            "_MainTex_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
            MaterialPropertyTarget.MAIN_TEX,
        ),
        MaterialProperty(
            "_ShadeTexture_ST",
            MaterialPropertyType.UV_SCALE_TRANSLATION,
            MaterialPropertyTarget.SHADE_TEXTURE,
        ),
        MaterialProperty(
            "_ShadeTexture_ST_S",
            MaterialPropertyType.UV_SCALE,
            MaterialPropertyTarget.SHADE_TEXTURE,
        ),
        MaterialProperty(
            "_ShadeTexture_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
            MaterialPropertyTarget.SHADE_TEXTURE,
        ),
        MaterialProperty(
            "_BumpMap_ST",
            MaterialPropertyType.UV_SCALE_TRANSLATION,
            MaterialPropertyTarget.BUMP_MAP,
        ),
        MaterialProperty(
            "_BumpMap_ST_S",
            MaterialPropertyType.UV_SCALE,
            MaterialPropertyTarget.BUMP_MAP,
        ),
        MaterialProperty(
            "_BumpMap_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
            MaterialPropertyTarget.BUMP_MAP,
        ),
        MaterialProperty(
            "_ReceiveShadowTexture_ST",
            MaterialPropertyType.UV_SCALE_TRANSLATION,
        ),
        MaterialProperty(
            "_ReceiveShadowTexture_ST_S",
            MaterialPropertyType.UV_SCALE,
        ),
        MaterialProperty(
            "_ReceiveShadowTexture_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
        ),
        MaterialProperty(
            "_ShadingGradeTexture_ST",
            MaterialPropertyType.UV_SCALE_TRANSLATION,
        ),
        MaterialProperty(
            "_ShadingGradeTexture_ST_S",
            MaterialPropertyType.UV_SCALE,
        ),
        MaterialProperty(
            "_ShadingGradeTexture_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
        ),
        MaterialProperty(
            "_RimColor",
            MaterialPropertyType.RGB,
            MaterialPropertyTarget.RIM_COLOR,
        ),
        MaterialProperty(
            "_RimTexture_ST",
            MaterialPropertyType.UV_SCALE_TRANSLATION,
            MaterialPropertyTarget.RIM_TEXTURE,
        ),
        MaterialProperty(
            "_RimTexture_ST_S",
            MaterialPropertyType.UV_SCALE,
            MaterialPropertyTarget.RIM_TEXTURE,
        ),
        MaterialProperty(
            "_RimTexture_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
            MaterialPropertyTarget.RIM_TEXTURE,
        ),
        MaterialProperty(
            "_SphereAdd_ST",
            MaterialPropertyType.UV_SCALE_TRANSLATION,
            MaterialPropertyTarget.SPHERE_ADD,
        ),
        MaterialProperty(
            "_SphereAdd_ST_S",
            MaterialPropertyType.UV_SCALE,
            MaterialPropertyTarget.SPHERE_ADD,
        ),
        MaterialProperty(
            "_SphereAdd_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
            MaterialPropertyTarget.SPHERE_ADD,
        ),
        MaterialProperty(
            "_EmissionColor",
            MaterialPropertyType.RGB,
            MaterialPropertyTarget.EMISSION_COLOR,
        ),
        MaterialProperty(
            "_EmissionMap_ST",
            MaterialPropertyType.UV_SCALE_TRANSLATION,
            MaterialPropertyTarget.EMISSION_MAP,
        ),
        MaterialProperty(
            "_EmissionMap_ST_S",
            MaterialPropertyType.UV_SCALE,
            MaterialPropertyTarget.EMISSION_MAP,
        ),
        MaterialProperty(
            "_EmissionMap_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
            MaterialPropertyTarget.EMISSION_MAP,
        ),
        MaterialProperty(
            "_OutlineWidthTexture_ST",
            MaterialPropertyType.UV_SCALE_TRANSLATION,
            MaterialPropertyTarget.OUTLINE_WIDTH_TEXTURE,
        ),
        MaterialProperty(
            "_OutlineWidthTexture_ST_S",
            MaterialPropertyType.UV_SCALE,
            MaterialPropertyTarget.OUTLINE_WIDTH_TEXTURE,
        ),
        MaterialProperty(
            "_OutlineWidthTexture_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
            MaterialPropertyTarget.OUTLINE_WIDTH_TEXTURE,
        ),
        MaterialProperty(
            "_OutlineColor",
            MaterialPropertyType.RGB,
            MaterialPropertyTarget.OUTLINE_COLOR,
        ),
        MaterialProperty(
            "_UvAnimMaskTexture_ST",
            MaterialPropertyType.UV_SCALE_TRANSLATION,
            MaterialPropertyTarget.UV_ANIM_MASK_TEXTURE,
        ),
        MaterialProperty(
            "_UvAnimMaskTexture_ST_S",
            MaterialPropertyType.UV_SCALE,
            MaterialPropertyTarget.UV_ANIM_MASK_TEXTURE,
        ),
        MaterialProperty(
            "_UvAnimMaskTexture_ST_T",
            MaterialPropertyType.UV_TRANSLATION,
            MaterialPropertyTarget.UV_ANIM_MASK_TEXTURE,
        ),
    )
}
