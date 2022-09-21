import functools
from collections import abc
from sys import float_info
from typing import Any, List, Optional, Tuple, Union

import bpy

from ...common import shader
from ...common.logging import get_logger

logger = get_logger(__name__)


class MaterialTraceablePropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    def find_material(self) -> bpy.types.Material:
        chain = getattr(self, "material_property_chain", None)
        if not isinstance(chain, abc.Sequence):
            raise NotImplementedError(
                f"No material property chain: {type(self)}.{type(chain)} => {chain}"
            )

        for material in bpy.data.materials:
            ext = material.vrm_addon_extension.mtoon1
            if functools.reduce(getattr, chain, ext) == self:
                return material

        raise RuntimeError(f"No matching material: {type(self)} {chain}")

    def get_value(
        self,
        name: str,
        default_value: Union[int, float] = 0,
    ) -> Union[int, float]:
        node = self.find_material().node_tree.nodes.get(name)
        if not isinstance(node, bpy.types.ShaderNodeValue):
            return default_value
        v = node.outputs[0].default_value
        if not isinstance(v, (int, float)):
            return default_value
        return v

    def set_value(
        self,
        name: str,
        value: Any,
    ) -> None:
        if not isinstance(value, (int, float)):
            return
        node = self.find_material().node_tree.nodes.get(name)
        if not isinstance(node, bpy.types.ShaderNodeValue):
            return
        node.outputs[0].default_value = value

    def get_bool(
        self,
        name: str,
        default_value: bool = False,
    ) -> bool:
        v = self.get_value(name, 1 if default_value else 0)
        return abs(v) >= float_info.epsilon

    def set_bool(
        self,
        name: str,
        value: Any,
    ) -> None:
        self.set_value(name, 1 if value else 0)

    def get_int(
        self,
        name: str,
        default_value: int = 0,
    ) -> int:
        return int(self.get_value(name, default_value))

    def set_int(
        self,
        name: str,
        value: Any,
    ) -> None:
        self.set_value(name, value)

    def get_rgba(
        self,
        name: str,
        default_value: Optional[Tuple[float, float, float, float]] = None,
    ) -> Tuple[float, float, float, float]:
        if not default_value:
            default_value = (0.0, 0.0, 0.0, 0.0)
        node = self.find_material().node_tree.nodes.get(name)
        if not isinstance(node, bpy.types.ShaderNodeRGB):
            return default_value
        v = shader.rgba_or_none(node.outputs[0].default_value)
        if not v:
            return default_value
        return v

    def set_rgba(
        self,
        name: str,
        value: Any,
        default_value: Optional[Tuple[float, float, float, float]] = None,
    ) -> None:
        if not default_value:
            default_value = (0.0, 0.0, 0.0, 0.0)
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

    def get_rgb(
        self,
        name: str,
        default_value: Optional[Tuple[float, float, float]] = None,
    ) -> Tuple[float, float, float]:
        if not default_value:
            default_value = (0.0, 0.0, 0.0)
        node = self.find_material().node_tree.nodes.get(name)
        if not isinstance(node, bpy.types.ShaderNodeRGB):
            return default_value
        v = shader.rgb_or_none(node.outputs[0].default_value)
        if not v:
            return default_value
        return v

    def set_rgb(
        self,
        name: str,
        value: Any,
        default_value: Optional[Tuple[float, float, float]] = None,
    ) -> None:
        if not default_value:
            default_value = (0.0, 0.0, 0.0)
        node = self.find_material().node_tree.nodes.get(name)
        if not isinstance(node, bpy.types.ShaderNodeRGB):
            return
        if not isinstance(value, abc.Iterable):
            node.outputs[0].default_value = default_value + (1.0,)
            return
        value = list(value)
        if len(value) < 3:
            node.outputs[0].default_value = default_value + (1.0,)
            return
        value = value[0:3]
        value.append(1.0)
        node.outputs[0].default_value = value

    def get_source_node_name(self) -> str:
        name = getattr(self, "source_node_name", None)
        if not isinstance(name, str):
            raise NotImplementedError(
                f"No source node name: {type(self)}.{type(name)} => {name}"
            )
        return name

    def update_image(self, image: Optional[bpy.types.Image]) -> None:
        node = self.find_material().node_tree.nodes.get(self.get_source_node_name())
        if not isinstance(node, bpy.types.ShaderNodeTexImage):
            return
        node.image = image
        self.refresh_image_node_links()

    def refresh_image_node_links(self) -> None:
        node_tree = self.find_material().node_tree
        nodes = node_tree.nodes
        node = nodes.get(self.get_source_node_name())
        if not isinstance(node, bpy.types.ShaderNodeTexImage):
            return

        color_target_node = nodes.get(self.get_source_node_name() + "ColorTarget")
        if isinstance(color_target_node, bpy.types.NodeReroute):
            color_socket = node.outputs[0]
            color_target_node_socket = color_target_node.inputs[0]
            color_link = {
                0: link
                for link in node_tree.links
                if link.to_socket == color_target_node_socket
                and link.from_socket == color_socket
            }.get(0)
            if node.image:
                if not color_link:
                    node_tree.links.new(color_target_node_socket, color_socket)
            else:
                if color_link:
                    node_tree.links.remove(color_link)

        alpha_target_node = nodes.get(self.get_source_node_name() + "AlphaTarget")
        if isinstance(alpha_target_node, bpy.types.NodeReroute):
            alpha_socket = node.outputs[1]
            alpha_target_node_socket = alpha_target_node.inputs[0]
            alpha_link = {
                0: link
                for link in node_tree.links
                if link.to_socket == alpha_target_node_socket
                and link.from_socket == alpha_socket
            }.get(0)
            if node.image:
                if not alpha_link:
                    node_tree.links.new(alpha_target_node_socket, alpha_socket)
            else:
                if alpha_link:
                    node_tree.links.remove(alpha_link)

    def get_texture_offset(
        self,
        name: str,
    ) -> Tuple[float, float]:
        node = self.find_material().node_tree.nodes.get(name)
        if not isinstance(node, bpy.types.ShaderNodeTexImage):
            return (0, 0)
        return (
            node.texture_mapping.translation[0],
            node.texture_mapping.translation[1],
        )

    def set_texture_offset(
        self,
        name: str,
        value: Any,
    ) -> None:
        node = self.find_material().node_tree.nodes.get(name)
        if not isinstance(node, bpy.types.ShaderNodeTexImage):
            return
        if not isinstance(value, abc.Iterable):
            return
        value = list(value)
        if len(value) < 2:
            return
        node.texture_mapping.translation = (value[0], value[1], 0)

    def get_texture_scale(
        self,
        name: str,
    ) -> Tuple[float, float]:
        node = self.find_material().node_tree.nodes.get(name)
        if not isinstance(node, bpy.types.ShaderNodeTexImage):
            return (1, 1)
        return (
            node.texture_mapping.scale[0],
            node.texture_mapping.scale[1],
        )

    def set_texture_scale(
        self,
        name: str,
        value: Any,
    ) -> None:
        node = self.find_material().node_tree.nodes.get(name)
        if not isinstance(node, bpy.types.ShaderNodeTexImage):
            return
        if not isinstance(value, abc.Iterable):
            return
        value = list(value)
        if len(value) < 2:
            return
        node.texture_mapping.scale = (value[0], value[1], 1)


