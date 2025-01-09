# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Optional, Union

from bpy.app.translations import pgettext
from bpy.types import (
    Armature,
    Collection,
    Constraint,
    Context,
    CopyRotationConstraint,
    Curve,
    DampedTrackConstraint,
    Material,
    Mesh,
    Object,
    ObjectConstraints,
    PoseBoneConstraints,
    ShaderNodeGroup,
    ShaderNodeOutputMaterial,
)

from ..common.logger import get_logger
from .extension import get_armature_extension

logger = get_logger(__name__)

MESH_CONVERTIBLE_OBJECT_TYPES = [
    "CURVE",
    "FONT",
    "MESH",
    # "META",  # Disable until the glTF 2.0 add-on supports it
    "SURFACE",
]


def export_materials(context: Context, objects: Sequence[Object]) -> Sequence[Material]:
    result: list[Material] = []
    for obj in objects:
        if obj.type not in MESH_CONVERTIBLE_OBJECT_TYPES:
            continue

        mesh_convertible = obj.data
        if isinstance(mesh_convertible, (Curve, Mesh)):
            for material_ref in mesh_convertible.materials:
                if not isinstance(material_ref, Material):
                    continue
                material = context.blend_data.materials.get(material_ref.name)
                if not isinstance(material, Material):
                    continue
                result.append(material)
        else:
            logger.error(
                "Unexpected mesh convertible object type: %s", type(mesh_convertible)
            )

        for material_slot in obj.material_slots:
            if not material_slot:
                continue
            material_ref = material_slot.material
            if not material_ref:
                continue
            material = context.blend_data.materials.get(material_ref.name)
            if not isinstance(material, Material):
                continue
            result.append(material)

    return list(dict.fromkeys(result))  # 重複削除


LEGACY_SHADER_NAMES: Final = (
    "MToon_unversioned",
    "GLTF",
    "TRANSPARENT_ZWRITE",
)


def legacy_shader_node(
    material: Material,
) -> tuple[Optional[ShaderNodeGroup], Optional[str]]:
    if not material.use_nodes:
        return (None, None)

    node_tree = material.node_tree
    if not node_tree:
        return (None, None)

    for node in node_tree.nodes:
        if node.mute:
            continue

        if not isinstance(node, ShaderNodeOutputMaterial):
            continue

        surface_socket = node.inputs.get("Surface")
        if not surface_socket:
            continue

        links = surface_socket.links
        if not links:
            continue

        link = links[0]
        if not link.is_valid or link.is_muted:
            continue

        group_node = link.from_node
        if group_node.mute:
            continue

        if not isinstance(group_node, ShaderNodeGroup):
            continue

        group_node_tree = group_node.node_tree
        if not group_node_tree:
            continue

        legacy_shader_name = group_node_tree.get("SHADER")
        if not isinstance(legacy_shader_name, str):
            continue

        return (group_node, legacy_shader_name)

    return (None, None)


def shader_nodes_and_materials(
    materials: Sequence[Material],
) -> Sequence[tuple[ShaderNodeGroup, str, Material]]:
    result: list[tuple[ShaderNodeGroup, str, Material]] = []
    for material in materials:
        node, legacy_shader_name = legacy_shader_node(material)
        if node is not None and legacy_shader_name is not None:
            result.append((node, legacy_shader_name, material))
    return result


def object_distance(
    left: Object,
    right: Object,
    collection_child_to_parent: dict[Collection, Optional[Collection]],
) -> tuple[int, int, int, int]:
    left_collection_path: list[Collection] = []
    left_collections = [
        collection
        for collection in left.users_collection
        if collection in collection_child_to_parent
    ]
    if left_collections:
        left_collection: Optional[Collection] = left_collections[0]
        while left_collection:
            left_collection_path.insert(0, left_collection)
            left_collection = collection_child_to_parent.get(left_collection)

    right_collection_path: list[Collection] = []
    right_collections = [
        collection
        for collection in right.users_collection
        if collection in collection_child_to_parent
    ]
    if right_collections:
        right_collection: Optional[Collection] = right_collections[0]
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

    left_parent_path: list[Object] = []
    traversing_left: Optional[Object] = left
    while traversing_left:
        left_parent_path.insert(0, traversing_left)
        traversing_left = traversing_left.parent

    right_parent_path: list[Object] = []
    traversing_right: Optional[Object] = right
    while traversing_right:
        right_parent_path.insert(0, traversing_right)
        traversing_right = traversing_right.parent

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


