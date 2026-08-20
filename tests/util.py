# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math
import re
import shutil
import subprocess
import sys
from collections.abc import Generator
from contextlib import contextmanager
from os import environ
from pathlib import Path
from typing import ClassVar, Final, Optional
from unittest import SkipTest, TestCase

import bpy

import io_scene_vrm
from io_scene_vrm.common.blender_manifest import BlenderManifest
from io_scene_vrm.common.logger import get_logger

_logger = get_logger(__name__)


DEVELOPMENT_MODULE: Final = io_scene_vrm.__name__
MANIFEST_ID: Final = BlenderManifest.read().id
TEST_METHOD_NAME_ESCAPE_CHAR: Final = "\N{MODIFIER LETTER PRIME}"
TEST_METHOD_NAME_SPECIAL_REPLACEMENTS: Final = {
    " ": "\N{MODIFIER LETTER LOW MACRON}",
    ".": "\N{MODIFIER LETTER LOW VERTICAL LINE}",
    "-": "\N{MODIFIER LETTER HALF TRIANGULAR COLON}",
    "(": "\N{MODIFIER LETTER SMALL R}",
    ")": "\N{MODIFIER LETTER SMALL TURNED R}",
}
REPOSITORY_ROOT_PATH: Final = Path(__file__).resolve(strict=True).parent.parent
RESOURCES_PATH: Final = Path(
    environ.get(
        "BLENDER_VRM_TEST_RESOURCES_PATH",
        str(REPOSITORY_ROOT_PATH / "tests" / "resources"),
    )
)

BLENDER_MAJOR_MINOR_VERSION: Final = f"{bpy.app.version[0]}.{bpy.app.version[1]}"
RESOURCES_VRM_PATH: Final = RESOURCES_PATH / "vrm"
RESOURCES_BLEND_PATH: Final = RESOURCES_PATH / "blend"
DEFAULT_TEMP_PATH: Final = REPOSITORY_ROOT_PATH / ".local" / "tmp"


def make_test_method_name(text: str) -> str:
    special_chars = [
        TEST_METHOD_NAME_ESCAPE_CHAR,
        *TEST_METHOD_NAME_SPECIAL_REPLACEMENTS.values(),
    ]
    if not all(char.isidentifier() for char in special_chars):
        message = f"{special_chars} contains non identifier"
        raise AssertionError(message)
    if len(set(special_chars)) != len(special_chars):
        message = f"{special_chars} contains duplicates"
        raise AssertionError(message)

    test_method_name = "test_"
    for char in text:
        replacement_char = TEST_METHOD_NAME_SPECIAL_REPLACEMENTS.get(char)
        if replacement_char is not None:
            test_method_name = f"{test_method_name}{replacement_char}"
            continue

        if char in special_chars:
            test_method_name = f"{test_method_name}{char}{char}"
            continue

        appended_test_method_name = f"{test_method_name}{char}"
        if appended_test_method_name.isidentifier():
            test_method_name = appended_test_method_name
            continue

        test_method_name = (
            test_method_name
            + TEST_METHOD_NAME_ESCAPE_CHAR
            + f"{ord(char):x}"
            + TEST_METHOD_NAME_ESCAPE_CHAR
        )

    if not test_method_name.isidentifier():
        message = f"Cannot convert to test method name: {text}"
        raise ValueError(message)

    return test_method_name


class AddonTestCase(TestCase):
    _disabled_installed_module: ClassVar[Optional[str]] = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls._disabled_installed_module = None
        for addon in bpy.context.preferences.addons:
            module = addon.module
            if not module.endswith("." + MANIFEST_ID):
                continue
            bpy.ops.preferences.addon_disable(module=module)
            cls._disabled_installed_module = module

    def setUp(self) -> None:
        super().setUp()
        bpy.ops.preferences.addon_enable(module=DEVELOPMENT_MODULE)
        bpy.ops.wm.read_homefile(use_empty=True)

    def tearDown(self) -> None:
        super().tearDown()
        bpy.ops.preferences.addon_disable(module=DEVELOPMENT_MODULE)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

        disabled_installed_module = cls._disabled_installed_module
        if disabled_installed_module is not None:
            bpy.ops.preferences.addon_enable(module=disabled_installed_module)

        cls._disabled_installed_module = None


