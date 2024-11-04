# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import contextlib
import json
import uuid
from typing import Optional

from bpy.types import ID, Armature, Context, Mesh, Object, Text

from ...common import convert, ops
from ...common.convert import Json
from ...common.deep import make_json
from ...common.vrm0.human_bone import HumanBoneSpecifications
from ..extension import get_armature_extension, get_bone_extension
from ..property_group import BonePropertyGroup
from .property_group import (
    Vrm0BlendShapeMasterPropertyGroup,
    Vrm0FirstPersonPropertyGroup,
    Vrm0HumanoidPropertyGroup,
    Vrm0MeshAnnotationPropertyGroup,
    Vrm0MetaPropertyGroup,
    Vrm0PropertyGroup,
    Vrm0SecondaryAnimationPropertyGroup,
)


def read_textblock_json(context: Context, armature: Object, armature_key: str) -> Json:
    text_key = armature.get(armature_key)
    if isinstance(text_key, Text):
        textblock: Optional[Text] = text_key
    elif not isinstance(text_key, str):
        return None
    else:
        textblock = context.blend_data.texts.get(text_key)
    if not isinstance(textblock, Text):
        return None
    textblock_str = "".join([line.body for line in textblock.lines])
    with contextlib.suppress(json.JSONDecodeError):
        return make_json(json.loads(textblock_str))
    return None


def migrate_vrm0_meta(
    context: Context, meta: Vrm0MetaPropertyGroup, armature: Object
) -> None:
    allowed_user_name = armature.get("allowedUserName")
    if (
        isinstance(allowed_user_name, str)
        and allowed_user_name
        in Vrm0MetaPropertyGroup.allowed_user_name_enum.identifiers()
    ):
        meta.allowed_user_name = allowed_user_name

    author = armature.get("author")
    if isinstance(author, str):
        meta.author = author

    commercial_ussage_name = armature.get("commercialUssageName")
    if (
        isinstance(commercial_ussage_name, str)
        and commercial_ussage_name
        in Vrm0MetaPropertyGroup.commercial_ussage_name_enum.identifiers()
    ):
        meta.commercial_ussage_name = commercial_ussage_name

    contact_information = armature.get("contactInformation")
    if isinstance(contact_information, str):
        meta.contact_information = contact_information

    license_name = armature.get("licenseName")
    if (
        isinstance(license_name, str)
        and license_name in Vrm0MetaPropertyGroup.license_name_enum.identifiers()
    ):
        meta.license_name = license_name

    other_license_url = armature.get("otherLicenseUrl")
    if isinstance(other_license_url, str):
        meta.other_license_url = other_license_url

    other_permission_url = armature.get("otherPermissionUrl")
    if isinstance(other_permission_url, str):
        meta.other_permission_url = other_permission_url

    reference = armature.get("reference")
    if isinstance(reference, str):
        meta.reference = reference

    sexual_ussage_name = armature.get("sexualUssageName")
    if (
        isinstance(sexual_ussage_name, str)
        and sexual_ussage_name
        in Vrm0MetaPropertyGroup.sexual_ussage_name_enum.identifiers()
    ):
        meta.sexual_ussage_name = sexual_ussage_name

    title = armature.get("title")
    if isinstance(title, str):
        meta.title = title

    version = armature.get("version")
    if isinstance(version, str):
        meta.version = version

    violent_ussage_name = armature.get("violentUssageName")
    if (
        isinstance(violent_ussage_name, str)
        and violent_ussage_name
        in Vrm0MetaPropertyGroup.violent_ussage_name_enum.identifiers()
    ):
        meta.violent_ussage_name = violent_ussage_name

    texture = armature.get("texture")
    if isinstance(texture, str):
        texture_image = context.blend_data.images.get(texture)
        if texture_image:
            meta.texture = texture_image


