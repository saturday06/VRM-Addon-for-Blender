# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import bpy
from bpy.types import Context, Object

from .logger import get_logger

_logger = get_logger(__name__)


def remove_object(context: Context, obj: Object) -> bool:
    for child in tuple(obj.children):
        if child.parent_type != obj.parent_type:
            child.parent_type = obj.parent_type
        if child.parent != obj.parent:
            child.parent = obj.parent
        if child.parent_bone != obj.parent_bone:
            child.parent_bone = obj.parent_bone

    for collection in tuple(obj.users_collection):
        if obj.name in collection.objects:
            collection.objects.unlink(obj)

    if obj.parent_type != "OBJECT":
        obj.parent_type = "OBJECT"
    if obj.parent is not None:
        obj.parent = None

    if obj.users:
        user_class_names = list[str]()
        _logger.debug("Object %r is used by %d users:", obj.name, obj.users)
        for users in context.blend_data.user_map(subset=(obj,)).values():
            for user in users:
                user_class_names.append(type(user).__name__)
                _logger.debug("  %r", user)

        # TODO: In Blender 5.2, Scene objects may remain as users.
        # Until the cause is identified, forcibly remove with do_unlink=True.
        if bpy.app.version >= (5, 2) and user_class_names == ["Scene"]:
            context.blend_data.objects.remove(obj, do_unlink=True)
            return True

        return False

    context.blend_data.objects.remove(obj, do_unlink=True)
    return True
