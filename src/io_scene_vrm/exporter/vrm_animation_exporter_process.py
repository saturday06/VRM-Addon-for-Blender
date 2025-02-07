# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import contextlib
import getpass
import json
import os
import platform
import subprocess
import sys
from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from pathlib import Path
from threading import Lock, Thread
from typing import IO, TYPE_CHECKING, Final, Optional, Union

import addon_utils
import bpy
from bpy.props import BoolProperty, CollectionProperty, IntProperty, StringProperty
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
from ..common.deep import make_json
from ..common.logger import get_logger
from ..common.version import get_addon_version
from ..editor.ops import VRM_OT_open_url_in_web_browser, layout_operator
from ..editor.property_group import CollectionPropertyProtocol
from . import vrm_animation_exporter_process_startup
from .vrm_animation_exporter import VrmAnimationExporter
from .vrm_animation_exporter_process_startup import EXPORT_ADDON_MODULE_NAME_ENV_KEY

logger = get_logger(__name__)


EXPORT_CONFIG_PATH_ENV_KEY: Final = "BLENDER_VRMA_EXPORT_CONFIG_PATH"


@dataclass
class ExportConfig:
    blend_path: str
    result_path: str
    armature_object_name: str

    def serialize(self) -> str:
        return json.dumps(
            {
                "blend_path": self.blend_path,
                "result_path": self.result_path,
                "armature_object_name": self.armature_object_name,
            }
        )

    @staticmethod
    def deserialize(serialized: str) -> "ExportConfig":
        parsed = make_json(json.loads(serialized))
        if not isinstance(parsed, dict):
            message = f"Unexpected JSON: {serialized}"
            raise TypeError(message)

        blend_path = parsed.get("blend_path")
        if not isinstance(blend_path, str):
            message = f"Unexpected blend_path in JSON: {serialized}"
            raise TypeError(message)

        result_path = parsed.get("result_path")
        if not isinstance(result_path, str):
            message = f"Unexpected result_path in JSON: {serialized}"
            raise TypeError(message)

        armature_object_name = parsed.get("armature_object_name")
        if not isinstance(armature_object_name, str):
            message = f"Unexpected armature_object_name in JSON: {serialized}"
            raise TypeError(message)

        return ExportConfig(
            blend_path=blend_path,
            result_path=result_path,
            armature_object_name=armature_object_name,
        )


def mask_private_string(message: str) -> str:
    return message.replace(getpass.getuser(), "(username)")


class ExportProcessOutputLine:
    def __init__(self, *, line: str, is_error: bool) -> None:
        self.line = mask_private_string(line)
        self.is_error = is_error


class ExportProcessOutputLinePropertyGroup(PropertyGroup):
    line: StringProperty()  # type: ignore[valid-type]
    is_error: BoolProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        line: str  # type: ignore[no-redef]
        is_error: bool  # type: ignore[no-redef]


class VRM_UL_vrma_export_process_output(UIList):
    bl_idname = "VRM_UL_vrma_export_process_output"

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        _data: object,
        export_process_output: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(export_process_output, ExportProcessOutputLinePropertyGroup):
            return

        column = layout.column(align=True)
        column.alert = export_process_output.is_error
        column.label(text=export_process_output.line, translate=False)


class VRM_OT_save_vrma_export_error_message(Operator, ExportHelper):
    bl_idname = "vrm.save_vrma_export_error_message"
    bl_label = "Save Error Message"
    bl_description = "Save VRMA Export Error Message"
    bl_options: AbstractSet[str] = {"REGISTER"}

    filename_ext = ".txt"
    filter_glob: StringProperty(  # type: ignore[valid-type]
        default="*.txt",
        options={"HIDDEN"},
    )

    process_output_lines: CollectionProperty(  # type: ignore[valid-type]
        type=ExportProcessOutputLinePropertyGroup, options={"HIDDEN"}
    )

    def show_vrma_export_result(self) -> set[str]:
        return ops.wm.vrma_export_result(
            "INVOKE_DEFAULT",
            process_output_lines=[
                {
                    "name": process_output_line.name,
                    "line": process_output_line.line,
                    "is_error": process_output_line.is_error,
                }
                for process_output_line in self.process_output_lines
            ],
        )

    def cancel(self, _context: Context) -> None:
        self.show_vrma_export_result()

    def execute(self, _context: Context) -> set[str]:
        message = "\n".join(output.line for output in self.process_output_lines)
        Path(self.filepath).write_bytes(message.encode())
        return self.show_vrma_export_result()

    def invoke(self, context: Context, event: Event) -> set[str]:
        if not self.filepath:
            self.filepath = "vrma_export_error_message.txt"
        return ExportHelper.invoke(self, context, event)

    if TYPE_CHECKING:  # Make legacy mypy happy
        filepath: str

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        filter_glob: str  # type: ignore[no-redef]
        process_output_lines: CollectionPropertyProtocol[  # type: ignore[no-redef]
            ExportProcessOutputLinePropertyGroup
        ]


