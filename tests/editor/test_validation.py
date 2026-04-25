# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import main

import bpy
from bpy.types import Armature, Mesh
from mathutils import Vector

from io_scene_vrm.common import ops
from io_scene_vrm.editor import search
from io_scene_vrm.editor.extension import get_armature_extension
from io_scene_vrm.editor.validation import (
    ValidationState,
    WM_OT_vrm_validator,
    is_valid_url,
)
from tests.util import AddonTestCase


class TestValidation(AddonTestCase):
    def test_vrm0_bone_order_validation(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armatures = [
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        ]
        self.assertEqual(len(armatures), 1)
        armature = armatures[0]
        if not isinstance(armature.data, Armature):
            raise TypeError

        ext = get_armature_extension(armature.data)
        ext.spec_version = ext.SPEC_VERSION_VRM0
        humanoid = ext.vrm0.humanoid
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

        spine_bone = next(b for b in humanoid.human_bones if b.bone == "spine")
        chest_bone = next(b for b in humanoid.human_bones if b.bone == "chest")
        spine_bone.node.bone_name = "chest"
        chest_bone.node.bone_name = "spine"
        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})
        spine_bone.node.bone_name = "spine"
        chest_bone.node.bone_name = "chest"
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

        right_little_distal_bone = next(
            b for b in humanoid.human_bones if b.bone == "rightLittleDistal"
        )
        right_little_distal_bone.node.bone_name = "spine"
        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})
        right_little_distal_bone.node.bone_name = "hips"
        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})
        right_little_distal_bone.node.bone_name = "little_distal.L"
        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})
        right_little_distal_bone.node.bone_name = ""
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})
        right_little_distal_bone.node.bone_name = "little_distal.R"
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

    def test_vrm1_bone_order_validation(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armatures = [
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        ]
        self.assertEqual(len(armatures), 1)
        armature = armatures[0]
        if not isinstance(armature.data, Armature):
            raise TypeError

        ext = get_armature_extension(armature.data)
        humanoid = ext.vrm1.humanoid
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

        spine_bone = humanoid.human_bones.spine
        chest_bone = humanoid.human_bones.chest
        spine_bone.node.bone_name = "chest"
        chest_bone.node.bone_name = "spine"
        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})
        spine_bone.node.bone_name = "spine"
        chest_bone.node.bone_name = "chest"
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

        right_little_distal_bone = humanoid.human_bones.right_little_distal
        right_little_distal_bone.node.bone_name = "spine"
        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})
        right_little_distal_bone.node.bone_name = "hips"
        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})
        right_little_distal_bone.node.bone_name = "little_distal.L"
        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})
        right_little_distal_bone.node.bone_name = ""
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})
        right_little_distal_bone.node.bone_name = "little_distal.R"
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

    def test_vrm0_duplicate_assignment_validation_in_flexible_mode(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        ext = get_armature_extension(armature.data)
        ext.spec_version = ext.SPEC_VERSION_VRM0
        humanoid = ext.vrm0.humanoid
        humanoid.filter_by_human_bone_hierarchy = False
        spine_bone = next(b for b in humanoid.human_bones if b.bone == "spine")
        spine_bone.node.bone_name = "hips"

        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})

    def test_vrm1_duplicate_assignment_validation_in_flexible_mode(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        human_bones = get_armature_extension(armature.data).vrm1.humanoid.human_bones
        human_bones.filter_by_human_bone_hierarchy = False
        human_bones.spine.node.bone_name = "hips"

        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})

    def test_validate_vrm1_additional(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armatures = [
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        ]
        self.assertEqual(len(armatures), 1)
        armature = armatures[0]
        if not isinstance(armature.data, Armature):
            raise TypeError

        ext = get_armature_extension(armature.data)

        # 1. Test empty state
        state = ValidationState()
        WM_OT_vrm_validator.validate_vrm1_additional(armature.data, [armature], state)
        self.assertEqual(state.skippable_warning_messages, [])
        self.assertEqual(state.error_messages, [])

        # 2. Test invalid URL
        ext.vrm1.meta.other_license_url = "http://["
        state = ValidationState()
        WM_OT_vrm_validator.validate_vrm1_additional(armature.data, [armature], state)
        self.assertEqual(len(state.skippable_warning_messages), 1)
        self.assertIn("is not a valid URL", state.skippable_warning_messages[0])

        # 3. Test negative scale
        ext.vrm1.meta.other_license_url = ""
        armature.scale = Vector((-1, 1, 1))
        state = ValidationState()
        WM_OT_vrm_validator.validate_vrm1_additional(armature.data, [armature], state)
        self.assertEqual(len(state.error_messages), 1)
        self.assertIn(
            "contains a negative value for the scale", state.error_messages[0]
        )
        armature.scale = Vector((1, 1, 1))

        # 4. Test overlapping spring bones and ancestor-descendant chain
        springs = ext.spring_bone1.springs
        spring1 = springs.add()
        spring1.vrm_name = "Spring1"
        spring1.joints.add().node.bone_name = "spine"

        spring2 = springs.add()
        spring2.vrm_name = "Spring2"
        spring2.joints.add().node.bone_name = "chest"
        spring2.joints.add().node.bone_name = "spine"

        state = ValidationState()
        WM_OT_vrm_validator.validate_vrm1_additional(armature.data, [armature], state)
        self.assertEqual(len(state.skippable_warning_messages), 1)
        self.assertIn("have common bone", state.skippable_warning_messages[0])
        self.assertIn('"spine"', state.skippable_warning_messages[0])

    def test_validate_vrm0_blend_shape_material_validation(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armatures = [
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        ]
        self.assertEqual(len(armatures), 1)
        armature = armatures[0]
        if not isinstance(armature.data, Armature):
            raise TypeError

        ext = get_armature_extension(armature.data)
        ext.spec_version = ext.SPEC_VERSION_VRM0
        blend_shape_master = ext.vrm0.blend_shape_master
        group = blend_shape_master.blend_shape_groups.add()
        group.name = "TestGroup"

        # 1. Test empty material
        material_value = group.material_values.add()
        state = ValidationState()
        WM_OT_vrm_validator.validate_vrm0_additional(
            context, armature.data, [armature], state
        )
        self.assertTrue(any("no material is set" in msg for msg in state.info_messages))

        # 2. Test non-exported material
        material = context.blend_data.materials.new(name="TestMaterial")
        material_value.material = material
        state = ValidationState()
        WM_OT_vrm_validator.validate_vrm0_additional(
            context, armature.data, [armature], state
        )
        self.assertTrue(
            any("will not be exported" in msg for msg in state.info_messages)
        )

        # 3. Test empty property name
        # To make the material "exported", it needs to be used by an object in
        # export_objects.
        mesh = context.blend_data.meshes.new(name="TestMesh")
        mesh.from_pydata([(0, 0, 0), (0, 0, 1), (0, 1, 0)], [], [(0, 1, 2)])
        mesh_obj = context.blend_data.objects.new(
            name="TestMeshObj",
            object_data=mesh,
        )
        context.scene.collection.objects.link(mesh_obj)
        mesh_data = mesh_obj.data
        if not isinstance(mesh_data, Mesh):
            raise TypeError
        mesh_data.materials.append(material)

        export_objects = [armature, mesh_obj]
        state = ValidationState()
        state.used_materials.extend(search.export_materials(context, export_objects))
        WM_OT_vrm_validator.validate_vrm0_additional(
            context, armature.data, export_objects, state
        )
        self.assertTrue(
            any("the property name is empty" in msg for msg in state.info_messages)
        )

        # 4. Test valid state
        material_value.property_name = "_Color"
        state = ValidationState()
        state.used_materials.extend(search.export_materials(context, export_objects))
        WM_OT_vrm_validator.validate_vrm0_additional(
            context, armature.data, export_objects, state
        )
        # We don't check info_messages length because there might be other info
        # messages (like firstPersonBone)
        self.assertFalse(
            any("no material is set" in msg for msg in state.info_messages)
        )
        self.assertFalse(
            any("will not be exported" in msg for msg in state.info_messages)
        )
        self.assertFalse(
            any("the property name is empty" in msg for msg in state.info_messages)
        )

    def test_is_valid_url(self) -> None:
        self.assertTrue(is_valid_url("https://example.com", allow_empty_str=False))
        self.assertTrue(is_valid_url("https://example.com", allow_empty_str=True))

        self.assertFalse(is_valid_url("example.com", allow_empty_str=False))
        self.assertFalse(is_valid_url("example.com", allow_empty_str=True))

        self.assertFalse(is_valid_url("", allow_empty_str=False))
        self.assertTrue(is_valid_url("", allow_empty_str=True))

        self.assertFalse(is_valid_url("http://[", allow_empty_str=False))
        self.assertFalse(is_valid_url("http://[", allow_empty_str=True))


if __name__ == "__main__":
    main()
