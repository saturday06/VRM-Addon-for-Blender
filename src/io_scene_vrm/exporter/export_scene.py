from collections.abc import Set as AbstractSet
from pathlib import Path
from typing import TYPE_CHECKING

import bpy
from bpy.app.translations import pgettext
from bpy.props import BoolProperty, CollectionProperty, StringProperty
from bpy.types import (
    Armature,
    Context,
    Event,
    Object,
    Operator,
    Panel,
    SpaceFileBrowser,
    UILayout,
)
from bpy_extras.io_utils import ExportHelper

from ..common import version
from ..common.logging import get_logger
from ..common.preferences import (
    copy_export_preferences,
    draw_export_preferences_layout,
    get_preferences,
)
from ..editor import search, validation
from ..editor.ops import VRM_OT_open_url_in_web_browser, layout_operator
from ..editor.property_group import CollectionPropertyProtocol, StringPropertyGroup
from ..editor.validation import VrmValidationError
from ..editor.vrm0.panel import (
    draw_vrm0_humanoid_operators_layout,
    draw_vrm0_humanoid_optional_bones_layout,
    draw_vrm0_humanoid_required_bones_layout,
)
from ..editor.vrm0.property_group import Vrm0HumanoidPropertyGroup
from ..editor.vrm1.ops import VRM_OT_assign_vrm1_humanoid_human_bones_automatically
from ..editor.vrm1.panel import (
    draw_vrm1_humanoid_optional_bones_layout,
    draw_vrm1_humanoid_required_bones_layout,
)
from ..editor.vrm1.property_group import Vrm1HumanBonesPropertyGroup
from .abstract_base_vrm_exporter import AbstractBaseVrmExporter
from .gltf2_addon_vrm_exporter import Gltf2AddonVrmExporter
from .legacy_vrm_exporter import LegacyVrmExporter
from .vrm_animation_exporter import VrmAnimationExporter

logger = get_logger(__name__)


def export_vrm_update_addon_preferences(
    export_op: "EXPORT_SCENE_OT_vrm", context: Context
) -> None:
    if export_op.use_addon_preferences:
        copy_export_preferences(source=export_op, destination=get_preferences(context))

    validation.WM_OT_vrm_validator.detect_errors(
        context,
        export_op.errors,
        export_op.armature_object_name,
    )


