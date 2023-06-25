import base64
import contextlib
import functools
import itertools
import struct
from os import environ
from pathlib import Path
from typing import Dict, Set, Tuple, Union, cast
from urllib.parse import urlparse

import bpy
from bpy.app.translations import pgettext
from bpy_extras.io_utils import ImportHelper

from ..common import version
from ..common.gl import GL_FLOAT
from ..common.gltf import pack_glb, parse_glb
from ..common.logging import get_logger
from ..common.preferences import get_preferences, use_legacy_importer_exporter
from ..editor.ops import VRM_OT_open_url_in_web_browser
from .gltf2_addon_vrm_importer import Gltf2AddonVrmImporter, RetryUsingLegacyVrmImporter
from .legacy_vrm_importer import LegacyVrmImporter
from .license_validation import LicenseConfirmationRequired
from .vrm_parser import VrmParser

logger = get_logger(__name__)


class LicenseConfirmation(bpy.types.PropertyGroup):  # type: ignore[misc]
    message: bpy.props.StringProperty()  # type: ignore[valid-type]
    url: bpy.props.StringProperty()  # type: ignore[valid-type]
    json_key: bpy.props.StringProperty()  # type: ignore[valid-type]


def import_vrm_update_addon_preferences(
    import_op: bpy.types.Operator, context: bpy.types.Context
) -> None:
    preferences = get_preferences(context)

    if bool(preferences.set_shading_type_to_material_on_import) != bool(
        import_op.set_shading_type_to_material_on_import
    ):
        preferences.set_shading_type_to_material_on_import = (
            import_op.set_shading_type_to_material_on_import
        )

    if bool(preferences.set_view_transform_to_standard_on_import) != bool(
        import_op.set_view_transform_to_standard_on_import
    ):
        preferences.set_view_transform_to_standard_on_import = (
            import_op.set_view_transform_to_standard_on_import
        )

    if bool(preferences.set_armature_display_to_wire) != bool(
        import_op.set_armature_display_to_wire
    ):
        preferences.set_armature_display_to_wire = (
            import_op.set_armature_display_to_wire
        )

    if bool(preferences.set_armature_display_to_show_in_front) != bool(
        import_op.set_armature_display_to_show_in_front
    ):
        preferences.set_armature_display_to_show_in_front = (
            import_op.set_armature_display_to_show_in_front
        )


class IMPORT_SCENE_OT_vrm(bpy.types.Operator, ImportHelper):  # type: ignore[misc]
    bl_idname = "import_scene.vrm"
    bl_label = "Import VRM"
    bl_description = "Import VRM"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".vrm"
    filter_glob: bpy.props.StringProperty(  # type: ignore[valid-type]
        default="*.vrm", options={"HIDDEN"}  # noqa: F722,F821
    )

    extract_textures_into_folder: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Extract texture images into the folder",  # noqa: F722
        default=False,
    )
    make_new_texture_folder: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Don't overwrite existing texture folder",  # noqa: F722
        default=True,
    )
    set_shading_type_to_material_on_import: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name='Set shading type to "Material"',  # noqa: F722
        update=import_vrm_update_addon_preferences,
        default=True,
    )
    set_view_transform_to_standard_on_import: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name='Set view transform to "Standard"',  # noqa: F722
        update=import_vrm_update_addon_preferences,
        default=True,
    )
    set_armature_display_to_wire: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name='Set an imported armature display to "Wire"',  # noqa: F722
        update=import_vrm_update_addon_preferences,
        default=True,
    )
    set_armature_display_to_show_in_front: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name='Set an imported armature display to show "In-Front"',  # noqa: F722
        update=import_vrm_update_addon_preferences,
        default=True,
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        filepath = Path(self.filepath)
        if not filepath.is_file():
            return {"CANCELLED"}

        license_error = None
        try:
            return create_blend_model(
                self,
                context,
                license_validation=True,
            )
        except LicenseConfirmationRequired as e:
            license_error = e  # Prevent traceback dump on another exception

        logger.warning(license_error.description())

        execution_context = "INVOKE_DEFAULT"
        import_anyway = False
        if environ.get("BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION") == "true":
            execution_context = "EXEC_DEFAULT"
            import_anyway = True

        return cast(
            Set[str],
            bpy.ops.wm.vrm_license_warning(
                execution_context,
                import_anyway=import_anyway,
                license_confirmations=license_error.license_confirmations(),
                filepath=str(filepath),
                extract_textures_into_folder=self.extract_textures_into_folder,
                make_new_texture_folder=self.make_new_texture_folder,
            ),
        )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        preferences = get_preferences(context)
        (
            self.set_shading_type_to_material_on_import,
            self.set_view_transform_to_standard_on_import,
            self.set_armature_display_to_wire,
            self.set_armature_display_to_show_in_front,
        ) = (
            preferences.set_shading_type_to_material_on_import,
            preferences.set_view_transform_to_standard_on_import,
            preferences.set_armature_display_to_wire,
            preferences.set_armature_display_to_show_in_front,
        )

        if not use_legacy_importer_exporter() and "gltf" not in dir(
            bpy.ops.import_scene
        ):
            return cast(
                Set[str],
                bpy.ops.wm.vrm_gltf2_addon_disabled_warning(
                    "INVOKE_DEFAULT",
                ),
            )
        return cast(Set[str], ImportHelper.invoke(self, context, event))


