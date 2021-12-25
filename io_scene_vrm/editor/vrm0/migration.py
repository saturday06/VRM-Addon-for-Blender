import collections
import contextlib
import json
import uuid
from typing import Any, Dict, List, Optional

import bpy

from ...common import convert, human_bone_constants
from .property_group import Vrm0PropertyGroup


def read_textblock_json(armature: bpy.types.Object, armature_key: str) -> Optional[Any]:
    if armature_key not in armature:
        return None
    with contextlib.suppress(TypeError):
        if armature[armature_key] not in bpy.data.texts:
            return None
    textblock = bpy.data.texts[armature[armature_key]]
    textblock_str = "".join([line.body for line in textblock.lines])
    with contextlib.suppress(json.JSONDecodeError):
        return json.loads(
            textblock_str,
            object_pairs_hook=collections.OrderedDict,
        )
    return None


def migrate_vrm0_meta(
    meta_props: bpy.types.PropertyGroup, armature: bpy.types.Object
) -> None:
    allowed_user_name = armature.get("allowedUserName")
    if isinstance(allowed_user_name, str):
        meta_props.allowed_user_name = allowed_user_name

    author = armature.get("author")
    if isinstance(author, str):
        meta_props.author = author

    commercial_ussage_name = armature.get("commercialUssageName")  # noqa: SC200
    if isinstance(commercial_ussage_name, str):  # noqa: SC200
        meta_props.commercial_ussage_name = commercial_ussage_name  # noqa: SC200

    contact_information = armature.get("contactInformation")
    if isinstance(contact_information, str):
        meta_props.contact_information = contact_information

    license_name = armature.get("licenseName")
    if isinstance(license_name, str):
        meta_props.license_name = license_name

    other_license_url = armature.get("otherLicenseUrl")
    if isinstance(other_license_url, str):
        meta_props.other_license_url = other_license_url

    other_permission_url = armature.get("otherPermissionUrl")
    if isinstance(other_permission_url, str):
        meta_props.other_permission_url = other_permission_url

    reference = armature.get("reference")
    if isinstance(reference, str):
        meta_props.reference = reference

    sexual_ussage_name = armature.get("sexualUssageName")  # noqa: SC200
    if isinstance(sexual_ussage_name, str):  # noqa: SC200
        meta_props.sexual_ussage_name = sexual_ussage_name  # noqa: SC200

    title = armature.get("title")
    if isinstance(title, str):
        meta_props.title = title

    version = armature.get("version")
    if isinstance(version, str):
        meta_props.version = version

    violent_ussage_name = armature.get("violentUssageName")  # noqa: SC200
    if isinstance(violent_ussage_name, str):  # noqa: SC200
        meta_props.violent_ussage_name = violent_ussage_name  # noqa: SC200

    texture = armature.get("texture")
    if texture is not None and texture in bpy.data.images:
        meta_props.texture = bpy.data.images[texture]


def migrate_vrm0_humanoid(
    humanoid_props: bpy.types.PropertyGroup, humanoid_dict: Any
) -> None:
    if not isinstance(humanoid_dict, dict):
        return

    arm_stretch = humanoid_dict.get("armStretch")
    if isinstance(arm_stretch, (int, float)):
        humanoid_props.arm_stretch = arm_stretch

    leg_stretch = humanoid_dict.get("legStretch")
    if isinstance(leg_stretch, (int, float)):
        humanoid_props.leg_stretch = leg_stretch

    upper_arm_twist = humanoid_dict.get("upperArmTwist")
    if isinstance(upper_arm_twist, (int, float)):
        humanoid_props.upper_arm_twist = upper_arm_twist

    lower_arm_twist = humanoid_dict.get("lowerArmTwist")
    if isinstance(lower_arm_twist, (int, float)):
        humanoid_props.lower_arm_twist = lower_arm_twist

    upper_leg_twist = humanoid_dict.get("upperLegTwist")
    if isinstance(upper_leg_twist, (int, float)):
        humanoid_props.upper_leg_twist = upper_leg_twist

    lower_leg_twist = humanoid_dict.get("lowerLegTwist")
    if isinstance(lower_leg_twist, (int, float)):
        humanoid_props.lower_leg_twist = lower_leg_twist

    feet_spacing = humanoid_dict.get("feetSpacing")
    if isinstance(feet_spacing, (int, float)):
        humanoid_props.feet_spacing = feet_spacing

    has_translation_dof = humanoid_dict.get("hasTranslationDoF")
    if isinstance(has_translation_dof, bool):
        humanoid_props.has_translation_dof = has_translation_dof


