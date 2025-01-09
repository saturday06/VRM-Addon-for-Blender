# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from pathlib import Path
from sys import float_info
from typing import TYPE_CHECKING, Optional

from bpy.app.translations import pgettext
from bpy.props import BoolProperty, CollectionProperty, IntProperty, StringProperty
from bpy.types import (
    Armature,
    Bone,
    Context,
    Event,
    Image,
    Material,
    Mesh,
    NodesModifier,
    Object,
    Operator,
    PropertyGroup,
    ShaderNodeGroup,
    ShaderNodeTexImage,
    UILayout,
)
from mathutils import Vector

from ..common import shader, version
from ..common.legacy_gltf import RGBA_INPUT_NAMES, TEXTURE_INPUT_NAMES, VAL_INPUT_NAMES
from ..common.logger import get_logger
from ..common.mtoon_unversioned import MtoonUnversioned
from ..common.preferences import get_preferences
from ..common.vrm0 import human_bone as vrm0_human_bone
from ..common.vrm1 import human_bone as vrm1_human_bone
from . import migration, search
from .extension import get_armature_extension, get_material_extension
from .property_group import CollectionPropertyProtocol

logger = get_logger(__name__)


class VrmValidationError(PropertyGroup):
    message: StringProperty()  # type: ignore[valid-type]
    severity: IntProperty(min=0)  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        message: str  # type: ignore[no-redef]
        severity: int  # type: ignore[no-redef]


