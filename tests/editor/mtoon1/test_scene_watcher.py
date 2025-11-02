# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from unittest import main

import bpy

from io_scene_vrm.common.test_helper import AddonTestCase
from io_scene_vrm.editor.extension import get_material_extension


class TestOutlineUpdater(AddonTestCase):
    def test_outline_material_auto_duplication(self) -> None:
        context = bpy.context
        self.assertEqual(bpy.ops.mesh.primitive_cube_add(), {"FINISHED"})
        obj = context.active_object
        self.assertIsNotNone(obj)
        material1 = bpy.data.materials.new(name="MToonMaterial1")
        ext1 = get_material_extension(material1)
        ext1.mtoon1.enabled = True
        mtoon = ext1.mtoon1.extensions.vrmc_materials_mtoon
        mtoon.outline_width_factor = 0.005
        mtoon.outline_width_mode = mtoon.OUTLINE_WIDTH_MODE_WORLD_COORDINATES.identifier
        material2 = material1.copy()
        _ext2 = get_material_extension(material2)


if __name__ == "__main__":
    main()
