import os
from sys import float_info
from typing import List, Optional, Set, cast

import bpy
from bpy.app.translations import pgettext
from mathutils import Vector

from ..common.gltf_constants import Gltf
from ..common.human_bone import HumanBones
from ..common.mtoon_constants import MaterialMtoon
from ..common.preferences import get_preferences
from . import migration, search


class VrmValidationError(bpy.types.PropertyGroup):  # type: ignore[misc]
    message: bpy.props.StringProperty()  # type: ignore[valid-type]
    fatal: bpy.props.BoolProperty()  # type: ignore[valid-type]


class WM_OT_vrm_validator(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.model_validate"
    bl_label = "Validate VRM model"
    bl_description = "NO Quad_Poly & N_GON, NO unSkined Mesh etc..."
    bl_options = {"REGISTER", "UNDO"}

    show_successful_message: bpy.props.BoolProperty(  # type: ignore[valid-type]
        default=True
    )
    errors: bpy.props.CollectionProperty(type=VrmValidationError)  # type: ignore[valid-type]

    def execute(self, context: bpy.types.Context) -> Set[str]:
        self.detect_errors_and_warnings(
            context, self.errors, self.show_successful_message, execute_migration=True
        )
        if any(error.fatal for error in self.errors):
            for index, error in enumerate(self.errors):
                if index > 10:
                    print("ERROR: ... truncated ...")
                    break
                if error.fatal:
                    print("ERROR: " + error.message)
            return {"CANCELLED"}
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> Set[str]:
        self.detect_errors_and_warnings(
            context, self.errors, self.show_successful_message, execute_migration=True
        )
        if (
            not any(error.fatal for error in self.errors)
            and not self.show_successful_message
        ):
            return {"FINISHED"}
        return cast(
            Set[str], context.window_manager.invoke_props_dialog(self, width=800)
        )

    def draw(self, context: bpy.types.Context) -> None:
        self.detect_errors_and_warnings(
            context, self.errors, self.show_successful_message, self.layout
        )

    @staticmethod
    def detect_errors_and_warnings(
        context: bpy.types.Context,
        error_collection: bpy.types.CollectionProperty,
        show_successful_message: bool = True,
        layout: Optional[bpy.types.UILayout] = None,
        execute_migration: bool = False,
    ) -> None:
        messages = []
        warning_messages = []
        print("validation start")
        armature_count = 0
        armature: Optional[bpy.types.Object] = None
        node_names = []

        # region export object seeking
        export_invisibles = False
        export_only_selections = False
        preferences = get_preferences(context)
        if preferences:
            export_invisibles = bool(preferences.export_invisibles)
            export_only_selections = bool(preferences.export_only_selections)
        export_objects = search.export_objects(
            export_invisibles, export_only_selections
        )

        for obj in export_objects:
            if obj.type not in ["ARMATURE", "EMPTY"]:
                if obj.name in node_names:
                    messages.append(
                        pgettext(
                            "Nodes(mesh,bones) require unique names for VRM export. {name} is duplicated."
                        ).format(name=obj.name)
                    )
                if obj.name not in node_names:
                    node_names.append(obj.name)
            if (
                obj.type == "MESH"
                and obj.parent is not None
                and obj.parent.type != "ARMATURE"
                and obj.location != Vector([0.0, 0.0, 0.0])
            ):  # mesh and armature origin is on [0,0,0]
                warning_messages.append(
                    pgettext('There are not an object on the origin "{name}"').format(
                        name=obj.name
                    )
                )
            if obj.type == "ARMATURE":
                armature = obj
                if execute_migration:
                    migration.migrate(armature, defer=False)
                armature_count += 1
                if armature_count >= 2:  # only one armature
                    messages.append(
                        pgettext(
                            "Only one armature is required for VRM export. Multiple armatures found."
                        )
                    )
                for bone in obj.data.bones:
                    if bone.name in node_names:  # nodes name is unique
                        messages.append(
                            pgettext(
                                "Nodes(mesh,bones) require unique names for VRM export. {name} is duplicated.",
                            ).format(name=obj.name)
                        )
                    if bone.name not in node_names:
                        node_names.append(bone.name)
                # TODO: T_POSE,
                human_bones_props = (
                    armature.data.vrm_addon_extension.vrm0.humanoid.human_bones
                )
                for humanoid_name in HumanBones.vrm0_required_names:
                    if any(
                        human_bone_props.bone == humanoid_name
                        and human_bone_props.node
                        and human_bone_props.node.value
                        and human_bone_props.node.value in armature.data.bones
                        for human_bone_props in human_bones_props
                    ):
                        continue
                    messages.append(
                        pgettext(
                            'Required VRM HumanBone "{humanoid_name}" is not defined or bone is not found.'
                        ).format(humanoid_name=humanoid_name)
                    )

            if obj.type == "MESH":
                for poly in obj.data.polygons:
                    if poly.loop_total > 3:  # polygons need all triangle
                        warning_messages.append(
                            pgettext(
                                'Faces must be Triangle, but not face in "{name}" or '
                                + "it will be triangulated automatically.",
                            ).format(name=obj.name)
                        )
                        break

                # TODO modifier applied, vertex weight Bone exist, vertex weight numbers.
        # endregion export object seeking
        if armature_count == 0:
            warning_messages.append(pgettext("Please add ARMATURE to selections"))

        used_images: List[bpy.types.Image] = []
        used_materials = []
        bones_name = []
        if armature is not None:
            bones_name = [b.name for b in armature.data.bones]
        vertex_error_count = 0
        for mesh in [obj for obj in export_objects if obj.type == "MESH"]:
            mesh_vertex_group_names = [g.name for g in mesh.vertex_groups]
            for mat in mesh.data.materials:
                if mat not in used_materials:
                    used_materials.append(mat)

            for v in mesh.data.vertices:
                if len(v.groups) == 0 and mesh.parent_bone == "":
                    if vertex_error_count > 5:
                        continue
                    warning_messages.append(
                        pgettext(
                            'vertex index "{vertex_index}" is no weight in "{mesh_name}". '
                            + 'Add weight to VRM HumanBone "hips" automatically.'
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
                        warning_messages.append(
                            pgettext(
                                'vertex index "{vertex_index}" has too many(over 4) weight in "{mesh_name}". '
                                + "It will be truncated to 4 descending order by its weight."
                            ).format(vertex_index=v.index, mesh_name=mesh.name)
                        )
                        vertex_error_count = vertex_error_count + 1
        if bpy.app.version < (2, 83):
            for mat in used_materials:
                for node in mat.node_tree.nodes:
                    if node.type == "OUTPUT_MATERIAL" and (
                        not node.inputs["Surface"].links
                        or node.inputs["Surface"].links[0].from_node.type != "GROUP"
                        or node.inputs["Surface"]
                        .links[0]
                        .from_node.node_tree.get("SHADER")
                        is None
                    ):
                        groups = [
                            "GLTF",
                            "MToon_unversioned",
                            "TRANSPARENT_ZWRITE",
                        ]
                        if (
                            bpy.app.translations
                            and bpy.app.translations.locale == "ja_JP"
                        ):
                            groups_str = "".join(f"「{group}」" for group in groups)
                        else:
                            groups_str = "/".join(groups)
                        warning_messages.append(
                            pgettext(
                                '"{material_name}" needs to connect {groups} to "Surface" directly. '
                                + "Empty material will be exported."
                            ).format(material_name=mat.name, groups=groups_str)
                        )

        for node, material in search.shader_nodes_and_materials(used_materials):
            # MToon
            if node.node_tree["SHADER"] == "MToon_unversioned":
                for texture_val in MaterialMtoon.texture_kind_exchange_dic.values():
                    if texture_val == "ReceiveShadow_Texture":
                        texture_val += "_alpha"
                    node_material_input_check(
                        node, material, "TEX_IMAGE", texture_val, messages, used_images
                    )
                for float_val in MaterialMtoon.float_props_exchange_dic.values():
                    if float_val is None:
                        continue
                    node_material_input_check(
                        node, material, "VALUE", float_val, messages, used_images
                    )
                for k in ["_Color", "_ShadeColor", "_EmissionColor", "_OutlineColor"]:
                    node_material_input_check(
                        node,
                        material,
                        "RGB",
                        MaterialMtoon.vector_props_exchange_dic[k],
                        messages,
                        used_images,
                    )
            # GLTF
            elif node.node_tree["SHADER"] == "GLTF":
                for k in Gltf.TEXTURE_INPUT_NAMES:
                    node_material_input_check(
                        node, material, "TEX_IMAGE", k, messages, used_images
                    )
                for k in Gltf.VAL_INPUT_NAMES:
                    node_material_input_check(
                        node, material, "VALUE", k, messages, used_images
                    )
                for k in Gltf.RGBA_INPUT_NAMES:
                    node_material_input_check(
                        node, material, "RGB", k, messages, used_images
                    )
            # Transparent_Zwrite
            elif node.node_tree["SHADER"] == "TRANSPARENT_ZWRITE":
                node_material_input_check(
                    node, material, "TEX_IMAGE", "Main_Texture", messages, used_images
                )

        for image in used_images:
            if image.is_dirty or (image.packed_file is None and not image.filepath):
                messages.append(
                    pgettext('Image "{image_name}" is not saved. Please save.').format(
                        image_name=image.name
                    )
                )
                continue
            if image.packed_file is None and not os.path.exists(
                image.filepath_from_user()
            ):
                messages.append(
                    pgettext(
                        '"{image_name}" is not found in file path "{image_filepath}". '
                        + "Please load file of it in Blender."
                    ).format(
                        image_name=image.name, image_filepath=image.filepath_from_user()
                    )
                )
                continue
            if image.file_format.lower() not in ["png", "jpeg"]:
                messages.append(
                    pgettext(
                        'glTF only supports PNG and JPEG textures but "{image_name}" is "{image_file_format}"',
                    ).format(image_name=image.name, image_file_format=image.file_format)
                )

        if armature is not None:
            # region first_person
            first_person_props = armature.data.vrm_addon_extension.vrm0.first_person
            if not first_person_props.first_person_bone.value:
                warning_messages.append(
                    pgettext(
                        "firstPersonBone is not found. "
                        + 'Set VRM HumanBone "head" instead automatically.'
                    )
                )
            # endregion first_person

            # region blend_shape_master
            # TODO material value and material existence
            blend_shape_master_props = (
                armature.data.vrm_addon_extension.vrm0.blend_shape_master
            )
            for blend_shape_group_props in blend_shape_master_props.blend_shape_groups:
                for bind_props in blend_shape_group_props.binds:
                    if not bind_props.mesh or not bind_props.mesh.name:
                        continue

                    shape_keys = bind_props.mesh.shape_keys
                    if not shape_keys:
                        warning_messages.append(
                            pgettext(
                                'mesh "{mesh_name}" doesn\'t have shape key. '
                                + 'But blend shape group needs "{shape_key_name}" in its shape key.'
                            ).format(
                                mesh_name=bind_props.mesh.name,
                                shape_key_name=bind_props.index,
                            )
                        )
                        continue

                    if bind_props.index not in shape_keys.key_blocks:
                        warning_messages.append(
                            pgettext(
                                'mesh "{mesh_name}" doesn\'t have "{shape_key_name}" shape key. '
                                + "But blend shape group needs it."
                            ).format(
                                mesh_name=bind_props.mesh.name,
                                shape_key_name=bind_props.index,
                            )
                        )
            # endregion blend_shape_master

        # endregion vrm metas check

        print("validation finished")

        error_collection.clear()

        errors = []
        warnings = []
        for index, message in enumerate(messages):
            error = error_collection.add()
            error.name = f"VrmModelError{index}"
            error.fatal = True
            error.message = message
            errors.append(error)
        for index, message in enumerate(warning_messages):
            warning = error_collection.add()
            warning.name = f"VrmModelWarning{index}"
            warning.fatal = False
            warning.message = message
            warnings.append(warning)

        if layout is None:
            return
        if not errors and show_successful_message:
            layout.label(text="No error. Ready for export VRM")
        if errors:
            layout.label(text="Error", icon="ERROR")
            for error in errors:
                layout.prop(
                    error,
                    "message",
                    text="",
                    translate=False,
                )
        if warnings:
            layout.label(text="Info", icon="INFO")
            for warning in warnings:
                layout.prop(
                    warning,
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
    # But 'shader_val', which is come from MaterialMtoon.texture_kind_exchange_dic, can be "NormalmapTexture".
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
