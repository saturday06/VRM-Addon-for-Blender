# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2018 iCyP

import sys
from dataclasses import dataclass, field
from itertools import repeat
from pathlib import Path
from typing import Optional, Union

from ..common import deep
from ..common.binary_reader import BinaryReader
from ..common.convert import Json
from ..common.gltf import parse_glb
from ..common.logging import get_logger
from .license_validation import validate_license

logger = get_logger(__name__)


@dataclass(frozen=True)
class Vrm0MaterialProperty:
    name: str
    shader: str
    render_queue: Optional[int]
    keyword_map: dict[str, bool]
    tag_map: dict[str, str]
    float_properties: dict[str, float]
    vector_properties: dict[str, list[float]]
    texture_properties: dict[str, int]

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
                k: float(v)
                for k, v in raw_float_properties.items()
                if isinstance(v, (float, int))
            }
        else:
            float_properties = fallback.float_properties

        raw_vector_properties = json_dict.get("vectorProperties")
        if isinstance(raw_vector_properties, dict):
            vector_properties: dict[str, list[float]] = {}
            for k, v in raw_vector_properties.items():
                if not isinstance(v, list):
                    continue
                float_v: list[float] = []
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
    json_dict: dict[str, Json] = field(default_factory=dict)
    spec_version_number: tuple[int, int] = (0, 0)
    spec_version_str: str = "0.0"
    spec_version_is_stable: bool = True
    vrm0_extension: dict[str, Json] = field(init=False, default_factory=dict)
    vrm1_extension: dict[str, Json] = field(init=False, default_factory=dict)
    hips_node_index: Optional[int] = None
    image_properties: list[ImageProperties] = field(init=False, default_factory=list)
    vrm0_material_properties: list[Vrm0MaterialProperty] = field(
        init=False, default_factory=list
    )
    skins_joints_list: list[list[int]] = field(init=False, default_factory=list)
    skins_root_node_list: list[int] = field(init=False, default_factory=list)


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


def decode_bin(
    json_dict: dict[str, Json], binary: bytes
) -> list[list[Union[int, float, list[int], list[float]]]]:
    """Decode bin and index by accessor indices."""
    br = BinaryReader(binary)
    decoded_binary: list[list[Union[int, float, list[int], list[float]]]] = []
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
            logger.warning("Unrecognized accessor type: %s", accessor_type)
            continue
        buffer_view_index = accessor_dict.get("bufferView")
        if not isinstance(buffer_view_index, int):
            logger.warning(
                "accessors[%s] doesn't have bufferView that is not implemented yet",
                accessor_index,
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
        data_list: list[Union[int, float, list[int], list[float]]] = []
        accessor_count = accessor_dict.get("count")
        if not isinstance(accessor_count, int):
            accessor_count = 0
        component_type = accessor_dict.get("componentType")
        if not isinstance(component_type, int):
            message = f"Unsupported component type: {component_type}"
            raise TypeError(message)
        for _ in range(accessor_count):
            if type_num == 1:
                single_data = br.read_as_data_type(component_type)
                data_list.append(single_data)
            else:
                multiple_data = [
                    br.read_as_data_type(component_type) for _ in range(type_num)
                ]
                data_list.append(multiple_data)
        decoded_binary.append(data_list)

    return decoded_binary


@dataclass
class VrmParser:
    filepath: Path
    extract_textures_into_folder: bool
    make_new_texture_folder: bool
    license_validation: bool
    decoded_binary: list[list[Union[int, float, list[int], list[float]]]] = field(
        init=False, default_factory=list
    )
    json_dict: dict[str, Json] = field(init=False, default_factory=dict)

    def parse(self) -> ParseResult:
        json_dict, _ = parse_glb(self.filepath.read_bytes())
        self.json_dict = json_dict

        if self.license_validation:
            validate_license(self.json_dict)

        parse_result = ParseResult(filepath=self.filepath, json_dict=self.json_dict)
        self.vrm_extension_read(parse_result)
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
        self, parse_result: ParseResult, vrm0_dict: dict[str, Json]
    ) -> None:
        spec_version = vrm0_dict.get("specVersion")
        if isinstance(spec_version, str):
            parse_result.spec_version_str = spec_version
        parse_result.vrm0_extension = vrm0_dict

        human_bones = deep.get(vrm0_dict, ["humanoid", "humanBones"], [])
        if not isinstance(human_bones, list):
            message = "No human bones"
            raise TypeError(message)

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
        self, parse_result: ParseResult, vrm1_dict: dict[str, Json]
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


if __name__ == "__main__":
    VrmParser(
        Path(sys.argv[1]),
        extract_textures_into_folder=True,
        make_new_texture_folder=True,
        license_validation=True,
    ).parse()
