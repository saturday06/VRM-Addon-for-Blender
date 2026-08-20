# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

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
_expected_import_messages: list[str] = ["minimal: " + str(uuid.uuid4())]


def register() -> None:
    _import_messages.clear()


def unregister() -> None:
    pass


def assert_vrm_third_party_user_extension_state() -> None:
    if _import_messages == _expected_import_messages:
        return
    message = (
        "Expected import messages: "
        f"{_expected_import_messages}, "
        f"but got: {_import_messages}"
    )
    raise AssertionError(message)


class Vrm1ImportUserExtension:
    def post_import_hook(
        self,
        _json_dict: Mapping[str, object],
        _buffer0: bytes,
        _armature: Object,
        _node_index_to_object: Mapping[int, Object],
        _node_index_to_bone: Mapping[int, Bone],
        _image_index_to_image: Mapping[int, Image],
        _material_index_to_material: Mapping[int, Material],
        _mesh_index_to_mesh: Mapping[int, Mesh],
    ) -> None:
        _import_messages.extend(_expected_import_messages)
