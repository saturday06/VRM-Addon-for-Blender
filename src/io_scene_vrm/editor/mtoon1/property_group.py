# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import functools
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Final, Optional, Protocol, Union

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    IntVectorProperty,
    PointerProperty,
)
from bpy.types import (
    Context,
    Driver,
    FCurve,
    Image,
    Material,
    Node,
    NodeReroute,
    NodeSocketColor,
    NodeSocketFloat,
    PropertyGroup,
    ShaderNodeBsdfPrincipled,
    ShaderNodeEmission,
    ShaderNodeGroup,
    ShaderNodeMath,
    ShaderNodeNormalMap,
    ShaderNodeTexImage,
)
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
from mathutils import Vector

from ...common import convert, ops, shader
from ...common.gl import (
    GL_CLAMP_TO_EDGE,
    GL_LINEAR,
    GL_LINEAR_MIPMAP_LINEAR,
    GL_LINEAR_MIPMAP_NEAREST,
    GL_MIRRORED_REPEAT,
    GL_NEAREST,
    GL_NEAREST_MIPMAP_LINEAR,
    GL_NEAREST_MIPMAP_NEAREST,
    GL_REPEAT,
)
from ...common.logger import get_logger
from ...common.preferences import VrmAddonPreferences
from ...common.version import get_addon_version
from ..property_group import property_group_enum

logger = get_logger(__name__)


MTOON1_OUTPUT_NODE_GROUP_NAME: Final = "Mtoon1Material.Mtoon1Output"

PRINCIPLED_BSDF_BASE_COLOR_INPUT_KEY: Final = "Base Color"
PRINCIPLED_BSDF_ALPHA_INPUT_KEY: Final = "Alpha"
PRINCIPLED_BSDF_EMISSION_INPUT_KEY: Final = (
    "Emission Color" if bpy.app.version >= (4,) else "Emission"
)
PRINCIPLED_BSDF_EMISSION_STRENGTH_INPUT_KEY: Final = "Emission Strength"
PRINCIPLED_BSDF_NORMAL_INPUT_KEY: Final = "Normal"
NORMAL_MAP_COLOR_INPUT_KEY: Final = "Color"
EMISSION_COLOR_INPUT_KEY: Final = "Color"
EMISSION_STRENGTH_INPUT_KEY: Final = "Strength"
TEX_IMAGE_COLOR_OUTPUT_KEY: Final = "Color"
TEX_IMAGE_ALPHA_OUTPUT_KEY: Final = "Alpha"

IMAGE_INTERPOLATION_CLOSEST: Final = "Closest"
IMAGE_INTERPOLATION_LINEAR: Final = "Linear"
IMAGE_INTERPOLATION_CUBIC: Final = "Cubic"
IMAGE_INTERPOLATION_SMART: Final = "Smart"
GL_LINEAR_IMAGE_INTERPOLATIONS: Final = (
    IMAGE_INTERPOLATION_LINEAR,
    IMAGE_INTERPOLATION_CUBIC,
    IMAGE_INTERPOLATION_SMART,
)

ALPHA_CLIP_INPUT_NODE_NAME: Final = "Mtoon1Material.AlphaClip.Input"
ALPHA_CLIP_INPUT_NODE_SOCKET_NAME: Final = "Value"
ALPHA_CLIP_OUTPUT_NODE_NAME: Final = "Mtoon1Material.AlphaClip.Output"
ALPHA_CLIP_OUTPUT_NODE_SOCKET_NAME: Final = "Value"


def get_gltf_emissive_node(material: Material) -> Optional[ShaderNodeEmission]:
    node_tree = material.node_tree
    if not node_tree:
        return None
    return next(
        (
            node
            for node in node_tree.nodes
            if isinstance(node, ShaderNodeEmission)
            and node.name == "Mtoon1Material.GltfEmissive"
        ),
        None,
    )


class NodeSocketTarget(Protocol):
    def get_in_socket_name(self) -> str: ...

    def create_node_selector(self, material: Material) -> Callable[[Node], bool]: ...


class PrincipledBsdfNodeSocketTarget(NodeSocketTarget):
    def __init__(self, *, in_socket_name: str) -> None:
        self.in_socket_name = in_socket_name

    def get_in_socket_name(self) -> str:
        return self.in_socket_name

    @staticmethod
    def get_node_name(material: Material) -> Optional[str]:
        # nodeはネイティブ側の生存期間が短く危険なため、関数の外に露出しないようにする
        node = PrincipledBSDFWrapper(material).node_principled_bsdf
        if node is None:
            return None
        # internを用い、将来破棄されるnodeから直接参照されているstrを使わない
        # 以前、破棄されたBoneから参照されていたstrを使うと壊れていたことがある
        # のでそれを意識しての対応だが、気にしすぎかもしれない
        return sys.intern(node.name)

    def create_node_selector(self, material: Material) -> Callable[[Node], bool]:
        name = self.get_node_name(material)
        if name is None:
            return lambda _: False
        return (
            lambda node: isinstance(node, ShaderNodeBsdfPrincipled)
            and node.name == name
        )


class StaticNodeSocketTarget(NodeSocketTarget):
    def __init__(
        self, *, in_node_name: str, in_node_type: type[Node], in_socket_name: str
    ) -> None:
        self.in_node_name = in_node_name
        self.in_node_type = in_node_type
        self.in_socket_name = in_socket_name

    def get_in_socket_name(self) -> str:
        return self.in_socket_name

    def create_node_selector(self, material: Material) -> Callable[[Node], bool]:
        _ = material
        return (
            lambda node: isinstance(node, self.in_node_type)
            and node.name == self.in_node_name
        )


class PrincipledBsdfNormalMapNodeSocketTarget(NodeSocketTarget):
    def get_in_socket_name(self) -> str:
        return NORMAL_MAP_COLOR_INPUT_KEY

    @staticmethod
    def get_node_name(material: Material) -> Optional[str]:
        # nodeはネイティブ側の生存期間が短く危険なため、関数の外に露出しないようにする
        node = PrincipledBSDFWrapper(material).node_normalmap
        if node is None:
            return None
        # internを用い、将来破棄されるnodeから直接参照されているstrを使わない
        # 以前、破棄されたBoneから参照されていたstrを使うと壊れていたことがある
        # のでそれを意識しての対応だが、気にしすぎかもしれない
        return sys.intern(node.name)

    def create_node_selector(self, material: Material) -> Callable[[Node], bool]:
        name = self.get_node_name(material)
        if name is None:
            return lambda _: False
        return lambda node: isinstance(node, ShaderNodeNormalMap) and node.name == name


class GltfEmissionNodeSocketTarget(NodeSocketTarget):
    def get_in_socket_name(self) -> str:
        return EMISSION_COLOR_INPUT_KEY

    def create_node_selector(self, material: Material) -> Callable[[Node], bool]:
        _ = material
        # https://github.com/KhronosGroup/glTF-Blender-IO/pull/740
        return lambda node: isinstance(node, ShaderNodeEmission)


class NodeGroupSocketTarget(NodeSocketTarget):
    def __init__(self, *, node_group_node_tree_name: str, in_socket_name: str) -> None:
        self.node_group_node_tree_name = node_group_node_tree_name
        self.in_socket_name = in_socket_name

    def get_in_socket_name(self) -> str:
        return self.in_socket_name

    def select_node(self, node: Node) -> bool:
        if not isinstance(node, ShaderNodeGroup):
            return False
        node_tree = node.node_tree
        if not node_tree:
            return False
        return node_tree.name == self.node_group_node_tree_name

    def create_node_selector(self, material: Material) -> Callable[[Node], bool]:
        _ = material
        return self.select_node