class EXPORT_SCENE_OT_vrm(Operator, ExportHelper):
    bl_idname = "export_scene.vrm"
    bl_label = "Export VRM"
    bl_description = "Export VRM"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    filename_ext = ".vrm"
    filter_glob: StringProperty(  # type: ignore[valid-type]
        default="*.vrm",
        options={"HIDDEN"},
    )

    use_addon_preferences: BoolProperty(  # type: ignore[valid-type]
        name="Export using add-on preferences",
        description="Export using add-on preferences instead of operator arguments",
    )
    export_invisibles: BoolProperty(  # type: ignore[valid-type]
        name="Export Invisible Objects",
        update=export_vrm_update_addon_preferences,
    )
    export_only_selections: BoolProperty(  # type: ignore[valid-type]
        name="Export Only Selections",
        update=export_vrm_update_addon_preferences,
    )
    enable_advanced_preferences: BoolProperty(  # type: ignore[valid-type]
        name="Enable Advanced Options",
        update=export_vrm_update_addon_preferences,
    )
    export_fb_ngon_encoding: BoolProperty(  # type: ignore[valid-type]
        name="Try the FB_ngon_encoding under development"
        + " (Exported meshes can be corrupted)",
        update=export_vrm_update_addon_preferences,
    )
    export_all_influences: BoolProperty(  # type: ignore[valid-type]
        name="Export All Bone Influences",
        description="Don't limit to 4, most viewers truncate to 4, "
        + "so bone movement may cause jagged meshes",
        update=export_vrm_update_addon_preferences,
        # The upstream says that Models may appear incorrectly in many viewers.
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/356b3dda976303d3ecce8b3bd1591245e576db38/addons/io_scene_gltf2/__init__.py#L760
        default=False,
    )
    export_lights: BoolProperty(  # type: ignore[valid-type]
        name="Export Lights",
    )

    errors: CollectionProperty(  # type: ignore[valid-type]
        type=validation.VrmValidationError,
        options={"HIDDEN"},
    )
    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    ignore_warning: BoolProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        if not self.filepath:
            return {"CANCELLED"}

        if self.use_addon_preferences:
            copy_export_preferences(source=get_preferences(context), destination=self)

        if bpy.ops.vrm.model_validate(
            "INVOKE_DEFAULT",
            show_successful_message=False,
            armature_object_name=self.armature_object_name,
        ) != {"FINISHED"}:
            return {"CANCELLED"}

        if self.enable_advanced_preferences:
            export_fb_ngon_encoding = self.export_fb_ngon_encoding
        else:
            export_fb_ngon_encoding = False

        export_objects = search.export_objects(
            context,
            self.armature_object_name,
            self.export_invisibles,
            self.export_only_selections,
            self.export_lights,
        )
        is_vrm1 = any(
            obj.type == "ARMATURE"
            and isinstance(obj.data, Armature)
            and obj.data.vrm_addon_extension.is_vrm1()
            for obj in export_objects
        )

        if is_vrm1:
            vrm_exporter: AbstractBaseVrmExporter = Gltf2AddonVrmExporter(
                context,
                export_objects,
                self.export_all_influences,
                self.export_lights,
            )
        else:
            vrm_exporter = LegacyVrmExporter(
                context,
                export_objects,
                export_fb_ngon_encoding,
            )

        vrm_bin = vrm_exporter.export_vrm()
        if vrm_bin is None:
            return {"CANCELLED"}
        Path(self.filepath).write_bytes(vrm_bin)
        return {"FINISHED"}

    def invoke(self, context: Context, event: Event) -> set[str]:
        self.use_addon_preferences = True
        copy_export_preferences(source=get_preferences(context), destination=self)

        if "gltf" not in dir(bpy.ops.export_scene):
            return bpy.ops.wm.vrm_gltf2_addon_disabled_warning(
                "INVOKE_DEFAULT",
            )

        export_objects = search.export_objects(
            context,
            self.armature_object_name,
            self.export_invisibles,
            self.export_only_selections,
            self.export_lights,
        )

        armatures = [obj for obj in export_objects if obj.type == "ARMATURE"]
        if len(armatures) > 1:
            return bpy.ops.wm.vrm_export_armature_selection("INVOKE_DEFAULT")
        if len(armatures) == 1:
            armature = armatures[0]
            armature_data = armature.data
            if not isinstance(armature_data, Armature):
                pass
            elif armature_data.vrm_addon_extension.is_vrm0():
                Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
                Vrm0HumanoidPropertyGroup.update_all_node_candidates(armature_data.name)
                humanoid = armature_data.vrm_addon_extension.vrm0.humanoid
                if all(
                    b.node.bone_name not in b.node_candidates
                    for b in humanoid.human_bones
                ):
                    bpy.ops.vrm.assign_vrm0_humanoid_human_bones_automatically(
                        armature_name=armature.name
                    )
                if not humanoid.all_required_bones_are_assigned():
                    return bpy.ops.wm.vrm_export_human_bones_assignment(
                        "INVOKE_DEFAULT",
                        armature_object_name=self.armature_object_name,
                    )
            elif armature_data.vrm_addon_extension.is_vrm1():
                Vrm1HumanBonesPropertyGroup.fixup_human_bones(armature)
                Vrm1HumanBonesPropertyGroup.update_all_node_candidates(
                    armature_data.name
                )
                human_bones = (
                    armature_data.vrm_addon_extension.vrm1.humanoid.human_bones
                )
                if all(
                    human_bone.node.bone_name not in human_bone.node_candidates
                    for human_bone in (
                        human_bones.human_bone_name_to_human_bone().values()
                    )
                ):
                    bpy.ops.vrm.assign_vrm1_humanoid_human_bones_automatically(
                        armature_name=armature.name
                    )
                if (
                    not human_bones.all_required_bones_are_assigned()
                    and not human_bones.allow_non_humanoid_rig
                ):
                    return bpy.ops.wm.vrm_export_human_bones_assignment(
                        "INVOKE_DEFAULT",
                        armature_object_name=self.armature_object_name,
                    )

        if bpy.ops.vrm.model_validate(
            "INVOKE_DEFAULT",
            show_successful_message=False,
            armature_object_name=self.armature_object_name,
        ) != {"FINISHED"}:
            return {"CANCELLED"}

        validation.WM_OT_vrm_validator.detect_errors(
            context,
            self.errors,
            self.armature_object_name,
        )
        if not self.ignore_warning and any(
            error.severity <= 1 for error in self.errors
        ):
            return bpy.ops.wm.vrm_export_confirmation(
                "INVOKE_DEFAULT", armature_object_name=self.armature_object_name
            )

        return ExportHelper.invoke(self, context, event)

    def draw(self, _context: Context) -> None:
        pass  # Is needed to get panels available

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run python tools/property_typing.py`
        filter_glob: str  # type: ignore[no-redef]
        use_addon_preferences: bool  # type: ignore[no-redef]
        export_invisibles: bool  # type: ignore[no-redef]
        export_only_selections: bool  # type: ignore[no-redef]
        enable_advanced_preferences: bool  # type: ignore[no-redef]
        export_fb_ngon_encoding: bool  # type: ignore[no-redef]
        export_all_influences: bool  # type: ignore[no-redef]
        export_lights: bool  # type: ignore[no-redef]
        errors: CollectionPropertyProtocol[  # type: ignore[no-redef]
            VrmValidationError
        ]
        armature_object_name: str  # type: ignore[no-redef]
        ignore_warning: bool  # type: ignore[no-redef]


class VRM_PT_export_file_browser_tool_props(Panel):
    bl_idname = "VRM_IMPORTER_PT_export_error_messages"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_parent_id = "FILE_PT_operator"
    bl_label = ""
    bl_options: AbstractSet[str] = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        space_data = context.space_data
        if not isinstance(space_data, SpaceFileBrowser):
            return False
        return space_data.active_operator.bl_idname == "EXPORT_SCENE_OT_vrm"

    def draw(self, context: Context) -> None:
        space_data = context.space_data
        if not isinstance(space_data, SpaceFileBrowser):
            return

        operator = space_data.active_operator
        if not isinstance(operator, EXPORT_SCENE_OT_vrm):
            return

        layout = self.layout

        warning_message = version.panel_warning_message()
        if warning_message:
            box = layout.box()
            warning_column = box.column(align=True)
            for index, warning_line in enumerate(warning_message.splitlines()):
                warning_column.label(
                    text=warning_line,
                    translate=False,
                    icon="NONE" if index else "ERROR",
                )

        draw_export_preferences_layout(operator, layout)

        if operator.errors:
            validation.WM_OT_vrm_validator.draw_errors(
                operator.errors, False, layout.box()
            )


class VRM_PT_export_vrma_help(Panel):
    bl_idname = "VRM_PT_export_vrma_help"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_parent_id = "FILE_PT_operator"
    bl_label = ""
    bl_options: AbstractSet[str] = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        space_data = context.space_data
        if not isinstance(space_data, SpaceFileBrowser):
            return False
        return space_data.active_operator.bl_idname == "EXPORT_SCENE_OT_vrma"

    def draw(self, _context: Context) -> None:
        draw_help_message(self.layout)


def menu_export(menu_op: Operator, _context: Context) -> None:
    vrm_export_op = layout_operator(
        menu_op.layout, EXPORT_SCENE_OT_vrm, text="VRM (.vrm)"
    )
    vrm_export_op.use_addon_preferences = True
    vrm_export_op.armature_object_name = ""
    vrm_export_op.ignore_warning = False

    vrma_export_op = layout_operator(
        menu_op.layout, EXPORT_SCENE_OT_vrma, text="VRM Animation (.vrma)"
    )
    vrma_export_op.armature_object_name = ""


class EXPORT_SCENE_OT_vrma(Operator, ExportHelper):
    bl_idname = "export_scene.vrma"
    bl_label = "Export VRM Animation"
    bl_description = "Export VRM Animation"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    filename_ext = ".vrma"
    filter_glob: StringProperty(  # type: ignore[valid-type]
        default="*.vrma",
        options={"HIDDEN"},
    )

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        if WM_OT_vrma_export_prerequisite.detect_errors(
            context, self.armature_object_name
        ):
            return {"CANCELLED"}
        if not self.filepath:
            return {"CANCELLED"}
        if not self.armature_object_name:
            armature = search.current_armature(context)
        else:
            armature = context.blend_data.objects.get(self.armature_object_name)
        if not armature:
            return {"CANCELLED"}
        return VrmAnimationExporter.execute(context, Path(self.filepath), armature)

    def invoke(self, context: Context, event: Event) -> set[str]:
        if WM_OT_vrma_export_prerequisite.detect_errors(
            context, self.armature_object_name
        ):
            return bpy.ops.wm.vrma_export_prerequisite(
                "INVOKE_DEFAULT",
                armature_object_name=self.armature_object_name,
            )
        return ExportHelper.invoke(self, context, event)

    def draw(self, _context: Context) -> None:
        pass  # Is needed to get panels available

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run python tools/property_typing.py`
        filter_glob: str  # type: ignore[no-redef]
        armature_object_name: str  # type: ignore[no-redef]


