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
            message = "Failed to read VRM glTF header: " + ",".join(
                chr(b) for b in header_bytes
            )
            raise ValueError(message)

        header: tuple[bytes, int, int] = struct.unpack("<4sII", header_bytes)
        magic, version, length = header
        if magic != b"glTF":
            message = "Invalid VRM glTF magic bytes: " + ",".join(chr(b) for b in magic)
            raise ValueError(message)

        if version != 2:
            message = f"Unsupported VRM glTF Version: {version}"
            raise ValueError(message)

        chunks_bytes_length = length - 12
        if chunks_bytes_length < 0:
            message = f"Invalid VRM glTF length: {length}"
            raise ValueError(message)

        chunks_bytes = glb.read(chunks_bytes_length)
        if len(chunks_bytes) != chunks_bytes_length:
            message = "Failed to read VRM chunks bytes"
            raise ValueError(message)

    with BytesIO(chunks_bytes) as chunks:
        json_chunk_length_bytes = chunks.read(4)
        if len(json_chunk_length_bytes) != 4:
            message = "Failed to read VRM json chunk length bytes"
            raise ValueError(message)

        json_chunk_type_bytes = chunks.read(4)
        if len(json_chunk_type_bytes) != 4:
            message = "Failed to read VRM json chunk type bytes"
            raise ValueError(message)

        if json_chunk_type_bytes != b"JSON":
            message = "Invalid VRM json chunk type bytes: " + ",".join(
                chr(b) for b in json_chunk_type_bytes
            )
            raise ValueError(message)

        json_chunk_data_length: int = struct.unpack("<I", json_chunk_length_bytes)[0]
        json_chunk_data_bytes = chunks.read(json_chunk_data_length)
        if len(json_chunk_data_bytes) != json_chunk_data_length:
            message = "Failed to read VRM json chunk"
            raise ValueError(message)

        raw_json = json.loads(json_chunk_data_bytes)  # raises json.JSONDecodeError
        json_obj = make_json(raw_json)
        if not isinstance(json_obj, dict):
            message = f"Unexpected VRM json format: {type(json_obj)}"
            raise TypeError(message)

        bin_chunk_length_bytes = chunks.read(4)
        if not bin_chunk_length_bytes:
            return json_obj, b""
        if len(bin_chunk_length_bytes) != 4:
            message = "Failed to read VRM bin chunk length bytes"
            raise ValueError(message)

        bin_chunk_type_bytes = chunks.read(4)
        if len(bin_chunk_type_bytes) != 4:
            message = "Failed to read VRM bin chunk type bytes"
            raise ValueError(message)

        if bin_chunk_type_bytes != b"BIN\x00":
            message = "Invalid VRM bin chunk type bytes: " + ",".join(
                chr(b) for b in bin_chunk_type_bytes
            )
            raise ValueError(message)

        bin_chunk_data_length: int = struct.unpack("<I", bin_chunk_length_bytes)[0]
        bin_chunk_data_bytes = chunks.read(bin_chunk_data_length)
        if len(bin_chunk_data_bytes) != bin_chunk_data_length:
            message = "Failed to read VRM bin chunk"
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
            # json chunk
            + 8
            + len(json_chunk_bytes)
            # binary chunk
            + 8
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
