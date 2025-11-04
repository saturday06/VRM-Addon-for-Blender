# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from unittest import main

import bpy
from bpy.types import Mesh

from io_scene_vrm.common.test_helper import AddonTestCase
from io_scene_vrm.editor.extension import get_material_extension
from io_scene_vrm.editor.mtoon1.scene_watcher import OutlineUpdater, RunState


class TestOutlineUpdater(AddonTestCase):
    def test_outline_material_auto_duplication(self) -> None:
        context = bpy.context
        self.assertEqual(bpy.ops.mesh.primitive_cube_add(), {"FINISHED"})
        obj = context.active_object
        if obj is None:
            raise AssertionError
        mesh_data = obj.data
        if not isinstance(mesh_data, Mesh):
            raise TypeError

        material1 = bpy.data.materials.new(name="MToonMaterial1")
        mesh_data.materials.append(material1)
        ext1 = get_material_extension(material1)
        ext1.mtoon1.enabled = True
        mtoon = ext1.mtoon1.extensions.vrmc_materials_mtoon
        mtoon.outline_width_factor = 0.005
        mtoon.outline_width_mode = mtoon.OUTLINE_WIDTH_MODE_WORLD_COORDINATES.identifier

        if bpy.app.version < (3, 3):
            return

        self.assertIsNotNone(ext1.mtoon1.outline_material)

        material2 = material1.copy()
        mesh_data.materials.append(material2)
        ext2 = get_material_extension(material2)
        self.assertEqual(ext1.mtoon1.outline_material, ext2.mtoon1.outline_material)

        outline_updater = OutlineUpdater()
        while outline_updater.run(context) == RunState.PREEMPT:
            pass

        self.assertNotEqual(ext1.mtoon1.outline_material, ext2.mtoon1.outline_material)

    def test_outline_material_auto_rename(self) -> None:
        context = bpy.context
        self.assertEqual(bpy.ops.mesh.primitive_cube_add(), {"FINISHED"})
        obj = context.active_object
        if obj is None:
            raise AssertionError
        mesh_data = obj.data
        if not isinstance(mesh_data, Mesh):
            raise TypeError

        material = bpy.data.materials.new(name="MToonMaterial")
        mesh_data.materials.append(material)
        ext = get_material_extension(material)
        ext.mtoon1.enabled = True
        mtoon = ext.mtoon1.extensions.vrmc_materials_mtoon
        mtoon.outline_width_factor = 0.005
        mtoon.outline_width_mode = mtoon.OUTLINE_WIDTH_MODE_WORLD_COORDINATES.identifier

        if bpy.app.version < (3, 3):
            return

        outline_material = ext.mtoon1.outline_material
        if outline_material is None:
            raise AssertionError
        self.assertEqual(outline_material.name, "MToon Outline (MToonMaterial)")

        material.name = "Renamed"
        outline_updater = OutlineUpdater()
        while outline_updater.run(context) == RunState.PREEMPT:
            pass

        outline_material = ext.mtoon1.outline_material
        if outline_material is None:
            raise AssertionError
        self.assertEqual(outline_material.name, "MToon Outline (Renamed)")


if __name__ == "__main__":
    main()
