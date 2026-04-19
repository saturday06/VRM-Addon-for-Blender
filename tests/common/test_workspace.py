# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from pathlib import Path
from unittest import TestCase

import bpy

from io_scene_vrm.common import workspace


class TestWorkspace(TestCase):
    def setUp(self) -> None:
        bpy.ops.wm.read_homefile(use_empty=True)

    def test_save_workspace_restores_cursor(self) -> None:
        context = bpy.context
        initial_matrix = context.scene.cursor.matrix.copy()

        with workspace.save_workspace(context):
            context.scene.cursor.matrix[0][3] += 1.0

        self.assertEqual(context.scene.cursor.matrix, initial_matrix)

    def test_save_workspace_restores_active_object(self) -> None:
        context = bpy.context
        bpy.ops.mesh.primitive_cube_add()
        obj1 = context.active_object
        if obj1 is None:
            self.fail("Failed to create test object 1")
        obj1.name = "obj1"

        bpy.ops.mesh.primitive_cube_add()
        obj2 = context.active_object
        if obj2 is None:
            self.fail("Failed to create test object 2")
        obj2.name = "obj2"

        context.view_layer.objects.active = obj1

        with workspace.save_workspace(context, obj2):
            self.assertEqual(context.active_object, obj2)

        self.assertEqual(context.active_object, obj1)

    def test_save_workspace_restores_mode(self) -> None:
        context = bpy.context
        bpy.ops.mesh.primitive_cube_add()
        obj = context.active_object
        if obj is None:
            self.fail("Failed to create test object")

        bpy.ops.object.mode_set(mode="EDIT")
        initial_mode = obj.mode

        with workspace.save_workspace(context, mode="OBJECT"):
            self.assertEqual(obj.mode, "OBJECT")

        self.assertEqual(obj.mode, initial_mode)

    def test_save_workspace_handles_hide_viewport(self) -> None:
        context = bpy.context
        bpy.ops.mesh.primitive_cube_add()
        obj = context.active_object
        if obj is None:
            self.fail("Failed to create test object")

        obj.hide_viewport = True

        # Normally mode_set fails if hide_viewport is True and it's not in OBJECT mode.
        # But workspace.py handles this.
        with workspace.save_workspace(context, mode="EDIT"):
            self.assertEqual(obj.mode, "EDIT")

        self.assertEqual(obj.mode, "OBJECT")
        self.assertEqual(obj.hide_viewport, True)

    def test_wm_append_without_library_removes_library(self) -> None:
        context = bpy.context

        # We need a blend file to append from.
        # We can use one of the existing test resources.
        resource_dir = Path(__file__).parent.parent / "resources" / "blend"
        blend_path = resource_dir / "basic_armature.blend"

        if not blend_path.exists():
            self.skipTest(f"{blend_path} not found")

        initial_libraries = list(bpy.data.libraries)
        blend_path_str = str(blend_path)

        # Append an object from the blend file
        result = workspace.wm_append_without_library(
            context,
            blend_path,
            append_filepath=blend_path_str + "/Object/Armature",
            append_filename="Armature",
            append_directory=blend_path_str + "/Object",
        )

        self.assertEqual(result, {"FINISHED"})

        # Check that the object was actually appended
        self.assertIn("Armature", bpy.data.objects)

        if bpy.app.version < (3, 0):
            self.skipTest(
                "Blender 2.x may not remove libraries properly, "
                "skipping library removal check"
            )

        # Check that the library was removed
        self.assertEqual(list(bpy.data.libraries), initial_libraries)

    def test_wm_append_without_library_handles_failure(self) -> None:
        context = bpy.context

        initial_libraries = list(bpy.data.libraries)

        # Try to append with invalid arguments. Depending on Blender version and
        # failure mode, this may either raise RuntimeError or return a non-finished
        # operator result such as {"CANCELLED"}.
        result = None
        try:
            result = workspace.wm_append_without_library(
                context,
                Path("/non/existent.blend"),
                append_filepath="/non/existent.blend/Object/None",
                append_filename="None",
                append_directory="/non/existent.blend/Object",
            )
        except RuntimeError:
            pass
        else:
            self.assertNotEqual(result, {"FINISHED"})

        self.assertEqual(list(bpy.data.libraries), initial_libraries)
