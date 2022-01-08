"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import contextlib
import os
import re
import sys
import tempfile
from collections import OrderedDict
from dataclasses import dataclass, field
from itertools import repeat
from typing import Any, Dict, List, Optional, Sequence, Tuple

import bgl
import bpy

from ..common import deep
from ..common.binary_reader import BinaryReader
from ..common.gltf import parse_glb
from ..common.mtoon_constants import MaterialMtoon, MaterialTransparentZWrite
from .license_validation import validate_license


@dataclass
class PyMesh:
    object_id: int
    name: str = ""
    face_indices: List[List[int]] = field(default_factory=list)
    skin_id: Optional[int] = None
    material_index: Optional[int] = None
    POSITION_accessor: Optional[int] = None
    POSITION: Optional[List[List[float]]] = None
    JOINTS_0: Optional[List[List[int]]] = None
    WEIGHTS_0: Optional[List[List[float]]] = None
    NORMAL: Optional[List[List[float]]] = None
    vert_normal_normalized: Optional[bool] = None
    morph_target_point_list_and_accessor_index_dict: Optional[
        Dict[str, List[Any]]
    ] = None


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


@dataclass
class PyMaterial:
    name: str = ""
    shader_name: str = ""


class PyMaterialGltf(PyMaterial):
    def __init__(self) -> None:
        super().__init__()

        self.base_color: List[float] = [1, 1, 1, 1]
        self.metallic_factor: float = 1
        self.roughness_factor: float = 1
        self.emissive_factor: List[float] = [0, 0, 0]

        self.color_texture_index: Optional[int] = None
        self.color_texcoord_index: Optional[int] = None
        self.metallic_roughness_texture_index: Optional[int] = None
        self.metallic_roughness_texture_texcoord: Optional[int] = None
        self.normal_texture_index: Optional[int] = None
        self.normal_texture_texcoord_index: Optional[int] = None
        self.emissive_texture_index: Optional[int] = None
        self.emissive_texture_texcoord_index: Optional[int] = None
        self.occlusion_texture_index: Optional[int] = None
        self.occlusion_texture_texcoord_index: Optional[int] = None
        self.alphaCutoff: Optional[float] = None

        self.double_sided = False
        self.alpha_mode = "OPAQUE"
        self.shadeless = 0  # 0 is shade ,1 is shadeless

        self.vrm_addon_for_blender_legacy_gltf_material = False


class PyMaterialTransparentZWrite(PyMaterial):
    def __init__(self) -> None:
        super().__init__()
        self.float_props_dic: Dict[str, Optional[float]] = {
            prop: None for prop in MaterialTransparentZWrite.float_props
        }
        self.vector_props_dic: Dict[str, Optional[List[float]]] = {
            prop: None for prop in MaterialTransparentZWrite.vector_props
        }
        self.texture_index_dic: Dict[str, Optional[int]] = {
            tex: None for tex in MaterialTransparentZWrite.texture_index_list
        }


class PyMaterialMtoon(PyMaterial):
    def __init__(self) -> None:
        super().__init__()
        self.float_props_dic: Dict[str, Optional[float]] = {
            prop: None for prop in MaterialMtoon.float_props_exchange_dic
        }
        self.vector_props_dic: Dict[str, Optional[Sequence[float]]] = {
            prop: None for prop in MaterialMtoon.vector_props_exchange_dic
        }
        self.texture_index_dic: Dict[str, Optional[int]] = {
            prop: None for prop in MaterialMtoon.texture_kind_exchange_dic
        }
        self.keyword_dic: Dict[str, bool] = {
            kw: False for kw in MaterialMtoon.keyword_list
        }
        self.tag_dic: Dict[str, Optional[str]] = {
            tag: None for tag in MaterialMtoon.tagmap_list
        }


@dataclass
class ImageProperties:
    name: str
    filepath: str
    filetype: str