def migrate_vrm0_first_person(
    first_person_props: bpy.types.PropertyGroup,
    first_person_dict: Any,
) -> None:
    if not isinstance(first_person_dict, dict):
        return

    first_person_bone = first_person_dict.get("firstPersonBone")
    if isinstance(first_person_bone, str):
        first_person_props.first_person_bone.value = first_person_bone

    first_person_bone_offset = convert.vrm_json_vector3_to_tuple(
        first_person_dict.get("firstPersonBoneOffset")
    )
    if first_person_bone_offset is not None:
        # Axis confusing
        (x, y, z) = first_person_bone_offset
        first_person_props.first_person_bone_offset = (x, z, y)

    mesh_annotations = first_person_dict.get("meshAnnotations")
    if isinstance(mesh_annotations, collections.Iterable):
        for mesh_annotation_dict in mesh_annotations:
            mesh_annotation_props = first_person_props.mesh_annotations.add()

            if not isinstance(mesh_annotation_dict, dict):
                continue

            mesh = mesh_annotation_dict.get("mesh")
            if isinstance(mesh, str) and mesh in bpy.data.meshes:
                mesh_annotation_props.mesh.value = bpy.data.meshes[mesh].name

            first_person_flag = mesh_annotation_dict.get("firstPersonFlag")
            if isinstance(first_person_flag, str):
                mesh_annotation_props.first_person_flag = first_person_flag

    look_at_type_name = first_person_dict.get("lookAtTypeName")
    if look_at_type_name in ["Bone", "BlendShape"]:
        first_person_props.look_at_type_name = look_at_type_name

    for (look_at_props, look_at_dict) in [
        (
            first_person_props.look_at_horizontal_inner,
            first_person_dict.get("lookAtHorizontalInner"),
        ),
        (
            first_person_props.look_at_horizontal_outer,
            first_person_dict.get("lookAtHorizontalOuter"),
        ),
        (
            first_person_props.look_at_vertical_down,
            first_person_dict.get("lookAtVerticalDown"),
        ),
        (
            first_person_props.look_at_vertical_up,
            first_person_dict.get("lookAtVerticalUp"),
        ),
    ]:
        if not isinstance(look_at_dict, dict):
            continue

        curve = convert.vrm_json_curve_to_list(look_at_dict.get("curve"))
        if curve is not None:
            look_at_props.curve = curve

        x_range = look_at_dict.get("xRange")
        if isinstance(x_range, (float, int)):
            look_at_props.x_range = x_range

        y_range = look_at_dict.get("yRange")
        if isinstance(y_range, (float, int)):
            look_at_props.y_range = y_range


