# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import statistics
import uuid
from collections.abc import Sequence
from sys import float_info
from typing import TYPE_CHECKING, Callable, Optional

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import Armature, Context, Object, PropertyGroup
from mathutils import Matrix, Quaternion, Vector

from ...common import convert
from ...common.logger import get_logger
from ...common.rotation import (
    get_rotation_as_quaternion,
    set_rotation_without_mode_change,
)
from ..property_group import BonePropertyGroup, property_group_enum

if TYPE_CHECKING:
    from ..property_group import CollectionPropertyProtocol

logger = get_logger(__name__)


def find_armature_and_collider(
    context: Context,
    match_collider: Callable[["SpringBone1ColliderPropertyGroup"], bool],
) -> tuple[Object, "SpringBone1ColliderPropertyGroup"]:
    for obj in context.blend_data.objects:
        if obj.type != "ARMATURE":
            continue
        armature_data = obj.data
        if not isinstance(armature_data, Armature):
            continue
        for collider in get_armature_spring_bone1_extension(armature_data).colliders:
            if match_collider(collider):
                return (obj, collider)
    message = "No armature"
    raise ValueError(message)


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.shape.schema.json#L7-L27
class SpringBone1ColliderShapeSpherePropertyGroup(PropertyGroup):
    def find_armature_and_collider(
        self,
        context: Context,
    ) -> tuple[Object, "SpringBone1ColliderPropertyGroup"]:
        return find_armature_and_collider(
            context, lambda collider: collider.shape.sphere == self
        )

    def get_offset(self) -> tuple[float, float, float]:
        context = bpy.context

        armature, collider = self.find_armature_and_collider(context)
        if not collider.bpy_object:
            logger.error(
                'Failed to get bpy object of "%s" in sphere.get_offset()', collider.name
            )
            return (0, 0, 0)
        bone = armature.pose.bones.get(collider.node.bone_name)
        if bone:
            matrix = (
                bone.matrix.inverted()
                @ armature.matrix_world.inverted()
                @ collider.bpy_object.matrix_world
            )
        else:
            matrix = armature.matrix_world.inverted() @ collider.bpy_object.matrix_world
        return convert.float3_or(matrix.to_translation(), (0.0, 0.0, 0.0))

    def set_offset(self, offset: Sequence[float]) -> None:
        context = bpy.context

        armature, collider = self.find_armature_and_collider(context)
        collider.reset_bpy_object(context, armature)
        bone = armature.pose.bones.get(collider.node.bone_name)
        if not bone:
            if collider.bpy_object:
                collider.bpy_object.matrix_world = (
                    armature.matrix_world @ Matrix.Translation(offset)
                )
            return
        if collider.bpy_object:
            collider.bpy_object.matrix_world = (
                armature.matrix_world @ bone.matrix @ Matrix.Translation(offset)
            )

    def update_offset(self, _context: Context) -> None:
        self.fallback_offset = self.offset

    def get_radius(self) -> float:
        context = bpy.context

        _, collider = self.find_armature_and_collider(context)
        if not collider.bpy_object:
            logger.error(
                'Failed to get bpy object of "%s" in sphere.get_radius()', collider.name
            )
            return 0.0
        mean_scale = statistics.mean(
            abs(s) for s in collider.bpy_object.matrix_basis.to_scale()
        )
        empty_display_size: float = collider.bpy_object.empty_display_size
        return float(mean_scale) * empty_display_size

    def set_radius(self, v: float) -> None:
        context = bpy.context

        armature, collider = self.find_armature_and_collider(context)
        collider.reset_bpy_object(context, armature)
        if not collider.bpy_object:
            logger.error(
                'Failed to reset bpy object of "%s" in sphere.set_radius()',
                collider.name,
            )
            return
        location, rotation, _ = collider.bpy_object.matrix_basis.decompose()
        collider.bpy_object.matrix_basis = (
            Matrix.Translation(location) @ rotation.to_matrix().to_4x4()
        )
        collider.bpy_object.empty_display_size = v

    def update_radius(self, _context: Context) -> None:
        self.fallback_radius = self.radius

    offset: FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="TRANSLATION",
        unit="LENGTH",
        default=(0, 0, 0),
        get=get_offset,
        set=set_offset,
        update=update_offset,
    )

    radius: FloatProperty(  # type: ignore[valid-type]
        name="Radius",
        min=0.0,
        default=0.0,
        soft_max=1.0,
        unit="LENGTH",
        get=get_radius,
        set=set_radius,
        update=update_radius,
    )

    fallback_offset: FloatVectorProperty(  # type: ignore[valid-type]
        name="Fallback Sphere Offset",
        size=3,
        subtype="TRANSLATION",
        unit="LENGTH",
        default=(0, 0, 0),
    )

    fallback_radius: FloatProperty(  # type: ignore[valid-type]
        name="Fallback Sphere Radius",
        min=0.0,
        default=0.0,
        soft_max=1.0,
        unit="LENGTH",
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        offset: Sequence[float]  # type: ignore[no-redef]
        radius: float  # type: ignore[no-redef]
        fallback_offset: Sequence[float]  # type: ignore[no-redef]
        fallback_radius: float  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.shape.schema.json#L28-L58
class SpringBone1ColliderShapeCapsulePropertyGroup(PropertyGroup):
    def find_armature_and_collider(
        self,
        context: Context,
    ) -> tuple[Object, "SpringBone1ColliderPropertyGroup"]:
        return find_armature_and_collider(
            context, lambda collider: collider.shape.capsule == self
        )

    def get_offset(self) -> tuple[float, float, float]:
        context = bpy.context

        armature, collider = self.find_armature_and_collider(context)
        if not collider.bpy_object:
            logger.error(
                'Failed to get bpy object of "%s" in capsule.get_offset()',
                collider.name,
            )
            return (0, 0, 0)
        bone = armature.pose.bones.get(collider.node.bone_name)
        if bone:
            matrix = (
                bone.matrix.inverted()
                @ armature.matrix_world.inverted()
                @ collider.bpy_object.matrix_world
            )
        else:
            matrix = armature.matrix_world.inverted() @ collider.bpy_object.matrix_world
        return convert.float3_or(matrix.to_translation(), (0.0, 0.0, 0.0))

    def set_offset(self, offset: Sequence[float]) -> None:
        context = bpy.context

        armature, collider = self.find_armature_and_collider(context)
        collider.reset_bpy_object(context, armature)
        bone = armature.pose.bones.get(collider.node.bone_name)
        if not bone:
            if collider.bpy_object:
                collider.bpy_object.matrix_world = (
                    armature.matrix_world @ Matrix.Translation(offset)
                )
            return
        if collider.bpy_object:
            collider.bpy_object.matrix_world = (
                armature.matrix_world @ bone.matrix @ Matrix.Translation(offset)
            )

    def update_offset(self, _context: Context) -> None:
        self.fallback_offset = self.offset

    def get_tail(self) -> tuple[float, float, float]:
        context = bpy.context

        armature, collider = self.find_armature_and_collider(context)
        if not collider.bpy_object or not collider.bpy_object.children:
            logger.error(
                'Failed to get bpy object of "%s" in capsule.get_tail()', collider.name
            )
            return (0, 0, 0)
        bone = armature.pose.bones.get(collider.node.bone_name)
        if bone:
            matrix = (
                bone.matrix.inverted()
                @ armature.matrix_world.inverted()
                @ collider.bpy_object.children[0].matrix_world
            )
        else:
            matrix = (
                armature.matrix_world.inverted()
                @ collider.bpy_object.children[0].matrix_world
            )
        return convert.float3_or(matrix.to_translation(), (0.0, 0.0, 0.0))

    def set_tail(self, offset: Sequence[float]) -> None:
        context = bpy.context

        armature, collider = self.find_armature_and_collider(context)
        collider.reset_bpy_object(context, armature)
        bone = armature.pose.bones.get(collider.node.bone_name)
        if not bone:
            if collider.bpy_object:
                collider.bpy_object.children[0].matrix_world = (
                    armature.matrix_world @ Matrix.Translation(offset)
                )
            return
        if collider.bpy_object:
            if not collider.bpy_object.children:
                logger.error(
                    'Failed to set tail bpy object matrix of "%s"'
                    " in capsule.set_tail()",
                    collider.name,
                )
                return
            collider.bpy_object.children[0].matrix_world = (
                armature.matrix_world @ bone.matrix @ Matrix.Translation(offset)
            )

    def update_tail(self, _context: Context) -> None:
        self.fallback_tail = self.tail

    def get_radius(self) -> float:
        context = bpy.context

        _, collider = self.find_armature_and_collider(context)
        if not collider.bpy_object:
            logger.error(
                'Failed to get bpy object of "%s" in capsule.get_radius()',
                collider.name,
            )
            return 0.0
        mean_scale: float = statistics.mean(
            abs(s) for s in collider.bpy_object.matrix_basis.to_scale()
        )
        empty_display_size: float = collider.bpy_object.empty_display_size
        return mean_scale * empty_display_size

    def set_radius(self, v: float) -> None:
        context = bpy.context

        armature, collider = self.find_armature_and_collider(context)
        collider.reset_bpy_object(context, armature)
        if not collider.bpy_object:
            logger.error(
                'Failed to reset bpy object of "%s" in capsule.set_radius()',
                collider.name,
            )
            return
        location, rotation, _ = collider.bpy_object.matrix_basis.decompose()
        collider.bpy_object.matrix_basis = (
            Matrix.Translation(location) @ rotation.to_matrix().to_4x4()
        )
        collider.bpy_object.empty_display_size = v
        if not collider.bpy_object.children:
            logger.error(
                'Failed to set tail bpy object size of "%s" in capsule.set_radius()',
                collider.name,
            )
            return
        collider.bpy_object.children[0].empty_display_size = v

    def update_radius(self, _context: Context) -> None:
        self.fallback_radius = self.radius

    offset: FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="TRANSLATION",
        unit="LENGTH",
        default=(0, 0, 0),
        get=get_offset,
        set=set_offset,
        update=update_offset,
    )

    radius: FloatProperty(  # type: ignore[valid-type]
        name="Radius",
        min=0.0,
        default=0.0,
        soft_max=1.0,
        unit="LENGTH",
        get=get_radius,
        set=set_radius,
        update=update_radius,
    )

    tail: FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="TRANSLATION",
        unit="LENGTH",
        default=(0, 0, 0),
        get=get_tail,
        set=set_tail,
        update=update_tail,
    )

    fallback_offset: FloatVectorProperty(  # type: ignore[valid-type]
        name="Fallback Capsule Head",
        size=3,
        subtype="TRANSLATION",
        unit="LENGTH",
        default=(0, 0, 0),
    )

    fallback_radius: FloatProperty(  # type: ignore[valid-type]
        name="Fallback Capsule Radius",
        min=0.0,
        default=0.0,
        soft_max=1.0,
        unit="LENGTH",
    )

    fallback_tail: FloatVectorProperty(  # type: ignore[valid-type]
        name="Fallback Capsule Tail",
        size=3,
        subtype="TRANSLATION",
        unit="LENGTH",
        default=(0, 0, 0),
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        offset: Sequence[float]  # type: ignore[no-redef]
        radius: float  # type: ignore[no-redef]
        tail: Sequence[float]  # type: ignore[no-redef]
        fallback_offset: Sequence[float]  # type: ignore[no-redef]
        fallback_radius: float  # type: ignore[no-redef]
        fallback_tail: Sequence[float]  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/9e8c886a2043639a3c166eb7cc93526be6313147/specification/VRMC_springBone_extended_collider-1.0/schema/VRMC_springBone_extended_collider.shape.schema.json#L9
class SpringBone1ExtendedColliderShapeSpherePropertyGroup(
    SpringBone1ColliderShapeSpherePropertyGroup
):
    def find_armature_and_collider(
        self,
        context: Context,
    ) -> tuple[Object, "SpringBone1ColliderPropertyGroup"]:
        return find_armature_and_collider(
            context,
            lambda collider: (
                collider.extensions.vrmc_spring_bone_extended_collider.shape.sphere
                == self
            ),
        )

    inside: BoolProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        inside: bool  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/9e8c886a2043639a3c166eb7cc93526be6313147/specification/VRMC_springBone_extended_collider-1.0/schema/VRMC_springBone_extended_collider.shape.schema.json#L36
class SpringBone1ExtendedColliderShapeCapsulePropertyGroup(
    SpringBone1ColliderShapeCapsulePropertyGroup
):
    def find_armature_and_collider(
        self,
        context: Context,
    ) -> tuple[Object, "SpringBone1ColliderPropertyGroup"]:
        return find_armature_and_collider(
            context,
            lambda collider: (
                collider.extensions.vrmc_spring_bone_extended_collider.shape.capsule
                == self
            ),
        )

    inside: BoolProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        inside: bool  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/9e8c886a2043639a3c166eb7cc93526be6313147/specification/VRMC_springBone_extended_collider-1.0/schema/VRMC_springBone_extended_collider.shape.schema.json#L73
class SpringBone1ExtendedColliderShapePlanePropertyGroup(PropertyGroup):
    def find_armature_and_collider(
        self,
        context: Context,
    ) -> tuple[Object, "SpringBone1ColliderPropertyGroup"]:
        return find_armature_and_collider(
            context,
            lambda collider: (
                collider.extensions.vrmc_spring_bone_extended_collider.shape.plane
                == self
            ),
        )

    def get_offset(self) -> tuple[float, float, float]:
        context = bpy.context

        armature, collider = self.find_armature_and_collider(context)
        if not collider.bpy_object:
            logger.error(
                'Failed to get bpy object of "%s" in extended_collider.get_offset()',
                collider.name,
            )
            return (0, 0, 0)
        bone = armature.pose.bones.get(collider.node.bone_name)
        if bone:
            matrix = (
                bone.matrix.inverted()
                @ armature.matrix_world.inverted()
                @ collider.bpy_object.matrix_world
            )
        else:
            matrix = armature.matrix_world.inverted() @ collider.bpy_object.matrix_world
        return convert.float3_or(matrix.to_translation(), (0.0, 0.0, 0.0))

    def set_offset(self, offset: Sequence[float]) -> None:
        context = bpy.context

        armature, collider = self.find_armature_and_collider(context)
        collider.reset_bpy_object(context, armature)
        bone = armature.pose.bones.get(collider.node.bone_name)
        if not bone:
            if collider.bpy_object:
                collider.bpy_object.matrix_world = (
                    armature.matrix_world @ Matrix.Translation(offset)
                )
            return
        if collider.bpy_object:
            collider.bpy_object.matrix_world = (
                armature.matrix_world @ bone.matrix @ Matrix.Translation(offset)
            )

    def get_normal(self) -> tuple[float, float, float]:
        context = bpy.context

        _, collider = self.find_armature_and_collider(context)
        bpy_object = collider.bpy_object
        if not bpy_object:
            return (0.0, 1.0, 0.0)

        result = Vector((0.0, 1.0, 0.0))
        result.rotate(get_rotation_as_quaternion(bpy_object))

        return (
            # use tuple initializer to make type checkers happy
            result.x,
            result.y,
            result.z,
        )

    def set_normal(self, normal: Sequence[float]) -> None:
        context = bpy.context

        armature, collider = self.find_armature_and_collider(context)
        collider.reset_bpy_object(context, armature)

        y_up_vec = Vector((0.0, 1.0, 0.0))
        normal_vec = Vector(normal)
        if normal_vec.length_squared > 0:
            rotation = y_up_vec.rotation_difference(normal_vec)
        else:
            rotation = Quaternion()

        bpy_object = collider.bpy_object
        if bpy_object:
            set_rotation_without_mode_change(bpy_object, rotation)

    offset: FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="TRANSLATION",
        unit="LENGTH",
        default=(0, 0, 0),
        get=get_offset,
        set=set_offset,
    )

    normal: FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        default=(0, 0, 1),
        get=get_normal,
        set=set_normal,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        offset: Sequence[float]  # type: ignore[no-redef]
        normal: Sequence[float]  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.shape.schema.json
