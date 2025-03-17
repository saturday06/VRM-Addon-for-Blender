# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import re
import time
from collections import defaultdict
from collections.abc import Set as AbstractSet
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import bpy
from bpy.app.translations import pgettext
from bpy.props import BoolProperty, CollectionProperty, StringProperty
from bpy.types import (
    Armature,
    Context,
    Event,
    Object,
    Operator,
    Panel,
    SpaceFileBrowser,
    UILayout,
)
from bpy_extras.io_utils import ExportHelper

from ..common import ops, version
from ..common.logger import get_logger
from ..common.preferences import (
    ExportPreferencesProtocol,
    copy_export_preferences,
    draw_export_preferences_layout,
    get_preferences,
)
from ..common.workspace import save_workspace
from ..editor import migration, search, validation
from ..editor.extension import get_armature_extension
from ..editor.ops import VRM_OT_open_url_in_web_browser, layout_operator
from ..editor.property_group import CollectionPropertyProtocol, StringPropertyGroup
from ..editor.validation import VrmValidationError
from ..editor.vrm0.panel import (
    draw_vrm0_humanoid_operators_layout,
    draw_vrm0_humanoid_optional_bones_layout,
    draw_vrm0_humanoid_required_bones_layout,
)
from ..editor.vrm0.property_group import Vrm0HumanoidPropertyGroup
from ..editor.vrm1.ops import VRM_OT_assign_vrm1_humanoid_human_bones_automatically
from ..editor.vrm1.panel import (
    draw_vrm1_humanoid_optional_bones_layout,
    draw_vrm1_humanoid_required_bones_layout,
)
from ..editor.vrm1.property_group import Vrm1HumanBonesPropertyGroup
from .abstract_base_vrm_exporter import AbstractBaseVrmExporter
from .vrm0_exporter import Vrm0Exporter
from .vrm1_exporter import Vrm1Exporter
from .vrm_animation_exporter import VrmAnimationExporter

logger = get_logger(__name__)


# ------------------------------------------------------------------------------
# Duplicate bones, update parenting, and assign them to a different layer or collection
# ------------------------------------------------------------------------------
def duplicate_bones():
    start_time = time.time()
    logger.info("Starting bone duplication process...")

    arm_obj = bpy.context.active_object
    if not arm_obj or arm_obj.type != "ARMATURE":
        logger.error("Active object is not an armature.")
        return None, None, None

    # Store the current mode so we can restore it later.
    original_mode = arm_obj.mode

    # Enter Edit mode to work on the skeleton.
    bpy.ops.object.mode_set(mode="EDIT")
    arm_data = arm_obj.data
    edit_bones = arm_data.edit_bones

    # Identify the hips bone from VRM1 human bones if available
    hips_bone_name = None
    try:
        vrm1 = get_armature_extension(arm_data).vrm1
        human_bones = vrm1.humanoid.human_bones
        hips_bone_name = human_bones.hips.node.bone_name
        logger.info(f"VRM hips bone identified: {hips_bone_name}")
    except (AttributeError, ValueError) as e:
        logger.info(f"Could not identify VRM hips bone: {e!s}")

    # Create a mapping from original bone names to duplicate bone names.
    bone_mapping = {}

    # List to track duplicated bones
    duplicated_bones = []

    # Copy the list of original bones (to avoid modifying the collection while iterating)
    original_edit_bones = list(edit_bones)

    # Track root bones (bones without parents)
    root_bones = [bone.name for bone in original_edit_bones if not bone.parent]
    logger.info(f"Root bones identified: {root_bones}")

    # Track end-chain bones and IK bones to ensure they get duplicated
    end_chain_bones = [
        bone.name for bone in original_edit_bones if len(bone.children) == 0
    ]
    ik_bones = [bone.name for bone in original_edit_bones if "IK" in bone.name]
    logger.info(f"End-chain bones identified: {end_chain_bones}")
    logger.info(f"IK bones identified: {ik_bones}")

    # First pass: Create all duplicate bones with unique names
    for bone in original_edit_bones:
        # Generate a unique name for the duplicate bone using the vrmaProxyBone suffix
        base_name = bone.name + ".vrmaProxyBone"
        new_name = base_name

        # Make sure the name is unique by adding a number if needed
        counter = 1
        while new_name in edit_bones:
            new_name = f"{base_name}.{counter:03d}"
            counter += 1

        # Create the duplicate bone
        dup_bone = edit_bones.new(new_name)

        # Store Mirror Bones Toggle Status:
        use_mirror_x = bpy.context.object.data.use_mirror_x

        # Set Status to false:
        bpy.context.object.data.use_mirror_x = False

        # Copy transform properties
        dup_bone.head = bone.head.copy()
        dup_bone.tail = bone.tail.copy()
        dup_bone.roll = bone.roll

        # Set Mirror Bones Status to original state:
        bpy.context.object.data.use_mirror_x = use_mirror_x

        # CRITICAL FIX: We must set use_deform=True for end-chain bones to ensure they're exported
        # This is especially important for bones without children
        if not bone.children:
            dup_bone.use_deform = True
            bone.use_deform = True  # Also ensure original bone has use_deform enabled
            logger.info(
                f"Ensuring deform is enabled for both original and duplicate of end-chain bone: {bone.name}"
            )

        # If this is the hips bone, we need to ensure it has the correct orientation
        # by matching the roll and orientation exactly from the original bone
        if bone.name == hips_bone_name:
            logger.info(f"Ensuring correct orientation for hips duplicate: {new_name}")
            # Make sure the duplicate matches the original exactly
            dup_bone.matrix = bone.matrix.copy()

        # The duplicate bone should not be connected to its parent.
        dup_bone.use_connect = False

        # Store the mapping (original name -> duplicate name)
        bone_mapping[bone.name] = new_name

        # Track the duplicated bone
        duplicated_bones.append(new_name)

    # Check if all bones were duplicated, especially our problematic ones
    problem_bones = [
        "LegIK2.L",
        "LegIK2.R",
        "ArmIK2.L",
        "ArmIK2.R",
        "Wing.R.003",
        "Wing.L.003",
    ]
    missed_bones = [
        bone.name for bone in original_edit_bones if bone.name not in bone_mapping
    ]
    if missed_bones:
        logger.error(f"Some bones were not duplicated: {missed_bones}")

    for bone_name in problem_bones:
        if bone_name in bone_mapping:
            logger.info(
                f"Successfully duplicated problem bone: {bone_name} → {bone_mapping[bone_name]}"
            )
        elif bone_name in [b.name for b in original_edit_bones]:
            logger.error(f"Failed to duplicate problem bone: {bone_name}")

    # Second pass: Recreate the parent/child relationships among the duplicates
    for bone in original_edit_bones:
        dup_bone_name = bone_mapping.get(bone.name)
        if dup_bone_name:
            dup_bone = edit_bones.get(dup_bone_name)
            if dup_bone:
                # Special case for hips: always parent to original hips
                if bone.name == hips_bone_name:
                    logger.info(
                        f"Special handling for hips bone: {bone.name} -> {dup_bone.name}"
                    )
                    dup_bone.parent = edit_bones.get(bone.name)
                    dup_bone.use_connect = False
                elif bone.name in root_bones:
                    # For root bones, parent the duplicate to the original
                    logger.info(
                        f"Special handling for root bone: {bone.name} -> {dup_bone.name}"
                    )
                    dup_bone.parent = edit_bones.get(bone.name)
                    dup_bone.use_connect = False
                elif bone.parent and bone.parent.name in bone_mapping:
                    parent_dup_name = bone_mapping[bone.parent.name]
                    parent_dup_bone = edit_bones.get(parent_dup_name)
                    if parent_dup_bone:
                        dup_bone.parent = parent_dup_bone
                        dup_bone.use_connect = False
                # If the bone has a parent but the parent's duplicate wasn't created,
                # parent to the original parent
                elif bone.parent:
                    logger.info(
                        f"Parenting {dup_bone.name} to original parent {bone.parent.name}"
                    )
                    dup_bone.parent = edit_bones.get(bone.parent.name)
                    dup_bone.use_connect = False

    # ------------------------------------------------------------------------------
    # Move duplicate bones out of the default bone collection / layer.
    # For Blender versions before 4.0 use bone layers;
    # for Blender 4.0 or higher, assign to a new bone collection.
    # ------------------------------------------------------------------------------
    use_collections = bpy.app.version >= (4, 0, 0)
    if not use_collections:
        # For older versions, use bone layers - assign all at once
        for bone_name in duplicated_bones:
            if bone_name in edit_bones:
                layers = [False] * 32
                layers[1] = True  # Choose a non-default layer
                edit_bones[bone_name].layers = layers
    else:
        # Blender 4.0+ – use bone collections
        bpy.ops.object.mode_set(mode="OBJECT")
        arm_data = arm_obj.data
        group = arm_data.collections.get("vrma translate scale export")
        if group is None:
            group = arm_data.collections.new("vrma translate scale export")

        # Make sure we have all the bones with the vrmaProxyBone suffix
        all_duplicate_bones = [
            b.name for b in arm_data.bones if ".vrmaProxyBone" in b.name
        ]
        logger.info(f"Found {len(all_duplicate_bones)} duplicate bones in OBJECT mode")

        # Assign all duplicate bones to the collection in a batch
        for bone_name in all_duplicate_bones:
            bone = arm_data.bones.get(bone_name)
            if bone:
                group.assign(bone)

        bpy.ops.object.mode_set(mode="EDIT")

    # Restore the original mode
    bpy.ops.object.mode_set(mode=original_mode)

    elapsed = time.time() - start_time
    logger.info(f"Bone duplication completed in {elapsed:.2f} seconds")
    logger.info(f"Created {len(duplicated_bones)} duplicate bones")

    return bone_mapping, root_bones, duplicated_bones


