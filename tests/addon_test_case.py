# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import TestCase

import bpy

MODULE = "io_scene_vrm"


class AddonTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bpy.ops.preferences.addon_enable(module=MODULE)

    def setUp(self) -> None:
        super().setUp()
        bpy.ops.wm.read_homefile(use_empty=True)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        bpy.ops.preferences.addon_disable(module=MODULE)
