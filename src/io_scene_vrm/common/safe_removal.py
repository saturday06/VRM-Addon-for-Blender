# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from bpy.types import Context, Object


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

    if obj.users:
        return False

    context.blend_data.objects.remove(obj, do_unlink=True)
    return True