def armature_exists(context: Context) -> bool:
    return any(armature.users for armature in context.blend_data.armatures) and any(
        obj.type == "ARMATURE" for obj in context.blend_data.objects
    )


def current_armature_is_vrm0(context: Context) -> bool:
    live_armature_datum = [
        armature_data
        for armature_data in context.blend_data.armatures
        if armature_data.users
    ]
    if not live_armature_datum:
        return False
    if all(
        hasattr(armature_data, "vrm_addon_extension")
        and get_armature_extension(armature_data).is_vrm0()
        for armature_data in live_armature_datum
    ) and any(obj.type == "ARMATURE" for obj in context.blend_data.objects):
        return True
    armature = current_armature(context)
    if armature is None:
        return False
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return False
    return get_armature_extension(armature_data).is_vrm0()


def current_armature_is_vrm1(context: Context) -> bool:
    live_armature_datum = [
        armature_data
        for armature_data in context.blend_data.armatures
        if armature_data.users
    ]
    if not live_armature_datum:
        return False
    if all(
        hasattr(armature_data, "vrm_addon_extension")
        and get_armature_extension(armature_data).is_vrm1()
        for armature_data in live_armature_datum
    ) and any(obj.type == "ARMATURE" for obj in context.blend_data.objects):
        return True
    armature = current_armature(context)
    if armature is None:
        return False
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return False
    return get_armature_extension(armature_data).is_vrm1()


def multiple_armatures_exist(context: Context) -> bool:
    first_data_exists = False
    for data in context.blend_data.armatures:
        if not data.users:
            continue
        if not first_data_exists:
            first_data_exists = True
            continue

        first_obj_exists = False
        for obj in context.blend_data.objects:
            if obj.type == "ARMATURE":
                if first_obj_exists:
                    return True
                first_obj_exists = True
        break
    return False


def current_armature(context: Context) -> Optional[Object]:
    objects = [obj for obj in context.blend_data.objects if obj.type == "ARMATURE"]
    if not objects:
        return None

    if len(objects) == 1:
        return objects[0]

    active_object = getattr(context, "active_object", None)
    if not isinstance(active_object, Object):
        active_object = context.view_layer.objects.active
    if not active_object:
        return objects[0]

    collection_child_to_parent: dict[Collection, Optional[Collection]] = {
        context.scene.collection: None
    }

    collections = [context.scene.collection]
    while collections:
        parent = collections.pop()
        for child in parent.children:
            collections.append(child)
            collection_child_to_parent[child] = parent

    min_distance: Optional[tuple[int, int, int, int]] = None
    nearest_object: Optional[Object] = None
    for obj in objects:
        distance = object_distance(active_object, obj, collection_child_to_parent)
        if min_distance is None or min_distance > distance:
            min_distance = distance
            nearest_object = obj

    return objects[0] if nearest_object is None else nearest_object


def export_objects(
    context: Context,
    armature_object_name: Optional[str],
    *,
    export_invisibles: bool,
    export_only_selections: bool,
    export_lights: bool,
) -> list[Object]:
    selected_objects = []
    if export_only_selections:
        selected_objects = list(context.selected_objects)
    elif export_invisibles:
        selected_objects = list(context.blend_data.objects)
    else:
        selected_objects = list(context.selectable_objects)

    objects: list[Object] = []

    # https://projects.blender.org/blender/blender/issues/113378
    context.view_layer.update()

    armature_object = None
    if armature_object_name:
        armature_object = context.blend_data.objects.get(armature_object_name)
        if armature_object and armature_object.name in context.view_layer.objects:
            objects.append(armature_object)
        else:
            armature_object = None
    if not armature_object:
        objects.extend(
            obj
            for obj in context.blend_data.objects
            if obj.type == "ARMATURE" and obj.name in context.view_layer.objects
        )

    collider_bpy_objects: list[Optional[Object]] = []
    for armature_data in context.blend_data.armatures:
        ext = get_armature_extension(armature_data)
        for spring_bone1_collider in ext.spring_bone1.colliders:
            if not spring_bone1_collider.bpy_object:
                continue
            collider_bpy_objects.append(spring_bone1_collider.bpy_object)
            collider_bpy_objects.extend(spring_bone1_collider.bpy_object.children)
        for collider_group in ext.vrm0.secondary_animation.collider_groups:
            collider_bpy_objects.extend(
                collider.bpy_object for collider in collider_group.colliders
            )

    for obj in selected_objects:
        if obj.type in ["ARMATURE", "CAMERA"]:
            continue
        if obj.type == "LIGHT" and not export_lights:
            continue
        if obj.name not in context.view_layer.objects:
            continue
        if not export_invisibles and not obj.visible_get():
            continue
        objects.append(obj)

    return [
        # コライダーと重複の削除
        obj
        for obj in dict.fromkeys(objects)
        if obj not in collider_bpy_objects
    ]


