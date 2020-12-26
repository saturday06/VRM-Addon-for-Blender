"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
import contextlib
import json
import os
import re
from collections import OrderedDict
from sys import float_info
from typing import List

import blf
import bpy
from mathutils import Vector

from .. import vrm_types
from ..vrm_types import Gltf
from ..vrm_types import nested_json_value_getter as json_get
from .make_armature import ICYP_OT_MAKE_ARMATURE


class Bones_rename(bpy.types.Operator):  # noqa: N801
    bl_idname = "vrm.bones_rename"
    bl_label = "Rename VRoid_bones"
    bl_description = "Rename VRoid_bones as Blender type"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        def reprstr(bone_name):
            ml = re.match("(.*)_" + "L" + "_(.*)", bone_name)
            mr = re.match("(.*)_" + "R" + "_(.*)", bone_name)
            if ml or mr:
                tmp = ""
                ma = ml if ml else mr
                for y in ma.groups():
                    tmp += y + "_"
                tmp += "R" if mr else "L"
                return tmp
            return bone_name

        for x in bpy.context.active_object.data.bones:
            x.name = reprstr(x.name)
        if "spring_bone" in bpy.context.active_object:
            textblock = bpy.data.texts[bpy.context.active_object["spring_bone"]]
            j = json.loads("".join([line.body for line in textblock.lines]))
            for jdic in j:
                for i, bones in enumerate(jdic["bones"]):
                    jdic["bones"][i] = reprstr(bones)
                for i, collider in enumerate(jdic["colliderGroups"]):
                    jdic["colliderGroups"][i] = reprstr(collider)
            textblock.from_string(json.dumps(j, indent=4))
        for bonename in vrm_types.HumanBones.requires + vrm_types.HumanBones.defines:
            if bonename in bpy.context.active_object.data:
                bpy.context.active_object.data[bonename] = reprstr(
                    bpy.context.active_object.data[bonename]
                )
        return {"FINISHED"}


class Add_VRM_extensions_to_armature(bpy.types.Operator):  # noqa: N801
    bl_idname = "vrm.add_vrm_extensions"
    bl_label = "Add vrm attributes"
    bl_description = "Add vrm extensions & metas to armature"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        ICYP_OT_MAKE_ARMATURE.make_extension_setting_and_metas(context.active_object)
        return {"FINISHED"}


class Add_VRM_require_humanbone_custom_property(bpy.types.Operator):  # noqa: N801
    bl_idname = "vrm.add_vrm_req_humanbone_prop"
    bl_label = "Add vrm humanbone_prop"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        arm = bpy.data.armatures[bpy.context.active_object.data.name]
        for req in vrm_types.HumanBones.requires:
            if req not in arm:
                arm[req] = ""
        return {"FINISHED"}


class Add_VRM_defined_humanbone_custom_property(bpy.types.Operator):  # noqa: N801
    bl_idname = "vrm.add_vrm_def_humanbone_prop"
    bl_label = "Add vrm humanbone_prop"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        arm = bpy.data.armatures[bpy.context.active_object.data.name]
        for d in vrm_types.HumanBones.defines:
            if d not in arm:
                arm[d] = ""
        return {"FINISHED"}


class Vroid2VRC_lipsync_from_json_recipe(bpy.types.Operator):  # noqa: N801
    bl_idname = "vrm.lipsync_vrm"
    bl_label = "Make lipsync4VRC"
    bl_description = "Make lipsync from VRoid to VRC by json"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        recipe_uri = os.path.join(
            os.path.dirname(__file__), "vroid2vrc_lipsync_recipe.json"
        )
        recipe = None
        with open(recipe_uri, "rt") as raw_recipe:
            recipe = json.loads(raw_recipe.read(), object_pairs_hook=OrderedDict)
        for shapekey_name, based_values in recipe["shapekeys"].items():
            for k in bpy.context.active_object.data.shape_keys.key_blocks:
                k.value = 0.0
            for based_shapekey_name, based_val in based_values.items():
                # if M_F00_000+_00
                if (
                    based_shapekey_name
                    not in bpy.context.active_object.data.shape_keys.key_blocks
                ):
                    based_shapekey_name = based_shapekey_name.replace(
                        "M_F00_000", "M_F00_000_00"
                    )  # Vroid064から命名が変わった
                bpy.context.active_object.data.shape_keys.key_blocks[
                    based_shapekey_name
                ].value = based_val
            bpy.ops.object.shape_key_add(from_mix=True)
            bpy.context.active_object.data.shape_keys.key_blocks[
                -1
            ].name = shapekey_name
        for k in bpy.context.active_object.data.shape_keys.key_blocks:
            k.value = 0.0
        return {"FINISHED"}


