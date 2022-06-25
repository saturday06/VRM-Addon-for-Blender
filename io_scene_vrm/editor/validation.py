import os
from sys import float_info
from typing import List, Optional, Set, cast

import bpy
from bpy.app.translations import pgettext
from mathutils import Vector

from ..common import gltf, version
from ..common.human_bone import HumanBoneSpecifications
from ..common.mtoon_constants import MaterialMtoon
from ..common.preferences import get_preferences
from . import migration, search


class VrmValidationError(bpy.types.PropertyGroup):  # type: ignore[misc]
    message: bpy.props.StringProperty()  # type: ignore[valid-type]
    severity: bpy.props.IntProperty(min=0)  # type: ignore[valid-type]


class WM_OT_vrm_validator(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.model_validate"
    bl_label = "Validate VRM Model"
    bl_description = "NO Quad_Poly & N_GON, NO unSkined Mesh etc..."
    bl_options = {"REGISTER", "UNDO"}

    show_successful_message: bpy.props.BoolProperty(  # type: ignore[valid-type]
        default=True
    )
    errors: bpy.props.CollectionProperty(type=VrmValidationError)  # type: ignore[valid-type]

    def execute(self, context: bpy.types.Context) -> Set[str]:
        self.detect_errors(
            context,
            self.errors,
            execute_migration=True,
            readonly=False,
        )
        fatal_error_count = 0
        for error in self.errors:
            if fatal_error_count > 10:
                print("ERROR: ... truncated ...")
                break
            if error.severity == 0:
                print("ERROR: " + error.message)
                fatal_error_count += 1
        if fatal_error_count > 0:
            return {"CANCELLED"}
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> Set[str]:
        self.detect_errors(
            context,
            self.errors,
            execute_migration=True,
            readonly=False,
        )
        if (
            not any(error.severity == 0 for error in self.errors)
            and not self.show_successful_message
        ):
            return {"FINISHED"}
        return cast(
            Set[str], context.window_manager.invoke_props_dialog(self, width=800)
        )

    def draw(self, _context: bpy.types.Context) -> None:
        self.draw_errors(self.errors, self.show_successful_message, self.layout)

    @staticmethod
    def validate_bone_order(
        messages: List[str],
        armature: bpy.types.Object,
        readonly: bool,
    ) -> None:
        humanoid = armature.data.vrm_addon_extension.vrm0.humanoid
        humanoid.check_last_bone_names_and_update(armature.data.name, defer=readonly)
        for human_bone in humanoid.human_bones:
            if (
                not human_bone.node.value
                or human_bone.node.value in human_bone.node_candidates
            ):
                continue
            messages.append(
                pgettext(
                    'Couldn\'t assign the "{bone}" bone to a VRM "{human_bone}". '
                    + 'Please confirm "VRM" Panel → "VRM 0.x Humanoid" → {human_bone}.'
                ).format(
                    bone=human_bone.node.value,
                    human_bone=human_bone.specification().title,
                )
            )
            break

    @staticmethod
    def detect_errors(
        context: bpy.types.Context,
        error_collection: bpy.types.CollectionProperty,
        execute_migration: bool = False,
        readonly: bool = True,
    ) -> None:
        error_messages = []
        warning_messages = []
        info_messages = []
        armature_count = 0
        armature: Optional[bpy.types.Object] = None
        node_names = []

        # region export object seeking
        export_invisibles = False
        export_only_selections = False
        export_fb_ngon_encoding = False
        preferences = get_preferences(context)
        if preferences:
            export_invisibles = bool(preferences.export_invisibles)
            export_only_selections = bool(preferences.export_only_selections)
            export_fb_ngon_encoding = bool(preferences.export_fb_ngon_encoding)

        if not version.supported():
            warning_messages.append(
                pgettext(
                    "The installed VRM add-on is not compatible with Blender {blender_version}. "
                    + " The VRM may not be exported correctly."
                ).format(blender_version=".".join(map(str, bpy.app.version)))
            )

        if export_fb_ngon_encoding:
            warning_messages.append(
                pgettext(
                    "The FB_ngon_encoding extension under development will be used. "
                    + "The exported mesh may be corrupted."
                )
            )

        export_objects = search.export_objects(
            export_invisibles, export_only_selections
        )

        for obj in export_objects:
            if obj.type in search.MESH_CONVERTIBLE_OBJECT_TYPES:
                if obj.name in node_names:
                    error_messages.append(
                        pgettext(
                            "Nodes(mesh,bones) require unique names for VRM export. {name} is duplicated."
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
                    pgettext('There are not an object on the origin "{name}"').format(
                        name=obj.name
                    )
                )
            if (
                obj.type == "MESH"
                and obj.data.shape_keys is not None
                and len(obj.data.shape_keys.key_blocks)
                >= 2  # Exclude a "Basis" shape key
                and any(map(lambda m: m.type != "ARMATURE", obj.modifiers))
            ):
                warning_messages.append(
                    pgettext(
                        'The "{name}" mesh has both a non-armature modifier and a shape key. '
                        + "However, they cannot coexist, so shape keys may not be export correctly."
                    ).format(name=obj.name)
                )
            if obj.type == "ARMATURE":
                armature = obj
                if execute_migration:
                    migration.migrate(armature.name, defer=False)
                armature_count += 1
                if armature_count >= 2:  # only one armature
                    error_messages.append(
                        pgettext(
                            "Only one armature is required for VRM export. Multiple armatures found."
                        )
                    )
                for bone in obj.data.bones:
                    if bone.name in node_names:  # nodes name is unique
                        error_messages.append(
                            pgettext(
                                "The same name cannot be used for a mesh object and a bone. "
                                + 'Rename either one whose name is "{name}".'
                            ).format(name=bone.name)
                        )
                    if bone.name not in node_names:
                        node_names.append(bone.name)

                # TODO: T_POSE,
                required_bone_error_format = (
                    'Required VRM Bone "{humanoid_name}" is not assigned. Please confirm'
                    + ' "VRM" Panel → "VRM 0.x Humanoid" → "VRM Required Bones" → "{humanoid_name}".'
                )
                if armature.data.vrm_addon_extension.is_vrm1():
                    warning_messages.append(
                        pgettext(
                            "VRM 1.0 support is under development.\n"
                            + "It won't work as intended in many situations."
                        ).replace("\n", " ")
                    )
                    human_bones = (
                        armature.data.vrm_addon_extension.vrm1.humanoid.human_bones
                    )
                    for (
                        human_bone_name,
                        human_bone,
                    ) in human_bones.human_bone_name_to_human_bone().items():
                        human_bone_specification = HumanBoneSpecifications.get(
                            human_bone_name
                        )
                        if not human_bone_specification.vrm1_requirement:
                            continue
                        if (
                            human_bone.node
                            and human_bone.node.value
                            and human_bone.node.value in armature.data.bones
                        ):
                            continue
                        error_messages.append(
                            pgettext(required_bone_error_format).format(
                                humanoid_name=human_bone_specification.title
                            )
                        )
                else:
                    humanoid = armature.data.vrm_addon_extension.vrm0.humanoid
                    human_bones = humanoid.human_bones
                    all_required_bones_exist = True
                    for humanoid_name in HumanBoneSpecifications.vrm0_required_names:
                        if any(
                            human_bone.bone == humanoid_name
                            and human_bone.node
                            and human_bone.node.value
                            and human_bone.node.value in armature.data.bones
                            for human_bone in human_bones
                        ):
                            continue
                        all_required_bones_exist = False
                        error_messages.append(
                            pgettext(required_bone_error_format).format(
                                humanoid_name=humanoid_name.capitalize()
                            )
                        )
                    if all_required_bones_exist:
                        WM_OT_vrm_validator.validate_bone_order(
                            error_messages, armature, readonly
                        )

            if obj.type == "MESH":
                for poly in obj.data.polygons:
                    if poly.loop_total > 3:  # polygons need all triangle
                        info_messages.append(
                            pgettext(
                                'Faces must be Triangle, but not face in "{name}" or '
                                + "it will be triangulated automatically.",
                            ).format(name=obj.name)
                        )
                        break

                # TODO modifier applied, vertex weight Bone exist, vertex weight numbers.
        # endregion export object seeking
        if armature_count == 0:
            info_messages.append(pgettext("Please add ARMATURE to selections"))

        used_materials = search.materials(export_objects)
        used_images: List[bpy.types.Image] = []
        bones_name = []
        if armature is not None:
            bones_name = [b.name for b in armature.data.bones]
        vertex_error_count = 0

        for mesh in [obj for obj in export_objects if obj.type == "MESH"]:
            mesh_vertex_group_names = [g.name for g in mesh.vertex_groups]

            for v in mesh.data.vertices:
                if len(v.groups) == 0 and mesh.parent_bone == "":
                    if vertex_error_count > 5:
                        continue
                    info_messages.append(
                        pgettext(
                            'vertex index "{vertex_index}" is no weight in "{mesh_name}". '
                            + "Add weight to parent bone automatically."
                        ).format(vertex_index=v.index, mesh_name=mesh.name)
                    )
                    vertex_error_count = vertex_error_count + 1
                elif len(v.groups) >= 5 and armature is not None:
                    weight_count = 0
                    for g in v.groups:
                        if (
                            mesh_vertex_group_names[g.group] in bones_name
                            and g.weight < float_info.epsilon
                        ):
                            weight_count += 1
                    if weight_count > 4 and vertex_error_count < 5:
                        info_messages.append(
                            pgettext(
                                'vertex index "{vertex_index}" has too many(over 4) weight in "{mesh_name}". '
                                + "It will be truncated to 4 descending order by its weight."
                            ).format(vertex_index=v.index, mesh_name=mesh.name)
                        )
                        vertex_error_count = vertex_error_count + 1

        for mat in used_materials:
            if not mat.node_tree:
                continue
            for node in mat.node_tree.nodes:
                if node.type != "OUTPUT_MATERIAL":
                    continue

                links = node.inputs["Surface"].links
                groups = [
                    "MToon_unversioned",
                    "GLTF",
                    "TRANSPARENT_ZWRITE",
                ]

                if links and links[0].from_node.type == "BSDF_PRINCIPLED":
                    continue

                if (
                    links
                    and links[0].from_node.type == "GROUP"
                    and links[0].from_node.node_tree.get("SHADER") in groups
                ):
                    continue

                warning_messages.append(
                    pgettext(
                        '"{material_name}" needs to connect Principled BSDF/MToon_unversioned/GLTF/TRANSPARENT_ZWRITE'
                        + ' to "Surface" directly. Empty material will be exported.'
                    ).format(material_name=mat.name)
                )

        for node, material in search.shader_nodes_and_materials(used_materials):
            # MToon
            if node.node_tree["SHADER"] == "MToon_unversioned":
                for texture_val in MaterialMtoon.texture_kind_exchange_dict.values():
                    if texture_val == "ReceiveShadow_Texture":
                        texture_val += "_alpha"
                    node_material_input_check(
                        node,
                        material,
                        "TEX_IMAGE",
                        texture_val,
                        error_messages,
                        used_images,
                    )
                for float_val in MaterialMtoon.float_props_exchange_dict.values():
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
                        MaterialMtoon.vector_props_exchange_dict[k],
                        error_messages,
                        used_images,
                    )
            # GLTF
            elif node.node_tree["SHADER"] == "GLTF":
                for k in gltf.TEXTURE_INPUT_NAMES:
                    node_material_input_check(
                        node, material, "TEX_IMAGE", k, error_messages, used_images
                    )
                for k in gltf.VAL_INPUT_NAMES:
                    node_material_input_check(
                        node, material, "VALUE", k, error_messages, used_images
                    )
                for k in gltf.RGBA_INPUT_NAMES:
                    node_material_input_check(
                        node, material, "RGB", k, error_messages, used_images
                    )
            # Transparent_Zwrite
            elif node.node_tree["SHADER"] == "TRANSPARENT_ZWRITE":
                node_material_input_check(
                    node,
                    material,
                    "TEX_IMAGE",
                    "Main_Texture",
                    error_messages,
                    used_images,
                )

        for image in used_images:
            if (
                image.source == "FILE"
                and not image.is_dirty
                and image.packed_file is None
                and not os.path.exists(image.filepath_from_user())
            ):
                error_messages.append(
                    pgettext(
                        '"{image_name}" is not found in file path "{image_filepath}". '
                        + "Please load file of it in Blender."
                    ).format(
                        image_name=image.name, image_filepath=image.filepath_from_user()
                    )
                )

        if armature is not None:
            # region first_person
            first_person = armature.data.vrm_addon_extension.vrm0.first_person
            if not first_person.first_person_bone.value:
                info_messages.append(
                    pgettext(
                        "firstPersonBone is not found. "
                        + 'Set VRM HumanBone "head" instead automatically.'
                    )
                )
            # endregion first_person

            # region blend_shape_master
            # TODO material value and material existence
            blend_shape_master = (
                armature.data.vrm_addon_extension.vrm0.blend_shape_master
            )
            for blend_shape_group in blend_shape_master.blend_shape_groups:
                for bind in blend_shape_group.binds:
                    if not bind.mesh or not bind.mesh.name:
                        continue

                    shape_keys = bind.mesh.shape_keys
                    if not shape_keys:
                        info_messages.append(
                            pgettext(
                                'mesh "{mesh_name}" doesn\'t have shape key. '
                                + 'But blend shape group needs "{shape_key_name}" in its shape key.'
                            ).format(
                                mesh_name=bind.mesh.name,
                                shape_key_name=bind.index,
                            )
                        )
                        continue

                    if bind.index not in shape_keys.key_blocks:
                        info_messages.append(
                            pgettext(
                                'mesh "{mesh_name}" doesn\'t have "{shape_key_name}" shape key. '
                                + "But blend shape group needs it."
                            ).format(
                                mesh_name=bind.mesh.name,
                                shape_key_name=bind.index,
                            )
                        )
            # endregion blend_shape_master

        # endregion vrm metas check

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

        for message in info_messages:
            error = error_collection.add()
            error.name = f"VrmModelError{len(error_collection)}"
            error.severity = 2
            error.message = message

    @staticmethod
    def draw_errors(
        error_collection: bpy.types.CollectionProperty,
        show_successful_message: bool,
        layout: bpy.types.UILayout,
    ) -> None:
        error_errors = []
        warning_errors = []
        info_errors = []

        for error in error_collection:
            if error.severity == 0:
                error_errors.append(error)
            elif error.severity == 1:
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
            column = layout.column()
            for error in error_errors:
                column.prop(
                    error,
                    "message",
                    text="",
                    translate=False,
                )

        if warning_errors:
            layout.label(text="Warning", icon="CANCEL")
            column = layout.column()
            for error in warning_errors:
                column.prop(
                    error,
                    "message",
                    text="",
                    translate=False,
                )

        if info_errors:
            layout.label(text="Info", icon="INFO")
            column = layout.column()
            for error in info_errors:
                column.prop(
                    error,
                    "message",
                    text="",
                    translate=False,
                )


def node_material_input_check(
    node: bpy.types.ShaderNodeGroup,
    material: bpy.types.Material,
    expect_node_type: str,
    shader_val: str,
    messages: List[str],
    used_images: List[bpy.types.Image],
) -> None:
    # Support models that were loaded by earlier versions (1.3.5 or earlier), which had this typo
    #
    # Those models have node.inputs["NomalmapTexture"] instead of "NormalmapTexture".  # noqa: SC100
    # But 'shader_val', which is come from MaterialMtoon.texture_kind_exchange_dict, can be "NormalmapTexture".
    # if script reference node.inputs["NormalmapTexture"] in that situation, it will occur error.
    # So change it to "NomalmapTexture" which is typo but points to the same thing  # noqa: SC100
    # in those models.
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
                    'need "{expect_node_type}" input in "{shader_val}" of "{material_name}"',
                ).format(
                    expect_node_type=expect_node_type,
                    shader_val=shader_val,
                    material_name=material.name,
                )
            )
        else:
            if expect_node_type == "TEX_IMAGE":
                if n.image is not None:
                    if n.image not in used_images:
                        used_images.append(n.image)
                else:
                    messages.append(
                        pgettext(
                            'image in material "{material_name}" is not put. Please set image.',
                        ).format(material_name=material.name)
                    )
