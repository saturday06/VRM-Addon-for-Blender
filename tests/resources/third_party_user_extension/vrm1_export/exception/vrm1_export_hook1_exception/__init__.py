# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import uuid
from collections.abc import Mapping

from bpy.types import Bone, Image, Material, Mesh, Object

from io_scene_vrm.common.third_party_user_extension import (
    _logger as third_party_user_extension_logger,
)

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

_error_message = "Expected test exception " + str(uuid.uuid4())


def register() -> None:
    third_party_user_extension_logger.clear_log_output_match_count()
    third_party_user_extension_logger.register_log_output_match(_error_message)


def unregister() -> None:
    pass


def assert_vrm_third_party_user_extension_state() -> None:
    count = third_party_user_extension_logger.get_log_output_match_count(_error_message)
    third_party_user_extension_logger.clear_log_output_match_count()
    if count == 1:
        return
    message = (
        f"'{_error_message}' should be logged once, but it was logged {count} times."
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
        raise RuntimeError(_error_message)
