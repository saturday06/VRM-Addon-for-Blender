# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import base64
import hashlib
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional
from unittest import SkipTest, TestCase

import bpy
from bpy.types import Camera, Context
from mathutils import Euler

from io_scene_vrm.common import ops


class TestVrmAnimationImporter(TestCase):
    @classmethod
    def base_blend_path(cls) -> Path:
        class_source_hash = (
            base64.urlsafe_b64encode(
                hashlib.sha3_224(Path(__file__).read_bytes()).digest()
            )
            .rstrip(b"=")
            .decode()
        )
        return (
            Path(__file__).parent
            / "temp"
            / (
                cls.__name__
                + "-"
                + "_".join(map(str, bpy.app.version))
                + "-"
                + class_source_hash
                + ".blend"
            )
        )

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        context = bpy.context

        bpy.ops.preferences.addon_enable(module="io_scene_vrm")
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

        cls.add_camera("forward", (0, -4, 1), Euler((math.pi / 2, 0, 0)))
        cls.add_camera("top", (0, 0, 4), Euler((0, 0, 0)))
        cls.add_camera("right", (4, 0, 1), Euler((math.pi / 2, 0, math.pi / 2)))

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

        bpy.ops.wm.save_as_mainfile(filepath=str(cls.base_blend_path()))

    @classmethod
    def add_camera(
        cls,
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

    def assert_vrma_individual_rendering(
        self,
        context: Context,
        input_vrm_path: Path,
        input_vrma_path: Path,
    ) -> None:
        bpy.ops.wm.open_mainfile(filepath=str(self.base_blend_path()))
        self.assertEqual(
            ops.import_scene.vrm(filepath=str(input_vrm_path)),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.import_scene.vrma(filepath=str(input_vrma_path)),
            {"FINISHED"},
        )
        debug_blend_path = (
            Path(__file__).parent
            / "temp"
            / (
                input_vrm_path.stem
                + "-"
                + "_".join(map(str, bpy.app.version))
                + ".vrm.blend"
            )
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
                / (
                    input_vrm_path.stem
                    + "-"
                    + input_vrma_path.stem
                    + f"-{i:02}_{camera_data.name}_blender.png"
                )
            )
            image_path.unlink(missing_ok=True)
            context.scene.render.filepath = str(image_path)
            self.assertEqual(
                bpy.ops.render.render(write_still=True),
                {"FINISHED"},
            )
            unity_image_path = image_path.with_stem(
                image_path.stem.removesuffix("_blender") + "_unity"
            )
            if not unity_image_path.exists():
                continue
            diff_image_path = image_path.with_stem(
                image_path.stem.removesuffix("_blender") + "_diff"
            )
            diff = compare_image(image_path, unity_image_path, diff_image_path)
            self.assertGreater(
                diff,
                1.8,
                "SSIM value exceeds acceptable range:\n"
                + f"  blender={image_path}\n"
                + f"  unity={unity_image_path}\n"
                + f"  diff={diff_image_path}",
            )

    def test_vrma_renderings(self) -> None:
        context = bpy.context

        input_vrm_path = (
            Path(__file__).parent
            / "resources"
            / "unity"
            / "VrmaRecorder"
            / "debug_robot.vrm"
        )

        input_vrma_folder_path = Path(__file__).parent / "resources" / "vrma" / "in"

        for input_vrma_path in sorted(input_vrma_folder_path.glob("*.vrma")):
            with self.subTest([str(input_vrm_path.name), str(input_vrma_path.name)]):
                self.assert_vrma_individual_rendering(
                    context, input_vrm_path, input_vrma_path
                )


def compare_image(image1_path: Path, image2_path: Path, diff_image_path: Path) -> float:
    if subprocess.run(["ffmpeg", "-version"], check=False).returncode != 0:
        message = "ffmpeg is required but could not be found"
        if sys.platform == "win32":
            raise SkipTest(message)
        raise AssertionError(message)

    compare_command: Optional[list[str]] = None
    try:
        if subprocess.run(["magick", "-version"], check=False).returncode == 0:
            compare_command = ["magick", "compare"]
    except FileNotFoundError:
        pass
    if compare_command is None:
        try:
            if subprocess.run(["compare", "-version"], check=False).returncode == 0:
                compare_command = ["compare"]
        except FileNotFoundError:
            pass

    if compare_command is None:
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
        capture_output=True,
    )

    compare_result = subprocess.run(
        [
            "ffmpeg",
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
        check=False,
        capture_output=True,
    )
    last_line = compare_result.stderr.decode().splitlines()[-1].strip()
    ssim_match = re.search(r" SSIM .+\((\d+\.?\d*|inf)\)$", last_line)
    if not ssim_match:
        message = f"Unexpected command output: {last_line}"
        raise ValueError(message)
    ssim_str = ssim_match.group(1)
    if ssim_str == "inf":
        return math.inf
    return float(ssim_str)
