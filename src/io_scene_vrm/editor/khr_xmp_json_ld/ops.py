# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import TYPE_CHECKING, ClassVar

from bpy.props import IntProperty, StringProperty
from bpy.types import (
    Armature,
    Context,
    Operator,
)

from ...common.logger import get_logger
from ..extension import get_armature_extension

logger = get_logger(__name__)


class VRM_OT_add_khr_xmp_json_ld_packet_dc_creator(Operator):
    bl_idname = "vrm.add_khr_xmp_json_ld_packet_dc_creator"
    bl_label = "Add Creator"
    bl_description = "Add Creator"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        packet = get_armature_extension(
            armature_data
        ).khr_character.khr_xmp_json_ld_packet
        dc_creator = packet.dc_creator.add()
        dc_creator.value = ""
        packet.active_dc_creator_index = len(packet.dc_creator) - 1
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]


class VRM_OT_remove_khr_xmp_json_ld_packet_dc_creator(Operator):
    bl_idname = "vrm.remove_khr_xmp_json_ld_packet_dc_creator"
    bl_label = "Remove Creator"
    bl_description = "Remove Creator"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    dc_creator_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        packet = get_armature_extension(
            armature_data
        ).khr_character.khr_xmp_json_ld_packet
        if len(packet.dc_creator) <= self.dc_creator_index:
            return {"CANCELLED"}
        packet.dc_creator.remove(self.dc_creator_index)
        packet.active_dc_creator_index = min(
            packet.active_dc_creator_index,
            max(0, len(packet.dc_creator) - 1),
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        dc_creator_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_khr_xmp_json_ld_packet_dc_creator(Operator):
    bl_idname = "vrm.move_up_khr_xmp_json_ld_packet_dc_creator"
    bl_label = "Move Up Creator"
    bl_description = "Move Up Creator"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    dc_creator_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        packet = get_armature_extension(
            armature_data
        ).khr_character.khr_xmp_json_ld_packet
        if len(packet.dc_creator) <= self.dc_creator_index:
            return {"CANCELLED"}
        new_index = (self.dc_creator_index - 1) % len(packet.dc_creator)
        packet.dc_creator.move(self.dc_creator_index, new_index)
        packet.active_dc_creator_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        dc_creator_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_khr_xmp_json_ld_packet_dc_creator(Operator):
    bl_idname = "vrm.move_down_khr_xmp_json_ld_packet_dc_creator"
    bl_label = "Move Down Creator"
    bl_description = "Move Down Creator"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    dc_creator_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        packet = get_armature_extension(
            armature_data
        ).khr_character.khr_xmp_json_ld_packet
        if len(packet.dc_creator) <= self.dc_creator_index:
            return {"CANCELLED"}
        new_index = (self.dc_creator_index + 1) % len(packet.dc_creator)
        packet.dc_creator.move(self.dc_creator_index, new_index)
        packet.active_dc_creator_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        dc_creator_index: int  # type: ignore[no-redef]


class VRM_OT_add_khr_xmp_json_ld_packet_dc_license(Operator):
    bl_idname = "vrm.add_khr_xmp_json_ld_packet_dc_license"
    bl_label = "Add License"
    bl_description = "Add License"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        packet = get_armature_extension(
            armature_data
        ).khr_character.khr_xmp_json_ld_packet
        dc_license = packet.dc_license.add()
        dc_license.value = ""
        packet.active_dc_license_index = len(packet.dc_license) - 1
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]