# ------------------------------------------------------------------------------
# Rename vertex groups: For every vertex group with the original bone name,
# change its name to the duplicate bone's name.
# ------------------------------------------------------------------------------
def rename_vertex_groups(bone_mapping) -> None:
    start_time = time.time()
    logger.info("Starting vertex group renaming...")

    # Process all mesh objects at once
    mesh_objects = [
        obj for obj in bpy.data.objects if obj.type == "MESH" and obj.vertex_groups
    ]

    # Process each mesh efficiently
    for mesh_obj in mesh_objects:
        # Get list of groups to rename
        rename_data = [
            (i, vg.name, bone_mapping.get(vg.name))
            for i, vg in enumerate(mesh_obj.vertex_groups)
            if vg.name in bone_mapping
        ]

        # Apply renames (in reverse order to avoid index shifts)
        for i, old_name, new_name in sorted(rename_data, reverse=True):
            logger.info(
                f"Renaming vertex group {old_name} to {new_name} in object {mesh_obj.name}"
            )
            mesh_obj.vertex_groups[i].name = new_name

    elapsed = time.time() - start_time
    logger.info(f"Vertex group renaming completed in {elapsed:.2f} seconds")


# ------------------------------------------------------------------------------
# Add a copy rotation constraint to each duplicate (pose) bone targeting its original.
# ------------------------------------------------------------------------------
def add_copy_rotation_constraints(bone_mapping, root_bones) -> None:
    start_time = time.time()
    logger.info("Adding copy rotation constraints...")

    arm_obj = bpy.context.active_object
    if not arm_obj or arm_obj.type != "ARMATURE":
        logger.error("Active object is not an armature.")
        return

    # Identify the hips bone from VRM1 human bones if available
    hips_bone_name = None
    try:
        arm_data = arm_obj.data
        vrm1 = get_armature_extension(arm_data).vrm1
        human_bones = vrm1.humanoid.human_bones
        hips_bone_name = human_bones.hips.node.bone_name
        logger.info(f"VRM hips bone identified for constraints: {hips_bone_name}")

        # Find the duplicate hips bone name
        if hips_bone_name in bone_mapping:
            dup_hips_bone_name = bone_mapping[hips_bone_name]
            logger.info(
                f"Duplicate hips bone: {dup_hips_bone_name} (will not receive constraint)"
            )
        else:
            logger.warning(f"Hips bone {hips_bone_name} not found in bone mapping")
    except (AttributeError, ValueError) as e:
        logger.info(f"Could not identify VRM hips bone: {e!s}")

    # Create reverse mapping for constraint setup
    reverse_mapping = {dup: orig for orig, dup in bone_mapping.items()}

    # Switch to POSE mode to work on pose bones (just once)
    bpy.ops.object.mode_set(mode="POSE")

    # Process all pose bones that need constraints in a batch
    for pbone in arm_obj.pose.bones:
        if pbone.name in reverse_mapping:
            orig_bone_name = reverse_mapping[pbone.name]

            # Skip root bones and hips bone - they should not get rotation constraints
            if orig_bone_name in root_bones:
                logger.info(
                    f"Skipping rotation constraint for root bone duplicate: {pbone.name}"
                )
                continue

            # Skip the duplicate of the hips bone
            if orig_bone_name == hips_bone_name:
                logger.info(
                    f"Skipping rotation constraint for hips bone duplicate: {pbone.name}"
                )
                continue

            # Check if the original bone exists
            if orig_bone_name in arm_obj.pose.bones:
                logger.info(
                    f"Adding rotation constraint to {pbone.name} targeting {orig_bone_name}"
                )
                constr = pbone.constraints.new("COPY_ROTATION")
                constr.name = f"CopyRot_{orig_bone_name}"
                constr.target = arm_obj
                constr.subtarget = orig_bone_name
                constr.use_x = True
                constr.use_y = True
                constr.use_z = True
                constr.mix_mode = "ADD"
                constr.target_space = "LOCAL"
                constr.owner_space = "LOCAL"

    # Return to OBJECT mode when done.
    bpy.ops.object.mode_set(mode="OBJECT")

    elapsed = time.time() - start_time
    logger.info(f"Copy rotation constraints added in {elapsed:.2f} seconds")


