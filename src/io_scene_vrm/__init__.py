# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
# SPDX-FileCopyrightText: 2018 iCyP

#
#
# - Please avoid importing anything in the global scope to minimize initialization and
#   support unzipping the partial add-on archive for users who downloaded the add-on
#   from "Code" -> "Download ZIP" on GitHub.
# - Ensure this script works with Blender 2.79.
#   ruff: noqa: UP032
#
#

bl_info = {
    "name": "VRM format",
    "author": "saturday06, iCyP",
    "version": (
        3,  # x-release-please-major
        9,  # x-release-please-minor
        2,  # x-release-please-patch
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

MINIMUM_UNSUPPORTED_BLENDER_MAJOR_MINOR_VERSION = (5, 0)


def register() -> None:
    if "bl_info" in globals():
        raise_error_if_too_old_blender()

    # Lazy import to minimize initialization before blender version checking and
    # support unzipping the partial add-on archive.
    try:
        from . import registration

        registration.register()
    except ImportError as exception:
        if "bl_info" in globals():
            raise_error_if_too_new_blender(exception)
        raise


def unregister() -> None:
    # Lazy import to minimize initialization before blender version checking.
    from . import registration

    registration.unregister()


def raise_error_if_too_old_blender() -> None:
    import bpy

    minimum_supported_version = bl_info["blender"]
    if (
        not isinstance(minimum_supported_version, tuple)
        or len(minimum_supported_version) != 3
    ):
        # use 'format()' method to support legacy Blender versions
        message = "Invalid version value: {}".format(minimum_supported_version)
        raise AssertionError(message)

    if bpy.app.version >= minimum_supported_version:
        return

    raise_not_implemented_error(
        default_message=(
            "This add-on requires Blender version {minimum_supported_version} or later."
            + " Your current version is {current_version}."
        ),
        ja_jp_message=(
            "このアドオンはBlenderのバージョン{minimum_supported_version}未満には未対応です。"
            + "お使いのBlenderのバージョンは{current_version}です。"
        ),
    )


def raise_error_if_too_new_blender(exception: object) -> None:
    import bpy

    if bpy.app.version[:2] < MINIMUM_UNSUPPORTED_BLENDER_MAJOR_MINOR_VERSION:
        return

    raise_not_implemented_error(
        exception=exception,
        default_message=(
            "This add-on is not compatible with Blender version"
            + " {minimum_unsupported_version} or later. Your current version is"
            + " {current_version}."
        ),
        ja_jp_message=(
            "このアドオンはBlenderのバージョン{minimum_unsupported_version}以降には未対応です。"
            + "お使いのBlenderのバージョンは{current_version}です。"
        ),
    )


def raise_not_implemented_error(
    *, exception: object = None, default_message: str, ja_jp_message: str
) -> None:
    import bpy

    context = bpy.context

    translated_messages = {
        "ja_JP": ja_jp_message,
    }

    if bpy.app.version >= (2, 80) and context.preferences.view.use_translate_interface:
        message = translated_messages.get(bpy.app.translations.locale, default_message)
    else:
        message = default_message

    # use 'format()' method to support legacy Blender versions
    highlighted_message = """

            ===========================================================
            {message}
            ===========================================================
        """.format(
        message=message.format(
            minimum_supported_version=".".join(map(str, bl_info["blender"])),
            current_version=".".join(map(str, bpy.app.version)),
            minimum_unsupported_version=".".join(
                map(str, MINIMUM_UNSUPPORTED_BLENDER_MAJOR_MINOR_VERSION)
            ),
        ),
    )
    if exception is not None:
        highlighted_message = (
            "            Original Exception: {exception_name}: {exception}".format(
                exception=exception,
                exception_name=type(exception).__name__,
            )
            + highlighted_message
        )
    raise NotImplementedError(highlighted_message)


class glTF2ImportUserExtension:
    def __init__(self) -> None:
        # Lazy import to minimize initialization.
        from .importer.gltf2_addon_importer_user_extension import (
            Gltf2AddonImporterUserExtension,
        )

        self.user_extension = Gltf2AddonImporterUserExtension()

    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/6f9d0d9fc1bb30e2b0bb019342ffe86bd67358fc/addons/io_scene_gltf2/blender/imp/gltf2_blender_image.py#L51
    def gather_import_image_after_hook(
        self, img: object, blender_image: object, gltf_importer: object
    ) -> None:
        self.user_extension.gather_import_image_after_hook(
            img, blender_image, gltf_importer
        )


class glTF2ExportUserExtension:
    def __init__(self) -> None:
        # Lazy import to minimize initialization.
        from .exporter.gltf2_addon_exporter_user_extension import (
            Gltf2AddonExporterUserExtension,
        )

        self.user_extension = Gltf2AddonExporterUserExtension()

    # 3 arguments in Blender 2.93.0
    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/709630548cdc184af6ea50b2ff3ddc5450bc0af3/addons/io_scene_gltf2/blender/exp/gltf2_blender_export.py#L68
    # 5 arguments in Blender 3.6.0
    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/78c9556942e0780b471c9985e83e39e8c8d8f85a/addons/io_scene_gltf2/blender/exp/gltf2_blender_export.py#L84
    def gather_gltf_hook(
        self, a: object, b: object, c: object = None, d: object = None
    ) -> None:
        self.user_extension.gather_gltf_hook(a, b, c, d)


if __name__ == "__main__":
    register()
