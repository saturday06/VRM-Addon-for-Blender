# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import main

import bpy
from bpy.types import Armature

from io_scene_vrm.common import ops
from io_scene_vrm.common.vrm1.human_bone import HumanBoneSpecifications
from io_scene_vrm.editor.extension import get_armature_extension
from io_scene_vrm.editor.vrm1 import ops as vrm1_ops
from tests.util import AddonTestCase


class TestVrm1ExpressionsPropertyGroup(AddonTestCase):
    def test_assign_vrm1_expressions_from_vrm0(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        mesh = bpy.data.meshes.new("BlendShapeMesh")
        mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
        mesh.update()
        mesh_object = bpy.data.objects.new("BlendShapeMesh", mesh)
        context.scene.collection.objects.link(mesh_object)

        expressions = get_armature_extension(armature.data).vrm1.expressions
        blend_shape_group = get_armature_extension(
            armature.data
        ).vrm0.blend_shape_master.blend_shape_groups.add()
        blend_shape_group.name = "Smile"
        bind = blend_shape_group.binds.add()
        bind.mesh.mesh_object_name = mesh_object.name
        bind.index = "SmileShape"
        bind.weight = 0.75

        result = vrm1_ops.assign_vrm1_expressions_from_vrm0(context, armature.name)

        self.assertEqual(result, {"FINISHED"})
        expressions_with_name = [
            expression
            for expression in expressions.custom
            if expression.custom_name == "Smile"
        ]
        self.assertEqual(len(expressions_with_name), 1)
        expression = expressions_with_name[0]
        self.assertEqual(expression.custom_name, "Smile")
        self.assertEqual(len(expression.morph_target_binds), 1)
        self.assertEqual(
            expression.morph_target_binds[0].node.mesh_object_name, mesh_object.name
        )
        self.assertEqual(expression.morph_target_binds[0].index, "SmileShape")
        self.assertAlmostEqual(expression.morph_target_binds[0].weight, 0.75)

    def test_assign_vrm1_expressions_from_vrm0_material_color_bind_rgba(
        self,
    ) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        material = bpy.data.materials.new("TestMaterial")

        expressions = get_armature_extension(armature.data).vrm1.expressions
        blend_shape_group = get_armature_extension(
            armature.data
        ).vrm0.blend_shape_master.blend_shape_groups.add()
        blend_shape_group.name = "Blink"
        material_value = blend_shape_group.material_values.add()
        material_value.material = material
        material_value.property_name = "_Color"
        material_value.target_value_as_rgba = (1.0, 0.5, 0.25, 0.75)

        result = vrm1_ops.assign_vrm1_expressions_from_vrm0(context, armature.name)

        self.assertEqual(result, {"FINISHED"})
        expressions_with_name = [
            expression
            for expression in expressions.custom
            if expression.custom_name == "Blink"
        ]
        self.assertEqual(len(expressions_with_name), 1)
        expression = expressions_with_name[0]
        self.assertEqual(len(expression.material_color_binds), 1)
        bind = expression.material_color_binds[0]
        self.assertEqual(bind.material, material)
        self.assertEqual(bind.type, "color")
        self.assertAlmostEqual(bind.target_value[0], 1.0)
        self.assertAlmostEqual(bind.target_value[1], 0.5)
        self.assertAlmostEqual(bind.target_value[2], 0.25)
        self.assertAlmostEqual(bind.target_value[3], 0.75)

    def test_assign_vrm1_expressions_from_vrm0_material_color_bind_rgb(
        self,
    ) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        material = bpy.data.materials.new("TestMaterial")

        expressions = get_armature_extension(armature.data).vrm1.expressions
        blend_shape_group = get_armature_extension(
            armature.data
        ).vrm0.blend_shape_master.blend_shape_groups.add()
        blend_shape_group.name = "Angry"
        material_value = blend_shape_group.material_values.add()
        material_value.material = material
        material_value.property_name = "_EmissionColor"
        material_value.target_value_as_rgb = (0.1, 0.2, 0.3)

        result = vrm1_ops.assign_vrm1_expressions_from_vrm0(context, armature.name)

        self.assertEqual(result, {"FINISHED"})
        expressions_with_name = [
            expression
            for expression in expressions.custom
            if expression.custom_name == "Angry"
        ]
        self.assertEqual(len(expressions_with_name), 1)
        expression = expressions_with_name[0]
        self.assertEqual(len(expression.material_color_binds), 1)
        bind = expression.material_color_binds[0]
        self.assertEqual(bind.material, material)
        self.assertEqual(bind.type, "emissionColor")
        self.assertAlmostEqual(bind.target_value[0], 0.1, places=5)
        self.assertAlmostEqual(bind.target_value[1], 0.2, places=5)
        self.assertAlmostEqual(bind.target_value[2], 0.3, places=5)

    def test_assign_vrm1_expressions_from_vrm0_texture_transform_bind(
        self,
    ) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        material = bpy.data.materials.new("TestMaterial")

        expressions = get_armature_extension(armature.data).vrm1.expressions
        blend_shape_group = get_armature_extension(
            armature.data
        ).vrm0.blend_shape_master.blend_shape_groups.add()
        blend_shape_group.name = "Joy"
        material_value = blend_shape_group.material_values.add()
        material_value.material = material
        material_value.property_name = "_MainTex_ST"
        material_value.target_value_tiling_s = 2.0
        material_value.target_value_tiling_t = 3.0
        material_value.target_value_offset_s = 0.1
        material_value.target_value_offset_t = 0.2

        result = vrm1_ops.assign_vrm1_expressions_from_vrm0(context, armature.name)

        self.assertEqual(result, {"FINISHED"})
        expressions_with_name = [
            expression
            for expression in expressions.custom
            if expression.custom_name == "Joy"
        ]
        self.assertEqual(len(expressions_with_name), 1)
        expression = expressions_with_name[0]
        self.assertEqual(len(expression.texture_transform_binds), 1)
        bind = expression.texture_transform_binds[0]
        self.assertEqual(bind.material, material)
        self.assertAlmostEqual(bind.scale[0], 2.0)
        self.assertAlmostEqual(bind.scale[1], 3.0)
        self.assertAlmostEqual(bind.offset[0], 0.1)
        # Convert the Unity UV origin used by VRM 0.x to the glTF UV origin.
        self.assertAlmostEqual(bind.offset[1], 1.0 - 0.2 - 3.0)


class TestVrm1HumanBonesPropertyGroup(AddonTestCase):
    def test_error_messages_report_parent_requirement(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        human_bones = get_armature_extension(armature.data).vrm1.humanoid.human_bones
        human_bone_name_to_human_bone = human_bones.human_bone_name_to_human_bone()

        target_specification = HumanBoneSpecifications.RIGHT_THUMB_DISTAL
        parent_specification = target_specification.parent
        if parent_specification is None:
            raise ValueError

        # Assign only child bone to trigger parent requirement diagnostics.
        human_bone_name_to_human_bone[parent_specification.name].node.bone_name = ""

        expected_parent_requirement_error = (
            f'Please assign "{parent_specification.title}" because '
            + f'"{target_specification.title}" requires it as its child bone.'
        )

        human_bones.filter_by_human_bone_hierarchy = True
        self.assertIn(
            expected_parent_requirement_error,
            human_bones.error_messages(),
        )

        human_bones.filter_by_human_bone_hierarchy = False
        self.assertIn(
            expected_parent_requirement_error,
            human_bones.error_messages(),
        )

    def test_duplicate_assignments_are_errors_in_flexible_mode(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        human_bones = get_armature_extension(armature.data).vrm1.humanoid.human_bones
        human_bones.filter_by_human_bone_hierarchy = False
        human_bones.spine.node.bone_name = human_bones.hips.node.bone_name

        self.assertFalse(human_bones.bones_are_correctly_assigned())
        self.assertTrue(human_bones.human_bone_duplication_error_messages())


if __name__ == "__main__":
    main()
