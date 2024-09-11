# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2018 iCyP

import json
import math
import re
import webbrowser
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from pathlib import Path
from sys import float_info
from typing import TYPE_CHECKING, Optional, TypeVar, Union, cast
from urllib.parse import urlparse

import bpy
from bpy.app.translations import pgettext
from bpy.props import StringProperty
from bpy.types import (
    Armature,
    Context,
    Event,
    Mesh,
    Object,
    Operator,
    PoseBone,
    UILayout,
)
from bpy_extras.io_utils import ExportHelper, ImportHelper
from mathutils import Quaternion, Vector

from ..common.deep import make_json
from ..common.vrm0.human_bone import HumanBoneName as Vrm0HumanBoneName
from ..common.vrm0.human_bone import HumanBoneSpecifications
from ..common.vrm1.human_bone import HumanBoneName as Vrm1HumanBoneName
from ..common.workspace import save_workspace
from . import search
from .extension import get_armature_extension
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
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}

        with save_workspace(context):
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

        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]


# deprecated
class VRM_OT_add_extensions_to_armature(Operator):
    bl_idname = "vrm.add_vrm_extensions"
    bl_label = "Add VRM attributes"
    bl_description = "Add VRM extensions & metas to armature"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    def execute(self, context: Context) -> set[str]:
        obj = context.view_layer.objects.active
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

    def execute(self, context: Context) -> set[str]:
        if self.armature_name not in context.blend_data.armatures:
            return {"CANCELLED"}
        armature = context.blend_data.armatures[self.armature_name]
        if self.bone_name not in armature:
            armature[self.bone_name] = ""
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
        bone_name: str  # type: ignore[no-redef]


# deprecated
class VRM_OT_add_required_human_bone_custom_property(Operator):
    bl_idname = "vrm.add_vrm_req_humanbone_prop"
    bl_label = "Add vrm human_bone_prop"
    bl_description = ""
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    def execute(self, context: Context) -> set[str]:
        obj = context.view_layer.objects.active
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
        obj = context.view_layer.objects.active
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
        for human_bone in get_armature_extension(
            armature_data
        ).vrm0.humanoid.human_bones:
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
        # To regenerate, run the `uv run tools/property_typing.py` command.
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

        obj = make_json(json.loads(Path(self.filepath).read_text(encoding="UTF-8")))
        if not isinstance(obj, dict):
            return {"CANCELLED"}

        for human_bone_name, bpy_bone_name in obj.items():
            if human_bone_name not in HumanBoneSpecifications.all_names:
                continue
            if not isinstance(bpy_bone_name, str):
                continue
            # INFO@MICROSOFT.COM
            found = False
            for human_bone in get_armature_extension(
                armature_data
            ).vrm0.humanoid.human_bones:
                if human_bone.bone == human_bone_name:
                    human_bone.node.set_bone_name(bpy_bone_name)
                    found = True
                    break
            if found:
                continue

            human_bone = get_armature_extension(
                armature_data
            ).vrm0.humanoid.human_bones.add()
            human_bone.bone = human_bone_name
            human_bone.node.set_bone_name(bpy_bone_name)

        return {"FINISHED"}

    def invoke(self, context: Context, event: Event) -> set[str]:
        return ImportHelper.invoke(self, context, event)

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
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
                    )  # Renamed since VRoid Studio 0.6.4
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
        return url.scheme in ["http", "https"]

    def execute(self, _context: Context) -> set[str]:
        url = self.url
        if not self.supported(url):
            return {"CANCELLED"}
        webbrowser.open(self.url)
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        url: str  # type: ignore[no-redef]