@dataclass
class ParseResult:
    filepath: str
    json_dict: Dict[str, Any] = field(default_factory=dict)
    spec_version_number: Tuple[int, int] = (0, 0)
    spec_version_str: str = "0.0"
    spec_version_is_stable: bool = True
    vrm0_extension: Dict[str, Any] = field(init=False, default_factory=dict)
    vrm1_extension: Dict[str, Any] = field(init=False, default_factory=dict)
    hips_node_index: int = 0
    image_properties: List[ImageProperties] = field(init=False, default_factory=list)
    meshes: List[List[PyMesh]] = field(init=False, default_factory=list)
    materials: List[PyMaterial] = field(init=False, default_factory=list)
    nodes_dict: Dict[int, PyNode] = field(init=False, default_factory=dict)
    origin_nodes_dict: Dict[int, List[Any]] = field(init=False, default_factory=dict)
    skins_joints_list: List[List[int]] = field(init=False, default_factory=list)
    skins_root_node_list: List[int] = field(init=False, default_factory=list)


def create_py_bone(node: Dict[str, Any]) -> PyNode:
    v_node = PyNode(
        name=node.get("name", "tmp"),
        position=node.get("translation", [0, 0, 0]),
        rotation=node.get("rotation", (0, 0, 0, 1)),
        scale=node.get("scale", (1, 1, 1)),
    )
    if "children" in node:
        children = node["children"]
        if isinstance(children, int):
            v_node.children = [children]
        else:
            v_node.children = children
    else:
        v_node.children = None
    if "mesh" in node:
        v_node.mesh_id = node["mesh"]
    if "skin" in node:
        v_node.skin_id = node["skin"]
    return v_node


