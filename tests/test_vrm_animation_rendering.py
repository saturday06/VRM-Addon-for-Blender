# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import base64
import functools
import hashlib
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Final, Optional
from unittest import SkipTest

import bpy
from bpy.types import Armature, Camera, Context
from mathutils import Color, Euler, Vector

from io_scene_vrm.common import ops
from io_scene_vrm.editor.extension import get_armature_extension
from io_scene_vrm.editor.search import current_armature
from io_scene_vrm.editor.vrm1.property_group import Vrm1LookAtPropertyGroup

from .addon_test_case import AddonTestCase


class __TestVrmAnimationRenderingBase(AddonTestCase):
    OBJECT_SUFFIX: Final[str] = "-TestVrmAnimationRenderingObject"
    OBJECT_DATA_SUFFIX: Final[str] = "-TestVrmAnimationRenderingObjectData"

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        context = bpy.context

        bpy.ops.wm.read_homefile(use_empty=True)
        cls.init_scene(context)
        bpy.ops.wm.save_as_mainfile(filepath=str(cls.base_blend_path()))

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
    def init_scene(cls, context: Context) -> None:
        scene = context.scene

        for obj in scene.collection.objects:
            if obj.type in ["CAMERA", "LIGHT"]:
                obj.hide_render = True
                obj.hide_viewport = True

        scene.view_settings.view_transform = "Standard"
        world = scene.world
        if not world:
            world = context.blend_data.worlds.new(name="World")
            scene.world = world
        world.use_nodes = False
        world.color[0] = 0
        world.color[1] = 0
        world.color[2] = 0

        cls.add_camera(
            context,
            "ForwardCamera",
            "forward",
            Vector((0, -4, 1)),
            Euler((math.pi / 2, 0, 0)),
        )
        cls.add_camera(
            context,
            "TopCamera",
            "top",
            Vector((0, 0, 4)),
            Euler((0, 0, 0)),
        )
        cls.add_camera(
            context,
            "RightCamera",
            "right",
            Vector((4, 0, 1)),
            Euler((math.pi / 2, 0, math.pi / 2)),
        )

        resolution = 256
        scene.render.resolution_x = resolution
        scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        scene.render.engine = "CYCLES"
        scene.eevee.taa_render_samples = 1
        scene.cycles.samples = 1
        scene.cycles.adaptive_min_samples = 1
        scene.cycles.use_denoising = False
        scene.cycles.use_adaptive_sampling = False

        light_data = context.blend_data.lights.new(
            name="Light" + cls.OBJECT_DATA_SUFFIX, type="SUN"
        )
        light_data.color = Color((1.0, 1.0, 1.0))
        light_object = context.blend_data.objects.new(
            name="Light" + cls.OBJECT_SUFFIX, object_data=light_data
        )
        light_object.location = Vector((0, -8, 0))
        light_object.rotation_mode = "XYZ"
        light_object.rotation_euler = Euler((math.pi / 2, 0, 0))

        scene.collection.objects.link(light_object)

    @classmethod
    def add_camera(
        cls,
        context: Context,
        object_name: str,
        object_data_name: str,
        location: Vector,
        rotation_euler: Euler,
    ) -> None:
        camera_data = context.blend_data.cameras.new(
            name=object_data_name + cls.OBJECT_DATA_SUFFIX
        )
        camera_data.type = "ORTHO"
        camera_data.ortho_scale = 2

        camera_object = context.blend_data.objects.new(
            name=object_name + cls.OBJECT_SUFFIX, object_data=camera_data
        )
        camera_object.location = location
        camera_object.rotation_mode = "XYZ"
        camera_object.rotation_euler = rotation_euler

        context.scene.collection.objects.link(camera_object)

    def assert_rendering(
        self, context: Context, render_folder_path: Path, *, suffix: str = ""
    ) -> None:
        render_blend_path = render_folder_path.with_name(
            render_folder_path.stem + f".render{suffix}.blend"
        )
        bpy.ops.wm.save_as_mainfile(filepath=str(render_blend_path))
        scene = context.scene

        max_end_frame: int = 1
        for obj in context.blend_data.objects:
            obj_data = obj.data
            if not isinstance(obj_data, Armature):
                continue

            if (animation_data := obj.animation_data) and (
                action := animation_data.action
            ):
                _, end_frame = action.frame_range
                max_end_frame = max(max_end_frame, math.ceil(end_frame))

            if (animation_data := obj_data.animation_data) and (
                action := animation_data.action
            ):
                _, end_frame = action.frame_range
                max_end_frame = max(max_end_frame, math.ceil(end_frame))

            ext = get_armature_extension(obj_data)
            ext.spring_bone1.enable_animation = True
            ext.vrm1.look_at.enable_preview = True
            look_at_target_obj = ext.vrm1.look_at.preview_target_bpy_object
            if (
                look_at_target_obj
                and (animation_data := look_at_target_obj.animation_data)
                and (action := animation_data.action)
            ):
                _, end_frame = action.frame_range
                max_end_frame = max(max_end_frame, math.ceil(end_frame))
        max_end_frame = min(
            max_end_frame,
            math.ceil(60 * scene.render.fps / scene.render.fps_base),
        )

        render_folder_path.mkdir(parents=True, exist_ok=True)
        last_render_time = None
        render_results = list[list[tuple[float, Path, Path, Path]]]()
        for frame_count in range(1, max_end_frame):
            scene.frame_set(frame_count)
            Vrm1LookAtPropertyGroup.update_all_previews(context)

            time = (frame_count - 1) * scene.render.fps_base / scene.render.fps
            if (
                last_render_time is not None
                and last_render_time + 1 > time
                and frame_count + 1 != max_end_frame
            ):
                continue

            last_render_time = time
            last_render_result = list[tuple[float, Path, Path, Path]]()

            for camera_object in context.blend_data.objects:
                if not camera_object.name.endswith(self.OBJECT_SUFFIX):
                    continue
                camera_data = camera_object.data
                if not isinstance(camera_data, Camera):
                    continue
                if not camera_data.name.endswith(self.OBJECT_DATA_SUFFIX):
                    continue
                context.scene.camera = camera_object

                blender_suffix = f"_blender{suffix}"
                image_path = render_folder_path / (
                    f"{len(render_results):02}_"
                    + camera_data.name.removesuffix(self.OBJECT_DATA_SUFFIX)
                    + f"{blender_suffix}.png"
                )
                image_path.unlink(missing_ok=True)

                context.scene.render.filepath = str(image_path)
                self.assertEqual(
                    bpy.ops.render.render(write_still=True),
                    {"FINISHED"},
                )

                unity_image_path = image_path.with_stem(
                    image_path.stem.removesuffix(blender_suffix) + "_unity"
                )
                if not unity_image_path.exists():
                    continue
                diff_image_path = image_path.with_stem(
                    image_path.stem.removesuffix(blender_suffix) + f"{suffix}_diff"
                )
                diff = compare_image(image_path, unity_image_path, diff_image_path)
                last_render_result.append(
                    (diff, image_path, unity_image_path, diff_image_path)
                )

            render_results.append(last_render_result)

        for diff, image_path, unity_image_path, diff_image_path in sum(
            render_results, list[tuple[float, Path, Path, Path]]()
        ):
            self.assertGreater(
                diff,
                1.8,
                "SSIM value exceeds acceptable range:\n"
                + f"  blender={image_path}\n"
                + f"  unity={unity_image_path}\n"
                + f"  diff={diff_image_path}",
            )

    def assert_vrma_rendering(
        self,
        context: Context,
        input_vrm_path: Path,
        input_vrma_path: Path,
        *,
        suffix: str = "",
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
        self.assert_rendering(context, input_vrma_path.with_suffix(""), suffix=suffix)

    def assert_import(self, input_vrma_path: Path) -> None:
        context = bpy.context

        default_input_vrm_path = (
            Path(__file__).parent
            / "resources"
            / "unity"
            / "VrmaRecorder"
            / "debug_robot.vrm"
        )

        input_vrm_path = input_vrma_path.with_suffix(".vrm")
        if not input_vrm_path.exists():
            input_vrm_path = default_input_vrm_path
        self.assert_vrma_rendering(context, input_vrm_path, input_vrma_path)

    def assert_blend_rendering(
        self, context: Context, input_blend_path: Path, *, lossless: bool
    ) -> None:
        bpy.ops.wm.open_mainfile(filepath=str(input_blend_path))
        self.init_scene(context)

        vrm_path = input_blend_path.with_suffix(".vrm")
        current_armature_object = current_armature(context)
        if not current_armature_object:
            message = "No armature object found"
            raise AssertionError(message)
        armature_object_name = current_armature_object.name
        self.assertEqual(
            ops.export_scene.vrm(
                filepath=str(vrm_path), armature_object_name=armature_object_name
            ),
            {"FINISHED"},
        )

        vrma_path = input_blend_path.with_suffix(".vrma")
        self.assertEqual(
            ops.export_scene.vrma(
                filepath=str(vrma_path), armature_object_name=armature_object_name
            ),
            {"FINISHED"},
        )

        if lossless:
            self.assert_rendering(context, input_blend_path.with_suffix(""))

        self.assert_vrma_rendering(context, vrm_path, vrma_path, suffix="_roundtrip")

    def assert_lossless_export(self, input_blend_path: Path) -> None:
        context = bpy.context

        if input_blend_path.name.endswith(
            ".render.blend"
        ) or input_blend_path.name.endswith(".render_roundtrip.blend"):
            return

        self.assert_blend_rendering(
            context,
            input_blend_path,
            lossless=True,
        )

    def assert_lossy_export(self, input_blend_path: Path) -> None:
        context = bpy.context

        if input_blend_path.name.endswith(
            ".render.blend"
        ) or input_blend_path.name.endswith(".render_roundtrip.blend"):
            return

        self.assert_blend_rendering(
            context,
            input_blend_path,
            lossless=False,
        )


TestVrmAnimationImport = type(
    "TestVrmAnimationImport",
    (__TestVrmAnimationRenderingBase,),
    {
        "test_" + path.stem: functools.partialmethod(
            __TestVrmAnimationRenderingBase.assert_import, path
        )
        for path in sorted(
            (Path(__file__).parent / "resources" / "vrma").glob("*.vrma")
        )
    },
)

TestVrmAnimationLosslessExport = type(
    "TestVrmAnimationLosslessExport",
    (__TestVrmAnimationRenderingBase,),
    {
        "test_" + path.stem: functools.partialmethod(
            __TestVrmAnimationRenderingBase.assert_lossless_export, path
        )
        for path in sorted(
            (Path(__file__).parent / "resources" / "blend" / "lossless_animation").glob(
                "*.blend"
            )
        )
    },
)

TestVrmAnimationLossyExport = type(
    "TestVrmAnimationLossyExport",
    (__TestVrmAnimationRenderingBase,),
    {
        "test_" + path.stem: functools.partialmethod(
            __TestVrmAnimationRenderingBase.assert_lossy_export, path
        )
        for path in sorted(
            (Path(__file__).parent / "resources" / "blend" / "lossy_animation").glob(
                "*.blend"
            )
        )
    },
)


def compare_image(image1_path: Path, image2_path: Path, diff_image_path: Path) -> float:
    try:
        subprocess.run(["ffmpeg", "-version"], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        message = "ffmpeg is required but could not be found"
        if sys.platform == "win32":
            raise SkipTest(message) from e
        raise AssertionError(message) from e

    compare_command: Optional[list[str]] = None
    try:
        subprocess.run(["magick", "-version"], check=True)
        compare_command = ["magick", "compare"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    if compare_command is None:
        try:
            subprocess.run(["compare", "-version"], check=True)
            compare_command = ["compare"]
        except (subprocess.CalledProcessError, FileNotFoundError):
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
