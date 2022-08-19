import functools
from collections import abc
from typing import Any, List, Optional, Tuple

import bpy

from ...common import shader


class MaterialTraceablePropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    def find_material(self) -> bpy.types.Material:
        chain = getattr(self, "material_property_chain", None)
        if not isinstance(chain, abc.Sequence):
            raise NotImplementedError(
                f"No material material property chain: {type(self)}.{type(chain)}"
            )

        for material in bpy.data.materials:
            ext = material.vrm_addon_extension.mtoon1
            if functools.reduce(getattr, chain, ext) == self:
                return material

        raise Exception(f"No matching material: {type(self)} {chain}")

    def get_rgba(
        self,
        name: str,
        default_value: Optional[Tuple[float, float, float, float]] = None,
    ) -> Tuple[float, float, float, float]:
        if not default_value:
            default_value = (0, 0, 0, 0)
        node = self.find_material().node_tree.nodes.get(name)
        if not isinstance(node, bpy.types.ShaderNodeRGB):
            return default_value
        v = shader.rgba_or_none(node.outputs[0].default_value)
        if not v:
            return default_value
        return v

    def set_rgba(
        self,
        value: Any,
        name: str,
        default_value: Optional[Tuple[float, float, float, float]] = None,
    ) -> None:
        if not default_value:
            default_value = (0, 0, 0, 0)

        node = self.find_material().node_tree.nodes.get(name)
        if not isinstance(node, bpy.types.ShaderNodeRGB):
            return

        if not isinstance(value, abc.Iterable):
            node.outputs[0].default_value = default_value
            return

        value = list(value)
        if len(value) < 4:
            node.outputs[0].default_value = default_value
            return

        value = value[0:4]
        node.outputs[0].default_value = value

    def update_image(self, image: Optional[bpy.types.Image], name: str) -> None:
        node = self.find_material().node_tree.nodes.get(name)
        if not isinstance(node, bpy.types.ShaderNodeTexImage):
            return
        node.image = image


class Mtoon1KhrTextureTransformPropertyGroup(MaterialTraceablePropertyGroup):
    pass


class Mtoon1BaseColorKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        subtype="TRANSLATION",  # noqa: F821
        default=(0, 0),
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
    )


class Mtoon1ShadeMultiplyKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        subtype="TRANSLATION",  # noqa: F821
        default=(0, 0),
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
    )


class Mtoon1NormalKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        subtype="TRANSLATION",  # noqa: F821
        default=(0, 0),
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
    )


class Mtoon1ShadingShiftKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        subtype="TRANSLATION",  # noqa: F821
        default=(0, 0),
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
    )


class Mtoon1EmissiveKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        subtype="TRANSLATION",  # noqa: F821
        default=(0, 0),
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
    )


class Mtoon1RimMultiplyKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        subtype="TRANSLATION",  # noqa: F821
        default=(0, 0),
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
    )


class Mtoon1MatcapKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        subtype="TRANSLATION",  # noqa: F821
        default=(0, 0),
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
    )


class Mtoon1OutlineWidthMultiplyKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        subtype="TRANSLATION",  # noqa: F821
        default=(0, 0),
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
    )


class Mtoon1UvAnimationMaskKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        subtype="TRANSLATION",  # noqa: F821
        default=(0, 0),
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
    )


class Mtoon1BaseColorTextureInfoExtensionsPropertyGroup(
    bpy.types.PropertyGroup  # type: ignore[misc]
):
    khr_texture_transform: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1BaseColorKhrTextureTransformPropertyGroup  # noqa: F722
    )


class Mtoon1ShadeMultiplyTextureInfoExtensionsPropertyGroup(
    bpy.types.PropertyGroup  # type: ignore[misc]
):
    khr_texture_transform: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadeMultiplyKhrTextureTransformPropertyGroup  # noqa: F722
    )


class Mtoon1NormalTextureInfoExtensionsPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    khr_texture_transform: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1NormalKhrTextureTransformPropertyGroup  # noqa: F722
    )


class Mtoon1ShadingShiftTextureInfoExtensionsPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    khr_texture_transform: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadingShiftKhrTextureTransformPropertyGroup  # noqa: F722
    )


class Mtoon1EmissiveTextureInfoExtensionsPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    khr_texture_transform: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1EmissiveKhrTextureTransformPropertyGroup  # noqa: F722
    )


