"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

# coding :utf-8
# for python 3.5 - for blender 2.79
import contextlib
import datetime
import json
import os
import re
import sys
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import ParseResult, parse_qsl, urlparse

import numpy

from .. import vrm_types
from ..gl_constants import GlConstants
from ..misc import vrm_helper
from ..vrm_types import nested_json_value_getter as json_get
from . import vrm2pydata_factory
from .binary_reader import BinaryReader


class LicenseConfirmationRequiredProp:
    def __init__(
        self,
        url: Optional[str],
        json_key: Optional[str],
        message_en: str,
        message_ja: str,
    ):
        self.url = url
        self.json_key = json_key
        self.message = vrm_helper.lang_support(message_en, message_ja)

    def description(self) -> str:
        return f"""class=LicenseConfirmationRequired
url={self.url}
json_key={self.json_key}
message={self.message}
"""


class LicenseConfirmationRequired(Exception):
    def __init__(self, props: List[LicenseConfirmationRequiredProp]):
        self.props = props
        super().__init__(self.description())

    def description(self) -> str:
        return "\n".join([prop.description() for prop in self.props])

    def license_confirmations(self) -> List[Dict[str, str]]:
        return [
            {
                "name": "LicenseConfirmation" + str(index),
                "url": prop.url or "",
                "json_key": prop.json_key or "",
                "message": prop.message or "",
            }
            for index, prop in enumerate(self.props)
        ]


def parse_glb(data: bytes) -> Tuple[Any, bytes]:
    reader = BinaryReader(data)
    magic = reader.read_str(4)
    if magic != "glTF":
        raise Exception("glTF header signature not found: #{}".format(magic))

    version = reader.read_as_data_type(GlConstants.UNSIGNED_INT)
    if version != 2:
        raise Exception(
            "version #{} found. This plugin only supports version 2".format(version)
        )

    size = reader.read_as_data_type(GlConstants.UNSIGNED_INT)
    size -= 12

    json_str = None
    body = None
    while size > 0:
        # print(size)

        if json_str is not None and body is not None:
            raise Exception(
                "This VRM has multiple chunks, this plugin reads one chunk only."
            )

        chunk_size = reader.read_unsigned_int()
        size -= 4

        chunk_type = reader.read_str(4)
        size -= 4

        chunk_data = reader.read_binary(chunk_size)
        size -= chunk_size

        if chunk_type == "BIN\x00":
            body = chunk_data
            continue
        if chunk_type == "JSON":
            json_str = chunk_data.decode("utf-8")  # blenderのpythonverが古く自前decode要す
            continue

        raise Exception("unknown chunk_type: {}".format(chunk_type))

    if not json_str:
        raise Exception("failed to read json chunk")
    return json.loads(json_str, object_pairs_hook=OrderedDict), (
        body if body else bytes()
    )


# あくまでvrm(の特にバイナリ)をpythonデータ化するだけで、blender型に変形はここではしない
def read_vrm(
    model_path: str,
    make_new_texture_folder: bool,
    use_simple_principled_material: bool,
    license_check: bool,
) -> vrm_types.VrmPydata:
    vrm_pydata = vrm_types.VrmPydata(filepath=model_path)
    # datachunkは普通一つしかない
    with open(model_path, "rb") as f:
        vrm_pydata.json, body_binary = parse_glb(f.read())

    # KHR_DRACO_MESH_COMPRESSION は対応してない場合落とさないといけないらしい。どのみち壊れたデータになるからね。
    if (
        "extensionsRequired" in vrm_pydata.json
        and "KHR_DRACO_MESH_COMPRESSION" in vrm_pydata.json["extensionsRequired"]
    ):
        raise Exception(
            "This VRM uses Draco compression. Unable to decompress. Draco圧縮されたVRMは未対応です"
        )

    if license_check:
        validate_license(vrm_pydata)

    texture_rip(vrm_pydata, body_binary, make_new_texture_folder)

    vrm_pydata.decoded_binary = decode_bin(vrm_pydata.json, body_binary)

    mesh_read(vrm_pydata)
    material_read(vrm_pydata, use_simple_principled_material)
    skin_read(vrm_pydata)
    node_read(vrm_pydata)

    return vrm_pydata


