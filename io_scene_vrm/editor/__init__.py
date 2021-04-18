from typing import List

import bpy


def find_export_objects(
    export_invisibles: bool, export_only_selections: bool
) -> List[bpy.types.Object]:
    print("Searching for VRM export objects:")

    objects = []
    if export_only_selections:
        print("  Selected objects:")
        objects = list(bpy.context.selected_objects)
    elif export_invisibles:
        print("  Select all objects:")
        objects = list(bpy.data.objects)
    else:
        print("  Select all selectable objects:")
        objects = list(bpy.context.selectable_objects)

    exclusion_types = ["LIGHT", "CAMERA"]
    export_objects = []
    for obj in objects:
        if obj.type in exclusion_types:
            print(f"  EXCLUDE: {obj.name}")
            continue
        if not export_invisibles and not obj.visible_get():
            print(f"  EXCLUDE: {obj.name}")
            continue
        export_objects.append(obj)

    for export_object in export_objects:
        print(f"  -> {export_object.name}")

    return export_objects
