"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
import json
import re
import webbrowser
from pathlib import Path
from typing import Set, cast
from urllib.parse import urlparse

import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper

from ..common.vrm0.human_bone import HumanBoneSpecifications
from . import search
from .make_armature import ICYP_OT_make_armature


class VRM_OT_simplify_vroid_bones(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.bones_rename"
    bl_label = "Symmetrize VRoid Bone Names on X-Axis"
    bl_description = "Make VRoid bone names X-axis mirror editable"
    bl_options = {"REGISTER", "UNDO"}

    left__pattern = re.compile("^J_(Adj|Bip|Opt|Sec)_L_")
    right_pattern = re.compile("^J_(Adj|Bip|Opt|Sec)_R_")
    full__pattern = re.compile("^J_(Adj|Bip|Opt|Sec)_([CLR]_)?")

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )

    @staticmethod
    def vroid_bones_exist(armature: bpy.types.Armature) -> bool:
        return any(
            map(VRM_OT_simplify_vroid_bones.full__pattern.match, armature.bones.keys())
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}

        back_to_edit_mode = False
        try:
            if context.active_object and context.active_object.mode == "EDIT":
                bpy.ops.object.mode_set(mode="OBJECT")
                back_to_edit_mode = True

            for bone_name, bone in armature.data.bones.items():
                left = VRM_OT_simplify_vroid_bones.left__pattern.sub("", bone_name)
                if left != bone_name:
                    bone.name = left + "_L"
                    continue

                right = VRM_OT_simplify_vroid_bones.right_pattern.sub("", bone_name)
                if right != bone_name:
                    bone.name = right + "_R"
                    continue

                a = VRM_OT_simplify_vroid_bones.full__pattern.sub("", bone_name)
                if a != bone_name:
                    bone.name = a
                    continue
        finally:
            if back_to_edit_mode:
                bpy.ops.object.mode_set(mode="EDIT")

        return {"FINISHED"}


