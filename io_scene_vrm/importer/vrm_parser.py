"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import contextlib
import re
import sys
import tempfile
from dataclasses import dataclass, field
from itertools import repeat
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

import bpy
from bpy.app.translations import pgettext

from ..common import deep
from ..common.binary_reader import BinaryReader
from ..common.convert import float3_or, float4_or, str_or
from ..common.deep import Json
from ..common.fs import (
    create_unique_indexed_directory_path,
    create_unique_indexed_file_path,
)
from ..common.gl import GL_TRIANGLES
from ..common.gltf import parse_glb
from ..common.logging import get_logger
from .license_validation import validate_license

logger = get_logger(__name__)


@dataclass
class PyMesh:
    object_id: int
    name: str = ""
    face_indices: List[List[int]] = field(default_factory=list)
    skin_id: Optional[int] = None
    material_index: int = 0
    POSITION_accessor: Optional[int] = None
    POSITION: Optional[List[List[float]]] = None
    JOINTS_0: Optional[List[List[int]]] = None
    WEIGHTS_0: Optional[List[List[float]]] = None
    NORMAL: Optional[List[List[float]]] = None
    vert_normal_normalized: Optional[bool] = None
    morph_target_point_list_and_accessor_index_dict: Optional[
        Dict[str, List[object]]
    ] = None
    has_FB_ngon_encoding: bool = False  # noqa: N815


@dataclass
class PyNode:
    name: str
    position: Sequence[float]
    rotation: Sequence[float]
    scale: Sequence[float]
    children: Optional[List[int]] = None
    blend_bone: Optional[bpy.types.Bone] = None
    mesh_id: Optional[int] = None
    skin_id: Optional[int] = None


@dataclass(frozen=True)
class Vrm0MaterialProperty:
    name: str
    shader: str
    render_queue: Optional[int]
    keyword_map: Dict[str, bool]
    tag_map: Dict[str, str]
    float_properties: Dict[str, float]
    vector_properties: Dict[str, List[float]]
    texture_properties: Dict[str, int]

    @staticmethod
    def create(json_dict: Json) -> "Vrm0MaterialProperty":
        fallback = Vrm0MaterialProperty(
            name="Undefined",
            shader="VRM_USE_GLTFSHADER",
            render_queue=None,
            keyword_map={},
            tag_map={},
            float_properties={},
            vector_properties={},
            texture_properties={},
        )
        if not isinstance(json_dict, dict):
            return fallback

        name = json_dict.get("name")
        if not isinstance(name, str):
            name = fallback.name

        shader = json_dict.get("shader")
        if not isinstance(shader, str):
            shader = fallback.shader

        render_queue = json_dict.get("renderQueue")
        if not isinstance(render_queue, int):
            render_queue = fallback.render_queue

        raw_keyword_map = json_dict.get("keywordMap")
        if isinstance(raw_keyword_map, dict):
            keyword_map = {
                k: v for k, v in raw_keyword_map.items() if isinstance(v, bool)
            }
        else:
            keyword_map = fallback.keyword_map

        raw_tag_map = json_dict.get("tagMap")
        if isinstance(raw_tag_map, dict):
            tag_map = {k: v for k, v in raw_tag_map.items() if isinstance(v, str)}
        else:
            tag_map = fallback.tag_map

        raw_float_properties = json_dict.get("floatProperties")
        if isinstance(raw_float_properties, dict):
            float_properties = {
                k: v
                for k, v in raw_float_properties.items()
                if isinstance(v, (float, int))
            }
        else:
            float_properties = fallback.float_properties

        raw_vector_properties = json_dict.get("vectorProperties")
        if isinstance(raw_vector_properties, dict):
            vector_properties: Dict[str, List[float]] = {}
            for k, v in raw_vector_properties.items():
                if not isinstance(v, list):
                    continue
                float_v: List[float] = []
                ok = True
                for e in v:
                    if not isinstance(e, (float, int)):
                        ok = False
                        break
                    float_v.append(float(e))
                if ok:
                    vector_properties[k] = float_v
        else:
            vector_properties = fallback.vector_properties

        raw_texture_properties = json_dict.get("textureProperties")
        if isinstance(raw_texture_properties, dict):
            texture_properties = {
                k: v for k, v in raw_texture_properties.items() if isinstance(v, int)
            }
        else:
            texture_properties = fallback.texture_properties

        return Vrm0MaterialProperty(
            name=name,
            shader=shader,
            render_queue=render_queue,
            keyword_map=keyword_map,
            tag_map=tag_map,
            float_properties=float_properties,
            vector_properties=vector_properties,
            texture_properties=texture_properties,
        )


