"""エクスポート用のBlenderプロセスで実行されるスクリプトです."""

import os
from typing import Final

import bpy

EXPORT_ADDON_MODULE_NAME_ENV_KEY: Final = "BLENDER_VRM_ADDON_MODULE_NAME"


def main() -> None:
    addon_module_name = os.getenv(EXPORT_ADDON_MODULE_NAME_ENV_KEY)
    if not addon_module_name:
        message = f"Environment variable not set: {EXPORT_ADDON_MODULE_NAME_ENV_KEY}"
        raise RuntimeError(message)

    if bpy.ops.preferences.addon_enable(module=addon_module_name) != {"FINISHED"}:
        message = f"Failed to enable: {addon_module_name}"
        raise RuntimeError(message)

    # モジュールの相対インポートができず型安全にできないため "type: ignore" を付与する
    if bpy.ops.vrm.export_vrm() != {"FINISHED"}:  # type: ignore[attr-defined]
        message = "Failed to export VRM"
        raise RuntimeError(message)


if __name__ == "__main__":
    main()
