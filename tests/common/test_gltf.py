# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import base64
import struct
from unittest import TestCase

from mathutils import Matrix, Quaternion

from io_scene_vrm.common import gltf
from io_scene_vrm.common.convert import Json

_DATA_URI_PREFIX = "data:application/gltf-buffer;base64,"


def _require_json_dict(value: Json, context: str) -> dict[str, Json]:
    if not isinstance(value, dict):
        message = f"{context} must be a dict"
        raise TypeError(message)
    return value


def _require_json_list(value: Json, context: str) -> list[Json]:
    if not isinstance(value, list):
        message = f"{context} must be a list"
        raise TypeError(message)
    return value


def _require_json_int(value: Json, context: str) -> int:
    if not isinstance(value, int):
        message = f"{context} must be an int"
        raise TypeError(message)
    return value


def _read_accessor_buffer_bytes(
    json_dict: dict[str, Json],
    accessor_index: int,
) -> bytes:
    accessor_dicts = _require_json_list(json_dict["accessors"], "accessors")
    accessor_dict = _require_json_dict(
        accessor_dicts[accessor_index], f"accessors[{accessor_index}]"
    )
    buffer_view_index = _require_json_int(
        accessor_dict.get("bufferView"), f"accessors[{accessor_index}].bufferView"
    )

    buffer_view_dicts = _require_json_list(json_dict["bufferViews"], "bufferViews")
    buffer_view_dict = _require_json_dict(
        buffer_view_dicts[buffer_view_index], f"bufferViews[{buffer_view_index}]"
    )
    buffer_index = _require_json_int(
        buffer_view_dict.get("buffer"), f"bufferViews[{buffer_view_index}].buffer"
    )
    byte_offset = _require_json_int(
        buffer_view_dict.get("byteOffset", 0),
        f"bufferViews[{buffer_view_index}].byteOffset",
    )
    byte_length = _require_json_int(
        buffer_view_dict.get("byteLength"),
        f"bufferViews[{buffer_view_index}].byteLength",
    )

    buffer_dicts = _require_json_list(json_dict["buffers"], "buffers")
    uri = _require_json_dict(
        buffer_dicts[buffer_index], f"buffers[{buffer_index}]"
    ).get("uri")
    if not isinstance(uri, str):
        message = f"buffers[{buffer_index}].uri must be a string"
        raise TypeError(message)
    if not uri.startswith(_DATA_URI_PREFIX):
        message = f"buffers[{buffer_index}].uri must be a glTF data URI"
        raise ValueError(message)

    buffer_bytes = base64.b64decode(uri[len(_DATA_URI_PREFIX) :])
    return buffer_bytes[byte_offset : byte_offset + byte_length]