class MaterialTraceablePropertyGroup(PropertyGroup):
    SELF_KEY_NUMBER_TO_MATERIAL_INDEX_CACHE: Final[dict[int, int]] = {}
    """selfを示す数値と、それに対応するマテリアルのインデックスのキャッシュ.

    本来ならselfからMaterialを引ける弱参照キャッシュにしたい。しかしそれらは
    ネイティブオブジェクトであり、そのままキャッシュをするのは非常に危険になる。
    そのため、代わりにselfに対応する数値からマテリアルのインデックスを引ける
    キャッシュにした。
    """

    def match_material(
        self, material: Material, material_property_chain: Sequence[str]
    ) -> bool:
        """selfに対応するマテリアルかどうかを調べる."""
        property_group: object = get_material_mtoon1_extension(material)
        for material_property in material_property_chain:
            property_group = getattr(property_group, material_property, None)
        return property_group == self

    def find_material(self) -> Material:
        """selfに対応するマテリアルを取得する.

        このメソッドは利用頻度が高いので、プロファイルの結果に気をつける。
        """
        context = bpy.context

        if self.id_data and self.id_data.is_evaluated:
            logger.error("%s is evaluated. May cause a problem.", self)

        material_property_chain = self.get_material_property_chain()

        # この関数を以前実行した際のキャッシュが残っているかを調べる。
        # キャッシュを使わない場合、リニアサーチが必要になり遅いことがわかっているため、
        # 結果をキャッシュして再利用を試みる。
        self_key_number = (
            # ポインタをそのまま使わないで欲しいという気持ちを込める
            ~self.as_pointer() ^ 0x01234567_89ABCDEF
        )
        cached_material_index = self.SELF_KEY_NUMBER_TO_MATERIAL_INDEX_CACHE.get(
            self_key_number
        )
        if cached_material_index is not None:
            # キャッシュが残っている場合は、そのキャッシュが現在も有効かをチェックする
            if (
                0 <= cached_material_index < len(context.blend_data.materials)
                and (
                    cached_material := context.blend_data.materials[
                        cached_material_index
                    ]
                )
                and self.match_material(cached_material, material_property_chain)
            ):
                # キャッシュが有効だった場合はキャッシュから取得したマテリアルを返す
                return cached_material
            # キャッシュが無効な場合、その他全てのキャッシュも無効になっている可能性が
            # 高いので全てのキャッシュを削除する。
            self.SELF_KEY_NUMBER_TO_MATERIAL_INDEX_CACHE.clear()

        # キャッシュが存在しなかった場合は、全てのマテリアルのリストの先頭からselfに
        # 対応するものを探す。発見したらキャッシュにマテリアルのインデックスを保存。
        for material_index, material in enumerate(context.blend_data.materials):
            if not material:
                continue
            if cached_material_index == material_index:
                continue
            if self.match_material(material, material_property_chain):
                self.SELF_KEY_NUMBER_TO_MATERIAL_INDEX_CACHE[self_key_number] = (
                    material_index
                )
                return material

        message = f"No matching material: {type(self)} {material_property_chain}"
        raise AssertionError(message)

    @classmethod
    def get_material_property_chain(cls) -> list[str]:
        chain = convert.sequence_or_none(getattr(cls, "material_property_chain", None))
        if chain is None:
            message = f"No material property chain: {cls}.{type(chain)} => {chain}"
            raise NotImplementedError(message)
        result: list[str] = []
        for property_name in chain:
            if isinstance(property_name, str):
                result.append(property_name)
                continue
            message = f"Invalid material property chain: {cls}.{type(chain)} => {chain}"
            raise AssertionError(message)
        return result

    @classmethod
    def find_outline_property_group(
        cls, material: Material
    ) -> Optional["MaterialTraceablePropertyGroup"]:
        if get_material_mtoon1_extension(material).is_outline_material:
            return None
        outline_material = get_material_mtoon1_extension(material).outline_material
        if not outline_material:
            return None
        if material.name == outline_material.name:
            logger.error(
                "Base material and outline material are same. name={material.name}"
            )
            return None
        chain = cls.get_material_property_chain()
        attr: object = get_material_mtoon1_extension(outline_material)
        for name in chain:
            attr = getattr(attr, name, None)
        if isinstance(attr, MaterialTraceablePropertyGroup):
            return attr
        message = f"No matching property group: {cls} {chain}"
        raise AssertionError(message)

    def get_bool(
        self,
        node_group_name: str,
        group_label: str,
        *,
        default_value: bool,
    ) -> bool:
        value = self.get_value(
            node_group_name, group_label, default_value=int(default_value)
        )
        if isinstance(value, float):
            return abs(value) > 0.000001
        return bool(value)

    def get_float(
        self,
        node_group_name: str,
        group_label: str,
        *,
        default_value: float,
    ) -> float:
        value = self.get_value(
            node_group_name, group_label, default_value=default_value
        )
        return float(value)

    def get_int(
        self,
        node_group_name: str,
        group_label: str,
        *,
        default_value: int,
    ) -> int:
        value = self.get_value(
            node_group_name, group_label, default_value=default_value
        )
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        return round(value)

    def get_value(
        self,
        node_group_name: str,
        group_label: str,
        *,
        default_value: float,
    ) -> Union[float, int, bool]:
        material = self.find_material()
        node_tree = material.node_tree
        if not node_tree:
            return default_value

        node = next(
            (
                node
                for node in node_tree.nodes
                if isinstance(node, ShaderNodeGroup)
                and node.node_tree
                and node.node_tree.name == node_group_name
            ),
            None,
        )
        if not node:
            return default_value

        socket = node.inputs.get(group_label)
        if isinstance(
            socket,
            (
                *shader.BOOL_SOCKET_CLASSES,
                *shader.FLOAT_SOCKET_CLASSES,
                *shader.INT_SOCKET_CLASSES,
            ),
        ):
            return socket.default_value

        return default_value

    def get_rgb(
        self,
        node_group_name: str,
        group_label: str,
        *,
        default_value: tuple[float, float, float],
    ) -> tuple[float, float, float]:
        material = self.find_material()
        node_tree = material.node_tree
        if not node_tree:
            return default_value

        node = next(
            (
                node
                for node in node_tree.nodes
                if isinstance(node, ShaderNodeGroup)
                and node.node_tree
                and node.node_tree.name == node_group_name
            ),
            None,
        )
        if not node:
            return default_value

        socket = node.inputs.get(group_label)
        if isinstance(socket, shader.COLOR_SOCKET_CLASSES):
            return (
                socket.default_value[0],
                socket.default_value[1],
                socket.default_value[2],
            )

        return default_value

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

        node = next(
            (
                node
                for node in node_tree.nodes
                if isinstance(node, ShaderNodeGroup)
                and node.node_tree
                and node.node_tree.name == node_group_name
            ),
            None,
        )
        if not node:
            logger.warning('No group node "%s"', node_group_name)
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
                'No "%s" in shader node group "%s"', group_label, node_group_name
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

        node = next(
            (
                node
                for node in node_tree.nodes
                if isinstance(node, ShaderNodeGroup)
                and node.node_tree
                and node.node_tree.name == node_group_name
            ),
            None,
        )
        if not node:
            logger.warning('No group node "%s"', node_group_name)
            return

        socket = node.inputs.get(group_label)
        if not isinstance(socket, shader.COLOR_SOCKET_CLASSES):
            logger.warning(
                'No "%s" in shader node group "%s"', group_label, node_group_name
            )
            return

        socket.default_value = rgba

    def set_rgb(
        self,
        node_group_name: str,
        group_label: str,
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

        node = next(
            (
                node
                for node in node_tree.nodes
                if isinstance(node, ShaderNodeGroup)
                and node.node_tree
                and node.node_tree.name == node_group_name
            ),
            None,
        )
        if not node:
            logger.warning('No group node "%s"', node_group_name)
            return

        socket = node.inputs.get(group_label)
        if not isinstance(socket, shader.COLOR_SOCKET_CLASSES):
            logger.warning(
                'No "%s" in shader node group "%s"', group_label, node_group_name
            )
            return

        socket.default_value = (*rgb, 1.0)


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
        ext = get_material_mtoon1_extension(material)
        property_group = functools.reduce(getattr, chain, ext)
        if not isinstance(property_group, Mtoon1TextureInfoPropertyGroup):
            message = f"{property_group} is not a Mtoon1TextureInfoPropertyGroup"
            raise TypeError(message)
        return property_group

    def get_texture_node_name(self, extra: str) -> str:
        texture_info = self.get_texture_info_property_group()
        name = type(texture_info.index).__name__
        return re.sub("PropertyGroup$", "", name) + "." + extra

    def get_image_texture_node_name(self) -> str:
        return self.get_texture_node_name("Image")

    def get_image_texture_uv_node_name(self) -> str:
        return self.get_texture_node_name("Uv")

    @classmethod
    def link_nodes(
        cls,
        material: Material,
        out_node_name: str,
        out_node_type: type[Node],
        out_node_socket_name: str,
        node_socket_target: NodeSocketTarget,
    ) -> None:
        if not material.node_tree:
            return

        select_in_node = node_socket_target.create_node_selector(material)
        in_socket_name = node_socket_target.get_in_socket_name()

        # 既につながっている場合は何もしない
        connection_check_node = next(
            (
                link.from_node
                for link in material.node_tree.links
                if select_in_node(link.to_node)
                and link.to_socket
                and link.to_socket.name == in_socket_name
            ),
            None,
        )
        while connection_check_node:
            if (
                isinstance(connection_check_node, out_node_type)
                and connection_check_node.name == out_node_name
            ):
                return
            if isinstance(connection_check_node, NodeReroute):
                connection_check_inputs = connection_check_node.inputs
                if len(connection_check_inputs) == 0:
                    break
                connection_check_links = connection_check_inputs[0].links
                if len(connection_check_links) == 0:
                    break
                connection_check_link = connection_check_links[0]
                connection_check_node = connection_check_link.from_node
                continue
            break

        # 関係ないノードとつながっている場合はリンクを切断
        cls.unlink_nodes(material, node_socket_target)

        # 出力ノードとソケットを探す
        out_node = material.node_tree.nodes.get(out_node_name)
        if not isinstance(out_node, out_node_type):
            logger.error("No output node: %s", out_node_name)
            return
        out_socket = out_node.outputs.get(out_node_socket_name)
        if not out_socket:
            logger.error("No output node socket: %s", out_node_socket_name)
            return
        traversing_sockets = [out_socket]
        while traversing_sockets:
            traversing_socket = traversing_sockets.pop()
            for connection_check_link in traversing_socket.links:
                connection_check_node = connection_check_link.to_node
                if not isinstance(connection_check_node, NodeReroute):
                    continue
                if connection_check_node.label != in_socket_name:
                    traversing_sockets.extend(connection_check_node.outputs)
                    continue
                traversing_outputs = connection_check_node.outputs
                if len(traversing_outputs) == 0:
                    continue
                out_socket = traversing_outputs[0]
                out_node = connection_check_node
                break

        # 入力ノードとソケットを探す
        in_node = next(
            (n for n in material.node_tree.nodes if select_in_node(n)),
            None,
        )
        if not in_node:
            logger.error("No input node")
            return

        in_socket = in_node.inputs.get(in_socket_name)
        if not in_socket:
            logger.error("No input socket: %s", in_socket_name)
            return

        material.node_tree.links.new(in_socket, out_socket)

    @classmethod
    def unlink_nodes(
        cls,
        material: Material,
        node_socket_target: NodeSocketTarget,
    ) -> None:
        while True:
            # Refresh in_node/out_node. These nodes may be invalidated.
            if not material.node_tree:
                return

            select_in_node = node_socket_target.create_node_selector(material)
            in_socket_name = node_socket_target.get_in_socket_name()
            disconnecting_link = next(
                (
                    link
                    for link in material.node_tree.links
                    if select_in_node(link.to_node)
                    and link.to_socket
                    and link.to_socket.name == in_socket_name
                ),
                None,
            )
            if not disconnecting_link:
                return

            material.node_tree.links.remove(disconnecting_link)

    @classmethod
    def link_or_unlink_nodes(
        cls,
        material: Material,
        out_node_name: str,
        out_node_type: type[Node],
        out_node_socket_name: str,
        node_socket_target: NodeSocketTarget,
        *,
        link: bool,
    ) -> None:
        if link:
            cls.link_nodes(
                material,
                out_node_name,
                out_node_type,
                out_node_socket_name,
                node_socket_target,
            )
        else:
            cls.unlink_nodes(
                material,
                node_socket_target,
            )

    def update_image(self, image: Optional[Image]) -> None:
        material = self.find_material()

        outline = self.find_outline_property_group(material)
        if outline and isinstance(outline, TextureTraceablePropertyGroup):
            outline.update_image(image)

        node_tree = material.node_tree
        if not node_tree:
            return

        node_name = self.get_image_texture_node_name()

        node = node_tree.nodes.get(node_name)
        if not isinstance(node, ShaderNodeTexImage):
            logger.warning('No shader node tex image "%s"', node_name)
            return

        node.image = image

        texture_info = self.get_texture_info_property_group()

        for (
            output_socket_name,
            node_socket_targets,
        ) in texture_info.node_socket_targets.items():
            for node_socket_target in node_socket_targets:
                self.link_or_unlink_nodes(
                    material,
                    node_name,
                    ShaderNodeTexImage,
                    output_socket_name,
                    node_socket_target,
                    link=bool(image),
                )

        texture_info.setup_drivers(material)

    def get_connected_node_image(self) -> Optional[Image]:
        material = self.find_material()
        if not material.use_nodes:
            return None

        node_tree = material.node_tree
        if not node_tree:
            return None

        texture_info = self.get_texture_info_property_group()
        node_socket_targets = next(
            iter(texture_info.node_socket_targets.values()), None
        )
        if not node_socket_targets:
            return None

        node_socket_target = next(iter(node_socket_targets), None)
        if not node_socket_target:
            return None

        node_selector = node_socket_target.create_node_selector(material)
        node = next((node for node in node_tree.nodes if node_selector(node)), None)
        if not node:
            return None

        traversing_input_socket = None
        for input_socket in node.inputs:
            if input_socket.name == node_socket_target.get_in_socket_name():
                traversing_input_socket = input_socket
                break

        while True:
            if not traversing_input_socket:
                return None

            links_to_input_socket = traversing_input_socket.links
            traversing_input_socket = None
            for link_to_input_socket in links_to_input_socket:
                from_node = link_to_input_socket.from_node
                if isinstance(from_node, ShaderNodeTexImage):
                    return from_node.image
                if isinstance(from_node, NodeReroute):
                    traversing_input_socket = from_node.inputs[0]
                    break

    def get_texture_uv_int(self, name: str, default_value: int) -> int:
        node_name = self.get_image_texture_uv_node_name()
        material = self.find_material()
        if not material.node_tree:
            return default_value
        node_tree = material.node_tree
        node = node_tree.nodes.get(node_name)
        if not isinstance(node, ShaderNodeGroup):
            return default_value
        socket = node.inputs.get(name)
        if not socket:
            logger.warning('No "%s" in shader node group "%s"', name, node_name)
            return default_value

        if isinstance(socket, shader.FLOAT_SOCKET_CLASSES):
            return round(socket.default_value)
        if isinstance(socket, shader.INT_SOCKET_CLASSES):
            return socket.default_value

        return default_value

    def get_texture_uv_float(self, name: str, default_value: float) -> float:
        node_name = self.get_image_texture_uv_node_name()
        material = self.find_material()
        if not material.node_tree:
            return default_value
        node_tree = material.node_tree
        node = node_tree.nodes.get(node_name)
        if not isinstance(node, ShaderNodeGroup):
            return default_value
        socket = node.inputs.get(name)
        if not socket:
            logger.warning('No "%s" in shader node group "%s"', name, node_name)
            return default_value

        if isinstance(socket, shader.FLOAT_SOCKET_CLASSES):
            return socket.default_value
        if isinstance(socket, shader.INT_SOCKET_CLASSES):
            return float(socket.default_value)

        return default_value

    def set_texture_uv(self, name: str, value: object) -> None:
        node_name = self.get_image_texture_uv_node_name()
        material = self.find_material()
        if not material.node_tree:
            return
        node_tree = material.node_tree
        node = node_tree.nodes.get(node_name)
        if not isinstance(node, ShaderNodeGroup):
            return
        socket = node.inputs.get(name)
        if not socket:
            logger.warning('No "%s" in shader node group "%s"', name, node_name)
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
    def get_texture_offset(self) -> tuple[float, float]:
        x = self.get_texture_uv_float(
            shader.UV_GROUP_UV_OFFSET_X_LABEL,
            default_value=shader.UV_GROUP_UV_OFFSET_X_DEFAULT,
        )
        y = self.get_texture_uv_float(
            shader.UV_GROUP_UV_OFFSET_Y_LABEL,
            default_value=shader.UV_GROUP_UV_OFFSET_Y_DEFAULT,
        )
        return x, y

    def set_texture_offset(self, value: object) -> None:
        offset = convert.float2_or_none(value)
        if offset is None:
            return

        self.set_texture_uv(shader.UV_GROUP_UV_OFFSET_X_LABEL, offset[0])
        self.set_texture_uv(shader.UV_GROUP_UV_OFFSET_Y_LABEL, offset[1])

        node_name = self.get_image_texture_node_name()
        material = self.find_material()
        if not material.node_tree:
            return
        node = material.node_tree.nodes.get(node_name)
        if not isinstance(node, ShaderNodeTexImage):
            logger.warning('No shader node tex image "%s"', node_name)
            return
        node.texture_mapping.translation = Vector((0, 0, 0))

        outline = self.find_outline_property_group(material)
        if not outline:
            return
        if not isinstance(outline, Mtoon1KhrTextureTransformPropertyGroup):
            return
        outline.set_texture_offset(offset)

    def get_texture_scale(self) -> tuple[float, float]:
        x = self.get_texture_uv_float(
            shader.UV_GROUP_UV_SCALE_X_LABEL,
            default_value=shader.UV_GROUP_UV_SCALE_X_DEFAULT,
        )
        y = self.get_texture_uv_float(
            shader.UV_GROUP_UV_SCALE_Y_LABEL,
            default_value=shader.UV_GROUP_UV_SCALE_Y_DEFAULT,
        )
        return x, y

    def set_texture_scale(self, value: object) -> None:
        scale = convert.float2_or_none(value)
        if scale is None:
            return

        self.set_texture_uv(shader.UV_GROUP_UV_SCALE_X_LABEL, scale[0])
        self.set_texture_uv(shader.UV_GROUP_UV_SCALE_Y_LABEL, scale[1])

        node_name = self.get_image_texture_node_name()
        material = self.find_material()
        if not material.node_tree:
            return
        node = material.node_tree.nodes.get(node_name)
        if not isinstance(node, ShaderNodeTexImage):
            logger.warning('No shader node tex image "%s"', node_name)
            return
        node.texture_mapping.scale = Vector((1, 1, 1))

        outline = self.find_outline_property_group(material)
        if not outline:
            return
        if not isinstance(outline, Mtoon1KhrTextureTransformPropertyGroup):
            return
        outline.set_texture_scale(scale)

    offset: FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",
        size=2,
        default=(
            shader.UV_GROUP_UV_OFFSET_X_DEFAULT,
            shader.UV_GROUP_UV_OFFSET_Y_DEFAULT,
        ),
        get=get_texture_offset,
        set=set_texture_offset,
    )

    scale: FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",
        size=2,
        default=(
            shader.UV_GROUP_UV_SCALE_X_DEFAULT,
            shader.UV_GROUP_UV_SCALE_Y_DEFAULT,
        ),
        get=get_texture_scale,
        set=set_texture_scale,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        offset: Sequence[float]  # type: ignore[no-redef]
        scale: Sequence[float]  # type: ignore[no-redef]


class Mtoon1BaseColorKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = (
        "pbr_metallic_roughness",
        "base_color_texture",
        "extensions",
        "khr_texture_transform",
    )


class Mtoon1ShadeMultiplyKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "shade_multiply_texture",
        "extensions",
        "khr_texture_transform",
    )


class Mtoon1NormalKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = (
        "normal_texture",
        "extensions",
        "khr_texture_transform",
    )


class Mtoon1ShadingShiftKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "shading_shift_texture",
        "extensions",
        "khr_texture_transform",
    )


class Mtoon1EmissiveKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = (
        "emissive_texture",
        "extensions",
        "khr_texture_transform",
    )


class Mtoon1RimMultiplyKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "rim_multiply_texture",
        "extensions",
        "khr_texture_transform",
    )


class Mtoon1MatcapKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "matcap_texture",
        "extensions",
        "khr_texture_transform",
    )


class Mtoon1OutlineWidthMultiplyKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "outline_width_multiply_texture",
        "extensions",
        "khr_texture_transform",
    )

    def set_texture_offset_and_outline(self, value: object) -> None:
        offset = convert.float2_or_none(value)
        if offset is None:
            return
        material = self.find_material()
        if get_material_mtoon1_extension(material).is_outline_material:
            return
        self.set_texture_offset(offset)
        ops.vrm.refresh_mtoon1_outline(material_name=material.name)

    def set_texture_scale_and_outline(self, value: object) -> None:
        scale = convert.float2_or_none(value)
        if scale is None:
            return
        material = self.find_material()
        if get_material_mtoon1_extension(material).is_outline_material:
            return
        self.set_texture_scale(scale)
        ops.vrm.refresh_mtoon1_outline(material_name=material.name)

    offset: FloatVectorProperty(  # type: ignore[valid-type]
        name="Offset",
        size=2,
        default=(
            shader.UV_GROUP_UV_OFFSET_X_DEFAULT,
            shader.UV_GROUP_UV_OFFSET_Y_DEFAULT,
        ),
        get=Mtoon1KhrTextureTransformPropertyGroup.get_texture_offset,
        set=set_texture_offset_and_outline,
    )

    scale: FloatVectorProperty(  # type: ignore[valid-type]
        name="Scale",
        size=2,
        default=(
            shader.UV_GROUP_UV_SCALE_X_DEFAULT,
            shader.UV_GROUP_UV_SCALE_Y_DEFAULT,
        ),
        get=Mtoon1KhrTextureTransformPropertyGroup.get_texture_scale,
        set=set_texture_scale_and_outline,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        offset: Sequence[float]  # type: ignore[no-redef]
        scale: Sequence[float]  # type: ignore[no-redef]


class Mtoon1UvAnimationMaskKhrTextureTransformPropertyGroup(
    Mtoon1KhrTextureTransformPropertyGroup
):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "uv_animation_mask_texture",
        "extensions",
        "khr_texture_transform",
    )


class Mtoon1TextureInfoExtensionsPropertyGroup(PropertyGroup):
    khr_texture_transform: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1KhrTextureTransformPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        khr_texture_transform: (  # type: ignore[no-redef]
            Mtoon1KhrTextureTransformPropertyGroup
        )


class Mtoon1BaseColorTextureInfoExtensionsPropertyGroup(
    Mtoon1TextureInfoExtensionsPropertyGroup
):
    khr_texture_transform: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1BaseColorKhrTextureTransformPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        khr_texture_transform: (  # type: ignore[no-redef]
            Mtoon1BaseColorKhrTextureTransformPropertyGroup
        )


class Mtoon1ShadeMultiplyTextureInfoExtensionsPropertyGroup(
    Mtoon1TextureInfoExtensionsPropertyGroup
):
    khr_texture_transform: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadeMultiplyKhrTextureTransformPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        khr_texture_transform: (  # type: ignore[no-redef]
            Mtoon1ShadeMultiplyKhrTextureTransformPropertyGroup
        )


class Mtoon1NormalTextureInfoExtensionsPropertyGroup(
    Mtoon1TextureInfoExtensionsPropertyGroup
):
    khr_texture_transform: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1NormalKhrTextureTransformPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        khr_texture_transform: (  # type: ignore[no-redef]
            Mtoon1NormalKhrTextureTransformPropertyGroup
        )


class Mtoon1ShadingShiftTextureInfoExtensionsPropertyGroup(
    Mtoon1TextureInfoExtensionsPropertyGroup
):
    khr_texture_transform: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadingShiftKhrTextureTransformPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        khr_texture_transform: (  # type: ignore[no-redef]
            Mtoon1ShadingShiftKhrTextureTransformPropertyGroup
        )


class Mtoon1EmissiveTextureInfoExtensionsPropertyGroup(
    Mtoon1TextureInfoExtensionsPropertyGroup
):
    khr_texture_transform: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1EmissiveKhrTextureTransformPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        khr_texture_transform: (  # type: ignore[no-redef]
            Mtoon1EmissiveKhrTextureTransformPropertyGroup
        )


class Mtoon1RimMultiplyTextureInfoExtensionsPropertyGroup(
    Mtoon1TextureInfoExtensionsPropertyGroup
):
    khr_texture_transform: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1RimMultiplyKhrTextureTransformPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        khr_texture_transform: (  # type: ignore[no-redef]
            Mtoon1RimMultiplyKhrTextureTransformPropertyGroup
        )


class Mtoon1MatcapTextureInfoExtensionsPropertyGroup(
    Mtoon1TextureInfoExtensionsPropertyGroup
):
    khr_texture_transform: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MatcapKhrTextureTransformPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        khr_texture_transform: (  # type: ignore[no-redef]
            Mtoon1MatcapKhrTextureTransformPropertyGroup
        )


class Mtoon1OutlineWidthMultiplyTextureInfoExtensionsPropertyGroup(
    Mtoon1TextureInfoExtensionsPropertyGroup
):
    khr_texture_transform: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1OutlineWidthMultiplyKhrTextureTransformPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        khr_texture_transform: (  # type: ignore[no-redef]
            Mtoon1OutlineWidthMultiplyKhrTextureTransformPropertyGroup
        )


class Mtoon1UvAnimationMaskTextureInfoExtensionsPropertyGroup(
    Mtoon1TextureInfoExtensionsPropertyGroup
):
    khr_texture_transform: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1UvAnimationMaskKhrTextureTransformPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        khr_texture_transform: (  # type: ignore[no-redef]
            Mtoon1UvAnimationMaskKhrTextureTransformPropertyGroup
        )


class Mtoon1SamplerPropertyGroup(TextureTraceablePropertyGroup):
    (
        mag_filter_enum,
        (
            MAG_FILTER_NEAREST,
            MAG_FILTER_LINEAR,
        ),
    ) = property_group_enum(
        ("NEAREST", "Nearest", "", "NONE", GL_NEAREST),
        ("LINEAR", "Linear", "", "NONE", GL_LINEAR),
    )
    MAG_FILTER_DEFAULT = MAG_FILTER_LINEAR

    def get_mag_filter(self) -> int:
        default_value = self.MAG_FILTER_DEFAULT.value

        material = self.find_material()
        node_name = self.get_image_texture_node_name()
        node_tree = material.node_tree
        if node_tree is None:
            return default_value

        node = node_tree.nodes.get(node_name)
        if not isinstance(node, ShaderNodeTexImage):
            return default_value

        if node.interpolation == IMAGE_INTERPOLATION_CLOSEST:
            return GL_NEAREST

        if node.interpolation in GL_LINEAR_IMAGE_INTERPOLATIONS:
            return GL_LINEAR

        value = self.get("mag_filter")
        if isinstance(value, int) and value in self.mag_filter_enum.values():
            return value

        return default_value

    def set_mag_filter(self, value: int) -> None:
        # 入力値がTexImageの値と矛盾する場合は、TexImageの値を変更する
        # 入力値がGL_NEARESTかつTexImageがClosestの場合は、内部値を削除する
        # 入力値がGL_LINEARかつTexImageがLinear/Cubic/Smartの場合は、内部値を削除する

        if value not in self.mag_filter_enum.values():
            self.pop("mag_filter", None)
            return

        material = self.find_material()
        node_name = self.get_image_texture_node_name()
        node_tree = material.node_tree
        if node_tree is not None:
            node = node_tree.nodes.get(node_name)
            if isinstance(node, ShaderNodeTexImage):
                if value == GL_NEAREST:
                    if node.interpolation == IMAGE_INTERPOLATION_CLOSEST:
                        self.pop("mag_filter", None)
                        return
                    node.interpolation = IMAGE_INTERPOLATION_CLOSEST
                if value == GL_LINEAR:
                    if node.interpolation in GL_LINEAR_IMAGE_INTERPOLATIONS:
                        self.pop("mag_filter", None)
                        return
                    node.interpolation = IMAGE_INTERPOLATION_LINEAR

        self["mag_filter"] = value

    def get_min_filter(self) -> int:
        value = self.get("min_filter")
        if isinstance(value, int) and value in self.min_filter_enum.values():
            return value

        default_value = self.MIN_FILTER_DEFAULT.value

        material = self.find_material()
        node_name = self.get_image_texture_node_name()
        node_tree = material.node_tree
        if node_tree is None:
            return default_value

        node = node_tree.nodes.get(node_name)
        if not isinstance(node, ShaderNodeTexImage):
            return default_value

        if node.interpolation == IMAGE_INTERPOLATION_CLOSEST:
            return GL_NEAREST

        if node.interpolation in GL_LINEAR_IMAGE_INTERPOLATIONS:
            return GL_LINEAR

        return default_value

    def set_min_filter(self, value: int) -> None:
        # 入力値がGL_NEARESTかつTexImageがClosestの場合は、内部値を削除する
        # 入力値がGL_LINEARかつTexImageがLinear/Cubic/Smartの場合は、内部値を削除する

        if value not in self.min_filter_enum.values():
            self.pop("min_filter", None)
            return

        material = self.find_material()
        node_name = self.get_image_texture_node_name()
        node_tree = material.node_tree
        if node_tree is not None:
            node = node_tree.nodes.get(node_name)
            if isinstance(node, ShaderNodeTexImage):
                if (
                    value == GL_NEAREST
                    and node.interpolation == IMAGE_INTERPOLATION_CLOSEST
                ):
                    self.pop("min_filter", None)
                    return
                if (
                    value == GL_LINEAR
                    and node.interpolation in GL_LINEAR_IMAGE_INTERPOLATIONS
                ):
                    self.pop("min_filter", None)
                    return

        self["min_filter"] = value

    (
        min_filter_enum,
        (
            MIN_FILTER_NEAREST,
            MIN_FILTER_LINEAR,
            MIN_FILTER_NEAREST_MIPMAP_NEAREST,
            MIN_FILTER_LINEAR_MIPMAP_NEAREST,
            MIN_FILTER_NEAREST_MIPMAP_LINEAR,
            MIN_FILTER_LINEAR_MIPMAP_LINEAR,
        ),
    ) = property_group_enum(
        ("NEAREST", "Nearest", "", "NONE", GL_NEAREST),
        ("LINEAR", "Linear", "", "NONE", GL_LINEAR),
        (
            "NEAREST_MIPMAP_NEAREST",
            "Nearest Mipmap Nearest",
            "",
            "NONE",
            GL_NEAREST_MIPMAP_NEAREST,
        ),
        (
            "LINEAR_MIPMAP_NEAREST",
            "Linear Mipmap Nearest",
            "",
            "NONE",
            GL_LINEAR_MIPMAP_NEAREST,
        ),
        (
            "NEAREST_MIPMAP_LINEAR",
            "Nearest Mipmap Linear",
            "",
            "NONE",
            GL_NEAREST_MIPMAP_LINEAR,
        ),
        (
            "LINEAR_MIPMAP_LINEAR",
            "Linear Mipmap Linear",
            "",
            "NONE",
            GL_LINEAR_MIPMAP_LINEAR,
        ),
    )
    MIN_FILTER_DEFAULT = MIN_FILTER_LINEAR

    # https://github.com/KhronosGroup/glTF/blob/2a9996a2ea66ab712590eaf62f39f1115996f5a3/specification/2.0/schema/sampler.schema.json#L67-L117
    (
        wrap_enum,
        (
            WRAP_CLAMP_TO_EDGE,
            WRAP_MIRRORED_REPEAT,
            WRAP_REPEAT,
        ),
    ) = property_group_enum(
        ("CLAMP_TO_EDGE", "Clamp to Edge", "", "NONE", GL_CLAMP_TO_EDGE),
        ("MIRRORED_REPEAT", "Mirrored Repeat", "", "NONE", GL_MIRRORED_REPEAT),
        ("REPEAT", "Repeat", "", "NONE", GL_REPEAT),
    )

    WRAP_DEFAULT = WRAP_REPEAT

    def get_wrap_s(self) -> int:
        wrap_s = self.get_texture_uv_int(
            shader.UV_GROUP_WRAP_S_LABEL, shader.UV_GROUP_WRAP_S_DEFAULT
        )
        if wrap_s in self.wrap_enum.values():
            return wrap_s
        return shader.UV_GROUP_WRAP_S_DEFAULT

    def set_wrap_s(self, value: object) -> None:
        self.set_texture_uv(shader.UV_GROUP_WRAP_S_LABEL, value)

    def get_wrap_t(self) -> int:
        wrap_t = self.get_texture_uv_int(
            shader.UV_GROUP_WRAP_T_LABEL, shader.UV_GROUP_WRAP_T_DEFAULT
        )
        if wrap_t in self.wrap_enum.values():
            return wrap_t
        return shader.UV_GROUP_WRAP_T_DEFAULT

    def set_wrap_t(self, value: object) -> None:
        self.set_texture_uv(shader.UV_GROUP_WRAP_T_LABEL, value)

    mag_filter: EnumProperty(  # type: ignore[valid-type]
        items=mag_filter_enum.items(),
        get=get_mag_filter,
        set=set_mag_filter,
        name="Mag Filter",
    )

    min_filter: EnumProperty(  # type: ignore[valid-type]
        items=min_filter_enum.items(),
        get=get_min_filter,
        set=set_min_filter,
        name="Min Filter",
    )

    wrap_s: EnumProperty(  # type: ignore[valid-type]
        items=wrap_enum.items(),
        name="Wrap S",
        default=WRAP_DEFAULT.value,
        get=get_wrap_s,
        set=set_wrap_s,
    )

    wrap_t: EnumProperty(  # type: ignore[valid-type]
        items=wrap_enum.items(),
        name="Wrap T",
        default=WRAP_DEFAULT.value,
        get=get_wrap_t,
        set=set_wrap_t,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        mag_filter: str  # type: ignore[no-redef]
        min_filter: str  # type: ignore[no-redef]
        wrap_s: str  # type: ignore[no-redef]
        wrap_t: str  # type: ignore[no-redef]


class Mtoon1BaseColorSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = (
        "pbr_metallic_roughness",
        "base_color_texture",
        "index",
        "sampler",
    )


class Mtoon1ShadeMultiplySamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "shade_multiply_texture",
        "index",
        "sampler",
    )


class Mtoon1NormalSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = (
        "normal_texture",
        "index",
        "sampler",
    )


class Mtoon1ShadingShiftSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "shading_shift_texture",
        "index",
        "sampler",
    )


class Mtoon1EmissiveSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = (
        "emissive_texture",
        "index",
        "sampler",
    )


class Mtoon1RimMultiplySamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "rim_multiply_texture",
        "index",
        "sampler",
    )


class Mtoon1MatcapSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "matcap_texture",
        "index",
        "sampler",
    )


class Mtoon1OutlineWidthMultiplySamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "outline_width_multiply_texture",
        "index",
        "sampler",
    )


class Mtoon1UvAnimationMaskSamplerPropertyGroup(Mtoon1SamplerPropertyGroup):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "uv_animation_mask_texture",
        "index",
        "sampler",
    )


