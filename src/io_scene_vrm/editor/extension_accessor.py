# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import TYPE_CHECKING, TypeVar

from bpy.types import Armature, Bone, Material, NodeTree, Object, Scene

if TYPE_CHECKING:
    from .extension import (
        VrmAddonArmatureExtensionPropertyGroup,
        VrmAddonBoneExtensionPropertyGroup,
        VrmAddonMaterialExtensionPropertyGroup,
        VrmAddonNodeTreeExtensionPropertyGroup,
        VrmAddonObjectExtensionPropertyGroup,
        VrmAddonSceneExtensionPropertyGroup,
    )

__Extension = TypeVar("__Extension")


def get_vrm_addon_extension_or_raise(
    obj: object, expected_type: type[__Extension]
) -> __Extension:
    extension = getattr(obj, "vrm_addon_extension", None)
    if isinstance(extension, expected_type):
        return extension

    message = f"{extension} is not a {expected_type} but {type(extension)}"
    raise TypeError(message)


def get_material_extension(
    material: Material,
) -> "VrmAddonMaterialExtensionPropertyGroup":
    from .extension import VrmAddonMaterialExtensionPropertyGroup

    return get_vrm_addon_extension_or_raise(
        material, VrmAddonMaterialExtensionPropertyGroup
    )


def get_armature_extension(
    armature: Armature,
) -> "VrmAddonArmatureExtensionPropertyGroup":
    from .extension import VrmAddonArmatureExtensionPropertyGroup

    return get_vrm_addon_extension_or_raise(
        armature, VrmAddonArmatureExtensionPropertyGroup
    )


def get_node_tree_extension(
    node_tree: NodeTree,
) -> "VrmAddonNodeTreeExtensionPropertyGroup":
    from .extension import VrmAddonNodeTreeExtensionPropertyGroup

    return get_vrm_addon_extension_or_raise(
        node_tree, VrmAddonNodeTreeExtensionPropertyGroup
    )


def get_scene_extension(scene: Scene) -> "VrmAddonSceneExtensionPropertyGroup":
    from .extension import VrmAddonSceneExtensionPropertyGroup

    return get_vrm_addon_extension_or_raise(scene, VrmAddonSceneExtensionPropertyGroup)


def get_bone_extension(bone: Bone) -> "VrmAddonBoneExtensionPropertyGroup":
    from .extension import VrmAddonBoneExtensionPropertyGroup

    return get_vrm_addon_extension_or_raise(bone, VrmAddonBoneExtensionPropertyGroup)


def get_object_extension(obj: Object) -> "VrmAddonObjectExtensionPropertyGroup":
    from .extension import VrmAddonObjectExtensionPropertyGroup

    return get_vrm_addon_extension_or_raise(obj, VrmAddonObjectExtensionPropertyGroup)
