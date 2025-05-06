# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import base64
import hashlib
import math
from pathlib import Path
from unittest import TestCase

import bpy
from bpy.types import Camera
from mathutils import Euler

from io_scene_vrm.common import ops


class TestVrmAnimationImporter(TestCase):
    def setUp(self) -> None:
        super().setUp()

        context = bpy.context

        bpy.ops.preferences.addon_enable(module="io_scene_vrm")

        class_source_hash = (
            base64.urlsafe_b64encode(
                hashlib.sha3_224(Path(__file__).read_bytes()).digest()
            )
            .rstrip(b"=")
            .decode()
        )

        cached_blend_path = (
            Path(__file__).parent
            / "temp"
            / (
                type(self).__name__
                + "-"
                + "_".join(map(str, bpy.app.version))
                + "-"
                + class_source_hash
                + ".blend"
            )
        )
        if cached_blend_path.exists():
            bpy.ops.wm.open_mainfile(filepath=str(cached_blend_path))
            return

        if context.view_layer.objects.active:
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()
        while context.blend_data.collections:
            context.blend_data.collections.remove(context.blend_data.collections[0])
        bpy.ops.outliner.orphans_purge(do_recursive=True)

        scene = context.scene
        scene.view_settings.view_transform = "Standard"
        scene.world.use_nodes = False
        scene.world.color[0] = 0
        scene.world.color[1] = 0
        scene.world.color[2] = 0

        self.add_camera("forward", (0, -4, 1), Euler((math.pi / 2, 0, 0)))
        self.add_camera("top", (0, 0, 4), Euler((0, 0, 0)))
        self.add_camera("right", (4, 0, 1), Euler((math.pi / 2, 0, math.pi / 2)))

        resolution = 512
        scene.render.resolution_x = resolution
        scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        scene.render.engine = "CYCLES"
        scene.cycles.samples = 1
        scene.cycles.adaptive_min_samples = 1
        scene.cycles.use_denoising = False
        scene.cycles.use_adaptive_sampling = False

        bpy.ops.wm.save_as_mainfile(filepath=str(cached_blend_path))

    def add_camera(
        self,
        name: str,
        location: tuple[float, float, float],
        rotation_euler: Euler,
    ) -> None:
        bpy.ops.object.camera_add(location=location)
        camera_object = bpy.context.object
        if not camera_object:
            raise TypeError
        camera_object.name = name
        camera_object.rotation_mode = "XYZ"
        camera_object.rotation_euler = rotation_euler

        camera_data = camera_object.data
        if not isinstance(camera_data, Camera):
            raise TypeError

        camera_data.name = name
        camera_data.type = "ORTHO"
        camera_data.ortho_scale = 2

    def test_visual_regression(self) -> None:
        context = bpy.context

        self.assertEqual(
            ops.import_scene.vrm(
                filepath=str(
                    Path(__file__).parent
                    / "resources"
                    / "unity"
                    / "VrmaRecorder"
                    / "debug_robot.vrm"
                )
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.import_scene.vrma(
                filepath=str(
                    Path(__file__).parent / "resources" / "vrma" / "in" / "nop.vrma"
                )
            ),
            {"FINISHED"},
        )
        debug_blend_path = (
            Path(__file__).parent
            / "temp"
            / ("nop-" + "_".join(map(str, bpy.app.version)) + ".vrm.blend")
        )
        debug_blend_path.unlink(missing_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(debug_blend_path))

        for camera_object in context.blend_data.objects:
            camera_data = camera_object.data
            if not isinstance(camera_data, Camera):
                continue
            context.scene.camera = camera_object

            i = 0
            image_path = (
                Path(__file__).parent
                / "temp"
                / f"nop_{i:02}_{camera_data.name}_blender.png"
            )
            image_path.unlink(missing_ok=True)
            context.scene.render.filepath = str(image_path)
            self.assertEqual(
                bpy.ops.render.render(write_still=True),
                {"FINISHED"},
            )
