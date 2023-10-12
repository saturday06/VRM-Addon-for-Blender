import functools
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

import bpy
from mathutils import Vector

from ...common import shader
from ...common.logging import get_logger
from ...common.preferences import VrmAddonPreferences
from ...common.version import addon_version

logger = get_logger(__name__)


MTOON1_OUTPUT_NODE_GROUP_NAME = "Mtoon1Material.Mtoon1Output"


class MaterialTraceablePropertyGroup(bpy.types.PropertyGroup):
    def find_material(self) -> bpy.types.Material:
        if self.id_data and self.id_data.is_evaluated:
            logger.error(f"{self} is evaluated. May cause a problem.")

        chain = self.get_material_property_chain()
        for material in bpy.data.materials:
            if not material:
                continue
            ext = material.vrm_addon_extension.mtoon1
            if functools.reduce(getattr, chain, ext) == self:
                return material

        raise AssertionError(f"No matching material: {type(self)} {chain}")

    @classmethod
    def get_material_property_chain(cls) -> list[str]:
        chain = getattr(cls, "material_property_chain", None)
        if not isinstance(chain, list):
            raise NotImplementedError(
                f"No material property chain: {cls}.{type(chain)} => {chain}",
            )
        result: list[str] = []
        for property_name in list(chain):
            if isinstance(property_name, str):
                result.append(property_name)
                continue
            raise AssertionError(
                f"Invalid material property chain: {cls}.{type(chain)} => {chain}",
            )
        return result

    @classmethod
    def find_outline_property_group(
        cls, material: bpy.types.Material
    ) -> Optional["MaterialTraceablePropertyGroup"]:
        if material.vrm_addon_extension.mtoon1.is_outline_material:
            return None
        outline_material = material.vrm_addon_extension.mtoon1.outline_material
        if not outline_material:
            return None
        if material.name == outline_material.name:
            logger.error(
                "Base material and outline material are same. name={material.name}"
            )
            return None
        chain = cls.get_material_property_chain()
        attr = outline_material.vrm_addon_extension.mtoon1
        for name in chain:
            attr = getattr(attr, name, None)
        if isinstance(attr, MaterialTraceablePropertyGroup):
            return attr
        raise AssertionError(f"No matching property group: {cls} {chain}")

    def set_value(
        self,
        node_group_name: str,
        group_label: str,
        value: object,
    ) -> None:
        material = self.find_material()
        outline = self.find_outline_property_group(material)
        if outline:
            outline.set_value(node_group_name, group_label, value)

        if not isinstance(value, (int, float)):
            return

        node_tree = material.node_tree
        if not node_tree:
            return

        node = {
            0: node
            for node in node_tree.nodes
            if isinstance(node, bpy.types.ShaderNodeGroup)
            and node.node_tree
            and node.node_tree.name == node_group_name
        }.get(0)
        if not node:
            logger.warning(f'No group node "{node_group_name}"')
            return

        socket = node.inputs.get(group_label)
        if isinstance(socket, shader.BOOL_SOCKET_CLASSES):
            socket.default_value = bool(value)
        elif isinstance(socket, shader.FLOAT_SOCKET_CLASSES):
            socket.default_value = float(value)
        elif isinstance(socket, shader.INT_SOCKET_CLASSES):
            socket.default_value = int(value)
        else:
            logger.warning(
                f'No "{group_label}" in shader node group "{node_group_name}"'
            )

    def set_bool(
        self,
        node_group_name: str,
        group_label: str,
        value: object,
    ) -> None:
        self.set_value(node_group_name, group_label, 1 if value else 0)

    def set_int(
        self,
        node_group_name: str,
        group_label: str,
        value: object,
    ) -> None:
        self.set_value(node_group_name, group_label, value)

    def set_rgba(
        self,
        node_group_name: str,
        group_label: str,
        value: object,
        default_value: Optional[tuple[float, float, float, float]] = None,
    ) -> None:
        material = self.find_material()

        outline = self.find_outline_property_group(material)
        if outline:
            outline.set_rgba(node_group_name, group_label, value, default_value)

        if not default_value:
            default_value = (0.0, 0.0, 0.0, 0.0)

        node_tree = material.node_tree
        if not node_tree:
            return

        rgba = shader.rgba_or_none(value) or default_value

        node = {
            0: node
            for node in node_tree.nodes
            if isinstance(node, bpy.types.ShaderNodeGroup)
            and node.node_tree
            and node.node_tree.name == node_group_name
        }.get(0)
        if not node:
            logger.warning(f'No group node "{node_group_name}"')
            return

        socket = node.inputs.get(group_label)
        if not isinstance(socket, shader.COLOR_SOCKET_CLASSES):
            logger.warning(
                f'No "{group_label}" in shader node group "{node_group_name}"'
            )
            return

        socket.default_value = rgba

    def set_rgb(
        self,
        node_group_name: str,
        group_label: Optional[str],
        value: object,
        default_value: Optional[tuple[float, float, float]] = None,
    ) -> None:
        material = self.find_material()

        outline = self.find_outline_property_group(material)
        if outline:
            outline.set_rgb(node_group_name, group_label, value, default_value)

        if not default_value:
            default_value = (0.0, 0.0, 0.0)

        node_tree = material.node_tree
        if not node_tree:
            return

        rgb = shader.rgb_or_none(value) or default_value

        node = {
            0: node
            for node in node_tree.nodes
            if isinstance(node, bpy.types.ShaderNodeGroup)
            and node.node_tree
            and node.node_tree.name == node_group_name
        }.get(0)
        if not node:
            logger.warning(f'No group node "{node_group_name}"')
            return

        if group_label is None:
            return

        socket = node.inputs.get(group_label)
        if not isinstance(socket, shader.COLOR_SOCKET_CLASSES):
            logger.warning(
                f'No "{group_label}" in shader node group "{node_group_name}"'
            )
            return

        socket.default_value = rgb + (1.0,)


