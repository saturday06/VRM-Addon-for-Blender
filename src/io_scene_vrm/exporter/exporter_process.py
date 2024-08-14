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
    Armature,
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
from ..common.preferences import ExportPreferencesProtocol
from ..common.version import get_addon_version
from ..editor import search
from ..editor.extension import get_armature_extension
from ..editor.ops import VRM_OT_open_url_in_web_browser, layout_operator
from ..editor.property_group import CollectionPropertyProtocol
from ..exporter.abstract_base_vrm_exporter import AbstractBaseVrmExporter
from ..exporter.exporter_process_startup import EXPORT_ADDON_MODULE_NAME_ENV_KEY
from ..exporter.vrm0_exporter import Vrm0Exporter
from ..exporter.vrm1_exporter import Vrm1Exporter

logger = get_logger(__name__)


EXPORT_CONFIG_PATH_ENV_KEY: Final = "BLENDER_VRM_EXPORT_CONFIG_PATH"


@dataclass
class ExportConfig(ExportPreferencesProtocol):
    blend_path: str
    result_path: str
    armature_object_name: str

    export_invisibles: bool = False
    export_only_selections: bool = False
    enable_advanced_preferences: bool = False
    export_all_influences: bool = False
    export_lights: bool = False
    export_gltf_animations: bool = False
    export_try_sparse_sk: bool = False

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


class VrmExportProcessOutputLine(PropertyGroup):
    line: StringProperty()  # type: ignore[valid-type]
    is_error: BoolProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        line: str  # type: ignore[no-redef]
        is_error: bool  # type: ignore[no-redef]


class VRM_UL_vrm_export_process_output(UIList):
    bl_idname = "VRM_UL_vrm_export_process_output"

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
        if not isinstance(export_process_output, VrmExportProcessOutputLine):
            return

        column = layout.column(align=True)
        column.alert = export_process_output.is_error
        column.label(text=export_process_output.line, translate=False)