class WM_OT_vrm_validator(Operator):
    bl_idname = "vrm.model_validate"
    bl_label = "Check as VRM Model"
    bl_description = "NO Quad_Poly & N_GON, NO unSkined Mesh etc..."

    show_successful_message: BoolProperty(  # type: ignore[valid-type]
        default=True
    )
    errors: CollectionProperty(type=VrmValidationError)  # type: ignore[valid-type]
    armature_object_name: StringProperty()  # type: ignore[valid-type]

    def execute(self, context: Context) -> set[str]:
        self.detect_errors(
            context,
            self.errors,
            self.armature_object_name,
            execute_migration=True,
            readonly=False,
        )
        fatal_error_count = 0
        for error in self.errors:
            if fatal_error_count > 10:
                logger.warning("Validation error: truncated ...")
                break
            if error.severity == 0:
                logger.warning("Validation error: %s", error.message)
                fatal_error_count += 1
        if fatal_error_count > 0:
            return {"CANCELLED"}
        return {"FINISHED"}

    def invoke(self, context: Context, _event: Event) -> set[str]:
        self.detect_errors(
            context,
            self.errors,
            self.armature_object_name,
            execute_migration=True,
            readonly=False,
        )
        if (
            not any(error.severity == 0 for error in self.errors)
            and not self.show_successful_message
        ):
            return {"FINISHED"}
        return context.window_manager.invoke_props_dialog(self, width=800)

    def draw(self, _context: Context) -> None:
        self.draw_errors(
            self.layout,
            self.errors,
            show_successful_message=self.show_successful_message,
        )

    @staticmethod
    def validate_bone_order_vrm0(
        context: Context,
        messages: list[str],
        armature: Object,
        *,
        readonly: bool,
    ) -> None:
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            message = f"{type(armature_data)} is not an Armature"
            raise TypeError(message)
        humanoid = get_armature_extension(armature_data).vrm0.humanoid
        if readonly:
            humanoid.defer_update_all_node_candidates(armature_data.name)
        else:
            humanoid.update_all_node_candidates(context, armature_data.name)
        for human_bone in humanoid.human_bones:
            if (
                not human_bone.node.bone_name
                or human_bone.node.bone_name in human_bone.node_candidates
            ):
                continue
            messages.append(
                pgettext(
                    'Couldn\'t assign "{bone}" bone'
                    + ' to VRM Humanoid Bone: "{human_bone}". '
                    + 'Confirm hierarchy of "{bone}" and its children. '
                    + '"VRM" Panel → "Humanoid" → "{human_bone}" is empty'
                    + " if wrong hierarchy"
                ).format(
                    bone=human_bone.node.bone_name,
                    human_bone=human_bone.specification().title,
                )
            )
            break

    @staticmethod
    def validate_bone_order_vrm1(
        context: Context,
        messages: list[str],
        armature: Object,
        *,
        readonly: bool,
    ) -> None:
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            message = f"{type(armature_data)} is not an Armature"
            raise TypeError(message)
        human_bones = get_armature_extension(armature_data).vrm1.humanoid.human_bones
        if readonly:
            human_bones.defer_update_all_node_candidates(armature_data.name)
        else:
            human_bones.update_all_node_candidates(context, armature_data.name)
        for (
            human_bone_name,
            human_bone,
        ) in human_bones.human_bone_name_to_human_bone().items():
            if (
                not human_bone.node.bone_name
                or human_bone.node.bone_name in human_bone.node_candidates
            ):
                continue

            specification = vrm1_human_bone.HumanBoneSpecifications.get(human_bone_name)
            messages.append(
                pgettext(
                    'Couldn\'t assign "{bone}" bone'
                    + ' to VRM Humanoid Bone: "{human_bone}". '
                    + 'Confirm hierarchy of "{bone}" and its children. '
                    + '"VRM" Panel → "Humanoid" → "{human_bone}" is empty'
                    + " if wrong hierarchy"
                ).format(
                    bone=human_bone.node.bone_name,
                    human_bone=specification.title,
                )
            )
            break

    @staticmethod
    def validate_bone_order(
        context: Context,
        messages: list[str],
        armature: Object,
        *,
        readonly: bool,
    ) -> None:
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            message = f"{type(armature_data)} is not an Armature"
            raise TypeError(message)
        if get_armature_extension(armature_data).is_vrm0():
            WM_OT_vrm_validator.validate_bone_order_vrm0(
                context, messages, armature, readonly=readonly
            )
        else:
            WM_OT_vrm_validator.validate_bone_order_vrm1(
                context, messages, armature, readonly=readonly
            )

    @staticmethod
    def detect_errors(
        context: Context,
        error_collection: CollectionPropertyProtocol[VrmValidationError],
        armature_object_name: str,
        *,
        execute_migration: bool = False,
        readonly: bool = True,
    ) -> None:
        error_messages: list[str] = []
        warning_messages: list[str] = []
        skippable_warning_messages: list[str] = []
        info_messages: list[str] = []
        armature_count = 0
        armature: Optional[Object] = None
        node_names: list[str] = []

        # export object seeking
        preferences = get_preferences(context)

        version_warning_message = version.validation_warning_message()
        if version_warning_message is not None:
            warning_messages.append(version_warning_message)

        export_objects = search.export_objects(
            context,
            armature_object_name,
            export_invisibles=preferences.export_invisibles,
            export_only_selections=preferences.export_only_selections,
            export_lights=preferences.export_lights,
        )

        if not any(
            obj.type in search.MESH_CONVERTIBLE_OBJECT_TYPES for obj in export_objects
        ):
            if preferences.export_only_selections:
                warning_messages.append(
                    pgettext(
                        '"{export_only_selections}" is enabled'
                        + ", but no mesh is selected."
                    ).format(export_only_selections=pgettext("Export Only Selections"))
                )
            else:
                warning_messages.append(pgettext("There is no mesh to export."))

        armature_count = len([True for obj in export_objects if obj.type == "ARMATURE"])
        if armature_count >= 2:  # only one armature
            error_messages.append(
                pgettext("VRM exporter needs only one armature not some armatures")
            )
        if armature_count == 0:
            info_messages.append(pgettext("No armature exists."))

        for obj in export_objects:
            if obj.type in search.MESH_CONVERTIBLE_OBJECT_TYPES:
                if obj.name in node_names:
                    error_messages.append(
                        pgettext(
                            "VRM exporter need Nodes(mesh,bones) name is unique. {name}"
                            + " is doubled."
                        ).format(name=obj.name)
                    )
                if obj.name not in node_names:
                    node_names.append(obj.name)
            if (
                obj.type in search.MESH_CONVERTIBLE_OBJECT_TYPES
                and obj.parent is not None
                and obj.parent.type != "ARMATURE"
                and obj.location != Vector([0.0, 0.0, 0.0])
            ):  # mesh and armature origin is on [0,0,0]
                info_messages.append(
                    pgettext("There are not on origine location object {name}").format(
                        name=obj.name
                    )
                )
            if (
                obj.type == "MESH"
                and isinstance(obj.data, Mesh)
                and obj.data.shape_keys is not None
                and len(obj.data.shape_keys.key_blocks)
                >= 2  # Exclude a "Basis" shape key
                and any(
                    modifier.type != "ARMATURE"
                    and not (
                        modifier.type == "NODES"
                        and isinstance(modifier, NodesModifier)
                        and modifier.node_group
                        and modifier.node_group.name
                        == shader.OUTLINE_GEOMETRY_GROUP_NAME
                    )
                    for modifier in obj.modifiers
                )
            ):
                skippable_warning_messages.append(
                    pgettext(
                        'The "{name}" mesh has both a non-armature modifier'
                        + " and a shape key. However, they cannot coexist"
                        + ", so shape keys may not be export correctly."
                    ).format(name=obj.name)
                )
            if obj.type == "ARMATURE" and armature_count == 1:
                armature = obj
                armature_data = armature.data
                if not isinstance(armature_data, Armature):
                    logger.error("%s is not an Armature", type(armature_data))
                    continue
                if execute_migration:
                    migration.migrate(context, armature.name)
                bone: Optional[Bone] = None
                for bone in armature_data.bones:
                    if bone.name in node_names:  # nodes name is unique
                        error_messages.append(
                            pgettext(
                                "The same name cannot be used"
                                + " for a mesh object and a bone."
                                + ' Rename either one whose name is "{name}".'
                            ).format(name=bone.name)
                        )
                    if bone.name not in node_names:
                        node_names.append(bone.name)

                # TODO: T_POSE,
                all_required_bones_exist = True
                armature_extension = get_armature_extension(armature_data)
                if armature_extension.is_vrm1():
                    _, _, constraint_warning_messages = search.export_constraints(
                        export_objects, armature
                    )
                    skippable_warning_messages.extend(constraint_warning_messages)

                    humanoid = armature_extension.vrm1.humanoid
                    if humanoid.pose == humanoid.POSE_AUTO_POSE.identifier:
                        info_messages.append(
                            pgettext(
                                "Automatic T-Pose Conversion is enabled."
                                + " There is a setting"
                                + ' in "VRM" panel → "Humanoid" → "T-Pose".'
                            )
                        )

                    human_bones = humanoid.human_bones

                    human_bone_name_to_human_bone = (
                        human_bones.human_bone_name_to_human_bone()
                    )
                    for (
                        human_bone_name,
                        human_bone,
                    ) in human_bone_name_to_human_bone.items():
                        human_bone_specification = (
                            vrm1_human_bone.HumanBoneSpecifications.get(human_bone_name)
                        )
                        if not human_bone_specification.requirement:
                            continue
                        if (
                            human_bone.node
                            and human_bone.node.bone_name
                            and human_bone.node.bone_name in armature_data.bones
                        ):
                            continue
                        all_required_bones_exist = False
                        if not human_bones.allow_non_humanoid_rig:
                            error_messages.append(
                                pgettext(
                                    'Required VRM Bone "{humanoid_name}" is'
                                    + " not assigned. Please confirm hierarchy"
                                    + " of {humanoid_name} and its children. "
                                    + '"VRM" Panel → "Humanoid" → {humanoid_name}'
                                    + " will be empty or displayed in red"
                                    + " if hierarchy is wrong"
                                ).format(humanoid_name=human_bone_specification.title)
                            )

                    if all_required_bones_exist:
                        # https://github.com/vrm-c/vrm-specification/blob/master/specification/VRMC_vrm-1.0-beta/humanoid.md#list-of-humanoid-bones
                        for (
                            human_bone_specification
                        ) in vrm1_human_bone.HumanBoneSpecifications.all_human_bones:
                            if not human_bone_specification.parent_requirement:
                                continue
                            parent = human_bone_specification.parent()
                            if parent is None:
                                message = (
                                    f"Fatal: {human_bone_specification.name} has"
                                    + " no parent"
                                )
                                raise ValueError(message)
                            child_human_bone = human_bone_name_to_human_bone[
                                human_bone_specification.name
                            ]
                            parent_human_bone = human_bone_name_to_human_bone[
                                parent.name
                            ]
                            if (
                                child_human_bone.node.bone_name
                                and not parent_human_bone.node.bone_name
                            ):
                                error_messages.append(
                                    pgettext(
                                        'VRM Bone "{child}" needs "{parent}".'
                                        + " Please confirm"
                                        + ' "VRM" Panel → "Humanoid"'
                                        + ' → "VRM Optional Bones" → "{parent}".'
                                    ).format(
                                        child=human_bone_specification.title,
                                        parent=parent.title,
                                    )
                                )
                    if (
                        not human_bones.all_required_bones_are_assigned()
                        and human_bones.allow_non_humanoid_rig
                    ):
                        warning_messages.append(
                            pgettext(
                                "This armature will be exported but not as humanoid."
                                + " It can not have animations applied"
                                + " for humanoid avatars."
                            )
                        )

                elif armature_extension.is_vrm0():
                    humanoid = armature_extension.vrm0.humanoid
                    if humanoid.pose == humanoid.POSE_AUTO_POSE.identifier:
                        info_messages.append(
                            pgettext(
                                "Automatic T-Pose Conversion is enabled."
                                + " There is a setting"
                                + ' in "VRM" panel → "VRM 0.x Humanoid" → "T-Pose".'
                            )
                        )

                    human_bones = humanoid.human_bones
                    all_required_bones_exist = True
                    for (
                        humanoid_name
                    ) in vrm0_human_bone.HumanBoneSpecifications.required_names:
                        if any(
                            human_bone.bone == humanoid_name
                            and human_bone.node
                            and human_bone.node.bone_name
                            and human_bone.node.bone_name in armature_data.bones
                            for human_bone in human_bones
                        ):
                            continue
                        all_required_bones_exist = False
                        error_messages.append(
                            pgettext(
                                'Required VRM Bone "{humanoid_name}" is'
                                + " not assigned. Please confirm hierarchy"
                                + " of {humanoid_name} and its children."
                                + ' "VRM" Panel → "VRM 0.x Humanoid" → {humanoid_name}'
                                + " will be empty or displayed in red"
                                + " if hierarchy is wrong"
                            ).format(humanoid_name=humanoid_name.capitalize())
                        )
                if all_required_bones_exist:
                    WM_OT_vrm_validator.validate_bone_order(
                        context, error_messages, armature, readonly=readonly
                    )

            if obj.type == "MESH":
                mesh_data = obj.data
                if not isinstance(mesh_data, Mesh):
                    logger.error("%s is not a Mesh", type(mesh_data))
                    continue
                for poly in mesh_data.polygons:
                    if poly.loop_total > 3:  # polygons need all triangle
                        info_messages.append(
                            pgettext(
                                'Non-tri faces detected in "{name}". '
                                + "will be triangulated automatically.",
                            ).format(name=obj.name)
                        )
                        break

                # TODO: modifier applied, vertex weight Bone exist
                # and vertex weight numbers.

        if (
            armature is not None
            and isinstance(armature.data, Armature)
            and get_armature_extension(armature.data).is_vrm1()
        ):
            error_messages.extend(
                pgettext(
                    'Object "{name}" contains a negative value for the scale;'
                    + " VRM 1.0 does not allow negative values to be specified"
                    + " for the scale."
                ).format(name=obj.name)
                for obj in export_objects
                if obj.scale[0] < 0 or obj.scale[1] < 0 or obj.scale[2] < 0
            )

            joint_chain_bone_names_to_spring_vrm_name: dict[str, str] = {}
            for spring in get_armature_extension(armature.data).spring_bone1.springs:
                joint_bone_names: list[str] = []
                for joint in spring.joints:
                    bone_name = joint.node.bone_name
                    if bone_name and bone_name not in joint_bone_names:
                        joint_bone_names.append(bone_name)

                joint_chain_bone_names: list[str] = []
                for bone_name in joint_bone_names:
                    search_joint_chain_bone_names: list[str] = []
                    bone = armature.data.bones.get(bone_name)
                    terminated = False
                    while bone:
                        if bone.name != bone_name and bone.name in joint_bone_names:
                            terminated = True
                            break
                        search_joint_chain_bone_names.append(bone.name)
                        bone = bone.parent
                    if not terminated:
                        if bone_name not in joint_chain_bone_names:
                            joint_chain_bone_names.append(bone_name)
                        continue
                    joint_chain_bone_names.extend(search_joint_chain_bone_names)

                for joint_chain_bone_name in joint_chain_bone_names:
                    spring_vrm_name = joint_chain_bone_names_to_spring_vrm_name.get(
                        joint_chain_bone_name
                    )
                    if not spring_vrm_name:
                        joint_chain_bone_names_to_spring_vrm_name[
                            joint_chain_bone_name
                        ] = spring.vrm_name
                        continue
                    skippable_warning_messages.append(
                        pgettext(
                            'Spring "{spring_name1}" and "{spring_name2}" have'
                            + ' common bone "{bone_name}".'
                        ).format(
                            spring_name1=spring_vrm_name,
                            spring_name2=spring.vrm_name,
                            bone_name=joint_chain_bone_name,
                        )
                    )

        used_materials = search.export_materials(context, export_objects)
        used_images: list[Image] = []
        bones_name = []
        if armature is not None and isinstance(armature.data, Armature):
            bones_name = [b.name for b in armature.data.bones]
        vertex_error_count = 0

        for mesh in [obj for obj in export_objects if obj.type == "MESH"]:
            if not isinstance(mesh.data, Mesh):
                continue

            mesh_vertex_group_names = [g.name for g in mesh.vertex_groups]

            for v in mesh.data.vertices:
                if not v.groups and mesh.parent_bone == "":
                    if vertex_error_count > 5:
                        continue
                    if (
                        armature is not None
                        and isinstance(armature.data, Armature)
                        and get_armature_extension(armature.data).is_vrm1()
                    ):
                        continue
                    info_messages.append(
                        pgettext(
                            'vertex index "{vertex_index}" is no weight'
                            + ' in "{mesh_name}".'
                            + " Add weight to parent bone automatically."
                        ).format(vertex_index=v.index, mesh_name=mesh.name)
                    )
                    vertex_error_count = vertex_error_count + 1
                elif len(v.groups) >= 5 and armature is not None:
                    weight_count = 0
                    for g in v.groups:
                        if (
                            0 <= g.group < len(mesh_vertex_group_names)
                            and mesh_vertex_group_names[g.group] in bones_name
                            and g.weight < float_info.epsilon
                        ):
                            weight_count += 1
                    if weight_count > 4 and vertex_error_count < 5:
                        info_messages.append(
                            pgettext(
                                'vertex index "{vertex_index}" has'
                                + ' too many (over 4) weight in "{mesh_name}".'
                                + " It will be truncated to 4 descending"
                                + " order by its weight."
                            ).format(vertex_index=v.index, mesh_name=mesh.name)
                        )
                        vertex_error_count = vertex_error_count + 1

        for mat in used_materials:
            if not mat.node_tree or get_material_extension(mat).mtoon1.enabled:
                continue
            for node in mat.node_tree.nodes:
                if node.type != "OUTPUT_MATERIAL":
                    continue

                links = node.inputs["Surface"].links
                if links and links[0].from_node.type == "BSDF_PRINCIPLED":
                    continue

                if links:
                    from_node = links[0].from_node
                    if from_node.type == "GROUP" and isinstance(
                        from_node, ShaderNodeGroup
                    ):
                        node_tree = from_node.node_tree
                        if (
                            node_tree
                            and node_tree.get("SHADER") in search.LEGACY_SHADER_NAMES
                        ):
                            continue

                skippable_warning_messages.append(
                    pgettext(
                        '"{material_name}" needs to enable'
                        + ' "VRM MToon Material" or connect'
                        + " Principled BSDF/MToon_unversioned/TRANSPARENT_ZWRITE"
                        + ' to "Surface" directly. Empty material will be exported.'
                    ).format(material_name=mat.name)
                )

        for node, legacy_shader_name, material in search.shader_nodes_and_materials(
            used_materials
        ):
            # MToon
            if legacy_shader_name == "MToon_unversioned":
                for texture_val in MtoonUnversioned.texture_kind_exchange_dict.values():
                    suffix = "_alpha" if texture_val == "ReceiveShadow_Texture" else ""
                    node_material_input_check(
                        node,
                        material,
                        "TEX_IMAGE",
                        texture_val + suffix,
                        error_messages,
                        used_images,
                    )
                for float_val in MtoonUnversioned.float_props_exchange_dict.values():
                    if float_val is None:
                        continue
                    node_material_input_check(
                        node, material, "VALUE", float_val, error_messages, used_images
                    )
                for k in ["_Color", "_ShadeColor", "_EmissionColor", "_OutlineColor"]:
                    node_material_input_check(
                        node,
                        material,
                        "RGB",
                        MtoonUnversioned.vector_props_exchange_dict[k],
                        error_messages,
                        used_images,
                    )
            # GLTF
            elif legacy_shader_name == "GLTF":
                for k in TEXTURE_INPUT_NAMES:
                    node_material_input_check(
                        node, material, "TEX_IMAGE", k, error_messages, used_images
                    )
                for k in VAL_INPUT_NAMES:
                    node_material_input_check(
                        node, material, "VALUE", k, error_messages, used_images
                    )
                for k in RGBA_INPUT_NAMES:
                    node_material_input_check(
                        node, material, "RGB", k, error_messages, used_images
                    )
            # Transparent_Zwrite
            elif legacy_shader_name == "TRANSPARENT_ZWRITE":
                node_material_input_check(
                    node,
                    material,
                    "TEX_IMAGE",
                    "Main_Texture",
                    error_messages,
                    used_images,
                )

        for mat in used_materials:
            gltf = get_material_extension(mat).mtoon1
            if not gltf.enabled:
                continue

            for texture in gltf.all_textures(
                downgrade_to_mtoon0=(
                    armature is None
                    or not isinstance(armature.data, Armature)
                    or get_armature_extension(armature.data).is_vrm0()
                )
            ):
                source = texture.get_connected_node_image()
                if not source:
                    continue
                if source not in used_images:
                    used_images.append(source)
                if source.colorspace_settings.name == texture.colorspace:
                    continue
                skippable_warning_messages.append(
                    pgettext(
                        'It is recommended to set "{colorspace}"'
                        + ' to "{input_colorspace}" for "{texture_label}"'
                        + ' in Material "{name}"'
                    ).format(
                        name=mat.name,
                        texture_label=source.name,
                        colorspace=pgettext(texture.colorspace),
                        input_colorspace=pgettext("Input Color Space"),
                    )
                )

            for texture_info in gltf.all_texture_info():
                source = texture_info.index.get_connected_node_image()
                if source and source not in used_images:
                    used_images.append(source)

                if (
                    armature is None
                    or not isinstance(armature.data, Armature)
                    or not get_armature_extension(armature.data).is_vrm0()
                    or not source
                ):
                    continue

                base_color_texture = gltf.pbr_metallic_roughness.base_color_texture
                base_extensions = base_color_texture.extensions
                base_scale = base_extensions.khr_texture_transform.scale
                base_offset = base_extensions.khr_texture_transform.offset
                scale = texture_info.extensions.khr_texture_transform.scale
                offset = texture_info.extensions.khr_texture_transform.offset
                if texture_info == gltf.extensions.vrmc_materials_mtoon.matcap_texture:
                    if (
                        abs(scale[0] - 1) > 0
                        or abs(scale[1] - 1) > 0
                        or abs(offset[0]) > 0
                        or abs(offset[1]) > 0
                    ):
                        skippable_warning_messages.append(
                            pgettext(
                                'Material "{name}" {texture}\'s Offset and Scale are'
                                + " ignored in VRM 0.0"
                            ).format(
                                name=mat.name,
                                texture=texture_info.index.label,
                            )
                        )
                elif (
                    abs(base_scale[0] - scale[0]) > 0
                    or abs(base_scale[1] - scale[1]) > 0
                    or abs(base_offset[0] - offset[0]) > 0
                    or abs(base_offset[1] - offset[1]) > 0
                ):
                    skippable_warning_messages.append(
                        pgettext(
                            'Material "{name}" {texture}\'s Offset and Scale'
                            + " in VRM 0.0 are the values of"
                            + " the Lit Color Texture"
                        ).format(
                            name=mat.name,
                            texture=texture_info.index.label,
                        )
                    )

        if (
            armature is not None
            and isinstance(armature.data, Armature)
            and get_armature_extension(armature.data).is_vrm0()
        ):
            # first_person
            first_person = get_armature_extension(armature.data).vrm0.first_person
            if not first_person.first_person_bone.bone_name:
                info_messages.append(
                    pgettext(
                        "firstPersonBone is not found. "
                        + 'Set VRM HumanBone "head" instead automatically.'
                    )
                )

            # blend_shape_master
            # TODO: material value and material existence
            blend_shape_master = get_armature_extension(
                armature.data
            ).vrm0.blend_shape_master
            for blend_shape_group in blend_shape_master.blend_shape_groups:
                for bind in blend_shape_group.binds:
                    mesh_object_name = bind.mesh.mesh_object_name
                    if not bind.index or not mesh_object_name:
                        continue
                    mesh_object = next(
                        iter(
                            obj
                            for obj in export_objects
                            if obj.name == mesh_object_name
                        ),
                        None,
                    )
                    if (
                        not mesh_object
                        and mesh_object_name in context.blend_data.objects
                    ):
                        info_messages.append(
                            pgettext(
                                'A mesh named "{mesh_name}" is assigned to a blend'
                                + ' shape group named "{blend_shape_group_name}" but'
                                + " the mesh will not be exported"
                            ).format(
                                blend_shape_group_name=blend_shape_group.name,
                                mesh_name=mesh_object_name,
                            )
                        )
                    if not mesh_object:
                        continue
                    mesh_data = mesh_object.data
                    if not isinstance(mesh_data, Mesh):
                        continue
                    shape_keys = mesh_data.shape_keys
                    if not shape_keys or bind.index not in shape_keys.key_blocks:
                        info_messages.append(
                            pgettext(
                                'A shape key named "{shape_key_name}" in a mesh'
                                + ' named "{mesh_name}" is assigned to a blend shape'
                                + ' group named "{blend_shape_group_name}" but the'
                                + " shape key doesn't exist."
                            ).format(
                                mesh_name=mesh_object.name,
                                shape_key_name=bind.index,
                                blend_shape_group_name=blend_shape_group.name,
                            )
                        )

        error_messages.extend(
            pgettext(
                '"{image_name}" is not found in file path "{image_filepath}". '
                + "please load file of it in Blender."
            ).format(image_name=image.name, image_filepath=image.filepath_from_user())
            for image in used_images
            if (
                image.source == "FILE"
                and not image.is_dirty
                and image.packed_file is None
                and not Path(image.filepath_from_user()).exists()
            )
        )

        error_collection.clear()

        for message in error_messages:
            error = error_collection.add()
            error.name = f"VrmModelError{len(error_collection)}"
            error.severity = 0
            error.message = message

        for message in warning_messages:
            error = error_collection.add()
            error.name = f"VrmModelError{len(error_collection)}"
            error.severity = 1
            error.message = message

        for message in skippable_warning_messages:
            error = error_collection.add()
            error.name = f"VrmModelError{len(error_collection)}"
            error.severity = 2
            error.message = message

        for message in info_messages:
            error = error_collection.add()
            error.name = f"VrmModelError{len(error_collection)}"
            error.severity = 3
            error.message = message

    @staticmethod
    def draw_errors(
        layout: UILayout,
        error_collection: CollectionPropertyProtocol[VrmValidationError],
        *,
        show_successful_message: bool,
    ) -> None:
        error_errors: list[VrmValidationError] = []
        warning_errors: list[VrmValidationError] = []
        info_errors: list[VrmValidationError] = []

        for error in error_collection:
            if error.severity == 0:
                error_errors.append(error)
            elif error.severity <= 2:
                warning_errors.append(error)
            else:
                info_errors.append(error)

        if not error_errors and warning_errors:
            row = layout.row()
            row.emboss = "NONE"
            row.box().label(
                text=pgettext(
                    "No error. But there're {warning_count} warning(s)."
                    + " The output may not be what you expected."
                ).format(
                    warning_count=len(warning_errors),
                ),
                translate=False,
            )
        elif not error_errors and show_successful_message:
            row = layout.row()
            row.emboss = "NONE"
            row.box().label(text="No error. Ready for export VRM")

        if error_errors:
            layout.label(text="Error", icon="ERROR")
            column = layout.column(align=True)
            for error in error_errors:
                column.prop(
                    error,
                    "message",
                    text="",
                    translate=False,
                )

        if warning_errors:
            layout.label(text="Warning", icon="CANCEL")
            column = layout.column(align=True)
            for error in warning_errors:
                column.prop(
                    error,
                    "message",
                    text="",
                    translate=False,
                )

        if info_errors:
            layout.label(text="Info", icon="INFO")
            column = layout.column(align=True)
            for error in info_errors:
                column.prop(
                    error,
                    "message",
                    text="",
                    translate=False,
                )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        show_successful_message: bool  # type: ignore[no-redef]
        errors: CollectionPropertyProtocol[  # type: ignore[no-redef]
            VrmValidationError
        ]
        armature_object_name: str  # type: ignore[no-redef]