def validate_license_url(
    url_str: str, json_key: str, props: List[LicenseConfirmationRequiredProp]
) -> None:
    if url_str == "undefined":  # Our plugin........................
        return
    url = None
    with contextlib.suppress(ValueError):
        url = urlparse(url_str)
    if url:
        query_dict = dict(parse_qsl(url.query))
        if validate_vroid_hub_license_url(
            url, query_dict, json_key, props
        ) or validate_uni_virtual_license_url(url, query_dict, json_key, props):
            return
    props.append(
        LicenseConfirmationRequiredProp(
            url_str,
            json_key,
            "Is this VRM allowed to edited? Please check its copyright license.",
            "独自のライセンスが記載されています。",
        )
    )


def validate_vroid_hub_license_url(
    url: ParseResult,
    query_dict: Dict[str, str],
    json_key: str,
    props: List[LicenseConfirmationRequiredProp],
) -> bool:
    # https://hub.vroid.com/en/license?allowed_to_use_user=everyone&characterization_allowed_user=everyone&corporate_commercial_use=allow&credit=unnecessary&modification=allow&personal_commercial_use=profit&redistribution=allow&sexual_expression=allow&version=1&violent_expression=allow
    if url.hostname != "hub.vroid.com" or not url.path.endswith("/license"):
        return False
    if query_dict.get("modification") == "disallow":
        props.append(
            LicenseConfirmationRequiredProp(
                url.geturl(),
                json_key,
                'This VRM is licensed by VRoid Hub License "Alterations: No".',
                "このVRMにはVRoid Hubの「改変: NG」ライセンスが設定されています。",
            )
        )
    return True


def validate_uni_virtual_license_url(
    url: ParseResult,
    query_dict: Dict[str, str],
    json_key: str,
    props: List[LicenseConfirmationRequiredProp],
) -> bool:
    # https://uv-license.com/en/license?utf8=%E2%9C%93&pcu=true
    if url.hostname != "uv-license.com" or not url.path.endswith("/license"):
        return False
    if query_dict.get("remarks") == "true":
        props.append(
            LicenseConfirmationRequiredProp(
                url.geturl(),
                json_key,
                'This VRM is licensed by UV License with "Remarks".',
                "このVRMには特記事項(Remarks)付きのUVライセンスが設定されています。",
            )
        )
    return True


def validate_license(vrm_pydata: vrm_types.VrmPydata):
    confirmations: List[LicenseConfirmationRequiredProp] = []

    # 既知の改変不可ライセンスを撥ねる
    # CC_NDなど
    license_name = json_get(
        vrm_pydata.json, ["extensions", "VRM", "meta", "licenseName"], ""
    )
    if re.match("CC(.*)ND(.*)", license_name):
        confirmations.append(
            LicenseConfirmationRequiredProp(
                None,
                None,
                'The VRM is licensed by "{license_name}".\nNo derivative works are allowed.',
                f"指定されたVRMは改変不可ライセンス「{license_name}」が設定されています。\n改変することはできません。",
            )
        )

    other_permission_url_str = json_get(
        vrm_pydata.json, ["extensions", "VRM", "meta", "otherPermissionUrl"], None
    )
    if other_permission_url_str:
        validate_license_url(
            other_permission_url_str, "otherPermissionUrl", confirmations
        )

    if license_name == "Other":
        other_license_url_str = json_get(
            vrm_pydata.json, ["extensions", "VRM", "meta", "otherLicenseUrl"], ""
        )
        validate_license_url(other_license_url_str, "otherLicenseUrl", confirmations)

    if confirmations:
        raise LicenseConfirmationRequired(confirmations)


