# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import functools
import shutil
import sys
from os import environ
from pathlib import Path

import bpy

from io_scene_vrm.common import ops
from io_scene_vrm.common.logger import get_logger
from io_scene_vrm.common.test_helper import AddonTestCase
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


class __TestBlendExportBase(AddonTestCase):
    def assert_blend_export(self, blend_path: Path) -> None:
        context = bpy.context

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

        pre_object_names = [obj.name for obj in context.blend_data.objects]
        pre_mesh_names = [mesh.name for mesh in context.blend_data.meshes]
        pre_armature_names = [
            armature.name for armature in context.blend_data.armatures
        ]
        pre_material_names = [
            material.name for material in context.blend_data.materials
        ]

        self.assertEqual(ops.export_scene.vrm(filepath=str(actual_path)), {"FINISHED"})

        post_object_names = [obj.name for obj in context.blend_data.objects]
        post_mesh_names = [mesh.name for mesh in context.blend_data.meshes]
        post_armature_names = [
            armature.name for armature in context.blend_data.armatures
        ]
        post_material_names = [
            material.name for material in context.blend_data.materials
        ]
        self.assertEqual(pre_object_names, post_object_names)
        self.assertEqual(pre_mesh_names, post_mesh_names)
        self.assertEqual(pre_armature_names, post_armature_names)
        self.assertEqual(pre_material_names, post_material_names)

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
