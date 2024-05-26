import sys
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Optional

import bpy
from bpy.types import Context, Object


@contextmanager
def save_workspace(
    context: Context, obj: Optional[Object] = None, *, mode: str = "OBJECT"
) -> Iterator[None]:
    # 3Dカーソルの位置を保存
    previous_cursor_matrix = context.scene.cursor.matrix.copy()

    # アクティブなオブジェクトがある場合は、モードを"OBJECT"にする
    previous_object_name = None
    previous_object_mode = None
    if context.view_layer.objects.active:
        # yield後にprevious_objectが消える場合がある。
        # いちおうinternをしておくが、不要かもしれない。
        previous_object_name = sys.intern(context.view_layer.objects.active.name)
        previous_object_mode = sys.intern(context.view_layer.objects.active.mode)
        if previous_object_mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

    # オブジェクトを渡された場合、それをアクティブにする
    if obj is not None:
        context.view_layer.objects.active = obj
        context.view_layer.update()

    # モードを変更する
    if (
        context.view_layer.objects.active
        and context.view_layer.objects.active.mode != mode
    ):
        bpy.ops.object.mode_set(mode=mode)

    try:
        yield  # yield前後でネイティブオブジェクトが消えていることがあるのに注意する
    finally:
        # 現在のオブジェクトのモードを"OBJECT"にする
        next_object = context.view_layer.objects.active
        if next_object and next_object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        # もともと設定されていたオブジェクトに戻す
        if previous_object_name is None:
            if context.view_layer.objects.active is not None:
                context.view_layer.objects.active = None
                context.view_layer.update()
        else:
            previous_object = context.blend_data.objects.get(previous_object_name)
            if context.view_layer.objects.active != previous_object:
                context.view_layer.objects.active = previous_object
                context.view_layer.update()
            if (
                previous_object_mode is not None
                and previous_object
                and previous_object.mode != previous_object_mode
            ):
                bpy.ops.object.mode_set(mode=previous_object_mode)

        # 3Dカーソルをの位置をもとに戻す
        context.scene.cursor.matrix = previous_cursor_matrix
