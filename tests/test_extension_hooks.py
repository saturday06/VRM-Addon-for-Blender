# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from unittest import TestCase
from unittest.mock import MagicMock, sentinel

from io_scene_vrm.common.convert import Json
from io_scene_vrm.extension_hooks import (
    Vrm1ExportExtensionContext,
    Vrm1ImportExtensionContext,
    clear_vrm1_extension_hooks,
    create_vrm1_import_extension_context,
    invoke_vrm1_export_extension_hooks,
    invoke_vrm1_import_extension_hooks,
    register_vrm1_export_extension_hook,
    register_vrm1_import_extension_hook,
    unregister_vrm1_export_extension_hook,
    unregister_vrm1_import_extension_hook,
)


class TestExtensionHooks(TestCase):
    def setUp(self) -> None:
        clear_vrm1_extension_hooks()

    def tearDown(self) -> None:
        clear_vrm1_extension_hooks()

    def test_import_hooks_preserve_order_and_ignore_duplicates(self) -> None:
        calls: list[str] = []

        def first(_context: Vrm1ImportExtensionContext) -> None:
            calls.append("first")

        def second(_context: Vrm1ImportExtensionContext) -> None:
            calls.append("second")

        register_vrm1_import_extension_hook(first)
        register_vrm1_import_extension_hook(second)
        register_vrm1_import_extension_hook(first)

        context = create_vrm1_import_extension_context(
            context=MagicMock(),
            armature=MagicMock(),
            json_dict={"asset": {"version": "2.0"}},
            node_index_to_object_name={0: "Mesh"},
            node_index_to_bone_name={1: "Hips"},
            image_index_to_image={},
            material_index_to_material={},
            mesh_index_to_object={},
            mesh_node_index_to_object_name={},
        )
        invoke_vrm1_import_extension_hooks(context)

        self.assertEqual(calls, ["first", "second"])

    def test_unregister_missing_hook_is_harmless(self) -> None:
        def hook(_context: Vrm1ImportExtensionContext) -> None:
            return None

        unregister_vrm1_import_extension_hook(hook)

    def test_import_maps_are_frozen_snapshots(self) -> None:
        source_objects = {0: "Mesh"}
        context = create_vrm1_import_extension_context(
            context=MagicMock(),
            armature=MagicMock(),
            json_dict={"extensions": {}},
            node_index_to_object_name=source_objects,
            node_index_to_bone_name={},
            image_index_to_image={},
            material_index_to_material={},
            mesh_index_to_object={},
            mesh_node_index_to_object_name={},
        )

        source_objects[1] = "Other"
        self.assertEqual(dict(context.node_index_to_object_name), {0: "Mesh"})
        with self.assertRaises(TypeError):
            context.node_index_to_object_name[2] = "Nope"  # type: ignore[index]

    def test_import_hook_can_unregister_during_dispatch(self) -> None:
        calls: list[str] = []

        def remove_self(_context: Vrm1ImportExtensionContext) -> None:
            calls.append("remove_self")
            unregister_vrm1_import_extension_hook(remove_self)

        def second(_context: Vrm1ImportExtensionContext) -> None:
            calls.append("second")

        register_vrm1_import_extension_hook(remove_self)
        register_vrm1_import_extension_hook(second)

        invoke_vrm1_import_extension_hooks(
            create_vrm1_import_extension_context(
                context=MagicMock(),
                armature=MagicMock(),
                json_dict={},
                node_index_to_object_name={},
                node_index_to_bone_name={},
                image_index_to_image={},
                material_index_to_material={},
                mesh_index_to_object={},
                mesh_node_index_to_object_name={},
            )
        )

        self.assertEqual(calls, ["remove_self", "second"])

        calls.clear()
        invoke_vrm1_import_extension_hooks(
            create_vrm1_import_extension_context(
                context=MagicMock(),
                armature=MagicMock(),
                json_dict={},
                node_index_to_object_name={},
                node_index_to_bone_name={},
                image_index_to_image={},
                material_index_to_material={},
                mesh_index_to_object={},
                mesh_node_index_to_object_name={},
            )
        )
        self.assertEqual(calls, ["second"])

    def test_export_hook_can_mutate_json_and_buffer(self) -> None:
        def hook(context: Vrm1ExportExtensionContext) -> None:
            extensions = context.json_dict.setdefault("extensions", {})
            if not isinstance(extensions, dict):
                message = "extensions must be a dict"
                raise TypeError(message)
            extensions["VRMXT_test"] = {"specVersion": "1.0"}
            extensions_used = context.json_dict.setdefault("extensionsUsed", [])
            if not isinstance(extensions_used, list):
                message = "extensionsUsed must be a list"
                raise TypeError(message)
            extensions_used.append("VRMXT_test")
            context.buffer0.extend(b"\x00\x01\x02\x03")
            context.image_name_to_index["Particle"] = 7

        register_vrm1_export_extension_hook(hook)

        json_dict: dict[str, Json] = {
            "extensions": {},
            "extensionsUsed": ["VRMC_vrm"],
        }
        buffer0 = bytearray()
        image_name_to_index: dict[str, int] = {}

        invoke_vrm1_export_extension_hooks(
            Vrm1ExportExtensionContext(
                context=MagicMock(),
                armature=MagicMock(),
                json_dict=json_dict,
                buffer0=buffer0,
                bone_name_to_node_index={"Hips": 0},
                object_name_to_node_index={},
                image_name_to_index=image_name_to_index,
                material_name_to_index={},
                mesh_object_name_to_node_index={},
                mesh_object_name_to_morph_target_names={},
            )
        )

        self.assertEqual(
            json_dict["extensions"],
            {"VRMXT_test": {"specVersion": "1.0"}},
        )
        self.assertEqual(json_dict["extensionsUsed"], ["VRMC_vrm", "VRMXT_test"])
        self.assertEqual(bytes(buffer0), b"\x00\x01\x02\x03")
        self.assertEqual(image_name_to_index, {"Particle": 7})

    def test_export_hook_exception_propagates(self) -> None:
        def hook(_context: Vrm1ExportExtensionContext) -> None:
            message = "boom"
            raise RuntimeError(message)

        register_vrm1_export_extension_hook(hook)

        with self.assertRaisesRegex(RuntimeError, "boom"):
            invoke_vrm1_export_extension_hooks(
                Vrm1ExportExtensionContext(
                    context=MagicMock(),
                    armature=sentinel.armature,
                    json_dict={},
                    buffer0=bytearray(),
                    bone_name_to_node_index={},
                    object_name_to_node_index={},
                    image_name_to_index={},
                    material_name_to_index={},
                    mesh_object_name_to_node_index={},
                    mesh_object_name_to_morph_target_names={},
                )
            )

    def test_unregister_export_hook(self) -> None:
        calls: list[str] = []

        def hook(_context: Vrm1ExportExtensionContext) -> None:
            calls.append("hook")

        register_vrm1_export_extension_hook(hook)
        unregister_vrm1_export_extension_hook(hook)
        unregister_vrm1_export_extension_hook(hook)

        invoke_vrm1_export_extension_hooks(
            Vrm1ExportExtensionContext(
                context=MagicMock(),
                armature=MagicMock(),
                json_dict={},
                buffer0=bytearray(),
                bone_name_to_node_index={},
                object_name_to_node_index={},
                image_name_to_index={},
                material_name_to_index={},
                mesh_object_name_to_node_index={},
                mesh_object_name_to_morph_target_names={},
            )
        )
        self.assertEqual(calls, [])
