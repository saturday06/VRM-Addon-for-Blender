import functools
import math
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

import bpy
from bpy.props import (
    CollectionProperty,
    EnumProperty,
    IntVectorProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import Context, PropertyGroup
from mathutils import Matrix, Quaternion

from ..common.logging import get_logger
from ..common.preferences import VrmAddonPreferences
from .mtoon1.property_group import Mtoon1MaterialPropertyGroup
from .node_constraint1.property_group import NodeConstraint1NodeConstraintPropertyGroup
from .property_group import StringPropertyGroup
from .spring_bone1.property_group import SpringBone1SpringBonePropertyGroup
from .vrm0.property_group import Vrm0HumanoidPropertyGroup, Vrm0PropertyGroup
from .vrm1.property_group import Vrm1HumanBonesPropertyGroup, Vrm1PropertyGroup

if TYPE_CHECKING:
    from .property_group import CollectionPropertyProtocol

logger = get_logger(__name__)


class VrmAddonSceneExtensionPropertyGroup(PropertyGroup):
    mesh_object_names: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )

    @staticmethod
    def check_mesh_object_names_and_update(
        scene_name: str,
        defer: bool = True,
    ) -> None:
        scene = bpy.data.scenes.get(scene_name)
        if not scene:
            logger.error(f'No scene "{scene_name}"')
            return
        ext = scene.vrm_addon_extension

        mesh_object_names = [obj.name for obj in bpy.data.objects if obj.type == "MESH"]
        up_to_date = mesh_object_names == [str(n.value) for n in ext.mesh_object_names]

        if up_to_date:
            return

        if defer:
            bpy.app.timers.register(
                functools.partial(
                    VrmAddonSceneExtensionPropertyGroup.check_mesh_object_names_and_update,
                    scene_name,
                    False,
                )
            )
            return

        ext.mesh_object_names.clear()
        for mesh_object_name in mesh_object_names:
            n = ext.mesh_object_names.add()
            n.value = mesh_object_name

    vrm0_material_gltf_property_names: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )

    vrm0_material_mtoon0_property_names: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )

    @staticmethod
    def update_vrm0_material_property_names(scene_name: str) -> None:
        scene = bpy.data.scenes.get(scene_name)
        if not scene:
            logger.error(f'No scene "{scene_name}"')
            return
        ext = scene.vrm_addon_extension

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

        if gltf_property_names != [
            str(n.value) for n in ext.vrm0_material_gltf_property_names
        ]:
            ext.vrm0_material_gltf_property_names.clear()
            for gltf_property_name in gltf_property_names:
                n = ext.vrm0_material_gltf_property_names.add()
                n.value = gltf_property_name

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

        if mtoon0_property_names != [
            str(n.value) for n in ext.vrm0_material_mtoon0_property_names
        ]:
            ext.vrm0_material_mtoon0_property_names.clear()
            for mtoon0_property_name in mtoon0_property_names:
                n = ext.vrm0_material_mtoon0_property_names.add()
                n.value = mtoon0_property_name

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run python tools/property_typing.py`
        mesh_object_names: CollectionPropertyProtocol[StringPropertyGroup]  # type: ignore[no-redef]
        vrm0_material_gltf_property_names: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]
        vrm0_material_mtoon0_property_names: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]


class VrmAddonBoneExtensionPropertyGroup(PropertyGroup):
    uuid: StringProperty()  # type: ignore[valid-type]

    AXIS_TRANSLATION_AUTO_ID = "AUTO"
    AXIS_TRANSLATION_NONE_ID = "NONE"
    AXIS_TRANSLATION_X_TO_Y_ID = "X_TO_Y"
    AXIS_TRANSLATION_MINUS_X_TO_Y_ID = "MINUS_X_TO_Y"
    AXIS_TRANSLATION_Z_TO_Y_ID = "Z_TO_Y"
    AXIS_TRANSLATION_MINUS_Z_TO_Y_ID = "MINUS_Z_TO_Y"
    AXIS_TRANSLATION_MINUS_Y_TO_Y_AROUND_Z_ID = "MINUS_Y_TO_Y_AROUND_Z"

    @classmethod
    def reverse_axis_translation(cls, axis_translation: str) -> str:
        return {
            cls.AXIS_TRANSLATION_AUTO_ID: cls.AXIS_TRANSLATION_AUTO_ID,
            cls.AXIS_TRANSLATION_NONE_ID: cls.AXIS_TRANSLATION_NONE_ID,
            cls.AXIS_TRANSLATION_X_TO_Y_ID: cls.AXIS_TRANSLATION_MINUS_X_TO_Y_ID,
            cls.AXIS_TRANSLATION_MINUS_X_TO_Y_ID: cls.AXIS_TRANSLATION_X_TO_Y_ID,
            cls.AXIS_TRANSLATION_Z_TO_Y_ID: cls.AXIS_TRANSLATION_MINUS_Z_TO_Y_ID,
            cls.AXIS_TRANSLATION_MINUS_Z_TO_Y_ID: cls.AXIS_TRANSLATION_Z_TO_Y_ID,
            cls.AXIS_TRANSLATION_MINUS_Y_TO_Y_AROUND_Z_ID: (
                cls.AXIS_TRANSLATION_MINUS_Y_TO_Y_AROUND_Z_ID
            ),
        }[axis_translation]

    @classmethod
    def node_constraint_roll_axis_translation(
        cls, axis_translation: str, roll_axis: Optional[str]
    ) -> Optional[str]:
        if roll_axis is None:
            return None
        return {
            cls.AXIS_TRANSLATION_AUTO_ID: {"X": "X", "Y": "Y", "Z": "Z"},
            cls.AXIS_TRANSLATION_NONE_ID: {"X": "X", "Y": "Y", "Z": "Z"},
            cls.AXIS_TRANSLATION_X_TO_Y_ID: {"X": "Y", "Y": "X", "Z": "Z"},
            cls.AXIS_TRANSLATION_MINUS_X_TO_Y_ID: {"X": "Y", "Y": "X", "Z": "Z"},
            cls.AXIS_TRANSLATION_Z_TO_Y_ID: {"X": "X", "Y": "Z", "Z": "Y"},
            cls.AXIS_TRANSLATION_MINUS_Z_TO_Y_ID: {"X": "X", "Y": "Z", "Z": "Y"},
            cls.AXIS_TRANSLATION_MINUS_Y_TO_Y_AROUND_Z_ID: {
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
            cls.AXIS_TRANSLATION_AUTO_ID: {
                "PositiveX": "PositiveX",
                "PositiveY": "PositiveY",
                "PositiveZ": "PositiveZ",
                "NegativeX": "NegativeX",
                "NegativeY": "NegativeY",
                "NegativeZ": "NegativeZ",
            },
            cls.AXIS_TRANSLATION_NONE_ID: {
                "PositiveX": "PositiveX",
                "PositiveY": "PositiveY",
                "PositiveZ": "PositiveZ",
                "NegativeX": "NegativeX",
                "NegativeY": "NegativeY",
                "NegativeZ": "NegativeZ",
            },
            cls.AXIS_TRANSLATION_X_TO_Y_ID: {
                "PositiveX": "PositiveY",
                "PositiveY": "NegativeX",
                "PositiveZ": "PositiveZ",
                "NegativeX": "NegativeY",
                "NegativeY": "PositiveX",
                "NegativeZ": "NegativeZ",
            },
            cls.AXIS_TRANSLATION_MINUS_X_TO_Y_ID: {
                "PositiveY": "PositiveX",
                "NegativeX": "PositiveY",
                "PositiveZ": "PositiveZ",
                "NegativeY": "NegativeX",
                "PositiveX": "NegativeY",
                "NegativeZ": "NegativeZ",
            },
            cls.AXIS_TRANSLATION_Z_TO_Y_ID: {
                "PositiveX": "PositiveX",
                "PositiveY": "NegativeZ",
                "PositiveZ": "PositiveY",
                "NegativeX": "NegativeX",
                "NegativeY": "PositiveZ",
                "NegativeZ": "NegativeY",
            },
            cls.AXIS_TRANSLATION_MINUS_Z_TO_Y_ID: {
                "PositiveX": "PositiveX",
                "NegativeZ": "PositiveY",
                "PositiveY": "PositiveZ",
                "NegativeX": "NegativeX",
                "PositiveZ": "NegativeY",
                "NegativeY": "NegativeZ",
            },
            cls.AXIS_TRANSLATION_MINUS_Y_TO_Y_AROUND_Z_ID: {
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

        if axis_translation == cls.AXIS_TRANSLATION_X_TO_Y_ID:
            rotation @= Quaternion((0, 0, 1), -math.pi / 2)
        elif axis_translation == cls.AXIS_TRANSLATION_MINUS_X_TO_Y_ID:
            rotation @= Quaternion((0, 0, 1), math.pi / 2)
        elif axis_translation == cls.AXIS_TRANSLATION_MINUS_Y_TO_Y_AROUND_Z_ID:
            rotation @= Quaternion((0, 0, 1), math.pi)
        elif axis_translation == cls.AXIS_TRANSLATION_Z_TO_Y_ID:
            rotation @= Quaternion((1, 0, 0), math.pi / 2)
        elif axis_translation == cls.AXIS_TRANSLATION_MINUS_Z_TO_Y_ID:
            rotation @= Quaternion((1, 0, 0), -math.pi / 2)

        # return Matrix.LocRotScale(location, rotation, scale)
        return (
            Matrix.Translation(location)
            @ rotation.to_matrix().to_4x4()
            @ Matrix.Diagonal(scale).to_4x4()
        )

    axis_translation_items = (
        (AXIS_TRANSLATION_AUTO_ID, "Auto", "", "NONE", 0),
        (AXIS_TRANSLATION_NONE_ID, "None", "", "NONE", 1),
        (AXIS_TRANSLATION_X_TO_Y_ID, "X,Y to Y,-X", "", "NONE", 2),
        (AXIS_TRANSLATION_MINUS_X_TO_Y_ID, "X,Y to -Y,X", "", "NONE", 3),
        (AXIS_TRANSLATION_MINUS_Y_TO_Y_AROUND_Z_ID, "X,Y to -X,-Y", "", "NONE", 4),
        (AXIS_TRANSLATION_Z_TO_Y_ID, "Y,Z to -Z,Y", "", "NONE", 5),
        (AXIS_TRANSLATION_MINUS_Z_TO_Y_ID, "Y,Z to Z,-Y", "", "NONE", 6),
    )

    axis_translation: EnumProperty(  # type: ignore[valid-type]
        items=axis_translation_items,
        name="Axis Translation on Export",
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run python tools/property_typing.py`
        uuid: str  # type: ignore[no-redef]
        axis_translation: str  # type: ignore[no-redef]