class TextureTraceablePropertyGroup(MaterialTraceablePropertyGroup):
    def get_texture_info_property_group(self) -> "Mtoon1TextureInfoPropertyGroup":
        chain = self.get_material_property_chain()
        if chain[-1:] == ["sampler"]:
            chain = chain[:-1]
        if chain[-1:] == ["index"]:
            chain = chain[:-1]
        if chain[-1:] == ["khr_texture_transform"]:
            chain = chain[:-1]
        if chain[-1:] == ["extensions"]:
            chain = chain[:-1]
        material = self.find_material()
        ext = material.vrm_addon_extension.mtoon1
        property_group = functools.reduce(getattr, chain, ext)
        if not isinstance(property_group, Mtoon1TextureInfoPropertyGroup):
            raise ValueError(
                f"{property_group} is not a Mtoon1TextureInfoPropertyGroup"
            )
        return property_group

    def get_texture_node_name(self, extra: str) -> str:
        texture_info = self.get_texture_info_property_group()
        name = type(texture_info.index).__name__
        return re.sub("PropertyGroup$", "", name) + "." + extra

    @staticmethod
    def link_tex_image_to_node_group(
        material: bpy.types.Material,
        tex_image_node_name: str,
        tex_image_node_socket_name: str,
        node_group_node_tree_name: str,
        node_group_socket_name: str,
    ) -> None:
        if not material.node_tree:
            return

        if any(
            1
            for link in material.node_tree.links
            if isinstance(link.from_node, bpy.types.ShaderNodeTexImage)
            and link.from_node.name == tex_image_node_name
            and link.from_socket
            and link.from_socket.name == tex_image_node_socket_name
            and isinstance(link.to_node, bpy.types.ShaderNodeGroup)
            and link.to_node.node_tree
            and link.to_node.node_tree.name == node_group_node_tree_name
            and link.to_socket
            and link.to_socket.name == node_group_socket_name
        ):
            return

        disconnecting_link = {
            0: link
            for link in material.node_tree.links
            if isinstance(link.to_node, bpy.types.ShaderNodeGroup)
            and link.to_node.node_tree
            and link.to_node.node_tree.name == node_group_node_tree_name
            and link.to_socket
            and link.to_socket.name == node_group_socket_name
        }.get(0)
        if disconnecting_link:
            material.node_tree.links.remove(disconnecting_link)

        in_node = {
            0: n
            for n in material.node_tree.nodes
            if isinstance(n, bpy.types.ShaderNodeGroup)
            and n.node_tree
            and n.node_tree.name == node_group_node_tree_name
        }.get(0)
        if not isinstance(in_node, bpy.types.ShaderNodeGroup):
            logger.error(f'No shader node group with "{node_group_node_tree_name}"')
            return

        in_socket = in_node.inputs.get(node_group_socket_name)
        if not in_socket:
            logger.error(f"No group socket: {node_group_socket_name}")
            return

        out_node = material.node_tree.nodes.get(tex_image_node_name)
        if not isinstance(out_node, bpy.types.ShaderNodeTexImage):
            logger.error(f"No tex image node: {tex_image_node_name}")
            return

        out_socket = out_node.outputs.get(tex_image_node_socket_name)
        if not out_socket:
            logger.error(f"No tex image node socket: {tex_image_node_socket_name}")
            return

        material.node_tree.links.new(in_socket, out_socket)

    @staticmethod
    def unlink_tex_image_to_node_group(
        material: bpy.types.Material,
        tex_image_node_name: str,
        tex_image_node_socket_name: str,
        node_group_node_tree_name: str,
        node_group_socket_name: str,
    ) -> None:
        while True:
            # Refresh in_node/out_node. These nodes may be invalidated.
            if not material.node_tree:
                return

            disconnecting_link = {
                0: link
                for link in material.node_tree.links
                if isinstance(link.from_node, bpy.types.ShaderNodeTexImage)
                and link.from_node.name == tex_image_node_name
                and link.from_socket
                and link.from_socket.name == tex_image_node_socket_name
                and isinstance(link.to_node, bpy.types.ShaderNodeGroup)
                and link.to_node.node_tree
                and link.to_node.node_tree.name == node_group_node_tree_name
                and link.to_socket
                and link.to_socket.name == node_group_socket_name
            }.get(0)
            if not disconnecting_link:
                break

            material.node_tree.links.remove(disconnecting_link)

    @staticmethod
    def connect_tex_image_to_node_group(
        link: bool,
        material: bpy.types.Material,
        tex_image_node_name: str,
        tex_image_node_socket_name: str,
        node_group_node_tree_name: str,
        node_group_socket_name: str,
    ) -> None:
        if link:
            TextureTraceablePropertyGroup.link_tex_image_to_node_group(
                material,
                tex_image_node_name,
                tex_image_node_socket_name,
                node_group_node_tree_name,
                node_group_socket_name,
            )
        else:
            TextureTraceablePropertyGroup.unlink_tex_image_to_node_group(
                material,
                tex_image_node_name,
                tex_image_node_socket_name,
                node_group_node_tree_name,
                node_group_socket_name,
            )

    def update_image(self, image: Optional[bpy.types.Image]) -> None:
        material = self.find_material()

        outline = self.find_outline_property_group(material)
        if outline and isinstance(outline, TextureTraceablePropertyGroup):
            outline.update_image(image)

        node_tree = material.node_tree
        if not node_tree:
            return

        node_name = self.get_texture_node_name("Image")

        node = node_tree.nodes.get(node_name)
        if not isinstance(node, bpy.types.ShaderNodeTexImage):
            logger.warning(f'No shader node tex image "{node_name}"')
            return

        node.image = image

        self.set_texture_uv("Image Width", max(image.size[0], 1) if image else 1)
        self.set_texture_uv("Image Height", max(image.size[1], 1) if image else 1)

        texture_info = self.get_texture_info_property_group()
        if isinstance(texture_info, Mtoon1BaseColorTextureInfoPropertyGroup):
            self.connect_tex_image_to_node_group(
                bool(image),
                material,
                node_name,
                "Color",
                texture_info.node_group_name,
                texture_info.group_label_base_name + " Color",
            )
            self.connect_tex_image_to_node_group(
                bool(image),
                material,
                node_name,
                "Alpha",
                texture_info.node_group_name,
                texture_info.group_label_base_name + " Alpha",
            )
        else:
            self.connect_tex_image_to_node_group(
                bool(image),
                material,
                node_name,
                "Color",
                texture_info.node_group_name,
                texture_info.group_label_base_name,
            )

    def set_texture_uv(self, name: str, value: object) -> None:
        node_name = self.get_texture_node_name("Uv")
        material = self.find_material()
        if not material.node_tree:
            return
        node_tree = material.node_tree
        node = node_tree.nodes.get(node_name)
        if not isinstance(node, bpy.types.ShaderNodeGroup):
            logger.warning(f'No shader node group "{node_name}"')
            return
        socket = node.inputs.get(name)
        if not socket:
            logger.warning(f'No "{name}" in shader node group "{node_name}"')
            return

        if isinstance(value, (float, int)):
            if isinstance(socket, shader.FLOAT_SOCKET_CLASSES):
                socket.default_value = float(value)
            if isinstance(socket, shader.INT_SOCKET_CLASSES):
                socket.default_value = int(value)

        outline = self.find_outline_property_group(material)
        if not outline:
            return
        if not isinstance(outline, TextureTraceablePropertyGroup):
            return
        outline.set_texture_uv(name, value)


class Mtoon1KhrTextureTransformPropertyGroup(TextureTraceablePropertyGroup):
    def update_texture_offset(self, _context: bpy.types.Context) -> None:
        self.set_texture_uv("UV Offset X", self.offset[0])
        self.set_texture_uv("UV Offset Y", self.offset[1])

        node_name = self.get_texture_node_name("Image")
        material = self.find_material()
        if not material.node_tree:
            return
        node = material.node_tree.nodes.get(node_name)
        if not isinstance(node, bpy.types.ShaderNodeTexImage):
            logger.warning(f'No shader node tex image "{node_name}"')
            return
        node.texture_mapping.translation = Vector((0, 0, 0))

        outline = self.find_outline_property_group(material)
        if not outline:
            return
        if not isinstance(outline, Mtoon1KhrTextureTransformPropertyGroup):
            return
        outline.update_texture_offset(_context)

    def update_texture_scale(self, _context: bpy.types.Context) -> None:
        self.set_texture_uv("UV Scale X", self.scale[0])
        self.set_texture_uv("UV Scale Y", self.scale[1])

        node_name = self.get_texture_node_name("Image")
        material = self.find_material()
        if not material.node_tree:
            return
        node = material.node_tree.nodes.get(node_name)
        if not isinstance(node, bpy.types.ShaderNodeTexImage):
            logger.warning(f'No shader node tex image "{node_name}"')
            return
        node.texture_mapping.scale = Vector((1, 1, 1))

        outline = self.find_outline_property_group(material)
        if not outline:
            return
        if not isinstance(outline, Mtoon1KhrTextureTransformPropertyGroup):
            return
        outline.update_texture_scale(_context)

    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        default=(0, 0),
        update=update_texture_offset,
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
        update=update_texture_scale,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        offset: Sequence[float]  # type: ignore[no-redef]
        scale: Sequence[float]  # type: ignore[no-redef]


class Mtoon1BaseColorKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = [
        "pbr_metallic_roughness",
        "base_color_texture",
        "extensions",
        "khr_texture_transform",
    ]


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


class Mtoon1NormalKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = [
        "normal_texture",
        "extensions",
        "khr_texture_transform",
    ]


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


class Mtoon1EmissiveKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = [
        "emissive_texture",
        "extensions",
        "khr_texture_transform",
    ]


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

    def update_texture_offset_and_outline(self, context: bpy.types.Context) -> None:
        material = self.find_material()
        if material.vrm_addon_extension.mtoon1.is_outline_material:
            return
        self.update_texture_offset(context)
        bpy.ops.vrm.refresh_mtoon1_outline(material_name=material.name)

    def update_texture_scale_and_outline(self, context: bpy.types.Context) -> None:
        material = self.find_material()
        if material.vrm_addon_extension.mtoon1.is_outline_material:
            return
        self.update_texture_scale(context)
        bpy.ops.vrm.refresh_mtoon1_outline(material_name=material.name)

    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",  # noqa: F821
        size=2,
        default=(0, 0),
        update=update_texture_offset_and_outline,
    )

    scale: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        size=2,
        default=(1, 1),
        update=update_texture_scale_and_outline,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        offset: Sequence[float]  # type: ignore[no-redef]
        scale: Sequence[float]  # type: ignore[no-redef]


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


class Mtoon1TextureInfoExtensionsPropertyGroup(bpy.types.PropertyGroup):
    pass


class Mtoon1BaseColorTextureInfoExtensionsPropertyGroup(
    Mtoon1TextureInfoExtensionsPropertyGroup
):
    khr_texture_transform: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1BaseColorKhrTextureTransformPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        khr_texture_transform: Mtoon1BaseColorKhrTextureTransformPropertyGroup  # type: ignore[no-redef]


class Mtoon1ShadeMultiplyTextureInfoExtensionsPropertyGroup(
    Mtoon1TextureInfoExtensionsPropertyGroup
):
    khr_texture_transform: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadeMultiplyKhrTextureTransformPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        khr_texture_transform: Mtoon1ShadeMultiplyKhrTextureTransformPropertyGroup  # type: ignore[no-redef]