class VRM_OT_show_blend_file_compatibility_warning(Operator):
    bl_idname = "vrm.show_blend_file_compatibility_warning"
    bl_label = "File Compatibility Warning"
    bl_description = "Show Blend File Compatibility Warning"
    bl_options: AbstractSet[str] = {"REGISTER"}

    file_version: StringProperty(options={"HIDDEN"})  # type: ignore[valid-type]
    app_version: StringProperty(options={"HIDDEN"})  # type: ignore[valid-type]

    def execute(self, _context: Context) -> set[str]:
        return {"FINISHED"}

    def invoke(self, context: Context, _event: Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, _context: Context) -> None:
        column = self.layout.row(align=True).column()
        text = pgettext(
            "The current file is not compatible with the running Blender.\n"
            + "The current file was created in Blender {file_version}, but the running"
            + " Blender version is {app_version}.\n"
            + "So it is not compatible. As a result some data may be lost or corrupted."
        ).format(
            app_version=self.app_version,
            file_version=self.file_version,
        )
        description_outer_column = column.column()
        description_outer_column.emboss = "NONE"
        description_column = description_outer_column.box().column(align=True)
        for i, line in enumerate(text.splitlines()):
            icon = "ERROR" if i == 0 else "NONE"
            description_column.label(text=line, translate=False, icon=icon)
        open_url = layout_operator(
            self.layout,
            VRM_OT_open_url_in_web_browser,
            text="Open Documentation",
            icon="URL",
        )
        open_url.url = "https://developer.blender.org/docs/handbook/guidelines/compatibility_handling_for_blend_files/#forward-compatibility"

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        file_version: str  # type: ignore[no-redef]
        app_version: str  # type: ignore[no-redef]


class VRM_OT_show_blend_file_addon_compatibility_warning(Operator):
    bl_idname = "vrm.show_blend_file_addon_compatibility_warning"
    bl_label = "VRM Add-on Compatibility Warning"
    bl_description = "Show Blend File and VRM Add-on Compatibility Warning"
    bl_options: AbstractSet[str] = {"REGISTER"}

    file_addon_version: StringProperty(options={"HIDDEN"})  # type: ignore[valid-type]
    installed_addon_version: StringProperty(options={"HIDDEN"})  # type: ignore[valid-type]

    def execute(self, _context: Context) -> set[str]:
        return {"FINISHED"}

    def invoke(self, context: Context, _event: Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, _context: Context) -> None:
        column = self.layout.row(align=True).column()
        text = pgettext(
            "The current file is not compatible with the installed VRM Add-on.\n"
            + "The current file was created in VRM Add-on {file_addon_version}, but the"
            + " installed\n"
            + "VRM Add-on version is {installed_addon_version}. So it is not"
            + " compatible. As a result some\n"
            + "data may be lost or corrupted."
        ).format(
            file_addon_version=self.file_addon_version,
            installed_addon_version=self.installed_addon_version,
        )
        description_outer_column = column.column()
        description_outer_column.emboss = "NONE"
        description_column = description_outer_column.box().column(align=True)
        for i, line in enumerate(text.splitlines()):
            icon = "ERROR" if i == 0 else "NONE"
            description_column.label(text=line, translate=False, icon=icon)

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        file_addon_version: str  # type: ignore[no-redef]
        installed_addon_version: str  # type: ignore[no-redef]


__Operator = TypeVar("__Operator", bound=Operator)


