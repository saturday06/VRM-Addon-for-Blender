# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional, TypeVar

import bpy
from bpy.props import (
    CollectionProperty,
    EnumProperty,
    IntVectorProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import (
    Armature,
    Bone,
    Context,
    Material,
    NodeTree,
    Object,
    PropertyGroup,
    Scene,
)
from mathutils import Matrix, Quaternion

from ..common.logger import get_logger
from ..common.preferences import VrmAddonPreferences
from .khr_character.property_group import KhrCharacterPropertyGroup
from .mtoon1.property_group import Mtoon1MaterialPropertyGroup
from .node_constraint1.property_group import NodeConstraint1NodeConstraintPropertyGroup
from .property_group import StringPropertyGroup, property_group_enum
from .spring_bone1.property_group import SpringBone1SpringBonePropertyGroup
from .vrm0.property_group import Vrm0HumanoidPropertyGroup, Vrm0PropertyGroup
from .vrm1.property_group import Vrm1HumanBonesPropertyGroup, Vrm1PropertyGroup

if TYPE_CHECKING:
    from .property_group import CollectionPropertyProtocol

logger = get_logger(__name__)


class VrmAddonSceneExtensionPropertyGroup(PropertyGroup):
    vrm0_material_gltf_property_names: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )

    vrm0_material_mtoon0_property_names: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )

    @staticmethod
    def update_vrm0_material_property_names_timer_callback() -> Optional[float]:
        context = bpy.context

        VrmAddonSceneExtensionPropertyGroup.update_vrm0_material_property_names(context)
        return None

    @staticmethod
    def defer_update_vrm0_material_property_names() -> None:
        s = VrmAddonSceneExtensionPropertyGroup
        bpy.app.timers.register(s.update_vrm0_material_property_names_timer_callback)

    @staticmethod
    def update_vrm0_material_property_names(
        context: Context, scene_name: Optional[str] = None
    ) -> None:
        # Unity 2022.3.4 + UniVRM 0.112.0
        gltf_property_names = [
            "_Color",
            "_MainTex_ST",
            "_MainTex_ST_S",
            "_MainTex_ST_T",
            "_MetallicGlossMap_ST",
            "_MetallicGlossMap_ST_S",
            "_MetallicGlossMap_ST_T",
            "_BumpMap_ST",
            "_BumpMap_ST_S",
            "_BumpMap_ST_T",
            "_ParallaxMap_ST",
            "_ParallaxMap_ST_S",
            "_ParallaxMap_ST_T",
            "_OcclusionMap_ST",
            "_OcclusionMap_ST_S",
            "_OcclusionMap_ST_T",
            "_EmissionColor",
            "_EmissionMap_ST",
            "_EmissionMap_ST_S",
            "_EmissionMap_ST_T",
            "_DetailMask_ST",
            "_DetailMask_ST_S",
            "_DetailMask_ST_T",
            "_DetailAlbedoMap_ST",
            "_DetailAlbedoMap_ST_S",
            "_DetailAlbedoMap_ST_T",
            "_DetailNormalMap_ST",
            "_DetailNormalMap_ST_S",
            "_DetailNormalMap_ST_T",
        ]

        # UniVRM 0.112.0
        mtoon0_property_names = [
            "_Color",
            "_ShadeColor",
            "_MainTex_ST",
            "_MainTex_ST_S",
            "_MainTex_ST_T",
            "_ShadeTexture_ST",
            "_ShadeTexture_ST_S",
            "_ShadeTexture_ST_T",
            "_BumpMap_ST",
            "_BumpMap_ST_S",
            "_BumpMap_ST_T",
            "_ReceiveShadowTexture_ST",
            "_ReceiveShadowTexture_ST_S",
            "_ReceiveShadowTexture_ST_T",
            "_ShadingGradeTexture_ST",
            "_ShadingGradeTexture_ST_S",
            "_ShadingGradeTexture_ST_T",
            "_RimColor",
            "_RimTexture_ST",
            "_RimTexture_ST_S",
            "_RimTexture_ST_T",
            "_SphereAdd_ST",
            "_SphereAdd_ST_S",
            "_SphereAdd_ST_T",
            "_EmissionColor",
            "_EmissionMap_ST",
            "_EmissionMap_ST_S",
            "_EmissionMap_ST_T",
            "_OutlineWidthTexture_ST",
            "_OutlineWidthTexture_ST_S",
            "_OutlineWidthTexture_ST_T",
            "_OutlineColor",
            "_UvAnimMaskTexture_ST",
            "_UvAnimMaskTexture_ST_S",
            "_UvAnimMaskTexture_ST_T",
        ]

        if scene_name is None:
            scenes: Sequence[Scene] = list(context.blend_data.scenes)
        else:
            scene = context.blend_data.scenes.get(scene_name)
            if not scene:
                logger.error('No scene "%s"', scene_name)
                return
            scenes = [scene]

        for scene in scenes:
            ext = get_scene_extension(scene)

            if gltf_property_names != [
                n.value for n in ext.vrm0_material_gltf_property_names
            ]:
                ext.vrm0_material_gltf_property_names.clear()
                for gltf_property_name in gltf_property_names:
                    n = ext.vrm0_material_gltf_property_names.add()
                    n.value = gltf_property_name

            if mtoon0_property_names != [
                n.value for n in ext.vrm0_material_mtoon0_property_names
            ]:
                ext.vrm0_material_mtoon0_property_names.clear()
                for mtoon0_property_name in mtoon0_property_names:
                    n = ext.vrm0_material_mtoon0_property_names.add()
                    n.value = mtoon0_property_name

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        vrm0_material_gltf_property_names: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]
        vrm0_material_mtoon0_property_names: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]


