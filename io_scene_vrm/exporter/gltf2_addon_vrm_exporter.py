import os
import secrets
import string
import tempfile
from collections import abc
from typing import Any, Dict, List, Optional, Union

import bpy

from ..common import deep, gltf, version
from ..common.char import INTERNAL_NAME_PREFIX
from ..editor.spring_bone1.property_group import SpringBone1SpringBonePropertyGroup
from ..editor.vrm1.property_group import (
    Vrm1ExpressionPropertyGroup,
    Vrm1ExpressionsPropertyGroup,
    Vrm1FirstPersonPropertyGroup,
    Vrm1HumanoidPropertyGroup,
    Vrm1LookAtPropertyGroup,
    Vrm1MetaPropertyGroup,
)
from .abstract_base_vrm_exporter import AbstractBaseVrmExporter


class Gltf2AddonVrmExporter(AbstractBaseVrmExporter):
    def __init__(self, export_objects: List[bpy.types.Object]) -> None:
        armatures = [obj for obj in export_objects if obj.type == "ARMATURE"]
        if not armatures:
            raise NotImplementedError("アーマチュア無しエクスポートはまだ未対応")
        self.armature = armatures[0]

        self.export_id = "BlenderVrmAddonExport" + (
            "".join(secrets.choice(string.digits) for _ in range(10))
        )
        self.extras_bone_name_key = INTERNAL_NAME_PREFIX + self.export_id + "BoneName"
        self.extras_object_name_key = (
            INTERNAL_NAME_PREFIX + self.export_id + "ObjectName"
        )
        self.extras_material_name_key = (
            INTERNAL_NAME_PREFIX + self.export_id + "MaterialName"
        )
        self.extras_mesh_name_key = INTERNAL_NAME_PREFIX + self.export_id + "MeshName"

    def create_dummy_skinned_mesh_object(self) -> str:
        vertices = [
            (index / 16.0, 0, 0) for index, _ in enumerate(self.armature.pose.bones)
        ]
        vertices.append((0, 1, 0))
        mesh = bpy.data.meshes.new(self.export_id + "_mesh")
        mesh.from_pydata(vertices, [], [])
        mesh.update()
        obj = bpy.data.objects.new(self.export_id + "_mesh_object", mesh)
        for index, bone_name in enumerate(self.armature.data.bones.keys()):
            vertex_group = obj.vertex_groups.new(name=bone_name)
            vertex_group.add([index], 1.0, "ADD")
        modifier = obj.modifiers.new(name="Armature", type="ARMATURE")
        modifier.object = self.armature
        bpy.context.scene.collection.objects.link(obj)
        obj[self.extras_object_name_key] = obj.name
        return str(obj.name)

    @staticmethod
    def create_meta_dict(meta_props: Vrm1MetaPropertyGroup) -> Dict[str, Any]:
        meta_dict: Dict[str, Union[str, bool, List[str]]] = {
            "licenseUrl": "https://vrm.dev/licenses/1.0/",
            "name": meta_props.vrm_name if meta_props.vrm_name else "undefined",
            "version": meta_props.version if meta_props.version else "undefined",
            "avatarPermission": meta_props.avatar_permission,
            "allowExcessivelyViolentUsage": meta_props.allow_excessively_violent_usage,
            "allowExcessivelySexualUsage": meta_props.allow_excessively_sexual_usage,
            "commercialUsage": meta_props.commercial_usage,
            "allowPoliticalOrReligiousUsage": meta_props.allow_political_or_religious_usage,
            "allowAntisocialOrHateUsage": meta_props.allow_antisocial_or_hate_usage,
            "creditNotation": meta_props.credit_notation,
            "allowRedistribution": meta_props.allow_redistribution,
            "modification": meta_props.modification,
        }

        authors = [author.value for author in meta_props.authors if author.value]
        if not authors:
            authors = ["undefined"]
        meta_dict["authors"] = authors

        if meta_props.copyright_information:
            meta_dict["copyrightInformation"] = meta_props.copyright_information

        references = [
            reference.value for reference in meta_props.references if reference.value
        ]
        if references:
            meta_dict["references"] = references

        if meta_props.third_party_licenses:
            meta_dict["thirdPartyLicenses"] = meta_props.third_party_licenses

        if meta_props.other_license_url:
            meta_dict["otherLicenseUrl"] = meta_props.other_license_url

        return meta_dict

    @staticmethod
    def create_humanoid_dict(
        humanoid_props: Vrm1HumanoidPropertyGroup,
        bone_name_to_index_dict: Dict[str, int],
    ) -> Dict[str, Any]:
        human_bones_dict: Dict[str, Any] = {}
        for (
            human_bone_name,
            human_bone,
        ) in humanoid_props.human_bones.human_bone_name_to_human_bone_props().items():
            index = bone_name_to_index_dict.get(human_bone.node.value)
            if isinstance(index, int):
                human_bones_dict[human_bone_name.value] = {"node": index}

        return {
            "humanBones": human_bones_dict,
        }

    @staticmethod
    def create_first_person_dict(
        first_person_props: Vrm1FirstPersonPropertyGroup,
        mesh_name_to_node_index_dict: Dict[str, int],
    ) -> Dict[str, Any]:
        mesh_annotations: List[Dict[str, Any]] = []
        for mesh_annotation_props in first_person_props.mesh_annotations:
            if not mesh_annotation_props.node or mesh_annotation_props.node.value:
                continue
            node_index = mesh_name_to_node_index_dict.get(
                mesh_annotation_props.node.value
            )
            if not isinstance(node_index, int):
                continue
            mesh_annotations.append(
                {
                    "node": node_index,
                    "type": mesh_annotation_props.type,
                }
            )
        if not mesh_annotations:
            return {}
        return {"meshAnnotations": mesh_annotations}

    @staticmethod
    def create_look_at_dict(
        look_at_props: Vrm1LookAtPropertyGroup,
    ) -> Dict[str, Any]:
        return {
            "offsetFromHeadBone": list(look_at_props.offset_from_head_bone),
            "type": look_at_props.type,
            "rangeMapHorizontalInner": {
                "inputMaxValue": look_at_props.range_map_horizontal_inner.input_max_value,
                "outputScale": look_at_props.range_map_horizontal_inner.output_scale,
            },
            "rangeMapHorizontalOuter": {
                "inputMaxValue": look_at_props.range_map_horizontal_outer.input_max_value,
                "outputScale": look_at_props.range_map_horizontal_outer.output_scale,
            },
            "rangeMapVerticalDown": {
                "inputMaxValue": look_at_props.range_map_vertical_down.input_max_value,
                "outputScale": look_at_props.range_map_vertical_down.output_scale,
            },
            "rangeMapVerticalUp": {
                "inputMaxValue": look_at_props.range_map_vertical_up.input_max_value,
                "outputScale": look_at_props.range_map_vertical_up.output_scale,
            },
        }

    @staticmethod
    def create_expression_dict(
        expression_props: Vrm1ExpressionPropertyGroup,
        mesh_name_to_node_index_dict: Dict[str, int],
        mesh_name_to_morph_target_names_dict: Dict[str, List[str]],
        material_name_to_index_dict: Dict[str, int],
    ) -> Dict[str, Any]:
        expression_dict = {
            "isBinary": expression_props.is_binary,
            "overrideBlink": expression_props.override_blink,
            "overrideLookAt": expression_props.override_look_at,
            "overrideMouth": expression_props.override_mouth,
        }
        morph_target_binds = []
        for morph_target_bind_props in expression_props.morph_target_binds:
            if (
                not morph_target_bind_props.node
                or not morph_target_bind_props.node.value
            ):
                continue
            node_index = mesh_name_to_node_index_dict.get(
                morph_target_bind_props.node.value
            )
            if not isinstance(node_index, int):
                continue
            morph_targets = mesh_name_to_morph_target_names_dict.get(
                morph_target_bind_props.node.value
            )
            if not isinstance(morph_targets, list):
                continue
            if morph_target_bind_props.index not in morph_targets:
                continue
            morph_target_binds.append(
                {
                    "node": node_index,
                    "index": morph_targets.index(morph_target_bind_props.index),
                    "weight": morph_target_bind_props.weight,
                }
            )
        if morph_target_binds:
            expression_dict["morphTargetBinds"] = morph_target_binds

        material_color_binds: List[Dict[str, Any]] = []
        for material_color_bind_props in expression_props.material_color_binds:
            if (
                not material_color_bind_props.material
                or material_color_bind_props.material.name
            ):
                continue
            material_index = material_name_to_index_dict.get(
                material_color_bind_props.material.name
            )
            if not isinstance(material_index, int):
                continue
            material_color_binds.append(
                {
                    "material": material_index,
                    "type": material_color_bind_props.type,
                    "targetValue": list(material_color_bind_props.target_value),
                }
            )
        if material_color_binds:
            expression_dict["materialColorBinds"] = material_color_binds

        texture_transform_binds: List[Dict[str, Any]] = []
        for texture_transform_bind_props in expression_props.texture_transform_binds:
            if (
                not texture_transform_bind_props.material
                or texture_transform_bind_props.material.name
            ):
                continue
            material_index = material_name_to_index_dict.get(
                texture_transform_bind_props.material.name
            )
            if not isinstance(material_index, int):
                continue
            texture_transform_binds.append(
                {
                    "material": material_index,
                    "scale": list(texture_transform_bind_props.scale),
                    "offset": list(texture_transform_bind_props.offset),
                }
            )
        if texture_transform_binds:
            expression_dict["textureTransformBinds"] = texture_transform_binds

        return expression_dict

    @staticmethod
    def create_expressions_dict(
        expressions_props: Vrm1ExpressionsPropertyGroup,
        mesh_name_to_node_index_dict: Dict[str, int],
        mesh_name_to_morph_target_names_dict: Dict[str, List[str]],
        material_name_to_index_dict: Dict[str, int],
    ) -> Dict[str, Any]:
        preset_dict = {}
        for (
            preset_name,
            expression_props,
        ) in expressions_props.preset_name_to_expression_dict().items():
            preset_dict[preset_name] = Gltf2AddonVrmExporter.create_expression_dict(
                expression_props,
                mesh_name_to_node_index_dict,
                mesh_name_to_morph_target_names_dict,
                material_name_to_index_dict,
            )
        custom_dict = {}
        for custom_expression_props in expressions_props.custom:
            custom_dict[
                custom_expression_props.custom_name
            ] = Gltf2AddonVrmExporter.create_expression_dict(
                custom_expression_props.expression,
                mesh_name_to_node_index_dict,
                mesh_name_to_morph_target_names_dict,
                material_name_to_index_dict,
            )
        return {
            "preset": preset_dict,
            "custom": custom_dict,
        }

    @staticmethod
    def create_spring_bone_colliders(
        _spring_bone: SpringBone1SpringBonePropertyGroup,
    ) -> List[Dict[str, Any]]:
        return []

    @staticmethod
    def create_spring_bone_collider_groups(
        _spring_bone: SpringBone1SpringBonePropertyGroup,
    ) -> List[Dict[str, Any]]:
        return []

    @staticmethod
    def create_spring_bone_springs(
        _spring_bone: SpringBone1SpringBonePropertyGroup,
    ) -> List[Dict[str, Any]]:
        return []

    def export_vrm(self) -> Optional[bytes]:
        dummy_skinned_mesh_object_name = self.create_dummy_skinned_mesh_object()
        try:
            # 他glTF2ExportUserExtensionの影響を最小化するため、影響が少ないと思われるカスタムプロパティを使ってBlenderのオブジェクトとインデックスの対応をとる。
            for obj in bpy.data.objects:
                obj[self.extras_object_name_key] = obj.name
            for material in bpy.data.materials:
                material[self.extras_material_name_key] = material.name
            for mesh in bpy.data.meshes:
                mesh[self.extras_mesh_name_key] = mesh.name

            # glTF 2.0アドオンのコメントにはPoseBoneとのカスタムプロパティを保存すると書いてあるが、実際にはBoneのカスタムプロパティを参照している。
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
                    export_current_frame=True,
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
            for mesh in bpy.data.meshes:
                if self.extras_mesh_name_key in mesh:
                    del mesh[self.extras_mesh_name_key]
            for material in bpy.data.materials:
                if self.extras_material_name_key in material:
                    del material[self.extras_material_name_key]
            dummy_skinned_mesh_object = bpy.data.objects.get(
                dummy_skinned_mesh_object_name
            )
            if isinstance(dummy_skinned_mesh_object, bpy.types.Object):
                bpy.context.scene.collection.objects.unlink(  # TODO: remove
                    dummy_skinned_mesh_object
                )

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
            if self.extras_bone_name_key in extras_dict:
                del extras_dict[self.extras_bone_name_key]
            if isinstance(bone_name, str):
                bone_name_to_index_dict[bone_name] = node_index

            object_name = extras_dict.get(self.extras_object_name_key)
            if self.extras_object_name_key in extras_dict:
                del extras_dict[self.extras_object_name_key]
            if isinstance(object_name, str) and (
                object_name == dummy_skinned_mesh_object_name
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

                # TODO: remove from scenes, skin joints ...

            if not extras_dict and "extras" in node_dict:
                del node_dict["extras"]

        material_name_to_index_dict: Dict[str, int] = {}
        materials = json_dict.get("materials")
        if not isinstance(materials, abc.Iterable):
            materials = []
        for material_index, material_dict in enumerate(materials):
            if not isinstance(material_dict, dict):
                continue
            extras_dict = material_dict.get("extras")
            if not isinstance(extras_dict, dict):
                continue

            material_name = extras_dict.get(self.extras_material_name_key)
            if self.extras_material_name_key in extras_dict:
                del extras_dict[self.extras_material_name_key]
            if not isinstance(material_name, str):
                continue

            material_name_to_index_dict[material_name] = material_index
            if not extras_dict:
                del material_dict["extras"]

        mesh_name_to_node_index_dict: Dict[str, int] = {}
        mesh_name_to_morph_target_names_dict: Dict[str, List[str]] = {}
        meshes = json_dict.get("meshes")
        if not isinstance(meshes, abc.Iterable):
            meshes = []
        for mesh_index, mesh_dict in enumerate(meshes):
            if not isinstance(mesh_dict, dict):
                continue
            extras_dict = mesh_dict.get("extras")
            if not isinstance(extras_dict, dict):
                continue

            mesh_name = extras_dict.get(self.extras_mesh_name_key)
            if self.extras_mesh_name_key in extras_dict:
                del extras_dict[self.extras_mesh_name_key]
            if not isinstance(mesh_name, str):
                continue

            target_names = extras_dict.get("targetNames")
            if isinstance(target_names, abc.Iterable):
                mesh_name_to_morph_target_names_dict[mesh_name] = list(target_names)

            for node_index, node_dict in enumerate(nodes):
                if not isinstance(node_dict, dict):
                    continue
                if node_dict.get("mesh") == mesh_index:
                    # FIXME: 複数のオブジェクトが同一のメッシュを参照している場合やばい
                    mesh_name_to_node_index_dict[mesh_name] = node_index
                    break

            mesh_name_to_node_index_dict[mesh_name] = mesh_index
            if not extras_dict:
                del mesh_dict["extras"]

        vrm_props = self.armature.data.vrm_addon_extension.vrm1

        extensions_used = json_dict.get("extensionsUsed")
        if not isinstance(extensions_used, abc.Iterable):
            extensions_used = []
        else:
            extensions_used = list(extensions_used)
        extensions_used.extend(["VRMC_vrm", "VRMC_springBone"])
        json_dict["extensionsUsed"] = extensions_used

        extensions = json_dict.get("extensions")
        if not isinstance(extensions, dict):
            extensions = {}
        extensions["VRMC_vrm"] = {
            "specVersion": self.armature.data.vrm_addon_extension.spec_version,
            "meta": self.create_meta_dict(vrm_props.meta),
            "humanoid": self.create_humanoid_dict(
                vrm_props.humanoid, bone_name_to_index_dict
            ),
            "firstPerson": self.create_first_person_dict(
                vrm_props.first_person, mesh_name_to_node_index_dict
            ),
            "lookAt": self.create_look_at_dict(vrm_props.look_at),
            "expressions": self.create_expressions_dict(
                vrm_props.expressions,
                mesh_name_to_node_index_dict,
                mesh_name_to_morph_target_names_dict,
                material_name_to_index_dict,
            ),
        }

        spring_bone_props = self.armature.data.vrm_addon_extension.spring_bone1
        extensions["VRMC_springBone"] = {
            "specVersion": self.armature.data.vrm_addon_extension.spec_version,
            "colliders": self.create_spring_bone_colliders(spring_bone_props),
            "colliderGroups": self.create_spring_bone_collider_groups(
                spring_bone_props
            ),
            "springs": self.create_spring_bone_springs(spring_bone_props),
        }
        json_dict["extensions"] = extensions

        v = version.version()
        if os.environ.get("BLENDER_VRM_USE_TEST_EXPORTER_VERSION") == "true":
            v = (999, 999, 999)

        generator = "VRM Add-on for Blender v" + ".".join(map(str, v))

        base_generator = deep.get(json_dict, ["asset", "generator"])
        if isinstance(base_generator, str):
            generator += " with " + base_generator

        json_dict["asset"]["generator"] = generator

        return gltf.pack_glb(json_dict, body_binary)
