from typing import Set, cast

import bpy
from bpy.app.translations import pgettext
from bpy_extras.io_utils import ExportHelper

from ..common import version
from ..common.preferences import get_preferences, use_legacy_importer_exporter
from ..editor import search, validation
from ..editor.vrm0.panel import (
    draw_vrm0_humanoid_operators_layout,
    draw_vrm0_humanoid_required_bones_layout,
)
from ..editor.vrm0.property_group import Vrm0HumanoidPropertyGroup
from .abstract_base_vrm_exporter import AbstractBaseVrmExporter
from .gltf2_addon_vrm_exporter import Gltf2AddonVrmExporter
from .legacy_vrm_exporter import LegacyVrmExporter


def export_vrm_update_addon_preferences(
    export_op: bpy.types.Operator, context: bpy.types.Context
) -> None:
    preferences = get_preferences(context)
    if not preferences:
        return

    changed = False

    if bool(preferences.export_invisibles) != bool(export_op.export_invisibles):
        preferences.export_invisibles = export_op.export_invisibles
        changed = True

    if bool(preferences.export_only_selections) != bool(
        export_op.export_only_selections
    ):
        preferences.export_only_selections = export_op.export_only_selections
        changed = True

    if bool(preferences.export_fb_ngon_encoding) != bool(
        export_op.export_fb_ngon_encoding
    ):
        preferences.export_fb_ngon_encoding = export_op.export_fb_ngon_encoding
        changed = True

    if changed:
        validation.WM_OT_vrm_validator.detect_errors(context, export_op.errors)


class EXPORT_SCENE_OT_vrm(bpy.types.Operator, ExportHelper):  # type: ignore[misc] # noqa: N801
    bl_idname = "export_scene.vrm"
    bl_label = "Export VRM"
    bl_description = "Export VRM"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".vrm"
    filter_glob: bpy.props.StringProperty(  # type: ignore[valid-type]
        default="*.vrm", options={"HIDDEN"}  # noqa: F722,F821
    )

    # vrm_version : bpy.props.EnumProperty(name="VRM version" ,items=(("0.0","0.0",""),("1.0","1.0","")))
    export_invisibles: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export Invisible Objects",  # noqa: F722
        update=export_vrm_update_addon_preferences,
    )
    export_only_selections: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export Only Selections",  # noqa: F722
        update=export_vrm_update_addon_preferences,
    )
    export_fb_ngon_encoding: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Try the FB_ngon_encoding under development (Exported meshes can be corrupted)",  # noqa: F722
        update=export_vrm_update_addon_preferences,
    )

    errors: bpy.props.CollectionProperty(type=validation.VrmValidationError)  # type: ignore[valid-type]

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if not self.filepath:
            return {"CANCELLED"}
        filepath: str = self.filepath

        if bpy.ops.vrm.model_validate(
            "INVOKE_DEFAULT", show_successful_message=False
        ) != {"FINISHED"}:
            return {"CANCELLED"}

        preferences = get_preferences(context)
        if preferences:
            export_invisibles = bool(preferences.export_invisibles)
            export_only_selections = bool(preferences.export_only_selections)
            export_fb_ngon_encoding = bool(preferences.export_fb_ngon_encoding)
        else:
            export_invisibles = False
            export_only_selections = False
            export_fb_ngon_encoding = False

        export_objects = search.export_objects(
            context, export_invisibles, export_only_selections
        )
        is_vrm1 = any(
            obj.type == "ARMATURE" and obj.data.vrm_addon_extension.is_vrm1()
            for obj in export_objects
        )

        if is_vrm1:
            vrm_exporter: AbstractBaseVrmExporter = Gltf2AddonVrmExporter(
                context, export_objects
            )
        else:
            vrm_exporter = LegacyVrmExporter(
                context, export_objects, export_fb_ngon_encoding
            )

        vrm_bin = vrm_exporter.export_vrm()
        if vrm_bin is None:
            return {"CANCELLED"}
        with open(filepath, "wb") as f:
            f.write(vrm_bin)
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        preferences = get_preferences(context)
        if preferences:
            (
                self.export_invisibles,
                self.export_only_selections,
                self.export_fb_ngon_encoding,
            ) = (
                bool(preferences.export_invisibles),
                bool(preferences.export_only_selections),
                bool(preferences.export_fb_ngon_encoding),
            )
        if not use_legacy_importer_exporter() and "gltf" not in dir(
            bpy.ops.export_scene
        ):
            return cast(
                Set[str],
                bpy.ops.wm.vrm_gltf2_addon_disabled_warning(
                    "INVOKE_DEFAULT",
                ),
            )

        export_objects = search.export_objects(
            context, bool(self.export_invisibles), bool(self.export_only_selections)
        )

        armatures = [obj for obj in export_objects if obj.type == "ARMATURE"]
        is_vrm0 = any(
            armature.data.vrm_addon_extension.is_vrm0() for armature in armatures
        )
        if len(armatures) == 1 and is_vrm0:
            armature = armatures[0]
            Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
            Vrm0HumanoidPropertyGroup.check_last_bone_names_and_update(
                armature.data.name,
                defer=False,
            )
            humanoid = armature.data.vrm_addon_extension.vrm0.humanoid
            if all(b.node.value not in b.node_candidates for b in humanoid.human_bones):
                bpy.ops.vrm.assign_vrm0_humanoid_human_bones_automatically(
                    armature_name=armature.name
                )
            if not humanoid.all_required_bones_are_assigned():
                bpy.ops.wm.vrm_export_human_bones_assignment("INVOKE_DEFAULT")
                return {"CANCELLED"}

        if bpy.ops.vrm.model_validate(
            "INVOKE_DEFAULT", show_successful_message=False
        ) != {"FINISHED"}:
            return {"CANCELLED"}

        validation.WM_OT_vrm_validator.detect_errors(context, self.errors)
        return cast(Set[str], ExportHelper.invoke(self, context, event))

    def draw(self, _context: bpy.types.Context) -> None:
        pass  # Is needed to get panels available