class VrmAddonObjectExtensionPropertyGroup(PropertyGroup):
    axis_translation: EnumProperty(  # type: ignore[valid-type]
        items=VrmAddonBoneExtensionPropertyGroup.axis_translation_items,
        name="Axis Translation on Export",
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run python tools/property_typing.py`
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

    armature_data_name: StringProperty()  # type: ignore[valid-type]

    SPEC_VERSION_VRM0 = "0.0"
    SPEC_VERSION_VRM1 = "1.0"
    spec_version_items = (
        (SPEC_VERSION_VRM0, "VRM 0.0", "", "NONE", 0),
        (SPEC_VERSION_VRM1, "VRM 1.0", "", "NONE", 1),
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
    )

    def is_vrm0(self) -> bool:
        return str(self.spec_version) == self.SPEC_VERSION_VRM0

    def is_vrm1(self) -> bool:
        return str(self.spec_version) == self.SPEC_VERSION_VRM1

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run python tools/property_typing.py`
        addon_version: Sequence[int]  # type: ignore[no-redef]
        vrm0: Vrm0PropertyGroup  # type: ignore[no-redef]
        vrm1: Vrm1PropertyGroup  # type: ignore[no-redef]
        spring_bone1: SpringBone1SpringBonePropertyGroup  # type: ignore[no-redef]
        node_constraint1: (  # type: ignore[no-redef]
            NodeConstraint1NodeConstraintPropertyGroup
        )
        armature_data_name: str  # type: ignore[no-redef]
        spec_version: str  # type: ignore[no-redef]


def update_internal_cache(context: Context) -> None:
    VrmAddonSceneExtensionPropertyGroup.check_mesh_object_names_and_update(
        context.scene.name,
        defer=False,
    )
    for armature in bpy.data.armatures:
        Vrm0HumanoidPropertyGroup.check_last_bone_names_and_update(
            armature.name, defer=False
        )
        Vrm1HumanBonesPropertyGroup.check_last_bone_names_and_update(
            armature.name, defer=False
        )
    VrmAddonSceneExtensionPropertyGroup.update_vrm0_material_property_names(
        context.scene.name
    )


class VrmAddonMaterialExtensionPropertyGroup(PropertyGroup):
    mtoon1: PointerProperty(  # type: ignore[valid-type]
        type=Mtoon1MaterialPropertyGroup
    )
    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run python tools/property_typing.py`
        mtoon1: Mtoon1MaterialPropertyGroup  # type: ignore[no-redef]