class Mtoon1TexturePropertyGroup(TextureTraceablePropertyGroup):
    label = ""
    panel_label = label
    colorspace = "sRGB"

    def update_source(self, _context: Context) -> None:
        self.update_image(self.source)

    source: PointerProperty(  # type: ignore[valid-type]
        type=Image,
        update=update_source,
    )

    def update_source_for_desynced_node_tree(self, context: Context) -> None:
        """NodeTreeと同期してしていない場合にprop()に渡すPointerProperty()を更新.

        NodeTreeと同期してしていない場合にprop()のPlaceholder側に正しいImageの名前を表示したい。
        そのため、次のように動作する。
        - 必ずPlaceholderを表示するため、値は常にNoneを返すようにする
        - 値が外部から入力されたら、値をNoneに戻してself.sourceに転送
        """
        original_syncing_source_name: Optional[str] = None
        if self.source_for_desynced_node_tree:
            original_syncing_source_name = self.source_for_desynced_node_tree.name

        if self.source_for_desynced_node_tree is not None:
            self.source_for_desynced_node_tree = None  # trigger recursive assignment

        if original_syncing_source_name is not None:
            image = context.blend_data.images.get(original_syncing_source_name)
            if image:
                self.source = image
        else:
            self.source = None

    source_for_desynced_node_tree: PointerProperty(  # type: ignore[valid-type]
        type=Image,
        update=update_source_for_desynced_node_tree,
    )

    sampler: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1SamplerPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        source: Optional[Image]  # type: ignore[no-redef]
        source_for_desynced_node_tree: Optional[Image]  # type: ignore[no-redef]
        sampler: Mtoon1SamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1BaseColorTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = (
        "pbr_metallic_roughness",
        "base_color_texture",
        "index",
    )

    label = "Lit Color, Alpha"
    panel_label = label
    colorspace = "sRGB"

    sampler: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1BaseColorSamplerPropertyGroup
    )

    def update_image(self, image: Optional[Image]) -> None:
        super().update_image(image)
        material = self.find_material()
        mtoon1 = get_material_mtoon1_extension(material)
        mtoon1.update_alpha_nodes(
            material,
            mtoon1.get_alpha_mode(),
        )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        sampler: Mtoon1BaseColorSamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1ShadeMultiplyTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "shade_multiply_texture",
        "index",
    )

    label = "Shade Color"
    panel_label = label
    colorspace = "sRGB"

    sampler: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadeMultiplySamplerPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        sampler: Mtoon1ShadeMultiplySamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1NormalTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = (
        "normal_texture",
        "index",
    )

    label = "Normal Map"
    panel_label = label
    colorspace = "Non-Color"

    sampler: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1NormalSamplerPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        sampler: Mtoon1NormalSamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1ShadingShiftTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "shading_shift_texture",
        "index",
    )

    label = "Additive Shading Shift"
    panel_label = label
    colorspace = "Non-Color"

    sampler: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadingShiftSamplerPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        sampler: Mtoon1ShadingShiftSamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1EmissiveTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = (
        "emissive_texture",
        "index",
    )

    label = "Emission"
    panel_label = label
    colorspace = "sRGB"

    sampler: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1EmissiveSamplerPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        sampler: Mtoon1EmissiveSamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1RimMultiplyTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "rim_multiply_texture",
        "index",
    )

    label = "Rim Color"
    panel_label = label
    colorspace = "sRGB"

    sampler: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1RimMultiplySamplerPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        sampler: Mtoon1RimMultiplySamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1MatcapTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "matcap_texture",
        "index",
    )

    label = "Matcap Rim"
    panel_label = label
    colorspace = "sRGB"

    sampler: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MatcapSamplerPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        sampler: Mtoon1MatcapSamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1OutlineWidthMultiplyTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "outline_width_multiply_texture",
        "index",
    )

    label = "Outline Width"
    panel_label = label
    colorspace = "Non-Color"

    def update_source(self, context: Context) -> None:
        mtoon1 = get_material_mtoon1_extension(self.find_material())
        mtoon1.extensions.vrmc_materials_mtoon.update_outline_geometry()
        super().update_source(context)

    sampler: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1OutlineWidthMultiplySamplerPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        sampler: (  # type: ignore[no-redef]
            Mtoon1OutlineWidthMultiplySamplerPropertyGroup
        )


class Mtoon1UvAnimationMaskTexturePropertyGroup(Mtoon1TexturePropertyGroup):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "uv_animation_mask_texture",
        "index",
    )

    label = "UV Animation Mask"
    panel_label = "Mask"
    colorspace = "Non-Color"

    sampler: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1UvAnimationMaskSamplerPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        sampler: Mtoon1UvAnimationMaskSamplerPropertyGroup  # type: ignore[no-redef]


class Mtoon1TextureInfoPropertyGroup(MaterialTraceablePropertyGroup):
    node_socket_targets: Mapping[str, Sequence[NodeSocketTarget]] = {}

    index: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1TexturePropertyGroup
    )

    extensions: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1TextureInfoExtensionsPropertyGroup
    )

    @dataclass(frozen=True)
    class TextureInfoBackup:
        source: Optional[Image]
        mag_filter: Optional[str]
        min_filter: Optional[str]
        wrap_s: str
        wrap_t: str
        offset: tuple[float, float]
        scale: tuple[float, float]

    def backup(self) -> TextureInfoBackup:
        return Mtoon1TextureInfoPropertyGroup.TextureInfoBackup(
            source=self.index.get_connected_node_image(),
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
        self.index.source = backup.source

        if (
            backup.mag_filter
            in Mtoon1SamplerPropertyGroup.mag_filter_enum.identifiers()
        ):
            self.index.sampler.mag_filter = backup.mag_filter
        elif backup.mag_filter is not None:
            logger.warning("invalid mag filter: %s", backup.mag_filter)
            self.index.sampler.mag_filter = (
                Mtoon1SamplerPropertyGroup.MAG_FILTER_DEFAULT.identifier
            )

        if (
            backup.min_filter
            in Mtoon1SamplerPropertyGroup.min_filter_enum.identifiers()
        ):
            self.index.sampler.min_filter = backup.min_filter
        elif backup.min_filter is not None:
            logger.warning("invalid min filter: %s", backup.min_filter)
            self.index.sampler.min_filter = (
                Mtoon1SamplerPropertyGroup.MIN_FILTER_DEFAULT.identifier
            )

        if backup.wrap_s in Mtoon1SamplerPropertyGroup.wrap_enum.identifiers():
            self.index.sampler.wrap_s = backup.wrap_s
        else:
            logger.warning("invalid wrap s: %s", backup.wrap_s)
            self.index.sampler.wrap_s = (
                Mtoon1SamplerPropertyGroup.WRAP_DEFAULT.identifier
            )

        if backup.wrap_t in Mtoon1SamplerPropertyGroup.wrap_enum.identifiers():
            self.index.sampler.wrap_t = backup.wrap_t
        else:
            logger.warning("invalid wrap t: %s", backup.wrap_t)
            self.index.sampler.wrap_t = (
                Mtoon1SamplerPropertyGroup.WRAP_DEFAULT.identifier
            )

        self.extensions.khr_texture_transform.offset = backup.offset
        self.extensions.khr_texture_transform.scale = backup.scale

    show_expanded: BoolProperty()  # type: ignore[valid-type]

    def setup_drivers(self, material: Material) -> None:
        mtoon1 = get_material_mtoon1_extension(material)
        if not mtoon1.get_enabled_in_material(material):
            return
        node_tree = material.node_tree
        if not node_tree:
            return
        animation_data = node_tree.animation_data
        if not animation_data:
            animation_data = node_tree.animation_data_create()
            if not animation_data:
                logger.error(
                    'Failed to create anomation data for node tree "%s"', node_tree.name
                )
                return
        uv_node_name = self.index.get_image_texture_uv_node_name()
        uv_node = node_tree.nodes.get(uv_node_name)
        if not uv_node or not isinstance(uv_node, ShaderNodeGroup):
            logger.error('Failed to get uv node "%s"', uv_node_name)
            return
        image_node_name = self.index.get_image_texture_node_name()
        image_node = node_tree.nodes.get(image_node_name)
        image_exists = isinstance(image_node, ShaderNodeTexImage) and isinstance(
            image_node.image, Image
        )
        for size_index, uv_input_label in (
            (0, shader.UV_GROUP_IMAGE_WIDTH_LABEL),
            (1, shader.UV_GROUP_IMAGE_HEIGHT_LABEL),
        ):
            uv_input_index = next(
                iter(
                    index
                    for index, socket in enumerate(uv_node.inputs)
                    if socket.name == uv_input_label
                ),
                None,
            )
            if uv_input_index is None:
                logger.error('Failed to get uv input index for "%s"', uv_input_label)
                continue
            data_path = (
                f'nodes["{uv_node_name}"]'
                + f".inputs[{uv_input_index}]"
                + ".default_value"
            )
            fcurve: Optional[Union[FCurve, list[FCurve]]] = next(
                iter(
                    fcurve
                    for fcurve in animation_data.drivers
                    if fcurve.data_path == data_path
                ),
                None,
            )
            if fcurve is None:
                try:
                    fcurve = node_tree.driver_add(data_path)
                except TypeError:
                    continue
            if not isinstance(fcurve, FCurve):
                logger.error(
                    'Failed to get fcurve "%s" for node tree "%s"',
                    data_path,
                    node_tree.name,
                )
                continue
            if fcurve.array_index != 0:
                fcurve.array_index = 0
            driver = fcurve.driver
            if not isinstance(driver, Driver):
                logger.error('Failed to get driver for fcurve "%s"', data_path)
                continue
            if driver.type != "SUM":
                driver.type = "SUM"
            if not driver.variables:
                driver.variables.new()
            while len(driver.variables) > 1:
                driver.variables.remove(driver.variables[-1])
            variable = driver.variables[0]
            if variable.type != "SINGLE_PROP":
                variable.type = "SINGLE_PROP"
            if not variable.targets:
                logger.error(
                    'No targets in variable for fcurve "%s" in node_tree "%s"',
                    data_path,
                    node_tree.name,
                )
                continue
            target = variable.targets[0]
            if target.id_type != "MATERIAL":
                target.id_type = "MATERIAL"
            if target.id != material:
                target.id = material
            target_data_path = (
                "node_tree"
                + f'.nodes["{image_node_name}"]'
                + ".image"
                + f".size[{size_index}]"
            )
            if target.data_path != target_data_path or (
                # Blender 2.93では、一度imageを削除するとis_validがFalseになる。
                # data_pathを再設定することで解消。
                image_exists and (not fcurve.is_valid or not driver.is_valid)
            ):
                target.data_path = target_data_path

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        index: Mtoon1TexturePropertyGroup  # type: ignore[no-redef]
        extensions: Mtoon1TextureInfoExtensionsPropertyGroup  # type: ignore[no-redef]
        show_expanded: bool  # type: ignore[no-redef]


# https://github.com/KhronosGroup/glTF/blob/1ab49ec412e638f2e5af0289e9fbb60c7271e457/specification/2.0/schema/textureInfo.schema.json
class Mtoon1BaseColorTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    material_property_chain = (
        "pbr_metallic_roughness",
        "base_color_texture",
    )

    node_socket_targets: Mapping[str, Sequence[NodeSocketTarget]] = {
        TEX_IMAGE_COLOR_OUTPUT_KEY: [
            NodeGroupSocketTarget(
                node_group_node_tree_name=shader.OUTPUT_GROUP_NAME,
                in_socket_name="Lit Color Texture Color",
            ),
            PrincipledBsdfNodeSocketTarget(
                in_socket_name=PRINCIPLED_BSDF_BASE_COLOR_INPUT_KEY
            ),
        ],
        TEX_IMAGE_ALPHA_OUTPUT_KEY: [
            NodeGroupSocketTarget(
                node_group_node_tree_name=shader.OUTPUT_GROUP_NAME,
                in_socket_name="Lit Color Texture Alpha",
            ),
        ],
    }

    index: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1BaseColorTexturePropertyGroup
    )
    extensions: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1BaseColorTextureInfoExtensionsPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        index: Mtoon1BaseColorTexturePropertyGroup  # type: ignore[no-redef]
        extensions: (  # type: ignore[no-redef]
            Mtoon1BaseColorTextureInfoExtensionsPropertyGroup
        )


class Mtoon1ShadeMultiplyTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "shade_multiply_texture",
    )

    node_socket_targets: Mapping[str, Sequence[NodeSocketTarget]] = {
        TEX_IMAGE_COLOR_OUTPUT_KEY: [
            NodeGroupSocketTarget(
                node_group_node_tree_name=shader.OUTPUT_GROUP_NAME,
                in_socket_name="Shade Color Texture",
            ),
        ],
    }

    index: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadeMultiplyTexturePropertyGroup
    )
    extensions: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadeMultiplyTextureInfoExtensionsPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        index: Mtoon1ShadeMultiplyTexturePropertyGroup  # type: ignore[no-redef]
        extensions: (  # type: ignore[no-redef]
            Mtoon1ShadeMultiplyTextureInfoExtensionsPropertyGroup
        )


# https://github.com/KhronosGroup/glTF/blob/1ab49ec412e638f2e5af0289e9fbb60c7271e457/specification/2.0/schema/material.normalTextureInfo.schema.json
class Mtoon1NormalTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    material_property_chain = ("normal_texture",)

    node_socket_targets: Mapping[str, Sequence[NodeSocketTarget]] = {
        TEX_IMAGE_COLOR_OUTPUT_KEY: [
            NodeGroupSocketTarget(
                node_group_node_tree_name=shader.NORMAL_GROUP_NAME,
                in_socket_name="Normal Map Texture",
            ),
            PrincipledBsdfNormalMapNodeSocketTarget(),
        ],
    }

    index: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1NormalTexturePropertyGroup
    )

    def get_scale(self) -> float:
        return self.get_float(
            shader.NORMAL_GROUP_NAME,
            shader.NORMAL_GROUP_SCALE_LABEL,
            default_value=shader.NORMAL_GROUP_SCALE_DEFAULT,
        )

    def set_scale(self, value: object) -> None:
        self.set_value(
            shader.NORMAL_GROUP_NAME,
            shader.NORMAL_GROUP_SCALE_LABEL,
            value,
        )
        material = self.find_material()
        principled_bsdf = PrincipledBSDFWrapper(material, is_readonly=False)
        principled_bsdf.normalmap_strength = self.scale

        mtoon1 = get_material_mtoon1_extension(material)
        if mtoon1.is_outline_material:
            return
        outline_material = mtoon1.outline_material
        if not outline_material:
            return
        outline_principled_bsdf = PrincipledBSDFWrapper(
            outline_material, is_readonly=False
        )
        outline_principled_bsdf.normalmap_strength = self.scale

    scale: FloatProperty(  # type: ignore[valid-type]
        name="Scale",
        default=shader.NORMAL_GROUP_SCALE_DEFAULT,
        get=get_scale,
        set=set_scale,
    )

    extensions: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1NormalTextureInfoExtensionsPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        index: Mtoon1NormalTexturePropertyGroup  # type: ignore[no-redef]
        scale: float  # type: ignore[no-redef]
        extensions: (  # type: ignore[no-redef]
            Mtoon1NormalTextureInfoExtensionsPropertyGroup
        )