def texture_rip(vrm_pydata, body_binary, make_new_texture_folder):
    buffer_views = vrm_pydata.json["bufferViews"]
    binary_reader = BinaryReader(body_binary)
    # ここ画像切り出し #blenderはバイト列から画像を読み込む術がないので、画像ファイルを書き出して、それを読み込むしかない。
    vrm_dir_path = os.path.dirname(os.path.abspath(vrm_pydata.filepath))
    if "images" not in vrm_pydata.json:
        return

    def invalid_chars_remover(filename):
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
            "", "", "".join([chr(charnum) for charnum in unsafe_chars])
        )
        safe_filename = filename.translate(remove_table)
        return safe_filename

    def get_meta(param, default_value, max_length):
        meta_value = vrm_pydata.json["extensions"]["VRM"]["meta"].get(param)
        if meta_value is not None:
            return meta_value[:max_length]
        return default_value

    model_title = invalid_chars_remover(get_meta("title", "", 12))
    model_author = invalid_chars_remover(get_meta("author", "", 8))
    model_version = invalid_chars_remover(get_meta("version", "", 7))
    dir_name = "tex"
    if model_title != "":
        dir_name += "_" + model_title
    if model_author != "":
        dir_name += "_by_" + model_author
    if model_version != "":
        dir_name += "_of_" + model_version
    dir_path = os.path.join(vrm_dir_path, dir_name)
    if dir_name == "tex":
        dir_name = invalid_chars_remover(
            datetime.datetime.today().strftime("%M%D%H%I%M%S")
        )
        for i in range(100000):
            dn = f"tex_{dir_name}_{i}"
            if os.path.exists(os.path.join(vrm_dir_path, dn)):
                continue
            if os.path.exists(os.path.join(vrm_dir_path, dn)) and i == 99999:
                dir_path = os.path.join(vrm_dir_path, dn)
                break
            os.mkdir(os.path.join(vrm_dir_path, dn))
            dir_path = os.path.join(vrm_dir_path, dn)
            break
    elif not os.path.exists(os.path.join(vrm_dir_path, dir_name)):
        os.mkdir(dir_path)
    elif make_new_texture_folder:
        for i in range(100001):
            dn = f"{dir_name}_{i}" if i != 0 else dir_name
            if not os.path.exists(os.path.join(vrm_dir_path, dn)):
                os.mkdir(os.path.join(vrm_dir_path, dn))
                dir_path = os.path.join(vrm_dir_path, dn)
                break
    for image_id, image_prop in enumerate(vrm_pydata.json["images"]):
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
            print("no name image is named {}".format(image_name))
        elif len(image_name) >= 50:
            print(
                "too long name image: {} is named {}".format(
                    image_name, "tex_2longname_" + str(image_id)
                )
            )
            image_name = "tex_2longname_" + str(image_id)

        image_name = invalid_chars_remover(image_name)
        image_path = os.path.join(dir_path, image_name)
        if os.path.splitext(image_name)[1].lower() != ("." + image_type).lower():
            image_path += "." + image_type
        if not os.path.exists(image_path):  # すでに同名の画像がある場合は基本上書きしない
            with open(image_path, "wb") as image_writer:
                image_writer.write(image_binary)
        elif image_name in [
            img.name for img in vrm_pydata.image_properties
        ]:  # ただ、それがこのVRMを開いた時の名前の時はちょっと考えて書いてみる。
            written_flag = False
            for i in range(5):
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
                    "There are more than 5 images with the same name in the folder. Failed to write file: {}".format(
                        image_name
                    )
                )
        else:
            print(image_name + " Image already exists. Was not overwritten.")
        image_property = vrm_types.ImageProps(image_name, image_path, image_type)
        vrm_pydata.image_properties.append(image_property)


#  "accessorの順に" データを読み込んでリストにしたものを返す
def decode_bin(json_data, binary):
    br = BinaryReader(binary)
    # This list indexed by accessor index
    decoded_binary = []
    buffer_views = json_data["bufferViews"]
    accessors = json_data["accessors"]
    type_num_dict = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
    for accessor in accessors:
        type_num = type_num_dict[accessor["type"]]
        br.set_pos(buffer_views[accessor["bufferView"]]["byteOffset"])
        data_list = []
        for _ in range(accessor["count"]):
            if type_num == 1:
                data = br.read_as_data_type(accessor["componentType"])
            else:
                data = []
                for _ in range(type_num):
                    data.append(br.read_as_data_type(accessor["componentType"]))
            data_list.append(data)
        decoded_binary.append(data_list)

    return decoded_binary


