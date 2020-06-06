"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
import bpy
import blf
from .. import vrm_types
from ..vrm_types import nested_json_value_getter as json_get
from .make_armature import ICYP_OT_MAKE_ARMATURE
import re
from mathutils import Vector
import json
from collections import OrderedDict
import os


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
                bpy.context.active_object.data[bonename] = reprstr(bpy.context.active_object.data[bonename])
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


class Vroid2VRC_ripsync_from_json_recipe(bpy.types.Operator):  # noqa: N801
    bl_idname = "vrm.ripsync_vrm"
    bl_label = "Make ripsync4VRC"
    bl_description = "Make ripsync from VRoid to VRC by json"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        recipe_uri = os.path.join(os.path.dirname(__file__), "vroid2vrc_ripsync_recipe.json")
        recipe = None
        with open(recipe_uri, "rt") as raw_recipe:
            recipe = json.loads(raw_recipe.read(), object_pairs_hook=OrderedDict)
        for shapekey_name, based_values in recipe["shapekeys"].items():
            for k in bpy.context.active_object.data.shape_keys.key_blocks:
                k.value = 0.0
            for based_shapekey_name, based_val in based_values.items():
                # if M_F00_000+_00
                if based_shapekey_name not in bpy.context.active_object.data.shape_keys.key_blocks:
                    based_shapekey_name = based_shapekey_name.replace("M_F00_000", "M_F00_000_00")  # Vroid064から命名が変わった
                bpy.context.active_object.data.shape_keys.key_blocks[based_shapekey_name].value = based_val
            bpy.ops.object.shape_key_add(from_mix=True)
            bpy.context.active_object.data.shape_keys.key_blocks[-1].name = shapekey_name
        for k in bpy.context.active_object.data.shape_keys.key_blocks:
            k.value = 0.0
        return {"FINISHED"}


