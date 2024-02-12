# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2018 iCyP

import json
import re
import webbrowser
from collections.abc import Set as AbstractSet
from pathlib import Path
from typing import TYPE_CHECKING, Optional, TypeVar, cast
from urllib.parse import urlparse

import bpy
from bpy.props import StringProperty
from bpy.types import Armature, Context, Event, Mesh, Operator, UILayout
from bpy_extras.io_utils import ExportHelper, ImportHelper

from ..common.vrm0.human_bone import HumanBoneSpecifications
from . import search
from .make_armature import ICYP_OT_make_armature


class VRM_OT_simplify_vroid_bones(Operator):
    bl_idname = "vrm.bones_rename"
    bl_label = "Symmetrize VRoid Bone Names on X-Axis"
    bl_description = "Make VRoid bone names X-axis mirror editable"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    left__pattern = re.compile("^J_(Adj|Bip|Opt|Sec)_L_")
    right_pattern = re.compile("^J_(Adj|Bip|Opt|Sec)_R_")
    full__pattern = re.compile("^J_(Adj|Bip|Opt|Sec)_([CLR]_)?")

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )

    @staticmethod
    def vroid_bones_exist(armature: Armature) -> bool:
        return any(
            map(VRM_OT_simplify_vroid_bones.full__pattern.match, armature.bones.keys())
        )

    def execute(self, context: Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}

        back_to_edit_mode = False
        try:
            if context.active_object and context.active_object.mode == "EDIT":
                bpy.ops.object.mode_set(mode="OBJECT")
                back_to_edit_mode = True

            for bone_name, bone in armature_data.bones.items():
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

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run python tools/property_typing.py`
        armature_name: str  # type: ignore[no-redef]


class VRM_OT_add_extensions_to_armature(Operator):
    bl_idname = "vrm.add_vrm_extensions"
    bl_label = "Add VRM attributes"
    bl_description = "Add VRM extensions & metas to armature"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    def execute(self, context: Context) -> set[str]:
        obj = context.active_object
        if not obj:
            return {"CANCELLED"}
        ICYP_OT_make_armature.make_extension_setting_and_metas(obj)
        return {"FINISHED"}


# deprecated
class VRM_OT_add_human_bone_custom_property(Operator):
    bl_idname = "vrm.add_vrm_humanbone_custom_property"
    bl_label = "Add VRM Human Bone prop"
    bl_description = ""
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty()  # type: ignore[valid-type]
    bone_name: StringProperty()  # type: ignore[valid-type]

    def execute(self, _context: Context) -> set[str]:
        if self.armature_name not in bpy.data.armatures:
            return {"CANCELLED"}
        armature = bpy.data.armatures[self.armature_name]
        if self.bone_name not in armature:
            armature[self.bone_name] = ""
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run python tools/property_typing.py`
        armature_name: str  # type: ignore[no-redef]
        bone_name: str  # type: ignore[no-redef]


# deprecated
class VRM_OT_add_required_human_bone_custom_property(Operator):
    bl_idname = "vrm.add_vrm_req_humanbone_prop"
    bl_label = "Add vrm human_bone_prop"
    bl_description = ""
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    def execute(self, context: Context) -> set[str]:
        obj = context.active_object
        if not obj:
            return {"CANCELLED"}
        armature = obj.data
        if not isinstance(armature, Armature):
            return {"CANCELLED"}
        for bone_name in HumanBoneSpecifications.required_names:
            if bone_name not in armature:
                armature[bone_name] = ""
        return {"FINISHED"}


# deprecated
class VRM_OT_add_defined_human_bone_custom_property(Operator):
    bl_idname = "vrm.add_vrm_def_humanbone_prop"
    bl_label = "Add vrm human_bone_prop"
    bl_description = ""
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    def execute(self, context: Context) -> set[str]:
        obj = context.active_object
        if not obj:
            return {"CANCELLED"}
        armature = obj.data
        if not isinstance(armature, Armature):
            return {"CANCELLED"}
        for bone_name in HumanBoneSpecifications.optional_names:
            if bone_name not in armature:
                armature[bone_name] = ""
        return {"FINISHED"}


