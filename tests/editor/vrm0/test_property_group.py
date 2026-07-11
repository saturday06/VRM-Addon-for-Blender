# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import main

import bpy
from bpy.types import Armature, Material

from io_scene_vrm.common import ops
from io_scene_vrm.common.vrm0.human_bone import HumanBoneName
from io_scene_vrm.editor.extension import get_armature_extension
from io_scene_vrm.editor.extension_accessor import get_material_extension
from io_scene_vrm.editor.vrm0.property_group import (
    Vrm0BlendShapeGroupPropertyGroup,
    Vrm0HumanoidPropertyGroup,
    Vrm0MaterialValueBindPropertyGroup,
)
from tests.util import AddonTestCase


class TestVrm0HumanoidPropertyGroup(AddonTestCase):
    def test_fixup_human_bones(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armatures = [
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        ]
        self.assertEqual(len(armatures), 1)
        armature = armatures[0]
        if not isinstance(armature.data, Armature):
            raise TypeError

        human_bones = get_armature_extension(armature.data).vrm0.humanoid.human_bones

        original = [(str(b.node.bone_name), str(b.bone)) for b in human_bones]

        human_bone1 = human_bones.add()
        human_bone1.bone = "NoHumanBone"
        Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
        self.assertEqual(
            original, [(str(b.node.bone_name), str(b.bone)) for b in human_bones]
        )

        human_bone2 = human_bones.add()
        human_bone2.bone = HumanBoneName.CHEST.value
        Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
        self.assertEqual(
            original, [(str(b.node.bone_name), str(b.bone)) for b in human_bones]
        )

        human_bones.add()
        human_bones.add()
        human_bones.add()
        Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
        self.assertEqual(
            original, [(str(b.node.bone_name), str(b.bone)) for b in human_bones]
        )

        chest_bone = next(b for b in human_bones if b.bone == HumanBoneName.CHEST.value)
        spine_bone = next(b for b in human_bones if b.bone == HumanBoneName.SPINE.value)
        chest_bone.node.bone_name = HumanBoneName.SPINE.value
        self.assertEqual(spine_bone.node.bone_name, HumanBoneName.SPINE.value)
        self.assertEqual(chest_bone.node.bone_name, HumanBoneName.SPINE.value)
        Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
        self.assertEqual(spine_bone.node.bone_name, HumanBoneName.SPINE.value)
        self.assertTrue(not chest_bone.node.bone_name)
        chest_bone.node.bone_name = HumanBoneName.CHEST.value
        self.assertEqual(
            original, [(str(b.node.bone_name), str(b.bone)) for b in human_bones]
        )

        hips_index = next(
            i for i, b in enumerate(human_bones) if b.bone == HumanBoneName.HIPS.value
        )
        human_bones.remove(hips_index)
        Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
        hips_bone = next(b for b in human_bones if b.bone == HumanBoneName.HIPS.value)
        self.assertTrue(not hips_bone.node.bone_name)
        hips_bone.node.bone_name = "hips"
        self.assertEqual(
            set(original), {(str(b.node.bone_name), str(b.bone)) for b in human_bones}
        )

    def test_duplicate_assignments_are_errors_in_flexible_mode(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        humanoid = get_armature_extension(armature.data).vrm0.humanoid
        humanoid.filter_by_human_bone_hierarchy = False
        Vrm0HumanoidPropertyGroup.update_all_bone_name_candidates(
            context,
            armature.data.name,
            force=True,
        )

        hips = next(
            human_bone
            for human_bone in humanoid.human_bones
            if human_bone.bone == HumanBoneName.HIPS.value
        )
        spine = next(
            human_bone
            for human_bone in humanoid.human_bones
            if human_bone.bone == HumanBoneName.SPINE.value
        )
        spine.node.bone_name = hips.node.bone_name

        self.assertFalse(humanoid.bones_are_correctly_assigned())
        self.assertTrue(humanoid.human_bone_duplication_error_messages())


class TestVrm0MaterialValueBindPropertyGroup(AddonTestCase):
    def _add_material_value_bind(self) -> Vrm0MaterialValueBindPropertyGroup:
        context = bpy.context
        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError
        ext = get_armature_extension(armature.data)
        group = ext.vrm0.blend_shape_master.blend_shape_groups.add()
        return group.material_values.add()

    def test_read_target_value_as_float_list_empty(self) -> None:
        material_value = self._add_material_value_bind()
        material_value.property_name = "_MainTex_ST"
        self.assertEqual(
            material_value.read_target_value_as_float_list(), [1.0, 1.0, 0.0, 0.0]
        )

    def test_read_target_value_as_float_list_partial_uv(self) -> None:
        material_value = self._add_material_value_bind()
        material_value.property_name = "_MainTex_ST"
        material_value.target_value.add().value = 2.0
        # UV defaults are (1.0, 1.0, 0.0, 0.0); the one provided value
        # overrides index 0, the rest come from defaults
        self.assertEqual(
            material_value.read_target_value_as_float_list(), [2.0, 1.0, 0.0, 0.0]
        )

    def test_read_target_value_as_float_list_all_values(self) -> None:
        material_value = self._add_material_value_bind()
        material_value.property_name = "_MainTex_ST"
        for v in [2.0, 3.0, 0.5, 0.25]:
            material_value.target_value.add().value = v
        self.assertEqual(
            material_value.read_target_value_as_float_list(), [2.0, 3.0, 0.5, 0.25]
        )

    def test_read_target_value_as_float_list_unknown_property(self) -> None:
        # When property_name is not in any known property table, there is no
        # default, so the raw values are returned without padding.
        material_value = self._add_material_value_bind()
        material_value.property_name = "_UnknownProperty"
        material_value.target_value.add().value = 5.0
        self.assertEqual(material_value.read_target_value_as_float_list(), [5.0])


class TestVrm0BlendShapeGroupMaterialPropertyVector(AddonTestCase):
    def _add_material_value_bind(self) -> Vrm0MaterialValueBindPropertyGroup:
        context = bpy.context
        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError
        ext = get_armature_extension(armature.data)
        group = ext.vrm0.blend_shape_master.blend_shape_groups.add()
        return group.material_values.add()

    def _create_mtoon_material(self) -> Material:
        material = bpy.data.materials.new(name="TestMToon")
        get_material_extension(material).mtoon1.enabled = True
        return material

    def test_non_mtoon_material_returns_none(self) -> None:
        material = bpy.data.materials.new(name="NonMToon")
        material_value = self._add_material_value_bind()
        material_value.property_name = "_MainTex_ST"
        for v in [1.0, 1.0, 0.0, 0.0]:
            material_value.target_value.add().value = v
        result = Vrm0BlendShapeGroupPropertyGroup.get_material_property_vector(
            material, material_value
        )
        self.assertIsNone(result)

    def test_uv_type_applies_v_flip(self) -> None:
        # _MainTex_ST is UV type: offset_v is flipped as 1 - offset_v - scale_v
        material = self._create_mtoon_material()
        material_value = self._add_material_value_bind()
        material_value.property_name = "_MainTex_ST"
        for v in [2.0, 3.0, 0.5, 0.25]:
            material_value.target_value.add().value = v
        result = Vrm0BlendShapeGroupPropertyGroup.get_material_property_vector(
            material, material_value
        )
        self.assertIsNotNone(result)
        if result is None:
            return
        target_vector, default_vector = result
        self.assertAlmostEqual(target_vector[0], 2.0)
        self.assertAlmostEqual(target_vector[1], 3.0)
        self.assertAlmostEqual(target_vector[2], 0.5)
        # v-flip: 1 - unity_offset_v - unity_scale_v = 1 - 0.25 - 3.0 = -2.25
        self.assertAlmostEqual(target_vector[3], -2.25)
        # khr defaults (scale 1,1; offset 0,0)
        self.assertEqual(default_vector, (1.0, 1.0, 0.0, 0.0))

    def test_uv_s_type_preserves_v_components(self) -> None:
        # _MainTex_ST_S is UV_S type: only U tiling/offset change;
        # V components are taken from the current khr_texture_transform values.
        material = self._create_mtoon_material()
        material_value = self._add_material_value_bind()
        material_value.property_name = "_MainTex_ST_S"
        for v in [2.0, 3.0, 0.5, 0.25]:
            material_value.target_value.add().value = v
        result = Vrm0BlendShapeGroupPropertyGroup.get_material_property_vector(
            material, material_value
        )
        self.assertIsNotNone(result)
        if result is None:
            return
        target_vector, default_vector = result
        self.assertAlmostEqual(target_vector[0], 2.0)  # unity_scale_u
        self.assertAlmostEqual(target_vector[1], 1.0)  # khr_scale_v (default)
        self.assertAlmostEqual(target_vector[2], 0.5)  # unity_offset_u
        self.assertAlmostEqual(target_vector[3], 0.0)  # khr_offset_v (default)
        self.assertEqual(default_vector, (1.0, 1.0, 0.0, 0.0))

    def test_uv_t_type_applies_v_flip(self) -> None:
        # _MainTex_ST_T is UV_T type: only V tiling/offset change;
        # U components are taken from khr_texture_transform; V offset is v-flipped.
        material = self._create_mtoon_material()
        material_value = self._add_material_value_bind()
        material_value.property_name = "_MainTex_ST_T"
        for v in [2.0, 3.0, 0.5, 0.25]:
            material_value.target_value.add().value = v
        result = Vrm0BlendShapeGroupPropertyGroup.get_material_property_vector(
            material, material_value
        )
        self.assertIsNotNone(result)
        if result is None:
            return
        target_vector, default_vector = result
        self.assertAlmostEqual(target_vector[0], 1.0)  # khr_scale_u (default)
        self.assertAlmostEqual(target_vector[1], 3.0)  # unity_scale_v
        self.assertAlmostEqual(target_vector[2], 0.0)  # khr_offset_u (default)
        # v-flip: 1 - unity_offset_v - unity_scale_v = 1 - 0.25 - 3.0 = -2.25
        self.assertAlmostEqual(target_vector[3], -2.25)
        self.assertEqual(default_vector, (1.0, 1.0, 0.0, 0.0))


if __name__ == "__main__":
    main()