class Mtoon1KhrTextureTransformPropertyGroup(MaterialTraceablePropertyGroup):
    pass


class Mtoon1BaseColorKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = [
        "pbr_metallic_roughness",
        "base_color_texture",
        "extensions",
        "khr_texture_transform",
    ]

    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        default=(0, 0),
        get=lambda self: self.get_texture_offset(
            "pbrMetallicRoughness.baseColorTexture"
        ),
        set=lambda self, value: self.set_texture_offset(
            "pbrMetallicRoughness.baseColorTexture", value
        ),
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
        get=lambda self: self.get_texture_scale(
            "pbrMetallicRoughness.baseColorTexture"
        ),
        set=lambda self, value: self.set_texture_scale(
            "pbrMetallicRoughness.baseColorTexture", value
        ),
    )


class Mtoon1ShadeMultiplyKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "shade_multiply_texture",
        "extensions",
        "khr_texture_transform",
    ]

    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        default=(0, 0),
        get=lambda self: self.get_texture_offset("mtoon.shadeMultiplyTexture"),
        set=lambda self, value: self.set_texture_offset(
            "mtoon.shadeMultiplyTexture", value
        ),
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
        get=lambda self: self.get_texture_scale("mtoon.shadeMultiplyTexture"),
        set=lambda self, value: self.set_texture_scale(
            "mtoon.shadeMultiplyTexture", value
        ),
    )


