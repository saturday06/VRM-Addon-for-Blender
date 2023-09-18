from pathlib import Path
from typing import TYPE_CHECKING, cast

import bpy
from bpy.app.translations import pgettext
from bpy_extras.io_utils import ExportHelper

from ..common import version
from ..common.logging import get_logger
from ..common.preferences import get_preferences
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
    export_op: "EXPORT_SCENE_OT_vrm", context: bpy.types.Context
) -> None:
    preferences = get_preferences(context)

    changed = False

    if bool(preferences.export_invisibles) != bool(export_op.export_invisibles):
        preferences.export_invisibles = export_op.export_invisibles
        changed = True

    if bool(preferences.export_only_selections) != bool(
        export_op.export_only_selections
    ):
        preferences.export_only_selections = export_op.export_only_selections
        changed = True

    if bool(preferences.enable_advanced_preferences) != bool(
        export_op.enable_advanced_preferences
    ):
        preferences.enable_advanced_preferences = export_op.enable_advanced_preferences
        changed = True

    if bool(preferences.export_fb_ngon_encoding) != bool(
        export_op.export_fb_ngon_encoding
    ):
        preferences.export_fb_ngon_encoding = export_op.export_fb_ngon_encoding
        changed = True

    if changed:
        validation.WM_OT_vrm_validator.detect_errors(
            context,
            export_op.errors,
            export_op.armature_object_name,
        )


