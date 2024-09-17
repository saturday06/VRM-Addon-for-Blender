# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2018 iCyP

#
#
# - Please don't import anything in the global scope to minimize initialization and
#   support unzipping the partial add-on archive for users who have acquired the add-on
#   from "Code" -> "Download ZIP" on GitHub.
# - Please write this script to work with Blender 2.79.
#   ruff: noqa: UP032
#
#

# Synchronize with https://github.com/saturday06/VRM-Addon-for-Blender/blob/2_20_49/src/io_scene_vrm/common/version.py#L94-L102
bl_info = {
    "name": "VRM format",
    "author": "saturday06, iCyP",
    "version": (2, 20, 86),
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

MAX_SUPPORTED_BLENDER_MAJOR_MINOR_VERSION = (4, 2)


def cleanse_modules() -> None:
    """Search for your plugin modules in blender python sys.modules and remove them.

    To support reload properly, try to access a package var, if it's there,
    reload everything
    """
    import sys

    all_modules = sys.modules
    all_modules = dict(sorted(all_modules.items(), key=lambda x: x[0]))  # sort them

    for k in all_modules:
        if k == __name__ or k.startswith(__name__ + "."):
            del sys.modules[k]


def register() -> None:
    if "bl_info" in globals():
        raise_error_if_too_old_blender()
        extract_github_private_partial_code_archive_if_necessary()

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
    import os

    from . import registration

    registration.unregister()

    # https://github.com/saturday06/VRM-Addon-for-Blender/issues/506#issuecomment-2183766778
    if os.getenv("BLENDER_VRM_DEVELOPMENT_MODE") == "yes":
        cleanse_modules()


def raise_error_if_too_old_blender() -> None:
    import bpy

    minimum_version = bl_info["blender"]
    if not isinstance(minimum_version, tuple) or len(minimum_version) != 3:
        # use 'format()' method to support legacy Blender versions
        message = "Invalid version value: {}".format(minimum_version)
        raise AssertionError(message)

    if bpy.app.version >= minimum_version:
        return

    raise_not_implemented_error(
        default_message=(
            "This add-on doesn't support Blender version less than {minimum_version}"
            + " but the current version is {current_version}"
        ),
        ja_jp_message=(
            "このアドオンはBlenderのバージョン{minimum_version}未満には未対応です。"
            + "お使いのBlenderのバージョンは{current_version}です。"
        ),
    )


def raise_error_if_too_new_blender(exception: object) -> None:
    import bpy

    if bpy.app.version[:2] <= MAX_SUPPORTED_BLENDER_MAJOR_MINOR_VERSION:
        return

    raise_not_implemented_error(
        exception=exception,
        default_message=(
            "This add-on doesn't support Blender version greater than {maximum_version}"
            + " but the current version is {current_version}"
        ),
        ja_jp_message=(
            "このアドオンはBlenderのバージョン{maximum_version}以降には未対応です。"
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
            minimum_version=".".join(map(str, bl_info["blender"])),
            current_version=".".join(map(str, bpy.app.version)),
            maximum_version=".".join(
                map(str, MAX_SUPPORTED_BLENDER_MAJOR_MINOR_VERSION)
            ),
        ),
    )
    if exception is not None:
        highlighted_message = (
            "            Original Exception={exception_name}: {exception}".format(
                exception=exception,
                exception_name=type(exception).__name__,
            )
            + highlighted_message
        )
    raise NotImplementedError(highlighted_message)


def extract_github_private_partial_code_archive_if_necessary() -> None:
    """GitHubの "Code" -> "Download ZIP" からのダウンロードを検知し、ソースを展開する.

    このアドオンは昔GitHubの "Code" -> "Download ZIP" からダウンロードして使う方式を採用
    していた。しかし、そのためにはレポジトリのルートに__init__.pyを配置する必要があり、それだとPythonの標準的な
    ソースコード配置から離れてしまい、開発ツールのサポートが弱くなってしまうのでそのダウンロード方式は廃止した。
    しかし、その昔の廃止した方式でダウンロードしてしまい、結果アドオンがうまく動かないという報告が多数あがるため
    どうにかソースコード配置を変えずに、その方式でも動作するように頑張った結果がこれである。

    この問題はBlender Extensions Platformの登場で解決すると思うのでそれまでは我慢。
    https://code.blender.org/2022/10/blender-extensions-platform/
    """
    import shutil
    import tarfile
    from io import BytesIO
    from logging import getLogger
    from pathlib import Path

    logger = getLogger(__name__)

    # https://github.com/saturday06/VRM-Addon-for-Blender/blob/2_20_33/src/io_scene_vrm/common/logging.py#L35-L38
    log_warning_prefix = "[VRM Add-on:WARNING]"
    log_exception_prefix = "[VRM Add-on:EXCEPTION]"

    github_private_partial_code_archive_path = (
        Path(__file__).parent
        / ".github"
        / "vrm_addon_for_blender_private"
        / ("_".join(map(str, bl_info["version"])) + ".tar.xz")
    )
    if not github_private_partial_code_archive_path.exists():
        return

    logger.warning(
        "%s Extracting the partial add-on archive for "
        "users who have acquired the add-on "
        'from "Code" -> "Download ZIP" on GitHub ...',
        log_warning_prefix,
    )

    with tarfile.open(github_private_partial_code_archive_path, "r:xz") as tar_xz:
        # Will be replaced with tar_xz.extractall(..., filter="data")
        base_path = Path(__file__).parent
        for member in tar_xz.getmembers():
            if ".." in member.path or not member.isfile():
                continue

            member_path = Path(member.path)
            if member_path.is_absolute():
                continue

            file = tar_xz.extractfile(member)
            if not file:
                continue
            with file, BytesIO() as output:
                shutil.copyfileobj(file, output)
                output_bytes = output.getvalue()

            output_path = base_path / member_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(output_bytes)

    try:
        github_private_partial_code_archive_path.unlink()
    except OSError:
        logger.exception(
            "%s Failed to remove the partial add-on archive: %s",
            log_exception_prefix,
            github_private_partial_code_archive_path,
        )

    logger.warning("%s ...OK", log_warning_prefix)


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
