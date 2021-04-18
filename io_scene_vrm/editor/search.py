from typing import List, Tuple

import bpy


def shader_nodes_and_materials(
    used_materials: List[bpy.types.Material],
) -> List[Tuple[bpy.types.Node, bpy.types.Material]]:
    return [
        (node.inputs["Surface"].links[0].from_node, mat)
        for mat in used_materials
        if mat.node_tree is not None
        for node in mat.node_tree.nodes
        if node.type == "OUTPUT_MATERIAL"
        and node.inputs["Surface"].links
        and node.inputs["Surface"].links[0].from_node.type == "GROUP"
        and node.inputs["Surface"].links[0].from_node.node_tree.get("SHADER")
        is not None
    ]


def export_objects(
    export_invisibles: bool, export_only_selections: bool
) -> List[bpy.types.Object]:
    print("Searching for VRM export objects:")

    selected_objects = []
    if export_only_selections:
        print("  Selected objects:")
        selected_objects = list(bpy.context.selected_objects)
    elif export_invisibles:
        print("  Select all objects:")
        selected_objects = list(bpy.data.objects)
    else:
        print("  Select all selectable objects:")
        selected_objects = list(bpy.context.selectable_objects)

    exclusion_types = ["LIGHT", "CAMERA"]
    objects = []
    for obj in selected_objects:
        if obj.type in exclusion_types:
            print(f"  EXCLUDE: {obj.name}")
            continue
        if not export_invisibles and not obj.visible_get():
            print(f"  EXCLUDE: {obj.name}")
            continue
        objects.append(obj)

    for obj in objects:
        print(f"  -> {obj.name}")

    return objects