def find_export_objects() -> List[bpy.types.Object]:
    print("Searching for VRM export objects:")
    selected_objects = list(bpy.context.selected_objects)
    if selected_objects:
        print("  Selected objects are found:")
        for selected_object in selected_objects:
            print(f"  -> {selected_object.name}")
        return selected_objects

    print("  Select all selectable objects:")
    objects = bpy.context.selectable_objects

    exclusion_types = ["LIGHT", "CAMERA"]
    export_objects = list(
        # TODO: こちらの議論の結果を参照して修正する
        # https://github.com/KhronosGroup/glTF-Blender-IO/issues/1139
        filter(lambda o: o.visible_get() and o.type not in exclusion_types, objects)
    )
    for export_object in export_objects:
        print(f"  -> {export_object.name}")

    return export_objects


class VRM_VALIDATOR(bpy.types.Operator):  # noqa: N801
    bl_idname = "vrm.model_validate"
    bl_label = "Validate VRM model"
    bl_description = "NO Quad_Poly & N_GON, NO unSkined Mesh etc..."
    bl_options = {"REGISTER", "UNDO"}

    show_successful_message: bpy.props.BoolProperty(  # type: ignore[valid-type]
        default=True
    )

    messages = List[str]

    def execute(self, context):
        messages = VRM_VALIDATOR.messages = []
        warning_messages = []
        print("validation start")
        armature_count = 0
        armature = None
        node_names = []

        # region export object seeking
        export_objects = find_export_objects()
        for obj in export_objects:
            if obj.name in node_names and obj.type != "EMPTY":
                messages.append(
                    lang_support(
                        f"Nodes(mesh,bones) require unique names for VRM export. {obj.name} is duplicated.",
                        f"glTFノード要素(メッシュ、ボーン)の名前は重複してはいけません。「{obj.name}」が重複しています。",
                    )
                )
            if obj.name not in node_names:
                node_names.append(obj.name)
            if (
                obj.type != "EMPTY"
                and obj.parent is not None
                and obj.parent.type != "ARMATURE"
                and obj.type == "MESH"
                and obj.location != Vector([0.0, 0.0, 0.0])
            ):  # mesh and armature origin is on [0,0,0]
                messages.append(
                    lang_support(
                        f'There are not an object on the origin "{obj.name}"',
                        f"「{obj.name}」が原点座標にありません",
                    )
                )
            if obj.type == "ARMATURE":
                armature = obj
                armature_count += 1
                if armature_count >= 2:  # only one armature
                    messages.append(
                        lang_support(
                            "Only one armature is required for VRM export. Multiple armatures found.",
                            "VRM出力の際、選択できるアーマチュアは1つのみです。複数選択されています。",
                        )
                    )
                for bone in obj.data.bones:
                    if bone.name in node_names:  # nodes name is unique
                        messages.append(
                            lang_support(
                                f"Nodes(mesh,bones) require unique names for VRM export. {obj.name} is duplicated.",
                                f"glTFノード要素(メッシュ、ボーン)の名前は重複してはいけません。「{obj.name}」が重複しています。",
                            )
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
                        lang_support(
                            f'Required VRM HumanBone "{humanoid_name}" is not defined or bone is not found. '
                            + 'Fix armature "object" custom property.',
                            f"必須VRMヒューマンボーン「{humanoid_name}」の属性を持つボーンがありません。"
                            + "アーマチュア「オブジェクト」のカスタムプロパティを修正してください。",
                        )
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
                        lang_support(
                            f'Bone name "{node_name}" as VRM HumanBone "{humanoid_name}" is not found. '
                            + 'Fix armature "object" custom property.',
                            f"ボーン名「{node_name}」のVRMヒューマンボーン属性「{humanoid_name}」がありません。"
                            + "アーマチュア「オブジェクト」のカスタムプロパティを修正してください。",
                        )
                    )

            if obj.type == "MESH":
                if len(obj.data.materials) == 0:
                    messages.append(
                        lang_support(
                            f'There is no material assigned to mesh "{obj.name}"',
                            f"マテリアルが1つも設定されていないメッシュ「{obj.name}」があります。",
                        )
                    )
                for poly in obj.data.polygons:
                    if poly.loop_total > 3:  # polygons need all triangle
                        warning_messages.append(
                            lang_support(
                                f'Faces must be Triangle, but not face in "{obj.name}" or '
                                + "it will be triangulated automatically.",
                                f"「{obj.name}」のポリゴンに三角形以外のものが含まれます。自動的に三角形に分割されます。",
                            )
                        )
                        break

                # TODO modifier applied, vertex weight Bone exist, vertex weight numbers.
        # endregion export object seeking
        if armature_count == 0:
            messages.append(
                lang_support("Please add ARMATURE to selections", "アーマチュアを選択範囲に含めてください")
            )

        used_images = []
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
                        lang_support(
                            f'vertex id "{v.index}" is no weight in "{mesh.name}". '
                            + 'Add weight to VRM HumanBone "hips" automatically.',
                            f"「{mesh.name}」の頂点id「{v.index}」にウェイトが乗っていません。"
                            + "VRMヒューマンボーン「hips」へのウエイトを自動で割り当てます。",
                        )
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
                            lang_support(
                                f'vertex id "{v.index}" has too many(over 4) weight in "{mesh.name}". '
                                + "It will be truncated to 4 descending order by its weight.",
                                f"「{mesh.name}」の頂点id「{v.index}」に影響を与えるボーンが5以上あります。"
                                + "重い順に4つまでエクスポートされます。",
                            )
                        )
                        vertex_error_count = vertex_error_count + 1
        for mat in used_materials:
            for node in mat.node_tree.nodes:
                if node.type == "OUTPUT_MATERIAL" and (
                    not node.inputs["Surface"].links
                    or node.inputs["Surface"].links[0].from_node.type != "GROUP"
                    or node.inputs["Surface"].links[0].from_node.node_tree.get("SHADER")
                    is None
                ):
                    groups = [
                        "GLTF",
                        "MToon_unversioned",
                        "TRANSPARENT_ZWRITE",
                    ]
                    groups_en_str = "/".join(groups)
                    groups_ja_str = "".join(f"「{group}」" for group in groups)
                    messages.append(
                        lang_support(
                            f'"{mat.name}" needs to connect {groups_en_str} to "Surface" directly.',
                            f"マテリアル「{mat.name}」は{groups_ja_str}のいずれかを直接「サーフェス」に指定してください。",
                        )
                    )

        for node, material in shader_nodes_and_materials(used_materials):
            # MToon
            if node.node_tree["SHADER"] == "MToon_unversioned":
                for (
                    shader_val
                ) in vrm_types.MaterialMtoon.texture_kind_exchange_dic.values():
                    if shader_val is None or shader_val == "ReceiveShadow_Texture":
                        continue
                    node_material_input_check(
                        node, material, "TEX_IMAGE", shader_val, messages, used_images
                    )
                for shader_val in [
                    *list(vrm_types.MaterialMtoon.float_props_exchange_dic.values()),
                    "ReceiveShadow_Texture_alpha",
                ]:
                    if shader_val is None:
                        continue
                    node_material_input_check(
                        node, material, "VALUE", shader_val, messages, used_images
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
        try:
            if armature is not None and armature.get("texture") is not None:
                thumbnail_image = bpy.data.images.get(armature["texture"])
                if thumbnail_image is not None:
                    used_images.append(thumbnail_image)
                else:
                    messages.append(
                        lang_support(
                            f"thumbnail_image is missing. Please load \"{armature['texture']}\"",
                            f"VRM用サムネイル画像がBlenderにロードされていません。「{armature['texture']}」を読み込んでください。",
                        )
                    )

        except Exception:
            messages.append(
                lang_support(
                    f"thumbnail_image is missing. Please load \"{armature['texture']}\"",
                    f"VRM用サムネイル画像がBlenderにロードされていません。「{armature['texture']}」を読み込んでください。",
                )
            )

        for image in used_images:
            if image.is_dirty or not image.filepath:
                messages.append(
                    lang_support(
                        f'"{image.name}" is not saved. Please save.',
                        f"「{image.name}」のBlender上での変更を保存してください。",
                    )
                )
            if not os.path.exists(image.filepath_from_user()):
                messages.append(
                    lang_support(
                        f'"{image.name}" is not found in file path "{image.filepath_from_user()}". '
                        + "Please load file of it in Blender.",
                        f'「{image.name}」の画像ファイルが指定ファイルパス「"{image.filepath_from_user()}"」'
                        + "に存在しません。画像を読み込み直してください。",
                    )
                )
            elif image.file_format.lower() not in ["png", "jpeg"]:
                messages.append(
                    lang_support(
                        f'glTF only supports PNG and JPEG textures but "{image.name}" is "{image.file_format}"',
                        f"glTFはPNGとJPEGのみの対応ですが「{image.name}」は「{image.file_format}」です。",
                    )
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
                        lang_support(
                            f'"{k}" value must be in "{v}". Value is "{armature.get(k)}"',
                            f"VRM権利情報の「{k}」は「{v}」のいずれかでないといけません。現在の設定値は「{armature.get(k)}」です。",
                        )
                    )

            # region textblock_validate

            def text_block_name_to_json(textblock_name):
                if textblock_name not in armature:
                    messages.append(
                        lang_support(
                            f'textblock name "{textblock_name}" isn\'t put on armature custom property.',
                            f"「{textblock_name}」のテキストブロックの指定がアーマチュアのカスタムプロパティにありません。",
                        )
                    )
                    return None
                text_key = armature[textblock_name]
                text_found = False
                with contextlib.suppress(TypeError):
                    text_found = text_key in bpy.data.texts
                if not text_found:
                    messages.append(
                        lang_support(
                            f'textblock name "{textblock_name}" doesn\'t exist.',
                            f"「{textblock_name}」のテキストがエディタ上にありません。",
                        )
                    )
                    return None
                try:
                    json_as_dict = json.loads(
                        "".join([line.body for line in bpy.data.texts[text_key].lines]),
                        object_pairs_hook=OrderedDict,
                    )
                except json.JSONDecodeError as e:
                    messages.append(
                        lang_support(
                            f'Cannot load textblock of "{textblock_name}" as Json at line {e.pos.lineno}. '
                            + "please check json grammar.",
                            f"「{textblock_name}」のJsonとしての読み込みに失敗しました。{e.pos.lineno}行目付近にエラーがあります。"
                            + "形式を確認してください。",
                        )
                    )
                    json_as_dict = None
                return json_as_dict

            def text_block_write(block_name, data_dict):
                textblock = bpy.data.texts.new(name=f"{block_name}_.json")
                textblock.write(json.dumps(data_dict, indent=4))
                return textblock

            mesh_obj_names = [obj.name for obj in export_objects if obj.type == "MESH"]
            # region humanoid_parameter
            humanoid_param_name = "humanoid_params"
            humanoid_param = text_block_name_to_json(humanoid_param_name)
            if humanoid_param is None:
                armature[humanoid_param_name] = text_block_write(
                    humanoid_param_name,
                    vrm_types.Vrm0.HUMANOID_DEFAULT_PARAMS,
                )
            # endregion humanoid_parameter
            # region first_person
            first_person_params_name = "firstPerson_params"
            firstperson_params = text_block_name_to_json(first_person_params_name)
            if firstperson_params is not None:
                fp_bone = json_get(firstperson_params, ["firstPersonBone"], -1)
                if (
                    fp_bone != -1
                    and firstperson_params["firstPersonBone"] not in armature.data.bones
                ):
                    messages.append(
                        lang_support(
                            f"firstPersonBone \"{firstperson_params['firstPersonBone']}\" is not found. "
                            + f'Please fix in textblock "{first_person_params_name}"',
                            f"firstPersonBone「{firstperson_params['firstPersonBone']}」がアーマチュアにありませんでした。"
                            + f"テキストエディタの「{first_person_params_name}」の該当項目を修正してください。",
                        )
                    )
                if "meshAnnotations" in firstperson_params.keys():
                    if isinstance(firstperson_params["meshAnnotations"], list):
                        for mesh_annotation in firstperson_params["meshAnnotations"]:
                            if mesh_annotation["mesh"] not in mesh_obj_names:
                                messages.append(
                                    lang_support(
                                        f"mesh \"{mesh_annotation['mesh']}\" is not found. "
                                        + f'Please fix setting in textblock "{first_person_params_name}"',
                                        f"「{mesh_annotation['mesh']}」というメッシュオブジェクトが見つかりません。"
                                        + f"テキストエディタの「{first_person_params_name}」を修正してください。",
                                    )
                                )
                    else:
                        messages.append(
                            lang_support(
                                f'meshAnnotations in textblock "{first_person_params_name}" must be list.',
                                f"テキストエディタの「{first_person_params_name}」のmeshAnnotationsはリスト要素でないといけません。",
                            )
                        )
                if "lookAtTypeName" in firstperson_params and firstperson_params[
                    "lookAtTypeName"
                ] not in [
                    "Bone",
                    "BlendShape",
                ]:
                    messages.append(
                        lang_support(
                            'lookAtTypeName is "Bone" or "BlendShape". '
                            + f"Current \"{firstperson_params['lookAtTypeName']}\". "
                            + f'Please fix setting in textblock "{first_person_params_name}"',
                            'lookAtTypeNameは "Bone" か "BlendShape" です。'
                            + f"今は「{firstperson_params['lookAtTypeName']}」です。"
                            + f"テキストエディタの「{first_person_params_name}」を修正してください。",
                        )
                    )
            # endregion first_person

            # region blendshape_master
            blendshape_group_name = "blendshape_group"
            blendshape_groups = text_block_name_to_json(blendshape_group_name)
            if blendshape_groups is None:
                blendshape_groups = []
            # TODO material value and material existence
            for blendshape_group in blendshape_groups:
                for bind_dic in blendshape_group["binds"]:
                    if bind_dic["mesh"] not in mesh_obj_names:
                        messages.append(
                            lang_support(
                                f"mesh \"{bind_dic['mesh']}\" is not found. "
                                + f'Please fix setting in textblock "{blendshape_group_name}"',
                                f"メッシュ「{bind_dic['mesh']}」が見つかりません。"
                                + f"テキストエディタの「{blendshape_group_name}」を修正してください。",
                            )
                        )
                    else:
                        if bpy.data.objects[bind_dic["mesh"]].data.shape_keys is None:
                            messages.append(
                                lang_support(
                                    f"mesh \"{bind_dic['mesh']}\" doesn't have shapekey. "
                                    + "But blendshape Group needs it. "
                                    + f'Please fix setting in textblock "{blendshape_group_name}"',
                                    f"メッシュ「{bind_dic['mesh']}」はシェイプキーがありません。"
                                    + "しかし blendshape Group の設定はそれを必要としています。"
                                    + f"テキストエディタの「{blendshape_group_name}」を修正してください。",
                                )
                            )
                        else:
                            if (
                                bind_dic["index"]
                                not in bpy.data.objects[
                                    bind_dic["mesh"]
                                ].data.shape_keys.key_blocks
                            ):
                                messages.append(
                                    lang_support(
                                        f"mesh \"{bind_dic['mesh']}\" doesn't have \"{bind_dic['index']}\" shapekey. "
                                        + "But blendshape Group needs it. "
                                        + f'Please fix setting in textblock "{blendshape_group_name}"',
                                        f"メッシュ「{bind_dic['mesh']}」にはシェイプキー「{bind_dic['index']}」が存在しません。"
                                        + "しかし blendshape Group の設定はそれを必要としています。"
                                        + f"テキストエディタの「{blendshape_group_name}」を修正してください。",
                                    )
                                )
                            if bind_dic["weight"] > 1 or bind_dic["weight"] < 0:
                                messages.append(
                                    lang_support(
                                        f"mesh \"{bind_dic['mesh']}:shapekey:{bind_dic['index']}:value\" "
                                        + "needs between 0 and 1."
                                        + f'Please fix setting in textblock "{blendshape_group_name}"',
                                        f"メッシュ「{bind_dic['mesh']}」のshapekey「{bind_dic['index']}」の値は0以上1以下でないといけません。"
                                        + f"テキストエディタの「{blendshape_group_name}」を修正してください。",
                                    )
                                )

            # endregion blendshape_master

            # region springbone
            spring_bonegroup_list = text_block_name_to_json("spring_bone")
            bone_names_list = [bone.name for bone in armature.data.bones]
            if spring_bonegroup_list is None:
                spring_bonegroup_list = []
            for bone_group in spring_bonegroup_list:
                for bone_name in bone_group["bones"]:
                    if bone_name not in bone_names_list:
                        messages.append(
                            lang_support(
                                f'Bone name "{bone_name}" is not found in spring_bone setting.',
                                f"spring_bone settingにある、ボーン名「{bone_name}」がアーマチュア中に見つかりません。"
                                + "テキストエディタの spring_bone の json を修正してください。",
                            )
                        )
                for bone_name in bone_group["colliderGroups"]:
                    if bone_name not in bone_names_list:
                        messages.append(
                            lang_support(
                                f'Bone name "{bone_name}" is not found in spring_bone setting.',
                                f"spring_bone settingにある、ボーン名「{bone_name}」がアーマチュア中に見つかりません。"
                                + "テキストエディタの spring_bone のjsonを修正してください。",
                            )
                        )

        # endregion vrm metas check

        print("validation finished")

        if len(messages) > 0:
            VRM_VALIDATOR.draw_func_add()
            for message in messages:
                self.report({"ERROR"}, message)
            return {"CANCELLED"}

        if self.show_successful_message:
            message = lang_support(
                "No error. Ready for export VRM",
                "エラーはありませんでした。VRMのエクスポートをすることができます",
            )
            self.report({"INFO"}, message)
            messages.append("[ " + message + " ]")
            messages.extend(warning_messages)
            VRM_VALIDATOR.draw_func_add()

        return {"FINISHED"}

    # region 3Dview drawer
    draw_func = None
    counter = 0

    @staticmethod
    def draw_func_add():
        if VRM_VALIDATOR.draw_func is not None:
            VRM_VALIDATOR.draw_func_remove()
        VRM_VALIDATOR.counter = 300
        VRM_VALIDATOR.draw_func = bpy.types.SpaceView3D.draw_handler_add(
            VRM_VALIDATOR.texts_draw, (), "WINDOW", "POST_PIXEL"
        )
        bpy.ops.wm.redraw_timer(type="DRAW", iterations=1)  # Force redraw

    @staticmethod
    def draw_func_remove():
        if VRM_VALIDATOR.draw_func is not None:
            bpy.types.SpaceView3D.draw_handler_remove(VRM_VALIDATOR.draw_func, "WINDOW")
            VRM_VALIDATOR.draw_func = None

    @staticmethod
    def texts_draw():
        text_size = 14
        dpi = 72
        blf.size(0, text_size, dpi)
        offset = 50
        for i, text in enumerate(VRM_VALIDATOR.messages):
            blf.position(0, text_size, text_size * (i + 1) + offset, 0)
            blf.draw(0, text)
        blf.position(
            0, text_size, text_size * (1 + len(VRM_VALIDATOR.messages)) + offset, 0
        )
        blf.draw(0, "[ Message delete count down: {} ]".format(VRM_VALIDATOR.counter))
        VRM_VALIDATOR.counter -= 1
        if VRM_VALIDATOR.counter <= 0 or len(VRM_VALIDATOR.messages) == 0:
            VRM_VALIDATOR.draw_func_remove()

    # endregion 3Dview drawer


def lang_support(en_message, ja_message):
    if bpy.app.translations.locale == "ja_JP":
        return ja_message
    return en_message


def node_material_input_check(
    node, material, expect_node_type, shader_val, messages, used_images
):
    if node.inputs[shader_val].links:
        n = node.inputs[shader_val].links[0].from_node
        if n.type != expect_node_type:
            messages.append(
                lang_support(
                    f'need "{expect_node_type}" input in "{shader_val}" of "{material.name}"',
                    f"「{material.name}」の「{shader_val}」には、「{expect_node_type}」を直接つないでください。 ",
                )
            )
        else:
            if expect_node_type == "TEX_IMAGE":
                if n.image is not None:
                    used_images.append(n.image)
                else:
                    messages.append(
                        lang_support(
                            f'image in material "{material.name}" is not put. Please set image.',
                            f"マテリアル「{material.name}」にテクスチャが設定されていないimageノードがあります。削除か画像を設定してください。",
                        )
                    )


def shader_nodes_and_materials(used_materials):
    return [
        (node.inputs["Surface"].links[0].from_node, mat)
        for mat in used_materials
        for node in mat.node_tree.nodes
        if node.type == "OUTPUT_MATERIAL"
        and node.inputs["Surface"].links
        and node.inputs["Surface"].links[0].from_node.type == "GROUP"
        and node.inputs["Surface"].links[0].from_node.node_tree.get("SHADER")
        is not None
    ]