def create_py_material(
    mat: Dict[str, Any], ext_mat: Dict[str, Any]
) -> Optional[PyMaterial]:
    shader = ext_mat.get("shader")

    # standard, or VRM unsupported shader(no saved)
    if shader not in ["VRM/MToon", "VRM/UnlitTransparentZWrite"]:
        gltf = PyMaterialGltf()
        gltf.name = mat.get("name", "")
        gltf.shader_name = "gltf"
        if "pbrMetallicRoughness" in mat:
            pbrmat = mat["pbrMetallicRoughness"]
            if "baseColorTexture" in pbrmat and isinstance(
                pbrmat["baseColorTexture"], dict
            ):
                texture_index = pbrmat["baseColorTexture"].get("index")
                gltf.color_texture_index = texture_index
                gltf.color_texcoord_index = pbrmat["baseColorTexture"].get("texCoord")
            if "baseColorFactor" in pbrmat:
                gltf.base_color = pbrmat["baseColorFactor"]
            if "metallicFactor" in pbrmat:
                gltf.metallic_factor = pbrmat["metallicFactor"]
            if "roughnessFactor" in pbrmat:
                gltf.roughness_factor = pbrmat["roughnessFactor"]
            if "metallicRoughnessTexture" in pbrmat and isinstance(
                pbrmat["metallicRoughnessTexture"], dict
            ):
                texture_index = pbrmat["metallicRoughnessTexture"].get("index")
                gltf.metallic_roughness_texture_index = texture_index
                gltf.metallic_roughness_texture_texcoord = pbrmat[
                    "metallicRoughnessTexture"
                ].get("texCoord")

        if "normalTexture" in mat and isinstance(mat["normalTexture"], dict):
            gltf.normal_texture_index = mat["normalTexture"].get("index")
            gltf.normal_texture_texcoord_index = mat["normalTexture"].get("texCoord")
        if "emissiveTexture" in mat and isinstance(mat["emissiveTexture"], dict):
            gltf.emissive_texture_index = mat["emissiveTexture"].get("index")
            gltf.emissive_texture_texcoord_index = mat["emissiveTexture"].get(
                "texCoord"
            )
        if "occlusionTexture" in mat and isinstance(mat["occlusionTexture"], dict):
            gltf.occlusion_texture_index = mat["occlusionTexture"].get("index")
            gltf.occlusion_texture_texcoord_index = mat["occlusionTexture"].get(
                "texCoord"
            )
        if "emissiveFactor" in mat:
            gltf.emissive_factor = mat["emissiveFactor"]

        if "doubleSided" in mat:
            gltf.double_sided = mat["doubleSided"]
        if "alphaMode" in mat:
            if mat["alphaMode"] == "MASK":
                gltf.alpha_mode = "MASK"
                if mat.get("alphaCutoff"):
                    gltf.alphaCutoff = mat.get("alphaCutoff")
                else:
                    gltf.alphaCutoff = 0.5
            elif mat["alphaMode"] == "BLEND":
                gltf.alpha_mode = "Z_TRANSPARENCY"
            elif mat["alphaMode"] == "OPAQUE":
                gltf.alpha_mode = "OPAQUE"
        if "extensions" in mat and "KHR_materials_unlit" in mat["extensions"]:
            gltf.shadeless = 1  # 0 is shade ,1 is shadeless

        if isinstance(ext_mat.get("extras"), dict) and isinstance(
            ext_mat["extras"].get("VRM_Addon_for_Blender_legacy_gltf_material"), dict
        ):
            gltf.vrm_addon_for_blender_legacy_gltf_material = True
        return gltf

    # "MToon or Transparent_Zwrite"
    if shader == "VRM/MToon":
        mtoon = PyMaterialMtoon()
        mtoon.name = ext_mat.get("name", "")
        mtoon.shader_name = ext_mat.get("shader", "")
        # region check unknown props exist
        subset = {
            "float": ext_mat.get("floatProperties", {}).keys()
            - mtoon.float_props_dic.keys(),
            "vector": ext_mat.get("vectorProperties", {}).keys()
            - mtoon.vector_props_dic.keys(),
            "texture": ext_mat.get("textureProperties", {}).keys()
            - mtoon.texture_index_dic.keys(),
            "keyword": ext_mat.get("keywordMap", {}).keys() - mtoon.keyword_dic.keys(),
        }
        for k, _subset in subset.items():
            if _subset:
                ext_mat_name = ext_mat.get("name")
                print(f"unknown {k} properties {_subset} in {ext_mat_name}")
        # endregion check unknown props exit

        mtoon.float_props_dic.update(ext_mat.get("floatProperties", {}))
        mtoon.vector_props_dic.update(ext_mat.get("vectorProperties", {}))
        mtoon.texture_index_dic.update(ext_mat.get("textureProperties", {}))
        mtoon.keyword_dic.update(ext_mat.get("keywordMap", {}))
        mtoon.tag_dic.update(ext_mat.get("tagMap", {}))
        return mtoon

    if shader == "VRM/UnlitTransparentZWrite":
        transparent_z_write = PyMaterialTransparentZWrite()
        transparent_z_write.name = ext_mat.get("name", "")
        transparent_z_write.shader_name = ext_mat.get("shader", "")
        transparent_z_write.float_props_dic = ext_mat.get("floatProperties", {})
        transparent_z_write.vector_props_dic = ext_mat.get("vectorProperties", {})
        transparent_z_write.texture_index_dic = ext_mat.get("textureProperties", {})
        return transparent_z_write

    # ここには入らないはず
    print(
        f"Unknown(or legacy) shader :material {ext_mat['name']} is {ext_mat['shader']}"
    )
    return None


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
        "".join([chr(charnum) for charnum in unsafe_chars]),
        "".join(repeat("_", len(unsafe_chars))),
    )
    safe_filename = filename.translate(remove_table)
    return safe_filename