class WM_OT_vrm_export_human_bones_assignment(Operator):
    bl_label = "VRM Required Bones Assignment"
    bl_idname = "wm.vrm_export_human_bones_assignment"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        preferences = get_preferences(context)
        export_objects = search.export_objects(
            context,
            self.armature_object_name,
            preferences.export_invisibles,
            preferences.export_only_selections,
            preferences.export_lights,
        )
        armatures = [obj for obj in export_objects if obj.type == "ARMATURE"]
        if len(armatures) != 1:
            return {"CANCELLED"}
        armature = armatures[0]
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        if armature_data.vrm_addon_extension.is_vrm0():
            Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
            Vrm0HumanoidPropertyGroup.update_all_node_candidates(armature_data.name)
            humanoid = armature_data.vrm_addon_extension.vrm0.humanoid
            if not humanoid.all_required_bones_are_assigned():
                return {"CANCELLED"}
        elif armature_data.vrm_addon_extension.is_vrm1():
            Vrm1HumanBonesPropertyGroup.fixup_human_bones(armature)
            Vrm1HumanBonesPropertyGroup.update_all_node_candidates(armature_data.name)
            human_bones = armature_data.vrm_addon_extension.vrm1.humanoid.human_bones
            if (
                not human_bones.all_required_bones_are_assigned()
                and not human_bones.allow_non_humanoid_rig
            ):
                return {"CANCELLED"}
        else:
            return {"CANCELLED"}
        return bpy.ops.export_scene.vrm(
            "INVOKE_DEFAULT", armature_object_name=self.armature_object_name
        )

    def invoke(self, context: Context, _event: Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self, width=800)

    def draw(self, context: Context) -> None:
        preferences = get_preferences(context)
        armatures = [
            obj
            for obj in search.export_objects(
                context,
                self.armature_object_name,
                preferences.export_invisibles,
                preferences.export_only_selections,
                preferences.export_lights,
            )
            if obj.type == "ARMATURE"
        ]
        if not armatures:
            return
        armature = armatures[0]
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return

        if armature_data.vrm_addon_extension.is_vrm0():
            WM_OT_vrm_export_human_bones_assignment.draw_vrm0(self.layout, armature)
        elif armature_data.vrm_addon_extension.is_vrm1():
            WM_OT_vrm_export_human_bones_assignment.draw_vrm1(self.layout, armature)

    @staticmethod
    def draw_vrm0(layout: UILayout, armature: Object) -> None:
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return

        humanoid = armature_data.vrm_addon_extension.vrm0.humanoid
        if humanoid.all_required_bones_are_assigned():
            alert_box = layout.box()
            alert_box.label(
                text="All VRM Required Bones have been assigned.", icon="CHECKMARK"
            )
        else:
            alert_box = layout.box()
            alert_box.alert = True
            alert_box.label(
                text="There are unassigned VRM Required Bones. Please assign all.",
                icon="ERROR",
            )
        draw_vrm0_humanoid_operators_layout(armature, layout)
        row = layout.split(factor=0.5)
        draw_vrm0_humanoid_required_bones_layout(armature, row.column())
        draw_vrm0_humanoid_optional_bones_layout(armature, row.column())

    @staticmethod
    def draw_vrm1(layout: UILayout, armature: Object) -> None:
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return

        human_bones = armature_data.vrm_addon_extension.vrm1.humanoid.human_bones
        if human_bones.all_required_bones_are_assigned():
            alert_box = layout.box()
            alert_box.label(
                text="All VRM Required Bones have been assigned.", icon="CHECKMARK"
            )
        elif human_bones.allow_non_humanoid_rig:
            alert_box = layout.box()
            alert_box.label(
                text="This armature will be exported but not as humanoid."
                + " It can not have animations applied"
                + " for humanoid avatars.",
                icon="CHECKMARK",
            )
        else:
            alert_box = layout.box()
            alert_box.alert = True
            alert_column = alert_box.column(align=True)
            for error_message in human_bones.error_messages():
                alert_column.label(text=error_message, translate=False, icon="ERROR")

        layout_operator(
            layout,
            VRM_OT_assign_vrm1_humanoid_human_bones_automatically,
            icon="ARMATURE_DATA",
        ).armature_name = armature.name

        row = layout.split(factor=0.5)
        draw_vrm1_humanoid_required_bones_layout(human_bones, row.column())
        draw_vrm1_humanoid_optional_bones_layout(human_bones, row.column())

        non_humanoid_export_column = layout.column()
        non_humanoid_export_column.prop(human_bones, "allow_non_humanoid_rig")

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run python tools/property_typing.py`
        armature_object_name: str  # type: ignore[no-redef]


class WM_OT_vrm_export_confirmation(Operator):
    bl_label = "VRM Export Confirmation"
    bl_idname = "wm.vrm_export_confirmation"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    errors: CollectionProperty(type=validation.VrmValidationError)  # type: ignore[valid-type]

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    export_anyway: BoolProperty(  # type: ignore[valid-type]
        name="Export Anyway",
    )

    def execute(self, _context: Context) -> set[str]:
        if not self.export_anyway:
            return {"CANCELLED"}
        bpy.ops.export_scene.vrm(
            "INVOKE_DEFAULT",
            ignore_warning=True,
            armature_object_name=self.armature_object_name,
        )
        return {"FINISHED"}

    def invoke(self, context: Context, _event: Event) -> set[str]:
        validation.WM_OT_vrm_validator.detect_errors(
            context,
            self.errors,
            self.armature_object_name,
        )
        return context.window_manager.invoke_props_dialog(self, width=800)

    def draw(self, _context: Context) -> None:
        layout = self.layout
        layout.label(
            text="There is a high-impact warning. VRM may not export as intended.",
            icon="ERROR",
        )

        column = layout.column()
        for error in self.errors:
            if error.severity != 1:
                continue
            column.prop(
                error,
                "message",
                text="",
                translate=False,
            )

        layout.prop(self, "export_anyway")

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run python tools/property_typing.py`
        errors: CollectionPropertyProtocol[  # type: ignore[no-redef]
            VrmValidationError
        ]
        armature_object_name: str  # type: ignore[no-redef]
        export_anyway: bool  # type: ignore[no-redef]


