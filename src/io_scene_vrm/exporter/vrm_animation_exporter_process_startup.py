# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
"""VRMAエクスポート用のBlenderプロセスで実行されるスクリプトです."""

import os
from typing import Final

import bpy

EXPORT_ADDON_MODULE_NAME_ENV_KEY: Final = "BLENDER_VRM_ADDON_MODULE_NAME"


def main() -> None:
    # VRMアドオンはデフォルトで無効の場合もあるため、有効化する。
    addon_module_name = os.getenv(EXPORT_ADDON_MODULE_NAME_ENV_KEY)
    if not addon_module_name:
        message = f"Environment variable not set: {EXPORT_ADDON_MODULE_NAME_ENV_KEY}"
        raise RuntimeError(message)
    addon_enable_result = bpy.ops.preferences.addon_enable(module=addon_module_name)
    if addon_enable_result != {"FINISHED"}:
        message = f'Failed to enable "{addon_module_name}": {addon_enable_result}'
        raise RuntimeError(message)

    # VRMAファイルのエクスポートを実行する。
    # モジュールの相対インポートができず型安全にできないため "type: ignore" を付与する
    export_vrma_result = bpy.ops.vrm.export_vrma()  # type: ignore[attr-defined]
    if export_vrma_result != {"FINISHED"}:
        message = f"Failed to export VRM Animation: {export_vrma_result}"
        raise RuntimeError(message)


if __name__ == "__main__":
    main()
