# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import re
import uuid
from collections.abc import Mapping
from pathlib import Path
from re import Pattern

from bpy.types import Bone, Image, Material, Mesh, Object

from io_scene_vrm.common import gltf

bl_info = {
    "name": "Third Party User Extension Test 3",
    "author": "saturday06",
    "version": (1, 0, 3),
    "location": "File > Import-Export",
    "description": "Test add-on",
    "blender": (2, 93, 0),
    "warning": "",
    "support": "COMMUNITY",
    "wiki_url": "",
    "doc_url": "https://vrm-addon-for-blender.info",
    "tracker_url": "https://github.com/saturday06/VRM-Addon-for-Blender/issues",
    "category": "Import-Export",
}

_export_messages: list[str] = []
_expected_export_messages: list[str] = ["multi 3: " + str(uuid.uuid4())]
_expected_assert_generator_pattern: Pattern[str] = re.compile(
    "^VRM Add-on for Blender v\\d+\\.\\d+\\.\\d+"
    + " with Khronos glTF Blender I/O v\\d+\\.\\d+\\.\\d+"
    + re.escape(
        " + Third Party User Extension Test 1 1.0.1"
        + " + Third Party User Extension Test 2 1.0.2"
        + " + Third Party User Extension Test 3 1.0.3"
    )
    + "$"
)


def register() -> None:
    _export_messages.clear()


def unregister() -> None:
    pass


def assert_vrm_third_party_user_extension_state() -> None:
    vrm_path = (
        Path(__file__).parent.parent.parent.parent.parent.parent.parent
        / ".local"
        / "tmp"
        / "test_vrm1_third_party_export_user_extension_multi.vrm"
    )
    if not vrm_path.exists():
        message = f"Expected VRM file not found at: {vrm_path}"
        raise FileNotFoundError(message)

    json_dict, _ = gltf.parse_glb(vrm_path.read_bytes())

    asset = json_dict.get("asset")
    if not isinstance(asset, dict):
        message = "Expected 'asset' field in JSON, but it was not found."
        raise TypeError(message)
    asset_generator = asset.get("generator")
    if not isinstance(asset_generator, str):
        message = (
            "Expected 'generator' field in 'asset' to be a string, but it was not."
        )
        raise TypeError(message)
    if not _expected_assert_generator_pattern.match(asset_generator):
        message = (
            f"Expected asset generator: {_expected_assert_generator_pattern.pattern}"
            + f", but got: {asset_generator}"
        )
        raise AssertionError(message)

    if _export_messages == _expected_export_messages:
        return
    message = (
        "Expected export messages: "
        f"{_expected_export_messages}, "
        f"but got: {_export_messages}"
    )
    raise AssertionError(message)


class Vrm1ExportUserExtension:
    def pre_save_hook(
        self,
        _json_dict: dict[str, object],
        _buffer0: bytearray,
        _armature: Object,
        _node_index_to_object: Mapping[int, Object],
        _node_index_to_bone: Mapping[int, Bone],
        _image_index_to_image: Mapping[int, Image],
        _material_index_to_material: Mapping[int, Material],
        _mesh_index_to_mesh: Mapping[int, Mesh],
    ) -> None:
        _export_messages.extend(_expected_export_messages)
