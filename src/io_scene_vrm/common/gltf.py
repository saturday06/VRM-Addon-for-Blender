# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import base64
import json
import struct
from io import BytesIO
from typing import Final, Optional, Union
from urllib.parse import urlparse

from mathutils import Quaternion, Vector

from .convert import Json
from .deep import make_json
from .gl import (
    GL_BYTE,
    GL_FLOAT,
    GL_INT,
    GL_SHORT,
    GL_UNSIGNED_BYTE,
    GL_UNSIGNED_INT,
    GL_UNSIGNED_SHORT,
)

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
        separators=(",", ":"),
        sort_keys=True,
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


def read_accessor_as_bytes(
    accessor_dict: dict[str, Json],
    buffer_view_dicts: list[Json],
    buffer_dicts: list[Json],
    bin_chunk_bytes: Optional[bytes],
) -> Optional[bytes]:
    buffer_view_index = accessor_dict.get("bufferView")
    if not isinstance(buffer_view_index, int):
        return None
    if not 0 <= buffer_view_index < len(buffer_view_dicts):
        return None
    buffer_view_dict = buffer_view_dicts[buffer_view_index]
    if not isinstance(buffer_view_dict, dict):
        return None
    buffer_index = buffer_view_dict.get("buffer")
    if not isinstance(buffer_index, int):
        return None
    if not 0 <= buffer_index < len(buffer_dicts):
        return None

    if buffer_index == 0 and bin_chunk_bytes is not None:
        buffer_bytes = bin_chunk_bytes
    else:
        prefix = "application/gltf-buffer;base64,"

        buffer_dict = buffer_dicts[buffer_index]
        if not isinstance(buffer_dict, dict):
            return None
        uri = buffer_dict.get("uri")

        if not isinstance(uri, str):
            return None
        try:
            parsed_url = urlparse(uri)
        except ValueError:
            return None
        if parsed_url.scheme != "data":
            return None
        if not parsed_url.path.startswith(prefix):  # TODO: all variants
            return None
        buffer_base64 = parsed_url.path.removeprefix(prefix)
        buffer_bytes = base64.b64decode(buffer_base64)

    byte_offset = buffer_view_dict.get("byteOffset", 0)
    if not isinstance(byte_offset, int):
        return None
    if not 0 <= byte_offset < len(buffer_bytes):
        return None
    byte_length = buffer_view_dict.get("byteLength")
    if not isinstance(byte_length, int):
        return None
    if not 0 <= byte_offset + byte_length <= len(buffer_bytes):
        return None
    return buffer_bytes[slice(byte_offset, byte_offset + byte_length)]


def unpack_component(
    component_type: int, unpack_count: int, buffer_bytes: bytes
) -> Optional[Union[tuple[int, ...], tuple[float, ...]]]:
    for search_component_type, component_count, unpack_symbol in [
        (GL_BYTE, 1, "b"),
        (GL_UNSIGNED_BYTE, 1, "B"),
        (GL_SHORT, 2, "h"),
        (GL_UNSIGNED_SHORT, 2, "H"),
        (GL_INT, 4, "i"),
        (GL_UNSIGNED_INT, 4, "I"),
        (GL_FLOAT, 4, "f"),
    ]:
        if search_component_type != component_type:
            continue
        if unpack_count == 0:
            return ()
        if not 1 <= unpack_count * component_count <= len(buffer_bytes):
            return None
        return struct.unpack("<" + unpack_symbol * unpack_count, buffer_bytes)
    return None


def unpack_accessor_as_scalar_components(
    accessor_dict: dict[str, Json],
    buffer_view_dicts: list[Json],
    buffer_dicts: list[Json],
    buffer0_bytes: bytes,
    unpack_count: int,
) -> Union[tuple[int, ...], tuple[float, ...], None]:
    component_type = accessor_dict.get("componentType")
    if not isinstance(component_type, int):
        return None

    raw_bytes = read_accessor_as_bytes(
        accessor_dict,
        buffer_view_dicts,
        buffer_dicts,
        buffer0_bytes,
    )
    if not raw_bytes:
        return None

    return unpack_component(component_type, unpack_count, raw_bytes)


def read_scalar_accessor(
    accessor_dict: dict[str, Json],
    buffer_view_dicts: list[Json],
    buffer_dicts: list[Json],
    buffer0_bytes: bytes,
) -> Union[tuple[int, ...], tuple[float, ...], None]:
    accessor_type = accessor_dict.get("type")
    if accessor_type != "SCALAR":
        return None
    count = accessor_dict.get("count")
    if not isinstance(count, int):
        return None
    return unpack_accessor_as_scalar_components(
        accessor_dict,
        buffer_view_dicts,
        buffer_dicts,
        buffer0_bytes,
        count,
    )


