import contextlib
import json
import os
from collections import OrderedDict
from sys import float_info
from typing import Any, Dict, List, Optional, Set, Union, cast

import bpy
from mathutils import Vector

from .. import deep, lang, vrm_types
from ..preferences import get_preferences
from ..vrm_types import Gltf
from . import search


class VrmValidationError(bpy.types.PropertyGroup):  # type: ignore[misc]
    message: bpy.props.StringProperty()  # type: ignore[valid-type]
    fatal: bpy.props.BoolProperty()  # type: ignore[valid-type]


class WM_OT_vrmValidator(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
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
            return {"CANCELLED"}
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
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
                        lang.support(
                            f"Nodes(mesh,bones) require unique names for VRM export. {obj.name} is duplicated.",
                            f"glTFノード要素(メッシュ、ボーン)の名前は重複してはいけません。「{obj.name}」が重複しています。",
                        )
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
                    lang.support(
                        f'There are not an object on the origin "{obj.name}"',
                        f"「{obj.name}」が原点座標にありません",
                    )
                )
            if obj.type == "ARMATURE":
                armature = obj
                armature_count += 1
                if armature_count >= 2:  # only one armature
                    messages.append(
                        lang.support(
                            "Only one armature is required for VRM export. Multiple armatures found.",
                            "VRM出力の際、選択できるアーマチュアは1つのみです。複数選択されています。",
                        )
                    )
                for bone in obj.data.bones:
                    if bone.name in node_names:  # nodes name is unique
                        messages.append(
                            lang.support(
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
                        lang.support(
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
                        lang.support(
                            f'Bone name "{node_name}" as VRM HumanBone "{humanoid_name}" is not found. '
                            + 'Fix armature "object" custom property.',
                            f"ボーン名「{node_name}」のVRMヒューマンボーン属性「{humanoid_name}」がありません。"
                            + "アーマチュア「オブジェクト」のカスタムプロパティを修正してください。",
                        )
                    )

            if obj.type == "MESH":
                for poly in obj.data.polygons:
                    if poly.loop_total > 3:  # polygons need all triangle
                        warning_messages.append(
                            lang.support(
                                f'Faces must be Triangle, but not face in "{obj.name}" or '
                                + "it will be triangulated automatically.",
                                f"「{obj.name}」のポリゴンに三角形以外のものが含まれます。自動的に三角形に分割されます。",
                            )
                        )
                        break

                # TODO modifier applied, vertex weight Bone exist, vertex weight numbers.
        # endregion export object seeking
        if armature_count == 0:
            warning_messages.append(
                lang.support("Please add ARMATURE to selections", "アーマチュアを選択範囲に含めてください")
            )

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
                        lang.support(
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
                            lang.support(
                                f'vertex id "{v.index}" has too many(over 4) weight in "{mesh.name}". '
                                + "It will be truncated to 4 descending order by its weight.",
                                f"「{mesh.name}」の頂点id「{v.index}」に影響を与えるボーンが5以上あります。"
                                + "重い順に4つまでエクスポートされます。",
                            )
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
                        groups_en_str = "/".join(groups)
                        groups_ja_str = "".join(f"「{group}」" for group in groups)
                        warning_messages.append(
                            lang.support(
                                f'"{mat.name}" needs to connect {groups_en_str} to "Surface" directly. '
                                + "Empty material will be exported.",
                                f"マテリアル「{mat.name}」には{groups_ja_str}のいずれかを直接「サーフェス」に指定してください。"
                                + "空のマテリアルを出力します。",
                            )
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
        try:
            if armature is not None and armature.get("texture") is not None:
                if armature["texture"] in bpy.data.images:
                    image = bpy.data.images[armature["texture"]]
                    if image not in used_images:
                        used_images.append(image)
                else:
                    messages.append(
                        lang.support(
                            f"thumbnail_image is missing. Please load \"{armature['texture']}\"",
                            f"VRM用サムネイル画像がBlenderにロードされていません。「{armature['texture']}」を読み込んでください。",
                        )
                    )

        except Exception:
            messages.append(
                lang.support(
                    f"thumbnail_image is missing. Please load \"{armature['texture']}\"",
                    f"VRM用サムネイル画像がBlenderにロードされていません。「{armature['texture']}」を読み込んでください。",
                )
            )

        for image in used_images:
            if image.is_dirty or (image.packed_file is None and not image.filepath):
                messages.append(
                    lang.support(
                        f'Image "{image.name}" is not saved. Please save.',
                        f"画像「{image.name}」のBlender上での変更を保存してください。",
                    )
                )
                continue
            if image.packed_file is None and not os.path.exists(
                image.filepath_from_user()
            ):
                messages.append(
                    lang.support(
                        f'"{image.name}" is not found in file path "{image.filepath_from_user()}". '
                        + "Please load file of it in Blender.",
                        f'「{image.name}」の画像ファイルが指定ファイルパス「"{image.filepath_from_user()}"」'
                        + "に存在しません。画像を読み込み直してください。",
                    )
                )
                continue
            if image.file_format.lower() not in ["png", "jpeg"]:
                messages.append(
                    lang.support(
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
                        lang.support(
                            f'"{k}" value must be in "{v}". Value is "{armature.get(k)}"',
                            f"VRM権利情報の「{k}」は「{v}」のいずれかでないといけません。現在の設定値は「{armature.get(k)}」です。",
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
                        lang.support(
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
                    warning_messages.append(
                        lang.support(
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
                    warning_messages.append(
                        lang.support(
                            f'Cannot load textblock of "{textblock_name}" as Json at line {e.lineno}. '
                            + "please check json grammar.",
                            f"「{textblock_name}」のJsonとしての読み込みに失敗しました。{e.lineno}行目付近にエラーがあります。"
                            + "形式を確認してください。",
                        )
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
            firstperson_params = text_block_name_to_json(first_person_params_name)
            if isinstance(firstperson_params, dict):
                fp_bone = deep.get(firstperson_params, ["firstPersonBone"], -1)
                if (
                    fp_bone != -1
                    and firstperson_params["firstPersonBone"] not in armature.data.bones
                ):
                    warning_messages.append(
                        lang.support(
                            f"firstPersonBone \"{firstperson_params['firstPersonBone']}\" is not found. "
                            + f'Please fix in textblock "{first_person_params_name}". '
                            + 'Set VRM HumanBone "head" instead automatically.',
                            f"firstPersonBone「{firstperson_params['firstPersonBone']}」がアーマチュアにありませんでした。"
                            + f"テキストエディタの「{first_person_params_name}」の該当項目を修正してください。"
                            + "代わりにfirstPersonBoneとしてVRMヒューマンボーン「head」を自動で設定します。",
                        )
                    )
                if "meshAnnotations" in firstperson_params:
                    if isinstance(firstperson_params["meshAnnotations"], list):
                        for mesh_annotation in firstperson_params["meshAnnotations"]:
                            if mesh_annotation["mesh"] not in mesh_name_to_mesh:
                                warning_messages.append(
                                    lang.support(
                                        f"mesh \"{mesh_annotation['mesh']}\" is not found. "
                                        + f'Please fix setting in textblock "{first_person_params_name}"',
                                        f"「{mesh_annotation['mesh']}」というメッシュオブジェクトが見つかりません。"
                                        + f"テキストエディタの「{first_person_params_name}」を修正してください。",
                                    )
                                )
                    else:
                        warning_messages.append(
                            lang.support(
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
                        lang.support(
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
            if not isinstance(blendshape_groups, list):
                blendshape_groups = []
            # TODO material value and material existence
            for blendshape_group in blendshape_groups:
                for bind_dic in blendshape_group.get("binds", []):
                    if bind_dic["mesh"] not in mesh_name_to_mesh:
                        warning_messages.append(
                            lang.support(
                                f"mesh \"{bind_dic['mesh']}\" is not found. "
                                + f'Please fix setting in textblock "{blendshape_group_name}"',
                                f"メッシュ「{bind_dic['mesh']}」が見つかりません。"
                                + f"テキストエディタの「{blendshape_group_name}」を修正してください。",
                            )
                        )
                    else:
                        shape_keys = mesh_name_to_mesh[bind_dic["mesh"]].shape_keys
                        if shape_keys is None:
                            warning_messages.append(
                                lang.support(
                                    f"mesh \"{bind_dic['mesh']}\" doesn't have shapekey. "
                                    + "But blendshape Group needs it. "
                                    + f'Please fix setting in textblock "{blendshape_group_name}"',
                                    f"メッシュ「{bind_dic['mesh']}」はシェイプキーがありません。"
                                    + "しかし blendshape Group の設定はそれを必要としています。"
                                    + f"テキストエディタの「{blendshape_group_name}」を修正してください。",
                                )
                            )
                        else:
                            if bind_dic["index"] not in shape_keys.key_blocks:
                                warning_messages.append(
                                    lang.support(
                                        f"mesh \"{bind_dic['mesh']}\" doesn't have \"{bind_dic['index']}\" shapekey. "
                                        + "But blendshape Group needs it. "
                                        + f'Please fix setting in textblock "{blendshape_group_name}"',
                                        f"メッシュ「{bind_dic['mesh']}」にはシェイプキー「{bind_dic['index']}」が存在しません。"
                                        + "しかし blendshape Group の設定はそれを必要としています。"
                                        + f"テキストエディタの「{blendshape_group_name}」を修正してください。",
                                    )
                                )
                            if bind_dic["weight"] > 1 or bind_dic["weight"] < 0:
                                warning_messages.append(
                                    lang.support(
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
            if not isinstance(spring_bonegroup_list, list):
                spring_bonegroup_list = []
            for bone_group in spring_bonegroup_list:
                if (
                    isinstance(bone_group.get("center"), str)
                    and bone_group["center"] not in bone_names_list
                ):
                    bone_name = bone_group["center"]
                    warning_messages.append(
                        lang.support(
                            f'Center bone name "{bone_name}" is not found in spring_bone setting.',
                            f"spring_boneのcenterのボーン名「{bone_name}」がアーマチュア中に見つかりません。"
                            + "テキストエディタの spring_bone の json を修正してください。",
                        )
                    )
                for bone_name in bone_group["bones"]:
                    if bone_name not in bone_names_list:
                        warning_messages.append(
                            lang.support(
                                f'Bone name "{bone_name}" is not found in spring_bone setting.',
                                f"spring_boneのボーン名「{bone_name}」がアーマチュア中に見つかりません。"
                                + "テキストエディタの spring_bone の json を修正してください。",
                            )
                        )
                for bone_name in bone_group["colliderGroups"]:
                    if bone_name not in bone_names_list:
                        warning_messages.append(
                            lang.support(
                                f'Bone name "{bone_name}" is not found in spring_bone setting.',
                                f"spring_bone settingにある、ボーン名「{bone_name}」がアーマチュア中に見つかりません。"
                                + "テキストエディタの spring_bone のjsonを修正してください。",
                            )
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
                lang.support(
                    f'need "{expect_node_type}" input in "{shader_val}" of "{material.name}"',
                    f"「{material.name}」の「{shader_val}」には、「{expect_node_type}」を直接つないでください。 ",
                )
            )
        else:
            if expect_node_type == "TEX_IMAGE":
                if n.image is not None:
                    if n.image not in used_images:
                        used_images.append(n.image)
                else:
                    messages.append(
                        lang.support(
                            f'image in material "{material.name}" is not put. Please set image.',
                            f"マテリアル「{material.name}」にテクスチャが設定されていないimageノードがあります。削除か画像を設定してください。",
                        )
                    )
