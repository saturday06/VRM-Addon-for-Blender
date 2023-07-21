"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

#
#
# Please don't import anything in the global scope to minimize initialization and
# support unzipping the partial add-on archive for users who have acquired the add-on
# from "Code" -> "Download ZIP" on GitHub.
#
#

bl_info = {
    "name": "VRM format",
    "author": "saturday06, iCyP",
    "version": (2, 17, 7),
    "blender": (2, 93, 0),
    "location": "File > Import-Export",
    "description": "Import-Edit-Export VRM",
    "warning": "",
    "support": "COMMUNITY",
    "wiki_url": "",
    "doc_url": "https://vrm-addon-for-blender.info",
    "tracker_url": "https://github.com/saturday06/VRM-Addon-for-Blender/issues",
    "category": "Import-Export",
}


def register() -> None:
    raise_error_if_current_blender_is_not_supported()
    extract_github_private_partial_code_archive_if_necessary()

    # Lazy import to minimize initialization before blender version checking and
    # support unzipping the partial add-on archive.
    from . import registration

    registration.register(bl_info["version"])


def unregister() -> None:
    import bpy

    if bpy.app.version < bl_info["blender"]:
        return

    # Lazy import to minimize initialization before blender version checking.
    from . import registration

    registration.unregister()


def raise_error_if_current_blender_is_not_supported() -> None:
    import bpy

    if bpy.app.version >= bl_info["blender"]:
        return

    default_message = (
        "This add-on doesn't support Blender version less than {minimum_version}"
        + " but the current version is {current_version}"
    )
    translated_messages = {
        "ja_JP": (
            "このアドオンはBlenderのバージョン{minimum_version}未満には未対応です。"
            + "お使いのBlenderのバージョンは{current_version}です。"
        ),
    }

    if (
        bpy.app.version >= (2, 80)
        and bpy.context.preferences.view.use_translate_interface
    ):
        message = translated_messages.get(bpy.app.translations.locale, default_message)
    else:
        message = default_message

    raise NotImplementedError(
        # pylint: disable=consider-using-f-string; for legacy Blender versions
        """

        ===========================================================
        {}
        ===========================================================
        """.format(
            message.format(
                minimum_version=".".join(map(str, bl_info["blender"])),
                current_version=".".join(map(str, bpy.app.version)),
            )
        )
    )


def extract_github_private_partial_code_archive_if_necessary() -> None:
    """GitHubの "Code" -> "Download ZIP" からのダウンロードを検知し、足りないソースコードを展開する。

    このアドオンは昔GitHubの "Code" -> "Download ZIP" からダウンロードして使う方式を採用していた。
    しかし、そのためにはレポジトリのルートに__init__.pyを配置する必要があり、それだとPythonの標準的な
    ソースコード配置から離れてしまい、開発ツールのサポートが弱くなってしまうのでそのダウンロード方式は廃止した。
    しかし、その昔の廃止した方式でダウンロードしてしまい、結果アドオンがうまく動かないという報告が多数あがるため
    どうにかソースコード配置を変えずに、その方式でも動作するように頑張った結果がこれである。

    この問題はBlender Extensions Platformの登場で解決すると思うのでそれまでは我慢。
    https://code.blender.org/2022/10/blender-extensions-platform/
    """

    import tarfile
    from logging import getLogger
    from pathlib import Path

    logger = getLogger(__name__)

    # https://github.com/saturday06/VRM-Addon-for-Blender/blob/2_5_0/io_scene_vrm/common/logging.py#L5-L7
    log_warning_prefix = "[VRM Add-on:Warning]"

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
        'users who have acquired the add-on from "Code" -> "Download ZIP" on GitHub ...',
        log_warning_prefix,
    )

    with tarfile.open(github_private_partial_code_archive_path, "r:xz") as tar_xz:
        for member in tar_xz.getmembers():
            if ".." in member.path or not (member.isfile() or member.isdir()):
                continue
            path = Path(member.path)
            if path.is_absolute():
                continue
            tar_xz.extract(member=member, path=Path(__file__).parent, set_attrs=False)

    try:
        github_private_partial_code_archive_path.unlink()
    except OSError:
        logger.exception(
            "%s Failed to remove the partial add-on archive: %s",
            log_warning_prefix,
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


if __name__ == "__main__":
    register()