class VRM_PT_import_unsupported_blender_version_warning(bpy.types.Panel):  # type: ignore[misc]
    bl_idname = "VRM_PT_import_unsupported_blender_version_warning"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_parent_id = "FILE_PT_operator"
    bl_label = ""
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return str(
            context.space_data.active_operator.bl_idname
        ) == "IMPORT_SCENE_OT_vrm" and (
            not version.supported() or version.blender_restart_required()
        )

    def draw(self, _context: bpy.types.Context) -> None:
        if version.blender_restart_required():
            warning_message = pgettext(
                "The VRM add-on has been\nupdated. "
                + "Please restart Blender\nto apply the changes."
            )
        else:
            warning_message = pgettext(
                "The installed VRM add-\non is not compatible with\nBlender {blender_version}."
                + " Please update."
            ).format(blender_version=".".join(map(str, bpy.app.version[:2])))

        box = self.layout.box()
        warning_column = box.column()
        for index, warning_line in enumerate(warning_message.splitlines()):
            warning_column.label(
                text=warning_line,
                translate=False,
                icon="NONE" if index else "ERROR",
            )


class WM_OT_vrm_license_confirmation(bpy.types.Operator):  # type: ignore[misc]
    bl_label = "VRM License Confirmation"
    bl_idname = "wm.vrm_license_warning"
    bl_options = {"REGISTER", "UNDO"}

    filepath: bpy.props.StringProperty()  # type: ignore[valid-type]

    license_confirmations: bpy.props.CollectionProperty(type=LicenseConfirmation)  # type: ignore[valid-type]
    import_anyway: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Import Anyway",  # noqa: F722
    )

    extract_textures_into_folder: bpy.props.BoolProperty()  # type: ignore[valid-type]
    make_new_texture_folder: bpy.props.BoolProperty()  # type: ignore[valid-type]

    def execute(self, context: bpy.types.Context) -> Set[str]:
        filepath = Path(self.filepath)
        if not filepath.is_file():
            return {"CANCELLED"}
        if not self.import_anyway:
            return {"CANCELLED"}
        return create_blend_model(
            self,
            context,
            license_validation=False,
        )

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> Set[str]:
        return cast(
            Set[str], context.window_manager.invoke_props_dialog(self, width=600)
        )

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(text=self.filepath, translate=False)
        for license_confirmation in self.license_confirmations:
            box = layout.box()
            for line in license_confirmation.message.split("\n"):
                box.label(text=line, translate=False, icon="INFO")
            if license_confirmation.json_key:
                box.label(
                    text=pgettext("For more information please check following URL.")
                )
                if VRM_OT_open_url_in_web_browser.supported(license_confirmation.url):
                    split = box.split(factor=0.85)
                    split.prop(
                        license_confirmation,
                        "url",
                        text=license_confirmation.json_key,
                        translate=False,
                    )
                    op = split.operator(VRM_OT_open_url_in_web_browser.bl_idname)
                    op.url = license_confirmation.url
                else:
                    box.prop(
                        license_confirmation,
                        "url",
                        text=license_confirmation.json_key,
                        translate=False,
                    )

        layout.prop(self, "import_anyway")