class VRM_OT_save_human_bone_mappings(Operator, ExportHelper):
    bl_idname = "vrm.save_human_bone_mappings"
    bl_label = "Save Bone Mappings"
    bl_description = "Save Bone Mappings"
    bl_options: AbstractSet[str] = {"REGISTER"}

    filename_ext = ".json"
    filter_glob: StringProperty(  # type: ignore[valid-type]
        default="*.json",
        options={"HIDDEN"},
    )

    @classmethod
    def poll(cls, context: Context) -> bool:
        return search.armature_exists(context)

    def execute(self, context: Context) -> set[str]:
        armature = search.current_armature(context)
        if not armature:
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}

        mappings = {}
        for human_bone in armature_data.vrm_addon_extension.vrm0.humanoid.human_bones:
            if human_bone.bone not in HumanBoneSpecifications.all_names:
                continue
            if not human_bone.node.bone_name:
                continue
            mappings[human_bone.bone] = human_bone.node.bone_name

        Path(self.filepath).write_bytes(
            json.dumps(mappings, sort_keys=True, indent=4)
            .replace("\r\n", "\n")
            .encode()
        )
        return {"FINISHED"}

    def invoke(self, context: Context, event: Event) -> set[str]:
        return ExportHelper.invoke(self, context, event)

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run python tools/property_typing.py`
        filter_glob: str  # type: ignore[no-redef]


class VRM_OT_load_human_bone_mappings(Operator, ImportHelper):
    bl_idname = "vrm.load_human_bone_mappings"
    bl_label = "Load Bone Mappings"
    bl_description = "Load Bone Mappings"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    filename_ext = ".json"
    filter_glob: StringProperty(  # type: ignore[valid-type]
        default="*.json",
        options={"HIDDEN"},
    )

    @classmethod
    def poll(cls, context: Context) -> bool:
        return search.armature_exists(context)

    def execute(self, context: Context) -> set[str]:
        armature = search.current_armature(context)
        if not armature:
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
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
            ) in armature_data.vrm_addon_extension.vrm0.humanoid.human_bones:
                if human_bone.bone == human_bone_name:
                    human_bone.node.set_bone_name(bpy_bone_name)
                    found = True
                    break
            if found:
                continue

            human_bone = (
                armature_data.vrm_addon_extension.vrm0.humanoid.human_bones.add()
            )
            human_bone.bone = human_bone_name
            human_bone.node.set_bone_name(bpy_bone_name)

        return {"FINISHED"}

    def invoke(self, context: Context, event: Event) -> set[str]:
        return ImportHelper.invoke(self, context, event)

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run python tools/property_typing.py`
        filter_glob: str  # type: ignore[no-redef]


class VRM_OT_vroid2vrc_lipsync_from_json_recipe(Operator):
    bl_idname = "vrm.lipsync_vrm"
    bl_label = "Make lipsync4VRC"
    bl_description = "Make lipsync from VRoid to VRC by json"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        obj = context.active_object
        if not obj:
            return False
        data = obj.data
        if not isinstance(data, Mesh):
            return False
        shape_keys = data.shape_keys
        if not shape_keys:
            return False
        return bool(shape_keys.key_blocks)

    def execute(self, context: Context) -> set[str]:
        recipe = json.loads(
            Path(__file__)
            .with_name("vroid2vrc_lipsync_recipe.json")
            .read_text(encoding="UTF-8")
        )

        obj = context.active_object
        if not obj:
            return {"CANCELLED"}
        data = obj.data
        if not isinstance(data, Mesh):
            return {"CANCELLED"}
        shape_keys = data.shape_keys
        if not shape_keys:
            return {"CANCELLED"}
        for shapekey_name, based_values in recipe["shapekeys"].items():
            for k in shape_keys.key_blocks:
                k.value = 0.0
            for based_shapekey_name, based_val in based_values.items():
                # if M_F00_000+_00
                if based_shapekey_name not in shape_keys.key_blocks:
                    vroid_shapekey_name = based_shapekey_name.replace(
                        "M_F00_000", "M_F00_000_00"
                    )  # Vroid064から命名が変わった
                else:
                    vroid_shapekey_name = based_shapekey_name
                shape_keys.key_blocks[vroid_shapekey_name].value = based_val
            bpy.ops.object.shape_key_add(from_mix=True)
            shape_keys.key_blocks[-1].name = shapekey_name
        for k in shape_keys.key_blocks:
            k.value = 0.0
        return {"FINISHED"}


class VRM_OT_open_url_in_web_browser(Operator):
    bl_idname = "vrm.open_url_in_web_browser"
    bl_label = "Open"
    bl_description = "Open the URL in the default web browser"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    url: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
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

    def execute(self, _context: Context) -> set[str]:
        url = self.url
        if not self.supported(url):
            return {"CANCELLED"}
        webbrowser.open(self.url)
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run python tools/property_typing.py`
        url: str  # type: ignore[no-redef]


__Operator = TypeVar("__Operator", bound=Operator)


def layout_operator(
    layout: UILayout,
    operator_type: type[__Operator],
    text: Optional[str] = None,
    text_ctxt: str = "",
    translate: bool = True,
    icon: str = "NONE",
    emboss: bool = True,
    depress: bool = False,
    icon_value: int = 0,
) -> __Operator:
    if text is None:
        text = operator_type.bl_label
    operator = layout.operator(
        operator_type.bl_idname,
        text=text,
        text_ctxt=text_ctxt,
        translate=translate,
        icon=icon,
        emboss=emboss,
        depress=depress,
        icon_value=icon_value,
    )

    split = operator_type.bl_idname.split(".")
    if len(split) != 2:
        message = f"Unexpected bl_idname: {operator_type.bl_idname}"
        raise AssertionError(message)
    name = f"{split[0].encode().upper().decode()}_OT_{split[1]}"
    if type(operator).__qualname__ != name:
        raise AssertionError(
            f"{type(operator)} is not compatible with {operator_type}."
            + f"the expected name is {name}"
        )
    return cast(__Operator, operator)