@dataclass(frozen=True)
class ExportConstraint:
    roll_constraints: dict[str, CopyRotationConstraint]
    aim_constraints: dict[str, DampedTrackConstraint]
    rotation_constraints: dict[str, CopyRotationConstraint]

    @property
    def all_constraints(self) -> list[tuple[str, Constraint]]:
        all_constraints: list[tuple[str, Constraint]] = []
        all_constraints.extend(self.roll_constraints.items())
        all_constraints.extend(self.aim_constraints.items())
        all_constraints.extend(self.rotation_constraints.items())
        return all_constraints


def roll_constraint_or_none(
    constraint: Constraint,
    objs: Sequence[Object],
    armature: Object,
) -> Optional[CopyRotationConstraint]:
    if (
        not isinstance(constraint, CopyRotationConstraint)
        or not constraint.is_valid
        or constraint.mute
        or not constraint.target
        or constraint.target not in objs
        or constraint.mix_mode != "ADD"
        or (int(constraint.use_x) + int(constraint.use_y) + int(constraint.use_z)) != 1
        or constraint.owner_space != "LOCAL"
        or constraint.target_space != "LOCAL"
    ):
        return None

    if constraint.target.type != "ARMATURE":
        return constraint

    if constraint.target != armature:
        return None

    armature_data = armature.data
    if (
        not isinstance(armature_data, Armature)
        or constraint.subtarget not in armature_data.bones
    ):
        return None

    return constraint


def aim_constraint_or_none(
    constraint: Constraint,
    objs: Sequence[Object],
    armature: Object,
) -> Optional[DampedTrackConstraint]:
    if (
        not isinstance(constraint, DampedTrackConstraint)
        or not constraint.is_valid
        or constraint.mute
        or not constraint.target
        or constraint.target not in objs
    ):
        return None

    if constraint.target.type != "ARMATURE":
        return constraint

    if constraint.target != armature:
        return None

    armature_data = armature.data
    if (
        not isinstance(armature_data, Armature)
        or constraint.subtarget not in armature_data.bones
        or abs(constraint.head_tail) > 0
    ):
        return None

    return constraint


def rotation_constraint_or_none(
    constraint: Constraint,
    objs: Sequence[Object],
    armature: Object,
) -> Optional[CopyRotationConstraint]:
    if (
        not isinstance(constraint, CopyRotationConstraint)
        or not constraint.is_valid
        or constraint.mute
        or not constraint.target
        or constraint.target not in objs
        or constraint.invert_x
        or constraint.invert_y
        or constraint.invert_z
        or constraint.mix_mode != "ADD"
        or not constraint.use_x
        or not constraint.use_y
        or not constraint.use_z
        or constraint.owner_space != "LOCAL"
        or constraint.target_space != "LOCAL"
    ):
        return None

    if constraint.target.type != "ARMATURE":
        return constraint

    if constraint.target != armature:
        return None

    armature_data = armature.data
    if (
        not isinstance(armature_data, Armature)
        or constraint.subtarget not in armature_data.bones
    ):
        return None

    return constraint