class Mtoon1NormalTextureInfoExtensionsPropertyGroup(
    Mtoon1TextureInfoExtensionsPropertyGroup
):
    khr_texture_transform: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1NormalKhrTextureTransformPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        khr_texture_transform: Mtoon1NormalKhrTextureTransformPropertyGroup  # type: ignore[no-redef]


class Mtoon1ShadingShiftTextureInfoExtensionsPropertyGroup(
    Mtoon1TextureInfoExtensionsPropertyGroup
):
    khr_texture_transform: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadingShiftKhrTextureTransformPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        khr_texture_transform: Mtoon1ShadingShiftKhrTextureTransformPropertyGroup  # type: ignore[no-redef]


class Mtoon1EmissiveTextureInfoExtensionsPropertyGroup(
    Mtoon1TextureInfoExtensionsPropertyGroup
):
    khr_texture_transform: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1EmissiveKhrTextureTransformPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        khr_texture_transform: Mtoon1EmissiveKhrTextureTransformPropertyGroup  # type: ignore[no-redef]


class Mtoon1RimMultiplyTextureInfoExtensionsPropertyGroup(
    Mtoon1TextureInfoExtensionsPropertyGroup
):
    khr_texture_transform: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1RimMultiplyKhrTextureTransformPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        khr_texture_transform: Mtoon1RimMultiplyKhrTextureTransformPropertyGroup  # type: ignore[no-redef]


class Mtoon1MatcapTextureInfoExtensionsPropertyGroup(
    Mtoon1TextureInfoExtensionsPropertyGroup
):
    khr_texture_transform: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MatcapKhrTextureTransformPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        khr_texture_transform: Mtoon1MatcapKhrTextureTransformPropertyGroup  # type: ignore[no-redef]


class Mtoon1OutlineWidthMultiplyTextureInfoExtensionsPropertyGroup(
    Mtoon1TextureInfoExtensionsPropertyGroup
):
    khr_texture_transform: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1OutlineWidthMultiplyKhrTextureTransformPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        khr_texture_transform: Mtoon1OutlineWidthMultiplyKhrTextureTransformPropertyGroup  # type: ignore[no-redef]


class Mtoon1UvAnimationMaskTextureInfoExtensionsPropertyGroup(
    Mtoon1TextureInfoExtensionsPropertyGroup
):
    khr_texture_transform: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1UvAnimationMaskKhrTextureTransformPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        khr_texture_transform: Mtoon1UvAnimationMaskKhrTextureTransformPropertyGroup  # type: ignore[no-redef]


class Mtoon1SamplerPropertyGroup(TextureTraceablePropertyGroup):
    mag_filter_items = [
        ("NEAREST", "Nearest", "", 9728),
        ("LINEAR", "Linear", "", 9729),
    ]
    MAG_FILTER_NUMBER_TO_ID: dict[int, str] = {
        filter[-1]: filter[0] for filter in mag_filter_items
    }
    MAG_FILTER_ID_TO_NUMBER: dict[str, int] = {
        filter[0]: filter[-1] for filter in mag_filter_items
    }

    def get_mag_filter(self) -> int:
        default_value = list(self.MAG_FILTER_NUMBER_TO_ID.keys())[0]
        value = self.get("mag_filter")
        if not isinstance(value, int):
            return default_value
        if value in self.MAG_FILTER_NUMBER_TO_ID:
            return int(value)
        return default_value

    def set_mag_filter(self, value: int) -> None:
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
    MIN_FILTER_NUMBER_TO_ID: dict[int, str] = {
        filter[-1]: filter[0] for filter in min_filter_items
    }
    MIN_FILTER_ID_TO_NUMBER: dict[str, int] = {
        filter[0]: filter[-1] for filter in min_filter_items
    }

    # https://github.com/KhronosGroup/glTF/blob/2a9996a2ea66ab712590eaf62f39f1115996f5a3/specification/2.0/schema/sampler.schema.json#L67-L117
    WRAP_DEFAULT_NUMBER = 10497
    WRAP_DEFAULT_ID = "REPEAT"

    wrap_items = [
        ("CLAMP_TO_EDGE", "Clamp to Edge", "", 33071),
        ("MIRRORED_REPEAT", "Mirrored Repeat", "", 33648),
        (WRAP_DEFAULT_ID, "Repeat", "", WRAP_DEFAULT_NUMBER),
    ]
    WRAP_NUMBER_TO_ID: dict[int, str] = {wrap[-1]: wrap[0] for wrap in wrap_items}
    WRAP_ID_TO_NUMBER: dict[str, int] = {wrap[0]: wrap[-1] for wrap in wrap_items}

    def update_wrap_s(self, _context: bpy.types.Context) -> None:
        wrap_s = self.WRAP_ID_TO_NUMBER.get(self.wrap_s, self.WRAP_DEFAULT_NUMBER)
        self.set_texture_uv("Wrap S", wrap_s)

    def update_wrap_t(self, _context: bpy.types.Context) -> None:
        wrap_t = self.WRAP_ID_TO_NUMBER.get(self.wrap_t, self.WRAP_DEFAULT_NUMBER)
        self.set_texture_uv("Wrap T", wrap_t)

    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=mag_filter_items,
        name="Mag Filter",  # noqa: F722
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=min_filter_items,
        name="Min Filter",  # noqa: F722
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=wrap_items,
        name="Wrap S",  # noqa: F722
        default=WRAP_DEFAULT_ID,
        update=update_wrap_s,
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=wrap_items,
        name="Wrap T",  # noqa: F722
        default=WRAP_DEFAULT_ID,
        update=update_wrap_t,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        mag_filter: str  # type: ignore[no-redef]
        min_filter: str  # type: ignore[no-redef]
        wrap_s: str  # type: ignore[no-redef]
        wrap_t: str  # type: ignore[no-redef]


class Mtoon1BaseColorSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = [
        "pbr_metallic_roughness",
        "base_color_texture",
        "index",
        "sampler",
    ]


class Mtoon1ShadeMultiplySamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "shade_multiply_texture",
        "index",
        "sampler",
    ]


class Mtoon1NormalSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = [
        "normal_texture",
        "index",
        "sampler",
    ]


class Mtoon1ShadingShiftSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "shading_shift_texture",
        "index",
        "sampler",
    ]


class Mtoon1EmissiveSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = [
        "emissive_texture",
        "index",
        "sampler",
    ]


class Mtoon1RimMultiplySamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "rim_multiply_texture",
        "index",
        "sampler",
    ]


class Mtoon1MatcapSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "matcap_texture",
        "index",
        "sampler",
    ]


class Mtoon1OutlineWidthMultiplySamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "outline_width_multiply_texture",
        "index",
        "sampler",
    ]


class Mtoon1UvAnimationMaskSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "uv_animation_mask_texture",
        "index",
        "sampler",
    ]


