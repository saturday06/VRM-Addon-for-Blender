import math
import tempfile
from copy import deepcopy
from os import environ
from pathlib import Path
from sys import float_info
from typing import Optional, Union

import bpy
from bpy.types import (
    Armature,
    ArmatureModifier,
    Bone,
    Context,
    CopyRotationConstraint,
    DampedTrackConstraint,
    Image,
    Material,
    Node,
    Object,
)
from mathutils import Matrix, Quaternion, Vector

from ..common import convert, deep, shader
from ..common.char import INTERNAL_NAME_PREFIX
from ..common.deep import Json, make_json
from ..common.gltf import pack_glb, parse_glb
from ..common.logging import get_logger
from ..common.version import addon_version
from ..common.vrm1.human_bone import HumanBoneName
from ..editor import search
from ..editor.mtoon1.property_group import (
    Mtoon1SamplerPropertyGroup,
    Mtoon1TextureInfoPropertyGroup,
)
from ..editor.spring_bone1.property_group import SpringBone1SpringBonePropertyGroup
from ..editor.vrm1.property_group import (
    Vrm1ExpressionPropertyGroup,
    Vrm1ExpressionsPropertyGroup,
    Vrm1FirstPersonPropertyGroup,
    Vrm1HumanBonesPropertyGroup,
    Vrm1HumanoidPropertyGroup,
    Vrm1LookAtPropertyGroup,
    Vrm1MetaPropertyGroup,
)
from ..external.io_scene_gltf2_support import (
    ExportSceneGltfArguments,
    export_scene_gltf,
    image_to_image_bytes,
    init_extras_export,
)
from .abstract_base_vrm_exporter import AbstractBaseVrmExporter, assign_dict

logger = get_logger(__name__)