class WM_OT_vrma_export_result(Operator):
    bl_label = "Failed to Export VRM Animation"
    bl_idname = "wm.vrma_export_result"
    bl_options: AbstractSet[str] = {"REGISTER"}

    process_output_lines: CollectionProperty(  # type: ignore[valid-type]
        type=ExportProcessOutputLinePropertyGroup, options={"HIDDEN"}
    )
    active_process_output_line_index: IntProperty(options={"HIDDEN"})  # type: ignore[valid-type]

    def execute(self, _context: Context) -> set[str]:
        return {"FINISHED"}

    def invoke(self, context: Context, _event: Event) -> set[str]:
        self.active_process_output_line_index = len(self.process_output_lines) - 1
        return context.window_manager.invoke_props_dialog(self, width=700)

    def draw(self, _context: Context) -> None:
        layout = self.layout
        row = layout.row()
        save_op = layout_operator(
            row, VRM_OT_save_vrma_export_error_message, icon="FILE"
        )
        for process_output_line in self.process_output_lines:
            output = save_op.process_output_lines.add()
            output.line = process_output_line.line
            output.is_error = process_output_line.is_error
        open_url_op = layout_operator(
            row, VRM_OT_open_url_in_web_browser, icon="URL", text="Open Support Site"
        )
        open_url_op.url = "https://github.com/saturday06/VRM-Addon-for-Blender/issues"
        layout.template_list(
            VRM_UL_vrma_export_process_output.bl_idname,
            "",
            self,
            "process_output_lines",
            self,
            "active_process_output_line_index",
            rows=20,
            sort_lock=True,
        )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        process_output_lines: CollectionPropertyProtocol[  # type: ignore[no-redef]
            ExportProcessOutputLinePropertyGroup
        ]
        active_process_output_line_index: int  # type: ignore[no-redef]


class VRM_OT_export_vrma(Operator):
    bl_idname = "vrm.export_vrma"
    bl_label = "Export VRM Animation (Internal)"
    bl_description = "Export VRM Animation (Internal)"
    bl_options: AbstractSet[str] = {"REGISTER", "INTERNAL"}

    def execute(self, context: Context) -> set[str]:
        config_path_str = os.environ.get(EXPORT_CONFIG_PATH_ENV_KEY)
        if not config_path_str:
            message = f'No "{EXPORT_CONFIG_PATH_ENV_KEY}" in environment variables'
            raise ValueError(message)

        config_path = Path(config_path_str)
        if not config_path.exists():
            message = f'No config file in "{config_path}"'
            raise ValueError(message)

        config_str = config_path.read_bytes().decode()
        config = ExportConfig.deserialize(config_str)

        open_result = bpy.ops.wm.open_mainfile(filepath=config.blend_path)
        if open_result != {"FINISHED"}:
            message = f'Failed to open "{config.blend_path}": {open_result}'
            raise ValueError(message)

        armature = context.blend_data.objects.get(config.armature_object_name)
        if not armature:
            message = f'No armature object "{config.armature_object_name}"'
            raise ValueError(message)

        return VrmAnimationExporter.execute(context, Path(config.result_path), armature)


def decode_line_bytes(line_bytes: bytes) -> str:
    line = None
    if sys.platform == "win32":
        with contextlib.suppress(UnicodeError):
            line = line_bytes.decode("ansi")
    if line is None:
        line = line_bytes.decode("utf-8", errors="replace")
    return str.rstrip(line)


def read_process_output(
    bytes_io: Optional[IO[bytes]],
    outputs: list[ExportProcessOutputLine],
    outputs_lock: Lock,
    *,
    is_error: bool,
) -> None:
    if not bytes_io:
        return
    for line_bytes in bytes_io.readlines():
        output = ExportProcessOutputLine(
            line=decode_line_bytes(line_bytes), is_error=is_error
        )
        with outputs_lock:
            outputs.append(output)