def node_material_input_check(
    node: ShaderNodeGroup,
    material: Material,
    expect_node_type: str,
    shader_val: str,
    messages: list[str],
    used_images: list[Image],
) -> None:
    # Support models that were loaded by earlier versions (1.3.5 or earlier), which had
    # this typo
    #
    # Those models have node.inputs["NomalmapTexture"] instead of "NormalmapTexture".
    # But 'shader_val', which is come from MaterialMtoon.texture_kind_exchange_dict,
    # can be "NormalmapTexture". if script reference node.inputs["NormalmapTexture"] in
    # that situation, it will occur error. So change it to "NomalmapTexture" which is
    # typo but points to the same thing in those models.
    if (
        shader_val == "NormalmapTexture"
        and "NormalmapTexture" not in node.inputs.keys()
    ):
        shader_val = "NomalmapTexture"

    if node.inputs[shader_val].links:
        n = node.inputs[shader_val].links[0].from_node
        if n.type != expect_node_type:
            messages.append(
                pgettext(
                    'need "{expect_node_type}" input'
                    + ' in "{shader_val}" of "{material_name}"',
                ).format(
                    expect_node_type=expect_node_type,
                    shader_val=shader_val,
                    material_name=material.name,
                )
            )
        elif expect_node_type == "TEX_IMAGE" and isinstance(n, ShaderNodeTexImage):
            if n.image is not None:
                if n.image not in used_images:
                    used_images.append(n.image)
            else:
                messages.append(
                    pgettext(
                        'image in material "{material_name}" is not put.'
                        + " Please set image.",
                    ).format(material_name=material.name)
                )