# ------------------------------------------------------------------------------
# Transfer fcurves for scale and translation from original bones to duplicates.
# ------------------------------------------------------------------------------
def transfer_fcurves(bone_mapping) -> None:
    start_time = time.time()
    logger.info("Starting FCurve transfer...")

    arm_obj = bpy.context.active_object
    anim_data = arm_obj.animation_data
    if not anim_data or not anim_data.action:
        logger.error("No active action found on the armature.")
        return

    # Identify the hips bone from VRM1 human bones if available
    hips_bone_name = None
    try:
        arm_data = arm_obj.data
        vrm1 = get_armature_extension(arm_data).vrm1
        human_bones = vrm1.humanoid.human_bones
        hips_bone_name = human_bones.hips.node.bone_name
        logger.info(f"VRM hips bone identified for FCurve transfer: {hips_bone_name}")
    except (AttributeError, ValueError) as e:
        logger.info(f"Could not identify VRM hips bone: {e!s}")

    action = anim_data.action

    # Compile regex once
    pattern = re.compile(r'pose\.bones\["(.+)"\]\.(location|scale)')

    # Pre-scan to find all fcurves to process and existing duplicate fcurves to remove
    fcurves_to_process = []
    fcurves_to_remove = []

    # Build reverse mapping for faster lookup
    reverse_mapping = {dup: orig for orig, dup in bone_mapping.items()}

    # Group fcurves by bone and property for batch processing
    fcurve_groups = {}

    for i, fc in enumerate(action.fcurves):
        match = pattern.match(fc.data_path)
        if match:
            bone_name, prop = match.groups()

            # Special handling for hips bone:
            # - Transfer ONLY scale tracks for hips bone, no location tracks
            # - Keep all original tracks on the original hips
            if bone_name == hips_bone_name:
                if prop == "scale" and bone_name in bone_mapping:
                    key = (bone_name, prop)
                    if key not in fcurve_groups:
                        fcurve_groups[key] = []
                    fcurve_groups[key].append(fc)
                    fcurves_to_remove.append(i)
                # Skip location tracks for hips duplicate
                continue
            # Normal processing for non-hips bones
            elif bone_name in bone_mapping:
                key = (bone_name, prop)
                if key not in fcurve_groups:
                    fcurve_groups[key] = []
                fcurve_groups[key].append(fc)
                fcurves_to_remove.append(i)

            # Check for duplicate bone fcurves that may already exist
            elif bone_name in reverse_mapping:
                # For hips duplicate, only remove scale fcurves if they exist
                # (should not have location fcurves anyway)
                if reverse_mapping[bone_name] == hips_bone_name and prop != "scale":
                    continue
                fcurves_to_remove.append(i)

    # Create new fcurves for duplicate bones (bulk creation for each bone+property)
    for (bone_name, prop), fcurves in fcurve_groups.items():
        dup_bone_name = bone_mapping[bone_name]
        logger.info(f"Transferring {prop} fcurves from {bone_name} to {dup_bone_name}")

        for fc in fcurves:
            new_data_path = f'pose.bones["{dup_bone_name}"].{prop}'

            # Create new fcurve
            new_fc = action.fcurves.new(data_path=new_data_path, index=fc.array_index)

            # Set up keyframes efficiently (only if there are keyframes)
            kp_count = len(fc.keyframe_points)
            if kp_count > 0:
                # Add all points at once
                new_fc.keyframe_points.add(kp_count)

                # Bulk copy keyframe data
                for i, kp in enumerate(fc.keyframe_points):
                    new_kp = new_fc.keyframe_points[i]
                    new_kp.co = kp.co
                    new_kp.handle_left = kp.handle_left
                    new_kp.handle_right = kp.handle_right
                    new_kp.interpolation = kp.interpolation
                    new_kp.easing = kp.easing

            # Copy modifiers efficiently
            for mod in fc.modifiers:
                new_mod = new_fc.modifiers.new(type=mod.type)
                # Copy essential properties based on modifier type
                if hasattr(mod, "points") and hasattr(new_mod, "points"):
                    for i, point in enumerate(mod.points):
                        if i < len(new_mod.points):
                            new_mod.points[i].co = point.co
                            new_mod.points[i].handle_type = point.handle_type

    # Remove original fcurves after transfer (except hips location)
    # Remove in reverse order to avoid index shifting issues
    for i in sorted(fcurves_to_remove, reverse=True):
        try:
            action.fcurves.remove(action.fcurves[i])
        except Exception as e:
            logger.error(f"Failed to remove fcurve at index {i}: {e!s}")

    bpy.ops.object.mode_set(mode="OBJECT")

    elapsed = time.time() - start_time
    logger.info(f"FCurve transfer completed in {elapsed:.2f} seconds")


# ------------------------------------------------------------------------------
# Main function that calls all steps.
# ------------------------------------------------------------------------------
def run_bone_duplication(for_vrma=False):
    start_time = time.time()

    arm_obj = bpy.context.active_object
    if not arm_obj or arm_obj.type != "ARMATURE":
        logger.error("Active object is not an armature.")
        return None, None

    logger.info("Starting bone duplication process...")

    # Before duplication, identify end-chain bones
    end_chain_bones = set()
    for bone in arm_obj.data.edit_bones:
        if not bone.children:
            end_chain_bones.add(bone.name)
            logger.info(f"Identified end-chain bone to preserve: {bone.name}")

    bone_mapping, root_bones, duplicated_bones = duplicate_bones()
    if not bone_mapping:
        logger.error("Bone duplication failed")
        return None, None

    # Rename vertex groups first to ensure they target the correct bones
    rename_vertex_groups(bone_mapping)

    # Add constraints to duplicates (but not to hips or root bones)
    add_copy_rotation_constraints(bone_mapping, root_bones)

    # Only transfer fcurves if we're exporting VRMA
    if for_vrma:
        transfer_fcurves(bone_mapping)

    elapsed = time.time() - start_time
    logger.info(f"Bone duplication process completed in {elapsed:.2f} seconds")

    # Return end-chain bones as well
    return bone_mapping, duplicated_bones, end_chain_bones


