# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from pathlib import Path

import bpy
import pytest
import requests
from bpy.types import Armature, Context, Mesh, Object
from pytest_codspeed.plugin import BenchmarkFixture

from io_scene_vrm.common import ops
from io_scene_vrm.editor.extension import (
    get_armature_extension,
)


def generate_random_shape_keys(context: Context, armature_object: Object) -> None:
    if not isinstance(armature_data := armature_object.data, Armature):
        raise TypeError

    for loop_index, (obj, key_block, copy_index) in enumerate(
        (obj, key_block, copy_index)
        for obj in context.blend_data.objects
        if isinstance(mesh_data := obj.data, Mesh)
        if (shape_keys := mesh_data.shape_keys)
        if (key_blocks := shape_keys.key_blocks)
        for key_block in list(key_blocks)
        if key_block.name != shape_keys.reference_key.name
        for copy_index in range(10)  # Create 10 copies of each shape key
    ):
        new_shape_key = obj.shape_key_add(
            name=f"{key_block.name}_copy_{copy_index}", from_mix=False
        )

        # Copy vertex positions from original key
        new_shape_key_points = new_shape_key.data
        for shape_key_point_index, shape_key_point in enumerate(key_block.data):
            new_shape_key_points[shape_key_point_index].co = shape_key_point.co.copy()

        if not new_shape_key_points:
            continue

        # Randomly move 10 vertices to prevent caching
        for i in range(10):
            new_shape_key_point = new_shape_key_points[
                (loop_index + i) % len(new_shape_key_points)
            ]
            new_shape_key_point.co.x += (loop_index + i + 1) / 100.0
            new_shape_key_point.co.y += (loop_index + i + 2) / 200.0
            new_shape_key_point.co.z += (loop_index + i + 3) / 300.0

        # Create a custom Expression corresponding to the newly added shape key
        ops.vrm.add_vrm1_expressions_custom_expression(
            armature_object_name=armature_object.name,
            custom_expression_name=new_shape_key.name,
        )
        ops.vrm.add_vrm1_expression_morph_target_bind(
            armature_object_name=armature_object.name,
            expression_name=new_shape_key.name,
        )
        new_expression = get_armature_extension(armature_data).vrm1.expressions.custom[
            -1
        ]
        new_morph_target_bind = new_expression.morph_target_binds[-1]
        new_morph_target_bind.node.mesh_object_name = obj.name
        new_morph_target_bind.index = new_shape_key.name

        # Bind the newly added shape key to existing custom Expressions as well
        expression_name_and_expressions = list(
            get_armature_extension(armature_data)
            .vrm1.expressions.all_name_to_expression_dict()
            .items()
        )
        for expression_index in (
            loop_index % len(expression_name_and_expressions),
            (loop_index + 11) % len(expression_name_and_expressions),
            (loop_index + 17) % len(expression_name_and_expressions),
            (loop_index + 43) % len(expression_name_and_expressions),
            (loop_index + 71) % len(expression_name_and_expressions),
            (loop_index + 97) % len(expression_name_and_expressions),
        ):
            expression_name, expression = expression_name_and_expressions[
                expression_index
            ]
            if expression == new_expression:
                continue
            ops.vrm.add_vrm1_expression_morph_target_bind(
                armature_object_name=armature_object.name,
                expression_name=expression_name,
            )
            new_morph_target_bind = expression.morph_target_binds[-1]
            new_morph_target_bind.node.mesh_object_name = obj.name
            new_morph_target_bind.index = new_shape_key.name


def test_expression_preview(benchmark: BenchmarkFixture) -> None:
    context = bpy.context

    bpy.ops.preferences.addon_enable(module="io_scene_vrm")
    bpy.ops.wm.read_homefile(use_empty=True)

    vrm_url = "https://raw.githubusercontent.com/vrm-c/vrm-specification/c24d76d99a18738dd2c266be1c83f089064a7b5e/samples/VRM1_Constraint_Twist_Sample/vrm/VRM1_Constraint_Twist_Sample.vrm"
    vrm_path = (
        Path(__file__).parent.parent.parent
        / "temp"
        / "VRM1_Constraint_Twist_Sample.vrm"
    )
    if not vrm_path.exists():
        with requests.get(vrm_url, timeout=5 * 60) as response:
            assert response.ok
            vrm_path.write_bytes(response.content)

    version_str = "_".join(map(str, tuple(bpy.app.version)))
    blend_path = (
        Path(__file__).parent.parent.parent
        / "temp"
        / (Path(__file__).stem + "_" + version_str + ".blend")
    )
    if not blend_path.exists():
        assert ops.import_scene.vrm(filepath=str(vrm_path)) == {"FINISHED"}
        armature = context.object
        if (
            not armature
            or not (armature_data := armature.data)
            or not isinstance(armature_data, Armature)
        ):
            raise AssertionError
        generate_random_shape_keys(context, armature)
        context.view_layer.update()
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
        bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    armature = context.object
    if (
        not armature
        or not (armature_data := armature.data)
        or not isinstance(armature_data, Armature)
    ):
        raise AssertionError
    all_expressions = list(
        get_armature_extension(armature_data)
        .vrm1.expressions.all_name_to_expression_dict()
        .values()
    )
    for expression_index, expression in enumerate(all_expressions):
        values = [0, 0.001, 0.05, 0.1, 0.2, 0.499, 0.5, 0.4, 0.7, 0.9, 0.999, 1]
        expression.preview = values[expression_index % len(values)]
    expressions = [
        all_expressions[expression_index % len(all_expressions)]
        for expression_index in (
            11369,
            21227,
            35023,
            41621,
            58411,
            63929,
            76243,
            87869,
            98669,
        )
    ]

    @benchmark
    def _() -> None:
        for expression, preview in (
            (expression, preview)
            for expression in expressions
            for preview in (0, 0.5, 0.7, 1)
        ):
            default_preview = expression.preview
            expression.preview = preview
            expression.preview = default_preview


if __name__ == "__main__":
    pytest.main()