# https://github.com/vrm-c/vrm-specification/blob/c5d1afdc4d59c292cb4fd6d54cad1dc0c4d19c60/specification/VRMC_materials_mtoon-1.0/schema/mtoon.shadingShiftTexture.schema.json
class Mtoon1ShadingShiftTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "shading_shift_texture",
    )

    node_socket_targets: Mapping[str, Sequence[NodeSocketTarget]] = {
        TEX_IMAGE_COLOR_OUTPUT_KEY: [
            NodeGroupSocketTarget(
                node_group_node_tree_name=shader.OUTPUT_GROUP_NAME,
                in_socket_name="Shading Shift Texture",
            ),
        ],
    }

    index: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadingShiftTexturePropertyGroup
    )

    def get_scale(self) -> float:
        return self.get_float(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_SHADING_SHIFT_TEXTURE_SCALE_LABEL,
            default_value=shader.OUTPUT_GROUP_SHADING_SHIFT_TEXTURE_SCALE_DEFAULT,
        )

    def set_scale(self, value: object) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_SHADING_SHIFT_TEXTURE_SCALE_LABEL,
            value,
        )

    scale: FloatProperty(  # type: ignore[valid-type]
        name="Scale",
        default=shader.OUTPUT_GROUP_SHADING_SHIFT_TEXTURE_SCALE_DEFAULT,
        set=set_scale,
        get=get_scale,
    )

    extensions: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadingShiftTextureInfoExtensionsPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        index: Mtoon1ShadingShiftTexturePropertyGroup  # type: ignore[no-redef]
        scale: float  # type: ignore[no-redef]
        extensions: (  # type: ignore[no-redef]
            Mtoon1ShadingShiftTextureInfoExtensionsPropertyGroup
        )


# https://github.com/KhronosGroup/glTF/blob/1ab49ec412e638f2e5af0289e9fbb60c7271e457/specification/2.0/schema/textureInfo.schema.json
class Mtoon1EmissiveTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    material_property_chain = ("emissive_texture",)

    node_socket_targets: Mapping[str, Sequence[NodeSocketTarget]] = {
        TEX_IMAGE_COLOR_OUTPUT_KEY: [
            NodeGroupSocketTarget(
                node_group_node_tree_name=shader.OUTPUT_GROUP_NAME,
                in_socket_name="Emissive Texture",
            ),
            PrincipledBsdfNodeSocketTarget(
                in_socket_name=PRINCIPLED_BSDF_EMISSION_INPUT_KEY,
            ),
            GltfEmissionNodeSocketTarget(),
        ],
    }

    index: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1EmissiveTexturePropertyGroup
    )
    extensions: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1EmissiveTextureInfoExtensionsPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        index: Mtoon1EmissiveTexturePropertyGroup  # type: ignore[no-redef]
        extensions: (  # type: ignore[no-redef]
            Mtoon1EmissiveTextureInfoExtensionsPropertyGroup
        )


class Mtoon1RimMultiplyTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "rim_multiply_texture",
    )

    node_socket_targets: Mapping[str, Sequence[NodeSocketTarget]] = {
        TEX_IMAGE_COLOR_OUTPUT_KEY: [
            NodeGroupSocketTarget(
                node_group_node_tree_name=shader.OUTPUT_GROUP_NAME,
                in_socket_name="Rim Color Texture",
            ),
        ],
    }

    index: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1RimMultiplyTexturePropertyGroup
    )
    extensions: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1RimMultiplyTextureInfoExtensionsPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        index: Mtoon1RimMultiplyTexturePropertyGroup  # type: ignore[no-redef]
        extensions: (  # type: ignore[no-redef]
            Mtoon1RimMultiplyTextureInfoExtensionsPropertyGroup
        )


class Mtoon1MatcapTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "matcap_texture",
    )

    node_socket_targets: Mapping[str, Sequence[NodeSocketTarget]] = {
        TEX_IMAGE_COLOR_OUTPUT_KEY: [
            NodeGroupSocketTarget(
                node_group_node_tree_name=shader.OUTPUT_GROUP_NAME,
                in_socket_name="MatCap Texture",
            ),
        ],
    }

    index: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MatcapTexturePropertyGroup
    )
    extensions: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MatcapTextureInfoExtensionsPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        index: Mtoon1MatcapTexturePropertyGroup  # type: ignore[no-redef]
        extensions: (  # type: ignore[no-redef]
            Mtoon1MatcapTextureInfoExtensionsPropertyGroup
        )


class Mtoon1OutlineWidthMultiplyTextureInfoPropertyGroup(
    Mtoon1TextureInfoPropertyGroup
):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "outline_width_multiply_texture",
    )

    node_socket_targets: Mapping[str, Sequence[NodeSocketTarget]] = {
        TEX_IMAGE_COLOR_OUTPUT_KEY: [
            NodeGroupSocketTarget(
                node_group_node_tree_name=shader.OUTPUT_GROUP_NAME,
                in_socket_name="Outline Width Texture",
            ),
        ],
    }

    index: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1OutlineWidthMultiplyTexturePropertyGroup
    )
    extensions: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1OutlineWidthMultiplyTextureInfoExtensionsPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        index: Mtoon1OutlineWidthMultiplyTexturePropertyGroup  # type: ignore[no-redef]
        extensions: (  # type: ignore[no-redef]
            Mtoon1OutlineWidthMultiplyTextureInfoExtensionsPropertyGroup
        )


class Mtoon1UvAnimationMaskTextureInfoPropertyGroup(Mtoon1TextureInfoPropertyGroup):
    material_property_chain = (
        "extensions",
        "vrmc_materials_mtoon",
        "uv_animation_mask_texture",
    )

    node_socket_targets: Mapping[str, Sequence[NodeSocketTarget]] = {
        TEX_IMAGE_COLOR_OUTPUT_KEY: [
            NodeGroupSocketTarget(
                node_group_node_tree_name=shader.UV_ANIMATION_GROUP_NAME,
                in_socket_name="Mask Texture",
            ),
        ],
    }

    index: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1UvAnimationMaskTexturePropertyGroup
    )
    extensions: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1UvAnimationMaskTextureInfoExtensionsPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        index: Mtoon1UvAnimationMaskTexturePropertyGroup  # type: ignore[no-redef]
        extensions: (  # type: ignore[no-redef]
            Mtoon1UvAnimationMaskTextureInfoExtensionsPropertyGroup
        )


class Mtoon0SamplerPropertyGroup(PropertyGroup):
    mag_filter: EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.mag_filter_enum.items(),
        name="Mag Filter",
    )

    min_filter: EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.min_filter_enum.items(),
        name="Min Filter",
    )

    wrap_s: EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_enum.items(),
        name="Wrap S",
        default=Mtoon1SamplerPropertyGroup.WRAP_DEFAULT.value,
    )

    wrap_t: EnumProperty(  # type: ignore[valid-type]
        items=Mtoon1SamplerPropertyGroup.wrap_enum.items(),
        name="Wrap T",
        default=Mtoon1SamplerPropertyGroup.WRAP_DEFAULT.value,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        mag_filter: str  # type: ignore[no-redef]
        min_filter: str  # type: ignore[no-redef]
        wrap_s: str  # type: ignore[no-redef]
        wrap_t: str  # type: ignore[no-redef]


class Mtoon0TexturePropertyGroup(PropertyGroup):
    label = ""
    panel_label = ""
    colorspace = "sRGB"

    def get_connected_node_image(self) -> Optional[Image]:
        return self.source if isinstance(self.source, Image) else None

    source: PointerProperty(  # type: ignore[valid-type]
        type=Image,
    )

    sampler: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon0SamplerPropertyGroup,
    )

    show_expanded: BoolProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        source: Optional[Image]  # type: ignore[no-redef]
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
    material_property_chain = ("pbr_metallic_roughness",)

    def get_base_color_factor(self) -> tuple[float, float, float, float]:
        rgb = self.get_rgb(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_BASE_COLOR_FACTOR_COLOR_LABEL,
            default_value=shader.OUTPUT_GROUP_BASE_COLOR_FACTOR_COLOR_DEFAULT,
        )
        a = self.get_value(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_BASE_COLOR_FACTOR_ALPHA_LABEL,
            default_value=shader.OUTPUT_GROUP_BASE_COLOR_FACTOR_ALPHA_DEFAULT,
        )
        return (*rgb, a)

    def set_base_color_factor(self, value: object) -> None:
        color = convert.float4_or_none(value)
        if color is None:
            return
        self.set_rgba(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_BASE_COLOR_FACTOR_COLOR_LABEL,
            color,
        )
        self.set_value(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_BASE_COLOR_FACTOR_ALPHA_LABEL,
            color[3],
        )
        material = self.find_material()
        principled_bsdf = PrincipledBSDFWrapper(material, is_readonly=False)
        principled_bsdf.base_color = (
            color[0],
            color[1],
            color[2],
        )
        mtoon1 = get_material_mtoon1_extension(material)
        alpha_mode_value = mtoon1.get_alpha_mode()
        mtoon1.update_alpha_nodes(material, alpha_mode_value)

        if mtoon1.is_outline_material:
            return
        outline_material = mtoon1.outline_material
        if not outline_material:
            return
        outline_mtoon1 = get_material_mtoon1_extension(outline_material)
        outline_mtoon1.update_alpha_nodes(outline_material, alpha_mode_value)

    base_color_factor: FloatVectorProperty(  # type: ignore[valid-type]
        size=4,
        subtype="COLOR",
        default=(
            *shader.OUTPUT_GROUP_BASE_COLOR_FACTOR_COLOR_DEFAULT,
            shader.OUTPUT_GROUP_BASE_COLOR_FACTOR_ALPHA_DEFAULT,
        ),
        min=0,
        max=1,
        get=get_base_color_factor,
        set=set_base_color_factor,
    )

    base_color_texture: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1BaseColorTextureInfoPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        base_color_factor: Sequence[float]  # type: ignore[no-redef]
        base_color_texture: (  # type: ignore[no-redef]
            Mtoon1BaseColorTextureInfoPropertyGroup
        )