class Mtoon1TexturePropertyGroup(TextureTraceablePropertyGroup):
    colorspace = "sRGB"

    def update_source(self, _context: bpy.types.Context) -> None:
        self.update_image(self.source)

    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image,  # noqa: F722
        update=update_source,
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1SamplerPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        source: Optional[bpy.types.Image]  # type: ignore[no-redef]
        sampler: Mtoon1SamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1BaseColorTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = [
        "pbr_metallic_roughness",
        "base_color_texture",
        "index",
    ]

    label = "Lit Color, Alpha"
    panel_label = label
    colorspace = "sRGB"

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1BaseColorSamplerPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        sampler: Mtoon1BaseColorSamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1ShadeMultiplyTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "shade_multiply_texture",
        "index",
    ]

    label = "Shade Color"
    panel_label = label
    colorspace = "sRGB"

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadeMultiplySamplerPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        sampler: Mtoon1ShadeMultiplySamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1NormalTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = [
        "normal_texture",
        "index",
    ]

    label = "Normal Map"
    panel_label = label
    colorspace = "Non-Color"

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1NormalSamplerPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        sampler: Mtoon1NormalSamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1ShadingShiftTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "shading_shift_texture",
        "index",
    ]

    label = "Additive Shading Shift"
    panel_label = label
    colorspace = "Non-Color"

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadingShiftSamplerPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        sampler: Mtoon1ShadingShiftSamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1EmissiveTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = [
        "emissive_texture",
        "index",
    ]

    label = "Emission"
    panel_label = label
    colorspace = "sRGB"

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1EmissiveSamplerPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        sampler: Mtoon1EmissiveSamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1RimMultiplyTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "rim_multiply_texture",
        "index",
    ]

    label = "Rim Color"
    panel_label = label
    colorspace = "sRGB"

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1RimMultiplySamplerPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        sampler: Mtoon1RimMultiplySamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1MatcapTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "matcap_texture",
        "index",
    ]

    label = "Matcap Rim"
    panel_label = label
    colorspace = "sRGB"

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MatcapSamplerPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        sampler: Mtoon1MatcapSamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1OutlineWidthMultiplyTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "outline_width_multiply_texture",
        "index",
    ]

    label = "Outline Width"
    panel_label = label
    colorspace = "Non-Color"

    def update_source(self, context: bpy.types.Context) -> None:
        mtoon = (
            self.find_material().vrm_addon_extension.mtoon1.extensions.vrmc_materials_mtoon
        )
        mtoon.update_outline_geometry(context)
        super().update_source(context)

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1OutlineWidthMultiplySamplerPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        sampler: Mtoon1OutlineWidthMultiplySamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1UvAnimationMaskTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = [
        "extensions",
        "vrmc_materials_mtoon",
        "uv_animation_mask_texture",
        "index",
    ]

    label = "UV Animation Mask"
    panel_label = "Mask"
    colorspace = "Non-Color"

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1UvAnimationMaskSamplerPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        sampler: Mtoon1UvAnimationMaskSamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1TextureInfoPropertyGroup(MaterialTraceablePropertyGroup):
    group_label_base_name: str = ""
    node_group_name: str = shader.OUTPUT_GROUP_NAME

    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1TexturePropertyGroup  # noqa: F722
    )

    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1TextureInfoExtensionsPropertyGroup  # noqa: F722
    )

    @dataclass(frozen=True)
    class TextureInfoBackup:
        source: bpy.types.Image
        mag_filter: str
        min_filter: str
        wrap_s: str
        wrap_t: str
        offset: tuple[float, float]
        scale: tuple[float, float]

    def backup(self) -> TextureInfoBackup:
        return Mtoon1TextureInfoPropertyGroup.TextureInfoBackup(
            source=self.index.source,
            mag_filter=self.index.sampler.mag_filter,
            min_filter=self.index.sampler.min_filter,
            wrap_s=self.index.sampler.wrap_s,
            wrap_t=self.index.sampler.wrap_t,
            offset=(
                self.extensions.khr_texture_transform.offset[0],
                self.extensions.khr_texture_transform.offset[1],
            ),
            scale=(
                self.extensions.khr_texture_transform.scale[0],
                self.extensions.khr_texture_transform.scale[1],
            ),
        )

    def restore(self, backup: TextureInfoBackup) -> None:
        # pylint: disable=attribute-defined-outside-init
        self.index.source = backup.source
        self.index.sampler.mag_filter = backup.mag_filter
        self.index.sampler.min_filter = backup.min_filter
        self.index.sampler.wrap_s = backup.wrap_s
        self.index.sampler.wrap_t = backup.wrap_t
        self.extensions.khr_texture_transform.offset = backup.offset
        self.extensions.khr_texture_transform.scale = backup.scale
        # pylint: enable=attribute-defined-outside-init

    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]


# https://github.com/KhronosGroup/glTF/blob/1ab49ec412e638f2e5af0289e9fbb60c7271e457/specification/2.0/schema/textureInfo.schema.json
class Mtoon1BaseColorTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    group_label_base_name = "Lit Color Texture"

    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1BaseColorTexturePropertyGroup  # noqa: F722
    )
    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1BaseColorTextureInfoExtensionsPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        index: Mtoon1BaseColorTexturePropertyGroup  # type: ignore[no-redef]
        extensions: Mtoon1BaseColorTextureInfoExtensionsPropertyGroup  # type: ignore[no-redef]


class Mtoon1ShadeMultiplyTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    group_label_base_name = "Shade Color Texture"

    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadeMultiplyTexturePropertyGroup  # noqa: F722
    )
    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadeMultiplyTextureInfoExtensionsPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        index: Mtoon1ShadeMultiplyTexturePropertyGroup  # type: ignore[no-redef]
        extensions: Mtoon1ShadeMultiplyTextureInfoExtensionsPropertyGroup  # type: ignore[no-redef]


# https://github.com/KhronosGroup/glTF/blob/1ab49ec412e638f2e5af0289e9fbb60c7271e457/specification/2.0/schema/material.normalTextureInfo.schema.json
class Mtoon1NormalTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    material_property_chain: list[str] = ["normal_texture"]
    group_label_base_name = "Normal Map Texture"
    node_group_name: str = shader.NORMAL_GROUP_NAME

    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1NormalTexturePropertyGroup  # noqa: F722
    )

    def update_scale(self, _context: bpy.types.Context) -> None:
        self.set_value(self.node_group_name, "Normal Map Texture Scale", self.scale)

    scale: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        default=1.0,
        update=update_scale,
    )

    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1NormalTextureInfoExtensionsPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        index: Mtoon1NormalTexturePropertyGroup  # type: ignore[no-redef]
        scale: float  # type: ignore[no-redef]
        extensions: Mtoon1NormalTextureInfoExtensionsPropertyGroup  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/c5d1afdc4d59c292cb4fd6d54cad1dc0c4d19c60/specification/VRMC_materials_mtoon-1.0/schema/mtoon.shadingShiftTexture.schema.json
class Mtoon1ShadingShiftTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    material_property_chain: list[str] = [
        "extensions",
        "vrmc_materials_mtoon",
        "shading_shift_texture",
    ]
    group_label_base_name = "Shading Shift Texture"

    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadingShiftTexturePropertyGroup  # noqa: F722
    )

    def update_scale(self, _context: bpy.types.Context) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME, "Shading Shift Texture Scale", self.scale
        )

    scale: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Scale",  # noqa: F821
        default=1.0,
        update=update_scale,
    )

    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadingShiftTextureInfoExtensionsPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        index: Mtoon1ShadingShiftTexturePropertyGroup  # type: ignore[no-redef]
        scale: float  # type: ignore[no-redef]
        extensions: Mtoon1ShadingShiftTextureInfoExtensionsPropertyGroup  # type: ignore[no-redef]


# https://github.com/KhronosGroup/glTF/blob/1ab49ec412e638f2e5af0289e9fbb60c7271e457/specification/2.0/schema/textureInfo.schema.json
class Mtoon1EmissiveTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    group_label_base_name = "Emissive Texture"

    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1EmissiveTexturePropertyGroup  # noqa: F722
    )
    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1EmissiveTextureInfoExtensionsPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        index: Mtoon1EmissiveTexturePropertyGroup  # type: ignore[no-redef]
        extensions: Mtoon1EmissiveTextureInfoExtensionsPropertyGroup  # type: ignore[no-redef]


class Mtoon1RimMultiplyTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    group_label_base_name = "Rim Color Texture"

    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1RimMultiplyTexturePropertyGroup  # noqa: F722
    )
    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1RimMultiplyTextureInfoExtensionsPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        index: Mtoon1RimMultiplyTexturePropertyGroup  # type: ignore[no-redef]
        extensions: Mtoon1RimMultiplyTextureInfoExtensionsPropertyGroup  # type: ignore[no-redef]


class Mtoon1MatcapTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    group_label_base_name = "MatCap Texture"

    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MatcapTexturePropertyGroup  # noqa: F722
    )
    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MatcapTextureInfoExtensionsPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        index: Mtoon1MatcapTexturePropertyGroup  # type: ignore[no-redef]
        extensions: Mtoon1MatcapTextureInfoExtensionsPropertyGroup  # type: ignore[no-redef]


class Mtoon1OutlineWidthMultiplyTextureInfoPropertyGroup(
    Mtoon1TextureInfoPropertyGroup
):
    group_label_base_name = "Outline Width Texture"

    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1OutlineWidthMultiplyTexturePropertyGroup  # noqa: F722
    )
    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1OutlineWidthMultiplyTextureInfoExtensionsPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        index: Mtoon1OutlineWidthMultiplyTexturePropertyGroup  # type: ignore[no-redef]
        extensions: Mtoon1OutlineWidthMultiplyTextureInfoExtensionsPropertyGroup  # type: ignore[no-redef]


class Mtoon1UvAnimationMaskTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    group_label_base_name = "Mask Texture"
    node_group_name: str = shader.UV_ANIMATION_GROUP_NAME

    index: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1UvAnimationMaskTexturePropertyGroup  # noqa: F722
    )
    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1UvAnimationMaskTextureInfoExtensionsPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        index: Mtoon1UvAnimationMaskTexturePropertyGroup  # type: ignore[no-redef]
        extensions: Mtoon1UvAnimationMaskTextureInfoExtensionsPropertyGroup  # type: ignore[no-redef]