def migrate_vrm0_humanoid(
    humanoid: Vrm0HumanoidPropertyGroup, humanoid_dict: Json
) -> None:
    if not isinstance(humanoid_dict, dict):
        return

    arm_stretch = humanoid_dict.get("armStretch")
    if isinstance(arm_stretch, (int, float)):
        humanoid.arm_stretch = arm_stretch

    leg_stretch = humanoid_dict.get("legStretch")
    if isinstance(leg_stretch, (int, float)):
        humanoid.leg_stretch = leg_stretch

    upper_arm_twist = humanoid_dict.get("upperArmTwist")
    if isinstance(upper_arm_twist, (int, float)):
        humanoid.upper_arm_twist = upper_arm_twist

    lower_arm_twist = humanoid_dict.get("lowerArmTwist")
    if isinstance(lower_arm_twist, (int, float)):
        humanoid.lower_arm_twist = lower_arm_twist

    upper_leg_twist = humanoid_dict.get("upperLegTwist")
    if isinstance(upper_leg_twist, (int, float)):
        humanoid.upper_leg_twist = upper_leg_twist

    lower_leg_twist = humanoid_dict.get("lowerLegTwist")
    if isinstance(lower_leg_twist, (int, float)):
        humanoid.lower_leg_twist = lower_leg_twist

    feet_spacing = humanoid_dict.get("feetSpacing")
    if isinstance(feet_spacing, (int, float)):
        humanoid.feet_spacing = feet_spacing

    has_translation_dof = humanoid_dict.get("hasTranslationDoF")
    if isinstance(has_translation_dof, bool):
        humanoid.has_translation_dof = has_translation_dof


def migrate_vrm0_first_person(
    context: Context,
    first_person: Vrm0FirstPersonPropertyGroup,
    first_person_dict: Json,
) -> None:
    if not isinstance(first_person_dict, dict):
        return

    first_person_bone = first_person_dict.get("firstPersonBone")
    if isinstance(first_person_bone, str):
        first_person.first_person_bone.set_bone_name(first_person_bone)

    first_person_bone_offset = convert.vrm_json_vector3_to_tuple(
        first_person_dict.get("firstPersonBoneOffset")
    )
    if first_person_bone_offset is not None:
        # Axis confusing
        (x, y, z) = first_person_bone_offset
        first_person.first_person_bone_offset = (x, z, y)

    mesh_annotation_dicts = first_person_dict.get("meshAnnotations")
    if isinstance(mesh_annotation_dicts, list):
        for mesh_annotation_dict in mesh_annotation_dicts:
            mesh_annotation = first_person.mesh_annotations.add()

            if not isinstance(mesh_annotation_dict, dict):
                continue

            mesh = mesh_annotation_dict.get("mesh")
            if isinstance(mesh, str):
                if mesh in context.blend_data.meshes:
                    for obj in context.blend_data.objects:
                        if obj.data == context.blend_data.meshes[mesh]:
                            mesh_annotation.mesh.mesh_object_name = obj.name
                            break
                elif (
                    mesh in context.blend_data.objects
                    and context.blend_data.objects[mesh].type == "MESH"
                ):
                    mesh_annotation.mesh.mesh_object_name = context.blend_data.objects[
                        mesh
                    ].name

            first_person_flag = mesh_annotation_dict.get("firstPersonFlag")
            if (
                isinstance(first_person_flag, str)
                and first_person_flag
                in Vrm0MeshAnnotationPropertyGroup.first_person_flag_enum.identifiers()
            ):
                mesh_annotation.first_person_flag = first_person_flag

    look_at_type_name = first_person_dict.get("lookAtTypeName")
    if (
        isinstance(look_at_type_name, str)
        and look_at_type_name in first_person.look_at_type_name_enum.identifiers()
    ):
        first_person.look_at_type_name = look_at_type_name

    for look_at, look_at_dict in [
        (
            first_person.look_at_horizontal_inner,
            first_person_dict.get("lookAtHorizontalInner"),
        ),
        (
            first_person.look_at_horizontal_outer,
            first_person_dict.get("lookAtHorizontalOuter"),
        ),
        (
            first_person.look_at_vertical_down,
            first_person_dict.get("lookAtVerticalDown"),
        ),
        (
            first_person.look_at_vertical_up,
            first_person_dict.get("lookAtVerticalUp"),
        ),
    ]:
        if not isinstance(look_at_dict, dict):
            continue

        curve = convert.vrm_json_curve_to_list(look_at_dict.get("curve"))
        if curve is not None:
            look_at.curve = curve

        x_range = look_at_dict.get("xRange")
        if isinstance(x_range, (float, int)):
            look_at.x_range = x_range

        y_range = look_at_dict.get("yRange")
        if isinstance(y_range, (float, int)):
            look_at.y_range = y_range