class VRM_PT_export_error_messages(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_IMPORTER_PT_export_error_messages"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_parent_id = "FILE_PT_operator"
    bl_label = ""
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return (
            str(context.space_data.active_operator.bl_idname) == "EXPORT_SCENE_OT_vrm"
        )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        if not version.supported():
            box = layout.box()
            warning_column = box.column()
            warning_message = pgettext(
                "The installed VRM add-on is\nnot compatible with Blender {blender_version}.\n"
                + "Please upgrade the add-on."
            ).format(blender_version=".".join(map(str, bpy.app.version[:2])))
            for index, warning_line in enumerate(warning_message.splitlines()):
                warning_column.label(
                    text=warning_line,
                    translate=False,
                    icon="NONE" if index else "ERROR",
                )

        operator = context.space_data.active_operator

        layout.prop(operator, "export_invisibles")
        layout.prop(operator, "export_only_selections")

        preferences = get_preferences(context)
        if preferences and preferences.show_experimental_features:
            layout.prop(operator, "export_fb_ngon_encoding")

        if operator.errors:
            validation.WM_OT_vrm_validator.draw_errors(
                operator.errors, False, layout.box()
            )


def menu_export(export_op: bpy.types.Operator, _context: bpy.types.Context) -> None:
    export_op.layout.operator(EXPORT_SCENE_OT_vrm.bl_idname, text="VRM (.vrm)")


class WM_OT_export_human_bones_assignment(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_label = "VRM Required Bones Assignment"
    bl_idname = "wm.vrm_export_human_bones_assignment"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        preferences = get_preferences(context)
        if preferences:
            export_invisibles = bool(preferences.export_invisibles)
            export_only_selections = bool(preferences.export_only_selections)
        else:
            export_invisibles = False
            export_only_selections = False
        export_objects = search.export_objects(
            context, export_invisibles, export_only_selections
        )
        armatures = [obj for obj in export_objects if obj.type == "ARMATURE"]
        if len(armatures) != 1:
            return {"CANCELLED"}
        armature = armatures[0]
        if not armature.data.vrm_addon_extension.is_vrm0():
            return {"CANCELLED"}
        Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
        Vrm0HumanoidPropertyGroup.check_last_bone_names_and_update(
            armature.data.name,
            defer=False,
        )
        humanoid = armature.data.vrm_addon_extension.vrm0.humanoid
        if not humanoid.all_required_bones_are_assigned():
            return {"CANCELLED"}
        bpy.ops.export_scene.vrm("INVOKE_DEFAULT")
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> Set[str]:
        return cast(
            Set[str], context.window_manager.invoke_props_dialog(self, width=550)
        )

    def draw(self, context: bpy.types.Context) -> None:
        preferences = get_preferences(context)
        if preferences:
            export_invisibles = bool(preferences.export_invisibles)
            export_only_selections = bool(preferences.export_only_selections)
        else:
            export_invisibles = False
            export_only_selections = False

        armatures = [
            obj
            for obj in search.export_objects(
                context, export_invisibles, export_only_selections
            )
            if obj.type == "ARMATURE"
        ]
        if not armatures:
            return
        armature = armatures[0]

        layout = self.layout
        humanoid = armature.data.vrm_addon_extension.vrm0.humanoid
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
        draw_vrm0_humanoid_required_bones_layout(armature, layout)
