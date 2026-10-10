# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from pathlib import Path

import bpy
from bpy.types import Armature, Object

from io_scene_vrm.common import ops
from io_scene_vrm.common.preferences import get_preferences
from io_scene_vrm.editor.extension_accessor import get_armature_extension
from io_scene_vrm.importer.abstract_base_vrm_importer import ParseResult
from io_scene_vrm.importer.vrm1_importer import Vrm1Importer
from tests.util import AddonTestCase


class TestVrm1Importer(AddonTestCase):
    def test_recovers_missing_node_markers_for_shared_mesh_expression_bind(
        self,
    ) -> None:
        context = bpy.context
        ops.icyp.make_basic_armature()
        armature = context.view_layer.objects.active
        if not armature or not isinstance(armature.data, Armature):
            message = "No armature"
            raise AssertionError(message)

        mesh_data = context.blend_data.meshes.new("SharedMesh")
        mesh_data.from_pydata([(0, 0, 0)], [], [])
        mesh_objects = list[Object]()
        for name in ("FirstMeshObject", "SecondMeshObject"):
            mesh_object = context.blend_data.objects.new(name, mesh_data)
            context.scene.collection.objects.link(mesh_object)
            mesh_objects.append(mesh_object)
        mesh_objects[0].shape_key_add(name="Basis")
        mesh_objects[0].shape_key_add(name="Key")

        importer = Vrm1Importer(
            context,
            ParseResult(
                filepath=Path(),
                json_dict={},
                spec_version_number=(1, 0),
                spec_version_str="1.0",
                spec_version_is_stable=True,
                vrm0_extension_dict={},
                vrm1_extension_dict={},
                hips_node_index=None,
                bin_chunk=b"",
            ),
            get_preferences(context),
        )
        importer._restore_object_names_from_mesh_node_indices(
            mesh_data,
            [0, 1],
            2,
        )

        self.assertEqual(
            importer._object_names,
            {0: mesh_objects[0].name, 1: mesh_objects[1].name},
        )
        expressions = get_armature_extension(armature.data).vrm1.expressions
        expression = expressions.custom.add()
        importer.load_vrm1_expression(
            expression,
            {"morphTargetBinds": [{"node": 1, "index": 0}]},
        )
        self.assertEqual(
            expression.morph_target_binds[0].node.mesh_object_name,
            mesh_objects[1].name,
        )
        self.assertEqual(expression.morph_target_binds[0].index, "Key")
