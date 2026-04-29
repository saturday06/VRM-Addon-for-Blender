# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import base64
from unittest import TestCase

from io_scene_vrm.common import gltf
from io_scene_vrm.common.convert import Json


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
