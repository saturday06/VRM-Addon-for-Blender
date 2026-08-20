# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import uuid

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
_expected_export_messages: list[str] = ["too few args: " + str(uuid.uuid4())]


def register() -> None:
    _export_messages.clear()


def unregister() -> None:
    pass


def assert_vrm_third_party_user_extension_state() -> None:
    if _export_messages == _expected_export_messages:
        return
    message = (
        "Expected export messages: "
        f"{_expected_export_messages}, "
        f"but got: {_export_messages}"
    )
    raise AssertionError(message)


class Vrm1ExportUserExtension:
    def pre_save_hook(self) -> None:
        _export_messages.extend(_expected_export_messages)