class Mtoon1RimMultiplyTextureInfoExtensionsPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    khr_texture_transform: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1RimMultiplyKhrTextureTransformPropertyGroup  # noqa: F722
    )


class Mtoon1MatcapTextureInfoExtensionsPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    khr_texture_transform: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MatcapKhrTextureTransformPropertyGroup  # noqa: F722
    )


class Mtoon1OutlineWidthMultiplyTextureInfoExtensionsPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    khr_texture_transform: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1OutlineWidthMultiplyKhrTextureTransformPropertyGroup  # noqa: F722
    )


class Mtoon1UvAnimationMaskTextureInfoExtensionsPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    khr_texture_transform: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1UvAnimationMaskKhrTextureTransformPropertyGroup  # noqa: F722
    )


class Mtoon1SamplerPropertyGroup(MaterialTraceablePropertyGroup):
    mag_filter_items = [
        ("NEAREST", "Nearest", "", 9728),
        ("LINEAR", "Linear", "", 9729),
    ]
    MAG_FILTER_NUMBER_TO_ID = {filter[-1]: filter[0] for filter in mag_filter_items}
    min_filter_items = [
        ("NEAREST", "Nearest", "", 9728),
        ("LINEAR", "Linear", "", 9729),
        (
            "NEAREST_MIPMAP_NEAREST",
            "Nearest Mipmap Nearest",
            "",
            9984,
        ),
        (
            "LINEAR_MIPMAP_NEAREST",
            "Linear Mipmap Nearest",
            "",
            9985,
        ),
        (
            "NEAREST_MIPMAP_LINEAR",
            "Nearest Mipmap Linear",
            "",
            9986,
        ),
        (
            "LINEAR_MIPMAP_LINEAR",
            "Linear Mipmap Linear",
            "",
            9987,
        ),
    ]
    MIN_FILTER_NUMBER_TO_ID = {filter[-1]: filter[0] for filter in min_filter_items}

    wrap_items = [
        ("CLAMP_TO_EDGE", "Clamp to Edge", "", 33071),
        ("MIRRORED_REPEAT", "Mirrored Repeat", "", 33648),
        ("REPEAT", "Repeat", "", 10497),
    ]
    WRAP_NUMBER_TO_ID = {wrap[-1]: wrap[0] for wrap in wrap_items}


class Mtoon1BaseColorSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items, name="Wrap S"  # noqa: F722
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items, name="Wrap T"  # noqa: F722
    )


class Mtoon1ShadeMultiplySamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items, name="Wrap S"  # noqa: F722
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items, name="Wrap T"  # noqa: F722
    )


class Mtoon1NormalSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items, name="Wrap S"  # noqa: F722
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items, name="Wrap T"  # noqa: F722
    )


class Mtoon1ShadingShiftSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items, name="Wrap S"  # noqa: F722
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items, name="Wrap T"  # noqa: F722
    )


class Mtoon1EmissiveSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items, name="Wrap S"  # noqa: F722
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items, name="Wrap T"  # noqa: F722
    )


class Mtoon1RimMultiplySamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items, name="Wrap S"  # noqa: F722
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items, name="Wrap T"  # noqa: F722
    )


class Mtoon1MatcapSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items, name="Wrap S"  # noqa: F722
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items, name="Wrap T"  # noqa: F722
    )


class Mtoon1OutlineWidthMultiplySamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items, name="Wrap S"  # noqa: F722
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items, name="Wrap T"  # noqa: F722
    )


class Mtoon1UvAnimationMaskSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items, name="Wrap S"  # noqa: F722
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items, name="Wrap T"  # noqa: F722
    )


class Mtoon1TexturePropertyGroup(MaterialTraceablePropertyGroup):
    pass


class Mtoon1BaseColorTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image  # noqa: F722
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1BaseColorSamplerPropertyGroup  # noqa: F722
    )


class Mtoon1ShadeMultiplyTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image  # noqa: F722
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadeMultiplySamplerPropertyGroup  # noqa: F722
    )


class Mtoon1NormalTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image  # noqa: F722
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1NormalSamplerPropertyGroup  # noqa: F722
    )


class Mtoon1ShadingShiftTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image  # noqa: F722
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadingShiftSamplerPropertyGroup  # noqa: F722
    )


class Mtoon1EmissiveTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image  # noqa: F722
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1EmissiveSamplerPropertyGroup  # noqa: F722
    )


class Mtoon1RimMultiplyTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image  # noqa: F722
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1RimMultiplySamplerPropertyGroup  # noqa: F722
    )