# ------------------------------------------------------------------------------
# Revert all changes made by the bone duplication process
# ------------------------------------------------------------------------------
def revert_bone_duplication(bone_mapping, duplicated_bones, for_vrma=False) -> None:
    start_time = time.time()

    arm_obj = bpy.context.active_object
    if not arm_obj or arm_obj.type != "ARMATURE":
        logger.error("Active object is not an armature.")
        return

    # Record the current mode to restore it later
    original_mode = arm_obj.mode

    logger.info(
        f"Starting reversal of bone duplication with {len(duplicated_bones) if duplicated_bones else 0} bones to clean up"
    )

    # Identify the hips bone from VRM1 human bones if available
    hips_bone_name = None
    hips_dup_bone_name = None
    try:
        arm_data = arm_obj.data
        vrm1 = get_armature_extension(arm_data).vrm1
        human_bones = vrm1.humanoid.human_bones
        hips_bone_name = human_bones.hips.node.bone_name

        # Find the duplicate hips bone name
        if hips_bone_name in bone_mapping:
            hips_dup_bone_name = bone_mapping[hips_bone_name]

        logger.info(
            f"VRM hips bone identified for cleanup: {hips_bone_name} -> {hips_dup_bone_name}"
        )
    except (AttributeError, ValueError) as e:
        logger.info(f"Could not identify VRM hips bone: {e!s}")

    # 1. Transfer fcurves back from duplicates to original bones (only for VRMA export)
    if for_vrma and bone_mapping:
        anim_data = arm_obj.animation_data
        if anim_data and anim_data.action:
            action = anim_data.action

            # Create a reverse mapping (duplicate -> original)
            reverse_mapping = {dup: orig for orig, dup in bone_mapping.items()}

            # Compiled regex pattern for efficiency
            pattern = re.compile(r'pose\.bones\["(.+)"\]\.(location|scale)')

            # Group fcurves by bone and property for batch processing
            fcurve_groups = defaultdict(list)
            for fc in action.fcurves:
                match = pattern.match(fc.data_path)
                if match:
                    dup_bone, prop = match.groups()
                    if dup_bone in reverse_mapping:
                        # Skip transferring location back from hips duplicate
                        if dup_bone == hips_dup_bone_name and prop == "location":
                            logger.info(
                                f"Skipping location transfer back from hips duplicate: {dup_bone}"
                            )
                            continue
                        fcurve_groups[(dup_bone, prop)].append(fc)

            # Process each group of fcurves efficiently
            for (dup_bone, prop), fcurves in fcurve_groups.items():
                orig_bone = reverse_mapping[dup_bone]
                logger.info(
                    f"Transferring {prop} fcurves back from {dup_bone} to {orig_bone}"
                )

                # Process each fcurve for this bone+property
                for fc in fcurves:
                    new_data_path = f'pose.bones["{orig_bone}"].{prop}'
                    array_index = fc.array_index

                    # Check if a matching fcurve already exists and remove it
                    existing_fcurve = None
                    for i, existing_fc in enumerate(action.fcurves):
                        if (
                            existing_fc.data_path == new_data_path
                            and existing_fc.array_index == array_index
                        ):
                            existing_fcurve = i
                            break

                    if existing_fcurve is not None:
                        # Remove the existing fcurve first
                        action.fcurves.remove(action.fcurves[existing_fcurve])

                    # Create a new fcurve for the original bone
                    new_fc = action.fcurves.new(
                        data_path=new_data_path, index=array_index
                    )

                    # Bulk add keyframe points
                    if len(fc.keyframe_points) > 0:
                        new_fc.keyframe_points.add(count=len(fc.keyframe_points))

                        # Copy keyframe points efficiently
                        for i, kp in enumerate(fc.keyframe_points):
                            new_kp = new_fc.keyframe_points[i]
                            new_kp.co = kp.co
                            new_kp.handle_left = kp.handle_left
                            new_kp.handle_right = kp.handle_right
                            new_kp.interpolation = kp.interpolation
                            new_kp.easing = kp.easing

                    # Copy modifiers efficiently
                    for mod in fc.modifiers:
                        new_mod = new_fc.modifiers.new(type=mod.type)
                        if hasattr(mod, "points") and hasattr(new_mod, "points"):
                            for i, point in enumerate(mod.points):
                                if i < len(new_mod.points):
                                    new_mod.points[i].co = point.co
                                    new_mod.points[i].handle_type = point.handle_type

                    # Update once after all modifications
                    new_fc.update()

            # Collect fcurves to remove in a list first
            fcurves_to_remove = []
            for i, fc in enumerate(action.fcurves):
                match = pattern.match(fc.data_path)
                if match and match.group(1) in reverse_mapping:
                    fcurves_to_remove.append(i)

            # Remove fcurves in reverse order to avoid index shifting
            for i in sorted(fcurves_to_remove, reverse=True):
                action.fcurves.remove(action.fcurves[i])

    # 2. Revert vertex group name changes if we have a bone mapping
    if bone_mapping:
        reverse_mapping = {dup: orig for orig, dup in bone_mapping.items()}
        mesh_objects = [
            obj for obj in bpy.data.objects if obj.type == "MESH" and obj.vertex_groups
        ]

        for mesh_obj in mesh_objects:
            # Get list of groups to rename
            rename_data = [
                (i, vg.name, reverse_mapping.get(vg.name))
                for i, vg in enumerate(mesh_obj.vertex_groups)
                if vg.name in reverse_mapping
            ]

            # Apply renames (in reverse order to avoid index shifts)
            for i, old_name, orig_name in sorted(rename_data, reverse=True):
                logger.info(
                    f"Reverting vertex group name from {old_name} to {orig_name} in {mesh_obj.name}"
                )
                mesh_obj.vertex_groups[i].name = orig_name

    # 3. Remove the bone collection if it exists (Blender 4.0+)
    if bpy.app.version >= (4, 0, 0):
        arm_data = arm_obj.data
        group = arm_data.collections.get("vrma translate scale export")
        if group is not None:
            arm_data.collections.remove(group)

    # 4. Remove constraints from duplicate bones in POSE mode
    bpy.ops.object.mode_set(mode="POSE")
    if duplicated_bones:
        logger.info(
            f"Removing constraints from {len(duplicated_bones)} duplicated bones"
        )
        for bone_name in duplicated_bones:
            pbone = arm_obj.pose.bones.get(bone_name)
            if pbone:
                # Remove all constraints
                while pbone.constraints:
                    pbone.constraints.remove(pbone.constraints[0])

    # 5. Remove the duplicate bones in EDIT mode - do this in a single mode switch
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = arm_obj.data.edit_bones

    if duplicated_bones:
        logger.info(f"Removing {len(duplicated_bones)} duplicated bones")
        for bone_name in duplicated_bones:
            bone = edit_bones.get(bone_name)
            if bone:
                logger.info(f"Removing bone: {bone_name}")
                edit_bones.remove(bone)

    # 6. Restore original mode
    bpy.ops.object.mode_set(mode=original_mode)

    elapsed = time.time() - start_time
    logger.info(f"Bone duplication reversal completed in {elapsed:.2f} seconds")


def export_vrm_update_addon_preferences(
    export_op: "EXPORT_SCENE_OT_vrm", context: Context
) -> None:
    if export_op.use_addon_preferences:
        copy_export_preferences(source=export_op, destination=get_preferences(context))

    validation.WM_OT_vrm_validator.detect_errors(
        context,
        export_op.errors,
        export_op.armature_object_name,
    )