def run_vrma_export_process(
    export_config: ExportConfig, config_path: Path
) -> tuple[bool, int, list[ExportProcessOutputLine]]:
    """現在の状態を別名で一時ファイルに保存し、別プロセスで一時ファイルを読みVRMAを出力する.

    VRMAエクスポート処理をフレームを進めながら行いたいが、その影響は非常に大きく
    「元に戻す」という処理が事実上実装できない。そのため、blendファイルのコピーを保存し
    それに対してエクスポート処理を行う。
    """
    # 「コピーを保存」機能を用い、現在の状態を一時ファイルに保存。
    if bpy.ops.wm.save_as_mainfile(
        filepath=str(export_config.blend_path), copy=True
    ) != {"FINISHED"}:
        return (
            False,
            -1,
            [
                ExportProcessOutputLine(
                    line=f"Failed to save the blend file: {export_config.blend_path}",
                    is_error=True,
                )
            ],
        )

    addon_module_path = (Path(__file__).parent.parent / "__init__.py").resolve(
        strict=True
    )

    # サブプロセスでアドオンが有効化されているとは限らない。明示的に有効化するため
    # bpy.ops.preferences.addon_enable()に渡せるアドオンのモジュール名を得る。
    # このコードが実行されているということは現在VRMアドオンは有効になっているが、その
    # 有効化設定が永続化されていない場合がある。
    addon_module_name: Optional[str] = None
    serching_paths: list[str] = []
    for addon_module in addon_utils.modules():
        # 型ヒントには "__file__" はあるが、ドキュメントには無いので
        # getattr()を使っている。
        path_str = getattr(addon_module, "__file__", None)
        if not isinstance(path_str, str) or not path_str:
            continue
        serching_paths.append(path_str)
        path = Path(path_str)
        if not path.exists():
            continue
        try:
            path = path.resolve(strict=True)
        except (FileNotFoundError, RuntimeError):
            continue
        if path != addon_module_path:
            continue
        addon_module_name = addon_module.__name__
        break

    if addon_module_name is None:
        return (
            False,
            -1,
            [
                ExportProcessOutputLine(
                    line=f"Failed to find enabled VRM add-on: {addon_module_path}",
                    is_error=True,
                ),
                *[
                    ExportProcessOutputLine(
                        line=f"Searching path: {searching_path}", is_error=True
                    )
                    for searching_path in serching_paths
                ],
            ],
        )

    error_exit_code = 50  #  0以外を指定

    # 設定ファイルのパスとアドオンモジュール名をサブプロセスに渡す。
    # コマンドライン引数で渡すのが本来は一般的だが、別のアドオンがコマンドライン引数を
    # 処理するなどをして競合しそうなので、競合しなさそうな環境変数で渡す。
    env = os.environ.copy()
    env[EXPORT_CONFIG_PATH_ENV_KEY] = str(config_path)
    env[EXPORT_ADDON_MODULE_NAME_ENV_KEY] = addon_module_name

    binary_path = bpy.app.binary_path  # TODO: Windowsストアアプリ

    config_path.write_bytes(export_config.serialize().encode())

    outputs_lock: Final = Lock()
    outputs: Final[list[ExportProcessOutputLine]] = []

    with subprocess.Popen(
        args=[
            binary_path,
            "-noaudio",
            "--python-exit-code",
            str(error_exit_code),
            "--background",
            "--python",
            vrm_animation_exporter_process_startup.__file__,
        ],
        shell=False,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as proc:
        # パイプの詰まりを回避するため、非効率ではあるがスレッドを使って出力を読む
        stdout_read_thread = Thread(
            target=lambda: read_process_output(
                proc.stdout, outputs, outputs_lock, is_error=False
            )
        )
        stderr_read_thread = Thread(
            target=lambda: read_process_output(
                proc.stderr, outputs, outputs_lock, is_error=True
            )
        )
        stdout_read_thread.start()
        try:
            stderr_read_thread.start()
            try:
                proc.wait()
            finally:
                stderr_read_thread.join()
        finally:
            stdout_read_thread.join()

        with outputs_lock:
            return proc.returncode == 0, proc.returncode, outputs.copy()


def run_vrma_export_process_and_show_result_if_error(
    export_config: ExportConfig, config_path: Path
) -> set[str]:
    try:
        finished, _, outputs = run_vrma_export_process(export_config, config_path)
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        finished = False
        outputs = [
            ExportProcessOutputLine(line=line, is_error=True)
            for line in str(e).splitlines()
        ]
    if finished:
        return {"FINISHED"}

    for output in outputs:
        if output.is_error:
            logger.error(output.line)
        else:
            logger.warning(output.line)

    process_output_lines: Sequence[Mapping[str, Union[str, bool]]] = [
        {
            "name": f"VrmExportProcessOutputLine{index}",
            "line": output.line,
            "is_error": output.is_error,
        }
        for index, output in enumerate(
            [
                ExportProcessOutputLine(
                    line=f"VRM Add-on {'.'.join(map(str, get_addon_version()))}"
                    + f" / {platform.system()} {platform.machine()}",
                    is_error=True,
                ),
                *outputs,
            ]
        )
    ]
    return ops.wm.vrma_export_result(
        "INVOKE_DEFAULT",
        process_output_lines=process_output_lines,
    )
