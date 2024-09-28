import json
import struct
from io import BytesIO
from typing import Final, Union

from .convert import Json
from .deep import make_json

# https://www.khronos.org/opengl/wiki/Small_Float_Formats#Numeric_limits_and_precision
FLOAT_POSITIVE_MAX: Final = 3.4028237e38
FLOAT_NEGATIVE_MAX: Final = -FLOAT_POSITIVE_MAX


def parse_glb(data: bytes) -> tuple[dict[str, Json], bytes]:
    with BytesIO(data) as glb:
        header_bytes = glb.read(12)
        if len(header_bytes) != 12:
            message = "failed to read glb header"
            raise ValueError(message)

        header: tuple[bytes, int, int] = struct.unpack("<4sII", header_bytes)
        magic, version, _length = header
        if magic != b"glTF":
            message = ""
            raise ValueError(message)

        if version != 2:
            message = ""
            raise ValueError(message)

        json_chunk_length_bytes = glb.read(4)
        if len(json_chunk_length_bytes) != 4:
            message = ""
            raise ValueError(message)

        json_chunk_type_bytes = glb.read(4)
        if len(json_chunk_type_bytes) != 4:
            message = ""
            raise ValueError(message)

        if json_chunk_type_bytes != b"JSON":
            message = ""
            raise ValueError(message)

        json_chunk_length: int = struct.unpack("<I", json_chunk_length_bytes)[0]
        json_chunk_data_length = json_chunk_length - 8
        if json_chunk_data_length < 0:
            message = ""
            raise ValueError(message)

        json_chunk_data_bytes = glb.read(json_chunk_data_length)
        if len(json_chunk_data_bytes) != json_chunk_data_length:
            message = ""
            raise ValueError(message)

        raw_json = json.loads(json_chunk_data_bytes)  # raises json.JSONDecodeError
        json_obj = make_json(raw_json)
        if not isinstance(json_obj, dict):
            raise TypeError("VRM has invalid json: " + str(json_obj))

        bin_chunk_length_bytes = glb.read(4)
        if len(bin_chunk_length_bytes) != 4:
            message = ""
            raise ValueError(message)

        bin_chunk_type_bytes = glb.read(4)
        if len(bin_chunk_type_bytes) != 4:
            message = ""
            raise ValueError(message)

        if bin_chunk_type_bytes != b"BIN\x00":
            message = ""
            raise ValueError(message)

        bin_chunk_length: int = struct.unpack("<I", bin_chunk_length_bytes)[0]
        bin_chunk_data_length = bin_chunk_length - 8
        if bin_chunk_data_length < 0:
            message = ""
            raise ValueError(message)

        bin_chunk_data_bytes = glb.read(bin_chunk_data_length)
        if len(bin_chunk_data_bytes) != bin_chunk_data_length:
            message = ""
            raise ValueError(message)

    return json_obj, bin_chunk_data_bytes


def pack_glb(
    json_dict: dict[str, Json], bin_chunk_bytes: Union[bytes, bytearray]
) -> bytes:
    # https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#binary-gltf-layout
    json_chunk_bytes = json.dumps(
        json_dict,
        # UniVRM 0.56.3 cannot import a json containing unicode escape chars into
        # Unity Editor.
        ensure_ascii=False,
    ).encode()

    while len(json_chunk_bytes) % 4 != 0:
        json_chunk_bytes += b"\x20"

    while len(bin_chunk_bytes) % 4 != 0:
        bin_chunk_bytes += b"\x00"

    glb = bytearray()

    glb.extend(b"glTF")  # magic
    glb.extend(struct.pack("<I", 2))  # version
    glb.extend(  # length
        struct.pack(
            "<I",
            # header
            12
            +
            # json chunk
            8
            + len(json_chunk_bytes)
            +
            # binary chunk
            8
            + len(bin_chunk_bytes),
        )
    )

    glb.extend(struct.pack("<I", len(json_chunk_bytes)))
    glb.extend(b"JSON")
    glb.extend(json_chunk_bytes)

    glb.extend(struct.pack("<I", len(bin_chunk_bytes)))
    glb.extend(b"BIN\x00")
    glb.extend(bin_chunk_bytes)

    return bytes(glb)