class EXPORT_SCENE_OT_vrm(Operator, ExportHelper):
    bl_idname = "export_scene.vrm"
    bl_label = "Save"
    bl_description = "export VRM"
    bl_options: AbstractSet[str] = {"REGISTER"}

    filename_ext = ".vrm"
    filter_glob: StringProperty(  # type: ignore[valid-type]
        default="*.vrm",
        options={"HIDDEN"},
    )

    use_addon_preferences: BoolProperty(  # type: ignore[valid-type]
        name="Export using add-on preferences",
        description="Export using add-on preferences instead of operator arguments",
    )
    export_invisibles: BoolProperty(  # type: ignore[valid-type]
        name="Export Invisible Objects",
        update=export_vrm_update_addon_preferences,
    )
    export_only_selections: BoolProperty(  # type: ignore[valid-type]
        name="Export Only Selections",
        update=export_vrm_update_addon_preferences,
    )
    enable_advanced_preferences: BoolProperty(  # type: ignore[valid-type]
        name="Enable Advanced Options",
        update=export_vrm_update_addon_preferences,
    )
    export_all_influences: BoolProperty(  # type: ignore[valid-type]
        name="Export All Bone Influences",
        description="Don't limit to 4, most viewers truncate to 4, so bone movement may cause jagged meshes",
        update=export_vrm_update_addon_preferences,
        # The upstream says that Models may appear incorrectly in many viewers.
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/356b3dda976303d3ecce8b3bd1591245e576db38/addons/io_scene_gltf2/__init__.py#L760
        default=False,
    )
    export_transform_scale: BoolProperty(  # type: ignore[valid-type]
        name="Support Transform and Scale (Experimental)",
        description="Does not violate humanoid standard, won't break any VRM Apps, but not all apps will support playing these tracks back",
        update=export_vrm_update_addon_preferences,
        default=False,
    )
    export_lights: BoolProperty(  # type: ignore[valid-type]
        name="Export Lights",
    )
    export_gltf_animations: BoolProperty(  # type: ignore[valid-type]
        name="Export glTF Animations",
    )

    errors: CollectionProperty(  # type: ignore[valid-type]
        type=validation.VrmValidationError,
        options={"HIDDEN"},
    )
    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    ignore_warning: BoolProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        if not self.filepath:
            return {"CANCELLED"}

        if self.use_addon_preferences:
            copy_export_preferences(source=get_preferences(context), destination=self)

        return export_vrm(
            Path(self.filepath),
            self,
            context,
            armature_object_name=self.armature_object_name,
        )

    def invoke(self, context: Context, event: Event) -> set[str]:
        self.use_addon_preferences = True
        copy_export_preferences(source=get_preferences(context), destination=self)

        if "gltf" not in dir(bpy.ops.export_scene):
            return ops.wm.vrm_gltf2_addon_disabled_warning(
                "INVOKE_DEFAULT",
            )

        export_objects = search.export_objects(
            context,
            self.armature_object_name,
            export_invisibles=self.export_invisibles,
            export_only_selections=self.export_only_selections,
            export_lights=self.export_lights,
        )

        armatures = [obj for obj in export_objects if obj.type == "ARMATURE"]
        if len(armatures) > 1:
            return ops.wm.vrm_export_armature_selection("INVOKE_DEFAULT")
        if len(armatures) == 1:
            armature = armatures[0]
            armature_data = armature.data
            if not isinstance(armature_data, Armature):
                pass
            elif get_armature_extension(armature_data).is_vrm0():
                Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
                Vrm0HumanoidPropertyGroup.update_all_node_candidates(
                    context, armature_data.name
                )
                humanoid = get_armature_extension(armature_data).vrm0.humanoid
                if all(
                    b.node.bone_name not in b.node_candidates
                    for b in humanoid.human_bones
                ):
                    ops.vrm.assign_vrm0_humanoid_human_bones_automatically(
                        armature_name=armature.name
                    )
                if not humanoid.all_required_bones_are_assigned():
                    return ops.wm.vrm_export_human_bones_assignment(
                        "INVOKE_DEFAULT",
                        armature_object_name=self.armature_object_name,
                    )
            elif get_armature_extension(armature_data).is_vrm1():
                Vrm1HumanBonesPropertyGroup.fixup_human_bones(armature)
                Vrm1HumanBonesPropertyGroup.update_all_node_candidates(
                    context, armature_data.name
                )
                human_bones = get_armature_extension(
                    armature_data
                ).vrm1.humanoid.human_bones
                if all(
                    human_bone.node.bone_name not in human_bone.node_candidates
                    for human_bone in (
                        human_bones.human_bone_name_to_human_bone().values()
                    )
                ):
                    ops.vrm.assign_vrm1_humanoid_human_bones_automatically(
                        armature_name=armature.name
                    )
                if (
                    not human_bones.all_required_bones_are_assigned()
                    and not human_bones.allow_non_humanoid_rig
                ):
                    return ops.wm.vrm_export_human_bones_assignment(
                        "INVOKE_DEFAULT",
                        armature_object_name=self.armature_object_name,
                    )

        if ops.vrm.model_validate(
            "INVOKE_DEFAULT",
            show_successful_message=False,
            armature_object_name=self.armature_object_name,
        ) != {"FINISHED"}:
            return {"CANCELLED"}

        validation.WM_OT_vrm_validator.detect_errors(
            context,
            self.errors,
            self.armature_object_name,
        )
        if not self.ignore_warning and any(
            error.severity <= 1 for error in self.errors
        ):
            return ops.wm.vrm_export_confirmation(
                "INVOKE_DEFAULT", armature_object_name=self.armature_object_name
            )

        return ExportHelper.invoke(self, context, event)

    def draw(self, _context: Context) -> None:
        pass  # Is needed to get panels available

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        filter_glob: str  # type: ignore[no-redef]
        use_addon_preferences: bool  # type: ignore[no-redef]
        export_invisibles: bool  # type: ignore[no-redef]
        export_only_selections: bool  # type: ignore[no-redef]
        enable_advanced_preferences: bool  # type: ignore[no-redef]
        export_all_influences: bool  # type: ignore[no-redef]
        export_transform_scale: bool  # type: ignore[no-redef]
        export_lights: bool  # type: ignore[no-redef]
        export_gltf_animations: bool  # type: ignore[no-redef]
        errors: CollectionPropertyProtocol[  # type: ignore[no-redef]
            VrmValidationError
        ]
        armature_object_name: str  # type: ignore[no-redef]
        ignore_warning: bool  # type: ignore[no-redef]


def export_vrm(
    filepath: Path,
    export_preferences: ExportPreferencesProtocol,
    context: Context,
    *,
    armature_object_name: str,
) -> set[str]:
    if ops.vrm.model_validate(
        "INVOKE_DEFAULT",
        show_successful_message=False,
        armature_object_name=armature_object_name,
    ) != {"FINISHED"}:
        return {"CANCELLED"}

    (
        export_all_influences,
        export_transform_scale,
        export_lights,
        export_gltf_animations,
    ) = (
        (
            export_preferences.export_all_influences,
            export_preferences.export_transform_scale,
            export_preferences.export_lights,
            export_preferences.export_gltf_animations,
        )
        if export_preferences.enable_advanced_preferences
        else (False, False, False, False)
    )

    export_objects = search.export_objects(
        context,
        armature_object_name,
        export_invisibles=export_preferences.export_invisibles,
        export_only_selections=export_preferences.export_only_selections,
        export_lights=export_lights,
    )

    armature_object: Optional[Object] = next(
        (obj for obj in export_objects if obj.type == "ARMATURE"), None
    )
    is_vrm1 = False

    # Initialize a set to track end-chain bones and bones that need preservation
    preserve_bones = set()

    with save_workspace(
        context,
        # アクティブオブジェクト変更しても元に戻せるようにする
        armature_object,
    ):
        if armature_object:
            armature_object_is_temporary = False
            armature_data = armature_object.data
            if isinstance(armature_data, Armature):
                is_vrm1 = get_armature_extension(armature_data).is_vrm1()
        else:
            armature_object_is_temporary = True
            ops.icyp.make_basic_armature("EXEC_DEFAULT")
            armature_object = context.view_layer.objects.active
            if not armature_object or armature_object.type != "ARMATURE":
                message = "Failed to generate temporary armature"
                raise RuntimeError(message)

        migration.migrate(context, armature_object.name)

        # Track if we did bone duplication so we can revert it
        bone_mapping = None
        duplicated_bones = None
        preserve_bones = set()

        # If transform_scale is enabled, set up the duplicate bones before export
        if export_transform_scale and armature_object:
            # Store current active object and set the armature as active
            original_active_object = context.view_layer.objects.active
            context.view_layer.objects.active = armature_object

            # Identify end-chain bones before duplication
            bpy.ops.object.mode_set(mode="EDIT")
            arm_data = armature_object.data

            # Get all bones that don't have children (end-chain bones)
            preserve_bones = set()
            for bone in arm_data.edit_bones:
                if not bone.children:
                    preserve_bones.add(bone.name)
                    logger.info(f"Identified end-chain bone to preserve: {bone.name}")

            bpy.ops.object.mode_set(mode="OBJECT")

            # Run the bone duplication process - don't transfer fcurves for regular VRM export
            logger.info("Running bone duplication for VRM export with transform_scale")
            bone_mapping, duplicated_bones, end_chain_bones = run_bone_duplication(
                for_vrma=False
            )

            # Restore original active object
            context.view_layer.objects.active = original_active_object

        if is_vrm1:
            vrm_exporter: AbstractBaseVrmExporter = Vrm1Exporter(
                context,
                export_objects,
                armature_object,
                export_all_influences=export_all_influences,
                export_lights=export_lights,
                export_gltf_animations=export_gltf_animations,
                export_transform_scale=export_transform_scale,
                preserve_end_bones=preserve_bones,
            )
        else:
            vrm_exporter = Vrm0Exporter(
                context,
                export_objects,
                armature_object,
                preserve_end_bones=preserve_bones,
            )

        vrm_bytes = vrm_exporter.export_vrm()

        # Revert bone duplication if we did it
        if bone_mapping and duplicated_bones:
            # Set the armature as active object
            original_active_object = context.view_layer.objects.active
            context.view_layer.objects.active = armature_object

            # Revert the bone duplication process - don't touch fcurves for VRM export
            logger.info("Reverting bone duplication after VRM export")
            revert_bone_duplication(bone_mapping, duplicated_bones, for_vrma=False)

            # Restore original active object
            context.view_layer.objects.active = original_active_object

        if vrm_bytes is None:
            return {"CANCELLED"}

    Path(filepath).write_bytes(vrm_bytes)

    if armature_object_is_temporary:
        if armature_object.users <= 1:
            # アクティブオブジェクトから外れた後にremoveする
            context.blend_data.objects.remove(armature_object)
        else:
            logger.warning("Failed to remove temporary armature")

    return {"FINISHED"}


