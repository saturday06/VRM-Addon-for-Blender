# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import Optional
from unittest import TestCase, main

import bpy

from io_scene_vrm.editor.search import current_armature, object_distance


class TestSearch(TestCase):
    def setUp(self) -> None:
        super().setUp()
        bpy.ops.wm.read_homefile(use_empty=True)

    def test_object_distance(self) -> None:
        context = bpy.context

        # Create objects
        obj1 = bpy.data.objects.new("Obj1", None)
        obj2 = bpy.data.objects.new("Obj2", None)
        obj3 = bpy.data.objects.new("Obj3", None)
        obj4 = bpy.data.objects.new("Obj4", None)

        # Set up object hierarchy: obj1 -> obj2 -> obj3
        # obj4 is standalone
        obj2.parent = obj1
        obj3.parent = obj2

        # Create collections
        col_root = context.scene.collection
        col_a = bpy.data.collections.new("ColA")
        col_b = bpy.data.collections.new("ColB")
        col_c = bpy.data.collections.new("ColC")

        # Set up collection hierarchy: root -> A -> B, root -> C
        col_root.children.link(col_a)
        col_a.children.link(col_b)
        col_root.children.link(col_c)

        # Link objects to collections
        col_a.objects.link(obj1)
        col_b.objects.link(obj2)
        col_b.objects.link(obj3)
        col_c.objects.link(obj4)

        # Create collection_child_to_parent mapping
        collection_child_to_parent: dict[
            bpy.types.Collection, Optional[bpy.types.Collection]
        ] = {col_root: None}
        collections = [col_root]
        while collections:
            parent = collections.pop()
            for child in parent.children:
                collections.append(child)
                collection_child_to_parent[child] = parent

        # Tests

        # 1. Same object
        self.assertEqual(
            object_distance(obj1, obj1, collection_child_to_parent),
            (0, 0, 0, 0, 0, 0, 0),
        )

        # 2. Parent-child
        self.assertEqual(
            object_distance(obj1, obj2, collection_child_to_parent),
            # left_parent_path: obj1, right_parent_path:
            # obj2->obj1 (pop obj1 -> obj2) => (0, 1)
            (1, 0, 0, 1, 0, 1, 0),
        )

        # 3. Grandparent-child
        self.assertEqual(
            object_distance(obj1, obj3, collection_child_to_parent),
            (1, 0, 0, 2, 0, 1, 0),
        )

        # 4. Siblings in same collection
        self.assertEqual(
            object_distance(obj2, obj3, collection_child_to_parent),
            (1, 0, 0, 1, 0, 0, 0),
        )

        # 5. Across different collection hierarchies
        # obj2 in col_b (root->a->b), obj4 in col_c (root->c)
        # obj2 parent path: obj2->obj1, obj4 parent path: obj4.
        # left_parent_path: [obj1, obj2], right: [obj4] -> len 2, 1
        # left_collection: root->a->b, right:
        # root->c. pop root -> [a,b], [c] -> len 2, 1
        self.assertEqual(
            object_distance(obj2, obj4, collection_child_to_parent),
            (1, 0, 2, 1, 2, 1, 0),
        )

        # 6. Object not in collection mapping
        obj5 = bpy.data.objects.new("Obj5", None)
        self.assertEqual(
            object_distance(obj1, obj5, collection_child_to_parent),
            (1, 0, 1, 1, 2, 0, 0),
        )

    def test_object_distance_includes_selection_and_visibility_priority(self) -> None:
        context = bpy.context

        source = bpy.data.objects.new("Source", None)
        selected_target = bpy.data.objects.new("SelectedTarget", None)
        unselected_target = bpy.data.objects.new("UnselectedTarget", None)
        hidden_target = bpy.data.objects.new("HiddenTarget", None)

        root = context.scene.collection
        root.objects.link(source)
        root.objects.link(selected_target)
        root.objects.link(unselected_target)
        root.objects.link(hidden_target)

        collection_child_to_parent: dict[
            bpy.types.Collection, Optional[bpy.types.Collection]
        ] = {root: None}

        source.select_set(True)
        selected_target.select_set(True)
        unselected_target.select_set(False)

        self.assertEqual(
            object_distance(source, selected_target, collection_child_to_parent),
            (0, 0, 1, 1, 0, 0, 0),
        )
        self.assertEqual(
            object_distance(source, unselected_target, collection_child_to_parent),
            (1, 0, 1, 1, 0, 0, 0),
        )

        source.select_set(False)
        hidden_target.select_set(False)
        hidden_target.hide_set(True)
        hidden_target.hide_render = True

        self.assertEqual(
            object_distance(source, hidden_target, collection_child_to_parent),
            (1, 1, 1, 1, 0, 0, 1),
        )

    def test_current_armature_prefers_visible_and_selection_matching_target(
        self,
    ) -> None:
        context = bpy.context

        active = bpy.data.objects.new("Active", None)
        armature_data_1 = bpy.data.armatures.new("ArmatureData1")
        armature_data_2 = bpy.data.armatures.new("ArmatureData2")
        armature_object_1 = bpy.data.objects.new("ArmatureObject1", armature_data_1)
        armature_object_2 = bpy.data.objects.new("ArmatureObject2", armature_data_2)

        root = context.scene.collection
        root.objects.link(active)
        root.objects.link(armature_object_1)
        root.objects.link(armature_object_2)

        active.select_set(True)
        armature_object_1.select_set(False)
        armature_object_2.select_set(True)
        context.view_layer.objects.active = active

        self.assertEqual(current_armature(context), armature_object_2)

        armature_object_1.select_set(True)
        armature_object_2.select_set(True)
        armature_object_1.hide_set(False)
        armature_object_1.hide_render = False
        armature_object_2.hide_set(True)
        armature_object_2.hide_render = True

        self.assertEqual(current_armature(context), armature_object_1)


if __name__ == "__main__":
    main()
