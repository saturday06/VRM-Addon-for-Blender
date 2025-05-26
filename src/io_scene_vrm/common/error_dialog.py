# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import getpass
import platform
import sysconfig
from collections.abc import Sequence
from collections.abc import Set as AbstractSet
from pathlib import Path
from typing import TYPE_CHECKING, Union

import bpy
from bpy.props import CollectionProperty, IntProperty, StringProperty
from bpy.types import (
    Context,
    Event,
    Operator,
    PropertyGroup,
    UILayout,
    UIList,
)
from bpy_extras.io_utils import ExportHelper

from ..common import ops
from ..common.logger import get_logger
from ..common.version import get_addon_version
from ..editor.ops import VRM_OT_open_url_in_web_browser, layout_operator
from ..editor.property_group import CollectionPropertyProtocol

logger = get_logger(__name__)


def show_error_dialog(
    title: str,
    lines: Union[str, Sequence[str]],
    *,
    append_environment: bool = True,
) -> set[str]:
    if isinstance(lines, str):
        lines = list(map(str.rstrip, lines.splitlines()))
        while lines and not lines[0].strip():
            del lines[0]
        while lines and not lines[-1].strip():
            del lines[-1]
    else:
        lines = list(lines)
    if not lines:
        return {"CANCELLED"}
    if append_environment:
        if lines:
            lines[0] = f"Python: {lines[0]}"

        runtime_platform = platform.system() + " " + platform.machine()
        build_platform = sysconfig.get_platform()
        lines.insert(
            0,
            "Environment: Blender {} / VRM Add-on {} / {} ({})".format(
                bpy.app.version_string,
                ".".join(map(str, get_addon_version())),
                runtime_platform,
                build_platform,
            ),
        )
    return ops.wm.vrm_error_dialog(
        "INVOKE_DEFAULT",
        title=title,
        lines=[
            {
                "name": f"error_line_{i}",
                "line": mask_private_string(line),
            }
            for i, line in enumerate(lines)
        ],
    )


def mask_private_string(message: str) -> str:
    script_path = Path(__file__).parent.parent.parent.parent.parent
    if len(script_path.parts) > 3:
        message = message.replace(str(script_path), "<script path>")

    message = message.replace(str(Path.home()), "<home path>")
    message = message.replace(getpass.getuser(), "<username>")
    return message


class VrmErrorDialogMessageLine(PropertyGroup):
    line: StringProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        line: str  # type: ignore[no-redef]


class VRM_UL_vrm_error_dialog_message(UIList):
    bl_idname = "VRM_UL_vrm_error_dialog_message"

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        _data: object,
        line: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(line, VrmErrorDialogMessageLine):
            return

        column = layout.column(align=True)
        column.label(text=line.line, translate=False)


class VRM_OT_save_error_dialog_message(Operator, ExportHelper):
    bl_idname = "vrm.save_error_dialog_message"
    bl_label = "Save Error Message"
    bl_description = "Save Error Message"
    bl_options: AbstractSet[str] = {"REGISTER"}

    filename_ext = ".txt"
    filter_glob: StringProperty(  # type: ignore[valid-type]
        default="*.txt",
        options={"HIDDEN"},
    )

    title: StringProperty(options={"HIDDEN"})  # type: ignore[valid-type]
    lines: CollectionProperty(  # type: ignore[valid-type]
        type=VrmErrorDialogMessageLine, options={"HIDDEN"}
    )

    def restore_error_dialog(self) -> set[str]:
        if bpy.app.version >= (4, 1):
            return {"FINISHED"}

        return show_error_dialog(
            self.title,
            [output.line for output in self.lines],
            append_environment=False,
        )

    def cancel(self, _context: Context) -> None:
        self.restore_error_dialog()

    def execute(self, _context: Context) -> set[str]:
        message = "\n".join(output.line for output in self.lines)
        Path(self.filepath).write_bytes(message.encode())
        return self.restore_error_dialog()

    def invoke(self, context: Context, event: Event) -> set[str]:
        if not self.filepath:
            self.filepath = "vrm_error_message.txt"
        return ExportHelper.invoke(self, context, event)

    if TYPE_CHECKING:  # Make legacy mypy happy
        filepath: str

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        filter_glob: str  # type: ignore[no-redef]
        title: str  # type: ignore[no-redef]
        lines: CollectionPropertyProtocol[  # type: ignore[no-redef]
            VrmErrorDialogMessageLine
        ]


class WM_OT_vrm_error_dialog(Operator):
    bl_label = "Error"
    bl_idname = "wm.vrm_error_dialog"
    bl_options: AbstractSet[str] = {"REGISTER"}

    title: StringProperty(options={"HIDDEN"})  # type: ignore[valid-type]
    lines: CollectionProperty(  # type: ignore[valid-type]
        type=VrmErrorDialogMessageLine, options={"HIDDEN"}
    )
    active_line_index: IntProperty(options={"HIDDEN"})  # type: ignore[valid-type]

    def execute(self, _context: Context) -> set[str]:
        return {"FINISHED"}

    def invoke(self, context: Context, _event: Event) -> set[str]:
        self.active_line_index = len(self.lines) - 1
        return context.window_manager.invoke_props_dialog(self, width=700)

    def draw(self, _context: Context) -> None:
        layout = self.layout.column()
        layout.emboss = "NONE"
        box = layout.box()
        box.emboss = "NORMAL"
        row = box.split(factor=0.5, align=True)
        row.label(text=self.title, icon="ERROR")
        save_op = layout_operator(row, VRM_OT_save_error_dialog_message, icon="FILE")
        save_op.title = self.title
        for process_output_line in self.lines:
            output = save_op.lines.add()
            output.line = process_output_line.line
        open_url_op = layout_operator(
            row, VRM_OT_open_url_in_web_browser, icon="URL", text="Open Support Site"
        )
        open_url_op.url = "https://github.com/saturday06/VRM-Addon-for-Blender/issues"
        box.template_list(
            VRM_UL_vrm_error_dialog_message.bl_idname,
            "",
            self,
            "lines",
            self,
            "active_line_index",
            rows=20,
            sort_lock=True,
        )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        title: str  # type: ignore[no-redef]
        lines: CollectionPropertyProtocol[  # type: ignore[no-redef]
            VrmErrorDialogMessageLine
        ]
        active_line_index: int  # type: ignore[no-redef]