@dataclass
class ImageProperties:
    name: str
    filepath: Path
    filetype: str


@dataclass
class ParseResult:
    filepath: Path
    json_dict: Dict[str, Json] = field(default_factory=dict)
    spec_version_number: Tuple[int, int] = (0, 0)
    spec_version_str: str = "0.0"
    spec_version_is_stable: bool = True
    vrm0_extension: Dict[str, Json] = field(init=False, default_factory=dict)
    vrm1_extension: Dict[str, Json] = field(init=False, default_factory=dict)
    hips_node_index: Optional[int] = None
    image_properties: List[ImageProperties] = field(init=False, default_factory=list)
    meshes: List[List[PyMesh]] = field(init=False, default_factory=list)
    vrm0_material_properties: List[Vrm0MaterialProperty] = field(
        init=False, default_factory=list
    )
    nodes_dict: Dict[int, PyNode] = field(init=False, default_factory=dict)
    origin_nodes_dict: Dict[
        int, Union[Tuple[PyNode, int], Tuple[PyNode, int, int]]
    ] = field(init=False, default_factory=dict)
    skins_joints_list: List[List[int]] = field(init=False, default_factory=list)
    skins_root_node_list: List[int] = field(init=False, default_factory=list)


def create_py_bone(node: Dict[str, Json]) -> PyNode:
    v_node = PyNode(
        name=str_or(node.get("name"), "tmp"),
        position=float3_or(node.get("translation"), (0, 0, 0)),
        rotation=float4_or(node.get("rotation"), (0, 0, 0, 1)),
        scale=float3_or(node.get("scale"), (1, 1, 1)),
    )
    children = node.get("children")
    if isinstance(children, int):
        v_node.children = [children]
    elif isinstance(children, list):
        v_node.children = [child for child in children if isinstance(child, int)]
    else:
        v_node.children = None

    mesh_id = node.get("mesh")
    if isinstance(mesh_id, int):
        v_node.mesh_id = mesh_id

    skin_id = node.get("skin")
    if isinstance(skin_id, int):
        v_node.skin_id = skin_id

    return v_node


def remove_unsafe_path_chars(filename: str) -> str:
    unsafe_chars = {
        0: "\x00",
        1: "\x01",
        2: "\x02",
        3: "\x03",
        4: "\x04",
        5: "\x05",
        6: "\x06",
        7: "\x07",
        8: "\x08",
        9: "\t",
        10: "\n",
        11: "\x0b",
        12: "\x0c",
        13: "\r",
        14: "\x0e",
        15: "\x0f",
        16: "\x10",
        17: "\x11",
        18: "\x12",
        19: "\x13",
        20: "\x14",
        21: "\x15",
        22: "\x16",
        23: "\x17",
        24: "\x18",
        25: "\x19",
        26: "\x1a",
        27: "\x1b",
        28: "\x1c",
        29: "\x1d",
        30: "\x1e",
        31: "\x1f",
        34: '"',
        42: "*",
        47: "/",
        58: ":",
        60: "<",
        62: ">",
        63: "?",
        92: "\\",
        124: "|",
    }  # 32:space #33:!
    remove_table = str.maketrans(
        "".join([chr(unsafe_char) for unsafe_char in unsafe_chars]),
        "".join(repeat("_", len(unsafe_chars))),
    )
    safe_filename = filename.translate(remove_table)
    return safe_filename


