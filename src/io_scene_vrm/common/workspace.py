# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import bpy
from bpy.types import Context, Object
from mathutils import Matrix


@dataclass(frozen=True)
class SavedWorkspace:
    cursor_matrix: Matrix
    previous_object_name: Optional[str]
    previous_object_mode: Optional[str]
    active_object_name: Optional[str]
    active_object_hide_viewport: bool


def enter_save_workspace(
    context: Context, obj: Optional[Object] = None, *, mode: str = "OBJECT"
) -> SavedWorkspace:
    cursor_matrix = context.scene.cursor.matrix.copy()

    previous_object_name = None
    previous_object_mode = None
    previous_object = context.view_layer.objects.active
    if previous_object:
        previous_object_name = sys.intern(previous_object.name)
        previous_object_mode = sys.intern(previous_object.mode)

        if previous_object != obj and previous_object_mode != "OBJECT":
            previous_object_hide_viewport = previous_object.hide_viewport
            if previous_object_hide_viewport:
                previous_object.hide_viewport = False
            bpy.ops.object.mode_set(mode="OBJECT")
            if previous_object.hide_viewport != previous_object_hide_viewport:
                previous_object.hide_viewport = previous_object_hide_viewport

    # オブジェクトを渡された場合、それをアクティブにする
    if obj is not None:
        context.view_layer.objects.active = obj
        context.view_layer.update()

    active_object_name = None
    active_object_hide_viewport = False
    # アクティブなオブジェクトのモードを変更する
    active_object = context.view_layer.objects.active
    if active_object:
        # yield後にactive_objectが消える場合がある。
        # いちおうinternをしておくが、不要かもしれない。
        active_object_name = sys.intern(active_object.name)
        active_object_hide_viewport = active_object.hide_viewport
        # hide_viewportがTrueの場合、そのままだとmode_setに失敗する可能性がある
        # 現在はモードを変更しない場合も強制的に表示状態にしてあるが、不適切かも
        if active_object_hide_viewport:
            active_object.hide_viewport = False
        if active_object.mode != mode:
            bpy.ops.object.mode_set(mode=mode)

    return SavedWorkspace(
        cursor_matrix=cursor_matrix,
        previous_object_name=previous_object_name,
        previous_object_mode=previous_object_mode,
        active_object_name=active_object_name,
        active_object_hide_viewport=active_object_hide_viewport,
    )


def exit_save_workspace(context: Context, saved_workspace: SavedWorkspace) -> None:
    cursor_matrix = saved_workspace.cursor_matrix
    previous_object_name = saved_workspace.previous_object_name
    previous_object_mode = saved_workspace.previous_object_mode
    active_object_name = saved_workspace.active_object_name
    active_object_hide_viewport = saved_workspace.active_object_hide_viewport

    previous_object = None
    if previous_object_name is not None:
        previous_object = context.blend_data.objects.get(previous_object_name)

    current_active_object = context.view_layer.objects.active

    # 現在アクティブなオブジェクトのモードを"OBJECT"にする。モードがそのままだと、
    # アクティブなオブジェクトを変更できないことがある
    if (
        current_active_object
        and current_active_object != previous_object
        and current_active_object.mode != "OBJECT"
    ):
        current_active_object_hide_viewport = current_active_object.hide_viewport
        if current_active_object.hide_viewport:
            current_active_object.hide_viewport = False
        bpy.ops.object.mode_set(mode="OBJECT")
        if current_active_object.hide_viewport != current_active_object_hide_viewport:
            current_active_object.hide_viewport = current_active_object_hide_viewport

    # アクティブにしたオブジェクトのhide_viewportを戻す
    if active_object_name is not None:
        active_object = context.blend_data.objects.get(active_object_name)
        if active_object and active_object.hide_viewport != active_object_hide_viewport:
            active_object.hide_viewport = active_object_hide_viewport

    # もともとアクティブだったオブジェクトに戻す
    previous_object = None
    if previous_object_name is not None:
        previous_object = context.blend_data.objects.get(previous_object_name)

    if context.view_layer.objects.active != previous_object:
        context.view_layer.objects.active = previous_object
        context.view_layer.update()

    # もともとアクティブだったオブジェクトのモードを戻す
    if (
        previous_object
        and previous_object_mode is not None
        and previous_object_mode != previous_object.mode
    ):
        previous_object_hide_viewport = previous_object.hide_viewport
        if previous_object_hide_viewport:
            previous_object.hide_viewport = False
        bpy.ops.object.mode_set(mode=previous_object_mode)
        if previous_object.hide_viewport != previous_object_hide_viewport:
            previous_object.hide_viewport = previous_object_hide_viewport

    # 3Dカーソルをの位置をもとに戻す
    context.scene.cursor.matrix = cursor_matrix


@contextmanager
def save_workspace(
    context: Context, obj: Optional[Object] = None, *, mode: str = "OBJECT"
) -> Iterator[None]:
    saved_workspace = enter_save_workspace(context, obj, mode=mode)
    try:
        yield
    finally:
        exit_save_workspace(context, saved_workspace)


def wm_append_without_library(
    context: Context,
    blend_path: Path,
    *,
    append_filepath: str,
    append_filename: str,
    append_directory: str,
) -> set[str]:
    """wm.appendを呼び、追加されたライブラリを削除する.

    wm.appendがライブラリを追加するとアセットライブラリの追加に失敗する問題を回避するために使う。
    https://github.com/saturday06/VRM-Addon-for-Blender/issues/631
    https://github.com/saturday06/VRM-Addon-for-Blender/issues/646
    """
    # https://projects.blender.org/blender/blender/src/tag/v2.93.18/source/blender/windowmanager/intern/wm_files_link.c#L85-L90
    with save_workspace(context):
        existing_library_pointers: list[int] = [
            library.as_pointer() for library in context.blend_data.libraries
        ]

        result = bpy.ops.wm.append(
            filepath=append_filepath,
            filename=append_filename,
            directory=append_directory,
            link=False,
        )
        if result != {"FINISHED"}:
            return result

        # 追加されたライブラリを一つ削除。
        # 再帰的な呼び出しに対応するため逆順にしているが、効果があるかは未確認。
        for library in reversed(list(context.blend_data.libraries)):
            if not blend_path.samefile(library.filepath):
                continue
            if (
                library.users <= 1
                and library.as_pointer() not in existing_library_pointers
            ):
                context.blend_data.libraries.remove(library)
            break
        return result
