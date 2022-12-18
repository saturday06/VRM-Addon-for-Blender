from dataclasses import dataclass
from sys import float_info
from typing import Dict, List, Optional, Sequence, Tuple, Union, cast

import bpy
from bpy.app.translations import pgettext

from ..common.logging import get_logger
from ..common.preferences import get_preferences

logger = get_logger(__name__)

MESH_CONVERTIBLE_OBJECT_TYPES = [
    "CURVE",
    "FONT",
    "MESH",
    # "META",  # Disable until the glTF 2.0 add-on supports it
    "SURFACE",
]


def export_materials(objects: List[bpy.types.Object]) -> List[bpy.types.Material]:
    result = []
    for mesh_convertible in [
        obj.data for obj in objects if obj.type in MESH_CONVERTIBLE_OBJECT_TYPES
    ]:
        if isinstance(mesh_convertible, (bpy.types.Curve, bpy.types.Mesh)):
            for material in mesh_convertible.materials:
                if isinstance(material, bpy.types.Material) and material not in result:
                    result.append(material)
        else:
            logger.error(
                f"Unexpected mesh convertible object type: {type(mesh_convertible)}"
            )
    return result


def object_candidates(context: bpy.types.Context) -> Sequence[bpy.types.Object]:
    preferences = get_preferences(context)
    if preferences.export_invisibles:
        objects = bpy.data.objects
    else:
        objects = context.selectable_objects
    return cast(Sequence[bpy.types.Object], objects)


def vrm_shader_node(material: bpy.types.Material) -> Optional[bpy.types.Node]:
    if not material.node_tree or not material.node_tree.nodes:
        return None
    for node in material.node_tree.nodes:
        if (
            node.type == "OUTPUT_MATERIAL"
            and node.inputs["Surface"].links
            and node.inputs["Surface"].links[0].from_node.type == "GROUP"
            and node.inputs["Surface"].links[0].from_node.node_tree.get("SHADER")
            is not None
        ):
            return node.inputs["Surface"].links[0].from_node
    return None


def shader_nodes_and_materials(
    materials: List[bpy.types.Material],
) -> List[Tuple[bpy.types.Node, bpy.types.Material]]:
    result = []
    for material in materials:
        node = vrm_shader_node(material)
        if node:
            result.append((node, material))
    return result


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


def current_armature(context: bpy.types.Context) -> Optional[bpy.types.Object]:
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
    ] = {context.scene.collection: None}

    collections = [context.scene.collection]
    while collections:
        parent = collections.pop()
        for child in parent.children:
            collections.append(child)
            collection_child_to_parent[child] = parent

    min_distance: Optional[Tuple[int, int, int, int]] = None
    nearest_object: Optional[bpy.types.Object] = None
    for obj in objects:
        distance = object_distance(active_object, obj, collection_child_to_parent)
        if min_distance is None or min_distance > distance:
            min_distance = distance
            nearest_object = obj

    return objects[0] if nearest_object is None else nearest_object


def export_objects(
    context: bpy.types.Context, export_invisibles: bool, export_only_selections: bool
) -> List[bpy.types.Object]:
    selected_objects = []
    if export_only_selections:
        selected_objects = list(context.selected_objects)
    elif export_invisibles:
        selected_objects = list(bpy.data.objects)
    else:
        selected_objects = list(context.selectable_objects)

    exclusion_types = ["LIGHT", "CAMERA"]
    objects = []
    for obj in selected_objects:
        if obj.type in exclusion_types:
            continue
        if obj.name not in context.view_layer.objects:
            continue
        if not export_invisibles and not obj.visible_get():
            continue
        objects.append(obj)

    return objects


@dataclass(frozen=True)
class ExportConstraint:
    roll_constraints: Dict[str, bpy.types.CopyRotationConstraint]
    aim_constraints: Dict[str, bpy.types.DampedTrackConstraint]
    rotation_constraints: Dict[str, bpy.types.CopyRotationConstraint]


def is_roll_constraint(
    constraint: bpy.types.Constraint,
    objs: List[bpy.types.Object],
    armature: bpy.types.Object,
) -> bool:
    return (
        isinstance(constraint, bpy.types.CopyRotationConstraint)
        and constraint.is_valid
        and not constraint.mute
        and constraint.target
        and constraint.target in objs
        and constraint.mix_mode == "ADD"
        and (int(constraint.use_x) + int(constraint.use_y) + int(constraint.use_z)) == 1
        and constraint.owner_space == "LOCAL"
        and constraint.target_space == "LOCAL"
        and (
            constraint.target.type != "ARMATURE"
            or (
                constraint.target == armature
                and constraint.subtarget in constraint.target.data.bones
            )
        )
    )


def is_aim_constraint(
    constraint: bpy.types.Constraint,
    objs: List[bpy.types.Object],
    armature: bpy.types.Object,
) -> bool:
    return (
        isinstance(constraint, bpy.types.DampedTrackConstraint)
        and constraint.is_valid
        and not constraint.mute
        and constraint.target
        and constraint.target in objs
        and (
            constraint.target.type != "ARMATURE"
            or (
                constraint.target == armature
                and constraint.subtarget in constraint.target.data.bones
                and abs(constraint.head_tail) < float_info.epsilon
            )
        )
    )


def is_rotation_constraint(
    constraint: bpy.types.Constraint,
    objs: List[bpy.types.Object],
    armature: bpy.types.Object,
) -> bool:
    return (
        isinstance(constraint, bpy.types.CopyRotationConstraint)
        and constraint.is_valid
        and not constraint.mute
        and constraint.target
        and constraint.target in objs
        and not constraint.invert_x
        and not constraint.invert_y
        and not constraint.invert_z
        and constraint.mix_mode == "ADD"
        and constraint.use_x
        and constraint.use_y
        and constraint.use_z
        and constraint.owner_space == "LOCAL"
        and constraint.target_space == "LOCAL"
        and (
            constraint.target.type != "ARMATURE"
            or (
                constraint.target == armature
                and constraint.subtarget in constraint.target.data.bones
            )
        )
    )