class VRM_OT_add_extensions_to_armature(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_vrm_extensions"
    bl_label = "Add VRM attributes"
    bl_description = "Add VRM extensions & metas to armature"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        ICYP_OT_make_armature.make_extension_setting_and_metas(context.active_object)
        return {"FINISHED"}


# deprecated
class VRM_OT_add_human_bone_custom_property(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_vrm_humanbone_custom_property"
    bl_label = "Add VRM Human Bone prop"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    bone_name: bpy.props.StringProperty()  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        if self.armature_name not in bpy.data.armatures:
            return {"CANCELLED"}
        armature = bpy.data.armatures[self.armature_name]
        if self.bone_name not in armature:
            armature[self.bone_name] = ""
        return {"FINISHED"}


# deprecated
class VRM_OT_add_required_human_bone_custom_property(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_vrm_req_humanbone_prop"
    bl_label = "Add vrm human_bone_prop"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures[context.active_object.data.name]
        for bone_name in HumanBoneSpecifications.required_names:
            if bone_name not in armature:
                armature[bone_name] = ""
        return {"FINISHED"}


# deprecated
class VRM_OT_add_defined_human_bone_custom_property(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_vrm_def_humanbone_prop"
    bl_label = "Add vrm human_bone_prop"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures[context.active_object.data.name]
        for bone_name in HumanBoneSpecifications.optional_names:
            if bone_name not in armature:
                armature[bone_name] = ""
        return {"FINISHED"}


class VRM_OT_save_human_bone_mappings(bpy.types.Operator, ExportHelper):  # type: ignore[misc]
    bl_idname = "vrm.save_human_bone_mappings"
    bl_label = "Save Bone Mappings"
    bl_description = ""
    bl_options = {"REGISTER"}

    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(  # type: ignore[valid-type]
        default="*.json", options={"HIDDEN"}  # noqa: F722,F821
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.armature_exists(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        armature = search.current_armature(context)
        if not armature:
            return {"CANCELLED"}

        mappings = {}
        for human_bone in armature.data.vrm_addon_extension.vrm0.humanoid.human_bones:
            if human_bone.bone not in HumanBoneSpecifications.all_names:
                continue
            if not human_bone.node.value:
                continue
            mappings[human_bone.bone] = human_bone.node.value

        Path(self.filepath).write_bytes(
            json.dumps(mappings, sort_keys=True, indent=4)
            .replace("\r\n", "\n")
            .encode()
        )
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        return cast(Set[str], ExportHelper.invoke(self, context, event))


class VRM_OT_load_human_bone_mappings(bpy.types.Operator, ImportHelper):  # type: ignore[misc]
    bl_idname = "vrm.load_human_bone_mappings"
    bl_label = "Load Bone Mappings"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(  # type: ignore[valid-type]
        default="*.json", options={"HIDDEN"}  # noqa: F722,F821
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.armature_exists(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        armature = search.current_armature(context)
        if not armature:
            return {"CANCELLED"}

        obj = json.loads(Path(self.filepath).read_text(encoding="UTF-8"))
        if not isinstance(obj, dict):
            return {"CANCELLED"}

        for human_bone_name, bpy_bone_name in obj.items():
            if human_bone_name not in HumanBoneSpecifications.all_names:
                continue

            found = False
            for (
                human_bone
            ) in armature.data.vrm_addon_extension.vrm0.humanoid.human_bones:
                if human_bone.bone == human_bone_name:
                    human_bone.node.value = bpy_bone_name
                    found = True
                    break
            if found:
                continue

            human_bone = (
                armature.data.vrm_addon_extension.vrm0.humanoid.human_bones.add()
            )
            human_bone.bone = human_bone_name
            human_bone.node.value = bpy_bone_name

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        return cast(Set[str], ImportHelper.invoke(self, context, event))


class VRM_OT_vroid2vrc_lipsync_from_json_recipe(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.lipsync_vrm"
    bl_label = "Make lipsync4VRC"
    bl_description = "Make lipsync from VRoid to VRC by json"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return bool(
            obj
            and obj.type == "MESH"
            and obj.data.shape_keys
            and obj.data.shape_keys.key_blocks
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        recipe = json.loads(
            Path(__file__)
            .with_name("vroid2vrc_lipsync_recipe.json")
            .read_text(encoding="UTF-8")
        )
        for shapekey_name, based_values in recipe["shapekeys"].items():
            for k in context.active_object.data.shape_keys.key_blocks:
                k.value = 0.0
            for based_shapekey_name, based_val in based_values.items():
                # if M_F00_000+_00
                if (
                    based_shapekey_name
                    not in context.active_object.data.shape_keys.key_blocks
                ):
                    based_shapekey_name = based_shapekey_name.replace(
                        "M_F00_000", "M_F00_000_00"
                    )  # Vroid064から命名が変わった
                context.active_object.data.shape_keys.key_blocks[
                    based_shapekey_name
                ].value = based_val
            bpy.ops.object.shape_key_add(from_mix=True)
            context.active_object.data.shape_keys.key_blocks[-1].name = shapekey_name
        for k in context.active_object.data.shape_keys.key_blocks:
            k.value = 0.0
        return {"FINISHED"}


class VRM_OT_open_url_in_web_browser(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.open_url_in_web_browser"
    bl_label = "Open"
    bl_description = "Open the URL in the default web browser"
    bl_options = {"REGISTER", "UNDO"}

    url: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F722,F821
    )

    @staticmethod
    def supported(url_str: str) -> bool:
        try:
            url = urlparse(url_str)
        except ValueError:
            return False
        if url.scheme not in ["http", "https"]:
            return False
        return True

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        url = self.url
        if not isinstance(url, str):
            return {"CANCELLED"}
        if not self.supported(url):
            return {"CANCELLED"}
        webbrowser.open(self.url)
        return {"FINISHED"}