def migrate_vrm0_blend_shape_groups(
    context: Context,
    blend_shape_master: Vrm0BlendShapeMasterPropertyGroup,
    blend_shape_group_dicts: Json,
) -> None:
    if not isinstance(blend_shape_group_dicts, list):
        return

    for blend_shape_group_dict in blend_shape_group_dicts:
        blend_shape_group = blend_shape_master.blend_shape_groups.add()
        if not isinstance(blend_shape_group_dict, dict):
            continue

        name = blend_shape_group_dict.get("name")
        if isinstance(name, str):
            blend_shape_group.name = name

        preset_name = blend_shape_group_dict.get("presetName")
        if (
            isinstance(preset_name, str)
            and preset_name in blend_shape_group.preset_name_enum.identifiers()
        ):
            blend_shape_group.preset_name = preset_name

        bind_dicts = blend_shape_group_dict.get("binds")
        if isinstance(bind_dicts, list):
            for bind_dict in bind_dicts:
                bind = blend_shape_group.binds.add()

                if not isinstance(bind_dict, dict):
                    continue

                mesh_name = bind_dict.get("mesh")
                if isinstance(mesh_name, str):
                    if mesh_name in context.blend_data.meshes:
                        mesh: Optional[ID] = context.blend_data.meshes[mesh_name]
                        for obj in context.blend_data.objects:
                            if obj.data == mesh:
                                bind.mesh.mesh_object_name = obj.name
                                break
                    elif (
                        mesh_name in context.blend_data.objects
                        and context.blend_data.objects[mesh_name].type == "MESH"
                    ):
                        obj = context.blend_data.objects[mesh_name]
                        bind.mesh.mesh_object_name = obj.name
                        mesh = obj.data
                    else:
                        mesh = None

                    if isinstance(mesh, Mesh):
                        index = bind_dict.get("index")
                        shape_keys = mesh.shape_keys
                        if (
                            isinstance(index, str)
                            and shape_keys
                            and index in shape_keys.key_blocks
                        ):
                            bind.index = index

                weight = bind_dict.get("weight")
                if isinstance(weight, (int, float)):
                    bind.weight = weight

        material_value_dicts = blend_shape_group_dict.get("materialValues")
        if isinstance(material_value_dicts, list):
            for material_value_dict in material_value_dicts:
                material_value = blend_shape_group.material_values.add()

                if not isinstance(material_value_dict, dict):
                    continue

                material_name = material_value_dict.get("materialName")
                if (
                    isinstance(material_name, str)
                    and material_name in context.blend_data.materials
                ):
                    material_value.material = context.blend_data.materials[
                        material_name
                    ]

                property_name = material_value_dict.get("propertyName")
                if isinstance(property_name, str):
                    material_value.property_name = property_name

                target_value_vector = material_value_dict.get("targetValue")
                if isinstance(target_value_vector, list):
                    for v in target_value_vector:
                        material_value.target_value.add().value = (
                            v if isinstance(v, (int, float)) else 0
                        )

        is_binary = blend_shape_group_dict.get("isBinary")
        if isinstance(is_binary, bool):
            blend_shape_group.is_binary = is_binary


