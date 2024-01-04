import json
import struct
from typing import Optional, Union

from .binary_reader import BinaryReader
from .deep import Json

# https://www.khronos.org/opengl/wiki/Small_Float_Formats#Numeric_limits_and_precision
FLOAT_POSITIVE_MAX = 3.4028237e38
FLOAT_NEGATIVE_MAX = -FLOAT_POSITIVE_MAX

TEXTURE_INPUT_NAMES = [
    "color_texture",
    "normal",
    "emissive_texture",
    "occlusion_texture",
]
VAL_INPUT_NAMES = ["metallic", "roughness", "unlit"]
RGBA_INPUT_NAMES = ["base_Color", "emissive_color"]


def parse_glb(data: bytes) -> tuple[dict[str, Json], bytes]:
    reader = BinaryReader(data)
    magic = reader.read_str(4)
    if magic != "glTF":
        message = f"glTF header signature not found: #{magic}"
        raise ValueError(message)

    version = reader.read_unsigned_int()
    if version != 2:
        message = f"version #{version} found. This plugin only supports version 2"
        raise ValueError(message)

    size = reader.read_unsigned_int()
    size -= 12

    json_str: Optional[str] = None
    body: Optional[bytes] = None
    while size > 0:
        if json_str is not None and body is not None:
            message = "This VRM has multiple chunks, this plugin reads one chunk only."
            raise ValueError(message)

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
            json_str = chunk_data.decode("utf-8")  # blenderのpythonが古く自前decode要す
            continue

        message = f"unknown chunk_type: {chunk_type}"
        raise ValueError(message)

    if not json_str:
        message = "failed to read json chunk"
        raise ValueError(message)

    json_obj = json.loads(json_str)
    if not isinstance(json_obj, dict):
        raise TypeError("VRM has invalid json: " + str(json_obj))
    return json_obj, body if body else b""


def pack_glb(
    json_dict: dict[str, Json], binary_chunk: Union[bytes, bytearray]
) -> bytes:
    magic = b"glTF" + struct.pack("<I", 2)
    json_str = json.dumps(
        json_dict,
        # UniVRM 0.56.3はエディタインポート時のUnicodeエスケープに未対応
        ensure_ascii=False,
    ).encode("utf-8")
    if len(json_str) % 4 != 0:
        json_str += b"\x20" * (4 - len(json_str) % 4)
    json_size = struct.pack("<I", len(json_str))
    if len(binary_chunk) % 4 != 0:
        binary_chunk += b"\x00" * (4 - len(binary_chunk) % 4)
    bin_size = struct.pack("<I", len(binary_chunk))
    total_size = struct.pack(
        "<I", len(json_str) + len(binary_chunk) + 28
    )  # include header size
    return (
        magic
        + total_size
        + json_size
        + b"JSON"
        + json_str
        + bin_size
        + b"BIN\x00"
        + binary_chunk
    )