class WM_OT_vrm_export_armature_selection(Operator):
    bl_label = "VRM Export Armature Selection"
    bl_idname = "wm.vrm_export_armature_selection"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    armature_object_name_candidates: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        if not self.armature_object_name:
            return {"CANCELLED"}
        armature_object = context.blend_data.objects.get(self.armature_object_name)
        if not armature_object or armature_object.type != "ARMATURE":
            return {"CANCELLED"}
        bpy.ops.export_scene.vrm(
            "INVOKE_DEFAULT", armature_object_name=self.armature_object_name
        )

        return {"FINISHED"}

    def invoke(self, context: Context, _event: Event) -> set[str]:
        if not self.armature_object_name:
            armature_object = search.current_armature(context)
            if armature_object:
                self.armature_object_name = armature_object.name
        self.armature_object_name_candidates.clear()
        for obj in context.blend_data.objects:
            if obj.type != "ARMATURE":
                continue
            candidate = self.armature_object_name_candidates.add()
            candidate.value = obj.name

        return context.window_manager.invoke_props_dialog(self, width=600)

    def draw(self, _context: Context) -> None:
        layout = self.layout
        layout.label(
            text="Multiple armatures were found; please select one to export as VRM.",
            icon="ERROR",
        )

        layout.prop_search(
            self,
            "armature_object_name",
            self,
            "armature_object_name_candidates",
            icon="OUTLINER_OB_ARMATURE",
            text="",
            translate=False,
        )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run python tools/property_typing.py`
        armature_object_name: str  # type: ignore[no-redef]
        armature_object_name_candidates: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]


class WM_OT_vrma_export_prerequisite(Operator):
    bl_label = "VRM Animation Export Prerequisite"
    bl_idname = "wm.vrma_export_prerequisite"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    armature_object_name_candidates: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup,
        options={"HIDDEN"},
    )

    @staticmethod
    def detect_errors(context: Context, armature_object_name: str) -> list[str]:
        error_messages = []

        if not armature_object_name:
            armature = search.current_armature(context)
        else:
            armature = context.blend_data.objects.get(armature_object_name)

        if not armature:
            error_messages.append(pgettext("Armature not found"))
            return error_messages

        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            error_messages.append(pgettext("Armature not found"))
            return error_messages

        ext = armature_data.vrm_addon_extension
        if armature_data.vrm_addon_extension.is_vrm1():
            humanoid = ext.vrm1.humanoid
            if not humanoid.human_bones.all_required_bones_are_assigned():
                error_messages.append(pgettext("Please assign required human bones"))
        else:
            error_messages.append(pgettext("Please set the version of VRM to 1.0"))

        return error_messages

    def execute(self, _context: Context) -> set[str]:
        return bpy.ops.export_scene.vrma(
            "INVOKE_DEFAULT", armature_object_name=self.armature_object_name
        )

    def invoke(self, context: Context, _event: Event) -> set[str]:
        if not self.armature_object_name:
            armature_object = search.current_armature(context)
            if armature_object:
                self.armature_object_name = armature_object.name
        self.armature_object_name_candidates.clear()
        for obj in context.blend_data.objects:
            if obj.type != "ARMATURE":
                continue
            candidate = self.armature_object_name_candidates.add()
            candidate.value = obj.name
        return context.window_manager.invoke_props_dialog(self, width=800)

    def draw(self, context: Context) -> None:
        layout = self.layout

        layout.label(
            text="VRM Animation export requires a VRM 1.0 armature",
            icon="INFO",
        )

        error_messages = WM_OT_vrma_export_prerequisite.detect_errors(
            context, self.armature_object_name
        )

        layout.prop_search(
            self,
            "armature_object_name",
            self,
            "armature_object_name_candidates",
            icon="OUTLINER_OB_ARMATURE",
            text="Armature to be exported",
        )

        if error_messages:
            error_column = layout.box().column(align=True)
            for error_message in error_messages:
                error_column.label(text=error_message, icon="ERROR", translate=False)

        if not self.armature_object_name:
            armature = search.current_armature(context)
        else:
            armature = context.blend_data.objects.get(self.armature_object_name)
        if armature:
            armature_data = armature.data
            if isinstance(armature_data, Armature):
                ext = armature_data.vrm_addon_extension
                if armature_data.vrm_addon_extension.is_vrm1():
                    humanoid = ext.vrm1.humanoid
                    if not humanoid.human_bones.all_required_bones_are_assigned():
                        WM_OT_vrm_export_human_bones_assignment.draw_vrm1(
                            self.layout, armature
                        )

        draw_help_message(layout)

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run python tools/property_typing.py`
        armature_object_name: str  # type: ignore[no-redef]
        armature_object_name_candidates: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]


def draw_help_message(layout: UILayout) -> None:
    help_message = pgettext(
        "Animations to be exported\n"
        + "- Humanoid bone rotations\n"
        + "- Humanoid hips bone translations\n"
        + "- Expression preview value\n"
        + "- Look At preview target translation\n"
    )
    help_box = layout.box()
    help_column = help_box.column(align=True)
    for index, help_line in enumerate(help_message.splitlines()):
        help_column.label(
            text=help_line,
            translate=False,
            icon="NONE" if index else "INFO",
        )

    open_op = layout_operator(
        help_column,
        VRM_OT_open_url_in_web_browser,
        icon="URL",
        text="Open help in a Web Browser",
    )
    open_op.url = pgettext("https://vrm-addon-for-blender.info/en/animation/")
