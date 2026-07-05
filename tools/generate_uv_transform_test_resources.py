#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import logging
import sys
from enum import Enum, auto
from pathlib import Path

import bpy
from bpy.types import (
    Armature,
    Context,
    Object,
)

from io_scene_vrm.common import ops
from io_scene_vrm.common.workspace import save_workspace
from io_scene_vrm.editor.extension import VrmAddonArmatureExtensionPropertyGroup
from io_scene_vrm.editor.extension_accessor import (
    get_armature_extension,
    get_material_extension,
)
from io_scene_vrm.editor.mtoon1.property_group import Mtoon1SamplerPropertyGroup

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)


class TestTexture(Enum):
    LIT = auto()
    EMISSION = auto()


def generate_uv_transform_vrm(
    context: Context,
    armature_obj: Object,
    *,
    test_texture: TestTexture,
    offset_u: float,
    offset_v: float,
    scale_u: float,
    scale_v: float,
    wrap_s: str,
    wrap_t: str,
    spec_version: str,
) -> None:
    armature_data = armature_obj.data
    if not armature_data:
        message = "Armature data not found"
        raise AssertionError(message)
    if not isinstance(armature_data, Armature):
        message = "Armature data is not of type bpy.types.Armature"
        raise TypeError(message)

    material = context.blend_data.materials.get("Material")
    if not material:
        message = "Material not found"
        raise AssertionError(message)
    ext = get_material_extension(material)
    if test_texture == TestTexture.LIT:
        ext.mtoon1.pbr_metallic_roughness.base_color_factor = (1, 1, 1, 1)
        ext.mtoon1.emissive_factor = (0, 0, 0)
        texture_info = ext.mtoon1.pbr_metallic_roughness.base_color_texture
    elif test_texture == TestTexture.EMISSION:
        ext.mtoon1.pbr_metallic_roughness.base_color_factor = (0, 0, 0, 1)
        ext.mtoon1.emissive_factor = (1, 1, 1)
        texture_info = ext.mtoon1.emissive_texture
    texture_info.index.sampler.wrap_s = wrap_s
    texture_info.index.sampler.wrap_t = wrap_t
    base_color_texture = ext.mtoon1.pbr_metallic_roughness.base_color_texture
    khr_texture_transform = base_color_texture.extensions.khr_texture_transform
    khr_texture_transform.offset = (offset_u, offset_v)
    khr_texture_transform.scale = (scale_u, scale_v)

    vrm_path = (
        Path(__file__).parent.parent
        / "tests"
        / "resources"
        / "blend"
        / "lossless_animation"
        / (
            "temp_"
            + f"uv_transform{test_texture.name}_"
            + f"spec{spec_version}_"
            + f"ou{offset_u}_ov{offset_v}_"
            + f"su{scale_u}_sv{scale_v}_"
            + f"ws{wrap_s}_wt{wrap_t}"
            + ".vrm"
        )
    )
    default_vrma_path = (
        Path(__file__).parent.parent / "tests" / "resources" / "vrma" / "nop.vrma"
    )

    for id_obj in list(context.blend_data.objects) + list(context.blend_data.armatures):
        if id_obj.animation_data:
            id_obj.animation_data_clear()

    context.scene.render.fps = 60
    context.scene.render.fps_base = 1.0
    context.scene.frame_start = 1
    context.scene.frame_end = 1

    result = ops.import_scene.vrma(
        filepath=str(default_vrma_path), armature_object_name=armature_obj.name
    )
    if result != {"FINISHED"}:
        message = f"Import error {default_vrma_path} {result}"
        raise AssertionError(message)

    get_armature_extension(armature_data).spec_version = spec_version

    blend_path = vrm_path.with_suffix(".blend")
    result = bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    if result != {"FINISHED"}:
        message = f"Export error {blend_path} {result}"
        raise AssertionError(message)


def main() -> int:
    context = bpy.context

    bpy.ops.preferences.addon_enable(module="io_scene_vrm")

    for (
        test_texture,
        offset_u,
        offset_v,
        scale_u,
        scale_v,
        wrap_s,
        wrap_t,
        spec_version,
    ) in (
        (
            test_texture,
            offset_u,
            offset_v,
            scale_u,
            scale_v,
            wrap_s,
            wrap_t,
            spec_version,
        )
        for test_texture in TestTexture
        for offset_u in (-1.5, -0.5, 0, 0.5, 1.5)
        for offset_v in (-1.5, -0.5, 0, 0.5, 1.5)
        for scale_u in (-4, -1, 1, 4)
        for scale_v in (-4, -1, 1, 4)
        for wrap_s in Mtoon1SamplerPropertyGroup.wrap_enum.identifiers()
        for wrap_t in Mtoon1SamplerPropertyGroup.wrap_enum.identifiers()
        for spec_version in (
            VrmAddonArmatureExtensionPropertyGroup.SPEC_VERSION_VRM0,
            VrmAddonArmatureExtensionPropertyGroup.SPEC_VERSION_VRM1,
        )
    ):
        bpy.ops.wm.read_homefile(use_empty=True)
        bpy.ops.wm.open_mainfile(
            filepath=str(
                Path(__file__).parent.parent
                / "tests"
                / "resources"
                / "template"
                / "uv_transform"
                / "uv_transform_template.blend"
            )
        )

        armature_obj = next(
            (obj for obj in context.blend_data.objects if obj.type == "ARMATURE"),
            None,
        )
        if not armature_obj:
            raise AssertionError
        with save_workspace(context, armature_obj):
            generate_uv_transform_vrm(
                context,
                armature_obj,
                test_texture=test_texture,
                offset_u=offset_u,
                offset_v=offset_v,
                scale_u=scale_u,
                scale_v=scale_v,
                wrap_s=wrap_s,
                wrap_t=wrap_t,
                spec_version=spec_version,
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