def create_blend_model(
    addon: Union[IMPORT_SCENE_OT_vrm, WM_OT_vrm_license_confirmation],
    context: bpy.types.Context,
    license_validation: bool,
) -> Set[str]:
    legacy_importer = use_legacy_importer_exporter()
    has_ui_localization = bpy.app.version < (2, 83)
    ui_localization = False
    if has_ui_localization:
        ui_localization = context.preferences.view.use_international_fonts
    try:
        if not legacy_importer:
            with contextlib.suppress(RetryUsingLegacyVrmImporter):
                parse_result = VrmParser(
                    Path(addon.filepath),
                    addon.extract_textures_into_folder,
                    addon.make_new_texture_folder,
                    license_validation=license_validation,
                    legacy_importer=False,
                ).parse()

                Gltf2AddonVrmImporter(
                    context,
                    parse_result,
                    addon.extract_textures_into_folder,
                    addon.make_new_texture_folder,
                ).import_vrm()
                return {"FINISHED"}

        parse_result = VrmParser(
            Path(addon.filepath),
            addon.extract_textures_into_folder,
            addon.make_new_texture_folder,
            license_validation=license_validation,
            legacy_importer=True,
        ).parse()
        LegacyVrmImporter(
            context,
            parse_result,
            addon.extract_textures_into_folder,
            addon.make_new_texture_folder,
        ).import_vrm()
    finally:
        if has_ui_localization and ui_localization:
            context.preferences.view.use_international_fonts = ui_localization

    return {"FINISHED"}


def menu_import(
    menu_op: bpy.types.Operator, _context: bpy.types.Context
) -> None:  # Same as test/blender_io.py for now
    menu_op.layout.operator(IMPORT_SCENE_OT_vrm.bl_idname, text="VRM (.vrm)")