def migrate_vrm0_blend_shape_groups(
    blend_shape_groups_props: bpy.types.PropertyGroup,
    blend_shape_groups: Any,
) -> None:
    if not isinstance(blend_shape_groups, collections.Iterable):
        return

    for blend_shape_group_dict in blend_shape_groups:
        blend_shape_group_props = blend_shape_groups_props.add()

        if not isinstance(blend_shape_group_dict, dict):
            continue

        name = blend_shape_group_dict.get("name")
        if name is not None:
            blend_shape_group_props.name = name

        preset_name = blend_shape_group_dict.get("presetName")
        if preset_name is not None:
            blend_shape_group_props.preset_name = preset_name

        binds = blend_shape_group_dict.get("binds")
        if isinstance(binds, collections.Iterable):
            for bind_dict in binds:
                bind_props = blend_shape_group_props.binds.add()

                if not isinstance(bind_dict, dict):
                    continue

                mesh = bind_dict.get("mesh")
                if isinstance(mesh, str) and mesh in bpy.data.meshes:
                    mesh = bpy.data.meshes[mesh]
                    bind_props.mesh.value = mesh.name
                    index = bind_dict.get("index")
                    if isinstance(index, str) and index in mesh.shape_keys.key_blocks:
                        bind_props.index = index

                weight = bind_dict.get("weight")
                if isinstance(weight, (int, float)):
                    bind_props.weight = weight

        material_values = blend_shape_group_dict.get("materialValues")
        if isinstance(material_values, collections.Iterable):
            for material_value_dict in material_values:
                material_value_props = blend_shape_group_props.material_values.add()

                if not isinstance(material_value_dict, dict):
                    continue

                material_name = material_value_dict.get("materialName")
                if (
                    isinstance(material_name, str)
                    and material_name in bpy.data.materials
                ):
                    material_value_props.material = bpy.data.materials[material_name]

                property_name = material_value_dict.get("propertyName")
                if isinstance(property_name, str):
                    material_value_props.property_name = property_name

                target_value = material_value_dict.get("targetValue")
                if isinstance(target_value, collections.Iterable):
                    for target_value_element in target_value:
                        if not isinstance(target_value_element, (int, float)):
                            target_value_element = 0
                        target_value_element_props = (
                            material_value_props.target_value.add()
                        )
                        target_value_element_props.value = target_value_element

        is_binary = blend_shape_group_dict.get("isBinary")
        if isinstance(is_binary, bool):
            blend_shape_group_props.is_binary = is_binary


def migrate_vrm0_secondary_animation(
    secondary_animation_props: bpy.types.PropertyGroup,
    bone_groups: Any,
    armature: bpy.types.Object,
) -> None:
    bone_name_to_collider_objects: Dict[str, List[bpy.types.Object]] = {}
    for collider_object in [
        child
        for child in armature.children
        if child.type == "EMPTY"
        and child.empty_display_type == "SPHERE"
        and child.parent_bone in armature.data.bones
    ]:
        if collider_object.parent_bone not in bone_name_to_collider_objects:
            bone_name_to_collider_objects[collider_object.parent_bone] = []
        bone_name_to_collider_objects[collider_object.parent_bone].append(
            collider_object
        )

    for bone_name, collider_objects in bone_name_to_collider_objects.items():
        collider_group_props = secondary_animation_props.collider_groups.add()
        collider_group_props.uuid = uuid.uuid4().hex
        collider_group_props.node.value = bone_name
        for collider_object in collider_objects:
            collider_prop = collider_group_props.colliders.add()
            collider_prop.blender_object = collider_object

    for collider_group_props in secondary_animation_props.collider_groups:
        collider_group_props.refresh(armature)

    if not isinstance(bone_groups, collections.Iterable):
        bone_groups = []

    for bone_group_dict in bone_groups:
        bone_group_props = secondary_animation_props.bone_groups.add()

        if not isinstance(bone_group_dict, dict):
            continue

        comment = bone_group_dict.get("comment")
        if isinstance(comment, str):
            bone_group_props.comment = comment

        stiffiness = bone_group_dict.get("stiffiness")  # noqa: SC200
        if isinstance(stiffiness, (int, float)):  # noqa: SC200
            bone_group_props.stiffiness = stiffiness  # noqa: SC200

        gravity_power = bone_group_dict.get("gravityPower")
        if isinstance(gravity_power, (int, float)):
            bone_group_props.gravity_power = gravity_power

        gravity_dir = convert.vrm_json_vector3_to_tuple(
            bone_group_dict.get("gravityDir")
        )
        if gravity_dir is not None:
            # Axis confusing
            (x, y, z) = gravity_dir
            bone_group_props.gravity_dir = (x, z, y)

        drag_force = bone_group_dict.get("dragForce")
        if isinstance(drag_force, (int, float)):
            bone_group_props.drag_force = drag_force

        center = bone_group_dict.get("center")
        if isinstance(center, str):
            bone_group_props.center.value = center

        hit_radius = bone_group_dict.get("hitRadius")
        if isinstance(hit_radius, (int, float)):
            bone_group_props.hit_radius = hit_radius

        bones = bone_group_dict.get("bones")
        if isinstance(bones, collections.Iterable):
            for bone in bones:
                bone_prop = bone_group_props.bones.add()
                if not isinstance(bone, str):
                    continue
                bone_prop.value = bone

        collider_group_node_names = bone_group_dict.get("colliderGroups")
        if not isinstance(collider_group_node_names, collections.Iterable):
            continue

        for collider_group_node_name in collider_group_node_names:
            if not isinstance(collider_group_node_name, str):
                continue
            for collider_group_props in secondary_animation_props.collider_groups:
                if collider_group_props.node.value != collider_group_node_name:
                    continue
                collider_group_name_props = bone_group_props.collider_groups.add()
                collider_group_name_props.value = collider_group_props.name
                break

    for bone_group_props in secondary_animation_props.bone_groups:
        bone_group_props.refresh(armature)


