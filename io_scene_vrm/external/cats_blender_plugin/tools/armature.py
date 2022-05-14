# MIT License

# Copyright (c) 2017 GiveMeAllYourCats

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Code author: Shotariya
# Repo: https://github.com/Grim-es/shotariya
# Code author: Neitri
# Repo: https://github.com/netri/blender_neitri_tools
# Edits by: GiveMeAllYourCats, Hotox

# pylint: disable=anomalous-backslash-in-string,redefined-builtin,no-else-break

import copy
from typing import List, Set, Union

from ...cats_blender_plugin_armature import (
    CatsArmature,
    CatsArmatureDataEditBone,
    CatsArmaturePoseBone,
)
from . import armature_bones as Bones


class FixArmature:
    @staticmethod
    def create_cats_bone_name_mapping(armature: CatsArmature) -> Set[str]:
        bone: Union[
            CatsArmaturePoseBone, CatsArmatureDataEditBone, List[str], None
        ] = None
        value: Union[str, List[str]] = ""

        # Todo: Remove this
        # armature = Common.get_armature()
        # Common.switch('EDIT')
        #
        # for bone in armature.data.edit_bones:
        #     bone.tail = bone.head
        #     bone.tail[2] += 0.1
        #
        # Common.switch('OBJECT')
        #
        #
        # return {'FINISHED'}

        print("\nFixing Model:\n")

        # Check if bone matrix == world matrix, important for xps models

        # Add rename bones to reweight bones
        temp_rename_bones = copy.deepcopy(Bones.bone_rename)

        for key, value in Bones.bone_rename_fingers.items():
            temp_rename_bones[key] = value

        # Count objects for loading bar

        # Get Double Entries
        print("DOUBLE ENTRIES:")
        print("RENAME:")
        list = []
        for key, value in temp_rename_bones.items():
            for name in value:
                if name.lower() not in list:
                    list.append(name.lower())
                else:
                    print(key + " | " + name)
        print("REWEIGHT:")
        print("DOUBLES END")

        # Check if model is mmd model

        # Perform source engine specific operations
        # Check if model is source engine model
        source_engine = False
        for bone in armature.pose.bones:
            if bone.name.startswith("ValveBiped"):
                source_engine = True
                break

        # Remove unused animation data

        # Delete unused VTA mesh

        # Reset to default

        # Find 3D view

        # Remove Rigidbodies and joints

        # Remove objects from different layers and things that are not meshes

        # Unlock all transforms

        # Unlock all bone transforms

        # Remove empty mmd object and unused objects

        # Fix VRM meshes being outside of the armature

        # Check if weird FBX model

        # Fixes bones disappearing, prevents bones from having their tail and head at the exact same position

        # Combines same materials

        # Apply transforms of this model

        # Puts all meshes into a list and joins them if selected

        # Translate bones and unhide them all

        # Armature should be selected

        # Reset pose position

        # Enter edit mode

        # Show all hidden verts and faces

        # Remove Bone Groups

        # Bone constraints should be deleted
        # if context.scene.remove_constraints:

        # Model should be in rest position
        # armature.data.pose_position = 'REST'

        # Count steps for loading bar again and reset the layers

        # Start loading bar

        # List of chars to replace if they are at the start of a bone name
        starts_with = [
            ("_", ""),
            ("ValveBiped_", ""),
            ("Valvebiped_", ""),
            ("Bip1_", "Bip_"),
            ("Bip01_", "Bip_"),
            ("Bip001_", "Bip_"),
            ("Bip01", ""),
            ("Bip02_", "Bip_"),
            ("Character1_", ""),
            ("HLP_", ""),
            ("JD_", ""),
            ("JU_", ""),
            ("Armature|", ""),
            ("Bone_", ""),
            ("C_", ""),
            ("Cf_S_", ""),
            ("Cf_J_", ""),
            ("G_", ""),
            ("Joint_", ""),
            ("Def_C_", ""),
            ("Def_", ""),
            ("DEF_", ""),
            ("Chr_", ""),
            ("Chr_", ""),
            ("B_", ""),
        ]
        # List of chars to replace if they are at the end of a bone name
        ends_with = [
            ("_Bone", ""),
            ("_Bn", ""),
            ("_Le", "_L"),
            ("_Ri", "_R"),
            ("_", ""),
        ]
        # List of chars to replace
        replaces = [
            (" ", "_"),
            ("-", "_"),
            (".", "_"),
            (":", "_"),
            ("____", "_"),
            ("___", "_"),
            ("__", "_"),
            ("_Le_", "_L_"),
            ("_Ri_", "_R_"),
            ("LEFT", "Left"),
            ("RIGHT", "Right"),
        ]

        # Standardize names
        for bone in armature.data.edit_bones:
            name = bone.name

            # Always uppercase at the start and after an underscore
            upper_name = ""
            for i, s in enumerate(name.split("_")):
                if i != 0:
                    upper_name += "_"
                upper_name += s[:1].upper() + s[1:]
            name = upper_name

            # Replace all the things!
            for replacement in replaces:
                name = name.replace(replacement[0], replacement[1])

            # Replace if name starts with specified chars
            for replacement in starts_with:
                if name.startswith(replacement[0]):
                    name = replacement[1] + name[len(replacement[0]) :]

            # Replace if name ends with specified chars
            for replacement in ends_with:
                if name.endswith(replacement[0]):
                    name = name[: -len(replacement[0])] + replacement[1]

            # Remove digits from the start
            name_split = name.split("_")
            if len(name_split) > 1 and name_split[0].isdigit():
                name = name_split[1]

            # Specific condition
            name_split = name.split('"')
            if len(name_split) > 3:
                name = name_split[1]

            # Another specific condition
            if ":" in name:
                for i, split in enumerate(name.split(":")):
                    if i == 0:
                        name = ""
                    else:
                        name += split

            # Remove S0 from the end
            if name[-2:] == "S0":
                name = name[:-2]

            if name[-4:] == "_Jnt":
                name = name[:-4]

            bone.name = name

        # Add conflicting bone names to new list
        conflicting_bones = []
        for names in Bones.bone_list_conflicting_names:
            if "\Left" not in names[1] and "\L" not in names[1]:
                conflicting_bones.append(names)
                continue

            names0 = []
            name1 = ""
            name2 = ""
            for name0 in names[0]:
                names0.append(
                    name0.replace("\Left", "Left")
                    .replace("\left", "left")
                    .replace("\L", "L")
                    .replace("\l", "l")
                )
            if "\Left" in names[1] or "\L" in names[1]:
                name1 = (
                    names[1]
                    .replace("\Left", "Left")
                    .replace("\left", "left")
                    .replace("\L", "L")
                    .replace("\l", "l")
                )
            if "\Left" in names[2] or "\L" in names[2]:
                name2 = (
                    names[2]
                    .replace("\Left", "Left")
                    .replace("\left", "left")
                    .replace("\L", "L")
                    .replace("\l", "l")
                )
            conflicting_bones.append((names0, name1, name2))

            for name0 in names[0]:
                names0.append(
                    name0.replace("\Left", "Right")
                    .replace("\left", "right")
                    .replace("\L", "R")
                    .replace("\l", "r")
                )
            if "\Left" in names[1] or "\L" in names[1]:
                name1 = (
                    names[1]
                    .replace("\Left", "Right")
                    .replace("\left", "right")
                    .replace("\L", "R")
                    .replace("\l", "r")
                )
            if "\Left" in names[2] or "\L" in names[2]:
                name2 = (
                    names[2]
                    .replace("\Left", "Right")
                    .replace("\left", "right")
                    .replace("\L", "R")
                    .replace("\l", "r")
                )
            conflicting_bones.append((names0, name1, name2))

        # Resolve conflicting bone names
        for names in conflicting_bones:

            # Search for bone in armature
            bone = None
            for bone_tmp in armature.data.edit_bones:
                if bone_tmp.name.lower() == names[1].lower():
                    bone = bone_tmp
                    break

            # Cancel if bone was not found
            if not bone:
                continue

            # Search for all the required bones
            found_all = True
            for name in names[0]:
                found = False
                for bone_tmp in armature.data.edit_bones:
                    if bone_tmp.name.lower() == name.lower():
                        found = True
                        break
                if not found:
                    found_all = False
                    break

            # Rename only if all required bones are found
            if found_all:
                bone.name = names[2]

        # Standardize bone names again (new duplicate bones have ".001" in it)
        for bone in armature.data.edit_bones:
            bone.name = bone.name.replace(".", "_")

        # Rename all the bones
        spines = []
        spine_parts = []
        for bone_new, bones_old in temp_rename_bones.items():
            if "\Left" in bone_new or "\L" in bone_new:
                bones = [
                    [
                        bone_new.replace("\Left", "Left")
                        .replace("\left", "left")
                        .replace("\L", "L")
                        .replace("\l", "l"),
                        "",
                    ],
                    [
                        bone_new.replace("\Left", "Right")
                        .replace("\left", "right")
                        .replace("\L", "R")
                        .replace("\l", "r"),
                        "",
                    ],
                ]
            else:
                bones = [[bone_new, ""]]
            for bone_old in bones_old:
                if "\Left" in bone_new or "\L" in bone_new:
                    bones[0][1] = (
                        bone_old.replace("\Left", "Left")
                        .replace("\left", "left")
                        .replace("\L", "L")
                        .replace("\l", "l")
                    )
                    bones[1][1] = (
                        bone_old.replace("\Left", "Right")
                        .replace("\left", "right")
                        .replace("\L", "R")
                        .replace("\l", "r")
                    )
                else:
                    bones[0][1] = bone_old

                for bone in bones:  # bone[0] = new name, bone[1] = old name
                    # Seach for bone in armature
                    bone_final = None
                    for bone_tmp in armature.data.edit_bones:
                        if bone_tmp.name.lower() == bone[1].lower():
                            bone_final = bone_tmp
                            break

                    # Cancel if bone was not found
                    if not bone_final:
                        continue

                    # If spine bone, then don't rename for now, and ignore spines with no children
                    if bone_new == "Spine":
                        if len(bone_final.children) > 0:
                            spines.append(bone_final.name)
                        else:
                            spine_parts.append(bone_final.name)
                        continue

                    # Rename the bone
                    if bone[0] not in armature.data.edit_bones:
                        # print(bone_final.name, '>', bone[0])
                        bone_final.name = bone[0]

        # Check if it is a mixamo model
        mixamo = False
        for bone in armature.data.edit_bones:
            if not mixamo and "Mixamo" in bone.name:
                mixamo = True
                break

        # Rename bones which don't have a side and try to detect it automatically
        for key, value in Bones.bone_list_rename_unknown_side.items():
            for bone in armature.data.edit_bones:
                parent = bone.parent
                if parent is None:
                    continue
                if parent.name == key or parent.name == key.lower():
                    if "right" in bone.name.lower():
                        parent.name = "Right " + value
                        break
                    elif "left" in bone.name.lower():
                        parent.name = "Left " + value
                        break

                parent = parent.parent
                if parent is None:
                    continue
                if parent.name == key or parent.name == key.lower():
                    if "right" in bone.name.lower():
                        parent.name = "Right " + value
                        break
                    elif "left" in bone.name.lower():
                        parent.name = "Left " + value
                        break

        # == FIXING OF SPECIAL BONE CASES ==

        # Fix all spines!
        spine_count = len(spines)

        # Fix spines from armatures with no upper body (like skirts)
        if len(spine_parts) == 1 and not armature.data.edit_bones.get("Neck"):
            if spine_count == 0:
                armature.data.edit_bones.get(spine_parts[0]).name = "Spine"
            else:
                spines.append(spine_parts[0])

        if spine_count == 0:
            pass

        elif spine_count == 1:  # Create missing Chest
            print("BONE CREATION")

            # Check for neck

            # Correct the names

            # Set new Chest bone to new position

            # Adjust spine bone position

            # Reparent bones to include new chest

        elif spine_count == 2:  # Everything correct, just rename them
            print("NORMAL")
            armature.data.edit_bones.get(spines[0]).name = "Spine"
            armature.data.edit_bones.get(spines[1]).name = "Chest"

        elif spine_count == 3:  # Everything correct, just rename them
            print("NORMAL")
            armature.data.edit_bones.get(spines[0]).name = "Spine"
            armature.data.edit_bones.get(spines[1]).name = "Chest"
            armature.data.edit_bones.get(spines[2]).name = "Upper Chest"

        elif spine_count == 4 and source_engine:  # SOURCE ENGINE SPECIFIC
            print("SOURCE ENGINE")
            spine = armature.data.edit_bones.get(spines[0])
            chest = armature.data.edit_bones.get(spines[2])

            chest.name = "Chest"
            spine.name = "Spine"

        elif spine_count > 2:  # Merge spines
            print("MASS MERGING")
            print(spines)
            spine = armature.data.edit_bones.get(spines[0])
            chest = armature.data.edit_bones.get(spines[spine_count - 1])

            # Correct names
            spine.name = "Spine"
            chest.name = "Chest"

            # Adjust spine bone position

            # Add all redundant spines to the merge list

        # Fix missing neck

        # Straighten up the head bone

        # Correct arm bone positions for better looks

        # Hips bone should be fixed as per specification from the SDK code

        # Function: Reweight all eye children into the eyes

        # Reweight all eye children into the eyes

        # Rotate if on head and not fbx (Unreal engine model)

        # Fixes bones disappearing, prevents bones from having their tail and head at the exact same position

        # Merged bones that should be deleted

        # Mixing the weights

        # Delete all the leftover bones from the merging process

        # Reparent all bones to be correct for unity mapping and vrc itself

        # Fix MMD twist bone names

        # Connect all bones with their children if they have exactly one

        # # This is code for testing
        # print('LOOKING FOR BONES!')
        # if 'Head' in Common.get_armature().pose.bones:
        #     print('THEY ARE THERE!')
        # else:
        #     print('NOT FOUND!!!!!!')
        # return {'FINISHED'}

        # At this point, everything should be fixed and now we validate and give errors if needed

        # The bone hierarchy needs to be validated

        # Armature should be named correctly (has to be at the end because of multiple armatures)

        # Fix shading (check for runtime error because of ci tests)

        return {"FINISHED"}