#  "accessorの順に" データを読み込んでリストにしたものを返す
def decode_bin(
    json_dict: Dict[str, Json], binary: bytes
) -> List[List[Union[int, float, List[int], List[float]]]]:
    br = BinaryReader(binary)
    # This list indexed by accessor index
    decoded_binary: List[List[Union[int, float, List[int], List[float]]]] = []
    buffer_view_dicts = json_dict.get("bufferViews")
    if not isinstance(buffer_view_dicts, list):
        buffer_view_dicts = []
    accessor_dicts = json_dict.get("accessors")
    if not isinstance(accessor_dicts, list):
        return []
    type_num_dict = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
    for accessor_index, accessor_dict in enumerate(accessor_dicts):
        if not isinstance(accessor_dict, dict):
            continue
        accessor_type = accessor_dict.get("type")
        if not isinstance(accessor_type, str):
            continue
        type_num = type_num_dict.get(accessor_type)
        if not isinstance(type_num, int):
            logger.warning(f"Unrecognized accessor type: {accessor_type}")
            continue
        buffer_view_index = accessor_dict.get("bufferView")
        if not isinstance(buffer_view_index, int):
            logger.warning(
                f"accessors[{accessor_index}] doesn't have bufferView that is not implemented yet"
            )
            decoded_binary.append([])
            continue
        buffer_view_dict = buffer_view_dicts[buffer_view_index]
        if not isinstance(buffer_view_dict, dict):
            continue
        buffer_view_byte_offset = buffer_view_dict.get("byteOffset")
        if not isinstance(buffer_view_byte_offset, int):
            buffer_view_byte_offset = 0
        br.set_pos(buffer_view_byte_offset)
        data_list: List[Union[int, float, List[int], List[float]]] = []
        accessor_count = accessor_dict.get("count")
        if not isinstance(accessor_count, int):
            accessor_count = 0
        component_type = accessor_dict.get("componentType")
        if not isinstance(component_type, int):
            raise ValueError(f"Unsupported component type: {component_type}")
        for _ in range(accessor_count):
            if type_num == 1:
                single_data = br.read_as_data_type(component_type)
                data_list.append(single_data)
            else:
                multiple_data = []
                for _ in range(type_num):
                    multiple_data.append(br.read_as_data_type(component_type))
                data_list.append(multiple_data)
        decoded_binary.append(data_list)

    return decoded_binary