def export_object_constraints(
    objs: List[bpy.types.Object],
    armature: bpy.types.Object,
) -> ExportConstraint:
    roll_constraints: Dict[str, bpy.types.CopyRotationConstraint] = {}
    aim_constraints: Dict[str, bpy.types.DampedTrackConstraint] = {}
    rotation_constraints: Dict[str, bpy.types.CopyRotationConstraint] = {}

    for obj in objs:
        for constraint in obj.constraints:
            if is_roll_constraint(constraint, objs, armature):
                roll_constraints[obj.name] = constraint
                break
            if is_aim_constraint(constraint, objs, armature):
                aim_constraints[obj.name] = constraint
                break
            if is_rotation_constraint(constraint, objs, armature):
                rotation_constraints[obj.name] = constraint
                break

    return ExportConstraint(
        roll_constraints=roll_constraints,
        aim_constraints=aim_constraints,
        rotation_constraints=rotation_constraints,
    )


def export_bone_constraints(
    objs: List[bpy.types.Object],
    armature: bpy.types.Object,
) -> ExportConstraint:
    roll_constraints: Dict[str, bpy.types.CopyRotationConstraint] = {}
    aim_constraints: Dict[str, bpy.types.DampedTrackConstraint] = {}
    rotation_constraints: Dict[str, bpy.types.CopyRotationConstraint] = {}

    for bone in armature.pose.bones:
        for constraint in bone.constraints:
            if is_roll_constraint(constraint, objs, armature):
                roll_constraints[bone.name] = constraint
                break
            if is_aim_constraint(constraint, objs, armature):
                aim_constraints[bone.name] = constraint
                break
            if is_rotation_constraint(constraint, objs, armature):
                rotation_constraints[bone.name] = constraint
                break

    return ExportConstraint(
        roll_constraints=roll_constraints,
        aim_constraints=aim_constraints,
        rotation_constraints=rotation_constraints,
    )


def export_constraints(
    objs: List[bpy.types.Object],
    armature: bpy.types.Object,
) -> Tuple[ExportConstraint, ExportConstraint, List[str]]:
    messages: List[str] = []
    object_constraints = export_object_constraints(objs, armature)
    bone_constraints = export_bone_constraints(objs, armature)

    all_roll_constraints = list(object_constraints.roll_constraints.values()) + list(
        bone_constraints.roll_constraints.values()
    )
    all_rotation_constraints = list(
        object_constraints.rotation_constraints.values()
    ) + list(bone_constraints.rotation_constraints.values())
    all_constraints: List[bpy.types.CopyRotationConstraint] = (
        all_roll_constraints
        + all_rotation_constraints
        # TODO: Aim Constraint's circular dependency detection
        # + list(object_constraints.aim_constraints.values())
        # + list(bone_constraints.aim_constraints.values())
    )

    excluded_constraints: List[
        Union[
            bpy.types.CopyRotationConstraint,
            bpy.types.DampedTrackConstraint,
            bpy.types.CopyRotationConstraint,
        ]
    ] = []

    for search_constraint in all_constraints:
        current_constraints = [
            (
                search_constraint,
                (
                    search_constraint.use_x,
                    search_constraint.use_y,
                    search_constraint.use_z,
                ),
            )
        ]
        iterated_constraints = set()
        while current_constraints:
            current_constraint, current_axis = current_constraints.pop()

            if current_constraint in iterated_constraints:
                break
            iterated_constraints.add(current_constraint)

            found = False

            if current_constraint.target.type == "ARMATURE":
                bone = current_constraint.target.pose.bones[
                    current_constraint.subtarget
                ]
                owner_name = bone.name
                target_constraints = bone.constraints
            else:
                owner_name = current_constraint.target.name
                target_constraints = current_constraint.target.constraints

            for target_constraint in target_constraints:
                if target_constraint not in all_constraints:
                    continue

                next_target_axis = (
                    current_axis[0] and target_constraint.use_x,
                    current_axis[1] and target_constraint.use_y,
                    current_axis[2] and target_constraint.use_z,
                )
                if next_target_axis == (False, False, False):
                    continue

                if target_constraint != search_constraint:
                    current_constraints.append((target_constraint, next_target_axis))
                    continue

                excluded_constraints.append(search_constraint)
                messages.append(
                    pgettext(
                        'Node Constraint "{owner_name} / {constraint_name}" has a circular dependency'
                    ).format(
                        owner_name=owner_name,
                        constraint_name=search_constraint.name,
                    )
                )
                found = True
                break

            if found:
                break

    return (
        ExportConstraint(
            roll_constraints={
                k: v
                for k, v in object_constraints.roll_constraints.items()
                if v not in excluded_constraints
            },
            aim_constraints={
                k: v
                for k, v in object_constraints.aim_constraints.items()
                if v not in excluded_constraints
            },
            rotation_constraints={
                k: v
                for k, v in object_constraints.rotation_constraints.items()
                if v not in excluded_constraints
            },
        ),
        ExportConstraint(
            roll_constraints={
                k: v
                for k, v in bone_constraints.roll_constraints.items()
                if v not in excluded_constraints
            },
            aim_constraints={
                k: v
                for k, v in bone_constraints.aim_constraints.items()
                if v not in excluded_constraints
            },
            rotation_constraints={
                k: v
                for k, v in bone_constraints.rotation_constraints.items()
                if v not in excluded_constraints
            },
        ),
        messages,
    )
