# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import difflib
import uuid
from collections.abc import Mapping

from bpy.types import Bone, Image, Material, Mesh, Object

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

_import_messages: list[str] = []
_expected_import_top_message = "simple: " + str(uuid.uuid4())
_expected_import_messages: list[str] = [
    _expected_import_top_message,
    "json_dict=mappingproxy",
    "buffer0=bytes",
    "Armature",
    "node_index_to_object=mappingproxy",
    "  17:Cutout",
    "  18:Opeque",
    "  19:Transparent",
    "  20:TransparentWithZWrite",
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


def register() -> None:
    _import_messages.clear()


def unregister() -> None:
    pass


def assert_vrm_third_party_user_extension_state() -> None:
    diff = list(
        difflib.unified_diff(
            _expected_import_messages,
            _import_messages,
            fromfile="expected",
            tofile="actual",
            lineterm="",
        )
    )
    if not diff:
        return
    message = (
        "Expected import messages:\n"
        + "".join(f"  {line}\n" for line in _expected_import_messages)
        + "but got:\n"
        + "".join(f"  {line}\n" for line in _import_messages)
        + "diff:\n"
        + "".join(f"  {line}\n" for line in diff)
    )
    raise AssertionError(message)


class Vrm1ImportUserExtension:
    def post_import_hook(
        self,
        json_dict: Mapping[str, object],
        buffer0: bytes,
        armature: Object,
        node_index_to_object: Mapping[int, Object],
        node_index_to_bone: Mapping[int, Bone],
        image_index_to_image: Mapping[int, Image],
        material_index_to_material: Mapping[int, Material],
        mesh_index_to_mesh: Mapping[int, Mesh],
    ) -> None:
        _import_messages.append(_expected_import_top_message)
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
        _import_messages.extend(dump)
