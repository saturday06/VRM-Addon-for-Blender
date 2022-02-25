from typing import Dict, List, Optional, Sequence, Tuple, cast

import bpy

from ..common.preferences import VrmAddonPreferences, get_preferences


def object_candidates(context: bpy.types.Context) -> Sequence[bpy.types.Object]:
    preferences = get_preferences(context)
    if isinstance(preferences, VrmAddonPreferences) and bool(
        preferences.export_invisibles
    ):
        objects = bpy.data.objects
    else:
        objects = context.selectable_objects
    return cast(Sequence[bpy.types.Object], objects)


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


def object_distance(
    left: bpy.types.Object,
    right: bpy.types.Object,
    collection_child_to_parent: Dict[
        bpy.types.Collection, Optional[bpy.types.Collection]
    ],
) -> Tuple[int, int, int, int]:
    left_collection_path: List[bpy.types.Collection] = []
    left_collections = [
        collection
        for collection in left.users_collection
        if collection in collection_child_to_parent
    ]
    if left_collections:
        left_collection = left_collections[0]
        while left_collection:
            left_collection_path.insert(0, left_collection)
            left_collection = collection_child_to_parent.get(left_collection)

    right_collection_path: List[bpy.types.Collection] = []
    right_collections = [
        collection
        for collection in right.users_collection
        if collection in collection_child_to_parent
    ]
    if right_collections:
        right_collection = right_collections[0]
        while right_collection:
            right_collection_path.insert(0, right_collection)
            right_collection = collection_child_to_parent.get(right_collection)

    while (
        left_collection_path
        and right_collection_path
        and left_collection_path[0] == right_collection_path[0]
    ):
        left_collection_path.pop(0)
        right_collection_path.pop(0)

    left_parent_path: List[bpy.types.Object] = []
    while left:
        left_parent_path.insert(0, left)
        left = left.parent

    right_parent_path: List[bpy.types.Object] = []
    while right:
        right_parent_path.insert(0, right)
        right = right.parent

    while (
        left_parent_path
        and right_parent_path
        and left_parent_path[0] == right_parent_path[0]
    ):
        left_parent_path.pop(0)
        right_parent_path.pop(0)

    return (
        len(left_parent_path),
        len(right_parent_path),
        len(left_collection_path),
        len(right_collection_path),
    )


def armature_exists(context: bpy.types.Object) -> bool:
    return any(armature.users for armature in bpy.data.armatures) and any(
        obj.type == "ARMATURE" for obj in object_candidates(context)
    )


def current_armature_is_vrm0(context: bpy.types.Context) -> bool:
    live_armature_datum = [
        armature_data for armature_data in bpy.data.armatures if armature_data.users
    ]
    if not live_armature_datum:
        return False
    if all(
        hasattr(armature_data, "vrm_addon_extension")
        and armature_data.vrm_addon_extension.is_vrm0()
        for armature_data in live_armature_datum
    ) and any(obj.type == "ARMATURE" for obj in object_candidates(context)):
        return True
    armature = current_armature(context)
    if armature is None:
        return False
    return bool(armature.data.vrm_addon_extension.is_vrm0())


def current_armature_is_vrm1(context: bpy.types.Context) -> bool:
    live_armature_datum = [
        armature_data for armature_data in bpy.data.armatures if armature_data.users
    ]
    if not live_armature_datum:
        return False
    if all(
        hasattr(armature_data, "vrm_addon_extension")
        and armature_data.vrm_addon_extension.is_vrm1()
        for armature_data in live_armature_datum
    ) and any(obj.type == "ARMATURE" for obj in object_candidates(context)):
        return True
    armature = current_armature(context)
    if armature is None:
        return False
    return bool(armature.data.vrm_addon_extension.is_vrm1())


def multiple_armatures_exist(context: bpy.types.Object) -> bool:
    first_data_exists = False
    for data in bpy.data.armatures:
        if not data.users:
            continue
        if not first_data_exists:
            first_data_exists = True
            continue

        first_obj_exists = False
        for obj in object_candidates(context):
            if obj.type == "ARMATURE":
                if first_obj_exists:
                    return True
                first_obj_exists = True
        break
    return False


def current_armature(context: bpy.types.Object) -> Optional[bpy.types.Object]:
    objects = [obj for obj in object_candidates(context) if obj.type == "ARMATURE"]
    if not objects:
        return None

    if len(objects) == 1:
        return objects[0]

    active_object = context.active_object
    if not active_object:
        active_object = context.view_layer.objects.active
    if not active_object:
        return objects[0]

    collection_child_to_parent: Dict[
        bpy.types.Collection, Optional[bpy.types.Collection]
    ] = {bpy.context.scene.collection: None}

    collections = [bpy.context.scene.collection]
    while collections:
        parent = collections.pop()
        for child in parent.children:
            collections.append(child)
            collection_child_to_parent[child] = parent

    object_to_distance: Dict[bpy.types.Object, Tuple[int, int, int, int]] = {}
    for obj in objects:
        object_to_distance[obj] = object_distance(
            active_object, obj, collection_child_to_parent
        )

    sorted_objs = [
        sorted_obj
        for (_, _, sorted_obj) in sorted(
            [(distance, obj.name, obj) for obj, distance in object_to_distance.items()]
        )
    ]
    return sorted_objs[0] if sorted_objs else None


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
