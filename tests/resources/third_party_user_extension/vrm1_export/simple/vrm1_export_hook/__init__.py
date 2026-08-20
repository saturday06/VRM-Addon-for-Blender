# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import difflib
import re
import uuid
from collections.abc import Mapping
from pathlib import Path
from re import Pattern

import bpy
from bpy.types import Bone, Image, Material, Mesh, Object

from io_scene_vrm.common import gltf
from io_scene_vrm.common.convert import Json

bl_info = {
    "name": "Third Party User Extension Test",
    "author": "saturday06",
    "version": (1, 0, 0),
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
_expected_export_top_message = "simple: " + str(uuid.uuid4())
_expected_export_messages: list[str] = [
    _expected_export_top_message,
    "json_dict=dict",
    "buffer0=bytearray",
    "Armature",
    "node_index_to_object=mappingproxy",
    "  17:Cutout",
    "  18:Opeque",
    "  19:Transparent",
    "  20:TransparentWithZWrite",
    *([] if bpy.app.version >= (4, 2) else ["  22:Armature"]),
    "node_index_to_bone=mappingproxy",
    "  0:head",
    "  1:neck",
    "  2:hand.L",
    "  3:lower_arm.L",
    "  4:upper_arm.L",
    "  5:hand.R",
    "  6:lower_arm.R",
    "  7:upper_arm.R",
    "  8:chest",
    "  9:spine",
    "  10:foot.L",
    "  11:lower_leg.L",
    "  12:upper_leg.L",
    "  13:foot.R",
    "  14:lower_leg.R",
    "  15:upper_leg.R",
    "  16:hips",
    "  21:root",
    "image_index_to_image=mappingproxy",
    "  0:13.png",
    "  1:14.png",
    "  2:15.png",
    "  3:1.png",
    "  4:normal.png",
    "  5:10.png",
    "  6:11.png",
    "  7:12.png",
    "  8:16.png",
    "  9:17.png",
    "  10:19.png",
    "  11:18.png",
    "  12:20.png",
    "  13:3.png",
    "  14:4.png",
    "  15:6.png",
    "  16:5.png",
    "  17:7.png",
    "material_index_to_material=mappingproxy",
    "  0:Cutout",
    "  1:Opaque",
    "  2:Transparent",
    "  3:TransparentWithZWrite",
    "mesh_index_to_mesh=mappingproxy",
    "  0:Cutout",
    "  1:Opaque",
    "  2:Transparent",
    "  3:TransparentWithZWrite",
]

_expected_binary_postfix: bytes = str(uuid.uuid4()).encode() + b".postfix"
_expected_json_extras: Mapping[str, str] = {
    f"hookExtrasKey{uuid.uuid4()}": f"hookExtrasValue{uuid.uuid4()}"
}
_expected_assert_generator_pattern: Pattern[str] = re.compile(
    "^VRM Add-on for Blender v\\d+\\.\\d+\\.\\d+"
    + " with Khronos glTF Blender I/O v\\d+\\.\\d+\\.\\d+"
    + re.escape(" + Third Party User Extension Test 1.0.0")
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
        / "test_vrm1_third_party_export_user_extension_simple.vrm"
    )
    if not vrm_path.exists():
        message = f"Expected VRM file not found at: {vrm_path}"
        raise FileNotFoundError(message)

    json_dict, binary = gltf.parse_glb(vrm_path.read_bytes())
    if not binary.endswith(_expected_binary_postfix):
        message = (
            f"Expected VRM file to end with: {_expected_binary_postfix},"
            " but it did not."
        )
        raise AssertionError(message)

    extras = json_dict.get("extras")
    if extras != _expected_json_extras:
        message = f"Expected extras: {_expected_json_extras}, but got: {extras}"
        raise AssertionError(message)

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

    diff = list(
        difflib.unified_diff(
            _expected_export_messages,
            _export_messages,
            fromfile="expected",
            tofile="actual",
            lineterm="",
        )
    )
    if not diff:
        return
    message = (
        "Expected export messages:\n"
        + "".join(f"  {line}\n" for line in _expected_export_messages)
        + "but got:\n"
        + "".join(f"  {line}\n" for line in _export_messages)
        + "diff:\n"
        + "".join(f"  {line}\n" for line in diff)
    )
    raise AssertionError(message)


class Vrm1ExportUserExtension:
    def pre_save_hook(
        self,
        json_dict: dict[str, Json],
        buffer0: bytearray,
        armature: Object,
        node_index_to_object: Mapping[int, Object],
        node_index_to_bone: Mapping[int, Bone],
        image_index_to_image: Mapping[int, Image],
        material_index_to_material: Mapping[int, Material],
        mesh_index_to_mesh: Mapping[int, Mesh],
    ) -> None:
        json_dict["extras"] = dict(_expected_json_extras)
        buffer0.extend(_expected_binary_postfix)

        _export_messages.append(_expected_export_top_message)
        dump = [
            "json_dict=" + type(json_dict).__name__,
            "buffer0=" + type(buffer0).__name__,
            armature.name,
            "node_index_to_object=" + type(node_index_to_object).__name__,
            *(f"  {k}:{v.name}" for k, v in sorted(node_index_to_object.items())),
            "node_index_to_bone=" + type(node_index_to_bone).__name__,
            *(f"  {k}:{v.name}" for k, v in sorted(node_index_to_bone.items())),
            "image_index_to_image=" + type(image_index_to_image).__name__,
            *(f"  {k}:{v.name}" for k, v in sorted(image_index_to_image.items())),
            "material_index_to_material=" + type(material_index_to_material).__name__,
            *(f"  {k}:{v.name}" for k, v in sorted(material_index_to_material.items())),
            "mesh_index_to_mesh=" + type(mesh_index_to_mesh).__name__,
            *(f"  {k}:{v.name}" for k, v in sorted(mesh_index_to_mesh.items())),
        ]
        _export_messages.extend(dump)
