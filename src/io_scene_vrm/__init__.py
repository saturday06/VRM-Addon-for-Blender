# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
# SPDX-FileCopyrightText: 2018 iCyP

from . import registration
from .exporter import gltf2_export_user_extension
from .importer import gltf2_import_user_extension

bl_info = {
    "name": "VRM format",
    "author": "saturday06, iCyP",
    "version": (
        3,  # x-release-please-major
        14,  # x-release-please-minor
        0,  # x-release-please-patch
    ),
    "location": "File > Import-Export",
    "description": "Import-Edit-Export VRM",
    "blender": (2, 93, 0),
    "warning": "",
    "support": "COMMUNITY",
    "wiki_url": "",
    "doc_url": "https://vrm-addon-for-blender.info",
    "tracker_url": "https://github.com/saturday06/VRM-Addon-for-Blender/issues",
    "category": "Import-Export",
}


def register() -> None:
    registration.register()


def unregister() -> None:
    registration.unregister()


class glTF2ImportUserExtension(gltf2_import_user_extension.glTF2ImportUserExtension):
    pass


class glTF2ExportUserExtension(gltf2_export_user_extension.glTF2ExportUserExtension):
    pass