class Mtoon0SamplerPropertyGroup(bpy.types.PropertyGroup):
    mag_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_items,
        name="Mag Filter",  # noqa: F722
    )

    min_filter: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_items,
        name="Min Filter",  # noqa: F722
    )

    wrap_s: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap S",  # noqa: F722
        default=Mtoon1SamplerPropertyGroup.WRAP_DEFAULT_ID,
    )

    wrap_t: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_items,
        name="Wrap T",  # noqa: F722
        default=Mtoon1SamplerPropertyGroup.WRAP_DEFAULT_ID,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        mag_filter: str  # type: ignore[no-redef]
        min_filter: str  # type: ignore[no-redef]
        wrap_s: str  # type: ignore[no-redef]
        wrap_t: str  # type: ignore[no-redef]


class Mtoon0TexturePropertyGroup(bpy.types.PropertyGroup):
    colorspace = "sRGB"

    source: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Image,  # noqa: F722
    )

    sampler: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon0SamplerPropertyGroup,  # noqa: F722
    )

    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        source: Optional[bpy.types.Image]  # type: ignore[no-redef]
        sampler: Mtoon0SamplerPropertyGroup  # type: ignore[no-redef]
        show_expanded: bool  # type: ignore[no-redef]


class Mtoon0ReceiveShadowTexturePropertyGroup(Mtoon0TexturePropertyGroup):
    label = "Shadow Receive Multiplier"
    panel_label = label
    colorspace = "Non-Color"


class Mtoon0ShadingGradeTexturePropertyGroup(Mtoon0TexturePropertyGroup):
    label = "Lit & Shade Mixing Multiplier"
    panel_label = label
    colorspace = "Non-Color"


# https://github.com/KhronosGroup/glTF/blob/1ab49ec412e638f2e5af0289e9fbb60c7271e457/specification/2.0/schema/material.pbrMetallicRoughness.schema.json#L9-L26
class Mtoon1PbrMetallicRoughnessPropertyGroup(MaterialTraceablePropertyGroup):
    material_property_chain = ["pbr_metallic_roughness"]

    def update_base_color_factor(self, _context: bpy.types.Context) -> None:
        self.set_rgba(shader.OUTPUT_GROUP_NAME, "Lit Color", self.base_color_factor)
        self.set_value(
            shader.OUTPUT_GROUP_NAME, "Lit Color Alpha", self.base_color_factor[3]
        )

    base_color_factor: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=4,
        subtype="COLOR",  # noqa: F821
        default=(1, 1, 1, 1),
        min=0,
        max=1,
        update=update_base_color_factor,
    )

    base_color_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1BaseColorTextureInfoPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        base_color_factor: Sequence[float]  # type: ignore[no-redef]
        base_color_texture: Mtoon1BaseColorTextureInfoPropertyGroup  # type: ignore[no-redef]


class Mtoon1VrmcMaterialsMtoonPropertyGroup(MaterialTraceablePropertyGroup):
    material_property_chain: list[str] = ["extensions", "vrmc_materials_mtoon"]

    def update_transparent_with_z_write(self, _context: bpy.types.Context) -> None:
        self.set_bool(
            shader.OUTPUT_GROUP_NAME,
            "Transparent With Z-Write",
            self.transparent_with_z_write,
        )

        # call update_mtoon0_render_queue()
        material = self.find_material()
        material.vrm_addon_extension.mtoon1.mtoon0_render_queue = (
            material.vrm_addon_extension.mtoon1.mtoon0_render_queue
        )

    transparent_with_z_write: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Transparent With ZWrite Mode",  # noqa: F722
        update=update_transparent_with_z_write,
    )

    def update_render_queue_offset_number(self, _context: bpy.types.Context) -> None:
        self.set_int(
            shader.OUTPUT_GROUP_NAME,
            "Render Queue Offset Number",
            self.render_queue_offset_number,
        )

    render_queue_offset_number: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="RenderQueue Offset",  # noqa: F722
        min=-9,
        default=0,
        max=9,
        update=update_render_queue_offset_number,
    )

    shade_multiply_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadeMultiplyTextureInfoPropertyGroup  # noqa: F722
    )

    def update_shade_color_factor(self, _context: bpy.types.Context) -> None:
        self.set_rgb(shader.OUTPUT_GROUP_NAME, "Shade Color", self.shade_color_factor)

    shade_color_factor: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="COLOR",  # noqa: F821
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        update=update_shade_color_factor,
    )

    shading_shift_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadingShiftTextureInfoPropertyGroup  # noqa: F722
    )

    def update_shading_shift_factor(self, _context: bpy.types.Context) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME, "Shading Shift", self.shading_shift_factor
        )

    shading_shift_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Shading Shift",  # noqa: F722
        soft_min=-1.0,
        default=-0.2,
        soft_max=1.0,
        update=update_shading_shift_factor,
    )

    def update_shading_toony_factor(self, _context: bpy.types.Context) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME, "Shading Toony", self.shading_toony_factor
        )

    shading_toony_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Shading Toony",  # noqa: F722
        min=0.0,
        default=0.9,
        max=1.0,
        update=update_shading_toony_factor,
    )

    def update_gi_equalization_factor(self, _context: bpy.types.Context) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME,
            "GI Equalization Factor",
            self.gi_equalization_factor,
        )

    gi_equalization_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="GI Equalization",  # noqa: F722
        min=0.0,
        default=0.9,
        max=1.0,
        update=update_gi_equalization_factor,
    )

    def update_matcap_factor(self, _context: bpy.types.Context) -> None:
        self.set_rgb(shader.OUTPUT_GROUP_NAME, "MatCap Factor", self.matcap_factor)

    matcap_factor: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="COLOR",  # noqa: F821
        default=(1, 1, 1),
        min=0,
        max=1,
        update=update_matcap_factor,
    )

    matcap_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MatcapTextureInfoPropertyGroup  # noqa: F722
    )

    def update_parametric_rim_color_factor(self, _context: bpy.types.Context) -> None:
        self.set_rgb(
            shader.OUTPUT_GROUP_NAME,
            "Parametric Rim Color",
            self.parametric_rim_color_factor,
        )

    parametric_rim_color_factor: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Parametric Rim Color",  # noqa: F722
        size=3,
        subtype="COLOR",  # noqa: F821
        default=(0, 0, 0),
        min=0,
        max=1,
        update=update_parametric_rim_color_factor,
    )

    rim_multiply_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1RimMultiplyTextureInfoPropertyGroup  # noqa: F722
    )

    def update_rim_lighting_mix_factor(self, _context: bpy.types.Context) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME, "Rim LightingMix", self.rim_lighting_mix_factor
        )

    rim_lighting_mix_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Rim LightingMix",  # noqa: F722
        soft_min=0,
        soft_max=1,
        update=update_rim_lighting_mix_factor,
    )

    def update_parametric_rim_fresnel_power_factor(
        self, _context: bpy.types.Context
    ) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME,
            "Parametric Rim Fresnel Power",
            self.parametric_rim_fresnel_power_factor,
        )

    parametric_rim_fresnel_power_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Parametric Rim Fresnel Power",  # noqa: F722
        min=0.0,
        default=1.0,
        soft_max=100.0,
        update=update_parametric_rim_fresnel_power_factor,
    )

    def update_parametric_rim_lift_factor(self, _context: bpy.types.Context) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME,
            "Parametric Rim Lift",
            self.parametric_rim_lift_factor,
        )

    parametric_rim_lift_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Parametric Rim Lift",  # noqa: F722
        soft_min=0.0,
        default=1.0,
        soft_max=1.0,
        update=update_parametric_rim_lift_factor,
    )

    OUTLINE_WIDTH_MODE_NONE = "none"
    OUTLINE_WIDTH_MODE_WORLD_COORDINATES = "worldCoordinates"
    OUTLINE_WIDTH_MODE_SCREEN_COORDINATES = "screenCoordinates"
    outline_width_mode_items: list[tuple[str, str, str, str, int]] = [
        (OUTLINE_WIDTH_MODE_NONE, "None", "", "NONE", 0),
        (OUTLINE_WIDTH_MODE_WORLD_COORDINATES, "World Coordinates", "", "NONE", 1),
        (OUTLINE_WIDTH_MODE_SCREEN_COORDINATES, "Screen Coordinates", "", "NONE", 2),
    ]
    OUTLINE_WIDTH_MODE_IDS = [
        outline_width_mode_item[0]
        for outline_width_mode_item in outline_width_mode_items
    ]

    def update_outline_geometry(self, _context: bpy.types.Context) -> None:
        material = self.find_material()
        if material.vrm_addon_extension.mtoon1.is_outline_material:
            return
        bpy.ops.vrm.refresh_mtoon1_outline(
            material_name=material.name, create_modifier=True
        )

    outline_width_mode: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=outline_width_mode_items,
        name="Outline Width Mode",  # noqa: F722
        update=update_outline_geometry,
    )

    def update_outline_width_factor(self, context: bpy.types.Context) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME, "Outline Width", self.outline_width_factor
        )
        self.update_outline_geometry(context)

    outline_width_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Outline Width",  # noqa: F722
        min=0.0,
        soft_max=0.05,
        update=update_outline_width_factor,
    )

    outline_width_multiply_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1OutlineWidthMultiplyTextureInfoPropertyGroup  # noqa: F722
    )

    def update_outline_color_factor(self, context: bpy.types.Context) -> None:
        self.set_rgb(
            shader.OUTPUT_GROUP_NAME, "Outline Color", self.outline_color_factor
        )
        self.update_outline_geometry(context)

    outline_color_factor: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Outline Color",  # noqa: F722
        size=3,
        subtype="COLOR",  # noqa: F821
        default=(0, 0, 0),
        min=0,
        max=1,
        update=update_outline_color_factor,
    )

    def update_outline_lighting_mix_factor(self, context: bpy.types.Context) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME,
            "Outline LightingMix",
            self.outline_lighting_mix_factor,
        )
        self.update_outline_geometry(context)

    outline_lighting_mix_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Outline LightingMix",  # noqa: F722
        min=0.0,
        default=1.0,
        max=1.0,
        update=update_outline_lighting_mix_factor,
    )

    uv_animation_mask_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1UvAnimationMaskTextureInfoPropertyGroup  # noqa: F722
    )

    def update_uv_animation_scroll_x_speed_factor(
        self, _context: bpy.types.Context
    ) -> None:
        self.set_value(
            shader.UV_ANIMATION_GROUP_NAME,
            "Translate X",
            self.uv_animation_scroll_x_speed_factor,
        )

    uv_animation_scroll_x_speed_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Translate X",  # noqa: F722
        update=update_uv_animation_scroll_x_speed_factor,
    )

    def update_uv_animation_scroll_y_speed_factor(
        self, _context: bpy.types.Context
    ) -> None:
        self.set_value(
            shader.UV_ANIMATION_GROUP_NAME,
            "Translate Y",
            self.uv_animation_scroll_y_speed_factor,
        )

    uv_animation_scroll_y_speed_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Translate Y",  # noqa: F722
        update=update_uv_animation_scroll_y_speed_factor,
    )

    def update_uv_animation_rotation_speed_factor(
        self, _context: bpy.types.Context
    ) -> None:
        self.set_value(
            shader.UV_ANIMATION_GROUP_NAME,
            "Rotation",
            self.uv_animation_rotation_speed_factor,
        )

    uv_animation_rotation_speed_factor: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Rotation",  # noqa: F821
        update=update_uv_animation_rotation_speed_factor,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        transparent_with_z_write: bool  # type: ignore[no-redef]
        render_queue_offset_number: int  # type: ignore[no-redef]
        shade_multiply_texture: Mtoon1ShadeMultiplyTextureInfoPropertyGroup  # type: ignore[no-redef]
        shade_color_factor: Sequence[float]  # type: ignore[no-redef]
        shading_shift_texture: Mtoon1ShadingShiftTextureInfoPropertyGroup  # type: ignore[no-redef]
        shading_shift_factor: float  # type: ignore[no-redef]
        shading_toony_factor: float  # type: ignore[no-redef]
        gi_equalization_factor: float  # type: ignore[no-redef]
        matcap_factor: Sequence[float]  # type: ignore[no-redef]
        matcap_texture: Mtoon1MatcapTextureInfoPropertyGroup  # type: ignore[no-redef]
        parametric_rim_color_factor: Sequence[float]  # type: ignore[no-redef]
        rim_multiply_texture: Mtoon1RimMultiplyTextureInfoPropertyGroup  # type: ignore[no-redef]
        rim_lighting_mix_factor: float  # type: ignore[no-redef]
        parametric_rim_fresnel_power_factor: float  # type: ignore[no-redef]
        parametric_rim_lift_factor: float  # type: ignore[no-redef]
        outline_width_mode: str  # type: ignore[no-redef]
        outline_width_factor: float  # type: ignore[no-redef]
        outline_width_multiply_texture: Mtoon1OutlineWidthMultiplyTextureInfoPropertyGroup  # type: ignore[no-redef]
        outline_color_factor: Sequence[float]  # type: ignore[no-redef]
        outline_lighting_mix_factor: float  # type: ignore[no-redef]
        uv_animation_mask_texture: Mtoon1UvAnimationMaskTextureInfoPropertyGroup  # type: ignore[no-redef]
        uv_animation_scroll_x_speed_factor: float  # type: ignore[no-redef]
        uv_animation_scroll_y_speed_factor: float  # type: ignore[no-redef]
        uv_animation_rotation_speed_factor: float  # type: ignore[no-redef]


