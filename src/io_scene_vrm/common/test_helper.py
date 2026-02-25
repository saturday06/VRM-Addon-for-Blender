# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import Final, Optional
from unittest import TestCase

import bpy

from .blender_manifest import BlenderManifest

DEVELOPMENT_MODULE: Final = ".".join(__name__.split(".")[:-2])
MANIFEST_ID: Final = BlenderManifest.read().id
ESCAPE_CHAR: Final = "\N{MODIFIER LETTER PRIME}"
SPECIAL_REPLACEMENTS: Final = {
    " ": "\N{MODIFIER LETTER LOW MACRON}",
    ".": "\N{MODIFIER LETTER LOW VERTICAL LINE}",
    "-": "\N{MODIFIER LETTER HALF TRIANGULAR COLON}",
}


def make_test_method_name(text: str) -> str:
    special_chars = [ESCAPE_CHAR, *SPECIAL_REPLACEMENTS.values()]
    if not all(char.isidentifier() for char in special_chars):
        message = f"{special_chars} contains non identifier"
        raise AssertionError(message)

    test_method_name = "test_"
    for char in text:
        replacement_char = SPECIAL_REPLACEMENTS.get(char)
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

        test_method_name = f"{test_method_name}{ESCAPE_CHAR}{ord(char):x}{ESCAPE_CHAR}"

    if not test_method_name.isidentifier():
        message = f"Cannot convert to test method name: {text}"
        raise ValueError(message)

    return test_method_name


class AddonTestCase(TestCase):
    disabled_installed_module: Optional[str]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.disabled_installed_module = None
        for addon in bpy.context.preferences.addons:
            module = addon.module
            if not module.endswith("." + MANIFEST_ID):
                continue
            bpy.ops.preferences.addon_disable(module=module)
            cls.disabled_installed_module = module

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

        disabled_installed_module = cls.disabled_installed_module
        if disabled_installed_module is not None:
            bpy.ops.preferences.addon_enable(module=disabled_installed_module)

        cls.disabled_installed_module = None