def migrate_legacy_custom_properties(armature: bpy.types.Object) -> None:
    ext = armature.data.vrm_addon_extension
    if tuple(ext.addon_version) >= (2, 0, 1):
        return

    migrate_vrm0_meta(ext.vrm0.meta, armature)
    migrate_vrm0_blend_shape_groups(
        ext.vrm0.blend_shape_master.blend_shape_groups,
        read_textblock_json(armature, "blendshape_group"),
    )
    migrate_vrm0_first_person(
        ext.vrm0.first_person, read_textblock_json(armature, "firstPerson_params")
    )
    migrate_vrm0_humanoid(
        ext.vrm0.humanoid, read_textblock_json(armature, "humanoid_params")
    )
    migrate_vrm0_secondary_animation(
        ext.vrm0.secondary_animation,
        read_textblock_json(armature, "spring_bone"),
        armature,
    )

    for human_bone_name in (
        human_bone_constants.HumanBone.requires + human_bone_constants.HumanBone.defines
    ):
        blender_bone_name = armature.data.get(human_bone_name)
        if not isinstance(blender_bone_name, str):
            continue

        for human_bone_props in ext.vrm0.humanoid.human_bones:
            if human_bone_props.bone == human_bone_name:
                human_bone_props.node.value = blender_bone_name
                break


def is_unnecessary(vrm0_props: Vrm0PropertyGroup) -> bool:
    return vrm0_props.first_person.first_person_bone.value or all(
        (human_bone.bone != "head" or not human_bone.node.value)
        for human_bone in vrm0_props.humanoid.human_bones
    )


def migrate(vrm0_props: Vrm0PropertyGroup, armature: bpy.types.Object) -> None:
    for collider_group_props in vrm0_props.secondary_animation.collider_groups:
        collider_group_props.refresh(armature)
    for bone_group_props in vrm0_props.secondary_animation.bone_groups:
        bone_group_props.refresh(armature)

    for human_bone_name in (
        human_bone_constants.HumanBone.requires + human_bone_constants.HumanBone.defines
    ):
        if any(
            human_bone.bone == human_bone_name
            for human_bone in vrm0_props.humanoid.human_bones
        ):
            continue
        human_bone_props = vrm0_props.humanoid.human_bones.add()
        human_bone_props.bone = human_bone_name

    if not vrm0_props.first_person.first_person_bone.value:
        for human_bone in vrm0_props.humanoid.human_bones:
            if human_bone.bone == "head":
                vrm0_props.first_person.first_person_bone.value = human_bone.node.value
                break

    migrate_legacy_custom_properties(armature)