# https://github.com/KhronosGroup/glTF/blob/d997b7dc7e426bc791f5613475f5b4490da0b099/extensions/2.0/Khronos/KHR_materials_emissive_strength/schema/glTF.KHR_materials_emissive_strength.schema.json
class Mtoon1KhrMaterialsEmissiveStrengthPropertyGroup(MaterialTraceablePropertyGroup):
    material_property_chain: list[str] = [
        "extensions",
        "khr_materials_emissive_strength",
    ]

    def update_emissive_strength(self, _context: bpy.types.Context) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME, "Emissive Strength", self.emissive_strength
        )

    emissive_strength: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Strength",  # noqa: F821
        min=0.0,
        default=1.0,
        update=update_emissive_strength,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        emissive_strength: float  # type: ignore[no-redef]


class Mtoon1MaterialExtensionsPropertyGroup(bpy.types.PropertyGroup):
    vrmc_materials_mtoon: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1VrmcMaterialsMtoonPropertyGroup  # noqa: F722
    )
    khr_materials_emissive_strength: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1KhrMaterialsEmissiveStrengthPropertyGroup  # noqa: F722
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        vrmc_materials_mtoon: Mtoon1VrmcMaterialsMtoonPropertyGroup  # type: ignore[no-redef]
        khr_materials_emissive_strength: Mtoon1KhrMaterialsEmissiveStrengthPropertyGroup  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/8dc51ec7241be27ee95f159cefc0190a0e41967b/specification/VRMC_materials_mtoon-1.0-beta/schema/VRMC_materials_mtoon.schema.json
