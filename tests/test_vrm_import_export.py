# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import functools
import shutil
import sys
from os import environ
from pathlib import Path
from unittest import TestCase

import bpy

from io_scene_vrm.common import ops
from io_scene_vrm.common.logger import get_logger
from io_scene_vrm.importer.vrm_diff import vrm_diff

logger = get_logger(__name__)

repository_root_dir = Path(__file__).resolve(strict=True).parent.parent
resources_dir = Path(
    environ.get(
        "BLENDER_VRM_TEST_RESOURCES_PATH",
        str(repository_root_dir / "tests" / "resources"),
    )
)
major_minor = f"{bpy.app.version[0]}.{bpy.app.version[1]}"
vrm_dir = resources_dir / "vrm"
blend_dir = resources_dir / "blend"


class __TestVrmImportExportBase(TestCase):
    def assert_vrm_import_export(
        self, in_path: Path, *, extract_textures: bool
    ) -> None:
        context = bpy.context

        environ["BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION"] = "true"
        environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"
        update_failed_vrm = environ.get("BLENDER_VRM_TEST_UPDATE_FAILED_VRM") == "true"

        out_vrm_dir = vrm_dir / major_minor / "out"
        temp_vrm_dir = vrm_dir / major_minor / "temp"
        temp_vrm_dir.mkdir(parents=True, exist_ok=True)

        # 非公開のテストモデルの中に特定のBlenderバージョンで
        # 出力結果が不安定なものがある
        if f"(unstable-{major_minor})" in in_path.name:
            logger.warning("Skipped: %s", in_path)
            return

        if context.view_layer.objects.active:
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()
        while context.blend_data.collections:
            context.blend_data.collections.remove(context.blend_data.collections[0])
        bpy.ops.outliner.orphans_purge(do_recursive=True)

        ops.import_scene.vrm(
            filepath=str(in_path),
            extract_textures_into_folder=extract_textures,
            make_new_texture_folder=extract_textures,
        )

        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

        actual_path = temp_vrm_dir / (
            f"test_import_export.{extract_textures}." + in_path.name
        )
        if actual_path.exists():
            actual_path.unlink()

        ops.export_scene.vrm(filepath=str(actual_path))
        actual_bytes = actual_path.read_bytes()

        float_tolerance = 0.00055

        expected_path = out_vrm_dir / in_path.name
        if not expected_path.exists():
            update_failed_vrm = True
            expected_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(actual_path, expected_path)

        diffs = vrm_diff(
            actual_bytes,
            expected_path.read_bytes(),
            float_tolerance,
        )
        if not diffs:
            return

        if update_failed_vrm:
            shutil.copy(actual_path, expected_path)

        diffs_str = "\n".join(diffs)
        message = (
            f"Exceeded the VRM diff threshold:{float_tolerance:19.17f}\n"
            + f"input={in_path}\n"
            + f"left ={actual_path}\n"
            + f"right={expected_path}\n"
            + f"{diffs_str}\n"
        )
        if sys.platform == "win32":
            sys.stderr.buffer.write(message.encode())
            raise AssertionError
        raise AssertionError(message)


TestVrmImportExport = type(
    "TestVrmImportExport",
    (__TestVrmImportExportBase,),
    {
        "test_" + path.stem: functools.partialmethod(
            __TestVrmImportExportBase.assert_vrm_import_export,
            path,
            extract_textures=extract_textures,
        )
        for path in sorted((vrm_dir / "in").glob("*.vrm"))
        for extract_textures in [False, True]
    },
)