class VRM_VALIDATOR(bpy.types.Operator):  # noqa: N801
    bl_idname = "vrm.model_validate"
    bl_label = "Validate VRM model"
    bl_description = "NO Quad_Poly & N_GON, NO unSkined Mesh etc..."
    bl_options = {"REGISTER", "UNDO"}

    messages_set = []

    def execute(self, context):
        messages = VRM_VALIDATOR.messages_set = set()
        is_lang_ja = True if bpy.app.translations.locale == "ja_JP" else False
        print("validation start")
        armature_count = 0
        armature = None
        node_name_set = set()

        def lang_support(en_message, ja_message):
            if is_lang_ja:
                return ja_message
            else:
                return en_message

        # region selected object seeking
        for obj in bpy.context.selected_objects:
            if obj.name in node_name_set and obj.type != "EMPTY":
                messages.add(
                    lang_support(
                        f"Nodes(mesh,bones) require unique names for VRM export. {obj.name} is duplicated.",
                        f"gltfノード要素(メッシュ、ボーン)の名前は重複してはいけません。:重複:{obj.name}",
                    )
                )
            node_name_set.add(obj.name)
            if obj.type != "EMPTY" and (
                obj.parent is not None and obj.parent.type != "ARMATURE" and obj.type == "MESH"
            ):
                if obj.location != Vector([0.0, 0.0, 0.0]):  # mesh and armature origin is on [0,0,0]
                    messages.add(
                        lang_support(f"There are not an object on the origin {obj.name}", f"{obj.name} が原点座標にありません")
                    )
            if obj.type == "ARMATURE":
                armature = obj
                armature_count += 1
                if armature_count >= 2:  # only one armature
                    messages.add(
                        lang_support(
                            "Only one armature is required for VRM export. Multiple armatures found.",
                            "VRM出力の際、選択できるアーマチュアは1つのみです。複数選択されています",
                        )
                    )
                already_root_bone_exist = False
                for bone in obj.data.bones:
                    if bone.name in node_name_set:  # nodes name is unique
                        messages.add(
                            lang_support(
                                f"Nodes(mesh,bones) require unique names for VRM export. {obj.name} is duplicated.",
                                f"gltfノード要素(メッシュ、ボーン)の名前は重複してはいけません。:重複:{obj.name}",
                            )
                        )
                    node_name_set.add(bone.name)
                    if bone.parent is None:  # root bone is only 1
                        if already_root_bone_exist:
                            messages.add(
                                lang_support(
                                    "There is only one root bone."
                                    + f" {bone.name},{already_root_bone_exist} is root bone now",
                                    f"ルートボーンが複数あると出力できません。現在、{bone.name} と {already_root_bone_exist} があります。",
                                )
                            )
                        already_root_bone_exist = bone.name
                # TODO: T_POSE,
                for humanbone in vrm_types.HumanBones.requires:
                    if humanbone not in armature.data or armature.data[humanbone] not in [
                        "",
                        *[b.name for b in armature.data.bones],
                    ]:
                        armature.data[humanbone] = ""
                        messages.add(
                            lang_support(
                                f"humanBone: {humanbone} is not defined or bone is not found. "
                                + 'fix armature "object" custom property.',
                                f'必須ボーン: {humanbone} の属性を持つボーンがありません。アーマチュア "オブジェクト"のカスタムプロパティを修正してください。',
                            )
                        )
                for v in vrm_types.HumanBones.defines:
                    if v in armature.data:
                        if armature.data[v] not in [
                            "",
                            *[b.name for b in armature.data.bones],
                        ]:
                            if v in armature.data:
                                armature.data[v] = ""
                            messages.add(
                                lang_support(
                                    f"bone name: {armature.data[v]} as humanBone:{v} is not found. "
                                    + 'fix armature "object" custom property.',
                                    f'ボーン名:{armature.data[v]} (属性:{v}) がありません。アーマチュア"オブジェクト"のカスタムプロパティを修正してください。',
                                )
                            )

            if obj.type == "MESH":
                if len(obj.data.materials) == 0:
                    messages.add(
                        lang_support(
                            f"There is no material assigned to mesh {obj.name}",
                            f"マテリアルが1つも設定されていないメッシュ( {obj.name} )があります。",
                        )
                    )
                for poly in obj.data.polygons:
                    if poly.loop_total > 3:  # polygons need all triangle
                        messages.add(
                            lang_support(
                                f"Faces must be Triangle, but not face in {obj.name}",
                                f"ポリゴンはすべて3角形である必要があります。:{obj.name}",
                            )
                        )
                        break

                # TODO modifier applied, vertex weight Bone exist, vertex weight numbers.
        # endregion selected object seeking
        if armature_count == 0:
            messages.add(lang_support("PLS SELECT with ARMATURE!", "アーマチュアが選択されていません"))

        used_image = []
        used_material_set = set()
        bones_name = []
        if armature is not None:
            bones_name = [b.name for b in armature.data.bones]
        vertex_error_count = 0
        for mesh in [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]:
            mesh_vertex_group_names = [g.name for g in mesh.vertex_groups]
            for mat in mesh.data.materials:
                used_material_set.add(mat)

            for v in mesh.data.vertices:
                if len(v.groups) == 0 and mesh.parent_bone == "":
                    if vertex_error_count < 5:
                        messages.add(
                            lang_support(
                                f"vertex id {v.index} is no weight in {mesh.name}",
                                f"{mesh.name}の頂点、id:{v.index} にウェイトが乗っていません。",
                            )
                        )
                        vertex_error_count = vertex_error_count + 1
                elif len(v.groups) >= 5:
                    if armature is not None:
                        weight_count = 0
                        for g in v.groups:
                            if mesh_vertex_group_names[g.group] in bones_name:
                                weight_count += 1
                        if weight_count > 4 and vertex_error_count < 5:
                            messages.add(
                                lang_support(
                                    f"vertex id {v.index} has too many(over 4) weight in {mesh.name}",
                                    f"{mesh.name} の頂点id {v.index} に影響を与えるボーンが5以上あります。4つ以下にしてください",
                                )
                            )
                            vertex_error_count = vertex_error_count + 1
        for mat in used_material_set:
            for node in mat.node_tree.nodes:
                if node.type == "OUTPUT_MATERIAL" and (
                    node.inputs["Surface"].links[0].from_node.type != "GROUP"
                    or node.inputs["Surface"].links[0].from_node.node_tree.get("SHADER") is None
                ):
                    messages.add(
                        lang_support(
                            f"{mat.name} doesn't connect VRM SHADER node group to Material output node "
                            + "in material node tree. Please use them and connect properly.",
                            f"マテリアル:{mat.name} はVRMexport向けノードグループが直接 Material output node に繋がれていません."
                            + "ノードグループからそれらを使ってください.",
                        )
                    )
        shader_nodes_and_material = [
            (node.inputs["Surface"].links[0].from_node, mat)
            for mat in used_material_set
            for node in mat.node_tree.nodes
            if node.type == "OUTPUT_MATERIAL"
            and node.inputs["Surface"].links[0].from_node.type == "GROUP"
            and node.inputs["Surface"].links[0].from_node.node_tree.get("SHADER") is not None
        ]

        for node, material in shader_nodes_and_material:

            def input_check(expect_node_type, shader_val):
                if node.inputs[shader_val].links:
                    n = node.inputs[shader_val].links[0].from_node
                    if n.type != expect_node_type:
                        messages.add(
                            lang_support(
                                f"need {expect_node_type} input in {shader_val} of {material.name}",
                                f"{material.name}の {shader_val}には、{expect_node_type} を直接つないでください。 ",
                            )
                        )
                    else:
                        if expect_node_type == "TEX_IMAGE":
                            if n.image is not None:
                                used_image.append(n.image)
                            else:
                                messages.add(
                                    lang_support(
                                        f"image in material:{material.name} is not putted . Please set image.",
                                        f"マテリアル:{material.name} にテクスチャが設定されていない imageノードがあります。削除か画像を設定してください",
                                    )
                                )

            # MToon
            if node.node_tree["SHADER"] == "MToon_unversioned":
                for shader_val in vrm_types.MaterialMtoon.texture_kind_exchange_dic.values():
                    if shader_val is None:
                        continue
                    else:
                        if shader_val == "ReceiveShadow_Texture":
                            continue
                        input_check("TEX_IMAGE", shader_val)
                for shader_val in [
                    *list(vrm_types.MaterialMtoon.float_props_exchange_dic.values()),
                    "ReceiveShadow_Texture_alpha",
                ]:
                    if shader_val is None:
                        continue
                    else:
                        input_check("VALUE", shader_val)
                for k in ["_Color", "_ShadeColor", "_EmissionColor", "_OutlineColor"]:
                    input_check("RGB", vrm_types.MaterialMtoon.vector_props_exchange_dic[k])
            # GLTF
            elif node.node_tree["SHADER"] == "GLTF":
                texture_input_name_list = [
                    "color_texture",
                    "normal",
                    "emissive_texture",
                    "occlusion_texture",
                ]
                val_input_name_list = ["metallic", "roughness", "unlit"]
                rgba_input_name_list = ["base_Color", "emissive_color"]
                for k in texture_input_name_list:
                    input_check("TEX_IMAGE", k)
                for k in val_input_name_list:
                    input_check("VALUE", k)
                for k in rgba_input_name_list:
                    input_check("RGB", k)
            # Transparent_Zwrite
            elif node.node_tree["SHADER"] == "TRANSPARENT_ZWRITE":
                input_check("TEX_IMAGE", "Main_Texture")
            else:
                pass  # ?
        # thumbnail
        try:
            if armature is not None:
                if armature.get("texture") is not None:
                    thumbnail_image = bpy.data.images.get(armature["texture"])
                    if thumbnail_image is not None:
                        used_image.append(thumbnail_image)
                    else:
                        messages.add(
                            lang_support(
                                f"thumbnail_image is missing. Please load {armature['texture']}",
                                f"VRM用サムネ画像がblenderにロードされていません。{armature['texture']} を読み込んでください。",
                            )
                        )

        except Exception:
            messages.add(
                lang_support(
                    f"thumbnail_image is missing. Please load {armature['texture']}",
                    f"VRM用サムネ画像がblenderにロードされていません。{armature['texture']} を読み込んでください。",
                )
            )
            pass

        for img in used_image:
            if img.is_dirty or img.filepath == "":
                messages.add(
                    lang_support(f"{img.name} is not saved. Please save.", f"{img.name} のBlender上での変更を保存してください。")
                )
            if img.file_format.lower() not in ["png", "jpeg"]:
                messages.add(
                    lang_support(
                        f"glTF only supports PNG and JPEG textures: {img.name}", f"gltfはPNGとJPEGのみの対応です。:{img.name}",
                    )
                )

        if armature is not None:
            # region vrm metas check
            required_vrm_metas = {  # care about order 0 : that must be SAFE SELECTION (for auto set custom properties )
                "allowedUserName": ["OnlyAuthor", "ExplicitlyLicensedPerson", "Everyone"],
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
            for k, v in required_vrm_metas.items():
                if armature.get(k) is not None and armature.get(k) not in v:
                    messages.add(
                        lang_support(
                            f"{k} value must be in {v}. Value is {armature.get(k)}",
                            f"VRM権利情報の {k} は{v} のいずれかでないといけません。現在の設定値は {armature.get(k)} です",
                        )
                    )

            # region textblock_validate

            def text_block_name_to_json(textblock_name):
                if textblock_name not in armature:
                    messages.add(
                        lang_support(
                            f"textblock name: {textblock_name} isn't putted on armature custom property.",
                            f"{textblock_name} のテキストブロックの指定がアーマチュアのカスタムプロパティにありません",
                        )
                    )
                    return None
                if not armature[textblock_name] in bpy.data.texts:
                    messages.add(
                        lang_support(
                            f"textblock name: {textblock_name} doesn't exist.", f"{textblock_name} のテキストがエディタ上にありません。",
                        )
                    )
                    return None
                try:
                    json_as_dict = json.loads(
                        "".join([line.body for line in bpy.data.texts[armature[textblock_name]].lines]),
                        object_pairs_hook=OrderedDict,
                    )
                except json.JSONDecodeError as e:
                    messages.add(
                        lang_support(
                            f"Cannot load textblock of {textblock_name} as Json at line {e.pos.lineno}. "
                            + "please check json grammar.",
                            f"{textblock_name} のJsonとしての読み込みに失敗しました。形式を確認してください。",
                        )
                    )
                    json_as_dict = None
                return json_as_dict

            def text_block_write(block_name, data_dict):
                textblock = bpy.data.texts.new(name=f"{block_name}_.json")
                textblock.write(json.dumps(data_dict, indent=4))
                return textblock

            mesh_obj_names = [obj.name for obj in bpy.context.selected_objects if obj.type == "MESH"]
            # region humanoid_parameter
            humanoid_param_name = "humanoid_params"
            humanoid_param = text_block_name_to_json(humanoid_param_name)
            if humanoid_param is None:
                armature[humanoid_param_name] = text_block_write(
                    humanoid_param_name,
                    {
                        "armStretch": 0.05,
                        "legStretch": 0.05,
                        "upperArmTwist": 0.5,
                        "lowerArmTwist": 0.5,
                        "upperLegTwist": 0.5,
                        "lowerLegTwist": 0.5,
                        "feetSpacing": 0,
                        "hasTranslationDoF": False,
                    },
                )
            # endregion humanoid_parameter
            # region first_person
            first_person_params_name = "firstPerson_params"
            firstperson_params = text_block_name_to_json(first_person_params_name)
            if firstperson_params is not None:
                fp_bone = json_get(firstperson_params, ["firstPersonBone"], -1)
                if fp_bone != -1:
                    if not firstperson_params["firstPersonBone"] in armature.data.bones:
                        messages.add(
                            lang_support(
                                f"firstPersonBone :{firstperson_params['firstPersonBone']} is not found."
                                + f"Please fix in textblock : {first_person_params_name} ",
                                f"firstPersonBone :{firstperson_params['firstPersonBone']} がアーマチュアにありませんでした。"
                                + f"テキストエディタの  {first_person_params_name} の該当項目を修正してください。",
                            )
                        )
                if "meshAnnotations" in firstperson_params.keys():
                    if type(firstperson_params["meshAnnotations"]) is not list:
                        messages.add(
                            lang_support(
                                f"meshAnnotations in textblock:{first_person_params_name} must be list.",
                                f"テキストエディタの {first_person_params_name} のmeshAnnotations はリスト要素でないといけません。",
                            )
                        )
                    else:
                        for mesh_annotation in firstperson_params["meshAnnotations"]:
                            if not mesh_annotation["mesh"] in mesh_obj_names:
                                messages.add(
                                    lang_support(
                                        f"mesh :{mesh_annotation['mesh']} is not found."
                                        + f"Please fix setting in textblock : {first_person_params_name} ",
                                        f"{mesh_annotation['mesh']} というメッシュオブジェクトが見つかりません。"
                                        + f"テキストエディタの {first_person_params_name} を修正してください。",
                                    )
                                )
                if "lookAtTypeName" in firstperson_params:
                    if not firstperson_params["lookAtTypeName"] in [
                        "Bone",
                        "BlendShape",
                    ]:
                        messages.add(
                            lang_support(
                                'lookAtTypeName is "Bone" or "BlendShape". '
                                + f"Current :{firstperson_params['lookAtTypeName']}."
                                + f"Please fix setting in textblock : {first_person_params_name} ",
                                'lookAtTypeName は "Bone" か "BlendShape"です.'
                                + f"今は :{firstperson_params['lookAtTypeName']}です。"
                                + f"テキストエディタの {first_person_params_name} を修正してください。",
                            )
                        )
            # endregion first_person

            # region blendshape_master
            blendshape_group_name = "blendshape_group"
            blendshape_groups_list = text_block_name_to_json(blendshape_group_name)
            if blendshape_groups_list is None:
                blendshape_groups_list = []
            # TODO material value and material existance
            for bsg in blendshape_groups_list:
                for bind_dic in bsg["binds"]:
                    if not bind_dic["mesh"] in mesh_obj_names:
                        messages.add(
                            lang_support(
                                f"mesh :{bind_dic['mesh']} is not found."
                                + f"Please fix setting in textblock : {blendshape_group_name} ",
                                f"メッシュ :{bind_dic['mesh']} が見つかりません。" + f"テキストエディタの {blendshape_group_name} を修正してください。",
                            )
                        )
                    else:
                        if bpy.data.objects[bind_dic["mesh"]].data.shape_keys is None:
                            messages.add(
                                lang_support(
                                    f"mesh :{bind_dic['mesh']} doesn't have shapekey. but blendshape Group need it."
                                    + f"Please fix setting in textblock :{blendshape_group_name}",
                                    f"メッシュ :{bind_dic['mesh']} はシェイプキーがありません。 しかし blendshape Group の設定はそれを必要としています。"
                                    + f"テキストエディタの {blendshape_group_name} を修正してください。",
                                )
                            )
                        else:
                            if not bind_dic["index"] in bpy.data.objects[bind_dic["mesh"]].data.shape_keys.key_blocks:
                                messages.add(
                                    lang_support(
                                        f"mesh :{bind_dic['mesh']} doesn't have {bind_dic['index']} shapekey. "
                                        + "but blendshape Group need it."
                                        + f"Please fix setting in textblock :{blendshape_group_name}",
                                        f"メッシュ :{bind_dic['mesh']} はシェイプキー {bind_dic['index']} が足りません。"
                                        + "しかし blendshape Group の設定はそれを必要としています。"
                                        + f"テキストエディタの {blendshape_group_name} を修正してください。",
                                    )
                                )
                            if bind_dic["weight"] > 1 or bind_dic["weight"] < 0:
                                messages.add(
                                    lang_support(
                                        f"mesh :{bind_dic['mesh']}:shapekey:{bind_dic['index']}:value "
                                        + "needs between 0 and 1."
                                        + f"Please fix setting in textblock :{blendshape_group_name}",
                                        f"メッシュ :{bind_dic['mesh']}のshapekey:{bind_dic['index']}の値は0以上1以内でないといけません。"
                                        + f"テキストエディタの {blendshape_group_name}  を修正してください。",
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
                        messages.add(
                            lang_support(
                                f"Bone name : {bone_name} is not found in spring_bone setting.",
                                f"spring_bone settingにある、ボーン名 : {bone_name} がアーマチュア中に見つかりません。"
                                + "テキストエディタの spring_bone のjsonを修正してください。",
                            )
                        )
                for bone_name in bone_group["colliderGroups"]:
                    if bone_name not in bone_names_list:
                        messages.add(
                            lang_support(
                                f"Bone name : {bone_name} is not found in spring_bone setting.",
                                f"spring_bone settingにある、ボーン名 : {bone_name} がアーマチュア中に見つかりません。"
                                + "テキストエディタの spring_bone のjsonを修正してください。",
                            )
                        )

        # endregion vrm metas check

        for mes in messages:
            self.report({"ERROR"}, mes)
        print("validation finished")

        if len(messages) > 0:
            VRM_VALIDATOR.draw_func_add()
            return {"CANCELLED"}

        messages.add("No error. Ready for export VRM.")
        VRM_VALIDATOR.draw_func_add()
        return {"FINISHED"}

    # region 3Dview drawer
    draw_func = None
    counter = 0

    @staticmethod
    def draw_func_add():
        if VRM_VALIDATOR.draw_func is not None:
            VRM_VALIDATOR.draw_func_remove()
        VRM_VALIDATOR.draw_func = bpy.types.SpaceView3D.draw_handler_add(
            VRM_VALIDATOR.texts_draw, (), "WINDOW", "POST_PIXEL"
        )
        VRM_VALIDATOR.counter = 300

    @staticmethod
    def draw_func_remove():
        if VRM_VALIDATOR.draw_func is not None:
            bpy.types.SpaceView3D.draw_handler_remove(VRM_VALIDATOR.draw_func, "WINDOW")
            VRM_VALIDATOR.draw_func = None

    @staticmethod
    def texts_draw():
        text_size = 20
        dpi = 72
        blf.size(0, text_size, dpi)
        for i, text in enumerate(list(VRM_VALIDATOR.messages_set)):
            blf.position(0, text_size, text_size * (i + 1) + 100, 0)
            blf.draw(0, text)
        blf.position(0, text_size, text_size * (2 + len(VRM_VALIDATOR.messages_set)) + 100, 0)
        blf.draw(0, "message delete count down...:{}".format(VRM_VALIDATOR.counter))
        VRM_VALIDATOR.counter -= 1
        if VRM_VALIDATOR.counter <= 0:
            VRM_VALIDATOR.draw_func_remove()

    # endregion 3Dview drawer