class VRM_PT_export_file_browser_tool_props(Panel):
    bl_idname = "VRM_IMPORTER_PT_export_error_messages"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_parent_id = "FILE_PT_operator"
    bl_label = ""
    bl_options: AbstractSet[str] = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        space_data = context.space_data
        if not isinstance(space_data, SpaceFileBrowser):
            return False
        return space_data.active_operator.bl_idname == "EXPORT_SCENE_OT_vrm"

    def draw(self, context: Context) -> None:
        space_data = context.space_data
        if not isinstance(space_data, SpaceFileBrowser):
            return

        operator = space_data.active_operator
        if not isinstance(operator, EXPORT_SCENE_OT_vrm):
            return

        layout = self.layout

        warning_message = version.panel_warning_message()
        if warning_message:
            box = layout.box()
            warning_column = box.column(align=True)
            for index, warning_line in enumerate(warning_message.splitlines()):
                warning_column.label(
                    text=warning_line,
                    translate=False,
                    icon="NONE" if index else "ERROR",
                )

        draw_export_preferences_layout(operator, layout)

        if operator.errors:
            validation.WM_OT_vrm_validator.draw_errors(
                layout.box(),
                operator.errors,
                show_successful_message=False,
            )


class VRM_PT_export_vrma_help(Panel):
    bl_idname = "VRM_PT_export_vrma_help"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_parent_id = "FILE_PT_operator"
    bl_label = ""
    bl_options: AbstractSet[str] = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        space_data = context.space_data
        if not isinstance(space_data, SpaceFileBrowser):
            return False
        return space_data.active_operator.bl_idname == "EXPORT_SCENE_OT_vrma"

    def draw(self, _context: Context) -> None:
        layout = self.layout
        draw_help_message(layout)
        if not isinstance(_context.space_data, SpaceFileBrowser):
            return
        space_data = _context.space_data
        if space_data.active_operator:
            op = space_data.active_operator
            if hasattr(op, "export_non_humanoid_tracks"):
                box = layout.box()
                box.label(text="Additional Export Options", icon="OPTIONS")
                box.prop(op, "export_non_humanoid_tracks")
                box.prop(op, "export_translation_tracks")
                box.prop(op, "export_scale_tracks")


def menu_export(menu_op: Operator, _context: Context) -> None:
    vrm_export_op = layout_operator(
        menu_op.layout, EXPORT_SCENE_OT_vrm, text="VRM (.vrm)"
    )
    vrm_export_op.use_addon_preferences = True
    vrm_export_op.armature_object_name = ""
    vrm_export_op.ignore_warning = False

    vrma_export_op = layout_operator(
        menu_op.layout, EXPORT_SCENE_OT_vrma, text="VRM Animation (.vrma)"
    )
    vrma_export_op.armature_object_name = ""


class EXPORT_SCENE_OT_vrma(Operator, ExportHelper):
    bl_idname = "export_scene.vrma"
    bl_label = "Save"
    bl_description = "Export VRM Animation"
    bl_options: AbstractSet[str] = {"REGISTER"}

    filename_ext = ".vrma"
    filter_glob: StringProperty(  # type: ignore[valid-type]
        default="*.vrma",
        options={"HIDDEN"},
    )

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    # New property to support translation and scale in VRM files
    export_transform_scale: BoolProperty(  # type: ignore[valid-type]
        name="Support Transform and Scale (Experimental)",
        description="Does not violate humanoid standard, won't break any VRM Apps, but not all apps will support playing these tracks back",
        default=False,
    )

    # New property for non-humanoid tracks export
    export_non_humanoid_tracks: BoolProperty(  # type: ignore[valid-type]
        name="include non-humanoid tracks? (rotation only)",
        description=(
            "Warning: scale and translation tracks are not supported by the VRMA "
            "standard and some apps will have errors if you include these tracks."
        ),
        default=False,
    )
    # New property for including translation tracks (for bones other than hips)
    export_translation_tracks: BoolProperty(  # type: ignore[valid-type]
        name="Include translation tracks for all bones? (humanoid + non-humanoid)",
        description=(
            "Include translation tracks for all bones (hips always export translation"
            " as required)."
        ),
        default=False,
    )
    # New property for including scale tracks
    export_scale_tracks: BoolProperty(  # type: ignore[valid-type]
        name="Include scale tracks for all bones? (humanoid + non-humanoid)",
        description="Include scale tracks for all bones.",
        default=False,
    )

    def execute(self, context: Context) -> set[str]:
        if WM_OT_vrma_export_prerequisite.detect_errors(
            context, self.armature_object_name
        ):
            return {"CANCELLED"}
        if not self.filepath:
            return {"CANCELLED"}
        if not self.armature_object_name:
            armature = search.current_armature(context)
        else:
            armature = context.blend_data.objects.get(self.armature_object_name)
        if not armature:
            return {"CANCELLED"}

        # If translation or scale tracks are enabled, we should also enable non-humanoid tracks
        if (
            self.export_translation_tracks
            or self.export_scale_tracks
            or self.export_transform_scale
        ):
            self.export_non_humanoid_tracks = True

        # Store current active object
        original_active_object = context.view_layer.objects.active

        # Set armature as active object
        context.view_layer.objects.active = armature

        # Flag to track if we performed bone duplication
        used_bone_duplication = False
        bone_mapping = None
        duplicated_bones = None

        # Get the transform_scale preference from any active VRM exporter
        export_transform_scale = False
        if hasattr(context, "scene") and hasattr(context.scene, "vrm_addon_extension"):
            if hasattr(context.scene.vrm_addon_extension, "export_transform_scale"):
                export_transform_scale = (
                    context.scene.vrm_addon_extension.export_transform_scale
                )

        # If translation or scale tracks are enabled, run the bone duplication process
        if (
            self.export_translation_tracks
            or self.export_scale_tracks
            or export_transform_scale
        ):
            used_bone_duplication = True
            # Run duplicating bones functionality
            logger.info("Duplicate bones for translation and scale export")
            bone_mapping, root_bones, duplicated_bones = duplicate_bones()

            if bone_mapping:
                add_copy_rotation_constraints(bone_mapping, root_bones)
                transfer_fcurves(bone_mapping)
            else:
                logger.warning("Bone duplication failed, continuing export without it")
                used_bone_duplication = False

        # Execute the export
        result = VrmAnimationExporter.execute(
            context,
            Path(self.filepath),
            armature,
            include_non_humanoid_tracks=self.export_non_humanoid_tracks,
            include_translation_tracks=self.export_translation_tracks,
            include_scale_tracks=self.export_scale_tracks,
        )

        # If bone duplication was performed, revert it
        if used_bone_duplication and bone_mapping and duplicated_bones:
            logger.info("Reverting bone duplication")
            revert_bone_duplication(bone_mapping, duplicated_bones, for_vrma=True)

        # Restore original active object
        context.view_layer.objects.active = original_active_object

        return result

    def invoke(self, context: Context, event: Event) -> set[str]:
        if WM_OT_vrma_export_prerequisite.detect_errors(
            context, self.armature_object_name
        ):
            return ops.wm.vrma_export_prerequisite(
                "INVOKE_DEFAULT",
                armature_object_name=self.armature_object_name,
            )
        return ExportHelper.invoke(self, context, event)

    def draw(self, _context: Context) -> None:
        pass  # Is needed to get panels available

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        filter_glob: str  # type: ignore[no-redef]
        armature_object_name: str  # type: ignore[no-redef]
        export_non_humanoid_tracks: bool  # type: ignore[no-redef]
        export_translation_tracks: bool  # type: ignore[no-redef]
        export_scale_tracks: bool  # type: ignore[no-redef]