class Gltf2AddonVrmExporter(AbstractBaseVrmExporter):
    def __init__(
        self,
        context: Context,
        export_objects: list[Object],
        export_all_influences: bool,
        export_lights: bool,
    ) -> None:
        super().__init__(context)
        self.export_objects = export_objects
        self.export_all_influences = export_all_influences
        self.export_lights = export_lights

        armatures = [obj for obj in export_objects if obj.type == "ARMATURE"]
        if not armatures:
            raise NotImplementedError(
                "Export without armature is not yet supported.\n"
                + "アーマチュア無しエクスポートはまだ未対応。"
            )
        self.armature = armatures[0]
        armature_data = self.armature.data
        if not isinstance(armature_data, Armature):
            message = f"{type(armature_data)} is not an Armature"
            raise TypeError(message)

        for collider in armature_data.vrm_addon_extension.spring_bone1.colliders:
            if not collider.bpy_object:
                continue
            if collider.bpy_object in self.export_objects:
                self.export_objects.remove(collider.bpy_object)
            for child in collider.bpy_object.children:
                if child in self.export_objects:
                    self.export_objects.remove(child)

        self.extras_main_armature_key = (
            INTERNAL_NAME_PREFIX + self.export_id + "MainArmature"
        )
        self.extras_bone_name_key = INTERNAL_NAME_PREFIX + self.export_id + "BoneName"
        self.extras_object_name_key = (
            INTERNAL_NAME_PREFIX + self.export_id + "ObjectName"
        )
        self.extras_material_name_key = (
            INTERNAL_NAME_PREFIX + self.export_id + "MaterialName"
        )
        self.object_visibility_and_selection: dict[str, tuple[bool, bool]] = {}
        self.mounted_object_names: list[str] = []

    def overwrite_object_visibility_and_selection(self) -> None:
        self.object_visibility_and_selection.clear()
        # https://projects.blender.org/blender/blender/issues/113378
        self.context.view_layer.update()
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

        # Blender 3.1.2付属アドオンのglTF 2.0エクスポート処理には次の条件をすべて満たす
        # ときinverseBindMatricesが不正なglbが出力される:
        # - アーマチュアの子孫になっていないメッシュがそのアーマチュアのボーンに
        #   スキニングされている
        # - スキニングされたボーンの子供に別のメッシュが存在する
        # そのため、アーマチュアの子孫になっていないメッシュの先祖の親をアーマチュアに
        # し、後で戻す
        for obj in self.export_objects:
            if obj.type != "MESH" or not [
                True
                for m in obj.modifiers
                if isinstance(m, ArmatureModifier) and m.object == armature
            ]:
                continue

            search_obj = obj
            while search_obj != armature:
                if search_obj.parent:
                    search_obj = search_obj.parent
                    continue
                self.mounted_object_names.append(search_obj.name)
                matrix_world = search_obj.matrix_world.copy()
                search_obj.parent = armature
                search_obj.matrix_world = matrix_world
                break

    def restore_skinned_mesh_parent(self) -> None:
        for mounted_object_name in self.mounted_object_names:
            obj = bpy.data.objects.get(mounted_object_name)
            if not obj:
                continue
            matrix_world = obj.matrix_world.copy()
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

        armature_data = self.armature.data
        if not isinstance(armature_data, Armature):
            message = f"{type(armature_data)} is not an Armature"
            raise TypeError(message)

        mesh = bpy.data.meshes.new(self.export_id + "_mesh")
        mesh.from_pydata(vertices, edges, faces)
        mesh.update()
        if mesh.validate():
            message = "Invalid geometry"
            raise ValueError(message)
        obj = bpy.data.objects.new("secondary", mesh)
        obj.parent_type = "OBJECT"
        obj.parent = self.armature
        for index, bone_name in enumerate(armature_data.bones.keys()):
            vertex_group = obj.vertex_groups.new(name=bone_name)
            vertex_group.add([index * 3, index * 3 + 1, index * 3 + 2], 1.0, "ADD")
        modifier = obj.modifiers.new(name="Armature", type="ARMATURE")
        if not isinstance(modifier, ArmatureModifier):
            message = f"{type(modifier)} is not a ArmatureModifier"
            raise TypeError(message)
        modifier.object = self.armature
        self.context.scene.collection.objects.link(obj)
        obj[self.extras_object_name_key] = obj.name
        return str(obj.name)

    def destroy_dummy_skinned_mesh_object(self, name: str) -> None:
        dummy_skinned_mesh_object = bpy.data.objects.get(name)
        if not isinstance(dummy_skinned_mesh_object, Object):
            return
        dummy_skinned_mesh_object.modifiers.clear()
        dummy_skinned_mesh_object.vertex_groups.clear()
        self.context.scene.collection.objects.unlink(  # TODO: remove completely
            dummy_skinned_mesh_object
        )

    @classmethod
    def create_meta_dict(
        cls,
        meta: Vrm1MetaPropertyGroup,
        json_dict: dict[str, Json],
        body_binary: bytearray,
        image_name_to_index_dict: dict[str, int],
        gltf2_addon_export_settings: dict[str, object],
    ) -> dict[str, Json]:
        meta_dict: dict[str, Json] = {
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
        meta_dict["authors"] = make_json(authors)

        if meta.copyright_information:
            meta_dict["copyrightInformation"] = meta.copyright_information

        references: list[Json] = [
            reference.value for reference in meta.references if reference.value
        ]
        if references:
            meta_dict["references"] = references

        if meta.third_party_licenses:
            meta_dict["thirdPartyLicenses"] = meta.third_party_licenses

        if meta.other_license_url:
            meta_dict["otherLicenseUrl"] = meta.other_license_url

        if meta.thumbnail_image:
            meta_dict["thumbnailImage"] = cls.find_or_create_image(
                json_dict,
                body_binary,
                image_name_to_index_dict,
                meta.thumbnail_image,
                gltf2_addon_export_settings,
            )

        return meta_dict

    @classmethod
    def create_humanoid_dict(
        cls,
        humanoid: Vrm1HumanoidPropertyGroup,
        bone_name_to_index_dict: dict[str, int],
    ) -> dict[str, Json]:
        human_bones_dict: dict[str, Json] = {}
        for (
            human_bone_name,
            human_bone,
        ) in humanoid.human_bones.human_bone_name_to_human_bone().items():
            index = bone_name_to_index_dict.get(human_bone.node.bone_name)
            if isinstance(index, int):
                human_bones_dict[human_bone_name.value] = {"node": index}

        return {
            "humanBones": human_bones_dict,
        }

    @classmethod
    def create_first_person_dict(
        cls,
        first_person: Vrm1FirstPersonPropertyGroup,
        mesh_object_name_to_node_index_dict: dict[str, int],
    ) -> dict[str, Json]:
        mesh_annotation_dicts: list[Json] = []
        for mesh_annotation in first_person.mesh_annotations:
            if not mesh_annotation.node or not mesh_annotation.node.mesh_object_name:
                continue
            node_index = mesh_object_name_to_node_index_dict.get(
                mesh_annotation.node.mesh_object_name
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

    @classmethod
    def create_look_at_dict(
        cls,
        look_at: Vrm1LookAtPropertyGroup,
    ) -> dict[str, Json]:
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

    @classmethod
    def create_expression_dict(
        cls,
        expression: Vrm1ExpressionPropertyGroup,
        mesh_object_name_to_node_index_dict: dict[str, int],
        mesh_object_name_to_morph_target_names_dict: dict[str, list[str]],
        material_name_to_index_dict: dict[str, int],
    ) -> dict[str, Json]:
        expression_dict: dict[str, Json] = {
            "isBinary": expression.is_binary,
            "overrideBlink": expression.override_blink,
            "overrideLookAt": expression.override_look_at,
            "overrideMouth": expression.override_mouth,
        }
        morph_target_bind_dicts: list[Json] = []
        for morph_target_bind in expression.morph_target_binds:
            if (
                not morph_target_bind.node
                or not morph_target_bind.node.mesh_object_name
            ):
                continue
            node_index = mesh_object_name_to_node_index_dict.get(
                morph_target_bind.node.mesh_object_name
            )
            if not isinstance(node_index, int):
                continue
            morph_targets = mesh_object_name_to_morph_target_names_dict.get(
                morph_target_bind.node.mesh_object_name
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

        material_color_bind_dicts: list[Json] = []
        for material_color_bind in expression.material_color_binds:
            if (
                not material_color_bind.material
                or not material_color_bind.material.name
            ):
                continue
            material_index = material_name_to_index_dict.get(
                material_color_bind.material.name
            )
            if not isinstance(material_index, int):
                continue
            if material_color_bind.type == "color":
                target_value: Json = list(material_color_bind.target_value)
            else:
                rgb = material_color_bind.target_value_as_rgb
                target_value = [rgb[0], rgb[1], rgb[2], 1.0]
            material_color_bind_dicts.append(
                {
                    "material": material_index,
                    "type": material_color_bind.type,
                    "targetValue": target_value,
                }
            )
        if material_color_bind_dicts:
            expression_dict["materialColorBinds"] = material_color_bind_dicts

        texture_transform_binds: list[Json] = []
        for texture_transform_bind in expression.texture_transform_binds:
            if (
                not texture_transform_bind.material
                or not texture_transform_bind.material.name
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

    @classmethod
    def create_expressions_dict(
        cls,
        expressions: Vrm1ExpressionsPropertyGroup,
        mesh_object_name_to_node_index_dict: dict[str, int],
        mesh_object_name_to_morph_target_names_dict: dict[str, list[str]],
        material_name_to_index_dict: dict[str, int],
    ) -> dict[str, Json]:
        preset_dict: dict[str, Json] = {}
        for (
            preset_name,
            expression,
        ) in expressions.preset.name_to_expression_dict().items():
            preset_dict[preset_name] = cls.create_expression_dict(
                expression,
                mesh_object_name_to_node_index_dict,
                mesh_object_name_to_morph_target_names_dict,
                material_name_to_index_dict,
            )
        custom_dict: dict[str, Json] = {}
        for custom_expression in expressions.custom:
            custom_dict[custom_expression.custom_name] = cls.create_expression_dict(
                custom_expression,
                mesh_object_name_to_node_index_dict,
                mesh_object_name_to_morph_target_names_dict,
                material_name_to_index_dict,
            )
        return {
            "preset": preset_dict,
            "custom": custom_dict,
        }

    @classmethod
    def create_spring_bone_collider_dicts(
        cls,
        spring_bone: SpringBone1SpringBonePropertyGroup,
        bone_name_to_index_dict: dict[str, int],
    ) -> tuple[list[Json], dict[str, int]]:
        collider_dicts: list[Json] = []
        collider_uuid_to_index_dict = {}
        for collider in spring_bone.colliders:
            collider_dict: dict[str, Json] = {}
            node_index = bone_name_to_index_dict.get(collider.node.bone_name)
            if not isinstance(node_index, int):
                continue
            collider_dict["node"] = node_index

            if collider.shape_type == collider.SHAPE_TYPE_SPHERE:
                shape_dict: dict[str, Json] = {
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

    @classmethod
    def create_spring_bone_collider_group_dicts(
        cls,
        spring_bone: SpringBone1SpringBonePropertyGroup,
        collider_uuid_to_index_dict: dict[str, int],
    ) -> tuple[list[Json], dict[str, int]]:
        collider_group_dicts: list[Json] = []
        collider_group_uuid_to_index_dict = {}
        for collider_group in spring_bone.collider_groups:
            collider_group_dict: dict[str, Json] = {"name": collider_group.vrm_name}
            collider_indices: list[Json] = []
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

    @classmethod
    def create_spring_bone_spring_dicts(
        cls,
        spring_bone: SpringBone1SpringBonePropertyGroup,
        bone_name_to_index_dict: dict[str, int],
        collider_group_uuid_to_index_dict: dict[str, int],
        armature: Object,
    ) -> list[Json]:
        spring_dicts: list[Json] = []
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            logger.error(f"{type(armature_data)} is not an Armature")
            return []
        for spring in spring_bone.springs:
            spring_dict: dict[str, Json] = {"name": spring.vrm_name}

            first_bone: Optional[Bone] = None
            joint_dicts: list[Json] = []
            for joint in spring.joints:
                bone = armature_data.bones.get(joint.node.bone_name)
                if not bone:
                    continue
                if first_bone is None:
                    first_bone = bone
                node_index = bone_name_to_index_dict.get(joint.node.bone_name)
                if not isinstance(node_index, int):
                    continue
                joint_dicts.append(
                    {
                        "node": node_index,
                        "hitRadius": joint.hit_radius,
                        "stiffness": joint.stiffness,
                        "gravityPower": joint.gravity_power,
                        "gravityDir": [
                            joint.gravity_dir[0],
                            joint.gravity_dir[2],
                            -joint.gravity_dir[1],
                        ],
                        "dragForce": joint.drag_force,
                    }
                )

            if joint_dicts:
                spring_dict["joints"] = joint_dicts

            center_bone = armature_data.bones.get(spring.center.bone_name)
            if center_bone:
                center_bone_is_ancestor_of_first_bone = False
                ancestor_of_first_bone = first_bone
                while ancestor_of_first_bone:
                    if center_bone == ancestor_of_first_bone:
                        center_bone_is_ancestor_of_first_bone = True
                        break
                    ancestor_of_first_bone = ancestor_of_first_bone.parent
                if center_bone_is_ancestor_of_first_bone:
                    center_index = bone_name_to_index_dict.get(spring.center.bone_name)
                    if isinstance(center_index, int):
                        spring_dict["center"] = center_index

            collider_group_indices: list[Json] = []
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

    @classmethod
    def search_constraint_target_index(
        cls,
        constraint: Union[CopyRotationConstraint, DampedTrackConstraint],
        object_name_to_index_dict: dict[str, int],
        bone_name_to_index_dict: dict[str, int],
    ) -> Optional[int]:
        target = constraint.target
        if not target:
            return None
        if target.type == "ARMATURE" and constraint.subtarget:
            return bone_name_to_index_dict.get(constraint.subtarget)
        return object_name_to_index_dict.get(target.name)

    @classmethod
    def create_constraint_dict(
        cls,
        name: str,
        constraints: search.ExportConstraint,
        object_name_to_index_dict: dict[str, int],
        bone_name_to_index_dict: dict[str, int],
    ) -> dict[str, Json]:
        roll_constraint = constraints.roll_constraints.get(name)
        aim_constraint = constraints.aim_constraints.get(name)
        rotation_constraint = constraints.rotation_constraints.get(name)
        constraint_dict: dict[str, Json] = {}
        if roll_constraint:
            source_index = cls.search_constraint_target_index(
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
                    message = "Unsupported roll axis"
                    raise ValueError(message)
                constraint_dict["roll"] = {
                    "source": source_index,
                    "rollAxis": roll_axis,
                    "weight": max(0.0, min(1.0, roll_constraint.influence)),
                }
        elif aim_constraint:
            source_index = cls.search_constraint_target_index(
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
            source_index = cls.search_constraint_target_index(
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

    @classmethod
    def create_mtoon0_khr_texture_transform(
        cls, node: Node, texture_input_name: str
    ) -> dict[str, Json]:
        default: dict[str, Json] = {
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

        result = default.copy()

        location_input = uv_offset_scaling_node.inputs.get("Location")
        if isinstance(location_input, shader.VECTOR_SOCKET_CLASSES):
            result["offset"] = [
                location_input.default_value[0],
                location_input.default_value[1],
            ]

        scale_input = uv_offset_scaling_node.inputs.get("Scale")
        if isinstance(scale_input, shader.VECTOR_SOCKET_CLASSES):
            result["scale"] = [
                scale_input.default_value[0],
                scale_input.default_value[1],
            ]

        return result

    @classmethod
    def find_or_create_image(
        cls,
        json_dict: dict[str, Json],
        body_binary: bytearray,
        image_name_to_index_dict: dict[str, int],
        image: Image,
        gltf2_addon_export_settings: dict[str, object],
    ) -> int:
        # TODO: Verify alignment requirement and optimize
        while len(body_binary) % 32 == 0:
            body_binary.append(0)

        image_bytes, mime = image_to_image_bytes(image, gltf2_addon_export_settings)
        buffer_view_dicts = json_dict.get("bufferViews")
        if not isinstance(buffer_view_dicts, list):
            buffer_view_dicts = []
            json_dict["bufferViews"] = buffer_view_dicts
        image_buffer_view_index = len(buffer_view_dicts)
        buffer_view_dicts.append(
            {
                "buffer": 0,
                "byteOffset": len(body_binary),
                "byteLength": len(image_bytes),
            }
        )

        image_index = image_name_to_index_dict.get(image.name)
        image_dicts = json_dict.get("images")
        if not isinstance(image_dicts, list):
            image_dicts = []
            json_dict["images"] = image_dicts
        if isinstance(image_index, int) and not 0 <= image_index < len(image_dicts):
            logger.error(f"Bug: not 0 <= {image_index} < len(images)) for {image.name}")
            image_index = None
        if not isinstance(image_index, int):
            image_index = len(image_dicts)
            image_dicts.append(
                {
                    "name": image.name,
                    "bufferView": image_buffer_view_index,
                    "mimeType": mime,
                }
            )
            image_name_to_index_dict[image.name] = image_index

        body_binary.extend(image_bytes)
        # TODO: Verify alignment requirement and optimize
        while len(body_binary) % 32 == 0:
            body_binary.append(0)

        return image_index

    @classmethod
    def create_mtoon1_texture_info_dict(
        cls,
        json_dict: dict[str, Json],
        body_binary: bytearray,
        texture_info: Mtoon1TextureInfoPropertyGroup,
        image_name_to_index_dict: dict[str, int],
        gltf2_addon_export_settings: dict[str, object],
    ) -> Optional[dict[str, Json]]:
        image = texture_info.index.source
        if not image:
            return None

        image_index = cls.find_or_create_image(
            json_dict,
            body_binary,
            image_name_to_index_dict,
            image,
            gltf2_addon_export_settings,
        )

        sampler_dict: dict[str, Json] = {
            "magFilter": Mtoon1SamplerPropertyGroup.MAG_FILTER_ID_TO_NUMBER[
                texture_info.index.sampler.mag_filter
            ],
            "minFilter": Mtoon1SamplerPropertyGroup.MIN_FILTER_ID_TO_NUMBER[
                texture_info.index.sampler.min_filter
            ],
            "wrapS": Mtoon1SamplerPropertyGroup.WRAP_ID_TO_NUMBER[
                texture_info.index.sampler.wrap_s
            ],
            "wrapT": Mtoon1SamplerPropertyGroup.WRAP_ID_TO_NUMBER[
                texture_info.index.sampler.wrap_t
            ],
        }

        sampler_dicts = json_dict.get("samplers")
        if not isinstance(sampler_dicts, list):
            sampler_dicts = []
            json_dict["samplers"] = sampler_dicts

        if sampler_dict in sampler_dicts:
            sampler_index = sampler_dicts.index(sampler_dict)
        else:
            sampler_index = len(sampler_dicts)
            sampler_dicts.append(sampler_dict)

        texture_dicts = json_dict.get("textures")
        if not isinstance(texture_dicts, list):
            texture_dicts = []
            json_dict["textures"] = texture_dicts

        texture_dict: dict[str, Json] = {
            "sampler": sampler_index,
            "source": image_index,
        }

        if texture_dict in texture_dicts:
            texture_index = texture_dicts.index(texture_dict)
        else:
            texture_index = len(texture_dicts)
            texture_dicts.append(texture_dict)

        extensions_used = json_dict.get("extensionsUsed")
        if not isinstance(extensions_used, list):
            extensions_used = []
            json_dict["extensionsUsed"] = extensions_used

        if "KHR_texture_transform" not in extensions_used:
            extensions_used.append("KHR_texture_transform")
        json_dict["extensionsUsed"] = extensions_used

        khr_texture_transform = texture_info.extensions.khr_texture_transform
        khr_texture_transform_dict: dict[str, Json] = {
            "offset": list(khr_texture_transform.offset),
            "scale": list(khr_texture_transform.scale),
        }

        return {
            "index": texture_index,
            "extensions": {"KHR_texture_transform": khr_texture_transform_dict},
        }

    @classmethod
    def create_mtoon0_texture_info_dict(
        cls,
        json_dict: dict[str, Json],
        body_binary: bytearray,
        node: Node,
        texture_input_name: str,
        image_name_to_index_dict: dict[str, int],
        gltf2_addon_export_settings: dict[str, object],
    ) -> Optional[dict[str, Json]]:
        image_name_and_sampler_type = shader.get_image_name_and_sampler_type(
            node, texture_input_name
        )
        if image_name_and_sampler_type is None:
            return None

        image_name, wrap_type, filter_type = image_name_and_sampler_type
        image_index = cls.find_or_create_image(
            json_dict,
            body_binary,
            image_name_to_index_dict,
            bpy.data.images[image_name],
            gltf2_addon_export_settings,
        )

        sampler_dict: dict[str, Json] = {
            "magFilter": filter_type,
            "minFilter": filter_type,
            "wrapS": wrap_type,
            "wrapT": wrap_type,
        }
        sampler_dicts = json_dict.get("samplers")
        if not isinstance(sampler_dicts, list):
            sampler_dicts = []
            json_dict["samplers"] = sampler_dicts
        if sampler_dict in sampler_dicts:
            sampler_index = sampler_dicts.index(sampler_dict)
        else:
            sampler_index = len(sampler_dicts)
            sampler_dicts.append(sampler_dict)

        texture_dicts = json_dict.get("textures")
        if not isinstance(texture_dicts, list):
            texture_dicts = []
            json_dict["textures"] = texture_dicts

        texture_dict: dict[str, Json] = {
            "sampler": sampler_index,
            "source": image_index,
        }

        if texture_dict in texture_dicts:
            texture_index = texture_dicts.index(texture_dict)
        else:
            texture_index = len(texture_dicts)
            texture_dicts.append(texture_dict)

        extensions_used = json_dict.get("extensionsUsed")
        if not isinstance(extensions_used, list):
            extensions_used = []
            json_dict["extensionsUsed"] = extensions_used

        if "KHR_texture_transform" not in extensions_used:
            extensions_used.append("KHR_texture_transform")
        json_dict["extensionsUsed"] = extensions_used

        khr_texture_transform_dict = cls.create_mtoon0_khr_texture_transform(
            node, texture_input_name
        )

        return {
            "index": texture_index,
            "extensions": {"KHR_texture_transform": khr_texture_transform_dict},
        }

    @classmethod
    def lerp(cls, a: float, b: float, t: float) -> float:
        return (1 - t) * a + t * b

    @classmethod
    def create_mtoon1_material_dict(
        cls,
        json_dict: dict[str, Json],
        body_binary: bytearray,
        material: Material,
        image_name_to_index_dict: dict[str, int],
        gltf2_addon_export_settings: dict[str, object],
    ) -> dict[str, Json]:
        extensions_used = json_dict.get("extensionsUsed")
        if not isinstance(extensions_used, list):
            extensions_used = []
            json_dict["extensionsUsed"] = extensions_used

        if "KHR_materials_unlit" not in extensions_used:
            extensions_used.append("KHR_materials_unlit")
        if "KHR_materials_emissive_strength" not in extensions_used:
            extensions_used.append("KHR_materials_emissive_strength")
        if "VRMC_materials_mtoon" not in extensions_used:
            extensions_used.append("VRMC_materials_mtoon")

        # https://github.com/vrm-c/UniVRM/blob/f3479190c330ec6ecd2b40be919285aa93a53aff/Assets/VRM10/Runtime/Migration/Materials/MigrationMToonMaterial.cs
        mtoon_dict: dict[str, Json] = {
            "specVersion": "1.0",
        }

        gltf = material.vrm_addon_extension.mtoon1
        mtoon = gltf.extensions.vrmc_materials_mtoon

        extensions_dict: dict[str, Json] = {
            "KHR_materials_unlit": {},
            "KHR_materials_emissive_strength": {
                "emissiveStrength": (
                    gltf.extensions.khr_materials_emissive_strength.emissive_strength
                ),
            },
            "VRMC_materials_mtoon": mtoon_dict,
        }

        material_dict: dict[str, Json] = {"name": material.name}
        pbr_metallic_roughness_dict: dict[str, Json] = {}

        material_dict["alphaMode"] = gltf.alpha_mode
        mtoon_dict["transparentWithZWrite"] = mtoon.transparent_with_z_write
        mtoon_dict["renderQueueOffsetNumber"] = mtoon.render_queue_offset_number
        if gltf.alpha_mode == "MASK":
            material_dict["alphaCutoff"] = gltf.alpha_cutoff
        material_dict["doubleSided"] = gltf.double_sided
        pbr_metallic_roughness_dict["baseColorFactor"] = list(
            gltf.pbr_metallic_roughness.base_color_factor
        )
        assign_dict(
            pbr_metallic_roughness_dict,
            "baseColorTexture",
            cls.create_mtoon1_texture_info_dict(
                json_dict,
                body_binary,
                gltf.pbr_metallic_roughness.base_color_texture,
                image_name_to_index_dict,
                gltf2_addon_export_settings,
            ),
        )
        mtoon_dict["shadeColorFactor"] = list(mtoon.shade_color_factor)
        assign_dict(
            mtoon_dict,
            "shadeMultiplyTexture",
            cls.create_mtoon1_texture_info_dict(
                json_dict,
                body_binary,
                mtoon.shade_multiply_texture,
                image_name_to_index_dict,
                gltf2_addon_export_settings,
            ),
        )
        assign_dict(
            material_dict,
            "normalTexture",
            cls.create_mtoon1_texture_info_dict(
                json_dict,
                body_binary,
                gltf.normal_texture,
                image_name_to_index_dict,
                gltf2_addon_export_settings,
            ),
        )
        normal_texture_dict = material_dict.get("normalTexture")
        if isinstance(normal_texture_dict, dict):
            normal_texture_dict["scale"] = gltf.normal_texture.scale
        mtoon_dict["shadingShiftFactor"] = mtoon.shading_shift_factor
        assign_dict(
            mtoon_dict,
            "shadingShiftTexture",
            cls.create_mtoon1_texture_info_dict(
                json_dict,
                body_binary,
                mtoon.shading_shift_texture,
                image_name_to_index_dict,
                gltf2_addon_export_settings,
            ),
        )
        shading_shift_texture_dict = mtoon_dict.get("shadingShiftTexture")
        if isinstance(shading_shift_texture_dict, dict):
            shading_shift_texture_dict["scale"] = mtoon.shading_shift_texture.scale
        mtoon_dict["shadingToonyFactor"] = mtoon.shading_toony_factor
        mtoon_dict["giEqualizationFactor"] = mtoon.gi_equalization_factor
        material_dict["emissiveFactor"] = list(gltf.emissive_factor)
        assign_dict(
            material_dict,
            "emissiveTexture",
            cls.create_mtoon1_texture_info_dict(
                json_dict,
                body_binary,
                gltf.emissive_texture,
                image_name_to_index_dict,
                gltf2_addon_export_settings,
            ),
        )
        if assign_dict(
            mtoon_dict,
            "matcapTexture",
            cls.create_mtoon1_texture_info_dict(
                json_dict,
                body_binary,
                mtoon.matcap_texture,
                image_name_to_index_dict,
                gltf2_addon_export_settings,
            ),
        ):
            mtoon_dict["matcapFactor"] = list(mtoon.matcap_factor)

        mtoon_dict["parametricRimColorFactor"] = list(mtoon.parametric_rim_color_factor)
        mtoon_dict[
            "parametricRimFresnelPowerFactor"
        ] = mtoon.parametric_rim_fresnel_power_factor
        mtoon_dict["parametricRimLiftFactor"] = mtoon.parametric_rim_lift_factor
        assign_dict(
            mtoon_dict,
            "rimMultiplyTexture",
            cls.create_mtoon1_texture_info_dict(
                json_dict,
                body_binary,
                mtoon.rim_multiply_texture,
                image_name_to_index_dict,
                gltf2_addon_export_settings,
            ),
        )
        mtoon_dict["rimLightingMixFactor"] = mtoon.rim_lighting_mix_factor
        mtoon_dict["outlineWidthMode"] = mtoon.outline_width_mode
        mtoon_dict["outlineWidthFactor"] = mtoon.outline_width_factor
        assign_dict(
            mtoon_dict,
            "outlineWidthMultiplyTexture",
            cls.create_mtoon1_texture_info_dict(
                json_dict,
                body_binary,
                mtoon.outline_width_multiply_texture,
                image_name_to_index_dict,
                gltf2_addon_export_settings,
            ),
        )
        mtoon_dict["outlineColorFactor"] = list(mtoon.outline_color_factor)
        mtoon_dict["outlineLightingMixFactor"] = mtoon.outline_lighting_mix_factor
        assign_dict(
            mtoon_dict,
            "uvAnimationMaskTexture",
            cls.create_mtoon1_texture_info_dict(
                json_dict,
                body_binary,
                mtoon.uv_animation_mask_texture,
                image_name_to_index_dict,
                gltf2_addon_export_settings,
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

    @classmethod
    def create_legacy_gltf_material_dict(
        cls,
        json_dict: dict[str, Json],
        body_binary: bytearray,
        material: Material,
        node: Node,
        image_name_to_index_dict: dict[str, int],
        gltf2_addon_export_settings: dict[str, object],
    ) -> dict[str, Json]:
        material_dict: dict[str, Json] = {"name": material.name}
        pbr_metallic_roughness_dict: dict[str, Json] = {}

        if material.blend_method == "OPAQUE":
            material_dict["alphaMode"] = "OPAQUE"
        elif material.blend_method == "CLIP":
            material_dict["alphaCutoff"] = max(0, min(1, material.alpha_threshold))
            material_dict["alphaMode"] = "MASK"
        else:
            material_dict["alphaMode"] = "BLEND"
        assign_dict(
            material_dict, "doubleSided", not material.use_backface_culling, False
        )
        assign_dict(
            pbr_metallic_roughness_dict,
            "baseColorFactor",
            shader.get_rgba_value(node, "base_Color", 0.0, 1.0),
        )
        base_color_texture_dict = cls.create_mtoon0_texture_info_dict(
            json_dict,
            body_binary,
            node,
            "color_texture",
            image_name_to_index_dict,
            gltf2_addon_export_settings,
        )
        assign_dict(
            pbr_metallic_roughness_dict, "baseColorTexture", base_color_texture_dict
        )

        assign_dict(
            pbr_metallic_roughness_dict,
            "metallicFactor",
            shader.get_float_value(node, "metallic", 0.0, 1.0),
            default_value=1.0,
        )
        assign_dict(
            pbr_metallic_roughness_dict,
            "roughnessFactor",
            shader.get_float_value(node, "roughness", 0.0, 1.0),
            default_value=1.0,
        )
        assign_dict(
            pbr_metallic_roughness_dict,
            "metallicRoughnessTexture",
            cls.create_mtoon0_texture_info_dict(
                json_dict,
                body_binary,
                node,
                "emissive_texture",
                image_name_to_index_dict,
                gltf2_addon_export_settings,
            ),
        )

        normal_texture_dict = cls.create_mtoon0_texture_info_dict(
            json_dict,
            body_binary,
            node,
            "normal",
            image_name_to_index_dict,
            gltf2_addon_export_settings,
        )
        assign_dict(material_dict, "normalTexture", normal_texture_dict)

        assign_dict(
            material_dict,
            "emissiveFactor",
            shader.get_rgb_value(node, "emissive_color", 0.0, 1.0),
        )
        assign_dict(
            material_dict,
            "emissiveTexture",
            cls.create_mtoon0_texture_info_dict(
                json_dict,
                body_binary,
                node,
                "emissive_texture",
                image_name_to_index_dict,
                gltf2_addon_export_settings,
            ),
        )

        assign_dict(
            material_dict,
            "occlusionTexture",
            cls.create_mtoon0_texture_info_dict(
                json_dict,
                body_binary,
                node,
                "occlusion_texture",
                image_name_to_index_dict,
                gltf2_addon_export_settings,
            ),
        )

        if pbr_metallic_roughness_dict:
            material_dict["pbrMetallicRoughness"] = pbr_metallic_roughness_dict

        unlit_value = shader.get_float_value(node, "unlit")
        if unlit_value is None or unlit_value > 0.5:
            extensions_used = json_dict.get("extensionsUsed")
            if not isinstance(extensions_used, list):
                extensions_used = []
                json_dict["extensionsUsed"] = extensions_used

            if "KHR_materials_unlit" not in extensions_used:
                extensions_used.append("KHR_materials_unlit")

            material_dict["extensions"] = {"KHR_materials_unlit": {}}

        return material_dict

    @classmethod
    def create_legacy_transparent_zwrite_material_dict(
        cls,
        json_dict: dict[str, Json],
        body_binary: bytearray,
        material: Material,
        node: Node,
        image_name_to_index_dict: dict[str, int],
        gltf2_addon_export_settings: dict[str, object],
    ) -> dict[str, Json]:
        # https://vrm-c.github.io/UniVRM/en/implementation/transparent_zwrite.html#mtoon-unlit
        extensions_used = json_dict.get("extensionsUsed")
        if not isinstance(extensions_used, list):
            extensions_used = []
            json_dict["extensionsUsed"] = extensions_used

        if "KHR_materials_unlit" not in extensions_used:
            extensions_used.append("KHR_materials_unlit")
        if "VRMC_materials_mtoon" not in extensions_used:
            extensions_used.append("VRMC_materials_mtoon")

        mtoon_dict: dict[str, Json] = {
            "specVersion": "1.0",
        }
        extensions_dict: dict[str, Json] = {
            "KHR_materials_unlit": {},
            "VRMC_materials_mtoon": mtoon_dict,
        }

        material_dict: dict[str, Json] = {
            "name": material.name,
            "emissiveFactor": [1, 1, 1],
        }
        pbr_metallic_roughness_dict: dict[str, Json] = {
            "baseColorFactor": [0, 0, 0, 1],
        }

        material_dict["alphaMode"] = "BLEND"
        mtoon_dict["transparentWithZWrite"] = True
        mtoon_dict["renderQueueOffsetNumber"] = 0
        assign_dict(
            material_dict, "doubleSided", not material.use_backface_culling, False
        )
        base_color_texture_dict = cls.create_mtoon0_texture_info_dict(
            json_dict,
            body_binary,
            node,
            "Main_Texture",
            image_name_to_index_dict,
            gltf2_addon_export_settings,
        )
        assign_dict(
            pbr_metallic_roughness_dict, "baseColorTexture", base_color_texture_dict
        )
        if base_color_texture_dict is not None:
            mtoon_dict["shadeMultiplyTexture"] = base_color_texture_dict
            material_dict["emissiveTexture"] = base_color_texture_dict

        if pbr_metallic_roughness_dict:
            material_dict["pbrMetallicRoughness"] = pbr_metallic_roughness_dict

        extensions_dict["VRMC_materials_mtoon"] = mtoon_dict
        material_dict["extensions"] = extensions_dict

        return material_dict

    @classmethod
    def create_mtoon_unversioned_material_dict(
        cls,
        json_dict: dict[str, Json],
        body_binary: bytearray,
        material: Material,
        node: Node,
        image_name_to_index_dict: dict[str, int],
        gltf2_addon_export_settings: dict[str, object],
    ) -> dict[str, Json]:
        extensions_used = json_dict.get("extensionsUsed")
        if not isinstance(extensions_used, list):
            extensions_used = []
            json_dict["extensionsUsed"] = extensions_used

        if "KHR_materials_unlit" not in extensions_used:
            extensions_used.append("KHR_materials_unlit")
        if "VRMC_materials_mtoon" not in extensions_used:
            extensions_used.append("VRMC_materials_mtoon")

        # https://github.com/vrm-c/UniVRM/blob/f3479190c330ec6ecd2b40be919285aa93a53aff/Assets/VRM10/Runtime/Migration/Materials/MigrationMToonMaterial.cs
        mtoon_dict: dict[str, Json] = {
            "specVersion": "1.0",
        }
        extensions_dict: dict[str, Json] = {
            "KHR_materials_unlit": {},
            "VRMC_materials_mtoon": mtoon_dict,
        }

        material_dict: dict[str, Json] = {"name": material.name}
        pbr_metallic_roughness_dict: dict[str, Json] = {}

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
            shader.get_rgba_value(node, "DiffuseColor", 0.0, 1.0),
        )
        base_color_texture_dict = cls.create_mtoon0_texture_info_dict(
            json_dict,
            body_binary,
            node,
            "MainTexture",
            image_name_to_index_dict,
            gltf2_addon_export_settings,
        )
        assign_dict(
            pbr_metallic_roughness_dict, "baseColorTexture", base_color_texture_dict
        )
        assign_dict(
            mtoon_dict,
            "shadeColorFactor",
            shader.get_rgb_value(node, "ShadeColor", 0.0, 1.0),
        )
        shade_multiply_texture_dict = cls.create_mtoon0_texture_info_dict(
            json_dict,
            body_binary,
            node,
            "ShadeTexture",
            image_name_to_index_dict,
            gltf2_addon_export_settings,
        )
        if shade_multiply_texture_dict is not None:
            mtoon_dict["shadeMultiplyTexture"] = shade_multiply_texture_dict
        elif base_color_texture_dict is not None:
            # https://github.com/vrm-c/UniVRM/blob/f3479190c330ec6ecd2b40be919285aa93a53aff/Assets/VRM10/Runtime/Migration/Materials/MigrationMToonMaterial.cs#L185-L204
            mtoon_dict["shadeMultiplyTexture"] = base_color_texture_dict
        normal_texture_dict = cls.create_mtoon0_texture_info_dict(
            json_dict,
            body_binary,
            node,
            "NormalmapTexture",
            image_name_to_index_dict,
            gltf2_addon_export_settings,
        )
        if not normal_texture_dict:
            normal_texture_dict = cls.create_mtoon0_texture_info_dict(
                json_dict,
                body_binary,
                node,
                "NomalmapTexture",
                image_name_to_index_dict,
                gltf2_addon_export_settings,
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

        mtoon_dict["shadingShiftFactor"] = convert.mtoon_shading_shift_0_to_1(
            shading_toony_0x, shading_shift_0x
        )

        mtoon_dict["shadingToonyFactor"] = convert.mtoon_shading_toony_0_to_1(
            shading_toony_0x, shading_shift_0x
        )

        gi_equalization_0x = shader.get_float_value(node, "IndirectLightIntensity")
        if gi_equalization_0x is not None:
            mtoon_dict[
                "giEqualizationFactor"
            ] = convert.mtoon_intensity_to_gi_equalization(gi_equalization_0x)

        assign_dict(
            material_dict,
            "emissiveFactor",
            shader.get_rgb_value(node, "EmissionColor", 0.0, 1.0),
        )
        assign_dict(
            material_dict,
            "emissiveTexture",
            cls.create_mtoon0_texture_info_dict(
                json_dict,
                body_binary,
                node,
                "Emission_Texture",
                image_name_to_index_dict,
                gltf2_addon_export_settings,
            ),
        )
        if assign_dict(
            mtoon_dict,
            "matcapTexture",
            cls.create_mtoon0_texture_info_dict(
                json_dict,
                body_binary,
                node,
                "SphereAddTexture",
                image_name_to_index_dict,
                gltf2_addon_export_settings,
            ),
        ):
            mtoon_dict["matcapFactor"] = [1, 1, 1]

        assign_dict(
            mtoon_dict,
            "parametricRimColorFactor",
            shader.get_rgb_value(node, "RimColor", 0.0, 1.0),
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
            cls.create_mtoon0_texture_info_dict(
                json_dict,
                body_binary,
                node,
                "RimTexture",
                image_name_to_index_dict,
                gltf2_addon_export_settings,
            ),
        )

        # https://github.com/vrm-c/UniVRM/blob/7c9919ef47a25c04100a2dcbe6a75dff49ef4857/Assets/VRM10/Runtime/Migration/Materials/MigrationMToonMaterial.cs#L287-L290
        mtoon_dict["rimLightingMixFactor"] = 1.0

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
            cls.create_mtoon0_texture_info_dict(
                json_dict,
                body_binary,
                node,
                "OutlineWidthTexture",
                image_name_to_index_dict,
                gltf2_addon_export_settings,
            ),
        )
        assign_dict(
            mtoon_dict,
            "outlineColorFactor",
            shader.get_rgb_value(node, "OutlineColor", 0.0, 1.0),
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
            cls.create_mtoon0_texture_info_dict(
                json_dict,
                body_binary,
                node,
                "UV_Animation_Mask_Texture",
                image_name_to_index_dict,
                gltf2_addon_export_settings,
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

    @classmethod
    def save_vrm_materials(
        cls,
        json_dict: dict[str, Json],
        body_binary: bytearray,
        material_name_to_index_dict: dict[str, int],
        image_name_to_index_dict: dict[str, int],
        gltf2_addon_export_settings: dict[str, object],
    ) -> None:
        material_dicts = json_dict.get("materials")
        if not isinstance(material_dicts, list):
            material_dicts = []
            json_dict["materials"] = material_dicts

        for material_name, index in material_name_to_index_dict.items():
            material = bpy.data.materials.get(material_name)
            if not isinstance(material, Material) or not (
                0 <= index < len(material_dicts)
            ):
                continue

            if material.vrm_addon_extension.mtoon1.enabled:
                material_dicts[index] = cls.create_mtoon1_material_dict(
                    json_dict,
                    body_binary,
                    material,
                    image_name_to_index_dict,
                    gltf2_addon_export_settings,
                )
                continue

            # MToon_unversioned (MToon for VRM 0.0)
            node = search.vrm_shader_node(material)
            if not isinstance(node, Node):
                continue
            shader_name = node.node_tree.get("SHADER")
            if shader_name == "MToon_unversioned":
                material_dicts[index] = cls.create_mtoon_unversioned_material_dict(
                    json_dict,
                    body_binary,
                    material,
                    node,
                    image_name_to_index_dict,
                    gltf2_addon_export_settings,
                )
            elif shader_name == "GLTF":
                material_dicts[index] = cls.create_legacy_gltf_material_dict(
                    json_dict,
                    body_binary,
                    material,
                    node,
                    image_name_to_index_dict,
                    gltf2_addon_export_settings,
                )
            elif shader_name == "TRANSPARENT_ZWRITE":
                material_dicts[
                    index
                ] = cls.create_legacy_transparent_zwrite_material_dict(
                    json_dict,
                    body_binary,
                    material,
                    node,
                    image_name_to_index_dict,
                    gltf2_addon_export_settings,
                )

        if material_dicts:
            json_dict["materials"] = material_dicts

    @classmethod
    def disable_mtoon1_material_nodes(cls) -> list[str]:
        disabled_material_names = []
        for material in bpy.data.materials:
            if not material:
                continue
            if material.vrm_addon_extension.mtoon1.enabled and material.use_nodes:
                material.use_nodes = False
                disabled_material_names.append(material.name)
        return disabled_material_names

    @classmethod
    def restore_mtoon1_material_nodes(cls, disabled_material_names: list[str]) -> None:
        for disabled_material_name in disabled_material_names:
            material = bpy.data.materials.get(disabled_material_name)
            if not material:
                continue
            if not material.use_nodes:
                material.use_nodes = True

    @classmethod
    def unassign_normal_from_mtoon_primitive_morph_target(
        cls,
        json_dict: dict[str, Json],
        material_name_to_index_dict: dict[str, int],
    ) -> None:
        mesh_dicts = json_dict.get("meshes")
        if not isinstance(mesh_dicts, list):
            return
        for mesh_dict in mesh_dicts:
            if not isinstance(mesh_dict, dict):
                continue
            primitive_dicts = mesh_dict.get("primitives")
            if not isinstance(primitive_dicts, list):
                continue
            for primitive_dict in primitive_dicts:
                if not isinstance(primitive_dict, dict):
                    continue
                material_index = primitive_dict.get("material")
                if not isinstance(material_index, int):
                    continue

                skip = True
                for (
                    search_material_name,
                    search_material_index,
                ) in material_name_to_index_dict.items():
                    if material_index != search_material_index:
                        continue
                    material = bpy.data.materials.get(search_material_name)
                    if not material:
                        continue
                    if material.vrm_addon_extension.mtoon1.export_shape_key_normals:
                        continue
                    if material.vrm_addon_extension.mtoon1.enabled:
                        skip = False
                        break
                    node = search.vrm_shader_node(material)
                    if not node:
                        continue
                    if node.node_tree["SHADER"] == "MToon_unversioned":
                        skip = False
                        break
                if skip:
                    continue

                target_dicts = primitive_dict.get("targets")
                if not isinstance(target_dicts, list):
                    continue
                for target_dict in target_dicts:
                    if not isinstance(target_dict, dict):
                        continue
                    target_dict.pop("NORMAL", None)

    @classmethod
    def setup_dummy_human_bones(
        cls,
        context: Context,
        armature: Object,
        armature_data: Armature,
    ) -> Optional[dict[HumanBoneName, str]]:
        ext = armature_data.vrm_addon_extension
        human_bones = ext.vrm1.humanoid.human_bones
        if human_bones.all_required_bones_are_assigned():
            return None

        human_bone_name_to_bone_name: dict[HumanBoneName, str] = {}
        for (
            human_bone_name,
            human_bone,
        ) in human_bones.human_bone_name_to_human_bone().items():
            if not human_bone.node.bone_name:
                continue
            human_bone_name_to_bone_name[human_bone_name] = human_bone.node.bone_name
            human_bone.node.bone_name = ""

        previous_active = context.view_layer.objects.active
        try:
            context.view_layer.objects.active = armature
            bpy.ops.object.mode_set(mode="EDIT")

            hips_bone = armature_data.edit_bones.new(HumanBoneName.HIPS.value)
            hips_bone.head = Vector((0, 0, 0.5))
            hips_bone.tail = Vector((0, 1, 0.5))
            hips_bone_name = deepcopy(hips_bone.name)

            right_upper_leg_bone = armature_data.edit_bones.new(
                HumanBoneName.RIGHT_UPPER_LEG.value
            )
            right_upper_leg_bone.head = Vector((-0.125, 0, 0.5))
            right_upper_leg_bone.tail = Vector((-0.125, 1, 0.5))
            right_upper_leg_bone.parent = hips_bone
            right_upper_leg_bone_name = deepcopy(right_upper_leg_bone.name)

            right_lower_leg_bone = armature_data.edit_bones.new(
                HumanBoneName.RIGHT_LOWER_LEG.value
            )
            right_lower_leg_bone.head = Vector((-0.125, 0, 0.25))
            right_lower_leg_bone.tail = Vector((-0.125, 1, 0.25))
            right_lower_leg_bone.parent = right_upper_leg_bone
            right_lower_leg_bone_name = deepcopy(right_lower_leg_bone.name)

            right_foot_bone = armature_data.edit_bones.new(
                HumanBoneName.RIGHT_FOOT.value
            )
            right_foot_bone.head = Vector((-0.125, 0, 0))
            right_foot_bone.tail = Vector((-0.125, 1, 0))
            right_foot_bone.parent = right_lower_leg_bone
            right_foot_bone_name = deepcopy(right_foot_bone.name)

            left_upper_leg_bone = armature_data.edit_bones.new(
                HumanBoneName.LEFT_UPPER_LEG.value
            )
            left_upper_leg_bone.head = Vector((0.125, 0, 0.5))
            left_upper_leg_bone.tail = Vector((0.125, 1, 0.5))
            left_upper_leg_bone.parent = hips_bone
            left_upper_leg_bone_name = deepcopy(left_upper_leg_bone.name)

            left_lower_leg_bone = armature_data.edit_bones.new(
                HumanBoneName.LEFT_LOWER_LEG.value
            )
            left_lower_leg_bone.head = Vector((0.125, 0, 0.25))
            left_lower_leg_bone.tail = Vector((0.125, 1, 0.25))
            left_lower_leg_bone.parent = left_upper_leg_bone
            left_lower_leg_bone_name = deepcopy(left_lower_leg_bone.name)

            left_foot_bone = armature_data.edit_bones.new(HumanBoneName.LEFT_FOOT.value)
            left_foot_bone.head = Vector((0.125, 0, 0))
            left_foot_bone.tail = Vector((0.125, 1, 0))
            left_foot_bone.parent = left_lower_leg_bone
            left_foot_bone_name = deepcopy(left_foot_bone.name)

            spine_bone = armature_data.edit_bones.new(HumanBoneName.SPINE.value)
            spine_bone.head = Vector((0, 0, 0.625))
            spine_bone.tail = Vector((0, 1, 0.625))
            spine_bone.parent = hips_bone
            spine_bone_name = deepcopy(spine_bone.name)

            right_upper_arm_bone = armature_data.edit_bones.new(
                HumanBoneName.RIGHT_UPPER_ARM.value
            )
            right_upper_arm_bone.head = Vector((-0.125, 0, 0.75))
            right_upper_arm_bone.tail = Vector((-0.125, 1, 0.75))
            right_upper_arm_bone.parent = spine_bone
            right_upper_arm_bone_name = deepcopy(right_upper_arm_bone.name)

            right_lower_arm_bone = armature_data.edit_bones.new(
                HumanBoneName.RIGHT_LOWER_ARM.value
            )
            right_lower_arm_bone.head = Vector((-0.25, 0, 0.75))
            right_lower_arm_bone.tail = Vector((-0.25, 1, 0.75))
            right_lower_arm_bone.parent = right_upper_arm_bone
            right_lower_arm_bone_name = deepcopy(right_lower_arm_bone.name)

            right_hand_bone = armature_data.edit_bones.new(
                HumanBoneName.RIGHT_HAND.value
            )
            right_hand_bone.head = Vector((-0.375, 0, 0.75))
            right_hand_bone.tail = Vector((-0.375, 1, 0.75))
            right_hand_bone.parent = right_lower_arm_bone
            right_hand_bone_name = deepcopy(right_hand_bone.name)

            left_upper_arm_bone = armature_data.edit_bones.new(
                HumanBoneName.LEFT_UPPER_ARM.value
            )
            left_upper_arm_bone.head = Vector((0.125, 0, 0.75))
            left_upper_arm_bone.tail = Vector((0.125, 1, 0.75))
            left_upper_arm_bone.parent = spine_bone
            left_upper_arm_bone_name = deepcopy(left_upper_arm_bone.name)

            left_lower_arm_bone = armature_data.edit_bones.new(
                HumanBoneName.LEFT_LOWER_ARM.value
            )
            left_lower_arm_bone.head = Vector((0.25, 0, 0.75))
            left_lower_arm_bone.tail = Vector((0.25, 1, 0.75))
            left_lower_arm_bone.parent = left_upper_arm_bone
            left_lower_arm_bone_name = deepcopy(left_lower_arm_bone.name)

            left_hand_bone = armature_data.edit_bones.new(HumanBoneName.LEFT_HAND.value)
            left_hand_bone.head = Vector((0.375, 0, 0.75))
            left_hand_bone.tail = Vector((0.375, 1, 0.75))
            left_hand_bone.parent = left_lower_arm_bone
            left_hand_bone_name = deepcopy(left_hand_bone.name)

            head_bone = armature_data.edit_bones.new(HumanBoneName.HEAD.value)
            head_bone.head = Vector((0, 0, 0.75))
            head_bone.tail = Vector((0, 1, 0.75))
            head_bone.parent = spine_bone
            head_bone_name = deepcopy(head_bone.name)
        finally:
            if (
                context.view_layer.objects.active
                and context.view_layer.objects.active.mode != "OBJECT"
            ):
                bpy.ops.object.mode_set(mode="OBJECT")
            context.view_layer.objects.active = previous_active

        Vrm1HumanBonesPropertyGroup.check_last_bone_names_and_update(
            armature_data.name, defer=False
        )

        human_bones.head.node.bone_name = head_bone_name
        human_bones.spine.node.bone_name = spine_bone_name
        human_bones.hips.node.bone_name = hips_bone_name

        human_bones.right_upper_arm.node.bone_name = right_upper_arm_bone_name
        human_bones.right_lower_arm.node.bone_name = right_lower_arm_bone_name
        human_bones.right_hand.node.bone_name = right_hand_bone_name

        human_bones.left_upper_arm.node.bone_name = left_upper_arm_bone_name
        human_bones.left_lower_arm.node.bone_name = left_lower_arm_bone_name
        human_bones.left_hand.node.bone_name = left_hand_bone_name

        human_bones.right_upper_leg.node.bone_name = right_upper_leg_bone_name
        human_bones.right_lower_leg.node.bone_name = right_lower_leg_bone_name
        human_bones.right_foot.node.bone_name = right_foot_bone_name

        human_bones.left_upper_leg.node.bone_name = left_upper_leg_bone_name
        human_bones.left_lower_leg.node.bone_name = left_lower_leg_bone_name
        human_bones.left_foot.node.bone_name = left_foot_bone_name

        return human_bone_name_to_bone_name

    @classmethod
    def restore_dummy_human_bones(
        cls,
        context: Context,
        armature: Object,
        armature_data: Armature,
        human_bone_name_to_bone_name: dict[HumanBoneName, str],
    ) -> None:
        ext = armature_data.vrm_addon_extension
        human_bones = ext.vrm1.humanoid.human_bones

        human_bone_name_to_human_bone = human_bones.human_bone_name_to_human_bone()
        dummy_bone_names = deepcopy(
            [
                human_bone.node.bone_name
                for human_bone in human_bone_name_to_human_bone.values()
                if human_bone.node.bone_name
            ]
        )

        for human_bone_name, human_bone in human_bone_name_to_human_bone.items():
            bone_name = human_bone_name_to_bone_name.get(human_bone_name)
            if bone_name:
                human_bone.node.bone_name = bone_name
            else:
                human_bone.node.bone_name = ""

        previous_active = context.view_layer.objects.active
        try:
            context.view_layer.objects.active = armature
            bpy.ops.object.mode_set(mode="EDIT")

            for dummy_bone_name in dummy_bone_names:
                dummy_edit_bone = armature_data.edit_bones.get(dummy_bone_name)
                if dummy_edit_bone:
                    armature_data.edit_bones.remove(dummy_edit_bone)
        finally:
            if (
                context.view_layer.objects.active
                and context.view_layer.objects.active.mode != "OBJECT"
            ):
                bpy.ops.object.mode_set(mode="OBJECT")
            context.view_layer.objects.active = previous_active

    def export_vrm(self) -> Optional[bytes]:
        init_extras_export()

        armature_data = self.armature.data
        if not isinstance(armature_data, Armature):
            message = f"{type(armature_data)} is not an Armature"
            raise TypeError(message)

        vrm = armature_data.vrm_addon_extension.vrm1
        backup_human_bone_name_to_bone_name = self.setup_dummy_human_bones(
            self.context, self.armature, armature_data
        )
        # dummy_skinned_mesh_object_name = self.create_dummy_skinned_mesh_object()
        object_name_to_modifier_name = self.hide_mtoon1_outline_geometry_nodes()
        blend_shape_previews = self.clear_blend_shape_proxy_previews(armature_data)
        disabled_mtoon1_material_names = []
        try:
            self.setup_pose(
                self.armature,
                armature_data,
                vrm.humanoid.pose_library,
                vrm.humanoid.pose_marker_name,
            )

            self.armature[self.extras_main_armature_key] = True
            # 他glTF2ExportUserExtensionの影響を最小化するため、
            # 影響が少ないと思われるカスタムプロパティを使って
            # Blenderのオブジェクトとインデックスの対応をとる。
            for obj in bpy.data.objects:
                obj[self.extras_object_name_key] = obj.name
            for material in bpy.data.materials:
                material[self.extras_material_name_key] = material.name

            # glTF 2.0アドオンのコメントにはPoseBoneとのカスタムプロパティを保存すると
            # 書いてあるが、実際にはBoneのカスタムプロパティを参照している。
            # そのため、いちおう両方に書いておく
            for pose_bone in self.armature.pose.bones:
                pose_bone[self.extras_bone_name_key] = pose_bone.name
            for bone in armature_data.bones:
                bone[self.extras_bone_name_key] = bone.name

            self.overwrite_object_visibility_and_selection()
            self.mount_skinned_mesh_parent()
            disabled_mtoon1_material_names = self.disable_mtoon1_material_nodes()
            with tempfile.TemporaryDirectory() as temp_dir:
                filepath = Path(temp_dir, "out.glb")
                export_scene_gltf_result = export_scene_gltf(
                    ExportSceneGltfArguments(
                        filepath=str(filepath),
                        check_existing=False,
                        export_format="GLB",
                        export_extras=True,
                        export_current_frame=True,
                        use_selection=True,
                        export_animations=True,
                        export_rest_position_armature=False,
                        export_apply=True,
                        # Models may appear incorrectly in many viewers
                        export_all_influences=self.export_all_influences,
                        # TODO: Expose UI Option, Unity allows light export
                        export_lights=self.export_lights,
                        # UniVRM 0.115.0 doesn't support `export_try_sparse_sk`
                        # https://github.com/saturday06/VRM-Addon-for-Blender/issues/381#issuecomment-1838365762
                        export_try_sparse_sk=False,
                    )
                )
                if export_scene_gltf_result == {"CANCELLED"}:
                    return None
                if export_scene_gltf_result != {"FINISHED"}:
                    message = (
                        'The glTF2 Exporter has not been {"FINISHED"}'
                        f" but {export_scene_gltf_result}"
                    )
                    raise AssertionError(message)
                extra_name_assigned_glb = filepath.read_bytes()
        finally:
            self.restore_mtoon1_material_nodes(disabled_mtoon1_material_names)
            for pose_bone in self.armature.pose.bones:
                pose_bone.pop(self.extras_bone_name_key, None)
            for bone in armature_data.bones:
                bone.pop(self.extras_bone_name_key, None)
            for obj in bpy.data.objects:
                obj.pop(self.extras_object_name_key, None)
            self.armature.pop(self.extras_main_armature_key, None)
            for material in bpy.data.materials:
                material.pop(self.extras_material_name_key, None)

            self.restore_object_visibility_and_selection()
            self.restore_skinned_mesh_parent()
            # self.destroy_dummy_skinned_mesh_object(dummy_skinned_mesh_object_name)
            self.restore_mtoon1_outline_geometry_nodes(object_name_to_modifier_name)
            self.restore_pose(self.armature, armature_data)
            self.restore_blend_shape_proxy_previews(armature_data, blend_shape_previews)

        json_dict, body_binary = parse_glb(extra_name_assigned_glb)
        body_binary = bytearray(body_binary)

        bone_name_to_index_dict: dict[str, int] = {}
        object_name_to_index_dict: dict[str, int] = {}
        image_name_to_index_dict: dict[str, int] = {}
        mesh_object_name_to_node_index_dict: dict[str, int] = {}
        mesh_object_name_to_morph_target_names_dict: dict[str, list[str]] = {}

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
            json_dict[key] = list(list_value) if isinstance(list_value, list) else []

        node_dicts = json_dict.get("nodes")
        if not isinstance(node_dicts, list):
            node_dicts = []
            json_dict["nodes"] = node_dicts

        for node_index, node_dict in enumerate(node_dicts):
            if not isinstance(node_dict, dict):
                continue
            extras_dict = node_dict.get("extras")
            if not isinstance(extras_dict, dict):
                continue

            bone_name = extras_dict.pop(self.extras_bone_name_key, None)
            if isinstance(bone_name, str):
                bone_name_to_index_dict[bone_name] = node_index

            is_main_armature = extras_dict.pop(self.extras_main_armature_key, None)

            object_name = extras_dict.pop(self.extras_object_name_key, None)
            if isinstance(object_name, str):
                object_name_to_index_dict[object_name] = node_index
                if bpy.app.version < (3, 3):
                    is_main_armature = object_name == self.armature.name

            if is_main_armature:
                if not extras_dict:
                    node_dict.pop("extras", None)

                armature_world_matrix = (
                    find_node_world_matrix(node_dicts, node_index, None) or Matrix()
                )

                # シーンにメインアーマチュアが存在したら置換する
                scene_dicts = json_dict.get("scenes")
                if isinstance(scene_dicts, list):
                    armature_replaced = False
                    for scene_dict in scene_dicts:
                        if not isinstance(scene_dict, dict):
                            continue
                        scene_node_indices = scene_dict.get("nodes")
                        if not isinstance(scene_node_indices, list):
                            continue

                        # シーンに属するノードのうち、そのアーマチュアの祖先ノードを削除
                        for scene_node_index in list(scene_node_indices):
                            if not isinstance(scene_node_index, int):
                                continue
                            search_scene_node_indices = [scene_node_index]
                            while search_scene_node_indices:
                                search_scene_node_index = (
                                    search_scene_node_indices.pop()
                                )
                                if search_scene_node_index == node_index:
                                    scene_node_indices.remove(scene_node_index)
                                    break
                                if not 0 <= search_scene_node_index < len(node_dicts):
                                    continue
                                search_scene_node_dict = node_dicts[
                                    search_scene_node_index
                                ]
                                if not isinstance(search_scene_node_dict, dict):
                                    continue
                                child_indices = search_scene_node_dict.get("children")
                                if not isinstance(child_indices, list):
                                    continue
                                for child_index in child_indices:
                                    if not isinstance(child_index, int):
                                        continue
                                    search_scene_node_indices.append(child_index)

                        child_indices = node_dict.get("children")
                        if not isinstance(child_indices, list):
                            continue
                        for child_index in child_indices:
                            if (
                                not isinstance(child_index, int)
                                or not 0 <= child_index < len(node_dicts)
                                or child_index in scene_node_indices
                            ):
                                continue
                            scene_node_indices.append(child_index)
                            if armature_replaced:
                                continue
                            # メインアーマチュアまでのワールド行列をその子供に適用
                            child_node_dict = node_dicts[child_index]
                            if not isinstance(child_node_dict, dict):
                                continue
                            child_matrix = get_node_matrix(child_node_dict)
                            set_node_matrix(
                                child_node_dict,
                                armature_world_matrix @ child_matrix,
                            )
                        armature_replaced = True
                    if armature_replaced:
                        node_dict.pop("children", None)
                        node_dict["name"] = "secondary"  # Assign dummy name
                        continue

            mesh_index = node_dict.get("mesh")
            mesh_dicts = json_dict.get("meshes")
            if (
                isinstance(object_name, str)
                and isinstance(mesh_index, int)
                and isinstance(mesh_dicts, list)
                and 0 <= mesh_index < len(mesh_dicts)
            ):
                mesh_object_name_to_node_index_dict[object_name] = node_index
                target_names = deep.get(
                    mesh_dicts, [mesh_index, "extras", "targetNames"]
                )
                if isinstance(target_names, list):
                    mesh_object_name_to_morph_target_names_dict[object_name] = [
                        str(target_name) for target_name in target_names
                    ]
            if isinstance(object_name, str) and (
                object_name.startswith(INTERNAL_NAME_PREFIX + "VrmAddonLinkTo")
                # or object_name == dummy_skinned_mesh_object_name
            ):
                node_dict.clear()
                for child_removing_node_dict in node_dicts:
                    if not isinstance(child_removing_node_dict, dict):
                        continue
                    children = child_removing_node_dict.get("children")
                    if not isinstance(children, list):
                        continue
                    children = [child for child in children if child != node_index]
                    if children:
                        child_removing_node_dict["children"] = children
                    else:
                        child_removing_node_dict.pop("children", None)

                # TODO: remove from scenes, skin joints ...

            if not extras_dict and "extras" in node_dict:
                node_dict.pop("extras", None)

        node_constraint_spec_version = "1.0"
        use_node_constraint = False
        object_constraints, bone_constraints, _ = search.export_constraints(
            self.export_objects, self.armature
        )

        for object_name, node_index in object_name_to_index_dict.items():
            if not 0 <= node_index < len(node_dicts):
                continue
            node_dict = node_dicts[node_index]
            if not isinstance(node_dict, dict):
                node_dict = {}
                node_dicts[node_index] = node_dict
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

        for bone_name, node_index in bone_name_to_index_dict.items():
            if not 0 <= node_index < len(node_dicts):
                continue
            node_dict = node_dicts[node_index]
            if not isinstance(node_dict, dict):
                node_dict = {}
                node_dicts[node_index] = node_dicts
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

        material_name_to_index_dict: dict[str, int] = {}
        material_dicts = json_dict.get("materials")
        if not isinstance(material_dicts, list):
            material_dicts = []
            json_dict["materials"] = material_dicts
        for material_index, material_dict in enumerate(material_dicts):
            if not isinstance(material_dict, dict):
                continue
            extras_dict = material_dict.get("extras")
            if not isinstance(extras_dict, dict):
                continue

            material_name = extras_dict.pop(self.extras_material_name_key, None)
            if not isinstance(material_name, str):
                continue

            material_name_to_index_dict[material_name] = material_index
            if not extras_dict:
                material_dict.pop("extras", None)

        self.save_vrm_materials(
            json_dict,
            body_binary,
            material_name_to_index_dict,
            image_name_to_index_dict,
            self.gltf2_addon_export_settings,
        )
        self.unassign_normal_from_mtoon_primitive_morph_target(
            json_dict, material_name_to_index_dict
        )

        extensions_used = json_dict.get("extensionsUsed")
        if not isinstance(extensions_used, list):
            extensions_used = []
            json_dict["extensionsUsed"] = extensions_used

        if use_node_constraint:
            extensions_used.append("VRMC_node_constraint")

        extensions = json_dict.get("extensions")
        if not isinstance(extensions, dict):
            json_dict["extensions"] = extensions = {}

        extensions_used.append("VRMC_vrm")
        extensions["VRMC_vrm"] = {
            "specVersion": armature_data.vrm_addon_extension.spec_version,
            "meta": self.create_meta_dict(
                vrm.meta,
                json_dict,
                body_binary,
                image_name_to_index_dict,
                self.gltf2_addon_export_settings,
            ),
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

        spring_bone = armature_data.vrm_addon_extension.spring_bone1
        spring_bone_dict: dict[str, Json] = {}

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
            self.armature,
        )
        if spring_bone_spring_dicts:
            spring_bone_dict["springs"] = spring_bone_spring_dicts

        if spring_bone_dict:
            extensions_used.append("VRMC_springBone")
            spring_bone_dict["specVersion"] = "1.0"
            extensions["VRMC_springBone"] = spring_bone_dict

        json_dict["extensions"] = extensions
        json_dict["extensionsUsed"] = extensions_used

        v = addon_version()
        if environ.get("BLENDER_VRM_USE_TEST_EXPORTER_VERSION") == "true":
            v = (999, 999, 999)

        generator = "VRM Add-on for Blender v" + ".".join(map(str, v))

        asset_dict = json_dict.get("asset")
        if not isinstance(asset_dict, dict):
            asset_dict = {}
            json_dict["asset"] = asset_dict

        base_generator = asset_dict.get("generator")
        if isinstance(base_generator, str):
            generator += " with " + base_generator

        asset_dict["generator"] = generator

        if len(body_binary):
            buffer_dicts = json_dict.get("buffers")
            if not isinstance(buffer_dicts, list) or not buffer_dicts:
                buffer_dicts = []
                json_dict["buffers"] = buffer_dicts
            if not buffer_dicts:
                buffer_dicts.append({})
            buffer_dict = buffer_dicts[0]
            if not isinstance(buffer_dict, dict):
                buffer_dict = {}
                buffer_dicts[0] = buffer_dict
            buffer_dict["byteLength"] = len(body_binary)

        for key in gltf_root_non_empty_array_keys:
            if not json_dict.get(key):
                json_dict.pop(key, None)

        if backup_human_bone_name_to_bone_name is not None:
            self.restore_dummy_human_bones(
                self.context,
                self.armature,
                armature_data,
                backup_human_bone_name_to_bone_name,
            )

        return pack_glb(json_dict, body_binary)


def find_node_world_matrix(
    node_dicts: list[Json],
    target_node_index: int,
    parent_node_index: Optional[int],
) -> Optional[Matrix]:
    if parent_node_index is None:
        all_child_indices: list[int] = []
        for node_dict in node_dicts:
            if not isinstance(node_dict, dict):
                continue
            child_node_indices = node_dict.get("children")
            if isinstance(child_node_indices, list):
                all_child_indices.extend(
                    child_node_index
                    for child_node_index in child_node_indices
                    if isinstance(child_node_index, int)
                )
        for node_index in range(len(node_dicts)):
            if node_index in all_child_indices:
                continue
            matrix = find_node_world_matrix(node_dicts, target_node_index, node_index)
            if matrix is not None:
                return matrix
        return Matrix()

    if not 0 <= parent_node_index < len(node_dicts):
        return None

    node_dict = node_dicts[parent_node_index]
    if not isinstance(node_dict, dict):
        return None

    parent_node_matrix = get_node_matrix(node_dict)

    if parent_node_index == target_node_index:
        return parent_node_matrix

    child_node_indices = node_dict.get("children")
    if not isinstance(child_node_indices, list):
        return None

    for child_node_index in child_node_indices:
        if not isinstance(child_node_index, int):
            continue
        child_node_matrix = find_node_world_matrix(
            node_dicts, target_node_index, child_node_index
        )
        if child_node_matrix is not None:
            return parent_node_matrix @ child_node_matrix

    return None


def get_node_matrix(node_dict: dict[str, Json]) -> Matrix:
    matrix = node_dict.get("matrix")
    if isinstance(matrix, list):
        if len(matrix) != 16:
            return Matrix()

        row0 = convert.float4_or_none((matrix[0], matrix[4], matrix[8], matrix[12]))
        row1 = convert.float4_or_none((matrix[1], matrix[5], matrix[9], matrix[13]))
        row2 = convert.float4_or_none((matrix[2], matrix[6], matrix[10], matrix[14]))
        row3 = convert.float4_or_none((matrix[3], matrix[7], matrix[11], matrix[15]))
        if not (row0 and row1 and row2 and row3):
            return Matrix()

        return Matrix((row0, row1, row2, row3))

    location_matrix = Matrix()
    location = convert.float3_or_none(node_dict.get("translation"))
    if location:
        location_matrix = Matrix.Translation(location)

    rotation_matrix = Matrix()
    rotation = convert.float4_or_none(node_dict.get("rotation"))
    if rotation:
        x, y, z, w = rotation
        quaternion = Quaternion((w, x, y, z))
        rotation_matrix = quaternion.to_matrix().to_4x4()

    scale_matrix = Matrix()
    scale = convert.float3_or_none(node_dict.get("scale"))
    if scale:
        scale_matrix = Matrix.Diagonal(scale).to_4x4()

    return location_matrix @ rotation_matrix @ scale_matrix


def set_node_matrix(node_dict: dict[str, Json], matrix: Matrix) -> None:
    node_dict.pop("matrix", None)
    location, rotation, scale = matrix.decompose()
    node_dict["translation"] = list(location)
    node_dict["rotation"] = [
        rotation.x,
        rotation.y,
        rotation.z,
        rotation.w,
    ]
    node_dict["scale"] = list(scale)