#  "accessorの順に" データを読み込んでリストにしたものを返す
def decode_bin(json_dict: Dict[str, Any], binary: bytes) -> List[Any]:
    br = BinaryReader(binary)
    # This list indexed by accessor index
    decoded_binary: List[Any] = []
    buffer_views = json_dict["bufferViews"]
    accessors = json_dict["accessors"]
    type_num_dict = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
    for accessor_index, accessor in enumerate(accessors):
        type_num = type_num_dict[accessor["type"]]
        if "bufferView" not in accessor:
            print(
                f"WARNING: accessors[{accessor_index}] doesn't have bufferView that is not implemented yet"
            )
            decoded_binary.append([])
            continue
        br.set_pos(buffer_views[accessor["bufferView"]]["byteOffset"])
        data_list = []
        for _ in range(accessor["count"]):
            if type_num == 1:
                data = br.read_as_data_type(accessor["componentType"])
            else:
                data = []  # type: ignore[assignment]
                for _ in range(type_num):
                    data.append(br.read_as_data_type(accessor["componentType"]))  # type: ignore[union-attr]
            data_list.append(data)
        decoded_binary.append(data_list)

    return decoded_binary


@dataclass
class VrmParser:
    filepath: str
    extract_textures_into_folder: bool
    make_new_texture_folder: bool
    license_validation: bool
    legacy_importer: bool
    decoded_binary: List[Any] = field(init=False, default_factory=list)
    json_dict: Dict[str, Any] = field(init=False, default_factory=dict)

    def parse(self) -> ParseResult:
        # datachunkは普通一つしかない
        with open(self.filepath, "rb") as f:
            json_dict, body_binary = parse_glb(f.read())
            self.json_dict = json_dict

        if (
            self.legacy_importer
            and "extensionsRequired" in self.json_dict
            and "KHR_DRACO_MESH_COMPRESSION" in self.json_dict["extensionsRequired"]
        ):
            raise Exception(
                "This VRM uses Draco compression. Unable to decompress. Draco圧縮されたVRMは未対応です"
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
            return

        raise Exception("No VRM extension found")

    def vrm0_extension_read(
        self, parse_result: ParseResult, vrm0_dict: Dict[str, Any]
    ) -> None:
        spec_version = vrm0_dict.get("specVersion")
        if isinstance(spec_version, str):
            parse_result.spec_version_str = spec_version
        parse_result.vrm0_extension = vrm0_dict

        human_bones = deep.get(vrm0_dict, ["humanoid", "humanBones"], [])
        if not isinstance(human_bones, list):
            raise Exception()

        hips_node_index: Optional[int] = None
        for human_bone in human_bones:
            if (
                isinstance(human_bone, dict)
                and human_bone.get("bone") == "hips"
                and isinstance(human_bone.get("node"), int)
            ):
                hips_node_index = human_bone["node"]

        if not isinstance(hips_node_index, int):
            raise Exception("No hips bone index found")

        parse_result.hips_node_index = hips_node_index

    def vrm1_extension_read(
        self, parse_result: ParseResult, vrm1_dict: Dict[str, Any]
    ) -> None:
        parse_result.vrm1_extension = vrm1_dict
        parse_result.spec_version_number = (1, 0)
        parse_result.spec_version_is_stable = False

        hips_node_index = deep.get(
            vrm1_dict, ["humanoid", "humanBones", "hips", "node"]
        )
        if not isinstance(hips_node_index, int):
            raise Exception("No hips bone index found")
        parse_result.hips_node_index = hips_node_index

    def texture_rip(
        self,
        parse_result: ParseResult,
        body_binary: bytes,
    ) -> None:
        buffer_views = self.json_dict["bufferViews"]
        binary_reader = BinaryReader(body_binary)
        if "images" not in self.json_dict:
            return

        if self.extract_textures_into_folder:
            dir_path = os.path.abspath(self.filepath) + ".textures"
            if self.make_new_texture_folder:
                for i in range(100001):
                    checking_dir_path = dir_path if i == 0 else f"{dir_path}.{i}"
                    if not os.path.exists(checking_dir_path):
                        os.mkdir(checking_dir_path)
                        dir_path = checking_dir_path
                        break
        else:
            dir_path = tempfile.mkdtemp()  # TODO: cleanup

        for image_id, image_prop in enumerate(self.json_dict["images"]):
            if "extra" in image_prop:
                image_name = image_prop["extra"]["name"]
            else:
                image_name = image_prop["name"]
            binary_reader.set_pos(buffer_views[image_prop["bufferView"]]["byteOffset"])
            image_binary = binary_reader.read_binary(
                buffer_views[image_prop["bufferView"]]["byteLength"]
            )
            image_type = image_prop["mimeType"].split("/")[-1]
            if image_name == "":
                image_name = "texture_" + str(image_id)
                print(f"no name image is named {image_name}")
            elif len(image_name) >= 50:
                new_image_name = "tex_2longname_" + str(image_id)
                print(f"too long name image: {image_name} is named {new_image_name}")
                image_name = new_image_name

            image_name = remove_unsafe_path_chars(image_name)
            image_path = os.path.join(dir_path, image_name)
            if os.path.splitext(image_name)[1].lower() != ("." + image_type).lower():
                image_path += "." + image_type
            if not os.path.exists(image_path):  # すでに同名の画像がある場合は基本上書きしない
                with open(image_path, "wb") as image_writer:
                    image_writer.write(image_binary)
            elif image_name in [
                img.name for img in parse_result.image_properties
            ]:  # ただ、それがこのVRMを開いた時の名前の時はちょっと考えて書いてみる。
                written_flag = False
                for i in range(100000):
                    second_image_name = image_name + "_" + str(i)
                    image_path = os.path.join(
                        dir_path, second_image_name + "." + image_type
                    )
                    if not os.path.exists(image_path):
                        with open(image_path, "wb") as image_writer:
                            image_writer.write(image_binary)
                        image_name = second_image_name
                        written_flag = True
                        break
                if not written_flag:
                    print(
                        "There are more than 100000 images with the same name in the folder."
                        + f" Failed to write file: {image_name}"
                    )
            else:
                print(image_name + " Image already exists. Was not overwritten.")
            image_property = ImageProperties(image_name, image_path, image_type)
            parse_result.image_properties.append(image_property)

    def mesh_read(self, parse_result: ParseResult) -> None:
        # メッシュをパースする
        for n, mesh in enumerate(self.json_dict.get("meshes", [])):
            primitives = []
            for j, primitive in enumerate(mesh.get("primitives", [])):
                vrm_mesh = PyMesh(object_id=n)
                if j == 0:  # mesh annotationとの兼ね合い
                    vrm_mesh.name = mesh["name"]
                else:
                    vrm_mesh.name = mesh["name"] + str(j)

                # region 頂点index
                if primitive.get("mode", 4) != bgl.GL_TRIANGLES:
                    # TODO その他メッシュタイプ対応
                    primitive_mode = primitive.get("mode")
                    raise Exception(
                        f"Unsupported polygon type(:{primitive_mode}) Exception"
                    )
                scalar_face_indices = self.decoded_binary[primitive["indices"]]
                while len(scalar_face_indices) % 3 != 0:
                    print(f"meshes[{n}]primitives[{j}] length is not a multiple of 3")
                    scalar_face_indices.append(0)

                # 3要素ずつに変換しておく(GlConstants.TRIANGLES前提なので)
                vrm_mesh.face_indices = [
                    scalar_face_indices[x : x + 3]
                    for x in range(0, len(scalar_face_indices), 3)
                ]

                # endregion 頂点index

                # ここから頂点属性
                vertex_attributes = primitive.get("attributes", {})
                # 頂点属性は実装によっては存在しない属性(例えばJOINTSやWEIGHTSがなかったりもする)もあるし、UVや頂点カラー0->Nで増やせる(スキニングは1要素(ボーン4本)限定
                for attr in vertex_attributes.keys():
                    vrm_mesh.__setattr__(
                        attr, self.decoded_binary[vertex_attributes[attr]]
                    )

                # region TEXCOORD_FIX [ 古いUniVRM誤り: uv.y = -uv.y ->修復 uv.y = 1 - ( -uv.y ) => uv.y=1+uv.y]
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
                # endregion TEXCOORD_FIX

                # meshに当てられるマテリアルの場所を記録
                vrm_mesh.material_index = primitive["material"]

                # 変換時のキャッシュ対応のためのデータ
                vrm_mesh.POSITION_accessor = primitive.get("attributes", {}).get(
                    "POSITION"
                )

                # ここからモーフターゲット vrmのtargetは相対位置 normalは無視する
                if "targets" in primitive:
                    morph_target_point_list_and_accessor_index_dict = OrderedDict()
                    for i, morph_target in enumerate(primitive["targets"]):
                        pos_array = self.decoded_binary[morph_target["POSITION"]]
                        if "extra" in morph_target:  # for old AliciaSolid
                            # accessorのindexを持つのは変換時のキャッシュ対応のため
                            morph_name = str(primitive["targets"][i]["extra"]["name"])
                        else:
                            morph_name = str(primitive["extras"]["targetNames"][i])
                            # 同上
                        morph_target_point_list_and_accessor_index_dict[morph_name] = [
                            pos_array,
                            primitive["targets"][i]["POSITION"],
                        ]
                    vrm_mesh.morph_target_point_list_and_accessor_index_dict = (
                        morph_target_point_list_and_accessor_index_dict
                    )
                primitives.append(vrm_mesh)
            parse_result.meshes.append(primitives)

    # ここからマテリアル
    def material_read(self, parse_result: ParseResult) -> None:
        json_materials = self.json_dict.get("materials", [])
        vrm_extension_material_properties = deep.get(
            self.json_dict,
            ["extensions", "VRM", "materialProperties"],
            default=[{"shader": "VRM_USE_GLTFSHADER"}] * len(json_materials),
        )
        if not isinstance(vrm_extension_material_properties, list):
            return

        for mat, ext_mat in zip(json_materials, vrm_extension_material_properties):
            material = create_py_material(mat, ext_mat)
            if material is not None:
                parse_result.materials.append(material)

        # skinをパース ->バイナリの中身はskinning実装の横着用
        # skinのjointsの(nodesの)indexをvertsのjoints_0は指定してる
        # inverseBindMatrices: 単にスキニングするときの逆行列。読み込み不要なのでしない(自前計算もできる、めんどいけど)
        # ついでに[i][3]ではなく、[3][i]にマイナスx,y,zが入っている。 ここで詰まった。(出力時に)
        # joints:JOINTS_0の指定node番号のindex

    def skin_read(self, parse_result: ParseResult) -> None:
        for skin in self.json_dict.get("skins", []):
            parse_result.skins_joints_list.append(skin["joints"])
            if "skeleton" in skin:
                parse_result.skins_root_node_list.append(skin["skeleton"])

        # node(ボーン)をパースする->親からの相対位置で記録されている

    def node_read(self, parse_result: ParseResult) -> None:
        for i, node in enumerate(self.json_dict["nodes"]):
            parse_result.nodes_dict[i] = create_py_bone(node)
            # TODO こっからorigin_bone
            if "mesh" in node:
                parse_result.origin_nodes_dict[i] = [
                    parse_result.nodes_dict[i],
                    node["mesh"],
                ]
                if "skin" in node:
                    parse_result.origin_nodes_dict[i].append(node["skin"])
                else:
                    print(node["name"] + "is not have skin")


if __name__ == "__main__":
    VrmParser(
        sys.argv[1],
        extract_textures_into_folder=True,
        make_new_texture_folder=True,
        license_validation=True,
        legacy_importer=True,
    ).parse()