class Mtoon1MatcapTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image  # noqa: F722
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MatcapSamplerPropertyGroup  # noqa: F722
    )


class Mtoon1OutlineWidthMultiplyTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image  # noqa: F722
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1OutlineWidthMultiplySamplerPropertyGroup  # noqa: F722
    )


class Mtoon1UvAnimationMaskTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image  # noqa: F722
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1UvAnimationMaskSamplerPropertyGroup  # noqa: F722
    )


class Mtoon1TextureInfoPropertyGroup(MaterialTraceablePropertyGroup):
    pass


# https://github.com/KhronosGroup/glTF/blob/1ab49ec412e638f2e5af0289e9fbb60c7271e457/specification/2.0/schema/textureInfo.schema.json
class Mtoon1BaseColorTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1BaseColorTexturePropertyGroup  # noqa: F722
    )
    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1BaseColorTextureInfoExtensionsPropertyGroup  # noqa: F722
    )
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]


class Mtoon1ShadeMultiplyTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadeMultiplyTexturePropertyGroup  # noqa: F722
    )
    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadeMultiplyTextureInfoExtensionsPropertyGroup  # noqa: F722
    )
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]


# https://github.com/KhronosGroup/glTF/blob/1ab49ec412e638f2e5af0289e9fbb60c7271e457/specification/2.0/schema/material.normalTextureInfo.schema.json
class Mtoon1NormalTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1NormalTexturePropertyGroup  # noqa: F722
    )
    scale: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        default=1.0,
    )
    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1NormalTextureInfoExtensionsPropertyGroup  # noqa: F722
    )
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]


class Mtoon1ShadingShiftTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadingShiftTexturePropertyGroup  # noqa: F722
    )
    scale: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        default=1.0,
    )
    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadingShiftTextureInfoExtensionsPropertyGroup  # noqa: F722
    )
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]


# https://github.com/KhronosGroup/glTF/blob/1ab49ec412e638f2e5af0289e9fbb60c7271e457/specification/2.0/schema/textureInfo.schema.json
class Mtoon1EmissiveTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1EmissiveTexturePropertyGroup  # noqa: F722
    )
    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1EmissiveTextureInfoExtensionsPropertyGroup  # noqa: F722
    )
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]


class Mtoon1RimMultiplyTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1RimMultiplyTexturePropertyGroup  # noqa: F722
    )
    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1RimMultiplyTextureInfoExtensionsPropertyGroup  # noqa: F722
    )
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]


class Mtoon1MatcapTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MatcapTexturePropertyGroup  # noqa: F722
    )
    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MatcapTextureInfoExtensionsPropertyGroup  # noqa: F722
    )
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]


class Mtoon1OutlineWidthMultiplyTextureInfoPropertyGroup(
    Mtoon1TextureInfoPropertyGroup
):
    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1OutlineWidthMultiplyTexturePropertyGroup  # noqa: F722
    )
    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1OutlineWidthMultiplyTextureInfoExtensionsPropertyGroup  # noqa: F722
    )
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]


class Mtoon1UvAnimationMaskTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1UvAnimationMaskTexturePropertyGroup  # noqa: F722
    )
    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1UvAnimationMaskTextureInfoExtensionsPropertyGroup  # noqa: F722
    )
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]


# https://github.com/KhronosGroup/glTF/blob/1ab49ec412e638f2e5af0289e9fbb60c7271e457/specification/2.0/schema/material.pbrMetallicRoughness.schema.json#L9-L26
class Mtoon1PbrMetallicRoughnessPropertyGroup(MaterialTraceablePropertyGroup):
    material_property_chain = ["pbr_metallic_roughness"]

    def __get_base_color_factor(self) -> Tuple[float, float, float, float]:
        return self.get_rgba("pbrMetallicRoughness.baseColorFactor")

    def __set_base_color_factor(self, value: Any) -> None:
        self.set_rgba(value, "pbrMetallicRoughness.baseColorFactor")

    def __update_base_color_texture(self, _context: bpy.types.Context) -> None:
        self.update_image(
            self.base_color_texture, "pbrMetallicRoughness.baseColorTexture"
        )

    base_color_factor: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=4,
        subtype="COLOR",  # noqa: F821
        default=(0, 0, 0, 0),
        min=0,
        max=1,
        get=__get_base_color_factor,
        set=__set_base_color_factor,
    )

    base_color_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1BaseColorTextureInfoPropertyGroup,  # noqa: F722
        update=__update_base_color_texture,
    )