class VrmAddonBoneExtensionPropertyGroup(PropertyGroup):
    uuid: StringProperty()  # type: ignore[valid-type]

    (
        axis_translation_enum,
        (
            AXIS_TRANSLATION_AUTO,
            AXIS_TRANSLATION_NONE,
            AXIS_TRANSLATION_X_TO_Y,
            AXIS_TRANSLATION_MINUS_X_TO_Y,
            AXIS_TRANSLATION_MINUS_Y_TO_Y_AROUND_Z,
            AXIS_TRANSLATION_Z_TO_Y,
            AXIS_TRANSLATION_MINUS_Z_TO_Y,
        ),
    ) = property_group_enum(
        ("AUTO", "Auto", "", "NONE", 0),
        ("NONE", "None", "", "NONE", 1),
        ("X_TO_Y", "X,Y to Y,-X", "", "NONE", 2),
        ("MINUS_X_TO_Y", "X,Y to -Y,X", "", "NONE", 3),
        ("MINUS_Y_TO_Y_AROUND_Z", "X,Y to -X,-Y", "", "NONE", 4),
        ("Z_TO_Y", "Y,Z to -Z,Y", "", "NONE", 5),
        ("MINUS_Z_TO_Y", "Y,Z to Z,-Y", "", "NONE", 6),
    )

    @classmethod
    def reverse_axis_translation(cls, axis_translation: str) -> str:
        return {
            cls.AXIS_TRANSLATION_AUTO.identifier: cls.AXIS_TRANSLATION_AUTO,
            cls.AXIS_TRANSLATION_NONE.identifier: cls.AXIS_TRANSLATION_NONE,
            cls.AXIS_TRANSLATION_X_TO_Y.identifier: (cls.AXIS_TRANSLATION_MINUS_X_TO_Y),
            cls.AXIS_TRANSLATION_MINUS_X_TO_Y.identifier: (cls.AXIS_TRANSLATION_X_TO_Y),
            cls.AXIS_TRANSLATION_Z_TO_Y.identifier: (cls.AXIS_TRANSLATION_MINUS_Z_TO_Y),
            cls.AXIS_TRANSLATION_MINUS_Z_TO_Y.identifier: (cls.AXIS_TRANSLATION_Z_TO_Y),
            cls.AXIS_TRANSLATION_MINUS_Y_TO_Y_AROUND_Z.identifier: (
                cls.AXIS_TRANSLATION_MINUS_Y_TO_Y_AROUND_Z
            ),
        }[axis_translation].identifier

    @classmethod
    def node_constraint_roll_axis_translation(
        cls, axis_translation: str, roll_axis: Optional[str]
    ) -> Optional[str]:
        if roll_axis is None:
            return None
        return {
            cls.AXIS_TRANSLATION_AUTO.identifier: {"X": "X", "Y": "Y", "Z": "Z"},
            cls.AXIS_TRANSLATION_NONE.identifier: {"X": "X", "Y": "Y", "Z": "Z"},
            cls.AXIS_TRANSLATION_X_TO_Y.identifier: {"X": "Y", "Y": "X", "Z": "Z"},
            cls.AXIS_TRANSLATION_MINUS_X_TO_Y.identifier: {
                "X": "Y",
                "Y": "X",
                "Z": "Z",
            },
            cls.AXIS_TRANSLATION_Z_TO_Y.identifier: {"X": "X", "Y": "Z", "Z": "Y"},
            cls.AXIS_TRANSLATION_MINUS_Z_TO_Y.identifier: {
                "X": "X",
                "Y": "Z",
                "Z": "Y",
            },
            cls.AXIS_TRANSLATION_MINUS_Y_TO_Y_AROUND_Z.identifier: {
                "X": "X",
                "Y": "Y",
                "Z": "Z",
            },
        }[axis_translation][roll_axis]

    @classmethod
    def node_constraint_aim_axis_translation(
        cls, axis_translation: str, aim_axis: Optional[str]
    ) -> Optional[str]:
        if aim_axis is None:
            return None
        return {
            cls.AXIS_TRANSLATION_AUTO.identifier: {
                "PositiveX": "PositiveX",
                "PositiveY": "PositiveY",
                "PositiveZ": "PositiveZ",
                "NegativeX": "NegativeX",
                "NegativeY": "NegativeY",
                "NegativeZ": "NegativeZ",
            },
            cls.AXIS_TRANSLATION_NONE.identifier: {
                "PositiveX": "PositiveX",
                "PositiveY": "PositiveY",
                "PositiveZ": "PositiveZ",
                "NegativeX": "NegativeX",
                "NegativeY": "NegativeY",
                "NegativeZ": "NegativeZ",
            },
            cls.AXIS_TRANSLATION_X_TO_Y.identifier: {
                "PositiveX": "PositiveY",
                "PositiveY": "NegativeX",
                "PositiveZ": "PositiveZ",
                "NegativeX": "NegativeY",
                "NegativeY": "PositiveX",
                "NegativeZ": "NegativeZ",
            },
            cls.AXIS_TRANSLATION_MINUS_X_TO_Y.identifier: {
                "PositiveY": "PositiveX",
                "NegativeX": "PositiveY",
                "PositiveZ": "PositiveZ",
                "NegativeY": "NegativeX",
                "PositiveX": "NegativeY",
                "NegativeZ": "NegativeZ",
            },
            cls.AXIS_TRANSLATION_Z_TO_Y.identifier: {
                "PositiveX": "PositiveX",
                "PositiveY": "NegativeZ",
                "PositiveZ": "PositiveY",
                "NegativeX": "NegativeX",
                "NegativeY": "PositiveZ",
                "NegativeZ": "NegativeY",
            },
            cls.AXIS_TRANSLATION_MINUS_Z_TO_Y.identifier: {
                "PositiveX": "PositiveX",
                "NegativeZ": "PositiveY",
                "PositiveY": "PositiveZ",
                "NegativeX": "NegativeX",
                "PositiveZ": "NegativeY",
                "NegativeY": "NegativeZ",
            },
            cls.AXIS_TRANSLATION_MINUS_Y_TO_Y_AROUND_Z.identifier: {
                "PositiveX": "NegativeX",
                "PositiveY": "NegativeY",
                "PositiveZ": "PositiveZ",
                "NegativeX": "PositiveX",
                "NegativeY": "PositiveY",
                "NegativeZ": "NegativeZ",
            },
        }[axis_translation][aim_axis]

    @classmethod
    def translate_axis(cls, matrix: Matrix, axis_translation: str) -> Matrix:
        location, rotation, scale = matrix.decompose()

        if axis_translation == cls.AXIS_TRANSLATION_X_TO_Y.identifier:
            rotation @= Quaternion((0, 0, 1), -math.pi / 2)
        elif axis_translation == cls.AXIS_TRANSLATION_MINUS_X_TO_Y.identifier:
            rotation @= Quaternion((0, 0, 1), math.pi / 2)
        elif axis_translation == cls.AXIS_TRANSLATION_MINUS_Y_TO_Y_AROUND_Z.identifier:
            rotation @= Quaternion((0, 0, 1), math.pi)
        elif axis_translation == cls.AXIS_TRANSLATION_Z_TO_Y.identifier:
            rotation @= Quaternion((1, 0, 0), math.pi / 2)
        elif axis_translation == cls.AXIS_TRANSLATION_MINUS_Z_TO_Y.identifier:
            rotation @= Quaternion((1, 0, 0), -math.pi / 2)

        # return Matrix.LocRotScale(location, rotation, scale)
        return (
            Matrix.Translation(location)
            @ rotation.to_matrix().to_4x4()
            @ Matrix.Diagonal(scale).to_4x4()
        )

    axis_translation: EnumProperty(  # type: ignore[valid-type]
        items=axis_translation_enum.items(),
        name="Axis Translation on Export",
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        uuid: str  # type: ignore[no-redef]
        axis_translation: str  # type: ignore[no-redef]


class VrmAddonObjectExtensionPropertyGroup(PropertyGroup):
    axis_translation: EnumProperty(  # type: ignore[valid-type]
        items=VrmAddonBoneExtensionPropertyGroup.axis_translation_enum.items(),
        name="Axis Translation on Export",
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        axis_translation: str  # type: ignore[no-redef]


class VrmAddonArmatureExtensionPropertyGroup(PropertyGroup):
    INITIAL_ADDON_VERSION = VrmAddonPreferences.INITIAL_ADDON_VERSION

    addon_version: IntVectorProperty(  # type: ignore[valid-type]
        size=3,
        default=INITIAL_ADDON_VERSION,
    )

    vrm0: PointerProperty(  # type: ignore[valid-type]
        type=Vrm0PropertyGroup
    )

    vrm1: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1PropertyGroup
    )

    spring_bone1: PointerProperty(  # type: ignore[valid-type]
        type=SpringBone1SpringBonePropertyGroup
    )

    node_constraint1: PointerProperty(  # type: ignore[valid-type]
        type=NodeConstraint1NodeConstraintPropertyGroup
    )

    khr_character: PointerProperty(  # type: ignore[valid-type]
        type=KhrCharacterPropertyGroup
    )

    SPEC_VERSION_VRM0 = "0.0"
    SPEC_VERSION_VRM1 = "1.0"
    SPEC_VERSION_KHR_CHARACTER = "KHR_character"
    spec_version_items = (
        (SPEC_VERSION_VRM0, "VRM 0.0", "", "NONE", 0),
        (SPEC_VERSION_VRM1, "VRM 1.0", "", "NONE", 1),
        *(
            [
                (
                    SPEC_VERSION_KHR_CHARACTER,
                    "KHR Character (Experimental)",
                    "",
                    "EXPERIMENTAL",
                    2,
                )
            ]
            if bpy.app.version >= (4, 5)
            else []
        ),
    )

    def update_spec_version(self, _context: Context) -> None:
        for blend_shape_group in self.vrm0.blend_shape_master.blend_shape_groups:
            blend_shape_group.preview = 0

        if self.spec_version == self.SPEC_VERSION_VRM0:
            vrm0_hidden = False
            vrm1_hidden = True
        elif self.spec_version == self.SPEC_VERSION_VRM1:
            vrm0_hidden = True
            vrm1_hidden = False
        else:
            return

        for vrm0_collider in [
            collider.bpy_object
            for collider_group in self.vrm0.secondary_animation.collider_groups
            for collider in collider_group.colliders
            if collider.bpy_object
        ]:
            vrm0_collider.hide_set(vrm0_hidden)

        for vrm1_collider in [
            collider.bpy_object
            for collider in self.spring_bone1.colliders
            if collider.bpy_object
        ]:
            vrm1_collider.hide_set(vrm1_hidden)
            for child in vrm1_collider.children:
                child.hide_set(vrm1_hidden)

    spec_version: EnumProperty(  # type: ignore[valid-type]
        items=spec_version_items,
        name="Spec Version",
        update=update_spec_version,
        default=SPEC_VERSION_VRM1,
    )

    def is_vrm0(self) -> bool:
        return str(self.spec_version) == self.SPEC_VERSION_VRM0

    def is_vrm1(self) -> bool:
        return str(self.spec_version) == self.SPEC_VERSION_VRM1

    def is_khr_character(self) -> bool:
        return str(self.spec_version) == self.SPEC_VERSION_KHR_CHARACTER

    @staticmethod
    def has_vrm_model_metadata(obj: Object) -> bool:
        if obj.type != "ARMATURE":
            return False
        armature = obj.data
        if not isinstance(armature, Armature):
            return False

        # https://github.com/saturday06/VRM-Addon-for-Blender/blob/2_0_3/io_scene_vrm/editor/migration.py#L372-L373
        ext = get_armature_extension(armature)
        if tuple(ext.addon_version) > (2, 0, 1):
            return True

        # https://github.com/saturday06/VRM-Addon-for-Blender/blob/0_79/importer/model_build.py#L731
        humanoid_params_key = obj.get("humanoid_params")
        if not isinstance(humanoid_params_key, str):
            return False

        # https://github.com/saturday06/VRM-Addon-for-Blender/blob/0_79/importer/model_build.py#L706
        return "hips" in armature

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        addon_version: Sequence[int]  # type: ignore[no-redef]
        vrm0: Vrm0PropertyGroup  # type: ignore[no-redef]
        vrm1: Vrm1PropertyGroup  # type: ignore[no-redef]
        spring_bone1: SpringBone1SpringBonePropertyGroup  # type: ignore[no-redef]
        node_constraint1: (  # type: ignore[no-redef]
            NodeConstraint1NodeConstraintPropertyGroup
        )
        khr_character: KhrCharacterPropertyGroup  # type: ignore[no-redef]
        spec_version: str  # type: ignore[no-redef]


def update_internal_cache(context: Context) -> None:
    for armature in context.blend_data.armatures:
        Vrm0HumanoidPropertyGroup.update_all_node_candidates(context, armature.name)
        Vrm1HumanBonesPropertyGroup.update_all_node_candidates(context, armature.name)
    VrmAddonSceneExtensionPropertyGroup.update_vrm0_material_property_names(context)


class VrmAddonMaterialExtensionPropertyGroup(PropertyGroup):
    mtoon1: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MaterialPropertyGroup
    )
    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        mtoon1: Mtoon1MaterialPropertyGroup  # type: ignore[no-redef]