def migrate_vrm0_secondary_animation(
    secondary_animation: Vrm0SecondaryAnimationPropertyGroup,
    bone_group_dicts: Json,
    armature: Object,
    armature_data: Armature,
) -> None:
    bone_name_to_collider_objects: dict[str, list[Object]] = {}
    for collider_object in [
        child
        for child in armature.children
        if child.type == "EMPTY"
        and child.empty_display_type == "SPHERE"
        and child.parent_type == "BONE"
        and child.parent_bone in armature_data.bones
    ]:
        if collider_object.parent_bone not in bone_name_to_collider_objects:
            bone_name_to_collider_objects[collider_object.parent_bone] = []
        bone_name_to_collider_objects[collider_object.parent_bone].append(
            collider_object
        )

    for bone_name, collider_objects in bone_name_to_collider_objects.items():
        collider_group = secondary_animation.collider_groups.add()
        collider_group.uuid = uuid.uuid4().hex
        collider_group.node.set_bone_name(bone_name)
        for collider_object in collider_objects:
            collider_prop = collider_group.colliders.add()
            collider_prop.bpy_object = collider_object

    for collider_group in secondary_animation.collider_groups:
        collider_group.refresh(armature)

    if not isinstance(bone_group_dicts, list):
        bone_group_dicts = []

    for bone_group_dict in bone_group_dicts:
        bone_group = secondary_animation.bone_groups.add()

        if not isinstance(bone_group_dict, dict):
            continue

        comment = bone_group_dict.get("comment")
        if isinstance(comment, str):
            bone_group.comment = comment

        stiffiness = bone_group_dict.get("stiffiness")
        if isinstance(stiffiness, (int, float)):
            bone_group.stiffiness = stiffiness

        gravity_power = bone_group_dict.get("gravityPower")
        if isinstance(gravity_power, (int, float)):
            bone_group.gravity_power = gravity_power

        gravity_dir = convert.vrm_json_vector3_to_tuple(
            bone_group_dict.get("gravityDir")
        )
        if gravity_dir is not None:
            # Axis confusing
            (x, y, z) = gravity_dir
            bone_group.gravity_dir = (x, z, y)

        drag_force = bone_group_dict.get("dragForce")
        if isinstance(drag_force, (int, float)):
            bone_group.drag_force = drag_force

        center = bone_group_dict.get("center")
        if isinstance(center, str):
            bone_group.center.set_bone_name(center)

        hit_radius = bone_group_dict.get("hitRadius")
        if isinstance(hit_radius, (int, float)):
            bone_group.hit_radius = hit_radius

        bones = bone_group_dict.get("bones")
        if isinstance(bones, list):
            for bone in bones:
                bone_prop = bone_group.bones.add()
                if not isinstance(bone, str):
                    continue
                bone_prop.set_bone_name(bone)

        collider_group_node_names = bone_group_dict.get("colliderGroups")
        if not isinstance(collider_group_node_names, list):
            continue

        for collider_group_node_name in collider_group_node_names:
            if not isinstance(collider_group_node_name, str):
                continue
            for collider_group in secondary_animation.collider_groups:
                if collider_group.node.bone_name != collider_group_node_name:
                    continue
                collider_group_name = bone_group.collider_groups.add()
                collider_group_name.value = collider_group.name
                break

    for bone_group in secondary_animation.bone_groups:
        bone_group.refresh(armature)


def migrate_legacy_custom_properties(
    context: Context, armature: Object, armature_data: Armature
) -> None:
    ext = get_armature_extension(armature_data)
    if tuple(ext.addon_version) >= (2, 0, 1):
        return

    migrate_vrm0_meta(context, ext.vrm0.meta, armature)
    migrate_vrm0_blend_shape_groups(
        context,
        ext.vrm0.blend_shape_master,
        read_textblock_json(context, armature, "blendshape_group"),
    )
    migrate_vrm0_first_person(
        context,
        ext.vrm0.first_person,
        read_textblock_json(context, armature, "firstPerson_params"),
    )
    migrate_vrm0_humanoid(
        ext.vrm0.humanoid, read_textblock_json(context, armature, "humanoid_params")
    )
    migrate_vrm0_secondary_animation(
        ext.vrm0.secondary_animation,
        read_textblock_json(context, armature, "spring_bone"),
        armature,
        armature_data,
    )

    assigned_bpy_bone_names: list[str] = []
    for human_bone_name in HumanBoneSpecifications.all_names:
        bpy_bone_name = armature_data.get(human_bone_name)
        if (
            not isinstance(bpy_bone_name, str)
            or not bpy_bone_name
            or bpy_bone_name in assigned_bpy_bone_names
        ):
            continue
        assigned_bpy_bone_names.append(bpy_bone_name)

        for human_bone in ext.vrm0.humanoid.human_bones:
            if human_bone.bone == human_bone_name:
                human_bone.node.set_bone_name(bpy_bone_name)
                break