class Mtoon1VrmcMaterialsMtoonPropertyGroup(MaterialTraceablePropertyGroup):
    material_property_chain = ("extensions", "vrmc_materials_mtoon")

    def get_transparent_with_z_write(self) -> bool:
        return self.get_bool(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_TRANSPARENT_WITH_Z_WRITE_LABEL,
            default_value=shader.OUTPUT_GROUP_TRANSPARENT_WITH_Z_WRITE_DEFAULT,
        )

    def set_transparent_with_z_write(self, value: object) -> None:
        self.set_bool(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_TRANSPARENT_WITH_Z_WRITE_LABEL,
            value,
        )

        mtoon1 = get_material_mtoon1_extension(self.find_material())
        mtoon1.set_mtoon0_render_queue_and_clamp(mtoon1.mtoon0_render_queue)

    transparent_with_z_write: BoolProperty(  # type: ignore[valid-type]
        name="Transparent With ZWrite Mode",
        default=shader.OUTPUT_GROUP_TRANSPARENT_WITH_Z_WRITE_DEFAULT,
        get=get_transparent_with_z_write,
        set=set_transparent_with_z_write,
    )

    def get_render_queue_offset_number(self) -> int:
        return self.get_int(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_RENDER_QUEUE_OFFSET_NUMBER_LABEL,
            default_value=shader.OUTPUT_GROUP_RENDER_QUEUE_OFFSET_NUMBER_DEFAULT,
        )

    def set_render_queue_offset_number(self, value: int) -> None:
        self.set_int(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_RENDER_QUEUE_OFFSET_NUMBER_LABEL,
            value,
        )

    render_queue_offset_number: IntProperty(  # type: ignore[valid-type]
        name="RenderQueue Offset",
        min=shader.OUTPUT_GROUP_RENDER_QUEUE_OFFSET_NUMBER_MIN,
        default=shader.OUTPUT_GROUP_RENDER_QUEUE_OFFSET_NUMBER_DEFAULT,
        max=shader.OUTPUT_GROUP_RENDER_QUEUE_OFFSET_NUMBER_MAX,
        get=get_render_queue_offset_number,
        set=set_render_queue_offset_number,
    )

    shade_multiply_texture: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadeMultiplyTextureInfoPropertyGroup
    )

    def get_shade_color_factor(self) -> tuple[float, float, float]:
        return self.get_rgb(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_SHADE_COLOR_FACTOR_LABEL,
            default_value=shader.OUTPUT_GROUP_SHADE_COLOR_FACTOR_DEFAULT,
        )

    def set_shade_color_factor(self, value: object) -> None:
        self.set_rgb(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_SHADE_COLOR_FACTOR_LABEL,
            value,
        )

    shade_color_factor: FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="COLOR",
        default=shader.OUTPUT_GROUP_SHADE_COLOR_FACTOR_DEFAULT,
        min=0.0,
        max=1.0,
        get=get_shade_color_factor,
        set=set_shade_color_factor,
    )

    shading_shift_texture: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1ShadingShiftTextureInfoPropertyGroup
    )

    def get_shading_shift_factor(self) -> float:
        return self.get_float(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_SHADING_SHIFT_FACTOR_LABEL,
            default_value=shader.OUTPUT_GROUP_SHADING_SHIFT_FACTOR_DEFAULT,
        )

    def set_shading_shift_factor(self, value: object) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_SHADING_SHIFT_FACTOR_LABEL,
            value,
        )

    shading_shift_factor: FloatProperty(  # type: ignore[valid-type]
        name=shader.OUTPUT_GROUP_SHADING_SHIFT_FACTOR_LABEL,
        soft_min=-1.0,
        default=shader.OUTPUT_GROUP_SHADING_SHIFT_FACTOR_DEFAULT,
        soft_max=1.0,
        get=get_shading_shift_factor,
        set=set_shading_shift_factor,
    )

    def get_shading_toony_factor(self) -> float:
        return self.get_float(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_SHADING_TOONY_FACTOR_LABEL,
            default_value=shader.OUTPUT_GROUP_SHADING_TOONY_FACTOR_DEFAULT,
        )

    def set_shading_toony_factor(self, value: object) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_SHADING_TOONY_FACTOR_LABEL,
            value,
        )

    shading_toony_factor: FloatProperty(  # type: ignore[valid-type]
        name=shader.OUTPUT_GROUP_SHADING_TOONY_FACTOR_LABEL,
        min=0.0,
        default=shader.OUTPUT_GROUP_SHADING_TOONY_FACTOR_DEFAULT,
        max=1.0,
        get=get_shading_toony_factor,
        set=set_shading_toony_factor,
    )

    def get_gi_equalization_factor(self) -> float:
        return self.get_float(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_GI_EQUALIZATION_FACTOR_LABEL,
            default_value=shader.OUTPUT_GROUP_GI_EQUALIZATION_FACTOR_DEFAULT,
        )

    def set_gi_equalization_factor(self, value: object) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_GI_EQUALIZATION_FACTOR_LABEL,
            value,
        )

    gi_equalization_factor: FloatProperty(  # type: ignore[valid-type]
        name="GI Equalization",
        min=0.0,
        default=shader.OUTPUT_GROUP_GI_EQUALIZATION_FACTOR_DEFAULT,
        max=1.0,
        get=get_gi_equalization_factor,
        set=set_gi_equalization_factor,
    )

    def get_matcap_factor(self) -> tuple[float, float, float]:
        return self.get_rgb(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_MATCAP_FACTOR_LABEL,
            default_value=shader.OUTPUT_GROUP_MATCAP_FACTOR_DEFAULT,
        )

    def set_matcap_factor(self, value: object) -> None:
        self.set_rgb(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_MATCAP_FACTOR_LABEL,
            value,
        )

    matcap_factor: FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="COLOR",
        default=shader.OUTPUT_GROUP_MATCAP_FACTOR_DEFAULT,
        min=0,
        max=1,
        get=get_matcap_factor,
        set=set_matcap_factor,
    )

    matcap_texture: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MatcapTextureInfoPropertyGroup
    )

    def get_parametric_rim_color_factor(self) -> tuple[float, float, float]:
        return self.get_rgb(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_PARAMETRIC_RIM_COLOR_FACTOR_LABEL,
            default_value=shader.OUTPUT_GROUP_PARAMETRIC_RIM_COLOR_FACTOR_DEFAULT,
        )

    def set_parametric_rim_color_factor(self, value: object) -> None:
        self.set_rgb(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_PARAMETRIC_RIM_COLOR_FACTOR_LABEL,
            value,
        )

    parametric_rim_color_factor: FloatVectorProperty(  # type: ignore[valid-type]
        name=shader.OUTPUT_GROUP_PARAMETRIC_RIM_COLOR_FACTOR_LABEL,
        size=3,
        subtype="COLOR",
        default=shader.OUTPUT_GROUP_PARAMETRIC_RIM_COLOR_FACTOR_DEFAULT,
        min=0,
        max=1,
        get=get_parametric_rim_color_factor,
        set=set_parametric_rim_color_factor,
    )

    rim_multiply_texture: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1RimMultiplyTextureInfoPropertyGroup
    )

    def get_rim_lighting_mix_factor(self) -> float:
        return self.get_value(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_RIM_LIGHTING_MIX_FACTOR_LABEL,
            default_value=shader.OUTPUT_GROUP_RIM_LIGHTING_MIX_FACTOR_DEFAULT,
        )

    def set_rim_lighting_mix_factor(self, value: object) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_RIM_LIGHTING_MIX_FACTOR_LABEL,
            value,
        )

    rim_lighting_mix_factor: FloatProperty(  # type: ignore[valid-type]
        name=shader.OUTPUT_GROUP_RIM_LIGHTING_MIX_FACTOR_LABEL,
        default=shader.OUTPUT_GROUP_RIM_LIGHTING_MIX_FACTOR_DEFAULT,
        soft_min=0,
        soft_max=1,
        get=get_rim_lighting_mix_factor,
        set=set_rim_lighting_mix_factor,
    )

    def get_parametric_rim_fresnel_power_factor(self) -> float:
        return self.get_float(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_PARAMETRIC_RIM_FRESNEL_POWER_LABEL,
            default_value=shader.OUTPUT_GROUP_PARAMETRIC_RIM_FRESNEL_POWER_DEFAULT,
        )

    def set_parametric_rim_fresnel_power_factor(self, value: object) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_PARAMETRIC_RIM_FRESNEL_POWER_LABEL,
            value,
        )

    parametric_rim_fresnel_power_factor: FloatProperty(  # type: ignore[valid-type]
        name=shader.OUTPUT_GROUP_PARAMETRIC_RIM_FRESNEL_POWER_LABEL,
        min=0.0,
        default=shader.OUTPUT_GROUP_PARAMETRIC_RIM_FRESNEL_POWER_DEFAULT,
        soft_max=100.0,
        get=get_parametric_rim_fresnel_power_factor,
        set=set_parametric_rim_fresnel_power_factor,
    )

    def get_parametric_rim_lift_factor(self) -> float:
        return self.get_float(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_PARAMETRIC_RIM_LIFT_FACTOR_LABEL,
            default_value=shader.OUTPUT_GROUP_PARAMETRIC_RIM_LIFT_FACTOR_DEFAULT,
        )

    def set_parametric_rim_lift_factor(self, value: object) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_PARAMETRIC_RIM_LIFT_FACTOR_LABEL,
            value,
        )

    parametric_rim_lift_factor: FloatProperty(  # type: ignore[valid-type]
        name=shader.OUTPUT_GROUP_PARAMETRIC_RIM_LIFT_FACTOR_LABEL,
        soft_min=0.0,
        default=shader.OUTPUT_GROUP_PARAMETRIC_RIM_LIFT_FACTOR_DEFAULT,
        soft_max=1.0,
        get=get_parametric_rim_lift_factor,
        set=set_parametric_rim_lift_factor,
    )

    (
        outline_width_mode_enum,
        (
            OUTLINE_WIDTH_MODE_NONE,
            OUTLINE_WIDTH_MODE_WORLD_COORDINATES,
            OUTLINE_WIDTH_MODE_SCREEN_COORDINATES,
        ),
    ) = property_group_enum(
        (
            "none",
            "None",
            "",
            "NONE",
            shader.OUTPUT_GROUP_OUTLINE_WIDTH_MODE_MIN,
        ),
        ("worldCoordinates", "World Coordinates", "", "NONE", 1),
        (
            "screenCoordinates",
            "Screen Coordinates",
            "",
            "NONE",
            shader.OUTPUT_GROUP_OUTLINE_WIDTH_MODE_MAX,
        ),
    )

    def get_outline_width_mode(self) -> int:
        return self.get_int(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_OUTLINE_WIDTH_MODE_LABEL,
            default_value=shader.OUTPUT_GROUP_OUTLINE_WIDTH_MODE_DEFAULT,
        )

    def set_outline_width_mode(self, value: object) -> None:
        self.set_int(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_OUTLINE_WIDTH_MODE_LABEL,
            value,
        )
        self.update_outline_geometry()

    def update_outline_geometry(self) -> None:
        material = self.find_material()
        if get_material_mtoon1_extension(material).is_outline_material:
            return
        ops.vrm.refresh_mtoon1_outline(
            material_name=material.name, create_modifier=True
        )

    outline_width_mode: EnumProperty(  # type: ignore[valid-type]
        items=outline_width_mode_enum.items(),
        name=shader.OUTPUT_GROUP_OUTLINE_WIDTH_MODE_LABEL,
        get=get_outline_width_mode,
        set=set_outline_width_mode,
    )

    def get_outline_width_factor(self) -> float:
        return self.get_value(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_OUTLINE_WIDTH_FACTOR_LABEL,
            default_value=shader.OUTPUT_GROUP_OUTLINE_WIDTH_FACTOR_DEFAULT,
        )

    def set_outline_width_factor(self, value: object) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_OUTLINE_WIDTH_FACTOR_LABEL,
            value,
        )
        self.update_outline_geometry()

    outline_width_factor: FloatProperty(  # type: ignore[valid-type]
        name=shader.OUTPUT_GROUP_OUTLINE_WIDTH_FACTOR_LABEL,
        default=shader.OUTPUT_GROUP_OUTLINE_WIDTH_FACTOR_DEFAULT,
        min=0.0,
        soft_max=0.05,
        get=get_outline_width_factor,
        set=set_outline_width_factor,
    )

    outline_width_multiply_texture: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1OutlineWidthMultiplyTextureInfoPropertyGroup
    )

    def get_outline_color_factor(self) -> tuple[float, float, float]:
        return self.get_rgb(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_OUTLINE_COLOR_FACTOR_LABEL,
            default_value=shader.OUTPUT_GROUP_OUTLINE_COLOR_FACTOR_DEFAULT,
        )

    def set_outline_color_factor(self, value: object) -> None:
        self.set_rgb(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_OUTLINE_COLOR_FACTOR_LABEL,
            value,
            shader.OUTPUT_GROUP_OUTLINE_COLOR_FACTOR_DEFAULT,
        )
        self.update_outline_geometry()

        material = self.find_material()
        mtoon1 = get_material_mtoon1_extension(material)
        if mtoon1.is_outline_material:
            return
        outline_material = mtoon1.outline_material
        if not outline_material:
            return
        outline_principled_bsdf = PrincipledBSDFWrapper(
            outline_material, is_readonly=False
        )

        outline_diffuse_alpha = outline_material.diffuse_color[3]
        outline_principled_bsdf.base_color = (
            self.outline_color_factor[0],
            self.outline_color_factor[1],
            self.outline_color_factor[2],
        )
        outline_material.diffuse_color[3] = outline_diffuse_alpha

    outline_color_factor: FloatVectorProperty(  # type: ignore[valid-type]
        name=shader.OUTPUT_GROUP_OUTLINE_COLOR_FACTOR_LABEL,
        size=3,
        subtype="COLOR",
        default=shader.OUTPUT_GROUP_OUTLINE_COLOR_FACTOR_DEFAULT,
        min=0,
        max=1,
        get=get_outline_color_factor,
        set=set_outline_color_factor,
    )

    def get_outline_lighting_mix_factor(self) -> float:
        return self.get_value(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_OUTLINE_LIGHTING_MIX_FACTOR_LABEL,
            default_value=shader.OUTPUT_GROUP_OUTLINE_LIGHTING_MIX_FACTOR_DEFAULT,
        )

    def set_outline_lighting_mix_factor(self, value: object) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_OUTLINE_LIGHTING_MIX_FACTOR_LABEL,
            value,
        )
        self.update_outline_geometry()

    outline_lighting_mix_factor: FloatProperty(  # type: ignore[valid-type]
        name=shader.OUTPUT_GROUP_OUTLINE_LIGHTING_MIX_FACTOR_LABEL,
        min=0.0,
        default=shader.OUTPUT_GROUP_OUTLINE_LIGHTING_MIX_FACTOR_DEFAULT,
        max=1.0,
        get=get_outline_lighting_mix_factor,
        set=set_outline_lighting_mix_factor,
    )

    def update_enable_outline_preview(self, context: Context) -> None:
        material_name = self.find_material().name
        ops.vrm.refresh_mtoon1_outline(
            material_name=material_name, create_modifier=True
        )
        for material in context.blend_data.materials:
            if material.name == material_name:
                continue
            ext = get_material_mtoon1_extension(material)
            if not ext.enabled:
                continue
            mtoon = ext.extensions.vrmc_materials_mtoon
            if mtoon.enable_outline_preview != self.enable_outline_preview:
                mtoon.enable_outline_preview = self.enable_outline_preview

    enable_outline_preview: BoolProperty(  # type: ignore[valid-type]
        default=True,
        update=update_enable_outline_preview,
    )

    uv_animation_mask_texture: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1UvAnimationMaskTextureInfoPropertyGroup
    )

    def get_uv_animation_scroll_x_speed_factor(self) -> float:
        return self.get_value(
            shader.UV_ANIMATION_GROUP_NAME,
            shader.UV_ANIMATION_GROUP_TRANSLATE_X_LABEL,
            default_value=shader.UV_ANIMATION_GROUP_TRANSLATE_X_DEFAULT,
        )

    def set_uv_animation_scroll_x_speed_factor(self, value: object) -> None:
        self.set_value(
            shader.UV_ANIMATION_GROUP_NAME,
            shader.UV_ANIMATION_GROUP_TRANSLATE_X_LABEL,
            value,
        )

    uv_animation_scroll_x_speed_factor: FloatProperty(  # type: ignore[valid-type]
        name=shader.UV_ANIMATION_GROUP_TRANSLATE_X_LABEL,
        default=shader.UV_ANIMATION_GROUP_TRANSLATE_X_DEFAULT,
        get=get_uv_animation_scroll_x_speed_factor,
        set=set_uv_animation_scroll_x_speed_factor,
    )

    def get_uv_animation_scroll_y_speed_factor(self) -> float:
        return self.get_value(
            shader.UV_ANIMATION_GROUP_NAME,
            shader.UV_ANIMATION_GROUP_TRANSLATE_Y_LABEL,
            default_value=shader.UV_ANIMATION_GROUP_TRANSLATE_Y_DEFAULT,
        )

    def set_uv_animation_scroll_y_speed_factor(self, value: object) -> None:
        self.set_value(
            shader.UV_ANIMATION_GROUP_NAME,
            shader.UV_ANIMATION_GROUP_TRANSLATE_Y_LABEL,
            value,
        )

    uv_animation_scroll_y_speed_factor: FloatProperty(  # type: ignore[valid-type]
        name=shader.UV_ANIMATION_GROUP_TRANSLATE_Y_LABEL,
        default=shader.UV_ANIMATION_GROUP_TRANSLATE_Y_DEFAULT,
        get=get_uv_animation_scroll_y_speed_factor,
        set=set_uv_animation_scroll_y_speed_factor,
    )

    def get_uv_animation_rotation_speed_factor(self) -> float:
        return self.get_value(
            shader.UV_ANIMATION_GROUP_NAME,
            shader.UV_ANIMATION_GROUP_ROTATION_LABEL,
            default_value=shader.UV_ANIMATION_GROUP_ROTATION_DEFAULT,
        )

    def set_uv_animation_rotation_speed_factor(self, value: object) -> None:
        self.set_value(
            shader.UV_ANIMATION_GROUP_NAME,
            shader.UV_ANIMATION_GROUP_ROTATION_LABEL,
            value,
        )

    uv_animation_rotation_speed_factor: FloatProperty(  # type: ignore[valid-type]
        name=shader.UV_ANIMATION_GROUP_ROTATION_LABEL,
        get=get_uv_animation_rotation_speed_factor,
        set=set_uv_animation_rotation_speed_factor,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        transparent_with_z_write: bool  # type: ignore[no-redef]
        render_queue_offset_number: int  # type: ignore[no-redef]
        shade_multiply_texture: (  # type: ignore[no-redef]
            Mtoon1ShadeMultiplyTextureInfoPropertyGroup
        )
        shade_color_factor: Sequence[float]  # type: ignore[no-redef]
        shading_shift_texture: (  # type: ignore[no-redef]
            Mtoon1ShadingShiftTextureInfoPropertyGroup
        )
        shading_shift_factor: float  # type: ignore[no-redef]
        shading_toony_factor: float  # type: ignore[no-redef]
        gi_equalization_factor: float  # type: ignore[no-redef]
        matcap_factor: Sequence[float]  # type: ignore[no-redef]
        matcap_texture: Mtoon1MatcapTextureInfoPropertyGroup  # type: ignore[no-redef]
        parametric_rim_color_factor: Sequence[float]  # type: ignore[no-redef]
        rim_multiply_texture: (  # type: ignore[no-redef]
            Mtoon1RimMultiplyTextureInfoPropertyGroup
        )
        rim_lighting_mix_factor: float  # type: ignore[no-redef]
        parametric_rim_fresnel_power_factor: float  # type: ignore[no-redef]
        parametric_rim_lift_factor: float  # type: ignore[no-redef]
        outline_width_mode: str  # type: ignore[no-redef]
        outline_width_factor: float  # type: ignore[no-redef]
        outline_width_multiply_texture: (  # type: ignore[no-redef]
            Mtoon1OutlineWidthMultiplyTextureInfoPropertyGroup
        )
        outline_color_factor: Sequence[float]  # type: ignore[no-redef]
        outline_lighting_mix_factor: float  # type: ignore[no-redef]
        enable_outline_preview: bool  # type: ignore[no-redef]
        uv_animation_mask_texture: (  # type: ignore[no-redef]
            Mtoon1UvAnimationMaskTextureInfoPropertyGroup
        )
        uv_animation_scroll_x_speed_factor: float  # type: ignore[no-redef]
        uv_animation_scroll_y_speed_factor: float  # type: ignore[no-redef]
        uv_animation_rotation_speed_factor: float  # type: ignore[no-redef]


# https://github.com/KhronosGroup/glTF/blob/d997b7dc7e426bc791f5613475f5b4490da0b099/extensions/2.0/Khronos/KHR_materials_emissive_strength/schema/glTF.KHR_materials_emissive_strength.schema.json
class Mtoon1KhrMaterialsEmissiveStrengthPropertyGroup(MaterialTraceablePropertyGroup):
    material_property_chain = (
        "extensions",
        "khr_materials_emissive_strength",
    )

    def get_emissive_strength(self) -> float:
        return self.get_float(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_EMISSIVE_STRENGTH_LABEL,
            default_value=shader.OUTPUT_GROUP_EMISSIVE_STRENGTH_DEFAULT,
        )

    def set_emissive_strength(self, value: object) -> None:
        self.set_value(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_EMISSIVE_STRENGTH_LABEL,
            value,
        )

        material = self.find_material()
        principled_bsdf = PrincipledBSDFWrapper(material, is_readonly=False)
        principled_bsdf.emission_strength = self.emissive_strength

        emissive_node = get_gltf_emissive_node(material)
        if emissive_node is not None:
            socket = emissive_node.inputs.get(EMISSION_STRENGTH_INPUT_KEY)
            if isinstance(socket, NodeSocketFloat):
                socket.default_value = self.emissive_strength

        mtoon1 = get_material_mtoon1_extension(material)
        if mtoon1.is_outline_material:
            return
        outline_material = mtoon1.outline_material
        if not outline_material:
            return
        outline_principled_bsdf = PrincipledBSDFWrapper(
            outline_material, is_readonly=False
        )
        outline_principled_bsdf.emission_strength = self.emissive_strength

        outline_emissive_node = get_gltf_emissive_node(outline_material)
        if outline_emissive_node is not None:
            outline_socket = outline_emissive_node.inputs.get(
                EMISSION_STRENGTH_INPUT_KEY
            )
            if isinstance(outline_socket, NodeSocketFloat):
                outline_socket.default_value = self.emissive_strength

    emissive_strength: FloatProperty(  # type: ignore[valid-type]
        name="Strength",
        min=0.0,
        default=shader.OUTPUT_GROUP_EMISSIVE_STRENGTH_DEFAULT,
        get=get_emissive_strength,
        set=set_emissive_strength,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        emissive_strength: float  # type: ignore[no-redef]


class Mtoon1MaterialExtensionsPropertyGroup(PropertyGroup):
    vrmc_materials_mtoon: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1VrmcMaterialsMtoonPropertyGroup
    )
    khr_materials_emissive_strength: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1KhrMaterialsEmissiveStrengthPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        vrmc_materials_mtoon: (  # type: ignore[no-redef]
            Mtoon1VrmcMaterialsMtoonPropertyGroup
        )
        khr_materials_emissive_strength: (  # type: ignore[no-redef]
            Mtoon1KhrMaterialsEmissiveStrengthPropertyGroup
        )


# https://github.com/vrm-c/vrm-specification/blob/8dc51ec7241be27ee95f159cefc0190a0e41967b/specification/VRMC_materials_mtoon-1.0-beta/schema/VRMC_materials_mtoon.schema.json
class Mtoon1MaterialPropertyGroup(MaterialTraceablePropertyGroup):
    material_property_chain: tuple[str, ...] = ()

    INITIAL_ADDON_VERSION = VrmAddonPreferences.INITIAL_ADDON_VERSION

    addon_version: IntVectorProperty(  # type: ignore[valid-type]
        size=3,
        default=INITIAL_ADDON_VERSION,
    )

    pbr_metallic_roughness: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1PbrMetallicRoughnessPropertyGroup
    )

    (
        alpha_mode_enum,
        (
            ALPHA_MODE_OPAQUE,
            ALPHA_MODE_MASK,
            ALPHA_MODE_BLEND,
        ),
    ) = property_group_enum(
        ("OPAQUE", "Opaque", "", "NONE", 0),
        ("MASK", "Cutout", "", "NONE", 1),
        ("BLEND", "Transparent", "", "NONE", 2),
    )

    alpha_mode_blend_method_hashed: BoolProperty()  # type: ignore[valid-type]

    def get_alpha_mode(self) -> int:
        alpha_mode_value = self.get_int(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_ALPHA_MODE_LABEL,
            default_value=self.ALPHA_MODE_OPAQUE.value,
        )
        if alpha_mode_value in self.alpha_mode_enum.values():
            return alpha_mode_value
        return self.ALPHA_MODE_OPAQUE.value

    @staticmethod
    def update_alpha_nodes(material: Material, alpha_mode_value: int) -> None:
        node_tree = material.node_tree
        if not node_tree:
            return

        # glTFのノードに合わせる
        # https://docs.blender.org/manual/en/4.2/addons/import_export/scene_gltf2.html#alpha-modes
        mtoon1 = get_material_mtoon1_extension(material)
        texture = mtoon1.pbr_metallic_roughness.base_color_texture.index
        tex_image_node_name = texture.get_image_texture_node_name()

        if alpha_mode_value != mtoon1.ALPHA_MODE_MASK.value:
            TextureTraceablePropertyGroup.unlink_nodes(
                material,
                StaticNodeSocketTarget(
                    in_node_name=ALPHA_CLIP_INPUT_NODE_NAME,
                    in_node_type=ShaderNodeMath,
                    in_socket_name=ALPHA_CLIP_INPUT_NODE_SOCKET_NAME,
                ),
            )
            TextureTraceablePropertyGroup.unlink_nodes(
                material,
                PrincipledBsdfNodeSocketTarget(
                    in_socket_name=PRINCIPLED_BSDF_ALPHA_INPUT_KEY
                ),
            )
        if alpha_mode_value != mtoon1.ALPHA_MODE_BLEND.value or bpy.app.version < (
            4,
            2,
        ):
            TextureTraceablePropertyGroup.unlink_nodes(
                material,
                PrincipledBsdfNodeSocketTarget(
                    in_socket_name=PRINCIPLED_BSDF_ALPHA_INPUT_KEY
                ),
            )

        principled_bsdf = PrincipledBSDFWrapper(material, is_readonly=False)
        if bpy.app.version < (4, 2):
            principled_bsdf.alpha = mtoon1.pbr_metallic_roughness.base_color_factor[3]
            tex_image_node = node_tree.nodes.get(tex_image_node_name)
            if isinstance(tex_image_node, ShaderNodeTexImage):
                TextureTraceablePropertyGroup.link_or_unlink_nodes(
                    material,
                    tex_image_node_name,
                    ShaderNodeTexImage,
                    TEX_IMAGE_ALPHA_OUTPUT_KEY,
                    PrincipledBsdfNodeSocketTarget(
                        in_socket_name=PRINCIPLED_BSDF_ALPHA_INPUT_KEY
                    ),
                    link=bool(tex_image_node.image),
                )
        elif alpha_mode_value == mtoon1.ALPHA_MODE_OPAQUE.value:
            principled_bsdf.alpha = 1.0
        elif alpha_mode_value == mtoon1.ALPHA_MODE_MASK.value:
            tex_image_node = node_tree.nodes.get(tex_image_node_name)
            image_exists = False
            if isinstance(tex_image_node, ShaderNodeTexImage):
                image_exists = bool(tex_image_node.image)
                TextureTraceablePropertyGroup.link_or_unlink_nodes(
                    material,
                    tex_image_node_name,
                    ShaderNodeTexImage,
                    TEX_IMAGE_ALPHA_OUTPUT_KEY,
                    StaticNodeSocketTarget(
                        in_node_name=ALPHA_CLIP_INPUT_NODE_NAME,
                        in_node_type=ShaderNodeMath,
                        in_socket_name=ALPHA_CLIP_INPUT_NODE_SOCKET_NAME,
                    ),
                    link=image_exists,
                )
                TextureTraceablePropertyGroup.link_or_unlink_nodes(
                    material,
                    ALPHA_CLIP_OUTPUT_NODE_NAME,
                    ShaderNodeMath,
                    ALPHA_CLIP_OUTPUT_NODE_SOCKET_NAME,
                    PrincipledBsdfNodeSocketTarget(
                        in_socket_name=PRINCIPLED_BSDF_ALPHA_INPUT_KEY
                    ),
                    link=image_exists,
                )
            if not image_exists:
                alpha = mtoon1.pbr_metallic_roughness.base_color_factor[3]
                if alpha >= mtoon1.alpha_cutoff:
                    principled_bsdf.alpha = 1.0
                else:
                    principled_bsdf.alpha = 0.0
        elif alpha_mode_value == mtoon1.ALPHA_MODE_BLEND.value:
            principled_bsdf.alpha = mtoon1.pbr_metallic_roughness.base_color_factor[3]
            tex_image_node = node_tree.nodes.get(tex_image_node_name)
            if isinstance(tex_image_node, ShaderNodeTexImage):
                TextureTraceablePropertyGroup.link_or_unlink_nodes(
                    material,
                    tex_image_node_name,
                    ShaderNodeTexImage,
                    TEX_IMAGE_ALPHA_OUTPUT_KEY,
                    PrincipledBsdfNodeSocketTarget(
                        in_socket_name=PRINCIPLED_BSDF_ALPHA_INPUT_KEY
                    ),
                    link=bool(tex_image_node.image),
                )

        alpha_clip_input_node = node_tree.nodes.get(ALPHA_CLIP_INPUT_NODE_NAME)
        if (
            isinstance(alpha_clip_input_node, ShaderNodeMath)
            and alpha_clip_input_node.operation == "MINIMUM"
        ):
            inputs = alpha_clip_input_node.inputs
            if len(inputs) >= 2:
                alpha_input = inputs[0]
                if isinstance(alpha_input, shader.FLOAT_SOCKET_CLASSES):
                    alpha_input.default_value = (
                        mtoon1.pbr_metallic_roughness.base_color_factor[3]
                    )
                else:
                    logger.error(
                        "Unexpected alpha input node input type: %s", type(alpha_input)
                    )

                alpha_cutoff_input = inputs[1]
                if isinstance(alpha_cutoff_input, shader.FLOAT_SOCKET_CLASSES):
                    alpha_cutoff_input.default_value = mtoon1.alpha_cutoff
                else:
                    logger.error(
                        "Unexpected alpha clip input node input type: %s",
                        type(alpha_cutoff_input),
                    )
            else:
                logger.error(
                    "Unexpected alpha clip input node input length: %s", len(inputs)
                )
        else:
            logger.error(
                "Unexpected alpha clip input node type: %s",
                type(alpha_clip_input_node),
            )

    def set_alpha_mode(self, value: int) -> None:
        changed = self.get_alpha_mode() != value

        material = self.find_material()

        shadow_method = None
        if bpy.app.version < (4, 2):
            if material.blend_method == "HASHED":
                self.alpha_mode_blend_method_hashed = True
            if material.blend_method == "BLEND":
                self.alpha_mode_blend_method_hashed = False

            if value == self.ALPHA_MODE_OPAQUE.value:
                material.blend_method = "OPAQUE"
                shadow_method = "OPAQUE"
            elif value == self.ALPHA_MODE_MASK.value:
                material.blend_method = "CLIP"
                shadow_method = "CLIP"
            elif value == self.ALPHA_MODE_BLEND.value:
                material.blend_method = "HASHED"
                shadow_method = "HASHED"
            else:
                logger.error("Unexpected alpha mode: {value}")
                material.blend_method = "OPAQUE"
                shadow_method = "OPAQUE"

        self.set_value(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_ALPHA_MODE_LABEL,
            value,
        )

        if changed:
            self.set_mtoon0_render_queue_and_clamp(self.mtoon0_render_queue)

        self.update_alpha_nodes(material, value)

        if self.is_outline_material:
            if bpy.app.version < (4, 2):
                material.shadow_method = "NONE"
            return

        if bpy.app.version < (4, 3) and shadow_method is not None:
            material.shadow_method = shadow_method

        outline_material = self.outline_material
        if not outline_material:
            return
        get_material_mtoon1_extension(outline_material).set_alpha_mode(value)

    alpha_mode: EnumProperty(  # type: ignore[valid-type]
        items=alpha_mode_enum.items(),
        name="Alpha Mode",
        get=get_alpha_mode,
        set=set_alpha_mode,
    )

    def get_double_sided(self) -> bool:
        return not self.find_material().use_backface_culling

    def set_double_sided(self, value: object) -> None:
        material = self.find_material()
        material.use_backface_culling = not value
        self.set_bool(
            shader.OUTPUT_GROUP_NAME, shader.OUTPUT_GROUP_DOUBLE_SIDED_LABEL, value
        )
        if get_material_mtoon1_extension(material).is_outline_material:
            return
        outline_material = get_material_mtoon1_extension(material).outline_material
        if not outline_material:
            return
        get_material_mtoon1_extension(outline_material).double_sided = False

    double_sided: BoolProperty(  # type: ignore[valid-type]
        name=shader.OUTPUT_GROUP_DOUBLE_SIDED_LABEL,
        get=get_double_sided,
        set=set_double_sided,
    )

    def get_alpha_cutoff(self) -> float:
        return self.get_float(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_ALPHA_CUTOFF_LABEL,
            default_value=shader.OUTPUT_GROUP_ALPHA_CUTOFF_DEFAULT,
        )

    def set_alpha_cutoff(self, value: float) -> None:
        material = self.find_material()
        if bpy.app.version < (4, 2):
            material.alpha_threshold = max(0, min(1, value - 0.00001))  # TODO: ...
        self.set_value(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_ALPHA_CUTOFF_LABEL,
            max(0, value),
        )

        self.update_alpha_nodes(material, self.get_alpha_mode())

        if self.is_outline_material:
            return
        outline_material = self.outline_material
        if not outline_material:
            return
        get_material_mtoon1_extension(outline_material).set_alpha_cutoff(value)

    alpha_cutoff: FloatProperty(  # type: ignore[valid-type]
        name="Cutoff",
        min=0,
        soft_max=1,
        get=get_alpha_cutoff,
        set=set_alpha_cutoff,
    )

    normal_texture: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1NormalTextureInfoPropertyGroup
    )

    emissive_texture: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1EmissiveTextureInfoPropertyGroup
    )

    def get_emissive_factor(self) -> tuple[float, float, float]:
        return self.get_rgb(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_EMISSIVE_FACTOR_LABEL,
            default_value=shader.OUTPUT_GROUP_EMISSIVE_FACTOR_DEFAULT,
        )

    def set_emissive_factor(self, value: object) -> None:
        self.set_rgb(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_EMISSIVE_FACTOR_LABEL,
            value,
            shader.OUTPUT_GROUP_EMISSIVE_FACTOR_DEFAULT,
        )

        material = self.find_material()
        principled_bsdf = PrincipledBSDFWrapper(material, is_readonly=False)
        principled_bsdf.emission_color = (
            self.emissive_factor[0],
            self.emissive_factor[1],
            self.emissive_factor[2],
        )

        emissive_node = get_gltf_emissive_node(material)
        if emissive_node is not None:
            socket = emissive_node.inputs.get(EMISSION_COLOR_INPUT_KEY)
            if isinstance(socket, NodeSocketColor):
                socket.default_value = (
                    self.emissive_factor[0],
                    self.emissive_factor[1],
                    self.emissive_factor[2],
                    1,
                )

        mtoon1 = get_material_mtoon1_extension(material)
        if mtoon1.is_outline_material:
            return
        outline_material = mtoon1.outline_material
        if not outline_material:
            return
        outline_principled_bsdf = PrincipledBSDFWrapper(
            outline_material, is_readonly=False
        )
        outline_principled_bsdf.emission_color = (
            self.emissive_factor[0],
            self.emissive_factor[1],
            self.emissive_factor[2],
        )

        outline_emissive_node = get_gltf_emissive_node(material)
        if outline_emissive_node is not None:
            outline_socket = outline_emissive_node.inputs.get(EMISSION_COLOR_INPUT_KEY)
            if isinstance(outline_socket, NodeSocketColor):
                outline_socket.default_value = (
                    self.emissive_factor[0],
                    self.emissive_factor[1],
                    self.emissive_factor[2],
                    1,
                )

    emissive_factor: FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="COLOR",
        default=shader.OUTPUT_GROUP_EMISSIVE_FACTOR_DEFAULT,
        min=0,
        max=1,
        get=get_emissive_factor,
        set=set_emissive_factor,
    )

    extensions: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MaterialExtensionsPropertyGroup
    )

    def get_enabled_in_material(self, material: Material) -> bool:
        if self.is_outline_material:
            return False

        if not material.use_nodes:
            return False

        node_tree = material.node_tree
        if not node_tree:
            return False

        group_node = node_tree.nodes.get("Mtoon1Material.Mtoon1Output")
        if not isinstance(group_node, ShaderNodeGroup):
            return False

        group_node_tree = group_node.node_tree
        if not group_node_tree:
            return False

        if group_node_tree.name != shader.OUTPUT_GROUP_NAME:
            return False

        return bool(self.get("enabled"))

    def get_enabled(self) -> bool:
        return self.get_enabled_in_material(self.find_material())

    def set_enabled(self, value: object) -> None:
        material = self.find_material()

        if not value:
            if self.get("enabled") and material.use_nodes:
                ops.vrm.convert_mtoon1_to_bsdf_principled(material_name=material.name)
            self["enabled"] = False
            return

        if not material.use_nodes:
            material.use_nodes = True
        if self.get_enabled():
            return

        ops.vrm.convert_material_to_mtoon1(material_name=material.name)
        self["enabled"] = True
        self.setup_drivers()

    enabled: BoolProperty(  # type: ignore[valid-type]
        name="Enable VRM MToon Material",
        get=get_enabled,
        set=set_enabled,
    )

    export_shape_key_normals: BoolProperty(  # type: ignore[valid-type]
        name="Export Shape Key Normals",
    )

    def update_is_outline_material(self, _context: Context) -> None:
        self.set_bool(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_IS_OUTLINE_LABEL,
            self.is_outline_material,
        )
        self.set_bool(
            shader.NORMAL_GROUP_NAME,
            shader.NORMAL_GROUP_IS_OUTLINE_LABEL,
            self.is_outline_material,
        )
        self.set_bool(
            shader.OUTPUT_GROUP_NAME,
            shader.OUTPUT_GROUP_DOUBLE_SIDED_LABEL,
            False if self.is_outline_material else self.double_sided,
        )

    is_outline_material: BoolProperty(  # type: ignore[valid-type]
        update=update_is_outline_material,
    )

    outline_material: PointerProperty(  # type: ignore[valid-type]
        type=Material,
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
        self, *, downgrade_to_mtoon0: bool
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

    show_expanded_mtoon0: BoolProperty(  # type: ignore[valid-type]
        name="Show MToon 0.0 Options",
    )

    mtoon0_front_cull_mode: BoolProperty(  # type: ignore[valid-type]
        name="Front Face Culling",
    )

    mtoon0_outline_scaled_max_distance: FloatProperty(  # type: ignore[valid-type]
        name="Outline Width Scaled Max Distance",
        min=1,
        default=1,
        max=10,
    )

    mtoon0_light_color_attenuation: FloatProperty(  # type: ignore[valid-type]
        name="LightColor Attenuation",
        min=0,
        default=0,
        max=1,
    )

    mtoon0_receive_shadow_texture: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon0ReceiveShadowTexturePropertyGroup
    )

    mtoon0_receive_shadow_rate: FloatProperty(  # type: ignore[valid-type]
        min=0,
        default=1,
        max=1,
    )

    mtoon0_shading_grade_texture: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon0ShadingGradeTexturePropertyGroup
    )

    mtoon0_shading_grade_rate: FloatProperty(  # type: ignore[valid-type]
        min=0,
        default=1,
        max=1,
    )

    mtoon0_rim_lighting_mix: FloatProperty(  # type: ignore[valid-type]
        name="Rim LightingMix (MToon 0.0)",
        min=0,
        default=0,
        max=1,
    )

    def get_mtoon0_render_queue_and_clamp(self) -> int:
        return int(self.mtoon0_render_queue)

    def set_mtoon0_render_queue_and_clamp(self, value: int) -> None:
        # https://github.com/Santarh/MToon/blob/42b03163459ac8e6b7aee08070d0f4f912035069/MToon/Scripts/Utils.cs#L74-L113
        if self.alpha_mode == self.ALPHA_MODE_OPAQUE.identifier:
            mtoon0_render_queue = 2000
        elif self.alpha_mode == self.ALPHA_MODE_MASK.identifier:
            mtoon0_render_queue = 2450
        elif not self.extensions.vrmc_materials_mtoon.transparent_with_z_write:
            mtoon0_render_queue = max(2951, min(3000, value))
        else:
            mtoon0_render_queue = max(2501, min(2550, value))

        if self.mtoon0_render_queue != mtoon0_render_queue:
            self.mtoon0_render_queue = mtoon0_render_queue

    # MToon0用のRender Queueの値を設定する。値代入時にクランプを行う。
    # UniVRMはUIからの値設定時や、Alpha Modeなどの変更時にクランプを行うため、
    # それと挙動を合わせる際はこちらを使う。
    mtoon0_render_queue_and_clamp: IntProperty(  # type: ignore[valid-type]
        name="Render Queue",
        get=get_mtoon0_render_queue_and_clamp,
        set=set_mtoon0_render_queue_and_clamp,
    )

    # MToon0用のRender Queueの値を設定する。値代入時にクランプを行わない。
    # UniVRMはVRM0のインポート時やエクスポート時はクランプを行わないため、
    # それと挙動を合わせるためインポート時やエクスポート時はこちらを使う。
    mtoon0_render_queue: IntProperty(  # type: ignore[valid-type]
        name="Render Queue",
        default=2000,
    )

    def setup_drivers(self) -> None:
        material = self.find_material()
        for texture_info in self.all_texture_info():
            texture_info.setup_drivers(material)

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        addon_version: Sequence[int]  # type: ignore[no-redef]
        pbr_metallic_roughness: (  # type: ignore[no-redef]
            Mtoon1PbrMetallicRoughnessPropertyGroup
        )
        alpha_mode_blend_method_hashed: bool  # type: ignore[no-redef]
        alpha_mode: str  # type: ignore[no-redef]
        double_sided: bool  # type: ignore[no-redef]
        alpha_cutoff: float  # type: ignore[no-redef]
        normal_texture: Mtoon1NormalTextureInfoPropertyGroup  # type: ignore[no-redef]
        emissive_texture: (  # type: ignore[no-redef]
            Mtoon1EmissiveTextureInfoPropertyGroup
        )
        emissive_factor: Sequence[float]  # type: ignore[no-redef]
        extensions: Mtoon1MaterialExtensionsPropertyGroup  # type: ignore[no-redef]
        enabled: bool  # type: ignore[no-redef]
        export_shape_key_normals: bool  # type: ignore[no-redef]
        is_outline_material: bool  # type: ignore[no-redef]
        outline_material: Optional[Material]  # type: ignore[no-redef]
        show_expanded_mtoon0: bool  # type: ignore[no-redef]
        mtoon0_front_cull_mode: bool  # type: ignore[no-redef]
        mtoon0_outline_scaled_max_distance: float  # type: ignore[no-redef]
        mtoon0_light_color_attenuation: float  # type: ignore[no-redef]
        mtoon0_receive_shadow_texture: (  # type: ignore[no-redef]
            Mtoon0ReceiveShadowTexturePropertyGroup
        )
        mtoon0_receive_shadow_rate: float  # type: ignore[no-redef]
        mtoon0_shading_grade_texture: (  # type: ignore[no-redef]
            Mtoon0ShadingGradeTexturePropertyGroup
        )
        mtoon0_shading_grade_rate: float  # type: ignore[no-redef]
        mtoon0_rim_lighting_mix: float  # type: ignore[no-redef]
        mtoon0_render_queue_and_clamp: int  # type: ignore[no-redef]
        mtoon0_render_queue: int  # type: ignore[no-redef]