def layout_operator(
    layout: UILayout,
    operator_type: type[__Operator],
    *,
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


@dataclass(frozen=True)
class ChainSingleChild:
    direction: Vector
    vrm0_human_bone_names: tuple[Vrm0HumanBoneName, ...]
    vrm1_human_bone_names: tuple[Vrm1HumanBoneName, ...]

    def execute(self, context: Context, armature: Object) -> None:
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            raise TypeError

        ext = get_armature_extension(armature_data)
        if ext.is_vrm0():
            humanoid = ext.vrm0.humanoid
            bones: list[PoseBone] = []
            for human_bone in humanoid.human_bones:
                human_bone_name = Vrm0HumanBoneName.from_str(human_bone.bone)
                if not human_bone_name:
                    continue
                if human_bone_name not in self.vrm0_human_bone_names:
                    continue
                bone = armature.pose.bones.get(human_bone.node.bone_name)
                if not bone:
                    continue
                bones.append(bone)
        else:
            human_bones = ext.vrm1.humanoid.human_bones
            human_bone_name_to_human_bone = human_bones.human_bone_name_to_human_bone()
            bones = [
                bone
                for bone in [
                    armature.pose.bones.get(human_bone.node.bone_name)
                    for human_bone in [
                        human_bone_name_to_human_bone.get(human_bone_name)
                        for human_bone_name in self.vrm1_human_bone_names
                    ]
                    if human_bone
                ]
                if bone
            ]

        if len(bones) < 2:
            return

        root_bone = bones[0]
        tip_bone = bones[-1]

        chained_bones: list[PoseBone] = []
        searching_bone: Optional[PoseBone] = tip_bone
        while True:
            if not searching_bone:
                return
            chained_bones.insert(0, searching_bone)
            if searching_bone == root_bone:
                break
            searching_bone = searching_bone.parent

        for bone, child_bone in zip(chained_bones, chained_bones[1:]):
            VRM_OT_make_estimated_humanoid_t_pose.set_bone_direction_to_align_child_bone(
                context, armature, self.direction, bone, child_bone
            )


@dataclass(frozen=True)
class ChainHorizontalMultipleChildren:
    direction: Vector
    vrm0_parent_human_bone_name: Vrm0HumanBoneName
    vrm0_human_bone_names: tuple[Vrm0HumanBoneName, ...]
    vrm1_parent_human_bone_name: Vrm1HumanBoneName
    vrm1_human_bone_names: tuple[Vrm1HumanBoneName, ...]

    def execute(self, context: Context, armature: Object) -> None:
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            raise TypeError

        ext = get_armature_extension(armature_data)
        if ext.is_vrm0():
            humanoid = ext.vrm0.humanoid
            bones: list[PoseBone] = []
            parent_bone: Optional[PoseBone] = None
            for human_bone in humanoid.human_bones:
                human_bone_name = Vrm0HumanBoneName.from_str(human_bone.bone)
                if not human_bone_name:
                    continue
                if human_bone_name == self.vrm0_parent_human_bone_name:
                    parent_bone = armature.pose.bones.get(human_bone.node.bone_name)
                elif human_bone_name in self.vrm0_human_bone_names:
                    bone = armature.pose.bones.get(human_bone.node.bone_name)
                    if bone:
                        bones.append(bone)
        else:
            human_bones = ext.vrm1.humanoid.human_bones
            human_bone_name_to_human_bone = human_bones.human_bone_name_to_human_bone()
            bones = [
                bone
                for bone in [
                    armature.pose.bones.get(human_bone.node.bone_name)
                    for human_bone in [
                        human_bone_name_to_human_bone.get(human_bone_name)
                        for human_bone_name in self.vrm1_human_bone_names
                    ]
                    if human_bone
                ]
                if bone
            ]
            parent_human_bone = human_bone_name_to_human_bone.get(
                self.vrm1_parent_human_bone_name
            )
            parent_bone = None
            if parent_human_bone:
                parent_bone = armature.pose.bones.get(parent_human_bone.node.bone_name)
        if not bones:
            return
        world_location = Vector((0, 0, 0))
        for bone in bones:
            world_location += (armature.matrix_world @ bone.matrix).to_translation()
        world_location /= len(bones)

        if not parent_bone:
            return

        VRM_OT_make_estimated_humanoid_t_pose.set_bone_direction_to_align_z_world_location(
            context, armature, self.direction, parent_bone, world_location
        )


class VRM_OT_make_estimated_humanoid_t_pose(Operator):
    bl_idname = "vrm.make_estimated_humanoid_t_pose"
    bl_label = "Make Estimated T-Pose"
    bl_description = "Make VRM Estimated Humanoid T-Pose"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    @staticmethod
    def set_bone_direction_to_align_child_bone(
        context: Context,
        armature: Object,
        direction: Vector,
        bone: PoseBone,
        child_bone: PoseBone,
    ) -> None:
        world_bone_matrix = armature.matrix_world @ bone.matrix
        world_child_bone_matrix = armature.matrix_world @ child_bone.matrix

        world_bone_length = (
            world_child_bone_matrix.translation - world_bone_matrix.translation
        ).length

        world_child_bone_from_translation = world_child_bone_matrix.translation
        world_child_bone_to_translation = (
            world_bone_matrix.translation + direction * world_bone_length
        )

        bone_local_child_bone_from_translation = (
            armature.matrix_world @ bone.matrix
        ).inverted_safe() @ world_child_bone_from_translation
        bone_local_child_bone_to_translation = (
            armature.matrix_world @ bone.matrix
        ).inverted_safe() @ world_child_bone_to_translation

        if bone_local_child_bone_from_translation.length_squared < float_info.epsilon:
            return
        if bone_local_child_bone_to_translation.length_squared < float_info.epsilon:
            return

        rotation = bone_local_child_bone_from_translation.rotation_difference(
            bone_local_child_bone_to_translation
        )

        if bone.rotation_mode != "QUATERNION":
            bone.rotation_mode = "QUATERNION"
        bone.rotation_quaternion = rotation @ bone.rotation_quaternion
        context.view_layer.update()

    @staticmethod
    def set_bone_direction_to_align_z_world_location(
        context: Context,
        armature: Object,
        direction: Vector,
        bone: PoseBone,
        from_world_location: Vector,
    ) -> None:
        world_bone_translation = (armature.matrix_world @ bone.matrix).to_translation()
        aligned_from_world_location = Vector(
            (
                from_world_location.x,
                world_bone_translation.y,
                from_world_location.z,
            )
        )
        aligned_to_world_location = world_bone_translation + direction

        bone_local_aligned_from_world_location = (
            armature.matrix_world @ bone.matrix
        ).inverted_safe() @ aligned_from_world_location
        bone_local_aligned_to_world_location = (
            armature.matrix_world @ bone.matrix
        ).inverted_safe() @ aligned_to_world_location

        if bone_local_aligned_from_world_location.length_squared < float_info.epsilon:
            return
        if bone_local_aligned_to_world_location.length_squared < float_info.epsilon:
            return

        rotation = bone_local_aligned_from_world_location.rotation_difference(
            bone_local_aligned_to_world_location
        )

        if bone.rotation_mode != "QUATERNION":
            bone.rotation_mode = "QUATERNION"
        bone.rotation_quaternion = rotation @ bone.rotation_quaternion
        context.view_layer.update()

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}

        ext = get_armature_extension(armature_data)
        if ext.is_vrm0():
            if not ext.vrm0.humanoid.all_required_bones_are_assigned():
                return {"CANCELLED"}
        else:
            human_bones = ext.vrm1.humanoid.human_bones
            if not human_bones.all_required_bones_are_assigned():
                return {"CANCELLED"}

        for bone in armature.pose.bones:
            bone.rotation_mode = "QUATERNION"
            bone.rotation_quaternion = Quaternion()
        context.view_layer.update()

        # https://github.com/vrm-c/vrm-specification/blob/73855bb77d431a3374212551a4fa48e043be3ced/specification/VRMC_vrm-1.0/tpose.md
        chains: tuple[Union[ChainSingleChild, ChainHorizontalMultipleChildren], ...] = (
            ChainSingleChild(
                Vector((-1, 0, 0)),
                (
                    Vrm0HumanBoneName.RIGHT_UPPER_ARM,
                    Vrm0HumanBoneName.RIGHT_LOWER_ARM,
                    Vrm0HumanBoneName.RIGHT_HAND,
                ),
                (
                    Vrm1HumanBoneName.RIGHT_UPPER_ARM,
                    Vrm1HumanBoneName.RIGHT_LOWER_ARM,
                    Vrm1HumanBoneName.RIGHT_HAND,
                ),
            ),
            ChainHorizontalMultipleChildren(
                Vector((-1, 0, 0)),
                Vrm0HumanBoneName.RIGHT_HAND,
                (
                    Vrm0HumanBoneName.RIGHT_INDEX_PROXIMAL,
                    Vrm0HumanBoneName.RIGHT_MIDDLE_PROXIMAL,
                    Vrm0HumanBoneName.RIGHT_RING_PROXIMAL,
                    Vrm0HumanBoneName.RIGHT_LITTLE_PROXIMAL,
                ),
                Vrm1HumanBoneName.RIGHT_HAND,
                (
                    Vrm1HumanBoneName.RIGHT_INDEX_PROXIMAL,
                    Vrm1HumanBoneName.RIGHT_MIDDLE_PROXIMAL,
                    Vrm1HumanBoneName.RIGHT_RING_PROXIMAL,
                    Vrm1HumanBoneName.RIGHT_LITTLE_PROXIMAL,
                ),
            ),
            ChainSingleChild(
                Vector((-math.sqrt(0.5), -math.sqrt(0.5), 0)),
                (
                    Vrm0HumanBoneName.RIGHT_THUMB_PROXIMAL,
                    Vrm0HumanBoneName.RIGHT_THUMB_INTERMEDIATE,
                    Vrm0HumanBoneName.RIGHT_THUMB_DISTAL,
                ),
                (
                    Vrm1HumanBoneName.RIGHT_THUMB_METACARPAL,
                    Vrm1HumanBoneName.RIGHT_THUMB_PROXIMAL,
                    Vrm1HumanBoneName.RIGHT_THUMB_DISTAL,
                ),
            ),
            ChainSingleChild(
                Vector((-1, 0, 0)),
                (
                    Vrm0HumanBoneName.RIGHT_INDEX_PROXIMAL,
                    Vrm0HumanBoneName.RIGHT_INDEX_INTERMEDIATE,
                    Vrm0HumanBoneName.RIGHT_INDEX_DISTAL,
                ),
                (
                    Vrm1HumanBoneName.RIGHT_INDEX_PROXIMAL,
                    Vrm1HumanBoneName.RIGHT_INDEX_INTERMEDIATE,
                    Vrm1HumanBoneName.RIGHT_INDEX_DISTAL,
                ),
            ),
            ChainSingleChild(
                Vector((-1, 0, 0)),
                (
                    Vrm0HumanBoneName.RIGHT_MIDDLE_PROXIMAL,
                    Vrm0HumanBoneName.RIGHT_MIDDLE_INTERMEDIATE,
                    Vrm0HumanBoneName.RIGHT_MIDDLE_DISTAL,
                ),
                (
                    Vrm1HumanBoneName.RIGHT_MIDDLE_PROXIMAL,
                    Vrm1HumanBoneName.RIGHT_MIDDLE_INTERMEDIATE,
                    Vrm1HumanBoneName.RIGHT_MIDDLE_DISTAL,
                ),
            ),
            ChainSingleChild(
                Vector((-1, 0, 0)),
                (
                    Vrm0HumanBoneName.RIGHT_RING_PROXIMAL,
                    Vrm0HumanBoneName.RIGHT_RING_INTERMEDIATE,
                    Vrm0HumanBoneName.RIGHT_RING_DISTAL,
                ),
                (
                    Vrm1HumanBoneName.RIGHT_RING_PROXIMAL,
                    Vrm1HumanBoneName.RIGHT_RING_INTERMEDIATE,
                    Vrm1HumanBoneName.RIGHT_RING_DISTAL,
                ),
            ),
            ChainSingleChild(
                Vector((-1, 0, 0)),
                (
                    Vrm0HumanBoneName.RIGHT_LITTLE_PROXIMAL,
                    Vrm0HumanBoneName.RIGHT_LITTLE_INTERMEDIATE,
                    Vrm0HumanBoneName.RIGHT_LITTLE_DISTAL,
                ),
                (
                    Vrm1HumanBoneName.RIGHT_LITTLE_PROXIMAL,
                    Vrm1HumanBoneName.RIGHT_LITTLE_INTERMEDIATE,
                    Vrm1HumanBoneName.RIGHT_LITTLE_DISTAL,
                ),
            ),
            ChainSingleChild(
                Vector((0, 0, -1)),
                (
                    Vrm0HumanBoneName.RIGHT_UPPER_LEG,
                    Vrm0HumanBoneName.RIGHT_LOWER_LEG,
                    Vrm0HumanBoneName.RIGHT_FOOT,
                ),
                (
                    Vrm1HumanBoneName.RIGHT_UPPER_LEG,
                    Vrm1HumanBoneName.RIGHT_LOWER_LEG,
                    Vrm1HumanBoneName.RIGHT_FOOT,
                ),
            ),
            ChainSingleChild(
                Vector((1, 0, 0)),
                (
                    Vrm0HumanBoneName.LEFT_UPPER_ARM,
                    Vrm0HumanBoneName.LEFT_LOWER_ARM,
                    Vrm0HumanBoneName.LEFT_HAND,
                ),
                (
                    Vrm1HumanBoneName.LEFT_UPPER_ARM,
                    Vrm1HumanBoneName.LEFT_LOWER_ARM,
                    Vrm1HumanBoneName.LEFT_HAND,
                ),
            ),
            ChainHorizontalMultipleChildren(
                Vector((1, 0, 0)),
                Vrm0HumanBoneName.LEFT_HAND,
                (
                    Vrm0HumanBoneName.LEFT_INDEX_PROXIMAL,
                    Vrm0HumanBoneName.LEFT_MIDDLE_PROXIMAL,
                    Vrm0HumanBoneName.LEFT_RING_PROXIMAL,
                    Vrm0HumanBoneName.LEFT_LITTLE_PROXIMAL,
                ),
                Vrm1HumanBoneName.LEFT_HAND,
                (
                    Vrm1HumanBoneName.LEFT_INDEX_PROXIMAL,
                    Vrm1HumanBoneName.LEFT_MIDDLE_PROXIMAL,
                    Vrm1HumanBoneName.LEFT_RING_PROXIMAL,
                    Vrm1HumanBoneName.LEFT_LITTLE_PROXIMAL,
                ),
            ),
            ChainSingleChild(
                Vector((math.sqrt(0.5), -math.sqrt(0.5), 0)),
                (
                    Vrm0HumanBoneName.LEFT_THUMB_PROXIMAL,
                    Vrm0HumanBoneName.LEFT_THUMB_INTERMEDIATE,
                    Vrm0HumanBoneName.LEFT_THUMB_DISTAL,
                ),
                (
                    Vrm1HumanBoneName.LEFT_THUMB_METACARPAL,
                    Vrm1HumanBoneName.LEFT_THUMB_PROXIMAL,
                    Vrm1HumanBoneName.LEFT_THUMB_DISTAL,
                ),
            ),
            ChainSingleChild(
                Vector((1, 0, 0)),
                (
                    Vrm0HumanBoneName.LEFT_INDEX_PROXIMAL,
                    Vrm0HumanBoneName.LEFT_INDEX_INTERMEDIATE,
                    Vrm0HumanBoneName.LEFT_INDEX_DISTAL,
                ),
                (
                    Vrm1HumanBoneName.LEFT_INDEX_PROXIMAL,
                    Vrm1HumanBoneName.LEFT_INDEX_INTERMEDIATE,
                    Vrm1HumanBoneName.LEFT_INDEX_DISTAL,
                ),
            ),
            ChainSingleChild(
                Vector((1, 0, 0)),
                (
                    Vrm0HumanBoneName.LEFT_MIDDLE_PROXIMAL,
                    Vrm0HumanBoneName.LEFT_MIDDLE_INTERMEDIATE,
                    Vrm0HumanBoneName.LEFT_MIDDLE_DISTAL,
                ),
                (
                    Vrm1HumanBoneName.LEFT_MIDDLE_PROXIMAL,
                    Vrm1HumanBoneName.LEFT_MIDDLE_INTERMEDIATE,
                    Vrm1HumanBoneName.LEFT_MIDDLE_DISTAL,
                ),
            ),
            ChainSingleChild(
                Vector((1, 0, 0)),
                (
                    Vrm0HumanBoneName.LEFT_RING_PROXIMAL,
                    Vrm0HumanBoneName.LEFT_RING_INTERMEDIATE,
                    Vrm0HumanBoneName.LEFT_RING_DISTAL,
                ),
                (
                    Vrm1HumanBoneName.LEFT_RING_PROXIMAL,
                    Vrm1HumanBoneName.LEFT_RING_INTERMEDIATE,
                    Vrm1HumanBoneName.LEFT_RING_DISTAL,
                ),
            ),
            ChainSingleChild(
                Vector((1, 0, 0)),
                (
                    Vrm0HumanBoneName.LEFT_LITTLE_PROXIMAL,
                    Vrm0HumanBoneName.LEFT_LITTLE_INTERMEDIATE,
                    Vrm0HumanBoneName.LEFT_LITTLE_DISTAL,
                ),
                (
                    Vrm1HumanBoneName.LEFT_LITTLE_PROXIMAL,
                    Vrm1HumanBoneName.LEFT_LITTLE_INTERMEDIATE,
                    Vrm1HumanBoneName.LEFT_LITTLE_DISTAL,
                ),
            ),
            ChainSingleChild(
                Vector((0, 0, -1)),
                (
                    Vrm0HumanBoneName.LEFT_UPPER_LEG,
                    Vrm0HumanBoneName.LEFT_LOWER_LEG,
                    Vrm0HumanBoneName.LEFT_FOOT,
                ),
                (
                    Vrm1HumanBoneName.LEFT_UPPER_LEG,
                    Vrm1HumanBoneName.LEFT_LOWER_LEG,
                    Vrm1HumanBoneName.LEFT_FOOT,
                ),
            ),
        )
        for chain in chains:
            chain.execute(context, armature)

        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_name: str  # type: ignore[no-redef]
