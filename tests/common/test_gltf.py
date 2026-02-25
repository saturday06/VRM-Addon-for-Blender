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
                accessor_dict: dict[str, Json] = {"bufferView": 0}
                buffer_view_dicts: list[Json] = [
                    {"buffer": 0, "byteOffset": 0, "byteLength": len(expected_data)}
                ]
                buffer_dicts: list[Json] = [{"uri": uri}]

                result = gltf.read_accessor_as_bytes(
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
                result = gltf.read_accessor_as_bytes(
                    accessor_dict, buffer_view_dicts, buffer_dicts, None
                )
                self.assertIsNone(result, f"Should have failed for URI: {uri}")
