# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import functools
from pathlib import Path

import bpy

from io_scene_vrm.common import ops
from io_scene_vrm.common.logger import get_logger
from tests.util import (
    DEFAULT_TEMP_PATH,
    RESOURCES_BLEND_PATH,
    RESOURCES_PATH,
    AddonTestCase,
    assert_module_state,
    make_test_method_name,
)

_logger = get_logger(__name__)


class __TestVrm1ThirdPartyExportUserExtensionBase(AddonTestCase):
    def assert_export(self, module_root_path: Path) -> None:
        _logger.info("Testing: %s", module_root_path)
        vrm_path = DEFAULT_TEMP_PATH / (
            "test_vrm1_third_party_export_user_extension_"
            + module_root_path.name
            + ".vrm"
        )
        blend_path = RESOURCES_BLEND_PATH / "mtoon1_2_20_61_vrm1.blend"
        with assert_module_state(module_root_path):
            bpy.ops.wm.open_mainfile(filepath=str(blend_path))
            ops.export_scene.vrm(filepath=str(vrm_path))


TestVrm1ThirdPartyExportUserExtension = type(
    "TestVrm1ThirdPartyExportUserExtension",
    (__TestVrm1ThirdPartyExportUserExtensionBase,),
    {
        make_test_method_name(path.stem): functools.partialmethod(
            __TestVrm1ThirdPartyExportUserExtensionBase.assert_export,
            path,
        )
        for path in sorted(
            (RESOURCES_PATH / "third_party_user_extension" / "vrm1_export").glob("*")
        )
        if not path.name.startswith(".") and path.is_dir()
    },
)