def read_vec2_accessor(
    accessor_dict: dict[str, Json],
    buffer_view_dicts: list[Json],
    buffer_dicts: list[Json],
    buffer0_bytes: bytes,
) -> Union[tuple[tuple[int, int], ...], tuple[tuple[float, float], ...], None]:
    accessor_type = accessor_dict.get("type")
    if accessor_type != "VEC2":
        return None
    count = accessor_dict.get("count")
    if not isinstance(count, int):
        return None
    components = unpack_accessor_as_scalar_components(
        accessor_dict,
        buffer_view_dicts,
        buffer_dicts,
        buffer0_bytes,
        count * 2,
    )
    if components is None:
        return None
    return tuple(
        (
            components[i],
            components[i + 1],
        )
        for i in range(0, count * 2, 2)
    )


def read_vec3_accessor(
    accessor_dict: dict[str, Json],
    buffer_view_dicts: list[Json],
    buffer_dicts: list[Json],
    buffer0_bytes: bytes,
) -> Union[
    tuple[tuple[int, int, int], ...], tuple[tuple[float, float, float], ...], None
]:
    accessor_type = accessor_dict.get("type")
    if accessor_type != "VEC3":
        return None
    count = accessor_dict.get("count")
    if not isinstance(count, int):
        return None
    components = unpack_accessor_as_scalar_components(
        accessor_dict,
        buffer_view_dicts,
        buffer_dicts,
        buffer0_bytes,
        count * 3,
    )
    if components is None:
        return None
    return tuple(
        (
            components[i],
            components[i + 1],
            components[i + 2],
        )
        for i in range(0, count * 3, 3)
    )


def read_vec4_accessor(
    accessor_dict: dict[str, Json],
    buffer_view_dicts: list[Json],
    buffer_dicts: list[Json],
    buffer0_bytes: bytes,
) -> Union[
    tuple[tuple[int, int, int, int], ...],
    tuple[tuple[float, float, float, float], ...],
    None,
]:
    accessor_type = accessor_dict.get("type")
    if accessor_type != "VEC4":
        return None
    count = accessor_dict.get("count")
    if not isinstance(count, int):
        return None
    components = unpack_accessor_as_scalar_components(
        accessor_dict,
        buffer_view_dicts,
        buffer_dicts,
        buffer0_bytes,
        count * 4,
    )
    if components is None:
        return None
    return tuple(
        (
            components[i],
            components[i + 1],
            components[i + 2],
            components[i + 3],
        )
        for i in range(0, count * 4, 4)
    )


def read_mat4_accessor(
    accessor_dict: dict[str, Json],
    buffer_view_dicts: list[Json],
    buffer_dicts: list[Json],
    buffer0_bytes: bytes,
) -> Union[
    tuple[
        tuple[
            tuple[int, int, int, int],
            tuple[int, int, int, int],
            tuple[int, int, int, int],
            tuple[int, int, int, int],
        ],
        ...,
    ],
    tuple[
        tuple[
            tuple[float, float, float, float],
            tuple[float, float, float, float],
            tuple[float, float, float, float],
            tuple[float, float, float, float],
        ],
        ...,
    ],
    None,
]:
    accessor_type = accessor_dict.get("type")
    if accessor_type != "MAT4":
        return None
    count = accessor_dict.get("count")
    if not isinstance(count, int):
        return None
    components = unpack_accessor_as_scalar_components(
        accessor_dict,
        buffer_view_dicts,
        buffer_dicts,
        buffer0_bytes,
        count * 16,
    )
    if components is None:
        return None
    return tuple(
        (
            (
                components[i],
                components[i + 1],
                components[i + 2],
                components[i + 3],
            ),
            (
                components[i + 4],
                components[i + 5],
                components[i + 6],
                components[i + 7],
            ),
            (
                components[i + 8],
                components[i + 9],
                components[i + 10],
                components[i + 11],
            ),
            (
                components[i + 12],
                components[i + 13],
                components[i + 14],
                components[i + 15],
            ),
        )
        for i in range(0, count * 16, 16)
    )