class EXPORT_SCENE_OT_vrm(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.vrm"
    bl_label = "Export VRM"
    bl_description = "Export VRM"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".vrm"
    filter_glob: bpy.props.StringProperty(  # type: ignore[valid-type]
        default="*.vrm", options={"HIDDEN"}  # noqa: F722,F821
    )

    export_invisibles: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export Invisible Objects",  # noqa: F722
        update=export_vrm_update_addon_preferences,
    )
    export_only_selections: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export Only Selections",  # noqa: F722
        update=export_vrm_update_addon_preferences,
    )
    enable_advanced_preferences: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Enable Advanced Options",  # noqa: F722
        update=export_vrm_update_addon_preferences,
    )
    export_fb_ngon_encoding: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Try the FB_ngon_encoding under development (Exported meshes can be corrupted)",  # noqa: F722
        update=export_vrm_update_addon_preferences,
    )
    errors: bpy.props.CollectionProperty(type=validation.VrmValidationError)  # type: ignore[valid-type]
    armature_object_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    ignore_warning: bpy.props.BoolProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not self.filepath:
            return {"CANCELLED"}

        if bpy.ops.vrm.model_validate(
            "INVOKE_DEFAULT",
            show_successful_message=False,
            armature_object_name=self.armature_object_name,
        ) != {"FINISHED"}:
            return {"CANCELLED"}

        preferences = get_preferences(context)
        export_invisibles = bool(preferences.export_invisibles)
        export_only_selections = bool(preferences.export_only_selections)
        if preferences.enable_advanced_preferences:
            export_fb_ngon_encoding = bool(preferences.export_fb_ngon_encoding)
        else:
            export_fb_ngon_encoding = False

        export_objects = search.export_objects(
            context,
            export_invisibles,
            export_only_selections,
            self.armature_object_name,
        )
        is_vrm1 = any(
            obj.type == "ARMATURE"
            and isinstance(obj.data, bpy.types.Armature)
            and obj.data.vrm_addon_extension.is_vrm1()
            for obj in export_objects
        )

        if is_vrm1:
            vrm_exporter: AbstractBaseVrmExporter = Gltf2AddonVrmExporter(
                context, export_objects
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

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        preferences = get_preferences(context)
        (
            self.export_invisibles,
            self.export_only_selections,
            self.enable_advanced_preferences,
            self.export_fb_ngon_encoding,
        ) = (
            bool(preferences.export_invisibles),
            bool(preferences.export_only_selections),
            bool(preferences.enable_advanced_preferences),
            bool(preferences.export_fb_ngon_encoding),
        )
        if "gltf" not in dir(bpy.ops.export_scene):
            return bpy.ops.wm.vrm_gltf2_addon_disabled_warning(
                "INVOKE_DEFAULT",
            )

        export_objects = search.export_objects(
            context,
            bool(self.export_invisibles),
            bool(self.export_only_selections),
            self.armature_object_name,
        )

        armatures = [obj for obj in export_objects if obj.type == "ARMATURE"]
        if len(armatures) > 1:
            return bpy.ops.wm.vrm_export_armature_selection("INVOKE_DEFAULT")
        if len(armatures) == 1:
            armature = armatures[0]
            armature_data = armature.data
            if not isinstance(armature_data, bpy.types.Armature):
                pass
            elif armature_data.vrm_addon_extension.is_vrm0():
                Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
                Vrm0HumanoidPropertyGroup.check_last_bone_names_and_update(
                    armature_data.name,
                    defer=False,
                )
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
                Vrm1HumanBonesPropertyGroup.check_last_bone_names_and_update(
                    armature_data.name,
                    defer=False,
                )
                human_bones = (
                    armature_data.vrm_addon_extension.vrm1.humanoid.human_bones
                )
                if all(
                    human_bone.node.bone_name not in human_bone.node_candidates
                    for human_bone in human_bones.human_bone_name_to_human_bone().values()
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

    def draw(self, _context: bpy.types.Context) -> None:
        pass  # Is needed to get panels available

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        filter_glob: str  # type: ignore[no-redef]
        export_invisibles: bool  # type: ignore[no-redef]
        export_only_selections: bool  # type: ignore[no-redef]
        enable_advanced_preferences: bool  # type: ignore[no-redef]
        export_fb_ngon_encoding: bool  # type: ignore[no-redef]
        errors: CollectionPropertyProtocol[VrmValidationError]  # type: ignore[no-redef]
        armature_object_name: str  # type: ignore[no-redef]
        ignore_warning: bool  # type: ignore[no-redef]


class VRM_PT_export_error_messages(bpy.types.Panel):
    bl_idname = "VRM_IMPORTER_PT_export_error_messages"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_parent_id = "FILE_PT_operator"
    bl_label = ""
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        space_data = context.space_data
        if not isinstance(space_data, bpy.types.SpaceFileBrowser):
            return False
        return space_data.active_operator.bl_idname == "EXPORT_SCENE_OT_vrm"

    def draw(self, context: bpy.types.Context) -> None:
        space_data = context.space_data
        if not isinstance(space_data, bpy.types.SpaceFileBrowser):
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

        operator = cast(EXPORT_SCENE_OT_vrm, space_data.active_operator)
        layout.prop(operator, "export_invisibles")
        layout.prop(operator, "export_only_selections")
        layout.prop(operator, "enable_advanced_preferences")
        if getattr(operator, "enable_advanced_preferences", False):
            advanced_options_box = layout.box()
            advanced_options_box.prop(operator, "export_fb_ngon_encoding")
        validation.WM_OT_vrm_validator.draw_errors(operator.errors, False, layout.box())


class VRM_PT_export_vrma_help(bpy.types.Panel):
    bl_idname = "VRM_PT_export_vrma_help"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_parent_id = "FILE_PT_operator"
    bl_label = ""
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        space_data = context.space_data
        if not isinstance(space_data, bpy.types.SpaceFileBrowser):
            return False
        return space_data.active_operator.bl_idname == "EXPORT_SCENE_OT_vrma"

    def draw(self, _context: bpy.types.Context) -> None:
        draw_help_message(self.layout)


def menu_export(menu_op: bpy.types.Operator, _context: bpy.types.Context) -> None:
    vrm_export_op = layout_operator(
        menu_op.layout, EXPORT_SCENE_OT_vrm, text="VRM (.vrm)"
    )
    vrm_export_op.armature_object_name = ""
    vrm_export_op.ignore_warning = False

    vrma_export_op = layout_operator(
        menu_op.layout, EXPORT_SCENE_OT_vrma, text="VRM Animation DRAFT (.vrma)"
    )
    vrma_export_op.armature_object_name = ""


class EXPORT_SCENE_OT_vrma(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.vrma"
    bl_label = "Export VRM Animation"
    bl_description = "Export VRM Animation"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".vrma"
    filter_glob: bpy.props.StringProperty(  # type: ignore[valid-type]
        default="*.vrma", options={"HIDDEN"}  # noqa: F722,F821
    )

    armature_object_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
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

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        if WM_OT_vrma_export_prerequisite.detect_errors(
            context, self.armature_object_name
        ):
            return bpy.ops.wm.vrma_export_prerequisite(
                "INVOKE_DEFAULT",
                armature_object_name=self.armature_object_name,
            )
        return ExportHelper.invoke(self, context, event)

    def draw(self, _context: bpy.types.Context) -> None:
        pass  # Is needed to get panels available

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        filter_glob: str  # type: ignore[no-redef]
        armature_object_name: str  # type: ignore[no-redef]


class WM_OT_vrm_export_human_bones_assignment(bpy.types.Operator):
    bl_label = "VRM Required Bones Assignment"
    bl_idname = "wm.vrm_export_human_bones_assignment"
    bl_options = {"REGISTER", "UNDO"}

    armature_object_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        preferences = get_preferences(context)
        export_invisibles = bool(preferences.export_invisibles)
        export_only_selections = bool(preferences.export_only_selections)
        export_objects = search.export_objects(
            context,
            export_invisibles,
            export_only_selections,
            self.armature_object_name,
        )
        armatures = [obj for obj in export_objects if obj.type == "ARMATURE"]
        if len(armatures) != 1:
            return {"CANCELLED"}
        armature = armatures[0]
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return {"CANCELLED"}
        if armature_data.vrm_addon_extension.is_vrm0():
            Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
            Vrm0HumanoidPropertyGroup.check_last_bone_names_and_update(
                armature_data.name,
                defer=False,
            )
            humanoid = armature_data.vrm_addon_extension.vrm0.humanoid
            if not humanoid.all_required_bones_are_assigned():
                return {"CANCELLED"}
        elif armature_data.vrm_addon_extension.is_vrm1():
            Vrm1HumanBonesPropertyGroup.fixup_human_bones(armature)
            Vrm1HumanBonesPropertyGroup.check_last_bone_names_and_update(
                armature_data.name,
                defer=False,
            )
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

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self, width=800)

    def draw(self, context: bpy.types.Context) -> None:
        preferences = get_preferences(context)
        export_invisibles = bool(preferences.export_invisibles)
        export_only_selections = bool(preferences.export_only_selections)

        armatures = [
            obj
            for obj in search.export_objects(
                context,
                export_invisibles,
                export_only_selections,
                self.armature_object_name,
            )
            if obj.type == "ARMATURE"
        ]
        if not armatures:
            return
        armature = armatures[0]
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return

        if armature_data.vrm_addon_extension.is_vrm0():
            WM_OT_vrm_export_human_bones_assignment.draw_vrm0(self.layout, armature)
        elif armature_data.vrm_addon_extension.is_vrm1():
            WM_OT_vrm_export_human_bones_assignment.draw_vrm1(self.layout, armature)

    @staticmethod
    def draw_vrm0(layout: bpy.types.UILayout, armature: bpy.types.Object) -> None:
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
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
    def draw_vrm1(layout: bpy.types.UILayout, armature: bpy.types.Object) -> None:
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
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
        # `poetry run ./scripts/property_typing.py`
        armature_object_name: str  # type: ignore[no-redef]


class WM_OT_vrm_export_confirmation(bpy.types.Operator):
    bl_label = "VRM Export Confirmation"
    bl_idname = "wm.vrm_export_confirmation"
    bl_options = {"REGISTER", "UNDO"}

    errors: bpy.props.CollectionProperty(type=validation.VrmValidationError)  # type: ignore[valid-type]

    armature_object_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    export_anyway: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export Anyway",  # noqa: F722
    )

    def execute(self, _context: bpy.types.Context) -> set[str]:
        if not self.export_anyway:
            return {"CANCELLED"}
        bpy.ops.export_scene.vrm(
            "INVOKE_DEFAULT",
            ignore_warning=True,
            armature_object_name=self.armature_object_name,
        )
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        validation.WM_OT_vrm_validator.detect_errors(
            context,
            self.errors,
            self.armature_object_name,
        )
        return context.window_manager.invoke_props_dialog(self, width=800)

    def draw(self, _context: bpy.types.Context) -> None:
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
        # `poetry run ./scripts/property_typing.py`
        errors: CollectionPropertyProtocol[VrmValidationError]  # type: ignore[no-redef]
        armature_object_name: str  # type: ignore[no-redef]
        export_anyway: bool  # type: ignore[no-redef]


class WM_OT_vrm_export_armature_selection(bpy.types.Operator):
    bl_label = "VRM Export Armature Selection"
    bl_idname = "wm.vrm_export_armature_selection"
    bl_options = {"REGISTER", "UNDO"}

    armature_object_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    armature_object_name_candidates: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup,
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not self.armature_object_name:
            return {"CANCELLED"}
        armature_object = context.blend_data.objects.get(self.armature_object_name)
        if not armature_object or armature_object.type != "ARMATURE":
            return {"CANCELLED"}
        bpy.ops.export_scene.vrm(
            "INVOKE_DEFAULT", armature_object_name=self.armature_object_name
        )

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
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

    def draw(self, _context: bpy.types.Context) -> None:
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
        # `poetry run ./scripts/property_typing.py`
        armature_object_name: str  # type: ignore[no-redef]
        armature_object_name_candidates: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]