def reset_shader_node_group(
    context: Context,
    material: Material,
    *,
    reset_material_node_tree: bool,
    reset_node_groups: bool,
) -> None:
    gltf = get_material_mtoon1_extension(material)
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
    matcap_factor = list(mtoon.matcap_factor)
    matcap_texture = mtoon.matcap_texture.backup()
    parametric_rim_color_factor = list(mtoon.parametric_rim_color_factor)
    rim_multiply_texture = mtoon.rim_multiply_texture.backup()
    rim_lighting_mix_factor = mtoon.rim_lighting_mix_factor
    parametric_rim_fresnel_power_factor = mtoon.parametric_rim_fresnel_power_factor
    parametric_rim_lift_factor = mtoon.parametric_rim_lift_factor
    enable_outline_preview = mtoon.enable_outline_preview
    outline_width_mode = mtoon.outline_width_mode
    outline_width_factor = mtoon.outline_width_factor
    outline_width_multiply_texture = mtoon.outline_width_multiply_texture.backup()
    outline_color_factor = list(mtoon.outline_color_factor)
    outline_lighting_mix_factor = mtoon.outline_lighting_mix_factor
    uv_animation_mask_texture = mtoon.uv_animation_mask_texture.backup()
    uv_animation_scroll_x_speed_factor = mtoon.uv_animation_scroll_x_speed_factor
    uv_animation_scroll_y_speed_factor = mtoon.uv_animation_scroll_y_speed_factor
    uv_animation_rotation_speed_factor = mtoon.uv_animation_rotation_speed_factor

    if reset_material_node_tree:
        shader.load_mtoon1_shader(
            context,
            material,
            reset_node_groups=reset_node_groups,
        )
        if gltf.outline_material:
            shader.load_mtoon1_shader(
                context,
                gltf.outline_material,
                reset_node_groups=reset_node_groups,
            )

    gltf.is_outline_material = False
    if gltf.outline_material:
        get_material_mtoon1_extension(gltf.outline_material).is_outline_material = True

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
    mtoon.enable_outline_preview = enable_outline_preview
    mtoon.outline_width_mode = outline_width_mode
    mtoon.outline_width_factor = outline_width_factor
    mtoon.outline_width_multiply_texture.restore(outline_width_multiply_texture)
    mtoon.outline_color_factor = outline_color_factor
    mtoon.outline_lighting_mix_factor = outline_lighting_mix_factor
    mtoon.uv_animation_mask_texture.restore(uv_animation_mask_texture)
    mtoon.uv_animation_scroll_x_speed_factor = uv_animation_scroll_x_speed_factor
    mtoon.uv_animation_scroll_y_speed_factor = uv_animation_scroll_y_speed_factor
    mtoon.uv_animation_rotation_speed_factor = uv_animation_rotation_speed_factor

    gltf.setup_drivers()
    gltf.addon_version = get_addon_version()


def get_material_mtoon1_extension(material: Material) -> Mtoon1MaterialPropertyGroup:
    from ..extension import get_material_extension

    mtoon1: Mtoon1MaterialPropertyGroup = get_material_extension(material).mtoon1
    return mtoon1


def setup_drivers(context: Context) -> None:
    for material in context.blend_data.materials:
        get_material_mtoon1_extension(material).setup_drivers()
    shader.setup_frame_count_driver(context)