def migrate_blender_object(armature_data: Armature) -> None:
    ext = get_armature_extension(armature_data)
    if tuple(ext.addon_version) >= (2, 3, 27):
        return

    for collider_group in ext.vrm0.secondary_animation.collider_groups:
        for collider in collider_group.colliders:
            bpy_object = collider.pop("blender_object", None)
            if isinstance(bpy_object, Object):
                collider.bpy_object = bpy_object


def migrate_link_to_bone_object(
    context: Context, armature: Object, armature_data: Armature
) -> None:
    ext = get_armature_extension(armature_data)
    if tuple(ext.addon_version) >= (2, 3, 27):
        return

    for bone_property_group in BonePropertyGroup.get_all_bone_property_groups(armature):
        bone_property_group.armature_data_name = armature_data.name

        link_to_bone = bone_property_group.get("link_to_bone")
        if not isinstance(link_to_bone, Object) or not link_to_bone.parent_bone:
            continue
        parent = link_to_bone.parent
        if not parent or not parent.name or parent.type != "ARMATURE":
            continue
        parent_data = parent.data
        if not isinstance(parent_data, Armature):
            continue
        bone = parent_data.bones.get(link_to_bone.parent_bone)
        if not bone:
            continue
        bone_extension = get_bone_extension(bone)
        if not bone_extension.uuid:
            bone_extension.uuid = uuid.uuid4().hex
        bone_property_group.bone_uuid = bone_extension.uuid

    for bone_property_group in BonePropertyGroup.get_all_bone_property_groups(armature):
        link_to_bone = bone_property_group.pop("link_to_bone", None)
        if not isinstance(link_to_bone, Object):
            continue
        if link_to_bone.parent_type != "OBJECT":
            link_to_bone.parent_type = "OBJECT"
        if link_to_bone.parent_bone:
            link_to_bone.parent_bone = ""
        if link_to_bone.parent is not None:
            link_to_bone.parent = None

    Vrm0HumanoidPropertyGroup.update_all_node_candidates(
        context,
        armature_data.name,
        force=True,
    )


def migrate_link_to_mesh_object(armature_data: Armature) -> None:
    ext = get_armature_extension(armature_data)
    if tuple(ext.addon_version) >= (2, 3, 23):
        return

    meshes = [
        mesh_annotation.mesh
        for mesh_annotation in ext.vrm0.first_person.mesh_annotations
    ] + [
        bind.mesh
        for blend_shape_group in ext.vrm0.blend_shape_master.blend_shape_groups
        for bind in blend_shape_group.binds
    ]

    for mesh in meshes:
        if not mesh:
            continue
        link_to_mesh = mesh.get("link_to_mesh")
        if (
            not isinstance(link_to_mesh, Object)
            or not link_to_mesh.parent
            or not link_to_mesh.parent.name
            or link_to_mesh.parent.type != "MESH"
        ):
            continue
        mesh.mesh_object_name = link_to_mesh.parent.name


def remove_link_to_mesh_object(armature_data: Armature) -> None:
    ext = get_armature_extension(armature_data)
    if tuple(ext.addon_version) >= (2, 3, 27):
        return

    meshes = [
        mesh_annotation.mesh
        for mesh_annotation in ext.vrm0.first_person.mesh_annotations
    ] + [
        bind.mesh
        for blend_shape_group in ext.vrm0.blend_shape_master.blend_shape_groups
        for bind in blend_shape_group.binds
    ]

    for mesh in meshes:
        if not mesh:
            continue
        link_to_mesh = mesh.pop("link_to_mesh", None)
        if not isinstance(link_to_mesh, Object):
            continue
        if link_to_mesh.parent_type != "OBJECT":
            link_to_mesh.parent_type = "OBJECT"
        if link_to_mesh.parent_bone:
            link_to_mesh.parent_bone = ""
        if link_to_mesh.parent is not None:
            link_to_mesh.parent = None


