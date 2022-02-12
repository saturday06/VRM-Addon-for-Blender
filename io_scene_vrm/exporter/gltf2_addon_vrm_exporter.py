import os
import secrets
import string
import tempfile
from collections import abc
from typing import Any, Dict, List, Optional

import bpy

from ..common import gltf
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
        self.extras_bone_name_key = INTERNAL_NAME_PREFIX + self.export_id + "BoneName"

    def export_vrm(self) -> Optional[bytes]:
        try:
            # glTF 2.0アドオンのコメントにはPoseBoneと書いてあるが、実際にはBoneのカスタムプロパティを参照している
            # そのため、いちおう両方に書いておく
            for bone in self.armature.pose.bones:
                bone[self.extras_bone_name_key] = bone.name
            for bone in self.armature.data.bones:
                bone[self.extras_bone_name_key] = bone.name

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
            if not isinstance(bone_name, str):
                continue
            bone_name_to_index_dict[bone_name] = node_index

        vrm0_props = self.armature.data.vrm_addon_extension.vrm0
        human_bones_dict: Dict[str, Any] = {}
        vrmc_vrm_dict: Dict[str, Any] = {
            "specVersion": "1.0-beta",
            "meta": {
                "name": vrm0_props.meta.title,
                "version": vrm0_props.meta.version,
                "authors": [vrm0_props.meta.author],
                "licenseUrl": "https://vrm.dev/licenses/1.0/",
            },
            "humanoid": {
                "humanBones": human_bones_dict,
            },
        }
        for human_bone in vrm0_props.humanoid.human_bones:
            index = bone_name_to_index_dict.get(human_bone.node.value)
            if isinstance(index, int):
                human_bones_dict[human_bone.bone] = {"node": index}

        extensions_used = json_dict.get("extensionsUsed")
        if not isinstance(extensions_used, abc.Iterable):
            extensions_used = []
        else:
            extensions_used = list(extensions_used)
        extensions_used.extend(["VRMC_vrm", "VRMC_springBone"])

        json_dict["extensionsUsed"] = extensions_used
        json_dict.update({"extensions": {"VRMC_vrm": vrmc_vrm_dict}})
        return gltf.pack_glb(json_dict, body_binary)
