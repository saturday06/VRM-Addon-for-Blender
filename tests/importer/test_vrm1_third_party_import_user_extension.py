# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import functools
from pathlib import Path

from io_scene_vrm.common import ops
from io_scene_vrm.common.logger import get_logger
from tests.util import (
    RESOURCES_PATH,
    RESOURCES_VRM_PATH,
    AddonTestCase,
    assert_module_state,
    make_test_method_name,
)

_logger = get_logger(__name__)


class __TestVrm1ThirdPartyImportUserExtensionBase(AddonTestCase):
    def assert_import(self, module_root_path: Path) -> None:
        _logger.info("Testing: %s", module_root_path)
        vrm_path = (
            RESOURCES_VRM_PATH / "5.2" / "out" / "blend" / "mtoon1_2_20_61_vrm1.vrm"
        )
        with assert_module_state(module_root_path):
            ops.import_scene.vrm(filepath=str(vrm_path))


TestVrm1ThirdPartyImportUserExtension = type(
    "TestVrm1ThirdPartyImportUserExtension",
    (__TestVrm1ThirdPartyImportUserExtensionBase,),
    {
        make_test_method_name(path.stem): functools.partialmethod(
            __TestVrm1ThirdPartyImportUserExtensionBase.assert_import,
            path,
        )
        for path in sorted(
            (RESOURCES_PATH / "third_party_user_extension" / "vrm1_import").glob("*")
        )
        if not path.name.startswith(".") and path.is_dir()
    },
)