class SpringBone1ColliderShapePropertyGroup(PropertyGroup):
    sphere: PointerProperty(  # type: ignore[valid-type]
        type=SpringBone1ColliderShapeSpherePropertyGroup
    )
    capsule: PointerProperty(  # type: ignore[valid-type]
        type=SpringBone1ColliderShapeCapsulePropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        sphere: SpringBone1ColliderShapeSpherePropertyGroup  # type: ignore[no-redef]
        capsule: SpringBone1ColliderShapeCapsulePropertyGroup  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/9e8c886a2043639a3c166eb7cc93526be6313147/specification/VRMC_springBone_extended_collider-1.0/schema/VRMC_springBone_extended_collider.shape.schema.json
class SpringBone1ExtendedColliderShapePropertyGroup(PropertyGroup):
    sphere: PointerProperty(  # type: ignore[valid-type]
        type=SpringBone1ExtendedColliderShapeSpherePropertyGroup
    )
    capsule: PointerProperty(  # type: ignore[valid-type]
        type=SpringBone1ExtendedColliderShapeCapsulePropertyGroup
    )
    plane: PointerProperty(  # type: ignore[valid-type]
        type=SpringBone1ExtendedColliderShapePlanePropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        sphere: (  # type: ignore[no-redef]
            SpringBone1ExtendedColliderShapeSpherePropertyGroup
        )
        capsule: (  # type: ignore[no-redef]
            SpringBone1ExtendedColliderShapeCapsulePropertyGroup
        )
        plane: (  # type: ignore[no-redef]
            SpringBone1ExtendedColliderShapePlanePropertyGroup
        )


# https://github.com/vrm-c/vrm-specification/blob/9e8c886a2043639a3c166eb7cc93526be6313147/specification/VRMC_springBone_extended_collider-1.0/schema/VRMC_springBone_extended_collider.schema.json
class SpringBone1VrmcSpringBoneExtendedColliderPropertyGroup(PropertyGroup):
    def update_shape_type(self, context: Context) -> None:
        armature, collider = find_armature_and_collider(
            context,
            lambda collider: (
                collider.extensions.vrmc_spring_bone_extended_collider == self
            ),
        )
        collider.reset_bpy_object(context, armature)

    enabled: BoolProperty(  # type: ignore[valid-type]
        name="Extended Collider",
        update=update_shape_type,
    )

    automatic_fallback_generation: BoolProperty(  # type: ignore[valid-type]
        name="Automatic Fallback Generation",
        default=True,
    )

    shape: PointerProperty(  # type: ignore[valid-type]
        type=SpringBone1ExtendedColliderShapePropertyGroup
    )

    (
        shape_type_enum,
        (
            SHAPE_TYPE_EXTENDED_SPHERE,
            SHAPE_TYPE_EXTENDED_CAPSULE,
            SHAPE_TYPE_EXTENDED_PLANE,
        ),
    ) = property_group_enum(
        ("extendedSphere", "Sphere", "", "NONE", 0),
        ("extendedCapsule", "Capsule", "", "NONE", 1),
        ("extendedPlane", "Plane", "", "NONE", 2),
    )

    shape_type: EnumProperty(  # type: ignore[valid-type]
        items=shape_type_enum.items(),
        name="Shape",
        update=update_shape_type,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        enabled: bool  # type: ignore[no-redef]
        automatic_fallback_generation: bool  # type: ignore[no-redef]
        shape: SpringBone1ExtendedColliderShapePropertyGroup  # type: ignore[no-redef]
        shape_type: str  # type: ignore[no-redef]


class SpringBone1ColliderExtensionsPropertyGroup(PropertyGroup):
    vrmc_spring_bone_extended_collider: PointerProperty(  # type: ignore[valid-type]
        type=SpringBone1VrmcSpringBoneExtendedColliderPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        vrmc_spring_bone_extended_collider: (  # type: ignore[no-redef]
            SpringBone1VrmcSpringBoneExtendedColliderPropertyGroup
        )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.collider.schema.json
class SpringBone1ColliderPropertyGroup(PropertyGroup):
    def broadcast_bpy_object_name(self, context: Context) -> None:
        if not self.bpy_object or not self.bpy_object.name:
            self.name = ""
            return
        if self.name == self.bpy_object.name:
            return
        self.name = self.bpy_object.name

        self.search_one_time_uuid = uuid.uuid4().hex
        for armature in context.blend_data.armatures:
            if not hasattr(armature, "vrm_addon_extension"):
                continue

            spring_bone = get_armature_spring_bone1_extension(armature)

            for collider in spring_bone.colliders:
                if collider.search_one_time_uuid != self.search_one_time_uuid:
                    continue

                for collider_group in spring_bone.collider_groups:
                    for collider_reference in collider_group.colliders:
                        if self.uuid != collider_reference.collider_uuid:
                            continue
                        collider_reference.collider_name = self.name

                return

    node: PointerProperty(type=BonePropertyGroup)  # type: ignore[valid-type]
    shape: PointerProperty(type=SpringBone1ColliderShapePropertyGroup)  # type: ignore[valid-type]
    extensions: PointerProperty(type=SpringBone1ColliderExtensionsPropertyGroup)  # type: ignore[valid-type]

    # for UI
    show_expanded: BoolProperty()  # type: ignore[valid-type]

    (
        shape_type_enum,
        (
            SHAPE_TYPE_SPHERE,
            SHAPE_TYPE_CAPSULE,
        ),
    ) = property_group_enum(
        ("Sphere", "Sphere", "", "NONE", 0),
        ("Capsule", "Capsule", "", "NONE", 1),
    )

    (
        ui_collider_type_enum,
        (
            UI_COLLIDER_TYPE_SPHERE,
            UI_COLLIDER_TYPE_CAPSULE,
            UI_COLLIDER_TYPE_PLANE,
            UI_COLLIDER_TYPE_SPHERE_INSIDE,
            UI_COLLIDER_TYPE_CAPSULE_INSIDE,
        ),
    ) = property_group_enum(
        ("uiColliderTypeSphere", "Sphere", "", "NONE", 0),
        ("uiColliderTypeCapsule", "Capsule", "", "NONE", 1),
        ("uiColliderTypePlane", "Plane", "", "NONE", 2),
        ("uiColliderTypeSphereInside", "Sphere Inside", "", "NONE", 3),
        ("uiColliderTypeCapsuleInside", "Capsule Inside", "", "NONE", 4),
    )

    def get_ui_collider_type(self) -> int:
        extended = self.extensions.vrmc_spring_bone_extended_collider
        if not extended.enabled:
            if self.shape_type == self.SHAPE_TYPE_SPHERE.identifier:
                return self.UI_COLLIDER_TYPE_SPHERE.value
            if self.shape_type == self.SHAPE_TYPE_CAPSULE.identifier:
                return self.UI_COLLIDER_TYPE_CAPSULE.value
            return self.UI_COLLIDER_TYPE_SPHERE.value

        if extended.shape_type == extended.SHAPE_TYPE_EXTENDED_PLANE.identifier:
            return self.UI_COLLIDER_TYPE_PLANE.value
        if extended.shape_type == extended.SHAPE_TYPE_EXTENDED_SPHERE.identifier:
            if extended.shape.sphere.inside:
                return self.UI_COLLIDER_TYPE_SPHERE_INSIDE.value
            return self.UI_COLLIDER_TYPE_SPHERE.value
        if extended.shape_type == extended.SHAPE_TYPE_EXTENDED_CAPSULE.identifier:
            if extended.shape.capsule.inside:
                return self.UI_COLLIDER_TYPE_CAPSULE_INSIDE.value
            return self.UI_COLLIDER_TYPE_CAPSULE.value
        return self.UI_COLLIDER_TYPE_SPHERE.value

    def set_ui_collider_type(self, value: int) -> None:
        extended = self.extensions.vrmc_spring_bone_extended_collider

        if value in [
            self.UI_COLLIDER_TYPE_SPHERE.value,
            self.UI_COLLIDER_TYPE_SPHERE_INSIDE.value,
        ]:
            if self.shape_type != self.SHAPE_TYPE_SPHERE.identifier:
                self.shape_type = self.SHAPE_TYPE_SPHERE.identifier
            if extended.shape_type != extended.SHAPE_TYPE_EXTENDED_SPHERE.identifier:
                extended.shape_type = extended.SHAPE_TYPE_EXTENDED_SPHERE.identifier
            inside = self.UI_COLLIDER_TYPE_SPHERE_INSIDE.value == value
            if extended.shape.sphere.inside != inside:
                extended.shape.sphere.inside = inside
            if extended.enabled != inside:
                extended.enabled = inside
            return

        if value in [
            self.UI_COLLIDER_TYPE_CAPSULE.value,
            self.UI_COLLIDER_TYPE_CAPSULE_INSIDE.value,
        ]:
            if self.shape_type != self.SHAPE_TYPE_CAPSULE.identifier:
                self.shape_type = self.SHAPE_TYPE_CAPSULE.identifier
            if extended.shape_type != extended.SHAPE_TYPE_EXTENDED_CAPSULE.identifier:
                extended.shape_type = extended.SHAPE_TYPE_EXTENDED_CAPSULE.identifier
            inside = self.UI_COLLIDER_TYPE_CAPSULE_INSIDE.value == value
            if extended.shape.capsule.inside != inside:
                extended.shape.capsule.inside = inside
            if extended.enabled != inside:
                extended.enabled = inside
            return

        if self.UI_COLLIDER_TYPE_PLANE.value == value:
            if not extended.enabled:
                extended.enabled = True
            if extended.shape_type != extended.SHAPE_TYPE_EXTENDED_PLANE.identifier:
                extended.shape_type = extended.SHAPE_TYPE_EXTENDED_PLANE.identifier

    def update_shape_type(self, context: Context) -> None:
        if (
            self.bpy_object
            and self.bpy_object.parent
            and self.bpy_object.parent.type == "ARMATURE"
        ):
            self.reset_bpy_object(context, self.bpy_object.parent)

    shape_type: EnumProperty(  # type: ignore[valid-type]
        items=shape_type_enum.items(),
        name="Shape",
        update=update_shape_type,
    )

    ui_collider_type: EnumProperty(  # type: ignore[valid-type]
        items=ui_collider_type_enum.items(),
        name="Collider Type",
        get=get_ui_collider_type,
        set=set_ui_collider_type,
    )

    # for View3D
    bpy_object: PointerProperty(  # type: ignore[valid-type]
        type=Object
    )

    # for references
    uuid: StringProperty()  # type: ignore[valid-type]
    search_one_time_uuid: StringProperty()  # type: ignore[valid-type]

    def reset_bpy_object(self, context: Context, armature: Object) -> None:
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        collider_prefix = armature_data.name
        if self.node and self.node.bone_name:
            collider_prefix = self.node.bone_name

        if not self.bpy_object or not self.bpy_object.name:
            obj = context.blend_data.objects.new(
                name=f"{collider_prefix} Collider", object_data=None
            )
            obj.empty_display_size = 0.125
            context.scene.collection.objects.link(obj)
            self.bpy_object = obj
        self.bpy_object.select_set(True)

        if self.bpy_object.parent != armature:
            self.bpy_object.parent = armature

        extended = self.extensions.vrmc_spring_bone_extended_collider
        if (
            not extended.enabled
            and self.shape_type == self.SHAPE_TYPE_SPHERE.identifier
        ) or (
            extended.enabled
            and extended.shape_type
            in [
                extended.SHAPE_TYPE_EXTENDED_SPHERE.identifier,
                extended.SHAPE_TYPE_EXTENDED_PLANE.identifier,
            ]
        ):
            children = list(self.bpy_object.children)
            for collection in context.blend_data.collections:
                for child in children:
                    child.parent = None
                    if child.name in collection.objects:
                        collection.objects.unlink(child)
            for child in children:
                if child.users <= 1:
                    context.blend_data.objects.remove(child, do_unlink=True)
            empty_display_type = "SPHERE"
            if extended.shape_type == extended.SHAPE_TYPE_EXTENDED_PLANE.identifier:
                empty_display_type = "CIRCLE"
            if self.bpy_object.empty_display_type != empty_display_type:
                self.bpy_object.empty_display_type = empty_display_type
        elif (
            not extended.enabled
            and self.shape_type == self.SHAPE_TYPE_CAPSULE.identifier
        ) or (
            extended.enabled
            and extended.shape_type == extended.SHAPE_TYPE_EXTENDED_CAPSULE.identifier
        ):
            if self.bpy_object.children:
                end_object = self.bpy_object.children[0]
            else:
                end_object = context.blend_data.objects.new(
                    name=f"{self.bpy_object.name} End", object_data=None
                )
                end_object.empty_display_size = self.bpy_object.empty_display_size
                context.scene.collection.objects.link(end_object)
                end_object.parent = self.bpy_object
                end_object.matrix_local = Matrix.Translation(Vector((0.0, 0.2, 0.0)))
            end_object.select_set(True)
            if self.bpy_object.empty_display_type != "SPHERE":
                self.bpy_object.empty_display_type = "SPHERE"
            if end_object.empty_display_type != "SPHERE":
                end_object.empty_display_type = "SPHERE"
            if end_object.empty_display_size != self.bpy_object.empty_display_size:
                end_object.empty_display_size = self.bpy_object.empty_display_size
            if end_object.scale != Vector((1, 1, 1)):
                end_object.scale = Vector((1, 1, 1))

        if self.node.bone_name:
            if self.bpy_object.parent_type != "BONE":
                self.bpy_object.parent_type = "BONE"
            if self.bpy_object.parent_bone != self.node.bone_name:
                self.bpy_object.parent_bone = self.node.bone_name
        else:
            if self.bpy_object.parent_type != "OBJECT":
                self.bpy_object.parent_type = "OBJECT"
            if self.bpy_object.parent_bone:
                self.bpy_object.parent_bone = ""

        self.broadcast_bpy_object_name(context)

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        node: BonePropertyGroup  # type: ignore[no-redef]
        shape: SpringBone1ColliderShapePropertyGroup  # type: ignore[no-redef]
        extensions: SpringBone1ColliderExtensionsPropertyGroup  # type: ignore[no-redef]
        show_expanded: bool  # type: ignore[no-redef]
        shape_type: str  # type: ignore[no-redef]
        ui_collider_type: str  # type: ignore[no-redef]
        bpy_object: Optional[Object]  # type: ignore[no-redef]
        uuid: str  # type: ignore[no-redef]
        search_one_time_uuid: str  # type: ignore[no-redef]


class SpringBone1ColliderReferencePropertyGroup(PropertyGroup):
    def get_collider_name(self) -> str:
        value = self.get("collider_name", "")
        return value if isinstance(value, str) else str(value)

    def set_collider_name(self, value: object) -> None:
        context = bpy.context

        if not isinstance(value, str):
            value = str(value)
        self.name = value
        if self.get("collider_name") == value:
            return
        self["collider_name"] = value

        self.search_one_time_uuid = uuid.uuid4().hex
        for armature in context.blend_data.armatures:
            spring_bone = get_armature_spring_bone1_extension(armature)
            for collider_group in spring_bone.collider_groups:
                for collider_reference in collider_group.colliders:
                    if (
                        collider_reference.search_one_time_uuid
                        != self.search_one_time_uuid
                    ):
                        continue

                    for collider in spring_bone.colliders:
                        if collider.name == value:
                            self.collider_uuid = collider.uuid
                    return

    collider_name: StringProperty(  # type: ignore[valid-type]
        get=get_collider_name, set=set_collider_name
    )
    collider_uuid: StringProperty()  # type: ignore[valid-type]
    search_one_time_uuid: StringProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        collider_name: str  # type: ignore[no-redef]
        collider_uuid: str  # type: ignore[no-redef]
        search_one_time_uuid: str  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/f2d8f158297fc883aef9c3071ca68fbe46b03f45/specification/0.0/schema/vrm.secondaryanimation.collidergroup.schema.json
class SpringBone1ColliderGroupPropertyGroup(PropertyGroup):
    def get_vrm_name(self) -> str:
        value = self.get("vrm_name", "")
        return value if isinstance(value, str) else str(value)

    def set_vrm_name(self, vrm_name: object) -> None:
        context = bpy.context

        if not isinstance(vrm_name, str):
            vrm_name = str(vrm_name)
        self["vrm_name"] = vrm_name
        self.fix_index(context)

    def fix_index(self, context: Context) -> None:
        self.search_one_time_uuid = uuid.uuid4().hex
        for armature in context.blend_data.armatures:
            spring_bone = get_armature_spring_bone1_extension(armature)

            for index, collider_group in enumerate(spring_bone.collider_groups):
                if collider_group.search_one_time_uuid != self.search_one_time_uuid:
                    continue

                name = f"{self.vrm_name} #{index + 1}"
                self.name = name

                for spring in spring_bone.springs:
                    for collider_group_reference in spring.collider_groups:
                        if collider_group_reference.collider_group_uuid == self.uuid:
                            collider_group_reference.collider_group_name = name

                return

    vrm_name: StringProperty(  # type: ignore[valid-type]
        name="Name",
        get=get_vrm_name,
        set=set_vrm_name,
    )

    colliders: CollectionProperty(  # type: ignore[valid-type]
        name="Colliders",
        type=SpringBone1ColliderReferencePropertyGroup,
    )

    # for UI
    show_expanded: BoolProperty()  # type: ignore[valid-type]
    active_collider_index: IntProperty(min=0)  # type: ignore[valid-type]

    # for reference
    # オブジェクトをコピーした場合同じuuidをもつオブジェクトが複数ある可能性がある
    uuid: StringProperty()  # type: ignore[valid-type]

    search_one_time_uuid: StringProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        vrm_name: str  # type: ignore[no-redef]
        colliders: CollectionPropertyProtocol[  # type: ignore[no-redef]
            SpringBone1ColliderReferencePropertyGroup
        ]
        show_expanded: bool  # type: ignore[no-redef]
        active_collider_index: int  # type: ignore[no-redef]
        uuid: str  # type: ignore[no-redef]
        search_one_time_uuid: str  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/tree/993a90a5bda9025f3d9e2923ad6dea7506f88553/specification/VRMC_springBone-1.0#initialization
class SpringBone1JointAnimationStatePropertyGroup(PropertyGroup):
    initialized_as_tail: BoolProperty()  # type: ignore[valid-type]

    previous_world_translation: FloatVectorProperty(size=3)  # type: ignore[valid-type]
    current_world_translation: FloatVectorProperty(size=3)  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        initialized_as_tail: bool  # type: ignore[no-redef]
        previous_world_translation: Sequence[float]  # type: ignore[no-redef]
        current_world_translation: Sequence[float]  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.joint.schema.json
class SpringBone1JointPropertyGroup(PropertyGroup):
    node: PointerProperty(type=BonePropertyGroup)  # type: ignore[valid-type]

    hit_radius: FloatProperty(  # type: ignore[valid-type]
        name="Joint Radius",
        min=0.0,
        default=0.0,
        soft_max=0.5,
    )

    stiffness: FloatProperty(  # type: ignore[valid-type]
        name="Stiffness Force",
        min=0.0,
        default=1.0,
        soft_max=4.0,
    )

    gravity_power: FloatProperty(  # type: ignore[valid-type]
        name="Gravity Power",
        min=0.0,
        default=0.0,
        soft_max=2.0,
    )

    def update_gravity_dir(self, _context: Context) -> None:
        gravity_dir = Vector(self.gravity_dir)
        normalized_gravity_dir = gravity_dir.normalized()
        if abs(normalized_gravity_dir.length) < float_info.epsilon:
            self.gravity_dir = (0, 0, -1)
        elif (gravity_dir - normalized_gravity_dir).length > 0.0001:
            self.gravity_dir = normalized_gravity_dir

    gravity_dir: FloatVectorProperty(  # type: ignore[valid-type]
        name="Gravity Dir",
        size=3,
        min=-1,
        max=1,
        default=(0, 0, -1),
        subtype="XYZ",
        update=update_gravity_dir,
    )

    drag_force: FloatProperty(  # type: ignore[valid-type]
        name="Drag Force",
        default=0.5,
        min=0,
        max=1.0,
    )

    animation_state: PointerProperty(  # type: ignore[valid-type]
        type=SpringBone1JointAnimationStatePropertyGroup,
    )

    # for UI
    show_expanded: BoolProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        node: BonePropertyGroup  # type: ignore[no-redef]
        hit_radius: float  # type: ignore[no-redef]
        stiffness: float  # type: ignore[no-redef]
        gravity_power: float  # type: ignore[no-redef]
        gravity_dir: Sequence[float]  # type: ignore[no-redef]
        drag_force: float  # type: ignore[no-redef]
        animation_state: (  # type: ignore[no-redef]
            SpringBone1JointAnimationStatePropertyGroup
        )
        show_expanded: bool  # type: ignore[no-redef]


class SpringBone1ColliderGroupReferencePropertyGroup(PropertyGroup):
    def get_collider_group_name(self) -> str:
        value = self.get("collider_group_name", "")
        return value if isinstance(value, str) else str(value)

    def set_collider_group_name(self, value: object) -> None:
        context = bpy.context

        if not isinstance(value, str):
            value = str(value)
        self.name = value
        if self.get("collider_group_name") == value:
            return
        self["collider_group_name"] = value

        self.search_one_time_uuid = uuid.uuid4().hex
        for armature in context.blend_data.armatures:
            spring_bone = get_armature_spring_bone1_extension(armature)
            for spring in spring_bone.springs:
                for collider_group_reference in spring.collider_groups:
                    if (
                        collider_group_reference.search_one_time_uuid
                        != self.search_one_time_uuid
                    ):
                        continue

                    for collider_group in spring_bone.collider_groups:
                        if collider_group.name == value:
                            self.collider_group_uuid = collider_group.uuid
                            break
                    return

    collider_group_name: StringProperty(  # type: ignore[valid-type]
        get=get_collider_group_name, set=set_collider_group_name
    )
    collider_group_uuid: StringProperty()  # type: ignore[valid-type]
    search_one_time_uuid: StringProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        collider_group_name: str  # type: ignore[no-redef]
        collider_group_uuid: str  # type: ignore[no-redef]
        search_one_time_uuid: str  # type: ignore[no-redef]


class SpringBone1SpringAnimationStatePropertyGroup(PropertyGroup):
    use_center_space: BoolProperty()  # type: ignore[valid-type]

    previous_center_world_translation: FloatVectorProperty(size=3)  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        use_center_space: bool  # type: ignore[no-redef]
        previous_center_world_translation: Sequence[float]  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.spring.schema.json
class SpringBone1SpringPropertyGroup(PropertyGroup):
    vrm_name: StringProperty(  # type: ignore[valid-type]
        name="Name"
    )
    joints: CollectionProperty(  # type: ignore[valid-type]
        type=SpringBone1JointPropertyGroup
    )
    collider_groups: CollectionProperty(  # type: ignore[valid-type]
        type=SpringBone1ColliderGroupReferencePropertyGroup,
    )
    center: PointerProperty(  # type: ignore[valid-type]
        type=BonePropertyGroup,
    )

    # for UI
    show_expanded: BoolProperty()  # type: ignore[valid-type]
    show_expanded_bones: BoolProperty(  # type: ignore[valid-type]
        name="Bones"
    )
    show_expanded_collider_groups: BoolProperty(  # type: ignore[valid-type]
        name="Collider Groups"
    )

    active_joint_index: IntProperty(min=0)  # type: ignore[valid-type]
    active_collider_group_index: IntProperty(min=0)  # type: ignore[valid-type]

    animation_state: PointerProperty(  # type: ignore[valid-type]
        type=SpringBone1SpringAnimationStatePropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        vrm_name: str  # type: ignore[no-redef]
        joints: CollectionPropertyProtocol[  # type: ignore[no-redef]
            SpringBone1JointPropertyGroup
        ]
        collider_groups: CollectionPropertyProtocol[  # type: ignore[no-redef]
            SpringBone1ColliderGroupReferencePropertyGroup
        ]
        center: BonePropertyGroup  # type: ignore[no-redef]
        show_expanded: bool  # type: ignore[no-redef]
        show_expanded_bones: bool  # type: ignore[no-redef]
        show_expanded_collider_groups: bool  # type: ignore[no-redef]
        active_joint_index: int  # type: ignore[no-redef]
        active_collider_group_index: int  # type: ignore[no-redef]
        animation_state: (  # type: ignore[no-redef]
            SpringBone1SpringAnimationStatePropertyGroup
        )


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.schema.json
class SpringBone1SpringBonePropertyGroup(PropertyGroup):
    colliders: CollectionProperty(  # type: ignore[valid-type]
        type=SpringBone1ColliderPropertyGroup,
    )
    collider_groups: CollectionProperty(  # type: ignore[valid-type]
        type=SpringBone1ColliderGroupPropertyGroup,
    )
    springs: CollectionProperty(  # type: ignore[valid-type]
        type=SpringBone1SpringPropertyGroup,
    )

    def update_enable_animation(self, _context: Context) -> None:
        for spring in self.springs:
            for joint in spring.joints:
                joint.animation_state.initialized_as_tail = False

    enable_animation: BoolProperty(  # type: ignore[valid-type]
        name="Enable Animation",
        update=update_enable_animation,
    )

    # for UI
    show_expanded_colliders: BoolProperty(  # type: ignore[valid-type]
        name="Spring Bone Colliders"
    )
    show_expanded_collider_groups: BoolProperty(  # type: ignore[valid-type]
        name="Spring Bone Collider Groups"
    )
    show_expanded_springs: BoolProperty(  # type: ignore[valid-type]
        name="Spring Bone Springs"
    )

    active_collider_index: IntProperty(min=0)  # type: ignore[valid-type]
    active_collider_group_index: IntProperty(min=0)  # type: ignore[valid-type]
    active_spring_index: IntProperty(min=0)  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        colliders: CollectionPropertyProtocol[  # type: ignore[no-redef]
            SpringBone1ColliderPropertyGroup
        ]
        collider_groups: CollectionPropertyProtocol[  # type: ignore[no-redef]
            SpringBone1ColliderGroupPropertyGroup
        ]
        springs: CollectionPropertyProtocol[  # type: ignore[no-redef]
            SpringBone1SpringPropertyGroup
        ]
        enable_animation: bool  # type: ignore[no-redef]
        show_expanded_colliders: bool  # type: ignore[no-redef]
        show_expanded_collider_groups: bool  # type: ignore[no-redef]
        show_expanded_springs: bool  # type: ignore[no-redef]
        active_collider_index: int  # type: ignore[no-redef]
        active_collider_group_index: int  # type: ignore[no-redef]
        active_spring_index: int  # type: ignore[no-redef]


def get_armature_spring_bone1_extension(
    armature: Armature,
) -> SpringBone1SpringBonePropertyGroup:
    spring_bone1 = getattr(
        getattr(armature, "vrm_addon_extension", None), "spring_bone1", None
    )
    if not isinstance(spring_bone1, SpringBone1SpringBonePropertyGroup):
        raise TypeError
    return spring_bone1
