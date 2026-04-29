# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import tempfile
from pathlib import Path
from unittest import TestCase, main

import bpy
from bpy.types import ShaderNodeEmission, ShaderNodeGroup

from io_scene_vrm.external import io_scene_gltf2_support


class TestIoSceneGltf2Support(TestCase):
    def test_image_to_image_bytes(self) -> None:
        context = bpy.context

        tga_path = Path(__file__).parent.parent / "resources" / "blend" / "tga_test.tga"
        image = context.blend_data.images.load(str(tga_path), check_existing=True)
        image_bytes, _ = io_scene_gltf2_support.image_to_image_bytes(
            image, io_scene_gltf2_support.create_export_settings()
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "image.png"
            temp_path.write_bytes(image_bytes)
            converted_image = context.blend_data.images.load(
                str(temp_path), check_existing=False
            )
            converted_image.update()

        self.assertEqual(image.size[:], converted_image.size[:])

    def test_export_scene_gltf_with_color_group_input_to_emission_strength(
        self,
    ) -> None:
        context = bpy.context

        mesh = context.blend_data.meshes.new(name="GltfEmissionStrengthColorInputMesh")
        mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
        mesh.update()

        obj = context.blend_data.objects.new(
            name="GltfEmissionStrengthColorInputObject",
            object_data=mesh,
        )
        context.scene.collection.objects.link(obj)

        material = context.blend_data.materials.new(
            name="GltfEmissionStrengthColorInputMaterial"
        )
        node_tree = material.node_tree
        if node_tree is None:
            self.fail("Material node tree is None")
        for node in list(node_tree.nodes):
            node_tree.nodes.remove(node)

        output_node = node_tree.nodes.new(type="ShaderNodeOutputMaterial")
        emission_node = node_tree.nodes.new(type="ShaderNodeEmission")
        if not isinstance(emission_node, ShaderNodeEmission):
            self.fail(f"{type(emission_node)} is not ShaderNodeEmission")

        group_tree = context.blend_data.node_groups.new(
            name="GltfEmissionStrengthColorInputGroup",
            type="ShaderNodeTree",
        )
        group_tree.interface.new_socket(
            name="Color",
            in_out="INPUT",
            socket_type="NodeSocketColor",
        )
        group_tree.interface.new_socket(
            name="Color",
            in_out="OUTPUT",
            socket_type="NodeSocketColor",
        )
        group_input_node = group_tree.nodes.new(type="NodeGroupInput")
        group_output_node = group_tree.nodes.new(type="NodeGroupOutput")
        group_tree.links.new(
            group_input_node.outputs["Color"], group_output_node.inputs["Color"]
        )

        # The glTF exporter reads this unlinked Color group input as the
        # Emission Strength factor and returns bpy_prop_array instead of float.
        group_node = node_tree.nodes.new(type="ShaderNodeGroup")
        if not isinstance(group_node, ShaderNodeGroup):
            self.fail(f"{type(group_node)} is not ShaderNodeGroup")
        group_node.node_tree = group_tree
        group_node.inputs["Color"].default_value = (0.25, 0.5, 0.75, 1)

        emission_node.inputs["Color"].default_value = (0.8, 0.7, 0.6, 1)
        node_tree.links.new(
            group_node.outputs["Color"], emission_node.inputs["Strength"]
        )
        node_tree.links.new(
            emission_node.outputs["Emission"], output_node.inputs["Surface"]
        )
        mesh.materials.append(material)

        try:
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            context.view_layer.objects.active = obj

            with tempfile.TemporaryDirectory() as temp_dir:
                filepath = Path(temp_dir) / "out.glb"
                arguments = io_scene_gltf2_support.ExportSceneGltfArguments(
                    filepath=str(filepath),
                    check_existing=False,
                    export_format="GLB",
                    export_extras=True,
                    export_def_bones=True,
                    export_current_frame=True,
                    use_selection=True,
                    use_active_scene=True,
                    export_animations=False,
                    export_armature_object_remove=False,
                    export_rest_position_armature=False,
                    export_all_influences=True,
                    export_vertex_color="MATERIAL",
                    export_lights=False,
                    export_try_sparse_sk=True,
                    export_apply=False,
                )
                with self.assertRaises(RuntimeError) as error:
                    io_scene_gltf2_support.export_scene_gltf(arguments)

            error_message = str(error.exception)
            self.assertIn("export_emission_factor", error_message)
            self.assertIn(
                "unsupported operand type(s) for *: 'float' and 'bpy_prop_array'",
                error_message,
            )
        finally:
            context.blend_data.objects.remove(obj, do_unlink=True)
            context.blend_data.meshes.remove(mesh)
            context.blend_data.materials.remove(material)
            context.blend_data.node_groups.remove(group_tree)


if __name__ == "__main__":
    main()