class WM_OT_vrm_export_human_bones_assignment(Operator):
    bl_label = "VRM Required Bones Assignment"
    bl_idname = "wm.vrm_export_human_bones_assignment"
    bl_options: AbstractSet[str] = {"REGISTER"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        preferences = get_preferences(context)
        export_objects = search.export_objects(
            context,
            self.armature_object_name,
            export_invisibles=preferences.export_invisibles,
            export_only_selections=preferences.export_only_selections,
            export_lights=preferences.export_lights,
        )
        armatures = [obj for obj in export_objects if obj.type == "ARMATURE"]
        if len(armatures) != 1:
            return {"CANCELLED"}
        armature = armatures[0]
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return {"CANCELLED"}
        if get_armature_extension(armature_data).is_vrm0():
            Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
            Vrm0HumanoidPropertyGroup.update_all_node_candidates(
                context, armature_data.name
            )
            humanoid = get_armature_extension(armature_data).vrm0.humanoid
            if not humanoid.all_required_bones_are_assigned():
                return {"CANCELLED"}
        elif get_armature_extension(armature_data).is_vrm1():
            Vrm1HumanBonesPropertyGroup.fixup_human_bones(armature)
            Vrm1HumanBonesPropertyGroup.update_all_node_candidates(
                context, armature_data.name
            )
            human_bones = get_armature_extension(
                armature_data
            ).vrm1.humanoid.human_bones
            if (
                not human_bones.all_required_bones_are_assigned()
                and not human_bones.allow_non_humanoid_rig
            ):
                return {"CANCELLED"}
        else:
            return {"CANCELLED"}
        return ops.export_scene.vrm(
            "INVOKE_DEFAULT", armature_object_name=self.armature_object_name
        )

    def invoke(self, context: Context, _event: Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self, width=800)

    def draw(self, context: Context) -> None:
        preferences = get_preferences(context)
        armatures = [
            obj
            for obj in search.export_objects(
                context,
                self.armature_object_name,
                export_invisibles=preferences.export_invisibles,
                export_only_selections=preferences.export_only_selections,
                export_lights=preferences.export_lights,
            )
            if obj.type == "ARMATURE"
        ]
        if not armatures:
            return
        armature = armatures[0]
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return

        if get_armature_extension(armature_data).is_vrm0():
            WM_OT_vrm_export_human_bones_assignment.draw_vrm0(self.layout, armature)
        elif get_armature_extension(armature_data).is_vrm1():
            WM_OT_vrm_export_human_bones_assignment.draw_vrm1(self.layout, armature)

    @staticmethod
    def draw_vrm0(layout: UILayout, armature: Object) -> None:
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return

        humanoid = get_armature_extension(armature_data).vrm0.humanoid
        if humanoid.all_required_bones_are_assigned():
            alert_box = layout.box()
            alert_box.label(
                text="All VRM Required Bones have been assigned.", icon="CHECKMARK"
            )
        else:
            alert_box = layout.box()
            alert_box.alert = True
            alert_box.label(
                text="There are unassigned VRM Required Bones. Please assign all.",
                icon="ERROR",
            )
        draw_vrm0_humanoid_operators_layout(armature, layout)
        row = layout.split(factor=0.5)
        draw_vrm0_humanoid_required_bones_layout(armature, row.column())
        draw_vrm0_humanoid_optional_bones_layout(armature, row.column())

    @staticmethod
    def draw_vrm1(layout: UILayout, armature: Object) -> None:
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return

        human_bones = get_armature_extension(armature_data).vrm1.humanoid.human_bones
        if human_bones.all_required_bones_are_assigned():
            alert_box = layout.box()
            alert_box.label(
                text="All VRM Required Bones have been assigned.", icon="CHECKMARK"
            )
        elif human_bones.allow_non_humanoid_rig:
            alert_box = layout.box()
            alert_box.label(
                text="This armature will be exported but not as humanoid."
                + " It can not have animations applied"
                + " for humanoid avatars.",
                icon="CHECKMARK",
            )
        else:
            alert_box = layout.box()
            alert_box.alert = True
            alert_column = alert_box.column(align=True)
            for error_message in human_bones.error_messages():
                alert_column.label(text=error_message, translate=False, icon="ERROR")

        layout_operator(
            layout,
            VRM_OT_assign_vrm1_humanoid_human_bones_automatically,
            icon="ARMATURE_DATA",
        ).armature_name = armature.name

        row = layout.split(factor=0.5)
        draw_vrm1_humanoid_required_bones_layout(human_bones, row.column())
        draw_vrm1_humanoid_optional_bones_layout(human_bones, row.column())

        non_humanoid_export_column = layout.column()
        non_humanoid_export_column.prop(human_bones, "allow_non_humanoid_rig")

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]


class WM_OT_vrm_export_confirmation(Operator):
    bl_label = "VRM Export Confirmation"
    bl_idname = "wm.vrm_export_confirmation"
    bl_options: AbstractSet[str] = {"REGISTER"}

    errors: CollectionProperty(type=validation.VrmValidationError)  # type: ignore[valid-type]

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    export_anyway: BoolProperty(  # type: ignore[valid-type]
        name="Export Anyway",
    )

    def execute(self, _context: Context) -> set[str]:
        if not self.export_anyway:
            return {"CANCELLED"}
        ops.export_scene.vrm(
            "INVOKE_DEFAULT",
            ignore_warning=True,
            armature_object_name=self.armature_object_name,
        )
        return {"FINISHED"}

    def invoke(self, context: Context, _event: Event) -> set[str]:
        validation.WM_OT_vrm_validator.detect_errors(
            context,
            self.errors,
            self.armature_object_name,
        )
        return context.window_manager.invoke_props_dialog(self, width=800)

    def draw(self, _context: Context) -> None:
        layout = self.layout
        layout.label(
            text="There is a high-impact warning. VRM may not export as intended.",
            icon="ERROR",
        )

        column = layout.column()
        for error in self.errors:
            if error.severity != 1:
                continue
            column.prop(
                error,
                "message",
                text="",
                translate=False,
            )

        layout.prop(self, "export_anyway")

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        errors: CollectionPropertyProtocol[  # type: ignore[no-redef]
            VrmValidationError
        ]
        armature_object_name: str  # type: ignore[no-redef]
        export_anyway: bool  # type: ignore[no-redef]