def read_accessor(
    accessor_dict: dict[str, Json],
    buffer_view_dicts: list[Json],
    buffer_dicts: list[Json],
    buffer0_bytes: bytes,
) -> Union[
    tuple[int, ...],
    tuple[float, ...],
    tuple[tuple[int, int], ...],
    tuple[tuple[float, float], ...],
    tuple[tuple[int, int, int], ...],
    tuple[tuple[float, float, float], ...],
    tuple[tuple[int, int, int, int], ...],
    tuple[tuple[float, float, float, float], ...],
    tuple[
        tuple[
            tuple[int, int, int, int],
            tuple[int, int, int, int],
            tuple[int, int, int, int],
            tuple[int, int, int, int],
        ],
        ...,
    ],
    tuple[
        tuple[
            tuple[float, float, float, float],
            tuple[float, float, float, float],
            tuple[float, float, float, float],
            tuple[float, float, float, float],
        ],
        ...,
    ],
    None,
]:
    accessor_type = accessor_dict.get("type")
    if accessor_type == "SCALAR":
        return read_scalar_accessor(
            accessor_dict, buffer_view_dicts, buffer_dicts, buffer0_bytes
        )
    if accessor_type == "VEC2":
        return read_vec2_accessor(
            accessor_dict, buffer_view_dicts, buffer_dicts, buffer0_bytes
        )
    if accessor_type == "VEC3":
        return read_vec3_accessor(
            accessor_dict, buffer_view_dicts, buffer_dicts, buffer0_bytes
        )
    if accessor_type == "VEC4":
        return read_vec4_accessor(
            accessor_dict, buffer_view_dicts, buffer_dicts, buffer0_bytes
        )
    if accessor_type == "MAT4":
        return read_mat4_accessor(
            accessor_dict, buffer_view_dicts, buffer_dicts, buffer0_bytes
        )
    return None


def read_accessors(
    json_dict: dict[str, Json],
    buffer0_bytes: bytes,
) -> tuple[
    Union[
        tuple[int, ...],
        tuple[float, ...],
        tuple[tuple[int, int], ...],
        tuple[tuple[float, float], ...],
        tuple[tuple[int, int, int], ...],
        tuple[tuple[float, float, float], ...],
        tuple[tuple[int, int, int, int], ...],
        tuple[tuple[float, float, float, float], ...],
        tuple[
            tuple[
                tuple[int, int, int, int],
                tuple[int, int, int, int],
                tuple[int, int, int, int],
                tuple[int, int, int, int],
            ],
            ...,
        ],
        tuple[
            tuple[
                tuple[float, float, float, float],
                tuple[float, float, float, float],
                tuple[float, float, float, float],
                tuple[float, float, float, float],
            ],
            ...,
        ],
        None,
    ],
    ...,
]:
    accessor_dicts = json_dict.get("accessors")
    if not isinstance(accessor_dicts, list):
        accessor_dicts = []

    buffer_view_dicts = json_dict.get("bufferViews")
    if not isinstance(buffer_view_dicts, list):
        buffer_view_dicts = []

    buffer_dicts = json_dict.get("buffers")
    if not isinstance(buffer_dicts, list):
        buffer_dicts = []

    return tuple(
        read_accessor(accessor_dict, buffer_view_dicts, buffer_dicts, buffer0_bytes)
        for accessor_dict in accessor_dicts
        if isinstance(accessor_dict, dict)
    )


def read_accessor_as_animation_sampler_input(
    accessor_dict: dict[str, Json],
    buffer_view_dicts: list[Json],
    buffer_dicts: list[Json],
    buffer0_bytes: bytes,
) -> Optional[list[float]]:
    scalar_accessor = read_scalar_accessor(
        accessor_dict, buffer_view_dicts, buffer_dicts, buffer0_bytes
    )
    if scalar_accessor is None:
        return None
    return [float(v) for v in scalar_accessor]


def read_accessor_as_animation_sampler_translation_output(
    accessor_dict: dict[str, Json],
    buffer_view_dicts: list[Json],
    buffer_dicts: list[Json],
    buffer0_bytes: bytes,
) -> Optional[list[Vector]]:
    vec3_accessor = read_vec3_accessor(
        accessor_dict, buffer_view_dicts, buffer_dicts, buffer0_bytes
    )
    if vec3_accessor is None:
        return None
    return [Vector((x, -z, y)) for x, y, z in vec3_accessor]


def read_accessor_as_animation_sampler_rotation_output(
    accessor_dict: dict[str, Json],
    buffer_view_dicts: list[Json],
    buffer_dicts: list[Json],
    buffer0_bytes: bytes,
) -> Optional[list[Quaternion]]:
    vec4_accessor = read_vec4_accessor(
        accessor_dict, buffer_view_dicts, buffer_dicts, buffer0_bytes
    )
    if vec4_accessor is None:
        return None
    return [Quaternion((w, x, -z, y)).normalized() for x, y, z, w in vec4_accessor]
