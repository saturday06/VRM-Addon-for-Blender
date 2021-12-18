import contextlib
import json
import os
from collections import OrderedDict
from sys import float_info
from typing import Any, Dict, List, Optional, Set, Union, cast

import bpy
from bpy.app.translations import pgettext
from mathutils import Vector

from ..common import deep, vrm_types
from ..common.preferences import get_preferences
from ..common.vrm_types import Gltf
from . import search


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
            context, self.errors, self.show_successful_message
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
            context, self.errors, self.show_successful_message
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
                for humanoid_name in vrm_types.HumanBones.requires:
                    if humanoid_name in armature.data and armature.data[
                        humanoid_name
                    ] in [bone.name for bone in armature.data.bones]:
                        continue
                    messages.append(
                        pgettext(
                            'Required VRM HumanBone "{humanoid_name}" is not defined or bone is not found. '
                            + 'Fix armature "object" custom property.',
                        ).format(humanoid_name=humanoid_name)
                    )

                for humanoid_name in vrm_types.HumanBones.defines:
                    if humanoid_name not in armature.data:
                        continue
                    node_name = armature.data[humanoid_name]
                    if not node_name or node_name in [
                        bone.name for bone in armature.data.bones
                    ]:
                        continue
                    warning_messages.append(
                        pgettext(
                            'Bone name "{node_name}" as VRM HumanBone "{humanoid_name}" is not found. '
                            + 'Fix armature "object" custom property.',
                        ).format(node_name=node_name, humanoid_name=humanoid_name)
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
                for (
                    texture_val
                ) in vrm_types.MaterialMtoon.texture_kind_exchange_dic.values():
                    if texture_val == "ReceiveShadow_Texture":
                        texture_val += "_alpha"
                    node_material_input_check(
                        node, material, "TEX_IMAGE", texture_val, messages, used_images
                    )
                for (
                    float_val
                ) in vrm_types.MaterialMtoon.float_props_exchange_dic.values():
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
                        vrm_types.MaterialMtoon.vector_props_exchange_dic[k],
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
        # thumbnail
        if armature is not None and "texture" in armature:
            try:
                if armature["texture"] in bpy.data.images:
                    image = bpy.data.images[armature["texture"]]
                    if image not in used_images:
                        used_images.append(image)
                else:
                    messages.append(
                        pgettext(
                            'VRM thumbnail image is missing. Please load "{thumbnail}"'
                        ).format(thumbnail=armature["texture"])
                    )

            except Exception:
                messages.append(
                    pgettext(
                        'VRM thumbnail image is missing. Please load "{thumbnail}"'
                    ).format(thumbnail=armature["texture"])
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
            # region vrm metas check
            enum_vrm_metas = {  # care about order 0 : that must be SAFE SELECTION (for auto set custom properties )
                "allowedUserName": [
                    "OnlyAuthor",
                    "ExplicitlyLicensedPerson",
                    "Everyone",
                ],
                "violentUssageName": ["Disallow", "Allow"],
                "sexualUssageName": ["Disallow", "Allow"],
                "commercialUssageName": ["Disallow", "Allow"],
                "licenseName": [
                    "Redistribution_Prohibited",
                    "CC0",
                    "CC_BY",
                    "CC_BY_NC",
                    "CC_BY_SA",
                    "CC_BY_NC_SA",
                    "CC_BY_ND",
                    "CC_BY_NC_ND",
                    "Other",
                ],
            }
            for k, v in enum_vrm_metas.items():
                if armature.get(k) is not None and armature.get(k) not in v:
                    messages.append(
                        pgettext(
                            '"{meta_key}" value must be in "{meta_values}". Value is "{current_meta_value}"',
                        ).format(
                            meta_key=k,
                            meta_values=v,
                            current_meta_value=armature.get(k),
                        )
                    )

            # region textblock_validate

            def text_block_name_to_json(
                textblock_name: str,
            ) -> Union[List[Any], Dict[str, Any], int, float, bool, str, None]:
                if armature is None:
                    return None
                if textblock_name not in armature:
                    warning_messages.append(
                        pgettext(
                            'textblock name "{textblock_name}" isn\'t put on armature custom property.',
                        ).format(textblock_name=textblock_name)
                    )
                    return None
                text_key = armature[textblock_name]
                text_found = False
                with contextlib.suppress(TypeError):
                    text_found = text_key in bpy.data.texts
                if not text_found:
                    warning_messages.append(
                        pgettext(
                            'textblock name "{textblock_name}" doesn\'t exist.'
                        ).format(textblock_name=textblock_name)
                    )
                    return None
                try:
                    json_as_dict = json.loads(
                        "".join([line.body for line in bpy.data.texts[text_key].lines]),
                        object_pairs_hook=OrderedDict,
                    )
                except json.JSONDecodeError as e:
                    warning_messages.append(
                        pgettext(
                            'Cannot load textblock of "{textblock_name}" as Json at line {error_lineno}. '
                            + "please check json grammar."
                        ).format(textblock_name=textblock_name, error_lineno=e.lineno)
                    )
                    json_as_dict = None
                return deep.make_return_value(json_as_dict)

            mesh_name_to_mesh = {
                **{obj.name: obj.data for obj in export_objects if obj.type == "MESH"},
                **{
                    obj.data.name: obj.data
                    for obj in export_objects
                    if obj.type == "MESH"
                },
            }
            # region humanoid_parameter
            text_block_name_to_json("humanoid_params")
            # endregion humanoid_parameter
            # region first_person
            first_person_params_name = "firstPerson_params"
            first_person_params = text_block_name_to_json(first_person_params_name)
            if isinstance(first_person_params, dict):
                fp_bone = deep.get(first_person_params, ["firstPersonBone"], -1)
                if (
                    fp_bone != -1
                    and first_person_params["firstPersonBone"]
                    not in armature.data.bones
                ):
                    warning_messages.append(
                        pgettext(
                            'firstPersonBone "{bone_name}" is not found. '
                            + 'Please fix in textblock "{first_person_params_name}". '
                            + 'Set VRM HumanBone "head" instead automatically.'
                        ).format(
                            bone_name=first_person_params["firstPersonBone"],
                            first_person_params_name=first_person_params_name,
                        )
                    )
                if "meshAnnotations" in first_person_params:
                    if isinstance(first_person_params["meshAnnotations"], list):
                        for mesh_annotation in first_person_params["meshAnnotations"]:
                            if mesh_annotation["mesh"] not in mesh_name_to_mesh:
                                warning_messages.append(
                                    pgettext(
                                        'mesh "{mesh_name}" is not found. '
                                        + 'Please fix setting in textblock "{first_person_params_name}"',
                                    ).format(
                                        mesh_name=mesh_annotation["mesh"],
                                        first_person_params_name=first_person_params_name,
                                    )
                                )
                    else:
                        warning_messages.append(
                            pgettext(
                                'meshAnnotations in textblock "{first_person_params_name}" must be list.'
                            ).format(first_person_params_name=first_person_params_name)
                        )
                if "lookAtTypeName" in first_person_params and first_person_params[
                    "lookAtTypeName"
                ] not in [
                    "Bone",
                    "BlendShape",
                ]:
                    messages.append(
                        pgettext(
                            'lookAtTypeName is "Bone" or "BlendShape". '
                            + 'Current "{look_at_type_name}". '
                            + 'Please fix setting in textblock "{first_person_params_name}"'
                        ).format(
                            look_at_type_name=first_person_params["lookAtTypeName"],
                            first_person_params_name=first_person_params_name,
                        )
                    )
            # endregion first_person

            # region blend_shape_master
            blend_shape_group_name = "blendshape_group"
            blend_shape_groups = text_block_name_to_json(blend_shape_group_name)
            if not isinstance(blend_shape_groups, list):
                blend_shape_groups = []
            # TODO material value and material existence
            for blend_shape_group in blend_shape_groups:
                for bind_dic in blend_shape_group.get("binds", []):
                    if bind_dic["mesh"] not in mesh_name_to_mesh:
                        warning_messages.append(
                            pgettext(
                                'mesh "{mesh_name}" is not found. '
                                + 'Please fix setting in textblock "{blend_shape_group_name}"',
                            ).format(
                                mesh_name=bind_dic["mesh"],
                                blend_shape_group_name=blend_shape_group_name,
                            )
                        )
                    else:
                        shape_keys = mesh_name_to_mesh[bind_dic["mesh"]].shape_keys
                        if shape_keys is None:
                            warning_messages.append(
                                pgettext(
                                    'mesh "{mesh_name}" doesn\'t have shapekey. '
                                    + "But blend shape group needs it. "
                                    + 'Please fix setting in textblock "{blend_shape_group_name}"',
                                ).format(
                                    mesh_name=bind_dic["mesh"],
                                    blend_shape_group_name=blend_shape_group_name,
                                )
                            )
                        else:
                            if bind_dic["index"] not in shape_keys.key_blocks:
                                warning_messages.append(
                                    pgettext(
                                        'mesh "{mesh_name}" doesn\'t have "{bind_dic[\'index\']}" shapekey. '
                                        + "But blend shape group needs it. "
                                        + 'Please fix setting in textblock "{blend_shape_group_name}"',
                                    ).format(
                                        mesh_name=bind_dic["mesh"],
                                        blend_shape_group_name=blend_shape_group_name,
                                    )
                                )
                            if bind_dic["weight"] > 1 or bind_dic["weight"] < 0:
                                warning_messages.append(
                                    pgettext(
                                        'mesh "{mesh_name}:shapekey:{shapekey_name}:value" '
                                        + "needs between 0 and 1."
                                        + 'Please fix setting in textblock "{blend_shape_group_name}"',
                                    ).format(
                                        mesh_name=bind_dic["mesh"],
                                        shapekey_name=bind_dic["index"],
                                        blend_shape_group_name=blend_shape_group_name,
                                    )
                                )

            # endregion blend_shape_master

            # region springbone
            spring_bonegroup_list = text_block_name_to_json("spring_bone")
            bone_names_list = [bone.name for bone in armature.data.bones]
            if not isinstance(spring_bonegroup_list, list):
                spring_bonegroup_list = []
            for bone_group in spring_bonegroup_list:
                if (
                    isinstance(bone_group.get("center"), str)
                    and bone_group["center"] not in bone_names_list
                ):
                    bone_name = bone_group["center"]
                    warning_messages.append(
                        pgettext(
                            'Center bone name "{bone_name}" is not found in spring_bone setting.',
                        ).format(bone_name=bone_name)
                    )
                for bone_name in bone_group["bones"]:
                    if bone_name not in bone_names_list:
                        warning_messages.append(
                            pgettext(
                                'Bone name "{bone_name}" is not found in spring_bone setting.',
                            ).format(bone_name=bone_name)
                        )
                for bone_name in bone_group["colliderGroups"]:
                    if bone_name not in bone_names_list:
                        warning_messages.append(
                            pgettext(
                                'Bone name "{bone_name}" is not found in spring_bone setting.'
                            ).format(bone_name=bone_name)
                        )

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
