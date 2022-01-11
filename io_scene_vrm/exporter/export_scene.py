from typing import Set, cast

import bpy
from bpy_extras.io_utils import ExportHelper

from ..common.preferences import get_preferences, use_legacy_importer_exporter
from ..editor import search, validation
from .abstract_base_vrm_exporter import AbstractBaseVrmExporter
from .gltf2_addon_vrm_exporter import Gltf2AddonVrmExporter
from .legacy_vrm_exporter import LegacyVrmExporter


def export_vrm_update_addon_preferences(
    export_op: bpy.types.Operator, context: bpy.types.Context
) -> None:
    preferences = get_preferences(context)
    if not preferences:
        return
    if bool(preferences.export_invisibles) != bool(export_op.export_invisibles):
        preferences.export_invisibles = export_op.export_invisibles
    if bool(preferences.export_only_selections) != bool(
        export_op.export_only_selections
    ):
        preferences.export_only_selections = export_op.export_only_selections


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

    errors: bpy.props.CollectionProperty(type=validation.VrmValidationError)  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        if not self.filepath:
            return {"CANCELLED"}
        filepath: str = self.filepath

        if bpy.ops.vrm.model_validate(
            "INVOKE_DEFAULT", show_successful_message=False
        ) != {"FINISHED"}:
            return {"CANCELLED"}

        export_objects = search.export_objects(
            bool(self.export_invisibles), bool(self.export_only_selections)
        )
        is_vrm1 = any(
            obj
            for obj in export_objects
            if obj.type == "ARMATURE"
            and obj.data.vrm_addon_extension.spec_version == "1.0-beta"
        )

        if is_vrm1:
            vrm_exporter: AbstractBaseVrmExporter = Gltf2AddonVrmExporter(
                export_objects
            )
        else:
            vrm_exporter = LegacyVrmExporter(export_objects)

        vrm_bin = vrm_exporter.export_vrm()
        if vrm_bin is None:
            return {"CANCELLED"}
        with open(filepath, "wb") as f:
            f.write(vrm_bin)
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        preferences = get_preferences(context)
        if preferences:
            self.export_invisibles = bool(preferences.export_invisibles)
            self.export_only_selections = bool(preferences.export_only_selections)
        if not use_legacy_importer_exporter() and "gltf" not in dir(
            bpy.ops.export_scene
        ):
            return cast(
                Set[str],
                bpy.ops.wm.vrm_gltf2_addon_disabled_warning(
                    "INVOKE_DEFAULT",
                ),
            )
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
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        operator = context.space_data.active_operator

        layout.prop(operator, "export_invisibles")
        layout.prop(operator, "export_only_selections")

        validation.WM_OT_vrm_validator.detect_errors_and_warnings(
            context, operator.errors, False, layout
        )


def menu_export(export_op: bpy.types.Operator, _context: bpy.types.Context) -> None:
    export_op.layout.operator(EXPORT_SCENE_OT_vrm.bl_idname, text="VRM (.vrm)")