class VRM_OT_remove_khr_xmp_json_ld_packet_dc_license(Operator):
    bl_idname = "vrm.remove_khr_xmp_json_ld_packet_dc_license"
    bl_label = "Remove License"
    bl_description = "Remove License"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    dc_license_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        packet = get_armature_extension(
            armature_data
        ).khr_character.khr_xmp_json_ld_packet
        if len(packet.dc_license) <= self.dc_license_index:
            return {"CANCELLED"}
        packet.dc_license.remove(self.dc_license_index)
        packet.active_dc_license_index = min(
            packet.active_dc_license_index,
            max(0, len(packet.dc_license) - 1),
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        dc_license_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_khr_xmp_json_ld_packet_dc_license(Operator):
    bl_idname = "vrm.move_up_khr_xmp_json_ld_packet_dc_license"
    bl_label = "Move Up License"
    bl_description = "Move Up License"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    dc_license_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        packet = get_armature_extension(
            armature_data
        ).khr_character.khr_xmp_json_ld_packet
        if len(packet.dc_license) <= self.dc_license_index:
            return {"CANCELLED"}
        new_index = (self.dc_license_index - 1) % len(packet.dc_license)
        packet.dc_license.move(self.dc_license_index, new_index)
        packet.active_dc_license_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        dc_license_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_khr_xmp_json_ld_packet_dc_license(Operator):
    bl_idname = "vrm.move_down_khr_xmp_json_ld_packet_dc_license"
    bl_label = "Move Down License"
    bl_description = "Move Down License"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    dc_license_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        packet = get_armature_extension(
            armature_data
        ).khr_character.khr_xmp_json_ld_packet
        if len(packet.dc_license) <= self.dc_license_index:
            return {"CANCELLED"}
        new_index = (self.dc_license_index + 1) % len(packet.dc_license)
        packet.dc_license.move(self.dc_license_index, new_index)
        packet.active_dc_license_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        dc_license_index: int  # type: ignore[no-redef]


class VRM_OT_add_khr_xmp_json_ld_packet_dc_subject(Operator):
    bl_idname = "vrm.add_khr_xmp_json_ld_packet_dc_subject"
    bl_label = "Add Subject"
    bl_description = "Add Subject"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        packet = get_armature_extension(
            armature_data
        ).khr_character.khr_xmp_json_ld_packet
        dc_subject = packet.dc_subject.add()
        dc_subject.value = ""
        packet.active_dc_subject_index = len(packet.dc_subject) - 1
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]


class VRM_OT_remove_khr_xmp_json_ld_packet_dc_subject(Operator):
    bl_idname = "vrm.remove_khr_xmp_json_ld_packet_dc_subject"
    bl_label = "Remove Subject"
    bl_description = "Remove Subject"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    dc_subject_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        packet = get_armature_extension(
            armature_data
        ).khr_character.khr_xmp_json_ld_packet
        if len(packet.dc_subject) <= self.dc_subject_index:
            return {"CANCELLED"}
        packet.dc_subject.remove(self.dc_subject_index)
        packet.active_dc_subject_index = min(
            packet.active_dc_subject_index,
            max(0, len(packet.dc_subject) - 1),
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        dc_subject_index: int  # type: ignore[no-redef]


class VRM_OT_move_up_khr_xmp_json_ld_packet_dc_subject(Operator):
    bl_idname = "vrm.move_up_khr_xmp_json_ld_packet_dc_subject"
    bl_label = "Move Up Subject"
    bl_description = "Move Up Subject"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    dc_subject_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        packet = get_armature_extension(
            armature_data
        ).khr_character.khr_xmp_json_ld_packet
        if len(packet.dc_subject) <= self.dc_subject_index:
            return {"CANCELLED"}
        new_index = (self.dc_subject_index - 1) % len(packet.dc_subject)
        packet.dc_subject.move(self.dc_subject_index, new_index)
        packet.active_dc_subject_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        dc_subject_index: int  # type: ignore[no-redef]


class VRM_OT_move_down_khr_xmp_json_ld_packet_dc_subject(Operator):
    bl_idname = "vrm.move_down_khr_xmp_json_ld_packet_dc_subject"
    bl_label = "Move Down Subject"
    bl_description = "Move Down Subject"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    dc_subject_index: IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        min=0,
    )

    def execute(self, context: Context) -> set[str]:
        armature = context.blend_data.objects.get(self.armature_object_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        packet = get_armature_extension(
            armature_data
        ).khr_character.khr_xmp_json_ld_packet
        if len(packet.dc_subject) <= self.dc_subject_index:
            return {"CANCELLED"}
        new_index = (self.dc_subject_index + 1) % len(packet.dc_subject)
        packet.dc_subject.move(self.dc_subject_index, new_index)
        packet.active_dc_subject_index = new_index
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        dc_subject_index: int  # type: ignore[no-redef]
