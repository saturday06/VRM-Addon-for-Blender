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
    "version": (2, 15, 22),
    "blender": (2, 83, 0),
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
    import zipfile
    from logging import getLogger
    from pathlib import Path

    import bpy

    logger = getLogger(__name__)

    if bpy.app.version < bl_info["blender"]:
        message = (
            "This add-on doesn't support Blender version less than {minimum_version}"
            + " but the current version is {current_version}"
        )
        if (
            bpy.app.version >= (2, 80)
            and bpy.context.preferences.view.use_translate_interface
            and bpy.app.translations.locale == "ja_JP"
        ):
            message = (
                "このアドオンはBlenderのバージョン{minimum_version}未満には未対応です。"
                + "お使いのBlenderのバージョンは{current_version}です。"
            )
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

    # https://github.com/saturday06/VRM-Addon-for-Blender/blob/2_5_0/io_scene_vrm/common/logging.py#L5-L7
    log_warning_prefix = "[VRM Add-on:Warning]"

    # For users who have acquired the add-on from "Code" -> "Download ZIP" on GitHub.
    github_code_download_zip_path = (
        Path(__file__).parent
        / ".github"
        / "vrm_addon_for_blender_private"
        / ("_".join(map(str, bl_info["version"])) + ".zip")
    )
    if github_code_download_zip_path.exists():
        # github_code_download_zip_pathにファイルが存在する場合、それに含まれているソースコードを展開する。
        #
        # このアドオンは昔GitHubの "Code" -> "Download ZIP" からダウンロードして使う方式を採用していた。
        # しかし、そのためにはレポジトリのルートに__init__.pyを配置する必要があり、それだとPythonの標準的な
        # ソースコード配置から離れてしまい、開発ツールのサポートが弱くなってしまうのでそのダウンロード方式は廃止した。
        # しかし、その昔の廃止した方式でダウンロードしてしまい、結果アドオンがうまく動かないという報告が多数あがるため
        # どうにかソースコード配置を変えずに、その方式でも動作するように頑張った結果がこれである。
        #
        # この問題はBlender Extensions Platformの登場で解決すると思うのでそれまでは我慢。
        # https://code.blender.org/2022/10/blender-extensions-platform/

        logger.warning(
            "%s Unzipping the partial add-on archive for "
            'users who have acquired the add-on from "Code" -> "Download ZIP" on GitHub ...',
            log_warning_prefix,
        )

        with zipfile.ZipFile(github_code_download_zip_path, "r") as z:
            z.extractall(Path(__file__).parent)

        try:
            github_code_download_zip_path.unlink()
        except OSError:
            logger.exception(
                "%s Failed to remove the partial add-on archive: %s",
                log_warning_prefix,
                github_code_download_zip_path,
            )

        logger.warning("%s ...OK", log_warning_prefix)

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