class Mtoon1NormalKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = [
        "normal_texture",
        "extensions",
        "khr_texture_transform",
    ]

    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        default=(0, 0),
        get=lambda self: self.get_texture_offset("normalTexture"),
        set=lambda self, value: self.set_texture_offset("normalTexture", value),
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
        get=lambda self: self.get_texture_scale("normalTexture"),
        set=lambda self, value: self.set_texture_scale("normalTexture", value),
    )


class Mtoon1ShadingShiftKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "shading_shift_texture",
        "extensions",
        "khr_texture_transform",
    ]

    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        default=(0, 0),
        get=lambda self: self.get_texture_offset("mtoon.shadingShiftTexture"),
        set=lambda self, value: self.set_texture_offset(
            "mtoon.shadingShiftTexture", value
        ),
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
        get=lambda self: self.get_texture_scale("mtoon.shadingShiftTexture"),
        set=lambda self, value: self.set_texture_scale(
            "mtoon.shadingShiftTexture", value
        ),
    )


class Mtoon1EmissiveKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = [
        "emissive_texture",
        "extensions",
        "khr_texture_transform",
    ]

    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        default=(0, 0),
        get=lambda self: self.get_texture_offset("emissiveTexture"),
        set=lambda self, value: self.set_texture_offset("emissiveTexture", value),
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
        get=lambda self: self.get_texture_scale("emissiveTexture"),
        set=lambda self, value: self.set_texture_scale("emissiveTexture", value),
    )


class Mtoon1RimMultiplyKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "rim_multiply_texture",
        "extensions",
        "khr_texture_transform",
    ]

    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        default=(0, 0),
        get=lambda self: self.get_texture_offset("mtoon.rimMultiplyTexture"),
        set=lambda self, value: self.set_texture_offset(
            "mtoon.rimMultiplyTexture", value
        ),
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
        get=lambda self: self.get_texture_scale("mtoon.rimMultiplyTexture"),
        set=lambda self, value: self.set_texture_scale(
            "mtoon.rimMultiplyTexture", value
        ),
    )


class Mtoon1MatcapKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "matcap_texture",
        "extensions",
        "khr_texture_transform",
    ]

    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        default=(0, 0),
        get=lambda self: self.get_texture_offset("mtoon.matcapTexture"),
        set=lambda self, value: self.set_texture_offset("mtoon.matcapTexture", value),
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
        get=lambda self: self.get_texture_scale("mtoon.matcapTexture"),
        set=lambda self, value: self.set_texture_scale("mtoon.matcapTexture", value),
    )


class Mtoon1OutlineWidthMultiplyKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "outline_width_multiply_texture",
        "extensions",
        "khr_texture_transform",
    ]

    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        default=(0, 0),
        get=lambda self: self.get_texture_offset("mtoon.outlineWidthMultiplyTexture"),
        set=lambda self, value: self.set_texture_offset(
            "mtoon.outlineWidthMultiplyTexture", value
        ),
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
        get=lambda self: self.get_texture_scale("mtoon.outlineWidthMultiplyTexture"),
        set=lambda self, value: self.set_texture_scale(
            "mtoon.outlineWidthMultiplyTexture", value
        ),
    )


