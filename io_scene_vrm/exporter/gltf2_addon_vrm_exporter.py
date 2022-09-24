import math
import os
import secrets
import string
import tempfile
from collections import abc
from sys import float_info
from typing import Any, Dict, List, Optional, Tuple, Union

import bpy

from ..common import convert, deep, gltf, shader, version
from ..common.char import INTERNAL_NAME_PREFIX
from ..editor import search
from ..editor.mtoon1.property_group import Mtoon1TextureInfoPropertyGroup
from ..editor.spring_bone1.property_group import SpringBone1SpringBonePropertyGroup
from ..editor.vrm1.property_group import (
    Vrm1ExpressionPropertyGroup,
    Vrm1ExpressionsPropertyGroup,
    Vrm1FirstPersonPropertyGroup,
    Vrm1HumanoidPropertyGroup,
    Vrm1LookAtPropertyGroup,
    Vrm1MetaPropertyGroup,
)
from ..external.io_scene_gltf2_support import image_to_image_bytes
from .abstract_base_vrm_exporter import AbstractBaseVrmExporter, assign_dict


class Gltf2AddonVrmExporter(AbstractBaseVrmExporter):
    def __init__(
        self, context: bpy.types.Context, export_objects: List[bpy.types.Object]
    ) -> None:
        super().__init__(context)
        self.export_objects = export_objects
        armatures = [obj for obj in export_objects if obj.type == "ARMATURE"]
        if not armatures:
            raise NotImplementedError("アーマチュア無しエクスポートはまだ未対応")
        self.armature = armatures[0]

        for collider in self.armature.data.vrm_addon_extension.spring_bone1.colliders:
            if not collider.bpy_object:
                continue
            if collider.bpy_object in self.export_objects:
                self.export_objects.remove(collider.bpy_object)
            for child in collider.bpy_object.children:
                if child in self.export_objects:
                    self.export_objects.remove(child)

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
        self.object_visibility_and_selection: Dict[str, Tuple[bool, bool]] = {}
        self.mounted_object_names: List[str] = []

    def overwrite_object_visibility_and_selection(self) -> None:
        self.object_visibility_and_selection.clear()
        for obj in self.context.view_layer.objects:
            self.object_visibility_and_selection[obj.name] = (
                obj.hide_get(),
                obj.select_get(),
            )
            enabled = obj in self.export_objects
            obj.hide_set(not enabled)
            obj.select_set(enabled)

    def restore_object_visibility_and_selection(self) -> None:
        for object_name, (
            hidden,
            selection,
        ) in self.object_visibility_and_selection.items():
            obj = bpy.data.objects.get(object_name)
            if obj:
                obj.hide_set(hidden)
                obj.select_set(selection)

    def mount_skinned_mesh_parent(self) -> None:
        armature = self.armature
        if not armature:
            return

        # Blender 3.1.2付属アドオンのglTF 2.0エクスポート処理には次の条件をすべて満たすとき
        # inverseBindMatricesが不正なglbが出力される:
        # - アーマチュアの子孫になっていないメッシュがそのアーマチュアのボーンにスキニングされている
        # - スキニングされたボーンの子供に別のメッシュが存在する
        # そのため、アーマチュアの子孫になっていないメッシュの先祖の親をアーマチュアにし、後で戻す
        for obj in self.export_objects:
            if obj.type != "MESH" or not [
                True
                for m in obj.modifiers
                if isinstance(m, bpy.types.ArmatureModifier) and m.object == armature
            ]:
                continue

            while obj != armature:
                if obj.parent:
                    obj = obj.parent
                    continue
                self.mounted_object_names.append(obj.name)
                matrix_world = obj.matrix_world
                obj.parent = armature
                obj.matrix_world = matrix_world
                break

    def restore_skinned_mesh_parent(self) -> None:
        for mounted_object_name in self.mounted_object_names:
            obj = bpy.data.objects.get(mounted_object_name)
            if not obj:
                continue
            matrix_world = obj.matrix_world
            obj.parent = None
            obj.matrix_world = matrix_world

    def create_dummy_skinned_mesh_object(self) -> str:
        vertices = []
        edges = []
        faces = []
        for index, _ in enumerate(self.armature.pose.bones):
            vertices.extend(
                [
                    (index / 16.0, 0, 0),
                    ((index + 1) / 16.0, 0, 1 / 16.0),
                    ((index + 1) / 16.0, 0, 0),
                ]
            )
            edges.extend(
                [
                    (index * 3 + 0, index * 3 + 1),
                    (index * 3 + 1, index * 3 + 2),
                    (index * 3 + 2, index * 3 + 0),
                ]
            )
            faces.append((index * 3, index * 3 + 1, index * 3 + 2))

        mesh = bpy.data.meshes.new(self.export_id + "_mesh")
        mesh.from_pydata(vertices, edges, faces)
        mesh.update()
        if mesh.validate():
            raise ValueError("Invalid geometry")
        obj = bpy.data.objects.new("secondary", mesh)
        obj.parent_type = "OBJECT"
        obj.parent = self.armature
        for index, bone_name in enumerate(self.armature.data.bones.keys()):
            vertex_group = obj.vertex_groups.new(name=bone_name)
            vertex_group.add([index * 3, index * 3 + 1, index * 3 + 2], 1.0, "ADD")
        modifier = obj.modifiers.new(name="Armature", type="ARMATURE")
        modifier.object = self.armature
        self.context.scene.collection.objects.link(obj)
        obj[self.extras_object_name_key] = obj.name
        return str(obj.name)

    def destroy_dummy_skinned_mesh_object(self, name: str) -> None:
        dummy_skinned_mesh_object = bpy.data.objects.get(name)
        if not isinstance(dummy_skinned_mesh_object, bpy.types.Object):
            return
        dummy_skinned_mesh_object.modifiers.clear()
        dummy_skinned_mesh_object.vertex_groups.clear()
        self.context.scene.collection.objects.unlink(  # TODO: remove completely
            dummy_skinned_mesh_object
        )

    @staticmethod
    def create_meta_dict(meta: Vrm1MetaPropertyGroup) -> Dict[str, Any]:
        meta_dict: Dict[str, Union[str, bool, List[str]]] = {
            "licenseUrl": "https://vrm.dev/licenses/1.0/",
            "name": meta.vrm_name if meta.vrm_name else "undefined",
            "version": meta.version if meta.version else "undefined",
            "avatarPermission": meta.avatar_permission,
            "allowExcessivelyViolentUsage": meta.allow_excessively_violent_usage,
            "allowExcessivelySexualUsage": meta.allow_excessively_sexual_usage,
            "commercialUsage": meta.commercial_usage,
            "allowPoliticalOrReligiousUsage": meta.allow_political_or_religious_usage,
            "allowAntisocialOrHateUsage": meta.allow_antisocial_or_hate_usage,
            "creditNotation": meta.credit_notation,
            "allowRedistribution": meta.allow_redistribution,
            "modification": meta.modification,
        }

        authors = [author.value for author in meta.authors if author.value]
        if not authors:
            authors = ["undefined"]
        meta_dict["authors"] = authors

        if meta.copyright_information:
            meta_dict["copyrightInformation"] = meta.copyright_information

        references = [
            reference.value for reference in meta.references if reference.value
        ]
        if references:
            meta_dict["references"] = references

        if meta.third_party_licenses:
            meta_dict["thirdPartyLicenses"] = meta.third_party_licenses

        if meta.other_license_url:
            meta_dict["otherLicenseUrl"] = meta.other_license_url

        return meta_dict

    @staticmethod
    def create_humanoid_dict(
        humanoid: Vrm1HumanoidPropertyGroup,
        bone_name_to_index_dict: Dict[str, int],
    ) -> Dict[str, Any]:
        human_bones_dict: Dict[str, Any] = {}
        for (
            human_bone_name,
            human_bone,
        ) in humanoid.human_bones.human_bone_name_to_human_bone().items():
            index = bone_name_to_index_dict.get(human_bone.node.value)
            if isinstance(index, int):
                human_bones_dict[human_bone_name.value] = {"node": index}

        return {
            "humanBones": human_bones_dict,
        }

    @staticmethod
    def create_first_person_dict(
        first_person: Vrm1FirstPersonPropertyGroup,
        mesh_object_name_to_node_index_dict: Dict[str, int],
    ) -> Dict[str, Any]:
        mesh_annotation_dicts: List[Dict[str, Any]] = []
        for mesh_annotation in first_person.mesh_annotations:
            if not mesh_annotation.node or not mesh_annotation.node.value:
                continue
            node_index = mesh_object_name_to_node_index_dict.get(
                mesh_annotation.node.value
            )
            if not isinstance(node_index, int):
                continue
            mesh_annotation_dicts.append(
                {
                    "node": node_index,
                    "type": mesh_annotation.type,
                }
            )
        if not mesh_annotation_dicts:
            return {}
        return {"meshAnnotations": mesh_annotation_dicts}

    @staticmethod
    def create_look_at_dict(
        look_at: Vrm1LookAtPropertyGroup,
    ) -> Dict[str, Any]:
        return {
            "offsetFromHeadBone": list(look_at.offset_from_head_bone),
            "type": look_at.type,
            "rangeMapHorizontalInner": {
                "inputMaxValue": look_at.range_map_horizontal_inner.input_max_value,
                "outputScale": look_at.range_map_horizontal_inner.output_scale,
            },
            "rangeMapHorizontalOuter": {
                "inputMaxValue": look_at.range_map_horizontal_outer.input_max_value,
                "outputScale": look_at.range_map_horizontal_outer.output_scale,
            },
            "rangeMapVerticalDown": {
                "inputMaxValue": look_at.range_map_vertical_down.input_max_value,
                "outputScale": look_at.range_map_vertical_down.output_scale,
            },
            "rangeMapVerticalUp": {
                "inputMaxValue": look_at.range_map_vertical_up.input_max_value,
                "outputScale": look_at.range_map_vertical_up.output_scale,
            },
        }

    @staticmethod
    def create_expression_dict(
        expression: Vrm1ExpressionPropertyGroup,
        mesh_object_name_to_node_index_dict: Dict[str, int],
        mesh_object_name_to_morph_target_names_dict: Dict[str, List[str]],
        material_name_to_index_dict: Dict[str, int],
    ) -> Dict[str, Any]:
        expression_dict = {
            "isBinary": expression.is_binary,
            "overrideBlink": expression.override_blink,
            "overrideLookAt": expression.override_look_at,
            "overrideMouth": expression.override_mouth,
        }
        morph_target_bind_dicts = []
        for morph_target_bind in expression.morph_target_binds:
            if not morph_target_bind.node or not morph_target_bind.node.value:
                continue
            node_index = mesh_object_name_to_node_index_dict.get(
                morph_target_bind.node.value
            )
            if not isinstance(node_index, int):
                continue
            morph_targets = mesh_object_name_to_morph_target_names_dict.get(
                morph_target_bind.node.value
            )
            if not isinstance(morph_targets, list):
                continue
            if morph_target_bind.index not in morph_targets:
                continue
            morph_target_bind_dicts.append(
                {
                    "node": node_index,
                    "index": morph_targets.index(morph_target_bind.index),
                    "weight": morph_target_bind.weight,
                }
            )
        if morph_target_bind_dicts:
            expression_dict["morphTargetBinds"] = morph_target_bind_dicts

        material_color_bind_dicts: List[Dict[str, Any]] = []
        for material_color_bind in expression.material_color_binds:
            if not material_color_bind.material or material_color_bind.material.name:
                continue
            material_index = material_name_to_index_dict.get(
                material_color_bind.material.name
            )
            if not isinstance(material_index, int):
                continue
            material_color_bind_dicts.append(
                {
                    "material": material_index,
                    "type": material_color_bind.type,
                    "targetValue": list(material_color_bind.target_value),
                }
            )
        if material_color_bind_dicts:
            expression_dict["materialColorBinds"] = material_color_bind_dicts

        texture_transform_binds: List[Dict[str, Any]] = []
        for texture_transform_bind in expression.texture_transform_binds:
            if (
                not texture_transform_bind.material
                or texture_transform_bind.material.name
            ):
                continue
            material_index = material_name_to_index_dict.get(
                texture_transform_bind.material.name
            )
            if not isinstance(material_index, int):
                continue
            texture_transform_binds.append(
                {
                    "material": material_index,
                    "scale": list(texture_transform_bind.scale),
                    "offset": list(texture_transform_bind.offset),
                }
            )
        if texture_transform_binds:
            expression_dict["textureTransformBinds"] = texture_transform_binds

        return expression_dict

    @staticmethod
    def create_expressions_dict(
        expressions: Vrm1ExpressionsPropertyGroup,
        mesh_object_name_to_node_index_dict: Dict[str, int],
        mesh_object_name_to_morph_target_names_dict: Dict[str, List[str]],
        material_name_to_index_dict: Dict[str, int],
    ) -> Dict[str, Any]:
        preset_dict = {}
        for (
            preset_name,
            expression,
        ) in expressions.preset_name_to_expression_dict().items():
            preset_dict[preset_name] = Gltf2AddonVrmExporter.create_expression_dict(
                expression,
                mesh_object_name_to_node_index_dict,
                mesh_object_name_to_morph_target_names_dict,
                material_name_to_index_dict,
            )
        custom_dict = {}
        for custom_expression in expressions.custom:
            custom_dict[
                custom_expression.custom_name
            ] = Gltf2AddonVrmExporter.create_expression_dict(
                custom_expression.expression,
                mesh_object_name_to_node_index_dict,
                mesh_object_name_to_morph_target_names_dict,
                material_name_to_index_dict,
            )
        return {
            "preset": preset_dict,
            "custom": custom_dict,
        }

    @staticmethod
    def create_spring_bone_collider_dicts(
        spring_bone: SpringBone1SpringBonePropertyGroup,
        bone_name_to_index_dict: Dict[str, int],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        collider_dicts: List[Dict[str, Any]] = []
        collider_uuid_to_index_dict = {}
        for collider in spring_bone.colliders:
            collider_dict: Dict[str, Any] = {}
            node_index = bone_name_to_index_dict.get(collider.node.value)
            if not isinstance(node_index, int):
                continue
            collider_dict["node"] = node_index

            if collider.shape_type == collider.SHAPE_TYPE_SPHERE:
                shape_dict = {
                    "sphere": {
                        "offset": list(collider.shape.sphere.offset),
                        "radius": collider.shape.sphere.radius,
                    }
                }
            elif collider.shape_type == collider.SHAPE_TYPE_CAPSULE:
                shape_dict = {
                    "capsule": {
                        "offset": list(collider.shape.capsule.offset),
                        "radius": collider.shape.capsule.radius,
                        "tail": list(collider.shape.capsule.tail),
                    }
                }
            else:
                continue

            collider_dict["shape"] = shape_dict
            collider_uuid_to_index_dict[collider.uuid] = len(collider_dicts)
            collider_dicts.append(collider_dict)

        return collider_dicts, collider_uuid_to_index_dict

    @staticmethod
    def create_spring_bone_collider_group_dicts(
        spring_bone: SpringBone1SpringBonePropertyGroup,
        collider_uuid_to_index_dict: Dict[str, int],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        collider_group_dicts: List[Dict[str, Any]] = []
        collider_group_uuid_to_index_dict = {}
        for collider_group in spring_bone.collider_groups:
            collider_group_dict = {"name": collider_group.vrm_name}
            collider_indices = []
            for collider_reference in collider_group.colliders:
                collider_index = collider_uuid_to_index_dict.get(
                    collider_reference.collider_uuid
                )
                if isinstance(collider_index, int):
                    collider_indices.append(collider_index)
            if collider_indices:
                collider_group_dict["colliders"] = collider_indices
            else:
                # 空のコライダーグループは仕様Validだが、UniVRM 0.98.0はこれを読み飛ばし
                # Springからのインデックス参照はそのままでずれるバグがあるので出力しない
                continue

            collider_group_uuid_to_index_dict[collider_group.uuid] = len(
                collider_group_dicts
            )
            collider_group_dicts.append(collider_group_dict)

        return collider_group_dicts, collider_group_uuid_to_index_dict

    @staticmethod
    def create_spring_bone_spring_dicts(
        spring_bone: SpringBone1SpringBonePropertyGroup,
        bone_name_to_index_dict: Dict[str, int],
        collider_group_uuid_to_index_dict: Dict[str, int],
    ) -> List[Dict[str, Any]]:
        spring_dicts = []
        for spring in spring_bone.springs:
            spring_dict = {"name": spring.vrm_name}

            center_index = bone_name_to_index_dict.get(spring.center.value)
            if isinstance(center_index, int):
                spring_dict["center"] = center_index

            joint_dicts = []
            for joint in spring.joints:
                node_index = bone_name_to_index_dict.get(joint.node.value)
                if not isinstance(node_index, int):
                    continue
                joint_dicts.append(
                    {
                        "node": node_index,
                        "hitRadius": joint.hit_radius,
                        "stiffness": joint.stiffness,
                        "gravityPower": joint.gravity_power,
                        "gravityDir": list(joint.gravity_dir),
                        "dragForce": joint.drag_force,
                    }
                )

            if joint_dicts:
                spring_dict["joints"] = joint_dicts

            collider_group_indices = []
            for collider_group_reference in spring.collider_groups:
                collider_group_index = collider_group_uuid_to_index_dict.get(
                    collider_group_reference.collider_group_uuid
                )
                if isinstance(collider_group_index, int):
                    collider_group_indices.append(collider_group_index)

            if collider_group_indices:
                spring_dict["colliderGroups"] = collider_group_indices

            spring_dicts.append(spring_dict)
        return spring_dicts

    @staticmethod
    def search_constraint_target_index(
        constraint: Union[
            bpy.types.CopyRotationConstraint, bpy.types.DampedTrackConstraint
        ],
        object_name_to_index_dict: Dict[str, int],
        bone_name_to_index_dict: Dict[str, int],
    ) -> Optional[int]:
        if constraint.target.type == "ARMATURE" and constraint.subtarget:
            return bone_name_to_index_dict.get(constraint.subtarget)
        return object_name_to_index_dict.get(constraint.target.name)

    @staticmethod
    def create_constraint_dict(
        name: str,
        constraints: search.ExportConstraint,
        object_name_to_index_dict: Dict[str, int],
        bone_name_to_index_dict: Dict[str, int],
    ) -> Dict[str, Any]:
        roll_constraint = constraints.roll_constraints.get(name)
        aim_constraint = constraints.aim_constraints.get(name)
        rotation_constraint = constraints.rotation_constraints.get(name)
        constraint_dict = {}
        if roll_constraint:
            source_index = Gltf2AddonVrmExporter.search_constraint_target_index(
                roll_constraint,
                object_name_to_index_dict,
                bone_name_to_index_dict,
            )
            if isinstance(source_index, int):
                if roll_constraint.use_x:
                    roll_axis = "X"
                elif roll_constraint.use_y:
                    roll_axis = "Y"
                elif roll_constraint.use_z:
                    roll_axis = "Z"
                else:
                    raise ValueError("Unsupported roll axis")
                constraint_dict["roll"] = {
                    "source": source_index,
                    "rollAxis": roll_axis,
                    "weight": max(0.0, min(1.0, roll_constraint.influence)),
                }
        elif aim_constraint:
            source_index = Gltf2AddonVrmExporter.search_constraint_target_index(
                aim_constraint,
                object_name_to_index_dict,
                bone_name_to_index_dict,
            )
            if isinstance(source_index, int):
                constraint_dict["aim"] = {
                    "source": source_index,
                    "aimAxis": convert.BPY_TRACK_AXIS_TO_VRM_AIM_AXIS[
                        aim_constraint.track_axis
                    ],
                    "weight": max(0.0, min(1.0, aim_constraint.influence)),
                }
        elif rotation_constraint:
            source_index = Gltf2AddonVrmExporter.search_constraint_target_index(
                rotation_constraint,
                object_name_to_index_dict,
                bone_name_to_index_dict,
            )
            if isinstance(source_index, int):
                constraint_dict["rotation"] = {
                    "source": source_index,
                    "weight": max(0.0, min(1.0, rotation_constraint.influence)),
                }
        return constraint_dict

    @staticmethod
    def create_mtoon0_khr_texture_transform(
        node: bpy.types.Node, texture_input_name: str
    ) -> Dict[str, Any]:
        default = {
            "offset": [0, 0],
            "scale": [1, 1],
        }

        texture_input = node.inputs.get(texture_input_name)
        if not texture_input:
            return default

        texture_input_links = texture_input.links
        if not texture_input_links:
            return default

        x_from_node = texture_input_links[0].from_node
        if not x_from_node:
            return default

        x_inputs = x_from_node.inputs
        if not x_inputs:
            return default

        x_links = x_inputs[0].links
        if not x_links:
            return default

        uv_offset_scaling_node = x_links[0].from_node
        if not uv_offset_scaling_node or uv_offset_scaling_node.type != "MAPPING'":
            return default

        location_input = uv_offset_scaling_node.inputs["Location"]
        scale_input = uv_offset_scaling_node.inputs["Scale"]
        return {
            "offset": [
                location_input.default_value[0],
                location_input.default_value[1],
            ],
            "scale": [
                scale_input.default_value[0],
                scale_input.default_value[1],
            ],
        }

    @staticmethod
    def create_mtoon1_texture_info_dict(
        json_dict: Dict[str, Any],
        body_binary: bytearray,
        texture_info: Mtoon1TextureInfoPropertyGroup,
    ) -> Optional[Dict[str, Any]]:
        # TODO: Verify alignment requirement and optimize
        while len(body_binary) % 32 == 0:
            body_binary.append(0)

        image = texture_info.index.source
        if not image:
            return None

        image_bytes, mime = image_to_image_bytes(image)
        image_buffer_view_index = len(json_dict["bufferViews"])
        json_dict["bufferViews"].append(
            {
                "buffer": 0,
                "byteOffset": len(body_binary),
                "byteLength": len(image_bytes),
            }
        )

        image_index = len(json_dict["images"])
        json_dict["images"].append(
            {
                "bufferView": image_buffer_view_index,
                "mimeType": mime,
            }
        )

        if "samplers" not in json_dict:
            json_dict["samplers"] = []
        sampler_index = len(json_dict["samplers"])
        json_dict["samplers"].append(
            {
                "magFilter": texture_info.index.sampler.mag_filter,
                "minFilter": texture_info.index.sampler.min_filter,
                "wrapS": texture_info.index.sampler.wrap_type,
                "wrapT": texture_info.index.sampler.wrap_type,
            }
        )

        if "textures" not in json_dict:
            json_dict["textures"] = []
        texture_index = len(json_dict["textures"])
        json_dict["textures"].append(
            {
                "sampler": sampler_index,
                "source": image_index,
            },
        )

        body_binary.extend(image_bytes)
        # TODO: Verify alignment requirement and optimize
        while len(body_binary) % 32 == 0:
            body_binary.append(0)

        extensions_used = json_dict["extensionsUsed"]

        if "KHR_texture_transform" not in extensions_used:
            extensions_used.append("KHR_texture_transform")
        json_dict["extensionsUsed"] = extensions_used

        khr_texture_transform = texture_info.extensions.khr_texture_transform
        khr_texture_transform_dict = {
            "offset": list(khr_texture_transform.offset),
            "scale": list(khr_texture_transform.scale),
        }

        return {
            "index": texture_index,
            "extensions": {"KHR_texture_transform": khr_texture_transform_dict},
        }

    @staticmethod
    def create_mtoon0_texture_info_dict(
        json_dict: Dict[str, Any],
        body_binary: bytearray,
        node: bpy.types.Node,
        texture_input_name: str,
    ) -> Optional[Dict[str, Any]]:
        image_name_and_sampler_type = shader.get_image_name_and_sampler_type(
            node, texture_input_name
        )
        if image_name_and_sampler_type is None:
            return None

        # TODO: Verify alignment requirement and optimize
        while len(body_binary) % 32 == 0:
            body_binary.append(0)

        image_name, wrap_type, filter_type = image_name_and_sampler_type
        image_bytes, mime = image_to_image_bytes(bpy.data.images[image_name])

        image_buffer_view_index = len(json_dict["bufferViews"])
        json_dict["bufferViews"].append(
            {
                "buffer": 0,
                "byteOffset": len(body_binary),
                "byteLength": len(image_bytes),
            }
        )

        image_index = len(json_dict["images"])
        json_dict["images"].append(
            {
                "bufferView": image_buffer_view_index,
                "mimeType": mime,
            }
        )

        if "samplers" not in json_dict:
            json_dict["samplers"] = []
        sampler_index = len(json_dict["samplers"])
        json_dict["samplers"].append(
            {
                "magFilter": filter_type,
                "minFilter": filter_type,
                "wrapS": wrap_type,
                "wrapT": wrap_type,
            }
        )

        if "textures" not in json_dict:
            json_dict["textures"] = []
        texture_index = len(json_dict["textures"])
        json_dict["textures"].append(
            {
                "sampler": sampler_index,
                "source": image_index,
            },
        )

        body_binary.extend(image_bytes)
        # TODO: Verify alignment requirement and optimize
        while len(body_binary) % 32 == 0:
            body_binary.append(0)

        extensions_used = json_dict["extensionsUsed"]

        if "KHR_texture_transform" not in extensions_used:
            extensions_used.append("KHR_texture_transform")
        json_dict["extensionsUsed"] = extensions_used

        khr_texture_transform_dict = (
            Gltf2AddonVrmExporter.create_mtoon0_khr_texture_transform(
                node, texture_input_name
            )
        )

        return {
            "index": texture_index,
            "extensions": {"KHR_texture_transform": khr_texture_transform_dict},
        }

    @staticmethod
    def lerp(a: float, b: float, t: float) -> float:
        return (1 - t) * a + t * b

    # https://github.com/vrm-c/UniVRM/blob/f3479190c330ec6ecd2b40be919285aa93a53aff/Assets/VRMShaders/VRM10/MToon10/Runtime/MToon10Migrator.cs#L10-L19
    @staticmethod
    def migrate_to_shading_toony(
        shading_toony_0x: float, shading_shift_0x: float
    ) -> float:
        (range_min, range_max) = Gltf2AddonVrmExporter.get_shading_range_0x(
            shading_toony_0x, shading_shift_0x
        )
        return max(0, min(1, (2 - (range_max - range_min)) * 0.5))

    # https://github.com/vrm-c/UniVRM/blob/f3479190c330ec6ecd2b40be919285aa93a53aff/Assets/VRMShaders/VRM10/MToon10/Runtime/MToon10Migrator.cs#L21-L30
    @staticmethod
    def migrate_to_shading_shift(
        shading_toony_0x: float, shading_shift_0x: float
    ) -> float:
        (range_min, range_max) = Gltf2AddonVrmExporter.get_shading_range_0x(
            shading_toony_0x, shading_shift_0x
        )
        return max(-1, min(1, ((range_max + range_min) * 0.5 * -1)))

    # https://github.com/vrm-c/UniVRM/blob/f3479190c330ec6ecd2b40be919285aa93a53aff/Assets/VRMShaders/VRM10/MToon10/Runtime/MToon10Migrator.cs#L32-L38
    @staticmethod
    def migrate_to_gi_equalization(gi_intensity_0x: float) -> float:
        return max(0, min(1, 1 - gi_intensity_0x))

    # https://github.com/vrm-c/UniVRM/blob/f3479190c330ec6ecd2b40be919285aa93a53aff/Assets/VRMShaders/VRM10/MToon10/Runtime/MToon10Migrator.cs#L40-L46
    @staticmethod
    def get_shading_range_0x(
        shading_toony_0x: float, shading_shift_0x: float
    ) -> Tuple[float, float]:
        range_min = shading_shift_0x
        range_max = (1 - shading_toony_0x) + shading_toony_0x * shading_shift_0x
        return (range_min, range_max)

    @staticmethod
    def create_mtoon1_material_dict(
        json_dict: Dict[str, Any],
        body_binary: bytearray,
        material: bpy.types.Material,
    ) -> Dict[str, Any]:
        extensions_used = json_dict["extensionsUsed"]

        if "KHR_materials_unlit" not in extensions_used:
            extensions_used.append("KHR_materials_unlit")
        if "VRMC_materials_mtoon" not in extensions_used:
            extensions_used.append("VRMC_materials_mtoon")

        # https://github.com/vrm-c/UniVRM/blob/f3479190c330ec6ecd2b40be919285aa93a53aff/Assets/VRM10/Runtime/Migration/Materials/MigrationMToonMaterial.cs
        mtoon_dict: Dict[str, Any] = {
            "specVersion": "1.0",
        }
        extensions_dict = {
            "KHR_materials_unlit": {},
            "VRMC_materials_mtoon": mtoon_dict,
        }

        root = material.vrm_addon_extension.mtoon1
        mtoon = root.extensions.vrmc_materials_mtoon

        material_dict: Dict[str, Any] = {}
        pbr_metallic_roughness_dict: Dict[str, Any] = {}

        material_dict["alphaMode"] = root.alpha_mode
        mtoon_dict["transparentWithZWrite"] = mtoon.transparent_with_z_write
        mtoon_dict["renderQueueOffsetNumber"] = mtoon.render_queue_offset_number
        material_dict["alphaCutoff"] = root.alpha_cutoff
        material_dict["doubleSided"] = root.double_sided
        pbr_metallic_roughness_dict["baseColorFactor"] = list(
            root.pbr_metallic_roughness.base_color_factor
        )
        assign_dict(
            pbr_metallic_roughness_dict,
            "baseColorTexture",
            Gltf2AddonVrmExporter.create_mtoon1_texture_info_dict(
                json_dict, body_binary, root.pbr_metallic_roughness.base_color_texture
            ),
        )
        mtoon_dict["shadeColorFactor"] = list(mtoon.shade_color_factor)
        assign_dict(
            mtoon_dict,
            "shadeMultiplyTexture",
            Gltf2AddonVrmExporter.create_mtoon1_texture_info_dict(
                json_dict, body_binary, mtoon.shade_color_texture
            ),
        )
        if assign_dict(
            material_dict,
            "normalTexture",
            Gltf2AddonVrmExporter.create_mtoon1_texture_info_dict(
                json_dict, body_binary, root.normal_texture
            ),
        ):
            material_dict["normalTexture"]["scale"] = root.normal_texture.scale
        mtoon_dict["shadingShiftFactor"] = mtoon.shading_shift_factor
        mtoon_dict["shadingToonyFactor"] = mtoon.shading_toony_factor
        mtoon_dict["giEqualizationFactor"] = mtoon.gi_equalization_factor
        material_dict["emissiveFactor"] = root.emissive_factor
        assign_dict(
            material_dict,
            "emissiveTexture",
            Gltf2AddonVrmExporter.create_mtoon1_texture_info_dict(
                json_dict, body_binary, root.emissive_texture
            ),
        )
        assign_dict(
            mtoon_dict,
            "matcapTexture",
            Gltf2AddonVrmExporter.create_mtoon1_texture_info_dict(
                json_dict, body_binary, mtoon.matcap_Texture
            ),
        )
        mtoon_dict["parametricRimColorFactor"] = list(mtoon.parametric_rim_color_factor)
        mtoon_dict[
            "parametricRimFresnelPowerFactor"
        ] = mtoon.parametric_rim_fresnel_power_factor
        mtoon_dict["parametricRimLiftFactor"] = mtoon.parametric_rim_lift_factor
        assign_dict(
            mtoon_dict,
            "rimMultiplyTexture",
            Gltf2AddonVrmExporter.create_mtoon1_texture_info_dict(
                json_dict, body_binary, mtoon.rim_multiply_texture
            ),
        )
        mtoon_dict["rimLightingMixFactor"] = mtoon.rim_lighting_mix_factor
        mtoon_dict["outlineWidthMode"] = mtoon.outline_width_mode
        mtoon_dict["outlineWidthFactor"] = mtoon.outline_width_factor
        assign_dict(
            mtoon_dict,
            "outlineWidthMultiplyTexture",
            Gltf2AddonVrmExporter.create_mtoon1_texture_info_dict(
                json_dict, body_binary, mtoon.outline_width_multiply_texture
            ),
        )
        mtoon_dict["outlineColorFactor"] = mtoon.outline_color_factor
        mtoon_dict["outlineLightingMixFactor"] = mtoon.outline_lighting_mix_factor
        assign_dict(
            mtoon_dict,
            "uvAnimationMaskTexture",
            Gltf2AddonVrmExporter.create_mtoon1_texture_info_dict(
                json_dict, body_binary, mtoon.uv_animation_mask_texture
            ),
        )
        mtoon_dict[
            "uvAnimationRotationSpeedFactor"
        ] = mtoon.uv_animation_rotation_speed_factor
        mtoon_dict[
            "uvAnimationScrollXSpeedFactor"
        ] = mtoon.uv_animation_scroll_x_speed_factor
        mtoon_dict[
            "uvAnimationScrollYSpeedFactor"
        ] = mtoon.uv_animation_scroll_y_speed_factor

        if pbr_metallic_roughness_dict:
            material_dict["pbrMetallicRoughness"] = pbr_metallic_roughness_dict

        extensions_dict["VRMC_materials_mtoon"] = mtoon_dict
        material_dict["extensions"] = extensions_dict

        return material_dict

    @staticmethod
    def create_mtoon_unversioned_material_dict(
        json_dict: Dict[str, Any],
        body_binary: bytearray,
        material: bpy.types.Material,
        node: bpy.types.Node,
    ) -> Dict[str, Any]:
        extensions_used = json_dict["extensionsUsed"]

        if "KHR_materials_unlit" not in extensions_used:
            extensions_used.append("KHR_materials_unlit")
        if "VRMC_materials_mtoon" not in extensions_used:
            extensions_used.append("VRMC_materials_mtoon")

        # https://github.com/vrm-c/UniVRM/blob/f3479190c330ec6ecd2b40be919285aa93a53aff/Assets/VRM10/Runtime/Migration/Materials/MigrationMToonMaterial.cs
        mtoon_dict: Dict[str, Any] = {
            "specVersion": "1.0",
        }
        extensions_dict = {
            "KHR_materials_unlit": {},
            "VRMC_materials_mtoon": mtoon_dict,
        }

        material_dict: Dict[str, Any] = {}
        pbr_metallic_roughness_dict: Dict[str, Any] = {}

        if material.blend_method == "OPAQUE":
            material_dict["alphaMode"] = "OPAQUE"
            mtoon_dict["transparentWithZWrite"] = False
            mtoon_dict["renderQueueOffsetNumber"] = 0
        elif material.blend_method == "CLIP":
            alpha_cutoff = shader.get_float_value(node, "CutoffRate", 0, float_info.max)
            if alpha_cutoff is not None:
                material_dict["alphaCutoff"] = alpha_cutoff
            else:
                material_dict["alphaCutoff"] = 0.5
            material_dict["alphaMode"] = "MASK"
            mtoon_dict["transparentWithZWrite"] = False
            mtoon_dict["renderQueueOffsetNumber"] = 0
        else:
            material_dict["alphaMode"] = "BLEND"
            transparent_with_z_write = shader.get_float_value(
                node, "TransparentWithZWrite"
            )
            if (
                transparent_with_z_write is None
                or math.fabs(transparent_with_z_write) < float_info.epsilon
            ):
                mtoon_dict["transparentWithZWrite"] = False
            else:
                mtoon_dict["transparentWithZWrite"] = True
        mtoon_dict["renderQueueOffsetNumber"] = 0
        assign_dict(
            material_dict, "doubleSided", not material.use_backface_culling, False
        )
        assign_dict(
            pbr_metallic_roughness_dict,
            "baseColorFactor",
            shader.get_rgba_val(node, "DiffuseColor", 0.0, 1.0),
        )
        base_color_texture_dict = Gltf2AddonVrmExporter.create_mtoon0_texture_info_dict(
            json_dict, body_binary, node, "MainTexture"
        )
        assign_dict(
            pbr_metallic_roughness_dict, "baseColorTexture", base_color_texture_dict
        )
        assign_dict(
            mtoon_dict,
            "shadeColorFactor",
            shader.get_rgb_val(node, "ShadeColor", 0.0, 1.0),
        )
        shade_multiply_texture_dict = (
            Gltf2AddonVrmExporter.create_mtoon0_texture_info_dict(
                json_dict, body_binary, node, "ShadeTexture"
            )
        )
        if shade_multiply_texture_dict is not None:
            mtoon_dict["shadeMultiplyTexture"] = shade_multiply_texture_dict
        elif base_color_texture_dict is not None:
            # https://github.com/vrm-c/UniVRM/blob/f3479190c330ec6ecd2b40be919285aa93a53aff/Assets/VRM10/Runtime/Migration/Materials/MigrationMToonMaterial.cs#L185-L204
            mtoon_dict["shadeMultiplyTexture"] = base_color_texture_dict
        normal_texture_dict = Gltf2AddonVrmExporter.create_mtoon0_texture_info_dict(
            json_dict, body_binary, node, "NormalmapTexture"
        )
        if assign_dict(
            material_dict, "normalTexture", normal_texture_dict
        ) and isinstance(normal_texture_dict, dict):
            assign_dict(
                normal_texture_dict, "scale", shader.get_float_value(node, "BumpScale")
            )

        shading_shift_0x = shader.get_float_value(node, "ShadeShift")
        if shading_shift_0x is None:
            shading_shift_0x = 0.0

        shading_toony_0x = shader.get_float_value(node, "ShadeToony")
        if shading_toony_0x is None:
            shading_toony_0x = 0.0

        mtoon_dict[
            "shadingShiftFactor"
        ] = Gltf2AddonVrmExporter.migrate_to_shading_shift(
            shading_toony_0x, shading_shift_0x
        )

        mtoon_dict[
            "shadingToonyFactor"
        ] = Gltf2AddonVrmExporter.migrate_to_shading_toony(
            shading_toony_0x, shading_shift_0x
        )

        gi_equalization_0x = shader.get_float_value(node, "IndirectLightIntensity")
        if gi_equalization_0x is not None:
            mtoon_dict[
                "giEqualizationFactor"
            ] = Gltf2AddonVrmExporter.migrate_to_gi_equalization(gi_equalization_0x)

        assign_dict(
            material_dict,
            "emissiveFactor",
            shader.get_rgb_val(node, "EmissionColor", 0.0, 1.0),
        )
        assign_dict(
            material_dict,
            "emissiveTexture",
            Gltf2AddonVrmExporter.create_mtoon0_texture_info_dict(
                json_dict, body_binary, node, "Emission_Texture"
            ),
        )
        assign_dict(
            mtoon_dict,
            "matcapTexture",
            Gltf2AddonVrmExporter.create_mtoon0_texture_info_dict(
                json_dict, body_binary, node, "SphereAddTexture"
            ),
        )
        assign_dict(
            mtoon_dict,
            "parametricRimColorFactor",
            shader.get_rgb_val(node, "RimColor", 0.0, 1.0),
        )
        assign_dict(
            mtoon_dict,
            "parametricRimFresnelPowerFactor",
            shader.get_float_value(node, "RimFresnelPower", 0.0, float_info.max),
        )
        assign_dict(
            mtoon_dict,
            "parametricRimLiftFactor",
            shader.get_float_value(node, "RimLift"),
        )
        assign_dict(
            mtoon_dict,
            "rimMultiplyTexture",
            Gltf2AddonVrmExporter.create_mtoon0_texture_info_dict(
                json_dict, body_binary, node, "RimTexture"
            ),
        )
        assign_dict(
            mtoon_dict,
            "rimLightingMixFactor",
            shader.get_float_value(node, "RimLightingMix"),
        )

        centimeter_to_meter = 0.01
        one_hundredth = 0.01

        outline_width_mode = shader.get_float_value(node, "OutlineWidthMode")
        if outline_width_mode is not None:
            outline_width_mode = int(round(outline_width_mode))
        else:
            outline_width_mode = 0

        outline_width = shader.get_float_value(node, "OutlineWidth")
        if outline_width is None:
            outline_width = 0.0

        if outline_width_mode == 1:
            mtoon_dict["outlineWidthMode"] = "worldCoordinates"
            mtoon_dict["outlineWidthFactor"] = max(
                0.0, outline_width * centimeter_to_meter
            )
        elif outline_width_mode == 2:
            mtoon_dict["outlineWidthMode"] = "screenCoordinates"
            mtoon_dict["outlineWidthFactor"] = max(
                0.0, outline_width * one_hundredth * 0.5
            )
        else:
            mtoon_dict["outlineWidthMode"] = "none"

        assign_dict(
            mtoon_dict,
            "outlineWidthMultiplyTexture",
            Gltf2AddonVrmExporter.create_mtoon0_texture_info_dict(
                json_dict, body_binary, node, "OutlineWidthTexture"
            ),
        )
        assign_dict(
            mtoon_dict,
            "outlineColorFactor",
            shader.get_rgb_val(node, "OutlineColor", 0.0, 1.0),
        )

        outline_color_mode = shader.get_float_value(node, "OutlineColorMode")
        if outline_color_mode is not None:
            outline_color_mode = int(round(outline_color_mode))
        else:
            outline_color_mode = 0

        mtoon_dict["outlineLightingMixFactor"] = 0.0
        if outline_color_mode == 1:
            assign_dict(
                mtoon_dict,
                "outlineLightingMixFactor",
                shader.get_float_value(node, "OutlineLightingMix"),
            )

        assign_dict(
            mtoon_dict,
            "uvAnimationMaskTexture",
            Gltf2AddonVrmExporter.create_mtoon0_texture_info_dict(
                json_dict, body_binary, node, "UV_Animation_Mask_Texture"
            ),
        )
        assign_dict(
            mtoon_dict,
            "uvAnimationRotationSpeedFactor",
            shader.get_float_value(node, "UV_Scroll_Rotation"),
        )
        assign_dict(
            mtoon_dict,
            "uvAnimationScrollXSpeedFactor",
            shader.get_float_value(node, "UV_Scroll_X"),
        )

        invert_y = -1
        uv_animation_scroll_y_speed_factor = shader.get_float_value(node, "UV_Scroll_Y")
        if uv_animation_scroll_y_speed_factor is not None:
            mtoon_dict["uvAnimationScrollYSpeedFactor"] = (
                uv_animation_scroll_y_speed_factor * invert_y
            )

        if pbr_metallic_roughness_dict:
            material_dict["pbrMetallicRoughness"] = pbr_metallic_roughness_dict

        extensions_dict["VRMC_materials_mtoon"] = mtoon_dict
        material_dict["extensions"] = extensions_dict

        return material_dict

    @staticmethod
    def save_vrm_materials(
        json_dict: Dict[str, Any],
        body_binary: bytearray,
        material_name_to_index_dict: Dict[str, int],
    ) -> None:
        material_dicts = json_dict["materials"]

        for material_name, index in material_name_to_index_dict.items():
            material = bpy.data.materials.get(material_name)
            if not isinstance(material, bpy.types.Material) or not (
                0 <= index < len(material_dicts)
            ):
                continue

            if material.vrm_addon_extension.mtoon1.enabled:
                material_dicts[
                    index
                ] = Gltf2AddonVrmExporter.create_mtoon1_material_dict(
                    json_dict, body_binary, material
                )
                continue

            # MToon_unversioned (MToon for VRM 0.0)
            node = search.vrm_shader_node(material)
            if not isinstance(node, bpy.types.Node):
                continue
            if node.node_tree["SHADER"] == "MToon_unversioned":
                material_dicts[
                    index
                ] = Gltf2AddonVrmExporter.create_mtoon_unversioned_material_dict(
                    json_dict, body_binary, material, node
                )

        if material_dicts:
            json_dict["materials"] = material_dicts

    def export_vrm(self) -> Optional[bytes]:
        dummy_skinned_mesh_object_name = self.create_dummy_skinned_mesh_object()
        try:
            # 他glTF2ExportUserExtensionの影響を最小化するため、影響が少ないと思われるカスタムプロパティを使ってBlenderのオブジェクトとインデックスの対応をとる。
            for obj in bpy.data.objects:
                obj[self.extras_object_name_key] = obj.name
            for material in bpy.data.materials:
                material[self.extras_material_name_key] = material.name

            # glTF 2.0アドオンのコメントにはPoseBoneとのカスタムプロパティを保存すると書いてあるが、実際にはBoneのカスタムプロパティを参照している。
            # そのため、いちおう両方に書いておく
            for bone in self.armature.pose.bones:
                bone[self.extras_bone_name_key] = bone.name
            for bone in self.armature.data.bones:
                bone[self.extras_bone_name_key] = bone.name

            self.overwrite_object_visibility_and_selection()
            self.mount_skinned_mesh_parent()

            with tempfile.TemporaryDirectory() as temp_dir:
                filepath = os.path.join(temp_dir, "out.glb")
                bpy.ops.export_scene.gltf(
                    filepath=filepath,
                    check_existing=False,
                    export_format="GLB",
                    export_extras=True,
                    export_current_frame=True,
                    use_selection=True,
                    export_animations=False,  # https://github.com/vrm-c/UniVRM/issues/1729
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
            for material in bpy.data.materials:
                if self.extras_material_name_key in material:
                    del material[self.extras_material_name_key]

            self.restore_object_visibility_and_selection()
            self.restore_skinned_mesh_parent()
            self.destroy_dummy_skinned_mesh_object(dummy_skinned_mesh_object_name)

        json_dict, body_binary = gltf.parse_glb(extra_name_assigned_glb)
        body_binary = bytearray(body_binary)

        bone_name_to_index_dict: Dict[str, int] = {}
        object_name_to_index_dict: Dict[str, int] = {}
        mesh_object_name_to_node_index_dict: Dict[str, int] = {}
        mesh_object_name_to_morph_target_names_dict: Dict[str, List[str]] = {}

        # https://github.com/KhronosGroup/glTF/blob/b6e0fcc6d8e9f83347aa8b2e3df085b81590a65c/specification/2.0/schema/glTF.schema.json
        gltf_root_non_empty_array_keys = [
            "extensionsUsed",
            "extensionsRequired",
            "accessors",
            "animations",
            "buffers",
            "bufferViews",
            "cameras",
            "images",
            "materials",
            "meshes",
            "nodes",
            "samplers",
            "scenes",
            "skins",
            "textures",
        ]

        for key in gltf_root_non_empty_array_keys:
            list_value = json_dict.get(key)
            json_dict[key] = (
                list(list_value) if isinstance(list_value, abc.Iterable) else []
            )

        nodes = json_dict["nodes"]

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
            if isinstance(object_name, str):
                object_name_to_index_dict[object_name] = node_index
            mesh_index = node_dict.get("mesh")
            mesh_dicts = json_dict["meshes"]
            if (
                isinstance(object_name, str)
                and isinstance(mesh_index, int)
                and 0 <= mesh_index < len(mesh_dicts)
            ):
                mesh_object_name_to_node_index_dict[object_name] = node_index
                target_names = deep.get(
                    mesh_dicts, [mesh_index, "extras", "targetNames"]
                )
                if isinstance(target_names, abc.Iterable):
                    mesh_object_name_to_morph_target_names_dict[object_name] = [
                        str(target_name) for target_name in target_names
                    ]
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

        node_constraint_spec_version = "1.0"
        use_node_constraint = False
        object_constraints = search.export_object_constraints(self.export_objects)
        for object_name, node_index in object_name_to_index_dict.items():
            if not 0 <= node_index < len(json_dict["nodes"]):
                continue
            if not isinstance(json_dict["nodes"][node_index], dict):
                json_dict["nodes"][node_index] = {}
            node_dict = json_dict["nodes"][node_index]
            constraint_dict = self.create_constraint_dict(
                object_name,
                object_constraints,
                object_name_to_index_dict,
                bone_name_to_index_dict,
            )
            if constraint_dict:
                extensions = node_dict.get("extensions")
                if not isinstance(extensions, dict):
                    node_dict["extensions"] = extensions = {}
                extensions["VRMC_node_constraint"] = {
                    "specVersion": node_constraint_spec_version,
                    "constraint": constraint_dict,
                }
                use_node_constraint = True

        bone_constraints = search.export_bone_constraints(
            self.export_objects, self.armature
        )
        for bone_name, node_index in bone_name_to_index_dict.items():
            if not 0 <= node_index < len(json_dict["nodes"]):
                continue
            if not isinstance(json_dict["nodes"][node_index], dict):
                json_dict["nodes"][node_index] = {}
            node_dict = json_dict["nodes"][node_index]
            constraint_dict = self.create_constraint_dict(
                bone_name,
                bone_constraints,
                object_name_to_index_dict,
                bone_name_to_index_dict,
            )
            if constraint_dict:
                extensions = node_dict.get("extensions")
                if not isinstance(extensions, dict):
                    node_dict["extensions"] = extensions = {}
                extensions["VRMC_node_constraint"] = {
                    "specVersion": node_constraint_spec_version,
                    "constraint": constraint_dict,
                }
                use_node_constraint = True

        material_name_to_index_dict: Dict[str, int] = {}
        materials = json_dict["materials"]
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

        self.save_vrm_materials(json_dict, body_binary, material_name_to_index_dict)

        vrm = self.armature.data.vrm_addon_extension.vrm1

        extensions_used = json_dict["extensionsUsed"]

        if use_node_constraint:
            extensions_used.append("VRMC_node_constraint")

        extensions = json_dict.get("extensions")
        if not isinstance(extensions, dict):
            json_dict["extensions"] = extensions = {}

        extensions_used.append("VRMC_vrm")
        extensions["VRMC_vrm"] = {
            "specVersion": self.armature.data.vrm_addon_extension.spec_version,
            "meta": self.create_meta_dict(vrm.meta),
            "humanoid": self.create_humanoid_dict(
                vrm.humanoid, bone_name_to_index_dict
            ),
            "firstPerson": self.create_first_person_dict(
                vrm.first_person, mesh_object_name_to_node_index_dict
            ),
            "lookAt": self.create_look_at_dict(vrm.look_at),
            "expressions": self.create_expressions_dict(
                vrm.expressions,
                mesh_object_name_to_node_index_dict,
                mesh_object_name_to_morph_target_names_dict,
                material_name_to_index_dict,
            ),
        }

        spring_bone = self.armature.data.vrm_addon_extension.spring_bone1
        spring_bone_dict: Dict[str, Any] = {}

        (
            spring_bone_collider_dicts,
            collider_uuid_to_index_dict,
        ) = self.create_spring_bone_collider_dicts(spring_bone, bone_name_to_index_dict)
        if spring_bone_collider_dicts:
            spring_bone_dict["colliders"] = spring_bone_collider_dicts

        (
            spring_bone_collider_group_dicts,
            collider_group_uuid_to_index_dict,
        ) = self.create_spring_bone_collider_group_dicts(
            spring_bone, collider_uuid_to_index_dict
        )
        if spring_bone_collider_group_dicts:
            spring_bone_dict["colliderGroups"] = spring_bone_collider_group_dicts

        spring_bone_spring_dicts = self.create_spring_bone_spring_dicts(
            spring_bone,
            bone_name_to_index_dict,
            collider_group_uuid_to_index_dict,
        )
        if spring_bone_spring_dicts:
            spring_bone_dict["springs"] = spring_bone_spring_dicts

        if spring_bone_dict:
            extensions_used.append("VRMC_springBone")
            spring_bone_dict["specVersion"] = "1.0"
            extensions["VRMC_springBone"] = spring_bone_dict

        json_dict["extensions"] = extensions
        json_dict["extensionsUsed"] = extensions_used

        v = version.version()
        if os.environ.get("BLENDER_VRM_USE_TEST_EXPORTER_VERSION") == "true":
            v = (999, 999, 999)

        generator = "VRM Add-on for Blender v" + ".".join(map(str, v))

        base_generator = deep.get(json_dict, ["asset", "generator"])
        if isinstance(base_generator, str):
            generator += " with " + base_generator

        json_dict["asset"]["generator"] = generator

        if len(body_binary):
            if not json_dict["buffers"]:
                json_dict["buffers"] = [{}]
            if not isinstance(json_dict["buffers"][0], dict):
                json_dict["buffers"][0] = {}
            json_dict["buffers"][0]["byteLength"] = len(body_binary)

        for key in gltf_root_non_empty_array_keys:
            if not json_dict[key]:
                del json_dict[key]

        return gltf.pack_glb(json_dict, body_binary)