def mesh_read(vrm_pydata):
    # メッシュをパースする
    for n, mesh in enumerate(vrm_pydata.json["meshes"]):
        primitives = []
        for j, primitive in enumerate(mesh["primitives"]):
            vrm_mesh = vrm_types.Mesh()
            vrm_mesh.object_id = n
            if j == 0:  # mesh annotationとの兼ね合い
                vrm_mesh.name = mesh["name"]
            else:
                vrm_mesh.name = mesh["name"] + str(j)

            # region 頂点index
            if primitive["mode"] != GlConstants.TRIANGLES:
                # TODO その他メッシュタイプ対応
                raise Exception(
                    "Unsupported polygon type(:{}) Exception".format(primitive["mode"])
                )
            vrm_mesh.face_indices = vrm_pydata.decoded_binary[primitive["indices"]]
            # 3要素ずつに変換しておく(GlConstants.TRIANGLES前提なので)
            # ATTENTION これだけndarray
            vrm_mesh.face_indices = numpy.reshape(vrm_mesh.face_indices, (-1, 3))
            # endregion 頂点index

            # ここから頂点属性
            vertex_attributes = primitive["attributes"]
            # 頂点属性は実装によっては存在しない属性(例えばJOINTSやWEIGHTSがなかったりもする)もあるし、UVや頂点カラー0->Nで増やせる(スキニングは1要素(ボーン4本)限定
            for attr in vertex_attributes.keys():
                vrm_mesh.__setattr__(
                    attr, vrm_pydata.decoded_binary[vertex_attributes[attr]]
                )

            # region TEXCOORD_FIX [ 古いUniVRM誤り: uv.y = -uv.y ->修復 uv.y = 1 - ( -uv.y ) => uv.y=1+uv.y]
            legacy_uv_flag = False  # f***
            gen = json_get(vrm_pydata.json, ["assets", "generator"], "")
            if re.match("UniGLTF", gen):
                with contextlib.suppress(ValueError):
                    if float("".join(gen[-4:])) < 1.16:
                        legacy_uv_flag = True

            uv_count = 0
            while True:
                texcoord_name = "TEXCOORD_{}".format(uv_count)
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
            vrm_mesh.POSITION_accessor = primitive["attributes"]["POSITION"]

            # ここからモーフターゲット vrmのtargetは相対位置 normalは無視する
            if "targets" in primitive:
                morph_target_point_list_and_accessor_index_dict = OrderedDict()
                for i, morph_target in enumerate(primitive["targets"]):
                    pos_array = vrm_pydata.decoded_binary[morph_target["POSITION"]]
                    if "extra" in morph_target:  # for old AliciaSolid
                        # accessorのindexを持つのは変換時のキャッシュ対応のため
                        morph_name = primitive["targets"][i]["extra"]["name"]
                    else:
                        morph_name = primitive["extras"]["targetNames"][i]
                        # 同上
                    morph_target_point_list_and_accessor_index_dict[morph_name] = [
                        pos_array,
                        primitive["targets"][i]["POSITION"],
                    ]

                vrm_mesh.__setattr__(
                    "morph_target_point_list_and_accessor_index_dict",
                    morph_target_point_list_and_accessor_index_dict,
                )
            primitives.append(vrm_mesh)
        vrm_pydata.meshes.append(primitives)

    # ここからマテリアル


def material_read(vrm_pydata, use_simple_principled_material):
    vrm_extension_material_properties = json_get(
        vrm_pydata.json,
        ["extensions", "VRM", "materialProperties"],
        default=[{"shader": "VRM_USE_GLTFSHADER"}] * len(vrm_pydata.json["materials"]),
    )
    if "textures" in vrm_pydata.json:
        textures = vrm_pydata.json["textures"]  # noqa: F841
    for mat, ext_mat in zip(
        vrm_pydata.json["materials"], vrm_extension_material_properties
    ):
        vrm_pydata.materials.append(
            vrm2pydata_factory.material(mat, ext_mat, use_simple_principled_material)
        )

    # skinをパース ->バイナリの中身はskinning実装の横着用
    # skinのjointsの(nodesの)indexをvertsのjoints_0は指定してる
    # inverseBindMatrices: 単にスキニングするときの逆行列。読み込み不要なのでしない(自前計算もできる、めんどいけど)
    # ついでに[i][3]ではなく、[3][i]にマイナスx,y,zが入っている。 ここで詰まった。(出力時に)
    # joints:JOINTS_0の指定node番号のindex


def skin_read(vrm_pydata):
    for skin in vrm_pydata.json.get("skins", []):
        vrm_pydata.skins_joints_list.append(skin["joints"])
        if "skeleton" in skin.keys():
            vrm_pydata.skins_root_node_list.append(skin["skeleton"])

    # node(ボーン)をパースする->親からの相対位置で記録されている


def node_read(vrm_pydata):
    for i, node in enumerate(vrm_pydata.json["nodes"]):
        vrm_pydata.nodes_dict[i] = vrm2pydata_factory.bone(node)
        # TODO こっからorigin_bone
        if "mesh" in node.keys():
            vrm_pydata.origin_nodes_dict[i] = [vrm_pydata.nodes_dict[i], node["mesh"]]
            if "skin" in node.keys():
                vrm_pydata.origin_nodes_dict[i].append(node["skin"])
            else:
                print(node["name"] + "is not have skin")


if __name__ == "__main__":
    read_vrm(
        sys.argv[1],
        make_new_texture_folder=True,
        use_simple_principled_material=False,
        license_check=True,
    )
