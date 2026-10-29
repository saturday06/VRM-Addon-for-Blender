# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import TYPE_CHECKING
from unittest import main

import bpy
from bpy.props import PointerProperty, StringProperty
from bpy.types import Armature, ChildOfConstraint, Object, PropertyGroup
from mathutils import Euler, Matrix, Vector

from io_scene_vrm.common import ops
from io_scene_vrm.editor.extension_accessor import get_armature_extension
from tests.util import AddonTestCase


class TestMmdRigidPropertyGroup(PropertyGroup):
    type: StringProperty()  # type: ignore[valid-type]
    shape: StringProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        type: str  # type: ignore[no-redef]
        shape: str  # type: ignore[no-redef]


class TestMmdAssignment(AddonTestCase):
    def setUp(self) -> None:
        super().setUp()
        bpy.utils.register_class(TestMmdRigidPropertyGroup)
        Object.mmd_type = StringProperty()  # type: ignore[attr-defined]
        Object.mmd_rigid = PointerProperty(type=TestMmdRigidPropertyGroup)  # type: ignore[attr-defined]

    def tearDown(self) -> None:
        delattr(Object, "mmd_rigid")
        delattr(Object, "mmd_type")
        bpy.utils.unregister_class(TestMmdRigidPropertyGroup)
        super().tearDown()

    def test_body_endpoints_and_multiple_bodies_per_bone(self) -> None:
        bpy.ops.object.add(type="ARMATURE")
        armature = bpy.context.object
        if armature is None or not isinstance(armature.data, Armature):
            raise AssertionError
        bpy.ops.object.mode_set(mode="EDIT")
        root = armature.data.edit_bones.new("Collider bone")
        root.name = "Collider bone"
        root.head = (0.2, -0.1, 0.3)
        root.tail = (0.8, 0.4, 1.1)
        spring = armature.data.edit_bones.new("Spring bone")
        spring.head, spring.tail = root.tail, root.tail + Vector((0, 0, 0.5))
        spring.parent = root
        bpy.ops.object.mode_set(mode="OBJECT")
        armature.matrix_world = (
            Matrix.Translation((2, -3, 1))
            @ Euler((0.3, -0.5, 0.6)).to_matrix().to_4x4()
            @ Matrix.Diagonal((2, 2, 2, 1))
        )
        armature.pose.bones["Collider bone"].rotation_mode = "XYZ"
        armature.pose.bones["Collider bone"].rotation_euler = Euler((0.4, 0.2, -0.3))
        bpy.context.view_layer.update()

        # The integration reads only these MMD properties and the bone constraint.
        # Supply that interface without requiring a second add-on in VRM tests.
        sources: list[Object] = []
        for i, shape in enumerate(("CAPSULE", "CAPSULE", "SPHERE", "BOX")):
            mesh = bpy.data.meshes.new(f"Rigid {i}")
            half_z = 0.8 if shape == "CAPSULE" else 0.3
            mesh.from_pydata(
                [
                    (x, y, z)
                    for x in (-0.3, 0.3)
                    for y in (-0.3, 0.3)
                    for z in (-half_z, half_z)
                ],
                [],
                [],
            )
            obj = bpy.data.objects.new(f"Rigid {i}", mesh)
            bpy.context.scene.collection.objects.link(obj)
            obj.matrix_world = (
                Matrix.Translation((i * 0.4, -0.6, 1.2))
                @ Euler((0.7, 0.2, i * 0.8)).to_matrix().to_4x4()
                @ Matrix.Diagonal((0.6, 0.6, 0.6, 1))
            )
            setattr(obj, "mmd_type", "RIGID_BODY")
            rigid = getattr(obj, "mmd_rigid", None)
            if not isinstance(rigid, TestMmdRigidPropertyGroup):
                raise TypeError
            rigid.shape = shape
            rigid.type = "0"
            constraint = obj.constraints.new("CHILD_OF")
            if not isinstance(constraint, ChildOfConstraint):
                raise TypeError
            constraint.name = "mmd_tools_rigid_parent"
            constraint.target = armature
            constraint.subtarget = "Collider bone"
            constraint.mute = True
            sources.append(obj)
        dynamic = bpy.data.objects.new("Dynamic", None)
        bpy.context.scene.collection.objects.link(dynamic)
        setattr(dynamic, "mmd_type", "RIGID_BODY")
        rigid = getattr(dynamic, "mmd_rigid", None)
        if not isinstance(rigid, TestMmdRigidPropertyGroup):
            raise TypeError
        rigid.type = "1"
        constraint = dynamic.constraints.new("CHILD_OF")
        if not isinstance(constraint, ChildOfConstraint):
            raise TypeError
        constraint.name = "mmd_tools_rigid_parent"
        constraint.target, constraint.subtarget = armature, "Spring bone"
        constraint.mute = True
        bpy.context.view_layer.update()
        result = ops.vrm.assign_spring_bone1_from_mmd(
            armature_object_name=armature.name
        )
        self.assertEqual(result, {"FINISHED"})
        bpy.context.view_layer.update()
        spring_bone = get_armature_extension(armature.data).spring_bone1
        self.assertEqual(len(spring_bone.colliders), 4)
        self.assertEqual(len(spring_bone.collider_groups), 1)
        self.assertEqual(len(spring_bone.collider_groups[0].colliders), 4)
        self.assertEqual(len(spring_bone.springs[0].collider_groups), 1)
        bone_world = armature.matrix_world @ armature.pose.bones["Collider bone"].matrix
        for source, collider in zip(sources, spring_bone.colliders):
            if collider.bpy_object is None:
                raise AssertionError
            rigid = getattr(source, "mmd_rigid", None)
            if not isinstance(rigid, TestMmdRigidPropertyGroup):
                raise TypeError
            capsule = rigid.shape == "CAPSULE"
            shape = collider.shape.capsule if capsule else collider.shape.sphere
            expected = source.matrix_world @ Vector((0, 0, -0.5 if capsule else 0))
            self.assertLess(
                (collider.bpy_object.matrix_world.translation - expected).length,
                1e-5,
            )
            self.assertLess((bone_world @ Vector(shape.offset) - expected).length, 1e-5)
            if capsule:
                expected_tail = source.matrix_world @ Vector((0, 0, 0.5))
                self.assertLess(
                    (
                        collider.bpy_object.children[0].matrix_world.translation
                        - expected_tail
                    ).length,
                    1e-5,
                )
                self.assertLess(
                    (
                        bone_world @ Vector(collider.shape.capsule.tail) - expected_tail
                    ).length,
                    1e-5,
                )
            self.assertAlmostEqual(shape.radius, 0.09, places=5)
        count = len(bpy.data.objects)
        self.assertEqual(
            ops.vrm.assign_spring_bone1_from_mmd(armature_object_name=armature.name),
            {"FINISHED"},
        )
        self.assertEqual(len(bpy.data.objects), count)
        self.assertEqual(len(spring_bone.colliders), 4)


if __name__ == "__main__":
    main()