class Mtoon1MaterialPropertyGroup(MaterialTraceablePropertyGroup):
    material_property_chain: list[str] = []

    INITIAL_ADDON_VERSION = VrmAddonPreferences.INITIAL_ADDON_VERSION

    addon_version: bpy.props.IntVectorProperty(  # type: ignore[valid-type]
        size=3,  # noqa: F722
        default=INITIAL_ADDON_VERSION,
    )

    pbr_metallic_roughness: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1PbrMetallicRoughnessPropertyGroup  # noqa: F722
    )

    ALPHA_MODE_OPAQUE = "OPAQUE"
    ALPHA_MODE_OPAQUE_VALUE = 0
    ALPHA_MODE_MASK = "MASK"
    ALPHA_MODE_MASK_VALUE = 1
    ALPHA_MODE_BLEND = "BLEND"
    ALPHA_MODE_BLEND_VALUE = 2
    alpha_mode_items: list[tuple[str, str, str, str, int]] = [
        (ALPHA_MODE_OPAQUE, "Opaque", "", "NONE", ALPHA_MODE_OPAQUE_VALUE),
        (ALPHA_MODE_MASK, "Cutout", "", "NONE", ALPHA_MODE_MASK_VALUE),
        (ALPHA_MODE_BLEND, "Transparent", "", "NONE", ALPHA_MODE_BLEND_VALUE),
    ]
    ALPHA_MODE_IDS = [alpha_mode_item[0] for alpha_mode_item in alpha_mode_items]

    alpha_mode_blend_method_hashed: bpy.props.BoolProperty()  # type: ignore[valid-type]

    def get_alpha_mode(self) -> int:
        # https://docs.blender.org/api/2.93/bpy.types.Material.html#bpy.types.Material.blend_method
        blend_method = self.find_material().blend_method
        if blend_method == "OPAQUE":
            return self.ALPHA_MODE_OPAQUE_VALUE
        if blend_method == "CLIP":
            return self.ALPHA_MODE_MASK_VALUE
        if blend_method in ["HASHED", "BLEND"]:
            return self.ALPHA_MODE_BLEND_VALUE
        raise ValueError(f"Unexpected blend_method: {blend_method}")

    def set_alpha_mode(self, value: int) -> None:
        material = self.find_material()
        if material.blend_method == "HASHED":
            self.alpha_mode_blend_method_hashed = True
        if material.blend_method == "BLEND":
            self.alpha_mode_blend_method_hashed = False

        if value == self.ALPHA_MODE_OPAQUE_VALUE:
            material.blend_method = "OPAQUE"
            shadow_method = "OPAQUE"
        elif value == self.ALPHA_MODE_MASK_VALUE:
            material.blend_method = "CLIP"
            shadow_method = "CLIP"
        elif value == self.ALPHA_MODE_BLEND_VALUE:
            material.blend_method = "HASHED"
            shadow_method = "HASHED"
        else:
            logger.error("Unexpected alpha mode: {value}")
            material.blend_method = "OPAQUE"
            shadow_method = "OPAQUE"

        # call self.update_mtoon0_render_queue()
        self.mtoon0_render_queue = self.mtoon0_render_queue

        if material.vrm_addon_extension.mtoon1.is_outline_material:
            material.shadow_method = "NONE"
            return

        material.shadow_method = shadow_method

        outline_material = material.vrm_addon_extension.mtoon1.outline_material
        if not outline_material:
            return
        outline_material.vrm_addon_extension.mtoon1.set_alpha_mode(value)

    alpha_mode: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=alpha_mode_items,
        name="Alpha Mode",  # noqa: F722
        get=get_alpha_mode,
        set=set_alpha_mode,
    )

    def get_double_sided(self) -> bool:
        return not self.find_material().use_backface_culling

    def set_double_sided(self, value: bool) -> None:
        material = self.find_material()
        material.use_backface_culling = not value
        self.set_bool(shader.OUTPUT_GROUP_NAME, "Double Sided", value)
        if material.vrm_addon_extension.mtoon1.is_outline_material:
            return
        outline_material = material.vrm_addon_extension.mtoon1.outline_material
        if not outline_material:
            return
        outline_material.vrm_addon_extension.mtoon1.double_sided = False

    double_sided: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Double Sided",  # noqa: F722
        get=get_double_sided,
        set=set_double_sided,
    )

    def get_alpha_cutoff(self) -> float:
        return max(0, min(1, float(self.find_material().alpha_threshold)))

    def set_alpha_cutoff(self, value: float) -> None:
        material = self.find_material()
        material.alpha_threshold = max(0, min(1, value))

        if material.vrm_addon_extension.mtoon1.is_outline_material:
            return
        outline_material = material.vrm_addon_extension.mtoon1.outline_material
        if not outline_material:
            return
        outline_material.vrm_addon_extension.mtoon1.set_alpha_cutoff(value)

    alpha_cutoff: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Cutoff",  # noqa: F821
        min=0,
        soft_max=1,
        get=get_alpha_cutoff,
        set=set_alpha_cutoff,
    )

    normal_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1NormalTextureInfoPropertyGroup  # noqa: F722
    )

    emissive_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1EmissiveTextureInfoPropertyGroup  # noqa: F722
    )

    def update_emissive_factor(self, _context: bpy.types.Context) -> None:
        self.set_rgb(shader.OUTPUT_GROUP_NAME, "Emissive Factor", self.emissive_factor)

    emissive_factor: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="COLOR",  # noqa: F821
        default=(0, 0, 0),
        min=0,
        max=1,
        update=update_emissive_factor,
    )

    extensions: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MaterialExtensionsPropertyGroup  # noqa: F722
    )

    def get_enabled_in_material(self, material: bpy.types.Material) -> bool:
        if self.is_outline_material:
            return False
        if not material.use_nodes:
            return False
        if not material.node_tree:
            return False

        group_node = material.node_tree.nodes.get("Mtoon1Material.Mtoon1Output")
        if (
            isinstance(group_node, bpy.types.ShaderNodeGroup)
            and group_node.node_tree
            and group_node.node_tree.name == shader.OUTPUT_GROUP_NAME
        ):
            return bool(self.get("enabled"))

        return False

    def get_enabled(self) -> bool:
        return self.get_enabled_in_material(self.find_material())

    def set_enabled(self, value: bool) -> None:
        material = self.find_material()

        if not value:
            if self.get("enabled") and material.use_nodes:
                bpy.ops.vrm.convert_mtoon1_to_bsdf_principled(
                    material_name=material.name
                )
            self["enabled"] = False
            return

        if not material.use_nodes:
            material.use_nodes = True
        if self.get_enabled():
            return

        bpy.ops.vrm.convert_material_to_mtoon1(material_name=material.name)
        self["enabled"] = True

    enabled: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Enable VRM MToon Material",  # noqa: F722
        get=get_enabled,
        set=set_enabled,
    )

    export_shape_key_normals: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export Shape Key Normals",  # noqa: F722
    )

    def update_is_outline_material(self, _context: bpy.types.Context) -> None:
        self.set_bool(shader.OUTPUT_GROUP_NAME, "Is Outline", self.is_outline_material)
        self.set_bool(
            shader.NORMAL_GROUP_NAME,
            "Is Outline",
            self.is_outline_material,
        )
        self.set_bool(
            shader.OUTPUT_GROUP_NAME,
            "Double Sided",
            False if self.is_outline_material else self.double_sided,
        )

    is_outline_material: bpy.props.BoolProperty(  # type: ignore[valid-type]
        update=update_is_outline_material,
    )

    outline_material: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Material,
    )

    def all_texture_info(self) -> list[Mtoon1TextureInfoPropertyGroup]:
        return [
            self.pbr_metallic_roughness.base_color_texture,
            self.normal_texture,
            self.emissive_texture,
            self.extensions.vrmc_materials_mtoon.shade_multiply_texture,
            self.extensions.vrmc_materials_mtoon.shading_shift_texture,
            self.extensions.vrmc_materials_mtoon.matcap_texture,
            self.extensions.vrmc_materials_mtoon.rim_multiply_texture,
            self.extensions.vrmc_materials_mtoon.outline_width_multiply_texture,
            self.extensions.vrmc_materials_mtoon.uv_animation_mask_texture,
        ]

    def all_textures(
        self, downgrade_to_mtoon0: bool
    ) -> list[Union[Mtoon0TexturePropertyGroup, Mtoon1TexturePropertyGroup]]:
        # TODO: remove code duplication
        result: list[Union[Mtoon0TexturePropertyGroup, Mtoon1TexturePropertyGroup]] = []
        result.extend(
            [
                self.pbr_metallic_roughness.base_color_texture.index,
                self.extensions.vrmc_materials_mtoon.shade_multiply_texture.index,
                self.normal_texture.index,
            ]
        )
        if downgrade_to_mtoon0:
            result.extend(
                [
                    self.mtoon0_receive_shadow_texture,
                    self.mtoon0_shading_grade_texture,
                ]
            )
        result.append(self.emissive_texture.index)
        if not downgrade_to_mtoon0:
            result.append(
                self.extensions.vrmc_materials_mtoon.shading_shift_texture.index
            )
        result.extend(
            [
                self.extensions.vrmc_materials_mtoon.matcap_texture.index,
                self.extensions.vrmc_materials_mtoon.rim_multiply_texture.index,
                self.extensions.vrmc_materials_mtoon.outline_width_multiply_texture.index,
                self.extensions.vrmc_materials_mtoon.uv_animation_mask_texture.index,
            ]
        )
        return result

    show_expanded_mtoon0: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Show MToon 0.0 Options",  # noqa: F722
    )

    mtoon0_front_cull_mode: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Front Face Culling",  # noqa: F722
    )

    mtoon0_outline_scaled_max_distance: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Outline Width Scaled Max Distance",  # noqa: F722
        min=1,
        default=1,
        max=10,
    )

    mtoon0_light_color_attenuation: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="LightColor Attenuation",  # noqa: F722
        min=0,
        default=0,
        max=1,
    )

    mtoon0_receive_shadow_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon0ReceiveShadowTexturePropertyGroup  # noqa: F722
    )

    mtoon0_receive_shadow_rate: bpy.props.FloatProperty(  # type: ignore[valid-type]
        min=0,
        default=1,
        max=1,
    )

    mtoon0_shading_grade_texture: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=Mtoon0ShadingGradeTexturePropertyGroup  # noqa: F722
    )

    mtoon0_shading_grade_rate: bpy.props.FloatProperty(  # type: ignore[valid-type]
        min=0,
        default=1,
        max=1,
    )

    mtoon0_rim_lighting_mix: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Rim LightingMix (MToon 0.0)",  # noqa: F722
        min=0,
        default=0,
        max=1,
    )

    def update_mtoon0_render_queue(self, _context: bpy.types.Context) -> None:
        # https://github.com/Santarh/MToon/blob/42b03163459ac8e6b7aee08070d0f4f912035069/MToon/Scripts/Utils.cs#L74-L113
        if self.alpha_mode == self.ALPHA_MODE_OPAQUE:
            mtoon0_render_queue = 2000
        elif self.alpha_mode == self.ALPHA_MODE_MASK:
            mtoon0_render_queue = 2450
        elif not self.extensions.vrmc_materials_mtoon.transparent_with_z_write:
            mtoon0_render_queue = max(2951, min(3000, self.mtoon0_render_queue))
        else:
            mtoon0_render_queue = max(2501, min(2550, self.mtoon0_render_queue))
        if self.mtoon0_render_queue != mtoon0_render_queue:
            self.mtoon0_render_queue = mtoon0_render_queue

    mtoon0_render_queue: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="Render Queue",  # noqa: F722
        default=2000,
        update=update_mtoon0_render_queue,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        addon_version: Sequence[int]  # type: ignore[no-redef]
        pbr_metallic_roughness: Mtoon1PbrMetallicRoughnessPropertyGroup  # type: ignore[no-redef]
        alpha_mode_blend_method_hashed: bool  # type: ignore[no-redef]
        alpha_mode: str  # type: ignore[no-redef]
        double_sided: bool  # type: ignore[no-redef]
        alpha_cutoff: float  # type: ignore[no-redef]
        normal_texture: Mtoon1NormalTextureInfoPropertyGroup  # type: ignore[no-redef]
        emissive_texture: Mtoon1EmissiveTextureInfoPropertyGroup  # type: ignore[no-redef]
        emissive_factor: Sequence[float]  # type: ignore[no-redef]
        extensions: Mtoon1MaterialExtensionsPropertyGroup  # type: ignore[no-redef]
        enabled: bool  # type: ignore[no-redef]
        export_shape_key_normals: bool  # type: ignore[no-redef]
        is_outline_material: bool  # type: ignore[no-redef]
        outline_material: Optional[bpy.types.Material]  # type: ignore[no-redef]
        show_expanded_mtoon0: bool  # type: ignore[no-redef]
        mtoon0_front_cull_mode: bool  # type: ignore[no-redef]
        mtoon0_outline_scaled_max_distance: float  # type: ignore[no-redef]
        mtoon0_light_color_attenuation: float  # type: ignore[no-redef]
        mtoon0_receive_shadow_texture: Mtoon0ReceiveShadowTexturePropertyGroup  # type: ignore[no-redef]
        mtoon0_receive_shadow_rate: float  # type: ignore[no-redef]
        mtoon0_shading_grade_texture: Mtoon0ShadingGradeTexturePropertyGroup  # type: ignore[no-redef]
        mtoon0_shading_grade_rate: float  # type: ignore[no-redef]
        mtoon0_rim_lighting_mix: float  # type: ignore[no-redef]
        mtoon0_render_queue: int  # type: ignore[no-redef]


