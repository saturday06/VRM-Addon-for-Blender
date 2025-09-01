# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from bpy.types import Context, Object


def remove_object(context: Context, obj: Object) -> bool:
    for collection in [
        *[scene.collection for scene in context.blend_data.scenes],
        *context.blend_data.collections,
    ]:
        for collection_object in collection.objects:
            if collection_object.parent != obj:
                continue
            if collection_object.parent_type != obj.parent_type:
                collection_object.parent_type = obj.parent_type
            if collection_object.parent != obj.parent:
                collection_object.parent = obj.parent
            if collection_object.parent_bone != obj.parent_bone:
                collection_object.parent_bone = obj.parent_bone

        if obj.name in collection.objects:
            collection.objects.unlink(obj)

    if obj.users:
        return False

    context.blend_data.objects.remove(obj, do_unlink=True)
    return True