class WM_OT_vrma_export_prerequisite(bpy.types.Operator):
    bl_label = "VRM Animation Export Prerequisite"
    bl_idname = "wm.vrma_export_prerequisite"
    bl_options = {"REGISTER", "UNDO"}

    armature_object_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    armature_object_name_candidates: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup,
        options={"HIDDEN"},  # noqa: F821
    )

    @staticmethod
    def detect_errors(
        context: bpy.types.Context, armature_object_name: str
    ) -> list[str]:
        error_messages = []

        if not armature_object_name:
            armature = search.current_armature(context)
        else:
            armature = context.blend_data.objects.get(armature_object_name)

        if not armature:
            error_messages.append(pgettext("Armature not found"))
            return error_messages

        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            error_messages.append(pgettext("Armature not found"))
            return error_messages

        ext = armature_data.vrm_addon_extension
        if armature_data.vrm_addon_extension.is_vrm1():
            humanoid = ext.vrm1.humanoid
            if not bool(humanoid.human_bones.all_required_bones_are_assigned()):
                error_messages.append(pgettext("Please assign required human bones"))
        else:
            error_messages.append(pgettext("Please set the version of VRM to 1.0"))

        return error_messages

    def execute(self, _context: bpy.types.Context) -> set[str]:
        return bpy.ops.export_scene.vrma(
            "INVOKE_DEFAULT", armature_object_name=self.armature_object_name
        )

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
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

    def draw(self, context: bpy.types.Context) -> None:
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
            if isinstance(armature_data, bpy.types.Armature):
                ext = armature_data.vrm_addon_extension
                if armature_data.vrm_addon_extension.is_vrm1():
                    humanoid = ext.vrm1.humanoid
                    if not bool(humanoid.human_bones.all_required_bones_are_assigned()):
                        WM_OT_vrm_export_human_bones_assignment.draw_vrm1(
                            self.layout, armature
                        )

        draw_help_message(layout)

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        armature_object_name: str  # type: ignore[no-redef]
        armature_object_name_candidates: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]


def draw_help_message(layout: bpy.types.UILayout) -> None:
    help_message = pgettext(
        "Animations to be exported\n"
        + "- Humanoid bone rotations\n"
        + "- Humanoid hips bone translations\n"
        + "- Expression preview value\n"
        + '- "Look At" value currently not supported\n'
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