def reset_shader_node_group(
    context: bpy.types.Context,
    material: bpy.types.Material,
    reset_node_tree: bool,
    overwrite: bool,
) -> None:
    gltf = material.vrm_addon_extension.mtoon1
    mtoon = gltf.extensions.vrmc_materials_mtoon

    base_color_factor = list(gltf.pbr_metallic_roughness.base_color_factor)
    base_color_texture = gltf.pbr_metallic_roughness.base_color_texture.backup()
    alpha_mode_blend_method_hashed = gltf.alpha_mode_blend_method_hashed
    alpha_mode = gltf.alpha_mode
    double_sided = gltf.double_sided
    alpha_cutoff = gltf.alpha_cutoff
    normal_texture = gltf.normal_texture.backup()
    normal_texture_scale = gltf.normal_texture.scale
    emissive_texture = gltf.emissive_texture.backup()
    emissive_factor = list(gltf.emissive_factor)
    export_shape_key_normals = gltf.export_shape_key_normals
    emissive_strength = (
        gltf.extensions.khr_materials_emissive_strength.emissive_strength
    )

    transparent_with_z_write = mtoon.transparent_with_z_write
    render_queue_offset_number = mtoon.render_queue_offset_number
    shade_multiply_texture = mtoon.shade_multiply_texture.backup()
    shade_color_factor = list(mtoon.shade_color_factor)
    shading_shift_texture = mtoon.shading_shift_texture.backup()
    shading_shift_texture_scale = mtoon.shading_shift_texture.scale
    shading_shift_factor = mtoon.shading_shift_factor
    shading_toony_factor = mtoon.shading_toony_factor
    gi_equalization_factor = mtoon.gi_equalization_factor
    matcap_factor = mtoon.matcap_factor
    matcap_texture = mtoon.matcap_texture.backup()
    parametric_rim_color_factor = list(mtoon.parametric_rim_color_factor)
    rim_multiply_texture = mtoon.rim_multiply_texture.backup()
    rim_lighting_mix_factor = mtoon.rim_lighting_mix_factor
    parametric_rim_fresnel_power_factor = mtoon.parametric_rim_fresnel_power_factor
    parametric_rim_lift_factor = mtoon.parametric_rim_lift_factor
    outline_width_mode = mtoon.outline_width_mode
    outline_width_factor = mtoon.outline_width_factor
    outline_width_multiply_texture = mtoon.outline_width_multiply_texture.backup()
    outline_color_factor = list(mtoon.outline_color_factor)
    outline_lighting_mix_factor = mtoon.outline_lighting_mix_factor
    uv_animation_mask_texture = mtoon.uv_animation_mask_texture.backup()
    uv_animation_scroll_x_speed_factor = mtoon.uv_animation_scroll_x_speed_factor
    uv_animation_scroll_y_speed_factor = mtoon.uv_animation_scroll_y_speed_factor
    uv_animation_rotation_speed_factor = mtoon.uv_animation_rotation_speed_factor

    if reset_node_tree:
        shader.load_mtoon1_shader(context, material, overwrite)
        if gltf.outline_material:
            shader.load_mtoon1_shader(context, gltf.outline_material, overwrite)

    gltf.is_outline_material = False
    if gltf.outline_material:
        gltf.outline_material.vrm_addon_extension.mtoon1.is_outline_material = True

    gltf.pbr_metallic_roughness.base_color_factor = base_color_factor
    gltf.pbr_metallic_roughness.base_color_texture.restore(base_color_texture)
    gltf.alpha_mode_blend_method_hashed = alpha_mode_blend_method_hashed
    gltf.alpha_mode = alpha_mode
    gltf.double_sided = double_sided
    gltf.alpha_cutoff = alpha_cutoff
    gltf.normal_texture.restore(normal_texture)
    gltf.normal_texture.scale = normal_texture_scale
    gltf.emissive_texture.restore(emissive_texture)
    gltf.emissive_factor = emissive_factor
    gltf.export_shape_key_normals = export_shape_key_normals
    gltf.extensions.khr_materials_emissive_strength.emissive_strength = (
        emissive_strength
    )

    mtoon.transparent_with_z_write = transparent_with_z_write
    mtoon.render_queue_offset_number = render_queue_offset_number
    mtoon.shade_multiply_texture.restore(shade_multiply_texture)
    mtoon.shade_color_factor = shade_color_factor
    mtoon.shading_shift_texture.restore(shading_shift_texture)
    mtoon.shading_shift_texture.scale = shading_shift_texture_scale
    mtoon.shading_shift_factor = shading_shift_factor
    mtoon.shading_toony_factor = shading_toony_factor
    mtoon.gi_equalization_factor = gi_equalization_factor
    mtoon.matcap_factor = matcap_factor
    mtoon.matcap_texture.restore(matcap_texture)
    mtoon.parametric_rim_color_factor = parametric_rim_color_factor
    mtoon.rim_multiply_texture.restore(rim_multiply_texture)
    mtoon.rim_lighting_mix_factor = rim_lighting_mix_factor
    mtoon.parametric_rim_fresnel_power_factor = parametric_rim_fresnel_power_factor
    mtoon.parametric_rim_lift_factor = parametric_rim_lift_factor
    mtoon.outline_width_mode = outline_width_mode
    mtoon.outline_width_factor = outline_width_factor
    mtoon.outline_width_multiply_texture.restore(outline_width_multiply_texture)
    mtoon.outline_color_factor = outline_color_factor
    mtoon.outline_lighting_mix_factor = outline_lighting_mix_factor
    mtoon.uv_animation_mask_texture.restore(uv_animation_mask_texture)
    mtoon.uv_animation_scroll_x_speed_factor = uv_animation_scroll_x_speed_factor
    mtoon.uv_animation_scroll_y_speed_factor = uv_animation_scroll_y_speed_factor
    mtoon.uv_animation_rotation_speed_factor = uv_animation_rotation_speed_factor

    gltf.addon_version = addon_version()
