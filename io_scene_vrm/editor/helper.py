"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
import json
import os
import re
from collections import OrderedDict
from typing import Set, cast

import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper

from ..common.human_bone_constants import HumanBone
from . import search
from .make_armature import ICYP_OT_make_armature


class VRM_OT_rename_bones(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.bones_rename"
    bl_label = "Rename VRoid_bones"
    bl_description = "Rename VRoid_bones as Blender type"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        def reprstr(bone_name: str) -> str:
            ml = re.match("(.*)_" + "L" + "_(.*)", bone_name)
            mr = re.match("(.*)_" + "R" + "_(.*)", bone_name)
            if ml or mr:
                tmp = ""
                ma = ml if ml else mr
                if ma is None:
                    raise Exception(f"{bone_name} is not vroid bone name")
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
        for bonename in HumanBone.requires + HumanBone.defines:
            if bonename in bpy.context.active_object.data:
                bpy.context.active_object.data[bonename] = reprstr(
                    bpy.context.active_object.data[bonename]
                )
        return {"FINISHED"}


class VRM_OT_add_extensions_to_armature(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm_extensions"
    bl_label = "Add VRM attributes"
    bl_description = "Add VRM extensions & metas to armature"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        ICYP_OT_make_armature.make_extension_setting_and_metas(context.active_object)
        return {"FINISHED"}


# deprecated
class VRM_OT_add_human_bone_custom_property(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
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
class VRM_OT_add_required_human_bone_custom_property(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm_req_humanbone_prop"
    bl_label = "Add vrm human_bone_prop"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures[bpy.context.active_object.data.name]
        for bone_name in HumanBone.requires:
            if bone_name not in armature:
                armature[bone_name] = ""
        return {"FINISHED"}


# deprecated
class VRM_OT_add_defined_human_bone_custom_property(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm_def_humanbone_prop"
    bl_label = "Add vrm human_bone_prop"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures[bpy.context.active_object.data.name]
        for bone_name in HumanBone.defines:
            if bone_name not in armature:
                armature[bone_name] = ""
        return {"FINISHED"}


class VRM_OT_save_human_bone_mappings(bpy.types.Operator, ExportHelper):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.save_human_bone_mappings"
    bl_label = "Save bone mappings"
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
            if human_bone.bone not in HumanBone.requires + HumanBone.defines:
                continue
            if not human_bone.node.value:
                continue
            mappings[human_bone.bone] = human_bone.node.value

        with open(self.filepath, "wb") as file:
            file.write(
                json.dumps(mappings, sort_keys=True, indent=4)
                .replace("\r\n", "\n")
                .encode()
            )
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        return cast(Set[str], ExportHelper.invoke(self, context, event))


class VRM_OT_load_human_bone_mappings(bpy.types.Operator, ImportHelper):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.load_human_bone_mappings"
    bl_label = "Load bone mappings"
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

        with open(self.filepath, "rb") as file:
            obj = json.load(file)
        if not isinstance(obj, dict):
            return {"CANCELLED"}

        for human_bone_name, blender_bone_name in obj.items():
            if human_bone_name not in HumanBone.requires + HumanBone.defines:
                continue

            found = False
            for (
                human_bone_props
            ) in armature.data.vrm_addon_extension.vrm0.humanoid.human_bones:
                if human_bone_props.bone == human_bone_name:
                    human_bone_props.node.value = blender_bone_name
                    found = True
                    break
            if found:
                continue

            human_bone_props = (
                armature.data.vrm_addon_extension.vrm0.humanoid.human_bones.add()
            )
            human_bone_props.bone = human_bone_name
            human_bone_props.node.value = blender_bone_name

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        return cast(Set[str], ImportHelper.invoke(self, context, event))


class VRM_OT_vroid2vrc_lipsync_from_json_recipe(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.lipsync_vrm"
    bl_label = "Make lipsync4VRC"
    bl_description = "Make lipsync from VRoid to VRC by json"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        recipe_uri = os.path.join(
            os.path.dirname(__file__), "vroid2vrc_lipsync_recipe.json"
        )
        recipe = None
        with open(recipe_uri, "rt", encoding="utf-8") as raw_recipe:
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