class VRM_OT_save_vrm_export_error_message(Operator, ExportHelper):
    bl_idname = "vrm.save_vrm_export_error_message"
    bl_label = "Save Error Message"
    bl_description = "Save VRM Export Error Message"
    bl_options: AbstractSet[str] = {"REGISTER"}

    filename_ext = ".txt"
    filter_glob: StringProperty(  # type: ignore[valid-type]
        default="*.txt",
        options={"HIDDEN"},
    )

    process_output_lines: CollectionProperty(  # type: ignore[valid-type]
        type=VrmExportProcessOutputLine, options={"HIDDEN"}
    )

    def show_vrm_export_result(self) -> set[str]:
        return ops.wm.vrm_export_result(
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
        self.show_vrm_export_result()

    def execute(self, _context: Context) -> set[str]:
        message = "\n".join(output.line for output in self.process_output_lines)
        Path(self.filepath).write_bytes(message.encode())
        return self.show_vrm_export_result()

    def invoke(self, context: Context, event: Event) -> set[str]:
        if not self.filepath:
            self.filepath = "vrm_export_error_message.txt"
        return ExportHelper.invoke(self, context, event)

    if TYPE_CHECKING:  # Make legacy mypy happy
        filepath: str

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        filter_glob: str  # type: ignore[no-redef]
        process_output_lines: CollectionPropertyProtocol[  # type: ignore[no-redef]
            VrmExportProcessOutputLine
        ]


class WM_OT_vrm_export_result(Operator):
    bl_label = "Failed to Export VRM"
    bl_idname = "wm.vrm_export_result"
    bl_options: AbstractSet[str] = {"REGISTER"}

    process_output_lines: CollectionProperty(  # type: ignore[valid-type]
        type=VrmExportProcessOutputLine, options={"HIDDEN"}
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
            row, VRM_OT_save_vrm_export_error_message, icon="FILE"
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
            VRM_UL_vrm_export_process_output.bl_idname,
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
            VrmExportProcessOutputLine
        ]
        active_process_output_line_index: int  # type: ignore[no-redef]


class VRM_OT_export_vrm(Operator):
    bl_idname = "vrm.export_vrm"
    bl_label = "Export VRM (Internal)"
    bl_description = "Export VRM (Internal)"
    bl_options: AbstractSet[str] = {"REGISTER", "INTERNAL"}

    def execute(self, context: Context) -> set[str]:
        config_path = os.environ.get(EXPORT_CONFIG_PATH_ENV_KEY)
        if not config_path:
            message = f'No "{EXPORT_CONFIG_PATH_ENV_KEY}" in environment variables'
            raise ValueError(message)

        if not Path(config_path).exists():
            message = f'No config file in "{config_path}"'
            raise ValueError(message)

        config_str = Path(config_path).read_bytes().decode()
        config = ExportConfig.deserialize(config_str)

        open_result = bpy.ops.wm.open_mainfile(filepath=config.blend_path)
        if open_result != {"FINISHED"}:
            message = f'Failed to open "{config.blend_path}": {open_result}'
            raise ValueError(message)

        if ops.vrm.model_validate(
            "INVOKE_DEFAULT",
            show_successful_message=False,
            armature_object_name=config.armature_object_name,
        ) != {"FINISHED"}:
            return {"CANCELLED"}

        export_objects = search.export_objects(
            context,
            config.armature_object_name,
            export_invisibles=config.export_invisibles,
            export_only_selections=config.export_only_selections,
            export_lights=config.export_lights,
        )

        armature = next((obj for obj in export_objects if obj.type == "ARMATURE"), None)
        if armature is None:
            message = f"Failed to find armature: {config.armature_object_name}"
            raise ValueError(message)

        armature_data = armature
        if not isinstance(armature_data, Armature):
            message = f"Unexpected armature type: {type(armature_data)}"
            raise TypeError(message)

        is_vrm1 = get_armature_extension(armature_data).is_vrm1()

        if is_vrm1:
            vrm_exporter: AbstractBaseVrmExporter = Vrm1Exporter(
                context,
                export_objects,
                armature=armature,
                export_preferences=config,
            )
        else:
            vrm_exporter = Vrm0Exporter(
                context,
                export_objects,
                armature=armature,
            )

        vrm_bin = vrm_exporter.export_vrm()
        if vrm_bin is None:
            message = f"Failed to export VRM: {config.serialize()}"
            raise ValueError(message)
        Path(config.result_path).write_bytes(vrm_bin)
        return {"FINISHED"}


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
        with outputs_lock:
            outputs.append(
                ExportProcessOutputLine(
                    line=decode_line_bytes(line_bytes), is_error=is_error
                )
            )


def run_vrm_export_process(
    export_config: ExportConfig, config_path: Path
) -> tuple[bool, int, list[ExportProcessOutputLine]]:
    """現在の状態を別名で一時ファイルに保存し、別プロセスで一時ファイルを読みVRMを出力する.

    VRMエクスポート処理は現在のデータに対して多くの前処理をする必要がある。その際次のような課題が発生する。

    - 多くの前処理に対して、それに対応する「元に戻す」処理を書くコストが非常に大きい
    - 注意深く実装しないと中間状態の「Undo」履歴が追加され、また「Redo」の履歴が消える

    これらの課題に対応するため、現在の状態を、編集中のファイルとは別名の一時ファイルに保存し、別プロセスで
    Blenderを起動しそのファイルを読み、そこでVRMのエクスポートを行う。
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
    addon_module_name = None
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

    # 設定ファイルのパスをサブプロセスに渡す。
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
            str(Path(__file__).with_name("exporter_process_startup.py")),
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


def run_vrm_export_process_and_show_result_if_error(
    export_config: ExportConfig, config_path: Path
) -> set[str]:
    try:
        finished, _, outputs = run_vrm_export_process(export_config, config_path)
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
    return ops.wm.vrm_export_result(
        "INVOKE_DEFAULT",
        process_output_lines=process_output_lines,
    )