def fixup_gravity_dir(armature_data: Armature) -> None:
    ext = get_armature_extension(armature_data)
    if tuple(ext.addon_version) >= (2, 15, 4):
        return

    for bone_group in ext.vrm0.secondary_animation.bone_groups:
        gravity_dir = list(bone_group.gravity_dir)
        bone_group.gravity_dir = (gravity_dir[0] + 1, 0, 0)  # Make a change
        bone_group.gravity_dir = gravity_dir


def fixup_humanoid_feet_spacing(armature_data: Armature) -> None:
    ext = get_armature_extension(armature_data)
    if tuple(ext.addon_version) >= (2, 18, 2):
        return
    humanoid = ext.vrm0.humanoid
    feet_spacing = humanoid.get("feet_spacing")
    if isinstance(feet_spacing, (int, float)):
        humanoid.feet_spacing = float(feet_spacing)


def migrate_pose(context: Context, armature: Object, armature_data: Armature) -> None:
    ext = get_armature_extension(armature_data)
    if tuple(ext.addon_version) >= (2, 20, 34):
        return

    humanoid = ext.vrm0.humanoid
    if isinstance(humanoid.get("pose"), int):
        return

    if tuple(ext.addon_version) == ext.INITIAL_ADDON_VERSION:
        if "humanoid_params" in armature and "hips" in armature_data:
            humanoid.pose = humanoid.POSE_CURRENT_POSE.identifier
        return

    action = humanoid.pose_library
    if action and action.name in context.blend_data.actions:
        humanoid.pose = humanoid.POSE_CUSTOM_POSE.identifier
    elif armature_data.pose_position == "REST":
        humanoid.pose = humanoid.POSE_REST_POSITION_POSE.identifier
    else:
        humanoid.pose = humanoid.POSE_CURRENT_POSE.identifier


def migrate_auto_pose(_context: Context, armature_data: Armature) -> None:
    ext = get_armature_extension(armature_data)
    if tuple(ext.addon_version) == ext.INITIAL_ADDON_VERSION or tuple(
        ext.addon_version
    ) >= (2, 20, 81):
        return

    humanoid = ext.vrm0.humanoid
    if not isinstance(humanoid.get("pose"), int):
        humanoid.pose = humanoid.POSE_CURRENT_POSE.identifier


def is_unnecessary(vrm0: Vrm0PropertyGroup) -> bool:
    if vrm0.humanoid.initial_automatic_bone_assignment:
        return False
    if vrm0.first_person.first_person_bone.bone_name:
        return True
    return all(
        (human_bone.bone != "head" or not human_bone.node.bone_name)
        for human_bone in vrm0.humanoid.human_bones
    )


def migrate(context: Context, vrm0: Vrm0PropertyGroup, armature: Object) -> None:
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return

    migrate_blender_object(armature_data)
    migrate_link_to_bone_object(context, armature, armature_data)
    Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)

    for collider_group in vrm0.secondary_animation.collider_groups:
        collider_group.refresh(armature)
    for bone_group in vrm0.secondary_animation.bone_groups:
        bone_group.refresh(armature)

    if not vrm0.first_person.first_person_bone.bone_name:
        for human_bone in vrm0.humanoid.human_bones:
            if human_bone.bone == "head":
                vrm0.first_person.first_person_bone.set_bone_name(
                    human_bone.node.bone_name
                )
                break

    migrate_legacy_custom_properties(context, armature, armature_data)
    migrate_link_to_mesh_object(armature_data)
    remove_link_to_mesh_object(armature_data)
    fixup_gravity_dir(armature_data)
    fixup_humanoid_feet_spacing(armature_data)
    migrate_pose(context, armature, armature_data)
    migrate_auto_pose(context, armature_data)

    Vrm0HumanoidPropertyGroup.update_all_node_candidates(
        context,
        armature_data.name,
        force=True,
    )

    if vrm0.humanoid.initial_automatic_bone_assignment:
        vrm0.humanoid.initial_automatic_bone_assignment = False
        if all(not b.node.bone_name for b in vrm0.humanoid.human_bones):
            ops.vrm.assign_vrm0_humanoid_human_bones_automatically(
                armature_name=armature.name
            )
