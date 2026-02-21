# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import Optional
from unittest import TestCase

import bpy
from bpy.types import Armature
from mathutils import Vector

from io_scene_vrm.common import ops
from io_scene_vrm.common.debug import assert_vector3_equals
from io_scene_vrm.common.test_helper import AddonTestCase
from io_scene_vrm.importer.vrm0_importer import (
    MaterialProperty,
    calculate_mtoon0_render_queue_offset_maps,
    setup_bones,
)


class TestVrm0Importer(AddonTestCase):
    def test_eye_bone_world_minus_y(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = context.view_layer.objects.active
        if not armature or not isinstance(armature.data, Armature):
            message = "No armature"
            raise AssertionError(message)

        bpy.ops.object.mode_set(mode="EDIT")
        eye_r = armature.data.edit_bones["eye.R"]
        eye_r.tail = Vector((-0.2, -0.2, 1.55))
        eye_l = armature.data.edit_bones["eye.L"]
        eye_l.tail = Vector((0.2, -0.2, 1.55))
        bpy.ops.object.mode_set(mode="OBJECT")
        # return
        setup_bones(context, armature)

        bpy.ops.object.mode_set(mode="EDIT")
        eye_r = armature.data.edit_bones["eye.R"]
        eye_l = armature.data.edit_bones["eye.L"]

        assert_vector3_equals(
            Vector((0, -1, 0)),
            (eye_r.tail - eye_r.head).normalized(),
            "eye.R direction is minus y",
        )
        assert_vector3_equals(
            Vector((0, -1, 0)),
            (eye_l.tail - eye_l.head).normalized(),
            "eye.L direction is minus y",
        )

    def test_head_bone_world_plus_z(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = context.view_layer.objects.active
        if not armature or not isinstance(armature.data, Armature):
            message = "No armature"
            raise AssertionError(message)

        bpy.ops.object.mode_set(mode="EDIT")
        neck = armature.data.edit_bones["neck"]
        neck.tail = Vector((0, -0.2, 1.5))
        head = armature.data.edit_bones["head"]
        head.tail = Vector((0, -0.4, 1.57))
        bpy.ops.object.mode_set(mode="OBJECT")
        # return
        setup_bones(context, armature)

        bpy.ops.object.mode_set(mode="EDIT")
        head = armature.data.edit_bones["head"]
        assert_vector3_equals(
            Vector((0, 0, 1)),
            (head.tail - head.head).normalized(),
            "head direction is plus z",
        )

        parent = head.parent
        if not parent:
            message = "head has no parent"
            raise AssertionError(message)

        self.assertLess(
            head.length - parent.length,
            0.0001,
            (f"head length {head.length} is same as neck length {parent.length}"),
        )

    def test_multiple_children_right_toes_direction_is_same_as_foot(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = context.view_layer.objects.active
        if not armature or not isinstance(armature.data, Armature):
            message = "No armature"
            raise AssertionError(message)

        bpy.ops.object.mode_set(mode="EDIT")
        right_foot = armature.data.edit_bones["foot.R"]
        right_foot.tail = Vector((-0.2, -0.2, -0.2))
        right_toes = armature.data.edit_bones["toes.R"]
        right_toes.tail = Vector((0, -0.4, 1.57))

        right_toes_child1 = armature.data.edit_bones.new("toes_child1.R")
        right_toes_child1.parent = right_toes
        right_toes_child1.head = Vector((-0.5, -0.25, 0))
        right_toes_child1.tail = Vector((-0.5, -0.5, 0))

        right_toes_child2 = armature.data.edit_bones.new("toes_child2.R")
        right_toes_child2.parent = right_toes
        right_toes_child2.head = Vector((-0.75, -0.25, 0))
        right_toes_child2.tail = Vector((-0.75, -0.5, 0))
        bpy.ops.object.mode_set(mode="OBJECT")
        # return
        setup_bones(context, armature)

        bpy.ops.object.mode_set(mode="EDIT")
        right_foot = armature.data.edit_bones["foot.R"]
        right_toes = armature.data.edit_bones["toes.R"]
        assert_vector3_equals(
            right_foot.vector.normalized(),
            right_toes.vector.normalized(),
            "foot.R and toes.R direction are same direction",
        )

        parent = right_toes.parent
        if not parent:
            message = "toes.R has no parent"
            raise AssertionError(message)

        self.assertLess(
            right_toes.length * 2 - parent.length,
            0.0001,
            (
                f"toes.R length {right_toes.length} is half as "
                + f"foot.R length {parent.length}"
            ),
        )

    def test_multiple_children_no_left_toes(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = context.view_layer.objects.active
        if not armature or not isinstance(armature.data, Armature):
            message = "No armature"
            raise AssertionError(message)

        bpy.ops.object.mode_set(mode="EDIT")
        armature.data.edit_bones.remove(armature.data.edit_bones["toes.R"])
        right_lower_leg = armature.data.edit_bones["lower_leg.R"]
        right_lower_leg.tail = Vector((-0.2, 0.2, 0.5))
        right_lower_leg.tail = Vector((-0.2, 0.2, 0))
        right_foot = armature.data.edit_bones["foot.R"]
        right_foot.tail = Vector((-0.2, 0.2, 0))
        right_foot.tail = Vector((-0.2, -0.2, 0))

        right_foot_child1 = armature.data.edit_bones.new("foot_child1.R")
        right_foot_child1.parent = right_foot
        right_foot_child1.head = Vector((-0.5, -0.25, 0))
        right_foot_child1.tail = Vector((-0.5, -0.5, 0))

        right_foot_child2 = armature.data.edit_bones.new("foot_child2.R")
        right_foot_child2.parent = right_foot
        right_foot_child2.head = Vector((-0.75, -0.25, 0))
        right_foot_child2.tail = Vector((-0.75, -0.5, 0))

        bpy.ops.object.mode_set(mode="OBJECT")
        # return
        setup_bones(context, armature)

        bpy.ops.object.mode_set(mode="EDIT")
        right_lower_leg = armature.data.edit_bones["lower_leg.R"]
        right_foot = armature.data.edit_bones["foot.R"]
        assert_vector3_equals(
            right_lower_leg.vector.normalized(),
            right_foot.vector.normalized(),
            "lower_leg.R and foot.R direction are same direction",
        )

        parent = right_foot.parent
        if not parent:
            message = "foot.R has no parent"
            raise AssertionError(message)

        self.assertLess(
            right_foot.length * 2 - parent.length,
            0.0001,
            (
                f"foot.R length {right_foot.length} is half as "
                + f"lower_leg.R length {parent.length}"
            ),
        )

    def test_multiple_children_no_right_fingers(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = context.view_layer.objects.active
        if not armature or not isinstance(armature.data, Armature):
            message = "No armature"
            raise AssertionError(message)

        bpy.ops.object.mode_set(mode="EDIT")
        for name in [
            "thumb_proximal.R",
            "thumb_intermediate.R",
            "thumb_distal.R",
            "index_proximal.R",
            "index_intermediate.R",
            "index_distal.R",
            "middle_proximal.R",
            "middle_intermediate.R",
            "middle_distal.R",
            "ring_proximal.R",
            "ring_intermediate.R",
            "ring_distal.R",
            "little_proximal.R",
            "little_intermediate.R",
            "little_distal.R",
        ]:
            armature.data.edit_bones.remove(armature.data.edit_bones[name])
        right_hand = armature.data.edit_bones["hand.R"]
        right_hand.tail = Vector((-0.5, -0.5, 1))

        right_hand_child1 = armature.data.edit_bones.new("hand_child1.R")
        right_hand_child1.parent = right_hand
        right_hand_child1.head = Vector((-0.5, -0.25, 1.5))
        right_hand_child1.tail = Vector((-0.5, -0.5, 1.5))

        right_hand_child2 = armature.data.edit_bones.new("hand_child2.R")
        right_hand_child2.parent = right_hand
        right_hand_child2.head = Vector((-0.75, -0.25, 1.5))
        right_hand_child2.tail = Vector((-0.75, -0.5, 1.5))

        bpy.ops.object.mode_set(mode="OBJECT")
        # return
        setup_bones(context, armature)

        bpy.ops.object.mode_set(mode="EDIT")
        right_lower_arm = armature.data.edit_bones["lower_arm.R"]
        right_hand = armature.data.edit_bones["hand.R"]
        assert_vector3_equals(
            right_lower_arm.vector.normalized(),
            right_hand.vector.normalized(),
            "lower_hand.R and hand.R direction are same direction",
        )

        parent = right_hand.parent
        if not parent:
            message = "hand.R has no parent"
            raise AssertionError(message)

        self.assertLess(
            right_hand.length * 2 - parent.length,
            0.0001,
            (
                f"hand.R length {right_hand.length} is half as "
                + f"lower_arm.R length {parent.length}"
            ),
        )

    def test_left_finger_only_multiple_children_index_intermediate(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = context.view_layer.objects.active
        if not armature or not isinstance(armature.data, Armature):
            message = "No armature"
            raise AssertionError(message)

        bpy.ops.object.mode_set(mode="EDIT")
        for name in [
            "thumb_proximal.R",
            "thumb_intermediate.R",
            "thumb_distal.R",
            "index_proximal.R",
            "index_distal.R",
            "middle_proximal.R",
            "middle_intermediate.R",
            "middle_distal.R",
            "ring_proximal.R",
            "ring_intermediate.R",
            "ring_distal.R",
            "little_proximal.R",
            "little_intermediate.R",
            "little_distal.R",
        ]:
            armature.data.edit_bones.remove(armature.data.edit_bones[name])
        right_hand = armature.data.edit_bones["hand.R"]
        right_hand.tail = Vector((-0.5, -0.5, 1))
        right_index_intermediate = armature.data.edit_bones["index_intermediate.R"]
        right_index_intermediate.tail = Vector((-1, -0.5, 1))

        right_index_intermediate_child1 = armature.data.edit_bones.new(
            "index_intermediate_child1.R"
        )
        right_index_intermediate_child1.parent = right_index_intermediate
        right_index_intermediate_child1.head = Vector((-0.5, -0.25, 1.5))
        right_index_intermediate_child1.tail = Vector((-0.5, -0.5, 1.5))

        right_index_intermediate_child2 = armature.data.edit_bones.new(
            "index_intermediate_child2.R"
        )
        right_index_intermediate_child2.parent = right_index_intermediate
        right_index_intermediate_child2.head = Vector((-0.75, -0.25, 1.5))
        right_index_intermediate_child2.tail = Vector((-0.75, -0.5, 1.5))

        bpy.ops.object.mode_set(mode="OBJECT")
        # return
        setup_bones(context, armature)

        bpy.ops.object.mode_set(mode="EDIT")
        right_index_intermediate = armature.data.edit_bones["index_intermediate.R"]
        right_hand = armature.data.edit_bones["hand.R"]
        assert_vector3_equals(
            right_index_intermediate.vector.normalized(),
            right_hand.vector.normalized(),
            "index_intermediate.R and hand.R direction are same direction",
        )

        parent = right_index_intermediate.parent
        if not parent:
            message = "hand.R has no parent"
            raise AssertionError(message)

        self.assertLess(
            right_index_intermediate.length * 2 - parent.length,
            0.0001,
            (
                f"index_intermediate.R length {right_index_intermediate.length}"
                + f" is half as hand.R length {parent.length}"
            ),
        )


class TestCalculateMtoon0RenderQueueOffsetMaps(TestCase):
    def make_mtoon_property(
        self, render_queue: Optional[int], blend_mode: Optional[float]
    ) -> MaterialProperty:
        return MaterialProperty(
            name="test",
            shader="VRM/MToon",
            render_queue=render_queue,
            keyword_map={},
            tag_map={},
            float_properties=({} if blend_mode is None else {"_BlendMode": blend_mode}),
            vector_properties={},
            texture_properties={},
        )

    def test_empty(self) -> None:
        t_map, tz_map = calculate_mtoon0_render_queue_offset_maps([])
        self.assertEqual(t_map, {})
        self.assertEqual(tz_map, {})

    def test_transparent_single_queue(self) -> None:
        mp = self.make_mtoon_property(render_queue=3000, blend_mode=2.0)
        t_map, tz_map = calculate_mtoon0_render_queue_offset_maps([mp])
        self.assertEqual(t_map, {3000: 0})
        self.assertEqual(tz_map, {})

    def test_transparent_two_queues(self) -> None:
        mp_high = self.make_mtoon_property(render_queue=3000, blend_mode=2.0)
        mp_low = self.make_mtoon_property(render_queue=2999, blend_mode=2.0)
        t_map, tz_map = calculate_mtoon0_render_queue_offset_maps([mp_high, mp_low])
        # Highest queue -> 0, lower queue -> -1
        self.assertEqual(t_map, {3000: 0, 2999: -1})
        self.assertEqual(tz_map, {})

    def test_transparent_more_than_nine_queues(self) -> None:
        # 11 unique render queues: maps to 0, -1, ..., -9, -10
        # the -10 entry should be clamped to -9 when applied
        mps = [
            self.make_mtoon_property(render_queue=3000 - i, blend_mode=2.0)
            for i in range(11)
        ]
        t_map, _ = calculate_mtoon0_render_queue_offset_maps(mps)
        # The lowest queue (2990) maps to -10, clamped to -9 at application
        self.assertEqual(t_map[3000], 0)
        self.assertEqual(t_map[2999], -1)
        self.assertEqual(t_map[2991], -9)
        self.assertEqual(t_map[2990], -10)

    def test_transparent_z_write_more_than_nine_queues(self) -> None:
        # 11 unique render queues: maps to 0, 1, ..., 9, 10
        # the 10 entry should be clamped to 9 when applied
        mps = [
            self.make_mtoon_property(render_queue=2501 + i, blend_mode=3.0)
            for i in range(11)
        ]
        _, tz_map = calculate_mtoon0_render_queue_offset_maps(mps)
        # The lowest queue (2501) maps to 0, the highest (2511) maps to 10
        self.assertEqual(tz_map[2501], 0)
        self.assertEqual(tz_map[2502], 1)
        self.assertEqual(tz_map[2509], 8)
        self.assertEqual(tz_map[2510], 9)
        self.assertEqual(tz_map[2511], 10)

    def test_transparent_z_write_single_queue(self) -> None:
        mp = self.make_mtoon_property(render_queue=2501, blend_mode=3.0)
        t_map, tz_map = calculate_mtoon0_render_queue_offset_maps([mp])
        self.assertEqual(t_map, {})
        self.assertEqual(tz_map, {2501: 0})

    def test_transparent_z_write_two_queues(self) -> None:
        mp_low = self.make_mtoon_property(render_queue=2501, blend_mode=3.0)
        mp_high = self.make_mtoon_property(render_queue=2502, blend_mode=3.0)
        t_map, tz_map = calculate_mtoon0_render_queue_offset_maps([mp_low, mp_high])
        self.assertEqual(t_map, {})
        # Lowest queue -> 0, higher queue -> 1
        self.assertEqual(tz_map, {2501: 0, 2502: 1})

    def test_non_mtoon_shader_ignored(self) -> None:
        mp = MaterialProperty(
            name="test",
            shader="VRM/UnlitTexture",
            render_queue=3000,
            keyword_map={},
            tag_map={},
            float_properties={"_BlendMode": 2.0},
            vector_properties={},
            texture_properties={},
        )
        t_map, tz_map = calculate_mtoon0_render_queue_offset_maps([mp])
        self.assertEqual(t_map, {})
        self.assertEqual(tz_map, {})

    def test_none_render_queue_ignored(self) -> None:
        mp = self.make_mtoon_property(render_queue=None, blend_mode=2.0)
        t_map, tz_map = calculate_mtoon0_render_queue_offset_maps([mp])
        self.assertEqual(t_map, {})
        self.assertEqual(tz_map, {})

    def test_mixed_render_modes(self) -> None:
        mp_opaque = self.make_mtoon_property(render_queue=2000, blend_mode=0.0)
        mp_cutout = self.make_mtoon_property(render_queue=2450, blend_mode=1.0)
        mp_transparent = self.make_mtoon_property(render_queue=3000, blend_mode=2.0)
        mp_z_write = self.make_mtoon_property(render_queue=2501, blend_mode=3.0)
        t_map, tz_map = calculate_mtoon0_render_queue_offset_maps(
            [mp_opaque, mp_cutout, mp_transparent, mp_z_write]
        )
        # Opaque and cutout do not appear in the maps
        self.assertNotIn(2000, t_map)
        self.assertNotIn(2450, t_map)
        self.assertEqual(t_map, {3000: 0})
        self.assertEqual(tz_map, {2501: 0})