def export_object_constraints(
    objs: Sequence[Object],
    armature: Object,
) -> ExportConstraint:
    roll_constraints: dict[str, CopyRotationConstraint] = {}
    aim_constraints: dict[str, DampedTrackConstraint] = {}
    rotation_constraints: dict[str, CopyRotationConstraint] = {}

    for obj in objs:
        for constraint in obj.constraints:
            roll_constraint = roll_constraint_or_none(constraint, objs, armature)
            if roll_constraint:
                roll_constraints[obj.name] = roll_constraint
                break
            aim_constraint = aim_constraint_or_none(constraint, objs, armature)
            if aim_constraint:
                aim_constraints[obj.name] = aim_constraint
                break
            rotation_constraint = rotation_constraint_or_none(
                constraint, objs, armature
            )
            if rotation_constraint:
                rotation_constraints[obj.name] = rotation_constraint
                break

    return ExportConstraint(
        roll_constraints=roll_constraints,
        aim_constraints=aim_constraints,
        rotation_constraints=rotation_constraints,
    )


def export_bone_constraints(
    objs: Sequence[Object],
    armature: Object,
) -> ExportConstraint:
    roll_constraints: dict[str, CopyRotationConstraint] = {}
    aim_constraints: dict[str, DampedTrackConstraint] = {}
    rotation_constraints: dict[str, CopyRotationConstraint] = {}

    for bone in armature.pose.bones:
        for constraint in bone.constraints:
            roll_constraint = roll_constraint_or_none(constraint, objs, armature)
            if roll_constraint:
                roll_constraints[bone.name] = roll_constraint
                break
            aim_constraint = aim_constraint_or_none(constraint, objs, armature)
            if aim_constraint:
                aim_constraints[bone.name] = aim_constraint
                break
            rotation_constraint = rotation_constraint_or_none(
                constraint, objs, armature
            )
            if rotation_constraint:
                rotation_constraints[bone.name] = rotation_constraint
                break

    return ExportConstraint(
        roll_constraints=roll_constraints,
        aim_constraints=aim_constraints,
        rotation_constraints=rotation_constraints,
    )


def export_constraints(
    objs: Sequence[Object],
    armature: Object,
) -> tuple[ExportConstraint, ExportConstraint, Sequence[str]]:
    messages: list[str] = []
    object_constraints = export_object_constraints(objs, armature)
    bone_constraints = export_bone_constraints(objs, armature)

    all_roll_constraints: list[CopyRotationConstraint] = list(
        object_constraints.roll_constraints.values()
    ) + list(bone_constraints.roll_constraints.values())
    all_rotation_constraints: list[CopyRotationConstraint] = list(
        object_constraints.rotation_constraints.values()
    ) + list(bone_constraints.rotation_constraints.values())

    # TODO: Aim Constraint's circular dependency detection
    # + list(object_constraints.aim_constraints.values())
    # + list(bone_constraints.aim_constraints.values())
    all_constraints: list[Constraint] = []
    all_constraints.extend(all_roll_constraints)
    all_constraints.extend(all_rotation_constraints)

    excluded_constraints: list[
        Union[
            CopyRotationConstraint,
            DampedTrackConstraint,
        ]
    ] = []

    for search_constraint in all_constraints:
        if not isinstance(search_constraint, CopyRotationConstraint):
            continue
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
        iterated_constraints: set[Constraint] = set()
        while current_constraints:
            current_constraint, current_axis = current_constraints.pop()

            if current_constraint in iterated_constraints:
                break
            iterated_constraints.add(current_constraint)

            found = False

            target = current_constraint.target
            if not target:
                continue

            if target.type == "ARMATURE":
                bone = target.pose.bones[current_constraint.subtarget]
                owner_name = bone.name
                target_constraints: Union[ObjectConstraints, PoseBoneConstraints] = (
                    bone.constraints
                )
            else:
                owner_name = target.name
                target_constraints = target.constraints

            for target_constraint in target_constraints:
                if not isinstance(target_constraint, CopyRotationConstraint):
                    continue
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
                        'Node Constraint "{owner_name} / {constraint_name}" has'
                        + " a circular dependency"
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


def active_object_is_vrm1_armature(context: Context) -> bool:
    active_object = context.active_object
    if not active_object:
        return False
    if active_object.type != "ARMATURE":
        return False
    armature_data = active_object.data
    if not isinstance(armature_data, Armature):
        return False
    return get_armature_extension(armature_data).is_vrm1()


def active_object_is_vrm0_armature(context: Context) -> bool:
    active_object = context.active_object
    if not active_object:
        return False
    if active_object.type != "ARMATURE":
        return False
    armature_data = active_object.data
    if not isinstance(armature_data, Armature):
        return False
    return get_armature_extension(armature_data).is_vrm0()