class Mtoon1MaterialVrmcMaterialsMtoonPropertyGroup(MaterialTraceablePropertyGroup):
    transparent_with_z_write: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Transparent With ZWrite Mode",  # noqa: F722
    )

    render_queue_offset_number: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="RenderQueue Offset", min=-9, max=9  # noqa: F722
    )

    shade_multiply_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadeMultiplyTextureInfoPropertyGroup  # noqa: F722
    )

    shade_color_factor: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="COLOR",  # noqa: F821
        default=(0, 0, 0),
        min=0,
        max=1,
    )

    shading_shift_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadingShiftTextureInfoPropertyGroup  # noqa: F722
    )

    shading_shift_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Shading Shift",  # noqa: F722
        soft_min=-1,
        soft_max=1,
    )

    shading_toony_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Shading Toony",  # noqa: F722
        soft_min=0,
        default=0.9,
        soft_max=1,
    )

    gi_equalization_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="GI Equalization",  # noqa: F722
        soft_min=0,
        default=0.9,
        soft_max=1,
    )

    matcap_factor: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="COLOR",  # noqa: F821
        default=(0, 0, 0),
        min=0,
        max=1,
    )

    parametric_rim_color_factor: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Parametric Rim Color",  # noqa: F722
        size=3,
        subtype="COLOR",  # noqa: F821
        default=(0, 0, 0),
        min=0,
        max=1,
    )

    matcap_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MatcapTextureInfoPropertyGroup  # noqa: F722
    )

    outline_width_multiply_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1OutlineWidthMultiplyTextureInfoPropertyGroup  # noqa: F722
    )

    rim_lighting_mix_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Rim LightingMix",  # noqa: F722
        soft_min=0,
        soft_max=1,
    )

    rim_multiply_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1RimMultiplyTextureInfoPropertyGroup  # noqa: F722
    )

    parametric_rim_fresnel_power_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Parametric Rim Fresnel Power",  # noqa: F722
        soft_min=0,
        default=1.0,
        soft_max=100,
    )

    parametric_rim_lift_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Parametric Rim Lift",  # noqa: F722
        soft_min=0,
        soft_max=1,
    )

    OUTLINE_WIDTH_MODE_NONE = "none"
    outline_width_mode_items = [
        (OUTLINE_WIDTH_MODE_NONE, "None", ""),
        ("worldCoordinates", "World Coordinates", ""),
        ("screenCoordinates", "Screen Coordinates", ""),
    ]
    OUTLINE_WIDTH_MODE_IDS = [
        outline_width_mode_item[0]
        for outline_width_mode_item in outline_width_mode_items
    ]

    outline_width_mode: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=outline_width_mode_items, name="Outline Width Mode"  # noqa: F722
    )

    outline_width_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Outline Width",  # noqa: F722
        soft_min=0,
        soft_max=0.05,
    )

    outline_color_factor: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Outline Color",  # noqa: F722
        size=3,
        subtype="COLOR",  # noqa: F821
        default=(0, 0, 0),
        min=0,
        max=1,
    )

    outline_lighting_mix_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Outline LightingMix",  # noqa: F722
        soft_min=0,
        soft_max=1,
    )

    uv_animation_mask_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1UvAnimationMaskTextureInfoPropertyGroup  # noqa: F722
    )

    uv_animation_scroll_x_speed_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Translate X"  # noqa: F722
    )

    uv_animation_scroll_y_speed_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Translate Y"  # noqa: F722
    )

    uv_animation_rotation_speed_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Rotation"  # noqa: F821
    )


class Mtoon1MaterialExtensionsPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    vrmc_materials_mtoon: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MaterialVrmcMaterialsMtoonPropertyGroup  # noqa: F722
    )


