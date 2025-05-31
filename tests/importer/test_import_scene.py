# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import functools
import shutil
import sys
from os import environ
from pathlib import Path
from unittest import TestCase, main

import bpy

from io_scene_vrm.common import ops
from io_scene_vrm.common.debug import clean_scene
from io_scene_vrm.common.logger import get_logger
from io_scene_vrm.importer.vrm_diff import vrm_diff

logger = get_logger(__name__)

repository_root_dir = Path(__file__).resolve(strict=True).parent.parent.parent
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


class __TestBlendExportBase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        bpy.ops.preferences.addon_enable(module="io_scene_vrm")

    def assert_blend_export(self, blend_path: Path) -> None:
        environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"
        update_failed_vrm = environ.get("BLENDER_VRM_TEST_UPDATE_FAILED_VRM") == "true"
        enable_second_export = not environ.get("BLENDER_VRM_TEST_RESOURCES_PATH")

        if blend_path.name.endswith(".merge.blend"):
            blend_path = blend_path.with_suffix("").with_suffix(".blend")
        expected_path = (
            vrm_dir / major_minor / "out" / "blend" / (blend_path.stem + ".vrm")
        )

        if Path(expected_path.with_suffix(expected_path.suffix + ".disabled")).exists():
            return

        temp_vrm_dir = vrm_dir / major_minor / "temp"
        temp_vrm_dir.mkdir(parents=True, exist_ok=True)

        bpy.ops.wm.open_mainfile(filepath=str(blend_path))

        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

        actual_path = temp_vrm_dir / ("test_blend_export." + expected_path.name)
        if actual_path.exists():
            actual_path.unlink()

        actual_second_path = temp_vrm_dir / (
            "test_blend_export.2nd." + expected_path.name
        )
        if actual_second_path.exists():
            actual_second_path.unlink()

        self.assertEqual(ops.export_scene.vrm(filepath=str(actual_path)), {"FINISHED"})
        if enable_second_export:
            self.assertEqual(
                ops.export_scene.vrm(filepath=str(actual_second_path)), {"FINISHED"}
            )

        if not expected_path.exists():
            message = f"No expected result file: {expected_path}"
            raise FileNotFoundError(message)

        self.vrm_bin_diff(
            blend_path,
            actual_path,
            expected_path,
            "Whether the export result is correct",
            update_failed_vrm=update_failed_vrm,
        )

        if enable_second_export:
            self.vrm_bin_diff(
                blend_path,
                actual_second_path,
                expected_path,
                "The results of multiple exports are the same",
                update_failed_vrm=False,
            )

    def vrm_bin_diff(
        self,
        in_path: Path,
        actual_path: Path,
        expected_path: Path,
        what: str,
        *,
        update_failed_vrm: bool,
    ) -> None:
        float_tolerance = 0.00015

        diffs = vrm_diff(
            actual_path.read_bytes(),
            expected_path.read_bytes(),
            float_tolerance,
        )
        if not diffs:
            return

        if update_failed_vrm:
            shutil.copy(actual_path, expected_path)

        diffs_str = "\n".join(diffs)
        message = (
            f"{what}\n"
            + f"Exceeded the VRM diff threshold:{float_tolerance:19.17f}\n"
            + f"input={in_path}\n"
            + f"left ={actual_path}\n"
            + f"right={expected_path}\n"
            + f"{diffs_str}\n"
        )
        if sys.platform == "win32":
            sys.stderr.buffer.write(message.encode())
            raise AssertionError
        raise AssertionError(message)


TestBlendExport = type(
    "TestBlendExport",
    (__TestBlendExportBase,),
    {
        "test_" + path.stem: functools.partialmethod(
            __TestBlendExportBase.assert_blend_export, path
        )
        for path in sorted(
            list(blend_dir.glob("*.blend"))
            + list((blend_dir / major_minor).glob("*.blend"))
        )
    },
)


class __TestImportSceneBrokenVrmBase(TestCase):
    def setUp(self) -> None:
        bpy.ops.preferences.addon_enable(module="io_scene_vrm")
        clean_scene(bpy.context)

    def assert_broken_vrm(self, vrm_path: Path) -> None:
        environ["BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION"] = "true"

        if (
            vrm_path.name == "draco.vrm"
            and sys.platform == "linux"
            and not bpy.app.binary_path
        ):
            # Linuxかつmoduleとしてビルドされている場合、dracoのライブラリが読めなくて
            # エラーになるので該当するテストは実施しない
            return

        self.assertEqual(ops.import_scene.vrm(filepath=str(vrm_path)), {"FINISHED"})


TestImportSceneBrokenVrm = type(
    "TestImportSceneBrokenVrm",
    (__TestImportSceneBrokenVrmBase,),
    {
        "test_" + path.stem: functools.partialmethod(
            __TestImportSceneBrokenVrmBase.assert_broken_vrm, path
        )
        for path in sorted((resources_dir / "vrm" / "broken").glob("*.vrm"))
    },
)

if __name__ == "__main__":
    main()
