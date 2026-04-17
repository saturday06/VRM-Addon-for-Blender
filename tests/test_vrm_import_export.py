# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import functools
import shutil
import sys
from os import environ
from pathlib import Path

import bpy

from io_scene_vrm.common import ops
from io_scene_vrm.common.logger import get_logger
from io_scene_vrm.importer.vrm_diff import vrm_diff
from tests.util import (
    BLENDER_MAJOR_MINOR_VERSION,
    RESOURCES_VRM_PATH,
    AddonTestCase,
    make_test_method_name,
)

_logger = get_logger(__name__)


class __TestVrmImportExportBase(AddonTestCase):
    def assert_vrm_import_export(
        self, in_path: Path, *, extract_textures: bool
    ) -> None:
        context = bpy.context
        environ["BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION"] = "true"
        environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"
        update_failed_vrm = environ.get("BLENDER_VRM_TEST_UPDATE_FAILED_VRM") == "true"

        out_vrm_dir = RESOURCES_VRM_PATH / BLENDER_MAJOR_MINOR_VERSION / "out"
        temp_vrm_dir = RESOURCES_VRM_PATH / BLENDER_MAJOR_MINOR_VERSION / "temp"
        temp_vrm_dir.mkdir(parents=True, exist_ok=True)

        # Some private test models have unstable output results
        # on specific Blender versions
        if f"(unstable-{BLENDER_MAJOR_MINOR_VERSION})" in in_path.name:
            _logger.warning("Skipped: %s", in_path)
            return

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

        actual_bytes = actual_path.read_bytes()

        float_tolerance = 0.00055

        expected_path = out_vrm_dir / in_path.name
        if not expected_path.exists():
            update_failed_vrm = True
            expected_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src=actual_path, dst=expected_path)

        diffs = vrm_diff(
            actual_bytes,
            expected_path.read_bytes(),
            float_tolerance,
        )
        if not diffs:
            return

        if update_failed_vrm:
            shutil.copy(src=actual_path, dst=expected_path)

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
        make_test_method_name(path.stem): functools.partialmethod(
            __TestVrmImportExportBase.assert_vrm_import_export,
            path,
            extract_textures=extract_textures,
        )
        for path in sorted((RESOURCES_VRM_PATH / "in").glob("*.vrm"))
        for extract_textures in (False, True)
    },
)