class Mtoon1UvAnimationMaskKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "uv_animation_mask_texture",
        "extensions",
        "khr_texture_transform",
    ]

    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        default=(0, 0),
        get=lambda self: self.get_texture_offset("mtoon.uvAnimationMaskTexture"),
        set=lambda self, value: self.set_texture_offset(
            "mtoon.uvAnimationMaskTexture", value
        ),
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
        get=lambda self: self.get_texture_scale("mtoon.uvAnimationMaskTexture"),
        set=lambda self, value: self.set_texture_scale(
            "mtoon.uvAnimationMaskTexture", value
        ),
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

    def get_mag_filter(self, _name: str) -> int:
        value = self.get("mag_filter")
        if value in self.MAG_FILTER_NUMBER_TO_ID:
            return int(value)
        return list(self.MAG_FILTER_NUMBER_TO_ID.keys())[0]

    def set_mag_filter(self, _name: str, value: int) -> None:
        if value not in self.MAG_FILTER_NUMBER_TO_ID:
            return
        self["mag_filter"] = value

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

    def get_min_filter(self, _name: str) -> int:
        value = self.get("min_filter")
        if value in self.MIN_FILTER_NUMBER_TO_ID:
            return int(value)
        return list(self.MIN_FILTER_NUMBER_TO_ID.keys())[0]

    def set_min_filter(self, _name: str, value: int) -> None:
        if value not in self.MIN_FILTER_NUMBER_TO_ID:
            return
        self["min_filter"] = value

    wrap_items = [
        ("CLAMP_TO_EDGE", "Clamp to Edge", "", 33071),
        ("MIRRORED_REPEAT", "Mirrored Repeat", "", 33648),
        ("REPEAT", "Repeat", "", 10497),
    ]
    WRAP_NUMBER_TO_ID = {wrap[-1]: wrap[0] for wrap in wrap_items}

    def get_wrap_s(self, _name: str) -> int:
        value = self.get("wrap_s")
        if value in self.WRAP_NUMBER_TO_ID:
            return int(value)
        return list(self.WRAP_NUMBER_TO_ID.keys())[0]

    def set_wrap_s(self, _name: str, value: int) -> None:
        if value not in self.WRAP_NUMBER_TO_ID:
            return
        self["wrap_s"] = value

    def get_wrap_t(self, _name: str) -> int:
        value = self.get("wrap_t")
        if value in self.WRAP_NUMBER_TO_ID:
            return int(value)
        return list(self.WRAP_NUMBER_TO_ID.keys())[0]

    def set_wrap_t(self, _name: str, value: int) -> None:
        if value not in self.WRAP_NUMBER_TO_ID:
            return
        self["wrap_t"] = value


class Mtoon1BaseColorSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = [
        "pbr_metallic_roughness",
        "base_color_texture",
        "index",
        "sampler",
    ]

    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
        get=lambda self: self.get_mag_filter("pbrMetallicRoughness.baseColorTexture"),
        set=lambda self, value: self.set_mag_filter(
            "pbrMetallicRoughness.baseColorTexture", value
        ),
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
        get=lambda self: self.get_min_filter("pbrMetallicRoughness.baseColorTexture"),
        set=lambda self, value: self.set_min_filter(
            "pbrMetallicRoughness.baseColorTexture", value
        ),
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap S",  # noqa: F722
        get=lambda self: self.get_wrap_s("pbrMetallicRoughness.baseColorTexture"),
        set=lambda self, value: self.set_wrap_s(
            "pbrMetallicRoughness.baseColorTexture", value
        ),
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap T",  # noqa: F722
        get=lambda self: self.get_wrap_t("pbrMetallicRoughness.baseColorTexture"),
        set=lambda self, value: self.set_wrap_t(
            "pbrMetallicRoughness.baseColorTexture", value
        ),
    )


class Mtoon1ShadeMultiplySamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "shade_multiply_texture",
        "index",
        "sampler",
    ]

    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
        get=lambda self: self.get_mag_filter("mtoon.shadeMultiplyTexture"),
        set=lambda self, value: self.set_mag_filter(
            "mtoon.shadeMultiplyTexture", value
        ),
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
        get=lambda self: self.get_min_filter("mtoon.shadeMultiplyTexture"),
        set=lambda self, value: self.set_min_filter(
            "mtoon.shadeMultiplyTexture", value
        ),
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap S",  # noqa: F722
        get=lambda self: self.get_wrap_s("mtoon.shadeMultiplyTexture"),
        set=lambda self, value: self.set_wrap_s("mtoon.shadeMultiplyTexture", value),
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap T",  # noqa: F722
        get=lambda self: self.get_wrap_t("mtoon.shadeMultiplyTexture"),
        set=lambda self, value: self.set_wrap_t("mtoon.shadeMultiplyTexture", value),
    )


