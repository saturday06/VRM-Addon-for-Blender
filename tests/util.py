# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math
import re
import shutil
import subprocess
import sys
from os import environ
from pathlib import Path
from typing import ClassVar, Final, Optional
from unittest import SkipTest, TestCase

import bpy

import io_scene_vrm
from io_scene_vrm.common.blender_manifest import BlenderManifest

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