@dataclass
class VrmParser:
    filepath: Path
    extract_textures_into_folder: bool
    make_new_texture_folder: bool
    license_validation: bool
    legacy_importer: bool
    decoded_binary: List[List[Union[int, float, List[int], List[float]]]] = field(
        init=False, default_factory=list
    )
    json_dict: Dict[str, Json] = field(init=False, default_factory=dict)

    def parse(self) -> ParseResult:
        # bin chunkは一つだけであることを期待
        json_dict, body_binary = parse_glb(self.filepath.read_bytes())
        self.json_dict = json_dict

        if (
            self.legacy_importer
            and self.json_dict.get("extensionsRequired")
            and isinstance(self.json_dict["extensionsRequired"], list)
            and "KHR_draco_mesh_compression" in self.json_dict["extensionsRequired"]
        ):
            raise ValueError(
                pgettext("This VRM uses Draco compression. Unable to decompress.")
            )

        if self.license_validation:
            validate_license(self.json_dict)

        parse_result = ParseResult(filepath=self.filepath, json_dict=self.json_dict)
        self.vrm_extension_read(parse_result)
        if self.legacy_importer:
            self.texture_rip(parse_result, body_binary)
            self.decoded_binary = decode_bin(self.json_dict, body_binary)
            self.mesh_read(parse_result)
            self.material_read(parse_result)
            self.skin_read(parse_result)
            self.node_read(parse_result)
        else:
            self.material_read(parse_result)

        return parse_result

    def vrm_extension_read(self, parse_result: ParseResult) -> None:
        vrm1_dict = deep.get(self.json_dict, ["extensions", "VRMC_vrm"])
        if isinstance(vrm1_dict, dict):
            self.vrm1_extension_read(parse_result, vrm1_dict)
            return

        vrm0_dict = deep.get(self.json_dict, ["extensions", "VRM"])
        if isinstance(vrm0_dict, dict):
            self.vrm0_extension_read(parse_result, vrm0_dict)

    def vrm0_extension_read(
        self, parse_result: ParseResult, vrm0_dict: Dict[str, Json]
    ) -> None:
        spec_version = vrm0_dict.get("specVersion")
        if isinstance(spec_version, str):
            parse_result.spec_version_str = spec_version
        parse_result.vrm0_extension = vrm0_dict

        human_bones = deep.get(vrm0_dict, ["humanoid", "humanBones"], [])
        if not isinstance(human_bones, list):
            raise ValueError("No human bones")

        hips_node_index: Optional[int] = None
        for human_bone in human_bones:
            if isinstance(human_bone, dict) and human_bone.get("bone") == "hips":
                index = human_bone.get("node")
                if isinstance(index, int):
                    hips_node_index = index

        if not isinstance(hips_node_index, int):
            logger.warning("No hips bone index found")
            return

        parse_result.hips_node_index = hips_node_index

    def vrm1_extension_read(
        self, parse_result: ParseResult, vrm1_dict: Dict[str, Json]
    ) -> None:
        parse_result.vrm1_extension = vrm1_dict
        parse_result.spec_version_number = (1, 0)
        parse_result.spec_version_is_stable = False

        hips_node_index = deep.get(
            vrm1_dict, ["humanoid", "humanBones", "hips", "node"]
        )
        if not isinstance(hips_node_index, int):
            logger.warning("No hips bone index found")
            return
        parse_result.hips_node_index = hips_node_index

    def texture_rip(
        self,
        parse_result: ParseResult,
        body_binary: bytes,
    ) -> None:
        buffer_views = self.json_dict.get("bufferViews")
        if not isinstance(buffer_views, list):
            return

        binary_reader = BinaryReader(body_binary)
        if "images" not in self.json_dict:
            return

        if self.extract_textures_into_folder:
            dir_path = self.filepath.with_suffix(".vrm.textures").absolute()
            if self.make_new_texture_folder:
                dir_path = create_unique_indexed_directory_path(dir_path)
            dir_path.mkdir(parents=True, exist_ok=True)
        else:
            dir_path = Path(tempfile.mkdtemp())  # TODO: cleanup

        image_dicts = self.json_dict.get("images")
        if not isinstance(image_dicts, list):
            image_dicts = []
        for image_index, image_dict in enumerate(image_dicts):
            if not isinstance(image_dict, dict):
                continue
            if "extra" in image_dict:
                image_name = deep.get(image_dict, ["extra", "name"])
            else:
                image_name = image_dict.get("name")

            buffer_view_index = image_dict.get("bufferView")
            if not isinstance(
                buffer_view_index, int
            ) or not 0 <= buffer_view_index < len(buffer_views):
                continue

            buffer_view_dict = buffer_views[buffer_view_index]
            if not isinstance(buffer_view_dict, dict):
                continue

            byte_offset = buffer_view_dict.get("byteOffset")
            if isinstance(byte_offset, int) and byte_offset >= 0:
                binary_reader.set_pos(byte_offset)

            byte_length = buffer_view_dict.get("byteLength")
            if not isinstance(byte_length, int) or byte_length <= 0:
                continue

            image_binary = binary_reader.read_binary(byte_length)

            mime_type = image_dict.get("mimeType")
            if not isinstance(mime_type, str):
                continue

            image_type = mime_type.split("/")[-1]
            if not image_name or not isinstance(image_name, str):
                image_name = "texture_" + str(image_index)
                logger.warning(f"No name image is named {image_name}")
            elif len(image_name) >= 50:
                new_image_name = "tex_2longname_" + str(image_index)
                logger.warning(
                    f"Too long name image: {image_name} is named {new_image_name}"
                )
                image_name = new_image_name

            image_name = remove_unsafe_path_chars(image_name)
            if not image_name:
                image_name = "_"
            image_path = dir_path / image_name
            if image_path.suffix.lower() != ("." + image_type).lower():
                image_path = image_path.with_name(image_path.name + "." + image_type)
            if not image_path.exists():  # すでに同名の画像がある場合は基本上書きしない
                image_path.write_bytes(image_binary)
            elif image_name in [
                img.name for img in parse_result.image_properties
            ]:  # ただ、それがこのVRMを開いた時の名前の時はちょっと考えて書いてみる。
                image_path = create_unique_indexed_file_path(image_path, image_binary)
            else:
                logger.warning(
                    image_name + " Image already exists. Was not overwritten."
                )
            image_property = ImageProperties(image_name, image_path, image_type)
            parse_result.image_properties.append(image_property)

    def mesh_read(self, parse_result: ParseResult) -> None:
        # メッシュをパースする
        mesh_dicts = self.json_dict.get("meshes")
        if not isinstance(mesh_dicts, list):
            return
        for n, mesh_dict in enumerate(mesh_dicts):
            if not isinstance(mesh_dict, dict):
                continue
            primitive_dicts = mesh_dict.get("primitives")
            if not isinstance(primitive_dicts, list):
                primitive_dicts = []
            primitives = []
            for j, primitive_dict in enumerate(primitive_dicts):
                if not isinstance(primitive_dict, dict):
                    primitive_dict = {}
                vrm_mesh = PyMesh(object_id=n)

                mesh_name = mesh_dict.get("name")
                if not isinstance(mesh_name, str):
                    mesh_name = ""
                if j == 0:  # mesh annotationとの兼ね合い
                    vrm_mesh.name = mesh_name
                else:
                    vrm_mesh.name = mesh_name + str(j)

                vrm_mesh.has_FB_ngon_encoding = isinstance(
                    deep.get(mesh_dict, ["extensions", "FB_ngon_encoding"]), dict
                )

                # 頂点index
                if primitive_dict.get("mode", 4) != GL_TRIANGLES:
                    # TODO その他メッシュタイプ対応
                    primitive_mode = primitive_dict.get("mode")
                    raise ValueError(f"Unsupported polygon type(:{primitive_mode})")
                indices = primitive_dict.get("indices")
                if isinstance(indices, int) and 0 <= indices < len(self.decoded_binary):
                    scalar_face_indices = self.decoded_binary[indices]
                    while len(scalar_face_indices) % 3 != 0:
                        logger.warning(
                            f"meshes[{n}]primitives[{j}] length is not a multiple of 3"
                        )
                        scalar_face_indices.append(0)

                    # 3要素ずつに変換しておく(GlConstants.TRIANGLES前提なので)
                    vrm_mesh.face_indices = [
                        scalar_face_indices[slice(x, x + 3)]  # type: ignore[misc]
                        for x in range(0, len(scalar_face_indices), 3)
                    ]

                # ここから頂点属性
                vertex_attributes = primitive_dict.get("attributes")
                if not isinstance(vertex_attributes, dict):
                    vertex_attributes = {}
                # 頂点属性は実装によっては存在しない属性(例えばJOINTSやWEIGHTSがなかったりもする)もあるし、UVや頂点カラー0->Nで増やせる(スキニングは1要素(ボーン4本)限定
                for attr_key, attr_value in vertex_attributes.items():
                    if not isinstance(attr_value, int) or not 0 <= attr_value < len(
                        self.decoded_binary
                    ):
                        continue
                    setattr(vrm_mesh, attr_key, self.decoded_binary[attr_value])

                # TEXCOORD_FIX [ 古いUniVRM誤り: uv.y = -uv.y ->修復 uv.y = 1 - ( -uv.y ) => uv.y=1+uv.y]
                legacy_uv_flag = False  # f***
                gen = str(deep.get(self.json_dict, ["assets", "generator"], ""))
                if re.match("UniGLTF", gen):
                    with contextlib.suppress(ValueError):
                        if float("".join(gen[-4:])) < 1.16:
                            legacy_uv_flag = True

                uv_count = 0
                while True:
                    texcoord_name = f"TEXCOORD_{uv_count}"
                    if hasattr(vrm_mesh, texcoord_name):
                        texcoord = getattr(vrm_mesh, texcoord_name)
                        if legacy_uv_flag:
                            for uv in texcoord:
                                uv[1] = 1 + uv[1]
                        uv_count += 1
                    else:
                        break
                # blenderとは上下反対のuv,それはblenderに書き込むときに直す

                # meshに当てられるマテリアルの場所を記録
                material_index = primitive_dict.get("material")
                if isinstance(material_index, int):
                    vrm_mesh.material_index = material_index

                # 変換時のキャッシュ対応のためのデータ
                attributes_dict = primitive_dict.get("attributes")
                if isinstance(attributes_dict, dict):
                    position_index = attributes_dict.get("POSITION")
                    if isinstance(position_index, int):
                        vrm_mesh.POSITION_accessor = position_index

                # ここからモーフターゲット vrmのtargetは相対位置 normalは無視する
                if "targets" in primitive_dict:
                    morph_target_point_list_and_accessor_index_dict = {}
                    morph_target_dicts = primitive_dict.get("targets")
                    if not isinstance(morph_target_dicts, list):
                        morph_target_dicts = []
                    for i, morph_target_dict in enumerate(morph_target_dicts):
                        if not isinstance(morph_target_dict, dict):
                            continue
                        position_index = morph_target_dict.get("POSITION")
                        if not isinstance(
                            position_index, int
                        ) or not 0 <= position_index < len(self.decoded_binary):
                            continue
                        pos_array = self.decoded_binary[position_index]
                        if "extra" in morph_target_dict:  # for old AliciaSolid
                            # accessorのindexを持つのは変換時のキャッシュ対応のため
                            morph_name = str(
                                deep.get(
                                    primitive_dict, ["targets", i, "extra", "name"]
                                )
                            )
                        else:
                            morph_name = str(
                                deep.get(primitive_dict, ["extras", "targetNames", i])
                            )
                            # 同上
                        morph_target_point_list_and_accessor_index_dict[morph_name] = [
                            pos_array,
                            deep.get(primitive_dict, ["targets", i, "POSITION"]),
                        ]

                    temp = morph_target_point_list_and_accessor_index_dict
                    vrm_mesh.morph_target_point_list_and_accessor_index_dict = temp  # type: ignore[assignment]
                primitives.append(vrm_mesh)
            parse_result.meshes.append(primitives)

    # ここからマテリアル
    def material_read(self, parse_result: ParseResult) -> None:
        material_dicts = self.json_dict.get("materials")
        if not isinstance(material_dicts, list):
            return
        for index in range(len(material_dicts)):
            parse_result.vrm0_material_properties.append(
                Vrm0MaterialProperty.create(
                    deep.get(
                        self.json_dict,
                        ["extensions", "VRM", "materialProperties", index],
                    )
                )
            )

    # skinをパース ->バイナリの中身はskinning実装の横着用
    # skinのjointsの(nodesの)indexをvertsのjoints_0は指定してる
    # inverseBindMatrices: 単にスキニングするときの逆行列。読み込み不要なのでしない(自前計算もできる、めんどいけど)
    # ついでに[i][3]ではなく、[3][i]にマイナスx,y,zが入っている。 ここで詰まった。(出力時に)
    # joints:JOINTS_0の指定node番号のindex
    def skin_read(self, parse_result: ParseResult) -> None:
        skin_dicts = self.json_dict.get("skins")
        if not isinstance(skin_dicts, list):
            return
        for skin_dict in skin_dicts:
            if not isinstance(skin_dict, dict):
                continue
            joints = skin_dict.get("joints")
            if not isinstance(joints, list):
                joints = []
            parse_result.skins_joints_list.append(
                [joint for joint in joints if isinstance(joint, int)]
            )
            skeleton = skin_dict.get("skeleton")
            if isinstance(skeleton, int):
                parse_result.skins_root_node_list.append(skeleton)

        # node(ボーン)をパースする->親からの相対位置で記録されている

    def node_read(self, parse_result: ParseResult) -> None:
        node_dicts = self.json_dict.get("nodes")
        if not isinstance(node_dicts, list):
            return
        for i, node_dict in enumerate(node_dicts):
            if not isinstance(node_dict, dict):
                continue
            parse_result.nodes_dict[i] = create_py_bone(node_dict)
            # TODO こっからorigin_bone
            mesh_index = node_dict.get("mesh")
            if isinstance(mesh_index, int):
                parse_result.origin_nodes_dict[i] = (
                    parse_result.nodes_dict[i],
                    mesh_index,
                )
                skin_index = node_dict.get("skin")
                if isinstance(skin_index, int):
                    parse_result.origin_nodes_dict[i] = (
                        parse_result.nodes_dict[i],
                        mesh_index,
                        skin_index,
                    )
                else:
                    logger.warning(f"{node_dict.get('name')} is not have skin")


if __name__ == "__main__":
    VrmParser(
        Path(sys.argv[1]),
        extract_textures_into_folder=True,
        make_new_texture_folder=True,
        license_validation=True,
        legacy_importer=True,
    ).parse()