class WM_OT_vrm_export_armature_selection(Operator):
    bl_label = "VRM Export Armature Selection"
    bl_idname = "wm.vrm_export_armature_selection"
    bl_options: AbstractSet[str] = {"REGISTER"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    armature_object_name_candidates: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup,
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        if not self.armature_object_name:
            return {"CANCELLED"}
        armature_object = context.blend_data.objects.get(self.armature_object_name)
        if not armature_object or armature_object.type != "ARMATURE":
            return {"CANCELLED"}
        ops.export_scene.vrm(
            "INVOKE_DEFAULT", armature_object_name=self.armature_object_name
        )

        return {"FINISHED"}

    def invoke(self, context: Context, _event: Event) -> set[str]:
        if not self.armature_object_name:
            armature_object = search.current_armature(context)
            if armature_object:
                self.armature_object_name = armature_object.name
        self.armature_object_name_candidates.clear()
        for obj in context.blend_data.objects:
            if obj.type != "ARMATURE":
                continue
            candidate = self.armature_object_name_candidates.add()
            candidate.value = obj.name

        return context.window_manager.invoke_props_dialog(self, width=600)

    def draw(self, _context: Context) -> None:
        layout = self.layout
        layout.label(
            text="Multiple armatures were found; please select one to export as VRM.",
            icon="ERROR",
        )

        layout.prop_search(
            self,
            "armature_object_name",
            self,
            "armature_object_name_candidates",
            icon="OUTLINER_OB_ARMATURE",
            text="",
            translate=False,
        )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        armature_object_name_candidates: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]


class WM_OT_vrma_export_prerequisite(Operator):
    bl_label = "VRM Animation Export Prerequisite"
    bl_idname = "wm.vrma_export_prerequisite"
    bl_options: AbstractSet[str] = {"REGISTER"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    armature_object_name_candidates: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup,
        options={"HIDDEN"},
    )
    export_non_humanoid_tracks: BoolProperty(  # type: ignore[valid-type]
        name="Include non-humanoid tracks with translation and scale?",
        description=(
            "(Warning: scale and translation tracks are not supported by the "
            "VRMA standard and some apps will have errors if you include "
            "these tracks)."
        ),
        default=False,
    )
    export_translation_tracks: BoolProperty(  # type: ignore[valid-type]
        name="Include translation tracks for all bones?",
        description=(
            "Include translation tracks for all bones (hips always export translation)."
        ),
        default=False,
    )
    export_scale_tracks: BoolProperty(  # type: ignore[valid-type]
        name="Include scale tracks for all bones?",
        description="Include scale tracks for all bones.",
        default=False,
    )
    export_transform_scale: BoolProperty(  # type: ignore[valid-type]
        name="Support Transform and Scale",
        description="Experimental support for transform and scale",
        default=False,
    )

    @staticmethod
    def detect_errors(context: Context, armature_object_name: str) -> list[str]:
        error_messages: list[str] = []

        if not armature_object_name:
            armature = search.current_armature(context)
        else:
            armature = context.blend_data.objects.get(armature_object_name)

        if not armature:
            error_messages.append(pgettext("Armature not found"))
            return error_messages

        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            error_messages.append(pgettext("Armature not found"))
            return error_messages

        ext = get_armature_extension(armature_data)
        if get_armature_extension(armature_data).is_vrm1():
            humanoid = ext.vrm1.humanoid
            if not humanoid.human_bones.all_required_bones_are_assigned():
                error_messages.append(pgettext("Please assign required human bones"))
        else:
            error_messages.append(pgettext("Please set the version of VRM to 1.0"))

        return error_messages

    def execute(self, _context: Context) -> set[str]:
        # If translation or scale tracks are enabled, automatically enable non-humanoid tracks
        if (
            self.export_translation_tracks
            or self.export_scale_tracks
            or self.export_transform_scale
        ):
            self.export_non_humanoid_tracks = True

        return ops.export_scene.vrma(
            "INVOKE_DEFAULT",
            armature_object_name=self.armature_object_name,
            export_non_humanoid_tracks=self.export_non_humanoid_tracks,
            export_translation_tracks=self.export_translation_tracks,
            export_scale_tracks=self.export_scale_tracks,
        )

    def invoke(self, context: Context, _event: Event) -> set[str]:
        if not self.armature_object_name:
            armature_object = search.current_armature(context)
            if armature_object:
                self.armature_object_name = armature_object.name
        self.armature_object_name_candidates.clear()
        for obj in context.blend_data.objects:
            if obj.type != "ARMATURE":
                continue
            candidate = self.armature_object_name_candidates.add()
            candidate.value = obj.name
        return context.window_manager.invoke_props_dialog(self, width=800)

    def draw(self, context: Context) -> None:
        layout = self.layout

        layout.label(
            text="VRM Animation export requires a VRM 1.0 armature",
            icon="INFO",
        )

        error_messages = WM_OT_vrma_export_prerequisite.detect_errors(
            context, self.armature_object_name
        )

        layout.prop_search(
            self,
            "armature_object_name",
            self,
            "armature_object_name_candidates",
            icon="OUTLINER_OB_ARMATURE",
            text="Armature to be exported",
        )

        if error_messages:
            error_column = layout.box().column(align=True)
            for error_message in error_messages:
                error_column.label(text=error_message, icon="ERROR", translate=False)

        if not self.armature_object_name:
            armature = search.current_armature(context)
        else:
            armature = context.blend_data.objects.get(self.armature_object_name)
        if armature:
            armature_data = armature.data
            if isinstance(armature_data, Armature):
                ext = get_armature_extension(armature_data)
                if get_armature_extension(armature_data).is_vrm1():
                    humanoid = ext.vrm1.humanoid
                    if not humanoid.human_bones.all_required_bones_are_assigned():
                        WM_OT_vrma_export_human_bones_assignment.draw_vrm1(
                            self.layout, armature
                        )

        # Draw the additional export options
        box = layout.box()
        box.label(text="Additional Export Options", icon="OPTIONS")
        box.prop(self, "export_non_humanoid_tracks")

        # Create a subbox for translation/scale options with a note that they auto-enable non-humanoid tracks
        scale_trans_box = box.box()
        scale_trans_box.label(
            text="Advanced Options (will enable non-humanoid tracks)", icon="ERROR"
        )
        scale_trans_box.prop(self, "export_translation_tracks")
        scale_trans_box.prop(self, "export_scale_tracks")

        # Update non-humanoid tracks if translation or scale is enabled
        if (
            self.export_translation_tracks
            or self.export_scale_tracks
            or self.export_transform_scale
        ):
            self.export_non_humanoid_tracks = True

    if TYPE_CHECKING:
        armature_object_name: str  # type: ignore[no-redef]
        armature_object_name_candidates: CollectionPropertyProtocol[StringPropertyGroup]  # type: ignore[no-redef]
        export_non_humanoid_tracks: bool  # type: ignore[no-redef]
        export_translation_tracks: bool  # type: ignore[no-redef]
        export_scale_tracks: bool  # type: ignore[no-redef]
        export_transform_scale: bool  # type: ignore[no-redef]


def draw_help_message(layout: UILayout) -> None:
    help_message = pgettext(
        "Animations to be exported\n"
        + "- Humanoid bone rotations\n"
        + "- Humanoid hips bone translations\n"
        + "- Expression preview value\n"
        + "- Look At preview target translation\n"
    )
    help_box = layout.box()
    help_column = help_box.column(align=True)
    for index, help_line in enumerate(help_message.splitlines()):
        help_column.label(
            text=help_line,
            translate=False,
            icon="NONE" if index else "INFO",
        )

    open_op = layout_operator(
        help_column,
        VRM_OT_open_url_in_web_browser,
        icon="URL",
        text="Open help in a Web Browser",
    )
    open_op.url = pgettext("https://vrm-addon-for-blender.info/en/animation/")
