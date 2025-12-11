# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import Optional
from unittest import TestCase

import bpy

from .blender_manifest import BlenderManifest

DEVELOPMENT_MODULE = ".".join(__name__.split(".")[:-2])
MANIFEST_ID = BlenderManifest.read().id


def make_test_method_name(text: str) -> str:
    replaced_chars: list[str] = []
    for char in text:
        if char in ["⟨", "⟩"]:
            replaced_chars.append(char * 2)
        elif ("_" + char).isidentifier():
            replaced_chars.append(char)
        else:
            replaced_chars.append(f"⟨{ord(char):x}⟩")
    return "test_" + ("".join(replaced_chars))


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