class TestGltf(TestCase):
    def test_read_accessor_as_bytes_data_uri(self) -> None:
        expected_data = b"Hello World"
        base64_data = base64.b64encode(expected_data).decode("ascii")

        test_cases = [
            f"data:application/gltf-buffer;base64,{base64_data}",
            f"data:application/octet-stream;base64,{base64_data}",
        ]

        for uri in test_cases:
            with self.subTest(uri=uri):
                accessor_dict: dict[str, Json] = {
                    "bufferView": 0,
                    "componentType": 5121,
                    "count": len(expected_data),
                    "type": "SCALAR",
                }
                buffer_view_dicts: list[Json] = [
                    {"buffer": 0, "byteOffset": 0, "byteLength": len(expected_data)}
                ]
                buffer_dicts: list[Json] = [{"uri": uri}]

                result = gltf._read_accessor_as_bytes(
                    accessor_dict,
                    buffer_view_dicts,
                    buffer_dicts,
                    None,  # bin_chunk_bytes
                )

                self.assertEqual(result, expected_data, f"Failed to parse URI: {uri}")

    def test_read_accessor_as_bytes_invalid_uri(self) -> None:
        test_cases = [
            "http://example.com/data",
            "data:text/plain,Hello%20World",  # Not base64
            "data:;base64,InvalidBase64!!!!",
        ]

        for uri in test_cases:
            with self.subTest(uri=uri):
                accessor_dict: dict[str, Json] = {"bufferView": 0}
                buffer_view_dicts: list[Json] = [
                    {"buffer": 0, "byteOffset": 0, "byteLength": 5}
                ]
                buffer_dicts: list[Json] = [{"uri": uri}]
                result = gltf._read_accessor_as_bytes(
                    accessor_dict, buffer_view_dicts, buffer_dicts, None
                )
                self.assertIsNone(result, f"Should have failed for URI: {uri}")

    def test_read_accessor_as_bytes_with_byte_stride(self) -> None:
        buffer_data = b"HEADxxxxABzzxxxxCDzzxxxxEFzzTAIL"

        accessor_dict: dict[str, Json] = {
            "bufferView": 0,
            "byteOffset": 4,
            "componentType": 5121,
            "count": 3,
            "type": "VEC2",
        }
        buffer_view_dicts: list[Json] = [
            {"buffer": 0, "byteOffset": 4, "byteLength": 24, "byteStride": 8}
        ]
        buffer_dicts: list[Json] = [
            {
                "uri": "data:application/gltf-buffer;base64,"
                + base64.b64encode(buffer_data).decode("ascii")
            }
        ]

        result = gltf._read_accessor_as_bytes(
            accessor_dict,
            buffer_view_dicts,
            buffer_dicts,
            None,
        )

        self.assertEqual(result, b"ABCDEF")

    def test_read_accessor_with_byte_stride(self) -> None:
        buffer_data = b"HEADxxxxABzzxxxxCDzzxxxxEFzzTAIL"

        accessor_dict: dict[str, Json] = {
            "bufferView": 0,
            "byteOffset": 4,
            "componentType": 5121,
            "count": 3,
            "type": "VEC2",
        }
        buffer_view_dicts: list[Json] = [
            {"buffer": 0, "byteOffset": 4, "byteLength": 24, "byteStride": 8}
        ]
        buffer_dicts: list[Json] = [{}]

        result = gltf._read_accessor(
            accessor_dict,
            buffer_view_dicts,
            buffer_dicts,
            buffer_data,
        )

        self.assertEqual(result, ((65, 66), (67, 68), (69, 70)))

    def test_read_accessor_as_bytes_invalid_byte_stride(self) -> None:
        buffer_data = b"abcdef"

        accessor_dict: dict[str, Json] = {
            "bufferView": 0,
            "componentType": 5121,
            "count": 2,
            "type": "VEC3",
        }
        buffer_view_dicts: list[Json] = [
            {
                "buffer": 0,
                "byteOffset": 0,
                "byteLength": len(buffer_data),
                "byteStride": 2,
            }
        ]
        buffer_dicts: list[Json] = [
            {
                "uri": "data:application/gltf-buffer;base64,"
                + base64.b64encode(buffer_data).decode("ascii")
            }
        ]

        result = gltf._read_accessor_as_bytes(
            accessor_dict,
            buffer_view_dicts,
            buffer_dicts,
            None,
        )

        self.assertIsNone(result)

    def test_read_accessor_as_bytes_sparse_without_base_buffer_view(self) -> None:
        indices_data = b"\x01\x03"
        values_data = b"\x05\x09"

        accessor_dict: dict[str, Json] = {
            "type": "SCALAR",
            "componentType": 5121,
            "count": 4,
            "sparse": {
                "count": 2,
                "indices": {"bufferView": 0, "componentType": 5121},
                "values": {"bufferView": 1},
            },
        }
        buffer_view_dicts: list[Json] = [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(indices_data)},
            {"buffer": 1, "byteOffset": 0, "byteLength": len(values_data)},
        ]
        buffer_dicts: list[Json] = [
            {
                "uri": "data:application/gltf-buffer;base64,"
                + base64.b64encode(indices_data).decode("ascii")
            },
            {
                "uri": "data:application/gltf-buffer;base64,"
                + base64.b64encode(values_data).decode("ascii")
            },
        ]

        result = gltf._read_accessor_as_bytes(
            accessor_dict,
            buffer_view_dicts,
            buffer_dicts,
            None,
        )

        self.assertEqual(result, b"\x00\x05\x00\t")

    def test_read_accessor_as_bytes_sparse_over_base_buffer_view(self) -> None:
        base_data = b"abcdef"
        indices_data = b"\x01"
        values_data = b"XYZ"

        accessor_dict: dict[str, Json] = {
            "bufferView": 0,
            "type": "VEC3",
            "componentType": 5121,
            "count": 2,
            "sparse": {
                "count": 1,
                "indices": {"bufferView": 1, "componentType": 5121},
                "values": {"bufferView": 2},
            },
        }
        buffer_view_dicts: list[Json] = [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(base_data)},
            {"buffer": 1, "byteOffset": 0, "byteLength": len(indices_data)},
            {"buffer": 2, "byteOffset": 0, "byteLength": len(values_data)},
        ]
        buffer_dicts: list[Json] = [
            {
                "uri": "data:application/gltf-buffer;base64,"
                + base64.b64encode(base_data).decode("ascii")
            },
            {
                "uri": "data:application/gltf-buffer;base64,"
                + base64.b64encode(indices_data).decode("ascii")
            },
            {
                "uri": "data:application/gltf-buffer;base64,"
                + base64.b64encode(values_data).decode("ascii")
            },
        ]

        result = gltf._read_accessor_as_bytes(
            accessor_dict,
            buffer_view_dicts,
            buffer_dicts,
            None,
        )

        self.assertEqual(result, b"abcXYZ")

    def test_read_accessor_as_bytes_sparse_over_strided_base_buffer_view(self) -> None:
        base_data = b"xxxxabc1xxxxdef2"
        indices_data = b"\x01"
        values_data = b"XYZ"

        accessor_dict: dict[str, Json] = {
            "bufferView": 0,
            "byteOffset": 4,
            "type": "VEC3",
            "componentType": 5121,
            "count": 2,
            "sparse": {
                "count": 1,
                "indices": {"bufferView": 1, "componentType": 5121},
                "values": {"bufferView": 2},
            },
        }
        buffer_view_dicts: list[Json] = [
            {
                "buffer": 0,
                "byteOffset": 0,
                "byteLength": len(base_data),
                "byteStride": 8,
            },
            {"buffer": 1, "byteOffset": 0, "byteLength": len(indices_data)},
            {"buffer": 2, "byteOffset": 0, "byteLength": len(values_data)},
        ]
        buffer_dicts: list[Json] = [
            {
                "uri": "data:application/gltf-buffer;base64,"
                + base64.b64encode(base_data).decode("ascii")
            },
            {
                "uri": "data:application/gltf-buffer;base64,"
                + base64.b64encode(indices_data).decode("ascii")
            },
            {
                "uri": "data:application/gltf-buffer;base64,"
                + base64.b64encode(values_data).decode("ascii")
            },
        ]

        result = gltf._read_accessor_as_bytes(
            accessor_dict,
            buffer_view_dicts,
            buffer_dicts,
            None,
        )

        self.assertEqual(result, b"abcXYZ")

    def test_read_accessor_as_bytes_sparse_invalid_indices(self) -> None:
        base_data = b"abcdef"
        indices_data = b"\x01\x01"
        values_data = b"XYZXYZ"

        accessor_dict: dict[str, Json] = {
            "bufferView": 0,
            "type": "VEC3",
            "componentType": 5121,
            "count": 2,
            "sparse": {
                "count": 2,
                "indices": {"bufferView": 1, "componentType": 5121},
                "values": {"bufferView": 2},
            },
        }
        buffer_view_dicts: list[Json] = [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(base_data)},
            {"buffer": 1, "byteOffset": 0, "byteLength": len(indices_data)},
            {"buffer": 2, "byteOffset": 0, "byteLength": len(values_data)},
        ]
        buffer_dicts: list[Json] = [
            {
                "uri": "data:application/gltf-buffer;base64,"
                + base64.b64encode(base_data).decode("ascii")
            },
            {
                "uri": "data:application/gltf-buffer;base64,"
                + base64.b64encode(indices_data).decode("ascii")
            },
            {
                "uri": "data:application/gltf-buffer;base64,"
                + base64.b64encode(values_data).decode("ascii")
            },
        ]

        result = gltf._read_accessor_as_bytes(
            accessor_dict,
            buffer_view_dicts,
            buffer_dicts,
            None,
        )

        self.assertIsNone(result)

    def test_read_accessor_as_bytes_sparse_out_of_range_indices(self) -> None:
        base_data = b"abcdef"
        indices_data = b"\x02"
        values_data = b"XYZ"

        accessor_dict: dict[str, Json] = {
            "bufferView": 0,
            "type": "VEC3",
            "componentType": 5121,
            "count": 2,
            "sparse": {
                "count": 1,
                "indices": {"bufferView": 1, "componentType": 5121},
                "values": {"bufferView": 2},
            },
        }
        buffer_view_dicts: list[Json] = [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(base_data)},
            {"buffer": 1, "byteOffset": 0, "byteLength": len(indices_data)},
            {"buffer": 2, "byteOffset": 0, "byteLength": len(values_data)},
        ]
        buffer_dicts: list[Json] = [
            {
                "uri": "data:application/gltf-buffer;base64,"
                + base64.b64encode(base_data).decode("ascii")
            },
            {
                "uri": "data:application/gltf-buffer;base64,"
                + base64.b64encode(indices_data).decode("ascii")
            },
            {
                "uri": "data:application/gltf-buffer;base64,"
                + base64.b64encode(values_data).decode("ascii")
            },
        ]

        result = gltf._read_accessor_as_bytes(
            accessor_dict,
            buffer_view_dicts,
            buffer_dicts,
            None,
        )

        self.assertIsNone(result)

    def test_read_accessor_as_bytes_sparse_values_length_mismatch(self) -> None:
        indices_data = b"\x01"
        values_data = b"XY"

        accessor_dict: dict[str, Json] = {
            "type": "VEC3",
            "componentType": 5121,
            "count": 2,
            "sparse": {
                "count": 1,
                "indices": {"bufferView": 0, "componentType": 5121},
                "values": {"bufferView": 1},
            },
        }
        buffer_view_dicts: list[Json] = [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(indices_data)},
            {"buffer": 1, "byteOffset": 0, "byteLength": len(values_data)},
        ]
        buffer_dicts: list[Json] = [
            {
                "uri": "data:application/gltf-buffer;base64,"
                + base64.b64encode(indices_data).decode("ascii")
            },
            {
                "uri": "data:application/gltf-buffer;base64,"
                + base64.b64encode(values_data).decode("ascii")
            },
        ]

        result = gltf._read_accessor_as_bytes(
            accessor_dict,
            buffer_view_dicts,
            buffer_dicts,
            None,
        )

        self.assertIsNone(result)

    def test_merge_duplicate_vertex_skinning_weights(self) -> None:
        joints_bytes = struct.pack("<8B", 1, 1, 2, 3, 4, 5, 4, 6)
        weights_bytes = struct.pack(
            "<8f",
            0.2,
            0.3,
            0.25,
            0.25,
            0.1,
            0.2,
            0.3,
            0.4,
        )
        buffer0_bytes = joints_bytes + weights_bytes

        json_dict: dict[str, Json] = {
            "buffers": [{"byteLength": len(buffer0_bytes)}],
            "bufferViews": [
                {"buffer": 0, "byteOffset": 0, "byteLength": len(joints_bytes)},
                {
                    "buffer": 0,
                    "byteOffset": len(joints_bytes),
                    "byteLength": len(weights_bytes),
                },
            ],
            "accessors": [
                {
                    "bufferView": 0,
                    "componentType": 5121,
                    "count": 2,
                    "type": "VEC4",
                },
                {
                    "bufferView": 1,
                    "componentType": 5126,
                    "count": 2,
                    "type": "VEC4",
                },
            ],
            "meshes": [
                {
                    "primitives": [
                        {"attributes": {"JOINTS_0": 0, "WEIGHTS_0": 1}},
                    ]
                }
            ],
        }

        gltf.merge_duplicate_vertex_skinning_weights(json_dict, buffer0_bytes)

        meshes = _require_json_list(json_dict["meshes"], "meshes")
        mesh_dict = _require_json_dict(meshes[0], "meshes[0]")
        primitive_dicts = _require_json_list(mesh_dict["primitives"], "primitives")
        primitive_dict = _require_json_dict(primitive_dicts[0], "primitives[0]")
        attributes_dict = _require_json_dict(primitive_dict["attributes"], "attributes")

        joints_accessor_index = _require_json_int(
            attributes_dict["JOINTS_0"], "attributes.JOINTS_0"
        )
        weights_accessor_index = _require_json_int(
            attributes_dict["WEIGHTS_0"], "attributes.WEIGHTS_0"
        )

        self.assertEqual(joints_accessor_index, 2)
        self.assertEqual(weights_accessor_index, 3)

        merged_joints_bytes = _read_accessor_buffer_bytes(
            json_dict, joints_accessor_index
        )
        merged_weights_bytes = _read_accessor_buffer_bytes(
            json_dict, weights_accessor_index
        )

        self.assertEqual(
            struct.unpack("<8H", merged_joints_bytes),
            (1, 3, 2, 0, 4, 6, 5, 0),
        )
        merged_weights = struct.unpack("<8f", merged_weights_bytes)
        self.assertAlmostEqual(merged_weights[0], 0.5, places=6)
        self.assertAlmostEqual(merged_weights[1], 0.25, places=6)
        self.assertAlmostEqual(merged_weights[2], 0.25, places=6)
        self.assertAlmostEqual(merged_weights[3], 0.0, places=6)
        self.assertAlmostEqual(merged_weights[4], 0.4, places=6)
        self.assertAlmostEqual(merged_weights[5], 0.4, places=6)
        self.assertAlmostEqual(merged_weights[6], 0.2, places=6)
        self.assertAlmostEqual(merged_weights[7], 0.0, places=6)

    def test_merge_duplicate_vertex_skinning_weights_zero_total_weight(self) -> None:
        joints_bytes = struct.pack("<4B", 1, 1, 2, 3)
        weights_bytes = struct.pack("<4f", 0.0, 0.0, 0.0, 0.0)
        buffer0_bytes = joints_bytes + weights_bytes

        json_dict: dict[str, Json] = {
            "buffers": [{"byteLength": len(buffer0_bytes)}],
            "bufferViews": [
                {"buffer": 0, "byteOffset": 0, "byteLength": len(joints_bytes)},
                {
                    "buffer": 0,
                    "byteOffset": len(joints_bytes),
                    "byteLength": len(weights_bytes),
                },
            ],
            "accessors": [
                {
                    "bufferView": 0,
                    "componentType": 5121,
                    "count": 1,
                    "type": "VEC4",
                },
                {
                    "bufferView": 1,
                    "componentType": 5126,
                    "count": 1,
                    "type": "VEC4",
                },
            ],
            "meshes": [
                {
                    "primitives": [
                        {"attributes": {"JOINTS_0": 0, "WEIGHTS_0": 1}},
                    ]
                }
            ],
        }

        gltf.merge_duplicate_vertex_skinning_weights(json_dict, buffer0_bytes)

        meshes = _require_json_list(json_dict["meshes"], "meshes")
        mesh_dict = _require_json_dict(meshes[0], "meshes[0]")
        primitive_dicts = _require_json_list(mesh_dict["primitives"], "primitives")
        primitive_dict = _require_json_dict(primitive_dicts[0], "primitives[0]")
        attributes_dict = _require_json_dict(primitive_dict["attributes"], "attributes")
        joints_accessor_index = _require_json_int(
            attributes_dict["JOINTS_0"], "attributes.JOINTS_0"
        )
        weights_accessor_index = _require_json_int(
            attributes_dict["WEIGHTS_0"], "attributes.WEIGHTS_0"
        )

        self.assertEqual(
            struct.unpack(
                "<4H", _read_accessor_buffer_bytes(json_dict, joints_accessor_index)
            ),
            (0, 0, 0, 0),
        )
        self.assertEqual(
            struct.unpack(
                "<4f", _read_accessor_buffer_bytes(json_dict, weights_accessor_index)
            ),
            (0.0, 0.0, 0.0, 0.0),
        )

    def test_merge_duplicate_vertex_skinning_weights_multiple_sets(self) -> None:
        joints0_bytes = struct.pack("<4B", 1, 2, 3, 4)
        weights0_bytes = struct.pack("<4B", 25, 25, 25, 25)
        joints1_bytes = struct.pack("<4B", 1, 5, 6, 7)
        weights1_bytes = struct.pack("<4B", 50, 25, 25, 25)
        buffer0_bytes = joints0_bytes + weights0_bytes + joints1_bytes + weights1_bytes

        weights0_offset = len(joints0_bytes)
        joints1_offset = weights0_offset + len(weights0_bytes)
        weights1_offset = joints1_offset + len(joints1_bytes)

        json_dict: dict[str, Json] = {
            "buffers": [{"byteLength": len(buffer0_bytes)}],
            "bufferViews": [
                {"buffer": 0, "byteOffset": 0, "byteLength": len(joints0_bytes)},
                {
                    "buffer": 0,
                    "byteOffset": weights0_offset,
                    "byteLength": len(weights0_bytes),
                },
                {
                    "buffer": 0,
                    "byteOffset": joints1_offset,
                    "byteLength": len(joints1_bytes),
                },
                {
                    "buffer": 0,
                    "byteOffset": weights1_offset,
                    "byteLength": len(weights1_bytes),
                },
            ],
            "accessors": [
                {
                    "bufferView": 0,
                    "componentType": 5121,
                    "count": 1,
                    "type": "VEC4",
                },
                {
                    "bufferView": 1,
                    "componentType": 5121,
                    "count": 1,
                    "normalized": True,
                    "type": "VEC4",
                },
                {
                    "bufferView": 2,
                    "componentType": 5121,
                    "count": 1,
                    "type": "VEC4",
                },
                {
                    "bufferView": 3,
                    "componentType": 5121,
                    "count": 1,
                    "normalized": True,
                    "type": "VEC4",
                },
            ],
            "meshes": [
                {
                    "primitives": [
                        {
                            "attributes": {
                                "JOINTS_0": 0,
                                "WEIGHTS_0": 1,
                                "JOINTS_1": 2,
                                "WEIGHTS_1": 3,
                            }
                        },
                    ]
                }
            ],
        }

        gltf.merge_duplicate_vertex_skinning_weights(json_dict, buffer0_bytes)

        meshes = _require_json_list(json_dict["meshes"], "meshes")
        mesh_dict = _require_json_dict(meshes[0], "meshes[0]")
        primitive_dicts = _require_json_list(mesh_dict["primitives"], "primitives")
        primitive_dict = _require_json_dict(primitive_dicts[0], "primitives[0]")
        attributes_dict = _require_json_dict(primitive_dict["attributes"], "attributes")

        joints0_accessor_index = _require_json_int(
            attributes_dict["JOINTS_0"], "attributes.JOINTS_0"
        )
        weights0_accessor_index = _require_json_int(
            attributes_dict["WEIGHTS_0"], "attributes.WEIGHTS_0"
        )
        joints1_accessor_index = _require_json_int(
            attributes_dict["JOINTS_1"], "attributes.JOINTS_1"
        )
        weights1_accessor_index = _require_json_int(
            attributes_dict["WEIGHTS_1"], "attributes.WEIGHTS_1"
        )

        self.assertEqual(
            struct.unpack(
                "<4H", _read_accessor_buffer_bytes(json_dict, joints0_accessor_index)
            ),
            (1, 7, 6, 5),
        )
        self.assertEqual(
            struct.unpack(
                "<4H", _read_accessor_buffer_bytes(json_dict, joints1_accessor_index)
            ),
            (4, 3, 2, 0),
        )

        weights0 = struct.unpack(
            "<4f", _read_accessor_buffer_bytes(json_dict, weights0_accessor_index)
        )
        weights1 = struct.unpack(
            "<4f", _read_accessor_buffer_bytes(json_dict, weights1_accessor_index)
        )
        for actual, expected in zip(weights0, (1 / 3, 1 / 9, 1 / 9, 1 / 9)):
            self.assertAlmostEqual(actual, expected, places=6)
        for actual, expected in zip(weights1, (1 / 9, 1 / 9, 1 / 9, 0.0)):
            self.assertAlmostEqual(actual, expected, places=6)

    def test_parse_gltf_node_matrix(self) -> None:
        # Default empty dict
        self.assertEqual(gltf.parse_gltf_node_matrix({}), Matrix())

        # Valid matrix (column-major in glTF -> row-major in Blender Matrix)
        node_dict_matrix: dict[str, Json] = {
            "matrix": [
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                1.0,
                2.0,
                3.0,
                1.0,
            ]
        }
        expected_matrix = Matrix(
            (
                (1.0, 0.0, 0.0, 1.0),
                (0.0, 1.0, 0.0, 2.0),
                (0.0, 0.0, 1.0, 3.0),
                (0.0, 0.0, 0.0, 1.0),
            )
        )
        self.assertEqual(gltf.parse_gltf_node_matrix(node_dict_matrix), expected_matrix)

        # Invalid matrix
        self.assertEqual(gltf.parse_gltf_node_matrix({"matrix": [1.0]}), Matrix())
        self.assertEqual(gltf.parse_gltf_node_matrix({"matrix": "invalid"}), Matrix())

        # Valid translation
        node_dict_translation: dict[str, Json] = {"translation": [1.0, 2.0, 3.0]}
        expected_translation = Matrix.Translation((1.0, 2.0, 3.0))
        self.assertEqual(
            gltf.parse_gltf_node_matrix(node_dict_translation), expected_translation
        )

        # Invalid translation
        self.assertEqual(
            gltf.parse_gltf_node_matrix({"translation": [1.0, 2.0]}),
            Matrix(),
        )

        # Valid rotation (glTF: x, y, z, w -> Blender: w, x, y, z)
        node_dict_rotation: dict[str, Json] = {"rotation": [0.0, 1.0, 0.0, 0.0]}
        expected_rotation = Quaternion((0.0, 0.0, 1.0, 0.0)).to_matrix().to_4x4()
        self.assertEqual(
            gltf.parse_gltf_node_matrix(node_dict_rotation), expected_rotation
        )

        # Invalid rotation
        node_dict_rotation_invalid: dict[str, Json] = {"rotation": [0.0, 1.0, 0.0]}
        self.assertEqual(
            gltf.parse_gltf_node_matrix(node_dict_rotation_invalid),
            Matrix(),
        )

        # Valid scale
        node_dict_scale: dict[str, Json] = {"scale": [2.0, 3.0, 4.0]}
        expected_scale = Matrix.Diagonal((2.0, 3.0, 4.0)).to_4x4()
        self.assertEqual(gltf.parse_gltf_node_matrix(node_dict_scale), expected_scale)

        # Invalid scale
        node_dict_invalid_scale: dict[str, Json] = {"scale": [2.0, 3.0]}
        self.assertEqual(gltf.parse_gltf_node_matrix(node_dict_invalid_scale), Matrix())

        # Valid combination of translation, rotation, and scale
        node_dict_combined: dict[str, Json] = {
            "translation": [1.0, 2.0, 3.0],
            "rotation": [0.0, 1.0, 0.0, 0.0],
            "scale": [2.0, 3.0, 4.0],
        }
        expected_combined = expected_translation @ expected_rotation @ expected_scale
        self.assertEqual(
            gltf.parse_gltf_node_matrix(node_dict_combined), expected_combined
        )
