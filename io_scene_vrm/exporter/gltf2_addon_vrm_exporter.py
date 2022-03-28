import os
import secrets
import string
import tempfile
from collections import abc
from typing import Any, Dict, List, Optional

import bpy

from ..common import deep, gltf, version
from ..common.char import INTERNAL_NAME_PREFIX
from .abstract_base_vrm_exporter import AbstractBaseVrmExporter


class Gltf2AddonVrmExporter(AbstractBaseVrmExporter):
    def __init__(self, export_objects: List[bpy.types.Object]) -> None:
        armatures = [obj for obj in export_objects if obj.type == "ARMATURE"]
        if not armatures:
            raise NotImplementedError("アーマチュア無しエクスポートはまだ無い")
        self.armature = armatures[0]

        self.export_id = "BlenderVrmAddonExport" + (
            "".join(secrets.choice(string.digits) for _ in range(10))
        )
        self.armature[self.export_id] = True
        self.extras_bone_name_key = INTERNAL_NAME_PREFIX + self.export_id + "BoneName"
        self.extras_object_name_key = (
            INTERNAL_NAME_PREFIX + self.export_id + "ObjectName"
        )

    def create_dummy_skinned_mesh_object(self) -> bpy.types.Object:
        vertices = [
            (index / 16.0, 0, 0) for index, _ in enumerate(self.armature.pose.bones)
        ]
        vertices.append((0, 1, 0))
        mesh = bpy.data.meshes.new(self.export_id + "_mesh")
        mesh.from_pydata(vertices, [], [])
        mesh.update()
        obj = bpy.data.objects.new(self.export_id + "_object_mesh", mesh)
        for index, bone_name in enumerate(self.armature.data.bones.keys()):
            vertex_group = obj.vertex_groups.new(name=bone_name)
            vertex_group.add([index], 1.0, "ADD")
        modifier = obj.modifiers.new(name="Armature", type="ARMATURE")
        modifier.object = self.armature
        bpy.context.scene.collection.objects.link(obj)
        obj[self.extras_object_name_key] = obj.name
        return obj

    def export_vrm(self) -> Optional[bytes]:
        dummy_skinned_mesh_object = self.create_dummy_skinned_mesh_object()
        try:
            # glTF 2.0アドオンのコメントにはPoseBoneと書いてあるが、実際にはBoneのカスタムプロパティを参照している
            # そのため、いちおう両方に書いておく
            for bone in self.armature.pose.bones:
                bone[self.extras_bone_name_key] = bone.name
            for bone in self.armature.data.bones:
                bone[self.extras_bone_name_key] = bone.name
            for obj in bpy.data.objects:
                obj[self.extras_object_name_key] = obj.name

            with tempfile.TemporaryDirectory() as temp_dir:
                filepath = os.path.join(temp_dir, "out.glb")
                bpy.ops.export_scene.gltf(
                    filepath=filepath,
                    check_existing=False,
                    export_format="GLB",
                    export_extras=True,
                )
                with open(filepath, "rb") as file:
                    extra_name_assigned_glb = file.read()
        finally:
            for bone in self.armature.pose.bones:
                if self.extras_bone_name_key in bone:
                    del bone[self.extras_bone_name_key]
            for bone in self.armature.data.bones:
                if self.extras_bone_name_key in bone:
                    del bone[self.extras_bone_name_key]
            for obj in bpy.data.objects:
                if self.extras_object_name_key in obj:
                    del obj[self.extras_object_name_key]

        json_dict, body_binary = gltf.parse_glb(extra_name_assigned_glb)
        bone_name_to_index_dict: Dict[str, int] = {}

        nodes = json_dict.get("nodes")
        if not isinstance(nodes, abc.Iterable):
            nodes = []
        for node_index, node_dict in enumerate(nodes):
            if not isinstance(node_dict, dict):
                continue
            extras_dict = node_dict.get("extras")
            if not isinstance(extras_dict, dict):
                continue

            bone_name = extras_dict.get(self.extras_bone_name_key)
            if isinstance(bone_name, str):
                bone_name_to_index_dict[bone_name] = node_index
                del extras_dict[self.extras_bone_name_key]
                if not extras_dict:
                    del node_dict["extras"]
                continue

            object_name = extras_dict.get(self.extras_object_name_key)
            if isinstance(object_name, str) and (
                object_name == dummy_skinned_mesh_object.name
                or object_name.startswith(INTERNAL_NAME_PREFIX + "VrmAddonLinkTo")
            ):
                node_dict.clear()
                for child_removing_node_dict in list(nodes):
                    if not isinstance(child_removing_node_dict, dict):
                        continue
                    children = child_removing_node_dict.get("children")
                    if not isinstance(children, abc.Iterable):
                        continue
                    children = [child for child in children if child != node_index]
                    if children:
                        child_removing_node_dict["children"] = children
                    else:
                        del child_removing_node_dict["children"]

                # TODO: remove from node children, scene, ...

        vrm_props = self.armature.data.vrm_addon_extension.vrm1.vrm
        human_bones_dict: Dict[str, Any] = {}
        vrmc_vrm_dict: Dict[str, Any] = {
            "specVersion": "1.0-beta",
            "meta": {
                "name": vrm_props.meta.vrm_name,
                "version": vrm_props.meta.version,
                "authors": [author.value for author in vrm_props.meta.authors],
                "licenseUrl": "https://vrm.dev/licenses/1.0/",
            },
            "humanoid": {
                "humanBones": human_bones_dict,
            },
        }
        for (
            human_bone_name,
            human_bone,
        ) in (
            vrm_props.humanoid.human_bones.human_bone_name_to_human_bone_props().items()
        ):
            index = bone_name_to_index_dict.get(human_bone.node.value)
            if isinstance(index, int):
                human_bones_dict[human_bone_name.value] = {"node": index}

        extensions_used = json_dict.get("extensionsUsed")
        if not isinstance(extensions_used, abc.Iterable):
            extensions_used = []
        else:
            extensions_used = list(extensions_used)
        extensions_used.extend(["VRMC_vrm", "VRMC_springBone"])

        json_dict["extensionsUsed"] = extensions_used
        json_dict.update({"extensions": {"VRMC_vrm": vrmc_vrm_dict}})

        v = version.version()
        if os.environ.get("BLENDER_VRM_USE_TEST_EXPORTER_VERSION") == "true":
            v = (999, 999, 999)

        generator = "VRM Add-on for Blender v" + ".".join(map(str, v))

        base_generator = deep.get(json_dict, ["asset", "generator"])
        if isinstance(base_generator, str):
            generator += " with " + base_generator

        json_dict["asset"]["generator"] = generator

        bpy.context.scene.collection.objects.unlink(
            dummy_skinned_mesh_object
        )  # TODO: remove

        return gltf.pack_glb(json_dict, body_binary)