class IMPORT_SCENE_OT_vrma(bpy.types.Operator, ImportHelper):  # type: ignore[misc]
    bl_idname = "import_scene.vrma"
    bl_label = "Import VRM Animation"
    bl_description = "Import VRM Animation"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".vrma"
    filter_glob: bpy.props.StringProperty(  # type: ignore[valid-type]
        default="*.vrma", options={"HIDDEN"}  # noqa: F722,F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        filepath = Path(self.filepath)
        if not filepath.is_file():
            return {"CANCELLED"}
        return wip(filepath)

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        return cast(Set[str], ImportHelper.invoke(self, context, event))


def generate_vrma(filepath: Path) -> None:
    human_bones_dict = {}
    node_dicts = []
    accessor_dicts = []
    buffer_view_dicts = []
    buffer_dicts = [{"byteLength": 0}]

    hips_node_index = len(node_dicts)
    node_dicts.append(
        {
            "name": "hips",
        }
    )
    human_bones_dict = {
        "hips": {"node": hips_node_index},
    }

    input_output: Dict[float, Tuple[float, float, float]] = {
        0.0: (0, 0, 0),
        0.1: (0, 0, 0.1),
        0.2: (0, 0, 0.2),
        0.3: (0, 0, 0.3),
    }
    inputs = list(input_output.keys())
    buffer_input_bytes = struct.pack("<" + "f" * len(inputs), *inputs)
    buffer_input_dict = {
        "uri": "data:application/gltf-buffer;base64,"
        + base64.b64encode(buffer_input_bytes).decode("ascii"),
        "byteLength": len(buffer_input_bytes),
    }
    buffer_input_index = len(buffer_dicts)
    buffer_dicts.append(buffer_input_dict)

    outputs = list(functools.reduce(itertools.chain, input_output.values(), []))
    print(str(outputs))
    buffer_output_bytes = struct.pack("<" + "f" * len(outputs), *outputs)
    buffer_output_dict = {
        "uri": "data:application/gltf-buffer;base64,"
        + base64.b64encode(buffer_output_bytes).decode("ascii"),
        "byteLength": len(buffer_output_bytes),
    }
    buffer_output_index = len(buffer_dicts)
    buffer_dicts.append(buffer_output_dict)

    hips_translation_sampler_input_buffer_view_index = len(buffer_view_dicts)
    buffer_view_dicts.append(
        {
            "buffer": buffer_input_index,
            "byteLength": len(buffer_input_bytes),
        }
    )
    hips_translation_sampler_output_buffer_view_index = len(buffer_view_dicts)
    buffer_view_dicts.append(
        {
            "buffer": buffer_output_index,
            "byteLength": len(buffer_output_bytes),
        }
    )

    hips_translation_sampler_input_accessor_index = len(accessor_dicts)
    accessor_dicts.append(
        {
            "bufferView": hips_translation_sampler_input_buffer_view_index,
            "componentType": GL_FLOAT,
            "count": 0,
            "type": "SCALAR",
            # TODO: sparse
        }
    )
    # "VEC3" float XYZ translation vector
    hips_translation_sampler_output_accessor_index = len(accessor_dicts)
    accessor_dicts.append(
        {
            "bufferView": hips_translation_sampler_output_buffer_view_index,
            "componentType": GL_FLOAT,
            "count": 0,
            "type": "VEC3",
            # TODO: sparse
        }
    )

    hips_translation_sampler_dict = {
        "input": hips_translation_sampler_input_accessor_index,
        "interpolation": "LINEAR",
        "output": hips_translation_sampler_output_accessor_index,
    }

    animation_sampler_dicts = []
    hips_translation_sampler_index = len(animation_sampler_dicts)
    animation_sampler_dicts.append(hips_translation_sampler_dict)

    hips_translation_channel_dict = {
        "sampler": hips_translation_sampler_index,
        "target": {"node": hips_node_index, "path": "translation"},
    }

    animation_channel_dicts = [hips_translation_channel_dict]

    vrma_dict = {
        "nodes": node_dicts,
        "buffers": buffer_dicts,
        "bufferViews": buffer_view_dicts,
        "accessors": accessor_dicts,
        "animations": [
            {
                "channels": animation_channel_dicts,
                "samplers": animation_sampler_dicts,
            }
        ],
        "extensions": {
            "VRMC_vrm_animation": {
                "humanoid": {
                    "humanBones": human_bones_dict,
                },
            },
        },
    }

    filepath.write_bytes(pack_glb(vrma_dict, bytearray()))


def wip(filepath: Path) -> Set[str]:
    import bpy

    generate_vrma(filepath)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while bpy.data.collections:
        bpy.data.collections.remove(bpy.data.collections[0])

    bpy.ops.icyp.make_basic_armature()
    assert bpy.ops.vrm.model_validate() == {"FINISHED"}

    armature = bpy.context.active_object
    print(str(armature))

    vrma_dict, _bytes = parse_glb(filepath.read_bytes())
    print(vrma_dict)

    node_dicts = vrma_dict.get("nodes")
    if not isinstance(node_dicts, list) or not node_dicts:
        return {"CANCELLED"}
    animation_dicts = vrma_dict.get("animations")
    if not isinstance(animation_dicts, list) or not animation_dicts:
        return {"CANCELLED"}
    animation_dict = animation_dicts[0]
    if not isinstance(animation_dict, dict):
        return {"CANCELLED"}
    animation_channel_dicts = animation_dict.get("channels")
    if not isinstance(animation_channel_dicts, list) or not animation_channel_dicts:
        return {"CANCELLED"}
    animation_sampler_dicts = animation_dict.get("samplers")
    if not isinstance(animation_sampler_dicts, list) or not animation_sampler_dicts:
        return {"CANCELLED"}

    extensions_dict = vrma_dict.get("extensions")
    if not isinstance(extensions_dict, dict):
        return {"CANCELLED"}
    vrmc_vrm_animation_dict = extensions_dict.get("VRMC_vrm_animation")
    if not isinstance(vrmc_vrm_animation_dict, dict):
        return {"CANCELLED"}
    humanoid_dict = vrmc_vrm_animation_dict.get("humanoid")
    if not isinstance(humanoid_dict, dict):
        return {"CANCELLED"}
    human_bones_dict = humanoid_dict.get("humanBones")
    if not isinstance(human_bones_dict, dict):
        return {"CANCELLED"}
    hips_dict = human_bones_dict.get("hips")
    if not isinstance(hips_dict, dict):
        return {"CANCELLED"}
    hips_node_index = hips_dict.get("node")
    if not isinstance(hips_node_index, int):
        return {"CANCELLED"}
    if not 0 <= hips_node_index < len(node_dicts):
        return {"CANCELLED"}
    hips_node_dict = node_dicts[hips_node_index]
    if not isinstance(hips_node_dict, dict):
        return {"CANCELLED"}
    accessor_dicts = vrma_dict.get("accessors")
    if not isinstance(accessor_dicts, list):
        return {"CANCELLED"}
    buffer_view_dicts = vrma_dict.get("bufferViews")
    if not isinstance(buffer_view_dicts, list):
        return {"CANCELLED"}
    buffer_dicts = vrma_dict.get("buffers")
    if not isinstance(buffer_dicts, list):
        return {"CANCELLED"}

    # search hips translation animation channel
    for animation_channel_dict in animation_channel_dicts:
        target_dict = animation_channel_dict.get("target")
        if not isinstance(target_dict, dict):
            continue
        if target_dict.get("node") != hips_node_index:
            continue
        if target_dict.get("path") != "translation":
            continue
        animation_sampler_index = animation_channel_dict.get("sampler")
        if not isinstance(animation_sampler_index, int):
            continue
        if not 0 <= animation_sampler_index < len(animation_sampler_dicts):
            continue
        animation_sampler_dict = animation_sampler_dicts[animation_sampler_index]
        if not isinstance(animation_sampler_dict, dict):
            continue

        input_index = animation_sampler_dict.get("input")
        if not isinstance(input_index, int):
            continue
        if not 0 <= input_index < len(accessor_dicts):
            continue
        input_accessor_dict = accessor_dicts[input_index]
        if not isinstance(input_accessor_dict, dict):
            continue
        input_buffer_view_index = input_accessor_dict.get("bufferView")
        if not isinstance(input_buffer_view_index, int):
            continue
        if not 0 <= input_buffer_view_index < len(buffer_view_dicts):
            continue
        input_buffer_view_dict = buffer_view_dicts[input_buffer_view_index]
        if not isinstance(input_buffer_view_dict, dict):
            continue
        input_buffer_index = input_buffer_view_dict.get("buffer")
        if not isinstance(input_buffer_index, int):
            continue
        if not 0 <= input_buffer_index < len(buffer_dicts):
            continue
        input_buffer_dict = buffer_dicts[input_buffer_index]
        uri = input_buffer_dict.get("uri")
        if not isinstance(uri, str):
            continue
        try:
            parsed_url = urlparse(uri)
        except ValueError:
            continue
        if parsed_url.scheme != "data":
            continue
        prefix = "application/gltf-buffer;base64,"
        print(f"{parsed_url.path}")
        if not parsed_url.path.startswith(prefix):  # TODO: all variants
            continue
        base64_input_bytes = parsed_url.path.removeprefix(prefix)
        input_bytes = base64.b64decode(base64_input_bytes)
        inputs = struct.unpack("<" + "f" * int(len(input_bytes) / 4), input_bytes)
        print(f"{inputs=}")

        output_index = animation_sampler_dict.get("output")
        if not isinstance(output_index, int):
            continue
        if not 0 <= output_index < len(accessor_dicts):
            continue
        output_accessor_dict = accessor_dicts[output_index]
        if not isinstance(output_accessor_dict, dict):
            continue
        output_buffer_view_index = output_accessor_dict.get("bufferView")
        if not isinstance(output_buffer_view_index, int):
            continue
        if not 0 <= output_buffer_view_index < len(buffer_view_dicts):
            continue
        output_buffer_view_dict = buffer_view_dicts[output_buffer_view_index]
        if not isinstance(output_buffer_view_dict, dict):
            continue
        output_buffer_index = output_buffer_view_dict.get("buffer")
        if not isinstance(output_buffer_index, int):
            continue
        if not 0 <= output_buffer_index < len(buffer_dicts):
            continue
        output_buffer_dict = buffer_dicts[output_buffer_index]
        uri = output_buffer_dict.get("uri")
        if not isinstance(uri, str):
            continue
        try:
            parsed_url = urlparse(uri)
        except ValueError:
            continue
        if parsed_url.scheme != "data":
            continue
        print(f"{parsed_url.path}")
        if not parsed_url.path.startswith(prefix):  # TODO: all variants
            continue
        base64_output_bytes = parsed_url.path.removeprefix(prefix)
        output_bytes = base64.b64decode(base64_output_bytes)
        outputs = struct.unpack("<" + "f" * int(len(output_bytes) / 4), output_bytes)
        for timestamp, translation in zip(
            inputs, [tuple(outputs[i : i + 3]) for i in range(0, len(outputs), 3)]
        ):
            print(f"{timestamp=} {translation=}")

    print("OK")

    action = bpy.data.actions.new(name="new action")
    action.frame_end = 70

    if not armature.animation_data:
        armature.animation_data_create()
    armature.animation_data.action = action

    armature.location = (0, 0, 0)
    armature.keyframe_insert(data_path="location", frame=0)
    armature.location = (1, 0, 0)
    armature.keyframe_insert(data_path="location", frame=50)

    return {"FINISHED"}