# https://github.com/vrm-c/vrm-specification/blob/8dc51ec7241be27ee95f159cefc0190a0e41967b/specification/VRMC_materials_mtoon-1.0-beta/schema/VRMC_materials_mtoon.schema.json
class Mtoon1MaterialPropertyGroup(MaterialTraceablePropertyGroup):
    material_property_chain: List[str] = []

    pbr_metallic_roughness: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1PbrMetallicRoughnessPropertyGroup  # noqa: F722
    )

    ALPHA_MODE_OPAQUE = "OPAQUE"
    ALPHA_MODE_OPAQUE_VALUE = 0
    ALPHA_MODE_MASK = "CUTOUT"
    ALPHA_MODE_MASK_VALUE = 1
    ALPHA_MODE_BLEND = "TRANSPARENT"
    ALPHA_MODE_BLEND_VALUE = 2
    alpha_mode_items = [
        (ALPHA_MODE_OPAQUE, "Opaque", "", "NONE", ALPHA_MODE_OPAQUE_VALUE),
        (ALPHA_MODE_MASK, "Cutout", "", "NONE", ALPHA_MODE_MASK_VALUE),
        (ALPHA_MODE_BLEND, "Transparent", "", "NONE", ALPHA_MODE_BLEND_VALUE),
    ]
    ALPHA_MODE_IDS = [alpha_mode_item[0] for alpha_mode_item in alpha_mode_items]

    alpha_mode_blend_method_hashed: bpy.props.BoolProperty()  # type: ignore[valid-type]

    def __get_alpha_mode(self) -> int:
        # https://docs.blender.org/api/2.93/bpy.types.Material.html#bpy.types.Material.blend_method
        blend_method = self.find_material().blend_method
        if blend_method == "OPAQUE":
            return self.ALPHA_MODE_OPAQUE_VALUE
        if blend_method == "CLIP":
            return self.ALPHA_MODE_MASK_VALUE
        if blend_method in ["HASHED", "BLEND"]:
            return self.ALPHA_MODE_BLEND_VALUE
        raise Exception(f"Unexpected blend_method: {blend_method}")

    def __set_alpha_mode(self, value: int) -> None:
        material = self.find_material()
        if material.blend_method == "HASHED":
            self.alpha_mode_blend_method_hashed = True
        if material.blend_method == "BLEND":
            self.alpha_mode_blend_method_hashed = False

        if value == self.ALPHA_MODE_OPAQUE_VALUE:
            material.blend_method = "OPAQUE"
        elif value == self.ALPHA_MODE_MASK_VALUE:
            material.blend_method = "CLIP"
        elif value == self.ALPHA_MODE_BLEND_VALUE:
            material.blend_method = "BLEND"
        else:
            print("Unexpected alpha mode: {value}")
            material.blend_method = "OPAQUE"

    alpha_mode: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=alpha_mode_items,
        name="Alpha Mode",  # noqa: F722
        get=__get_alpha_mode,
        set=__set_alpha_mode,
    )

    def __get_double_sided(self) -> bool:
        return not self.find_material().use_backface_culling

    def __set_double_sided(self, value: bool) -> None:
        self.find_material().use_backface_culling = not value

    double_sided: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Double Sided",  # noqa: F722
        get=__get_double_sided,
        set=__set_double_sided,
    )

    def __get_alpha_cutoff(self) -> float:
        return max(0, min(1, float(self.find_material().alpha_threshold)))

    def __set_alpha_cutoff(self, value: float) -> None:
        self.find_material().alpha_threshold = max(0, min(1, value))

    alpha_cutoff: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Cutoff",  # noqa: F821
        min=0,
        max=1,
        get=__get_alpha_cutoff,
        set=__set_alpha_cutoff,
    )

    normal_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1NormalTextureInfoPropertyGroup  # noqa: F722
    )

    emissive_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1EmissiveTextureInfoPropertyGroup  # noqa: F722
    )

    emissive_factor: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="COLOR",  # noqa: F821
        default=(0, 0, 0),
        min=0,
        max=1,
    )

    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MaterialExtensionsPropertyGroup  # noqa: F722
    )

    def __get_enabled(self) -> bool:
        material = self.find_material()
        if not material.use_nodes:
            return False
        return bool(self.get("enabled"))

    def __set_enabled(self, value: bool) -> None:
        material = self.find_material()

        if not value:
            if self.get("enabled") and material.use_nodes:
                material.node_tree.links.clear()
                material.node_tree.nodes.clear()
                material.node_tree.inputs.clear()
                material.node_tree.outputs.clear()
                shader_node = material.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
                output_node = material.node_tree.nodes.new("ShaderNodeOutputMaterial")
                material.node_tree.links.new(
                    output_node.inputs["Surface"], shader_node.outputs["BSDF"]
                )
            self["enabled"] = False
            return

        if not material.use_nodes:
            material.use_nodes = True
        if self.get("enabled"):
            return

        shader.load_mtoon1_shader(material)

        self["enabled"] = True

    enabled: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Use VRM Material",  # noqa: F722
        get=__get_enabled,
        set=__set_enabled,
    )