class Mtoon1NormalSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = [
        "normal_texture",
        "index",
        "sampler",
    ]

    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
        get=lambda self: self.get_mag_filter("normalTexture"),
        set=lambda self, value: self.set_mag_filter("normalTexture", value),
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
        get=lambda self: self.get_min_filter("normalTexture"),
        set=lambda self, value: self.set_min_filter("normalTexture", value),
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap S",  # noqa: F722
        get=lambda self: self.get_wrap_s("normalTexture"),
        set=lambda self, value: self.set_wrap_s("normalTexture", value),
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap T",  # noqa: F722
        get=lambda self: self.get_wrap_t("normalTexture"),
        set=lambda self, value: self.set_wrap_t("normalTexture", value),
    )


class Mtoon1ShadingShiftSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "shading_shift_texture",
        "index",
        "sampler",
    ]

    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
        get=lambda self: self.get_mag_filter("mtoon.shadingShiftTexture"),
        set=lambda self, value: self.set_mag_filter("mtoon.shadingShiftTexture", value),
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
        get=lambda self: self.get_min_filter("mtoon.shadingShiftTexture"),
        set=lambda self, value: self.set_min_filter("mtoon.shadingShiftTexture", value),
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap S",  # noqa: F722
        get=lambda self: self.get_wrap_s("mtoon.shadingShiftTexture"),
        set=lambda self, value: self.set_wrap_s("mtoon.shadingShiftTexture", value),
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap T",  # noqa: F722
        get=lambda self: self.get_wrap_t("mtoon.shadingShiftTexture"),
        set=lambda self, value: self.set_wrap_t("mtoon.shadingShiftTexture", value),
    )


class Mtoon1EmissiveSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = [
        "emissive_texture",
        "index",
        "sampler",
    ]

    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
        get=lambda self: self.get_mag_filter("emissiveTexture"),
        set=lambda self, value: self.set_mag_filter("emissiveTexture", value),
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
        get=lambda self: self.get_min_filter("emissiveTexture"),
        set=lambda self, value: self.set_min_filter("emissiveTexture", value),
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap S",  # noqa: F722
        get=lambda self: self.get_wrap_s("emissiveTexture"),
        set=lambda self, value: self.set_wrap_s("emissiveTexture", value),
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap T",  # noqa: F722
        get=lambda self: self.get_wrap_t("emissiveTexture"),
        set=lambda self, value: self.set_wrap_t("emissiveTexture", value),
    )


class Mtoon1RimMultiplySamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "rim_multiply_texture",
        "index",
        "sampler",
    ]

    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
        get=lambda self: self.get_mag_filter("mtoon.rimMultiplyTexture"),
        set=lambda self, value: self.set_mag_filter("mtoon.rimMultiplyTexture", value),
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
        get=lambda self: self.get_min_filter("mtoon.rimMultiplyTexture"),
        set=lambda self, value: self.set_min_filter("mtoon.rimMultiplyTexture", value),
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap S",  # noqa: F722
        get=lambda self: self.get_wrap_s("mtoon.rimMultiplyTexture"),
        set=lambda self, value: self.set_wrap_s("mtoon.rimMultiplyTexture", value),
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap T",  # noqa: F722
        get=lambda self: self.get_wrap_t("mtoon.rimMultiplyTexture"),
        set=lambda self, value: self.set_wrap_t("mtoon.rimMultiplyTexture", value),
    )


class Mtoon1MatcapSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "matcap_texture",
        "index",
        "sampler",
    ]

    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
        get=lambda self: self.get_mag_filter("mtoon.matcapTexture"),
        set=lambda self, value: self.set_mag_filter("mtoon.matcapTexture", value),
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
        get=lambda self: self.get_min_filter("mtoon.matcapTexture"),
        set=lambda self, value: self.set_min_filter("mtoon.matcapTexture", value),
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap S",  # noqa: F722
        get=lambda self: self.get_wrap_s("mtoon.matcapTexture"),
        set=lambda self, value: self.set_wrap_s("mtoon.matcapTexture", value),
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap T",  # noqa: F722
        get=lambda self: self.get_wrap_t("mtoon.matcapTexture"),
        set=lambda self, value: self.set_wrap_t("mtoon.matcapTexture", value),
    )


class Mtoon1OutlineWidthMultiplySamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "outline_width_multiply_texture",
        "index",
        "sampler",
    ]

    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
        get=lambda self: self.get_mag_filter("mtoon.outlineWidthMultiplyTexture"),
        set=lambda self, value: self.set_mag_filter(
            "mtoon.outlineWidthMultiplyTexture", value
        ),
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
        get=lambda self: self.get_min_filter("mtoon.outlineWidthMultiplyTexture"),
        set=lambda self, value: self.set_min_filter(
            "mtoon.outlineWidthMultiplyTexture", value
        ),
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap S",  # noqa: F722
        get=lambda self: self.get_wrap_s("mtoon.outlineWidthMultiplyTexture"),
        set=lambda self, value: self.set_wrap_s(
            "mtoon.outlineWidthMultiplyTexture", value
        ),
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap T",  # noqa: F722
        get=lambda self: self.get_wrap_t("mtoon.outlineWidthMultiplyTexture"),
        set=lambda self, value: self.set_wrap_t(
            "mtoon.outlineWidthMultiplyTexture", value
        ),
    )


class Mtoon1UvAnimationMaskSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "uv_animation_mask_texture",
        "index",
        "sampler",
    ]

    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
        get=lambda self: self.get_mag_filter("mtoon.uvAnimationMaskTexture"),
        set=lambda self, value: self.set_mag_filter(
            "mtoon.uvAnimationMaskTexture", value
        ),
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
        get=lambda self: self.get_min_filter("mtoon.uvAnimationMaskTexture"),
        set=lambda self, value: self.set_min_filter(
            "mtoon.uvAnimationMaskTexture", value
        ),
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap S",  # noqa: F722
        get=lambda self: self.get_wrap_s("mtoon.uvAnimationMaskTexture"),
        set=lambda self, value: self.set_wrap_s("mtoon.uvAnimationMaskTexture", value),
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap T",  # noqa: F722
        get=lambda self: self.get_wrap_t("mtoon.uvAnimationMaskTexture"),
        set=lambda self, value: self.set_wrap_t("mtoon.uvAnimationMaskTexture", value),
    )


class Mtoon1TexturePropertyGroup(MaterialTraceablePropertyGroup):
    pass


class Mtoon1BaseColorTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = [
        "pbr_metallic_roughness",
        "base_color_texture",
        "index",
    ]
    source_node_name = "pbrMetallicRoughness.baseColorTexture"

    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image,  # noqa: F722
        update=lambda self, _context: self.update_image(self.source),
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1BaseColorSamplerPropertyGroup  # noqa: F722
    )


class Mtoon1ShadeMultiplyTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "shade_multiply_texture",
        "index",
    ]
    source_node_name = "mtoon.shadeMultiplyTexture"

    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image,  # noqa: F722
        update=lambda self, _context: self.update_image(self.source),
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadeMultiplySamplerPropertyGroup  # noqa: F722
    )


class Mtoon1NormalTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = [
        "normal_texture",
        "index",
    ]
    source_node_name = "normalTexture"

    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image,  # noqa: F722
        update=lambda self, _context: self.update_image(self.source),
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1NormalSamplerPropertyGroup  # noqa: F722
    )


class Mtoon1ShadingShiftTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "shading_shift_texture",
        "index",
    ]
    source_node_name = "mtoon.shadingShiftTexture"

    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image,  # noqa: F722
        update=lambda self, _context: self.update_image(self.source),
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadingShiftSamplerPropertyGroup  # noqa: F722
    )


class Mtoon1EmissiveTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = [
        "emissive_texture",
        "index",
    ]
    source_node_name = "emissiveTexture"

    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image,  # noqa: F722
        update=lambda self, _context: self.update_image(self.source),
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1EmissiveSamplerPropertyGroup  # noqa: F722
    )


class Mtoon1RimMultiplyTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "rim_multiply_texture",
        "index",
    ]
    source_node_name = "mtoon.rimMultiplyTexture"

    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image,  # noqa: F722
        update=lambda self, _context: self.update_image(self.source),
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1RimMultiplySamplerPropertyGroup  # noqa: F722
    )


class Mtoon1MatcapTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "matcap_texture",
        "index",
    ]
    source_node_name = "mtoon.matcapTexture"

    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image,  # noqa: F722
        update=lambda self, _context: self.update_image(self.source),
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MatcapSamplerPropertyGroup  # noqa: F722
    )


class Mtoon1OutlineWidthMultiplyTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "outline_width_multiply_texture",
        "index",
    ]
    source_node_name = "mtoon.outlineWidthMultiplyTexture"

    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image,  # noqa: F722
        update=lambda self, _context: self.update_image(self.source),
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1OutlineWidthMultiplySamplerPropertyGroup  # noqa: F722
    )


class Mtoon1UvAnimationMaskTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "uv_animation_mask_texture",
        "index",
    ]
    source_node_name = "mtoon.uvAnimationMaskTexture"

    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image,  # noqa: F722
        update=lambda self, _context: self.update_image(self.source),
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

    base_color_factor: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=4,
        subtype="COLOR",  # noqa: F821
        default=(0, 0, 0, 0),
        min=0,
        max=1,
        get=lambda self: self.get_rgba("pbrMetallicRoughness.baseColorFactor"),
        set=lambda self, value: self.set_rgba(
            "pbrMetallicRoughness.baseColorFactor", value
        ),
    )

    base_color_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1BaseColorTextureInfoPropertyGroup  # noqa: F722
    )


class Mtoon1MaterialVrmcMaterialsMtoonPropertyGroup(MaterialTraceablePropertyGroup):
    material_property_chain: List[str] = ["extensions", "vrmc_materials_mtoon"]

    transparent_with_z_write: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Transparent With ZWrite Mode",  # noqa: F722
        get=lambda self: self.get_bool("mtoon.transparentWithZWrite"),
        set=lambda self, value: self.set_bool("mtoon.transparentWithZWrite", value),
    )

    render_queue_offset_number: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="RenderQueue Offset",  # noqa: F722
        min=-9,
        default=0,
        max=9,
        get=lambda self: self.get_int("mtoon.renderQueueOffsetNumber"),
        set=lambda self, value: self.set_int("mtoon.renderQueueOffsetNumber", value),
    )

    shade_multiply_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadeMultiplyTextureInfoPropertyGroup  # noqa: F722
    )

    shade_color_factor: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="COLOR",  # noqa: F821
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        get=lambda self: self.get_rgb("mtoon.shadeColorFactor"),
        set=lambda self, value: self.set_rgb("mtoon.shadeColorFactor", value),
    )

    shading_shift_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadingShiftTextureInfoPropertyGroup  # noqa: F722
    )

    shading_shift_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Shading Shift",  # noqa: F722
        soft_min=-1.0,
        default=0.0,
        soft_max=1.0,
        get=lambda self: self.get_value("mtoon.shadingShiftFactor"),
        set=lambda self, value: self.set_value("mtoon.shadingShiftFactor", value),
    )

    shading_toony_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Shading Toony",  # noqa: F722
        min=0.0,
        default=0.9,
        max=1.0,
        get=lambda self: self.get_value("mtoon.shadingToonyFactor"),
        set=lambda self, value: self.set_value("mtoon.shadingToonyFactor", value),
    )

    gi_equalization_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="GI Equalization",  # noqa: F722
        min=0.0,
        default=0.9,
        max=1.0,
        get=lambda self: self.get_value("mtoon.giEqualizationFactor"),
        set=lambda self, value: self.set_value("mtoon.giEqualizationFactor", value),
    )

    matcap_factor: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="COLOR",  # noqa: F821
        default=(1, 1, 1),
        min=0,
        max=1,
        get=lambda self: self.get_rgb("mtoon.matcapFactor"),
        set=lambda self, value: self.set_rgb("mtoon.matcapFactor", value),
    )

    matcap_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MatcapTextureInfoPropertyGroup  # noqa: F722
    )

    parametric_rim_color_factor: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Parametric Rim Color",  # noqa: F722
        size=3,
        subtype="COLOR",  # noqa: F821
        default=(0, 0, 0),
        min=0,
        max=1,
        get=lambda self: self.get_rgb("mtoon.parametricRimColorFactor"),
        set=lambda self, value: self.set_rgb("mtoon.parametricRimColorFactor", value),
    )

    rim_multiply_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1RimMultiplyTextureInfoPropertyGroup  # noqa: F722
    )

    rim_lighting_mix_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Rim LightingMix",  # noqa: F722
        soft_min=0,
        soft_max=1,
        get=lambda self: self.get_value("mtoon.rimLightingMixFactor"),
        set=lambda self, value: self.set_value("mtoon.rimLightingMixFactor", value),
    )

    parametric_rim_fresnel_power_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Parametric Rim Fresnel Power",  # noqa: F722
        min=0.0,
        default=1.0,
        soft_max=100.0,
        get=lambda self: self.get_value("mtoon.parametricRimFresnelPowerFactor"),
        set=lambda self, value: self.set_value(
            "mtoon.parametricRimFresnelPowerFactor", value
        ),
    )

    parametric_rim_lift_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Parametric Rim Lift",  # noqa: F722
        soft_min=0.0,
        default=1.0,
        soft_max=1.0,
        get=lambda self: self.get_value("mtoon.parametricRimLiftFactor"),
        set=lambda self, value: self.set_value("mtoon.parametricRimLiftFactor", value),
    )

    OUTLINE_WIDTH_MODE_NONE = "none"
    outline_width_mode_items = [
        (OUTLINE_WIDTH_MODE_NONE, "None", "", "NONE", 0),
        ("worldCoordinates", "World Coordinates", "", "NONE", 1),
        ("screenCoordinates", "Screen Coordinates", "", "NONE", 2),
    ]
    OUTLINE_WIDTH_MODE_IDS = [
        outline_width_mode_item[0]
        for outline_width_mode_item in outline_width_mode_items
    ]

    def __get_outline_width_mode(self) -> int:
        return self.get_int("mtoon.outlineWidthMode")

    def __set_outline_width_mode(self, value: int) -> None:
        if value in [item[-1] for item in self.outline_width_mode_items]:
            self.set_int("mtoon.outlineWidthMode", value)

    outline_width_mode: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=outline_width_mode_items,
        name="Outline Width Mode",  # noqa: F722
        get=__get_outline_width_mode,
        set=__set_outline_width_mode,
    )

    outline_width_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Outline Width",  # noqa: F722
        min=0.0,
        soft_max=0.05,
        get=lambda self: self.get_value("mtoon.outlineWidthFactor"),
        set=lambda self, value: self.set_value("mtoon.outlineWidthFactor", value),
    )

    outline_width_multiply_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1OutlineWidthMultiplyTextureInfoPropertyGroup  # noqa: F722
    )

    outline_color_factor: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Outline Color",  # noqa: F722
        size=3,
        subtype="COLOR",  # noqa: F821
        default=(0, 0, 0),
        min=0,
        max=1,
        get=lambda self: self.get_rgb("mtoon.outlineColorFactor"),
        set=lambda self, value: self.set_rgb("mtoon.outlineColorFactor", value),
    )

    outline_lighting_mix_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Outline LightingMix",  # noqa: F722
        min=0.0,
        default=1.0,
        max=1.0,
        get=lambda self: self.get_value("mtoon.outlineLightingMixFactor"),
        set=lambda self, value: self.set_value("mtoon.outlineLightingMixFactor", value),
    )

    uv_animation_mask_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1UvAnimationMaskTextureInfoPropertyGroup  # noqa: F722
    )

    uv_animation_scroll_x_speed_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Translate X",  # noqa: F722
        get=lambda self: self.get_value("mtoon.uvAnimationScrollXSpeedFactor"),
        set=lambda self, value: self.set_value(
            "mtoon.uvAnimationScrollXSpeedFactor", value
        ),
    )

    uv_animation_scroll_y_speed_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Translate Y",  # noqa: F722
        get=lambda self: self.get_value("mtoon.uvAnimationScrollYSpeedFactor"),
        set=lambda self, value: self.set_value(
            "mtoon.uvAnimationScrollYSpeedFactor", value
        ),
    )

    uv_animation_rotation_speed_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Rotation",  # noqa: F821
        get=lambda self: self.get_value("mtoon.uvAnimationRotationSpeedFactor"),
        set=lambda self, value: self.set_value(
            "mtoon.uvAnimationRotationSpeedFactor", value
        ),
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
        raise ValueError(f"Unexpected blend_method: {blend_method}")

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
            logger.error("Unexpected alpha mode: {value}")
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
        soft_max=1,
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
        get=lambda self: self.get_rgb("emissiveFactor"),
        set=lambda self, value: self.set_rgb("emissiveFactor", value),
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
