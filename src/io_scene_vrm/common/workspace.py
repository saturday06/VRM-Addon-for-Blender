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

from .logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class SavedWorkspace:
    # Be careful not to include objects that might disappear before and after yield
    cursor_matrix: Matrix
    previous_object_name: Optional[str]
    previous_object_mode: Optional[str]
    active_object_name: Optional[str]
    active_object_hide_viewport: bool


def enter_save_workspace(
    context: Context, obj: Optional[Object] = None, *, mode: str = "OBJECT"
) -> SavedWorkspace:
    # Save the position of the 3D cursor
    cursor_matrix = context.scene.cursor.matrix.copy()

    previous_object_name = None
    previous_object_mode = None
    previous_object = context.view_layer.objects.active
    if previous_object:
        # previous_object may disappear after yield.
        # We intern it just in case, but it might not be necessary.
        previous_object_name = sys.intern(previous_object.name)
        previous_object_mode = sys.intern(previous_object.mode)

        # If an obj argument is passed, set the mode to "OBJECT". If the mode
        # stays as is, it may not be possible to change the active object
        if previous_object != obj and previous_object_mode != "OBJECT":
            previous_object_hide_viewport = previous_object.hide_viewport
            if previous_object_hide_viewport:
                # If hide_viewport is True, mode_set may fail if left as is
                previous_object.hide_viewport = False
            bpy.ops.object.mode_set(mode="OBJECT")
            if previous_object.hide_viewport != previous_object_hide_viewport:
                previous_object.hide_viewport = previous_object_hide_viewport

    # If an object is passed, make it active
    if obj is not None:
        context.view_layer.objects.active = obj
        context.view_layer.update()

    active_object_name = None
    active_object_hide_viewport = False
    # Change the mode of the active object
    active_object = context.view_layer.objects.active
    if active_object:
        # active_object may disappear after yield.
        # We intern it just in case, but it might not be necessary.
        active_object_name = sys.intern(active_object.name)
        active_object_hide_viewport = active_object.hide_viewport
        # If hide_viewport is True, mode_set may fail if left as is
        # Currently we force it to be visible even when not changing mode,
        # but this may be inappropriate
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

    # Set the mode of the currently active object to "OBJECT". If the mode stays as is,
    # it may not be possible to change the active object
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

    # Restore the hide_viewport of the activated object
    if active_object_name is not None:
        active_object = context.blend_data.objects.get(active_object_name)
        if active_object and active_object.hide_viewport != active_object_hide_viewport:
            active_object.hide_viewport = active_object_hide_viewport

    # Return to the originally active object
    previous_object = None
    if previous_object_name is not None:
        previous_object = context.blend_data.objects.get(previous_object_name)

    if context.view_layer.objects.active != previous_object:
        context.view_layer.objects.active = previous_object
        context.view_layer.update()

    # Restore the mode of the originally active object
    if (
        previous_object
        and previous_object_mode is not None
        and previous_object_mode != previous_object.mode
    ):
        # If hide_viewport is True, mode_set may fail if left as is
        # Restore hide_viewport after mode_set is completed
        previous_object_hide_viewport = previous_object.hide_viewport
        if previous_object_hide_viewport:
            previous_object.hide_viewport = False
        bpy.ops.object.mode_set(mode=previous_object_mode)
        if previous_object.hide_viewport != previous_object_hide_viewport:
            previous_object.hide_viewport = previous_object_hide_viewport

    # Restore the 3D cursor position
    context.scene.cursor.matrix = cursor_matrix


@contextmanager
def save_workspace(
    context: Context, obj: Optional[Object] = None, *, mode: str = "OBJECT"
) -> Iterator[None]:
    saved_workspace = enter_save_workspace(context, obj, mode=mode)
    try:
        yield
        # After yield, bpy native objects may be deleted or become invalid
        # as frames advance. Accessing them in this state can cause crashes,
        # so be careful not to access potentially invalid native objects
        # after yield
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
    """Call wm.append and remove the added libraries.

    Used to work around the issue where wm.append adding libraries causes
    asset library addition to fail.
    https://github.com/saturday06/VRM-Addon-for-Blender/issues/631
    https://github.com/saturday06/VRM-Addon-for-Blender/issues/646
    """
    # https://projects.blender.org/blender/blender/src/tag/v2.93.18/source/blender/windowmanager/intern/wm_files_link.c#L85-L90
    with save_workspace(context):
        # List of pointers for library addition detection.
        # Used only for addition detection. Be careful not to dereference,
        # as it is dangerous.
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

        # Remove one added library.
        # Reverse order to handle recursive calls, but effectiveness is unconfirmed.
        for library in reversed(list(context.blend_data.libraries)):
            if not blend_path.samefile(library.filepath):
                continue

            if library.as_pointer() in existing_library_pointers:
                continue

            if bpy.app.version >= (3, 2) and library.use_extra_user:
                library.use_extra_user = False
            if library.users:
                logger.warning(
                    'Failed to remove "%s" with %d users'
                    " while appending blend file:"
                    ' filepath="%s" filename="%s" directory="%s"',
                    library.name,
                    library.users,
                    append_filepath,
                    append_filename,
                    append_directory,
                )
            else:
                context.blend_data.libraries.remove(library)

            break
        return result