class VrmAddonNodeTreeExtensionPropertyGroup(PropertyGroup):
    INITIAL_ADDON_VERSION = VrmAddonPreferences.INITIAL_ADDON_VERSION

    addon_version: IntVectorProperty(  # type: ignore[valid-type]
        size=3,
        default=INITIAL_ADDON_VERSION,
    )
    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        addon_version: Sequence[int]  # type: ignore[no-redef]


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
) -> VrmAddonMaterialExtensionPropertyGroup:
    return get_vrm_addon_extension_or_raise(
        material, VrmAddonMaterialExtensionPropertyGroup
    )


def get_armature_extension(
    armature: Armature,
) -> VrmAddonArmatureExtensionPropertyGroup:
    return get_vrm_addon_extension_or_raise(
        armature, VrmAddonArmatureExtensionPropertyGroup
    )


def get_node_tree_extension(
    node_tree: NodeTree,
) -> VrmAddonNodeTreeExtensionPropertyGroup:
    return get_vrm_addon_extension_or_raise(
        node_tree, VrmAddonNodeTreeExtensionPropertyGroup
    )


def get_scene_extension(scene: Scene) -> VrmAddonSceneExtensionPropertyGroup:
    return get_vrm_addon_extension_or_raise(scene, VrmAddonSceneExtensionPropertyGroup)


def get_bone_extension(bone: Bone) -> VrmAddonBoneExtensionPropertyGroup:
    return get_vrm_addon_extension_or_raise(bone, VrmAddonBoneExtensionPropertyGroup)


def get_object_extension(obj: Object) -> VrmAddonObjectExtensionPropertyGroup:
    return get_vrm_addon_extension_or_raise(obj, VrmAddonObjectExtensionPropertyGroup)
