import contextlib
import json
import uuid
from typing import Dict, List

import bpy

from ...common import convert
from ...common.deep import Json, make_json
from ...common.vrm0.human_bone import HumanBoneSpecifications
from ..property_group import BonePropertyGroup
from .property_group import (
    Vrm0BlendShapeGroupPropertyGroup,
    Vrm0FirstPersonPropertyGroup,
    Vrm0HumanoidPropertyGroup,
    Vrm0MeshAnnotationPropertyGroup,
    Vrm0MetaPropertyGroup,
    Vrm0PropertyGroup,
)


def read_textblock_json(armature: bpy.types.Object, armature_key: str) -> Json:
    text_key = armature.get(armature_key)
    if isinstance(text_key, bpy.types.Text):
        textblock = text_key
    elif not isinstance(text_key, str):
        return None
    else:
        textblock = bpy.data.texts.get(text_key)
        if not isinstance(textblock, bpy.types.Text):
            return None
    textblock_str = "".join([line.body for line in textblock.lines])
    with contextlib.suppress(json.JSONDecodeError):
        return make_json(json.loads(textblock_str))
    return None


def migrate_vrm0_meta(
    meta: bpy.types.PropertyGroup, armature: bpy.types.Object
) -> None:
    allowed_user_name = armature.get("allowedUserName")
    if (
        isinstance(allowed_user_name, str)
        and allowed_user_name in Vrm0MetaPropertyGroup.ALLOWED_USER_NAME_VALUES
    ):
        meta.allowed_user_name = allowed_user_name

    author = armature.get("author")
    if isinstance(author, str):
        meta.author = author

    commercial_ussage_name = armature.get("commercialUssageName")  # noqa: SC200
    if (
        isinstance(commercial_ussage_name, str)  # noqa: SC200
        and commercial_ussage_name  # noqa: SC200
        in Vrm0MetaPropertyGroup.COMMERCIAL_USSAGE_NAME_VALUES  # noqa: SC200
    ):
        meta.commercial_ussage_name = commercial_ussage_name  # noqa: SC200

    contact_information = armature.get("contactInformation")
    if isinstance(contact_information, str):
        meta.contact_information = contact_information

    license_name = armature.get("licenseName")
    if (
        isinstance(license_name, str)
        and license_name in Vrm0MetaPropertyGroup.LICENSE_NAME_VALUES
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

    sexual_ussage_name = armature.get("sexualUssageName")  # noqa: SC200
    if (
        isinstance(sexual_ussage_name, str)  # noqa: SC200
        and sexual_ussage_name  # noqa: SC200
        in Vrm0MetaPropertyGroup.SEXUAL_USSAGE_NAME_VALUES  # noqa: SC200
    ):
        meta.sexual_ussage_name = sexual_ussage_name  # noqa: SC200

    title = armature.get("title")
    if isinstance(title, str):
        meta.title = title

    version = armature.get("version")
    if isinstance(version, str):
        meta.version = version

    violent_ussage_name = armature.get("violentUssageName")  # noqa: SC200
    if (
        isinstance(violent_ussage_name, str)  # noqa: SC200
        and violent_ussage_name  # noqa: SC200
        in Vrm0MetaPropertyGroup.VIOLENT_USSAGE_NAME_VALUES  # noqa: SC200
    ):
        meta.violent_ussage_name = violent_ussage_name  # noqa: SC200

    texture = armature.get("texture")
    if texture is not None and texture in bpy.data.images:
        meta.texture = bpy.data.images[texture]


def migrate_vrm0_humanoid(
    humanoid: bpy.types.PropertyGroup, humanoid_dict: Json
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
    first_person: bpy.types.PropertyGroup,
    first_person_dict: Json,
) -> None:
    if not isinstance(first_person_dict, dict):
        return

    first_person_bone = first_person_dict.get("firstPersonBone")
    if isinstance(first_person_bone, str):
        first_person.first_person_bone.value = first_person_bone

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
                if mesh in bpy.data.meshes:
                    for obj in bpy.data.objects:
                        if obj.data == bpy.data.meshes[mesh]:
                            mesh_annotation.mesh.value = obj.name
                            break
                elif mesh in bpy.data.objects and bpy.data.objects[mesh].type == "MESH":
                    mesh_annotation.mesh.value = bpy.data.objects[mesh].name

            first_person_flag = mesh_annotation_dict.get("firstPersonFlag")
            if (
                isinstance(first_person_flag, str)
                and first_person_flag
                in Vrm0MeshAnnotationPropertyGroup.FIRST_PERSON_FLAG_VALUES
            ):
                mesh_annotation.first_person_flag = first_person_flag

    look_at_type_name = first_person_dict.get("lookAtTypeName")
    if (
        isinstance(look_at_type_name, str)
        and look_at_type_name in Vrm0FirstPersonPropertyGroup.LOOK_AT_TYPE_NAME_VALUES
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
    blend_shape_groups: bpy.types.PropertyGroup,
    blend_shape_group_dicts: Json,
) -> None:
    if not isinstance(blend_shape_group_dicts, list):
        return

    for blend_shape_group_dict in blend_shape_group_dicts:
        blend_shape_group = blend_shape_groups.add()

        if not isinstance(blend_shape_group_dict, dict):
            continue

        name = blend_shape_group_dict.get("name")
        if name is not None:
            blend_shape_group.name = name

        preset_name = blend_shape_group_dict.get("presetName")
        if (
            isinstance(preset_name, str)
            and preset_name in Vrm0BlendShapeGroupPropertyGroup.PRESET_NAME_VALUES
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
                    if mesh_name in bpy.data.meshes:
                        mesh = bpy.data.meshes[mesh_name]
                        for obj in bpy.data.objects:
                            if obj.data == mesh:
                                bind.mesh.value = obj.name
                                break
                    elif (
                        mesh_name in bpy.data.objects
                        and bpy.data.objects[mesh_name].type == "MESH"
                    ):
                        obj = bpy.data.objects[mesh_name]
                        bind.mesh.value = obj.name
                        mesh = obj.data
                    else:
                        mesh = None

                    if mesh:
                        index = bind_dict.get("index")
                        if (
                            isinstance(index, str)
                            and index in mesh.shape_keys.key_blocks
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
                    and material_name in bpy.data.materials
                ):
                    material_value.material = bpy.data.materials[material_name]

                property_name = material_value_dict.get("propertyName")
                if isinstance(property_name, str):
                    material_value.property_name = property_name

                target_value_vector = material_value_dict.get("targetValue")
                if isinstance(target_value_vector, list):
                    for v in target_value_vector:
                        if not isinstance(v, (int, float)):
                            v = 0
                        material_value.target_value.add().value = v

        is_binary = blend_shape_group_dict.get("isBinary")
        if isinstance(is_binary, bool):
            blend_shape_group.is_binary = is_binary


def migrate_vrm0_secondary_animation(
    secondary_animation: bpy.types.PropertyGroup,
    bone_group_dicts: Json,
    armature: bpy.types.Object,
) -> None:
    bone_name_to_collider_objects: Dict[str, List[bpy.types.Object]] = {}
    for collider_object in [
        child
        for child in armature.children
        if child.type == "EMPTY"
        and child.empty_display_type == "SPHERE"
        and child.parent_type == "BONE"
        and child.parent_bone in armature.data.bones
    ]:
        if collider_object.parent_bone not in bone_name_to_collider_objects:
            bone_name_to_collider_objects[collider_object.parent_bone] = []
        bone_name_to_collider_objects[collider_object.parent_bone].append(
            collider_object
        )

    for bone_name, collider_objects in bone_name_to_collider_objects.items():
        collider_group = secondary_animation.collider_groups.add()
        collider_group.uuid = uuid.uuid4().hex
        collider_group.node.value = bone_name
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

        stiffiness = bone_group_dict.get("stiffiness")  # noqa: SC200
        if isinstance(stiffiness, (int, float)):  # noqa: SC200
            bone_group.stiffiness = stiffiness  # noqa: SC200

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
            bone_group.center.value = center

        hit_radius = bone_group_dict.get("hitRadius")
        if isinstance(hit_radius, (int, float)):
            bone_group.hit_radius = hit_radius

        bones = bone_group_dict.get("bones")
        if isinstance(bones, list):
            for bone in bones:
                bone_prop = bone_group.bones.add()
                if not isinstance(bone, str):
                    continue
                bone_prop.value = bone

        collider_group_node_names = bone_group_dict.get("colliderGroups")
        if not isinstance(collider_group_node_names, list):
            continue

        for collider_group_node_name in collider_group_node_names:
            if not isinstance(collider_group_node_name, str):
                continue
            for collider_group in secondary_animation.collider_groups:
                if collider_group.node.value != collider_group_node_name:
                    continue
                collider_group_name = bone_group.collider_groups.add()
                collider_group_name.value = collider_group.name
                break

    for bone_group in secondary_animation.bone_groups:
        bone_group.refresh(armature)


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

    assigned_bpy_bone_names = []
    for human_bone_name in HumanBoneSpecifications.all_names:
        bpy_bone_name = armature.data.get(human_bone_name)
        if (
            not isinstance(bpy_bone_name, str)
            or not bpy_bone_name
            or bpy_bone_name in assigned_bpy_bone_names
        ):
            continue
        assigned_bpy_bone_names.append(bpy_bone_name)

        for human_bone in ext.vrm0.humanoid.human_bones:
            if human_bone.bone == human_bone_name:
                human_bone.node.value = bpy_bone_name
                break


def migrate_blender_object(armature: bpy.types.Object) -> None:
    ext = armature.data.vrm_addon_extension
    if tuple(ext.addon_version) >= (2, 3, 27):
        return

    for collider_group in ext.vrm0.secondary_animation.collider_groups:
        for collider in collider_group.colliders:
            bpy_object = collider.get("blender_object")
            if isinstance(bpy_object, bpy.types.Object):
                collider.bpy_object = bpy_object
            if "blender_object" in collider:
                del collider["blender_object"]


def migrate_link_to_bone_object(armature: bpy.types.Object) -> None:
    ext = armature.data.vrm_addon_extension
    if tuple(ext.addon_version) >= (2, 3, 27):
        return

    for bone_property_group in BonePropertyGroup.get_all_bone_property_groups(armature):
        bone_property_group.armature_data_name = armature.data.name

        link_to_bone = bone_property_group.get("link_to_bone")
        if (
            isinstance(link_to_bone, bpy.types.Object)
            and link_to_bone
            and link_to_bone.parent_bone
            and link_to_bone.parent
            and link_to_bone.parent.name
            and link_to_bone.parent.type == "ARMATURE"
            and link_to_bone.parent_bone in link_to_bone.parent.data.bones
        ):
            bone = link_to_bone.parent.data.bones[link_to_bone.parent_bone]
            if not bone.vrm_addon_extension.uuid:
                bone.vrm_addon_extension.uuid = uuid.uuid4().hex
            bone_property_group.bone_uuid = bone.vrm_addon_extension.uuid

    for bone_property_group in BonePropertyGroup.get_all_bone_property_groups(armature):
        link_to_bone = bone_property_group.get("link_to_bone")
        if "link_to_bone" in bone_property_group:
            del bone_property_group["link_to_bone"]
        if not isinstance(link_to_bone, bpy.types.Object):
            continue
        if link_to_bone.parent_type != "OBJECT":
            link_to_bone.parent_type = "OBJECT"
        if link_to_bone.parent_bone:
            link_to_bone.parent_bone = ""
        if link_to_bone.parent is not None:
            link_to_bone.parent = None

    armature.data.vrm_addon_extension.vrm0.humanoid.last_bone_names.clear()
    Vrm0HumanoidPropertyGroup.check_last_bone_names_and_update(
        armature.data.name,
        defer=False,
    )


def migrate_link_to_mesh_object(armature: bpy.types.Object) -> None:
    ext = armature.data.vrm_addon_extension
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
            not isinstance(link_to_mesh, bpy.types.Object)
            or not link_to_mesh.parent
            or not link_to_mesh.parent.name
            or link_to_mesh.parent.type != "MESH"
        ):
            continue
        mesh.value = link_to_mesh.parent.name


def remove_link_to_mesh_object(armature: bpy.types.Object) -> None:
    ext = armature.data.vrm_addon_extension
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
        link_to_mesh = mesh.get("link_to_mesh")
        if "link_to_mesh" in mesh:
            del mesh["link_to_mesh"]
        if not isinstance(link_to_mesh, bpy.types.Object):
            continue
        if link_to_mesh.parent_type != "OBJECT":
            link_to_mesh.parent_type = "OBJECT"
        if link_to_mesh.parent_bone:
            link_to_mesh.parent_bone = ""
        if link_to_mesh.parent is not None:
            link_to_mesh.parent = None


def fixup_gravity_dir(armature: bpy.types.Object) -> None:
    ext = armature.data.vrm_addon_extension
    if tuple(ext.addon_version) >= (2, 15, 4):
        return

    for bone_group in ext.vrm0.secondary_animation.bone_groups:
        gravity_dir = list(bone_group.gravity_dir)
        bone_group.gravity_dir[0] = gravity_dir[0] + 1  # Make a change
        bone_group.gravity_dir = gravity_dir


def is_unnecessary(vrm0: Vrm0PropertyGroup) -> bool:
    if vrm0.humanoid.initial_automatic_bone_assignment:
        return False
    return vrm0.first_person.first_person_bone.value or all(
        (human_bone.bone != "head" or not human_bone.node.value)
        for human_bone in vrm0.humanoid.human_bones
    )


def migrate(vrm0: Vrm0PropertyGroup, armature: bpy.types.Object) -> None:
    migrate_blender_object(armature)
    migrate_link_to_bone_object(armature)
    Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)

    for collider_group in vrm0.secondary_animation.collider_groups:
        collider_group.refresh(armature)
    for bone_group in vrm0.secondary_animation.bone_groups:
        bone_group.refresh(armature)

    if not vrm0.first_person.first_person_bone.value:
        for human_bone in vrm0.humanoid.human_bones:
            if human_bone.bone == "head":
                vrm0.first_person.first_person_bone.value = human_bone.node.value
                break

    migrate_legacy_custom_properties(armature)
    migrate_link_to_mesh_object(armature)
    remove_link_to_mesh_object(armature)
    fixup_gravity_dir(armature)

    vrm0.humanoid.last_bone_names.clear()
    Vrm0HumanoidPropertyGroup.check_last_bone_names_and_update(
        armature.data.name,
        defer=False,
    )

    if vrm0.humanoid.initial_automatic_bone_assignment:
        vrm0.humanoid.initial_automatic_bone_assignment = False
        if all(not b.node.value for b in vrm0.humanoid.human_bones):
            bpy.ops.vrm.assign_vrm0_humanoid_human_bones_automatically(
                armature_name=armature.name
            )