def compare_image(image1_path: Path, image2_path: Path, diff_image_path: Path) -> float:
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        message = "ffmpeg is required but could not be found"
        if sys.platform == "win32":
            raise SkipTest(message)
        raise AssertionError(message)

    compare_command: Optional[list[str]] = None
    if magick_path := shutil.which("magick"):
        compare_command = [magick_path, "compare"]
    elif compare_path := shutil.which("compare"):
        compare_command = [compare_path]
    else:
        message = "ImageMagick is required but could not be found"
        if sys.platform == "win32":
            raise SkipTest(message)
        raise AssertionError(message)

    subprocess.run(
        [
            *compare_command,
            str(image1_path),
            str(image2_path),
            str(diff_image_path),
        ],
        check=False,
    )

    compare_result = subprocess.run(
        [
            ffmpeg_path,
            "-hide_banner",
            "-nostats",
            "-i",
            str(image1_path),
            "-i",
            str(image2_path),
            "-filter_complex",
            "ssim",
            "-f",
            "null",
            "-",
        ],
        check=True,
        capture_output=True,
    )
    pattern = r" SSIM .+\((\d+\.?\d*|inf)\)$"
    for line in reversed(compare_result.stderr.decode().splitlines()):
        ssim_match = re.search(pattern, line.strip())
        if not ssim_match:
            continue
        ssim_str = ssim_match.group(1)
        if ssim_str == "inf":
            return math.inf
        return float(ssim_str)

    message = (
        f"SSIM value not found in command output pattern={pattern}\n"
        + compare_result.stderr.decode()
    )
    raise ValueError(message)


@contextmanager
def assert_module_state(module_root_path: Path) -> Generator[None, None, None]:
    _logger.info("Testing: %s", module_root_path)

    module_names: list[str] = [
        module_path.relative_to(module_root_path).as_posix().replace("/", ".")
        for module_path in sorted(module_root_path.glob("**"))
        if (module_path / "blender_manifest.toml").exists()
    ]
    if bpy.app.version < (4, 2) and any(
        "." in module_name for module_name in module_names
    ):
        message = "Blender version < 4.2 does not support nested modules"
        raise SkipTest(message)

    module_root_path_str = str(module_root_path)
    if module_root_path_str in sys.path:
        message = f"{module_root_path_str} is already in sys.path"
        raise AssertionError(message)

    enabled_module_names: list[str] = []
    sys.path.insert(0, module_root_path_str)
    try:
        try:
            for module_name in module_names:
                result = bpy.ops.preferences.addon_enable(module=module_name)
                if result != {"FINISHED"}:
                    message = f"Failed to enable addon: {module_name}, result: {result}"
                    raise AssertionError(message)
                enabled_module_names.append(module_name)

            yield

            for module_name in module_names:
                module = sys.modules.get(module_name)
                if not module:
                    message = f"Module not found in sys.modules: {module_name}"
                    raise AssertionError(message)
                assert_vrm_third_party_user_extension_state = getattr(
                    module,
                    "assert_vrm_third_party_user_extension_state",
                    None,
                )
                if assert_vrm_third_party_user_extension_state is None:
                    message = (
                        "Module.assert_vrm_third_party_user_extension_state"
                        f" not found: {module_name}"
                    )
                    raise AttributeError(message)
                if not callable(assert_vrm_third_party_user_extension_state):
                    message = (
                        "Module.assert_vrm_third_party_user_extension_state"
                        f" is not callable: {module_name}"
                    )
                    raise TypeError(message)
                assert_vrm_third_party_user_extension_state()
        finally:
            for module_name in reversed(enabled_module_names):
                result = bpy.ops.preferences.addon_disable(module=module_name)
                if result != {"FINISHED"}:
                    message = (
                        f"Failed to disable addon: {module_name}, result: {result}"
                    )
                    raise AssertionError(message)
    finally:
        sys.path.remove(module_root_path_str)

        module_root_path_resolved = module_root_path.resolve()
        for name, module in list(sys.modules.items()):
            module_file = getattr(module, "__file__", None)
            if not isinstance(module_file, str):
                continue
            module_file_path = Path(module_file).resolve()
            if (
                module_root_path_resolved == module_file_path
                or module_root_path_resolved in module_file_path.parents
            ):
                sys.modules.pop(name, None)
