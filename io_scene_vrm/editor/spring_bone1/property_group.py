import statistics
import uuid
from collections.abc import Sequence
from sys import float_info
from typing import TYPE_CHECKING, Optional

import bpy
from mathutils import Matrix, Vector

from ...common import convert
from ...common.logging import get_logger
from ..property_group import BonePropertyGroup

if TYPE_CHECKING:
    from ..property_group import CollectionPropertyProtocol

logger = get_logger(__name__)


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.shape.schema.json#L7-L27
class SpringBone1ColliderShapeSpherePropertyGroup(bpy.types.PropertyGroup):
    def find_armature_and_collider(
        self,
    ) -> tuple[bpy.types.Object, "SpringBone1ColliderPropertyGroup"]:
        for obj in bpy.data.objects:
            if obj.type != "ARMATURE":
                continue
            armature_data = obj.data
            if not isinstance(armature_data, bpy.types.Armature):
                continue
            for collider in armature_data.vrm_addon_extension.spring_bone1.colliders:
                if collider.shape.sphere == self:
                    return (obj, collider)
        raise ValueError("No armature")

    def get_offset(self) -> tuple[float, float, float]:
        armature, collider = self.find_armature_and_collider()
        if not collider.bpy_object:
            logger.error(f"Failed to get bpy object of {collider.name} in get_offset()")
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
        backup_radius = self.get_radius()
        armature, collider = self.find_armature_and_collider()
        collider.reset_bpy_object(bpy.context, armature)
        bone = armature.pose.bones.get(collider.node.bone_name)
        if not bone:
            if collider.bpy_object:
                collider.bpy_object.matrix_world = (
                    armature.matrix_world @ Matrix.Translation(offset)
                )
            self.set_radius(backup_radius)
            return
        if collider.bpy_object:
            collider.bpy_object.matrix_world = (
                armature.matrix_world @ bone.matrix @ Matrix.Translation(offset)
            )
        self.set_radius(backup_radius)

    def get_radius(self) -> float:
        _, collider = self.find_armature_and_collider()
        if not collider.bpy_object:
            logger.error(f"Failed to get bpy object of {collider.name} in get_radius()")
            return 0.0
        mean_scale = statistics.mean(
            abs(s) for s in collider.bpy_object.matrix_basis.to_scale()
        )
        return float(mean_scale * collider.bpy_object.empty_display_size)

    def set_radius(self, v: float) -> None:
        armature, collider = self.find_armature_and_collider()
        collider.reset_bpy_object(bpy.context, armature)
        if not collider.bpy_object:
            logger.error(f"Faild to reset bpy_object for collider: {collider.name}")
            return
        location, rotation, _ = collider.bpy_object.matrix_basis.decompose()
        collider.bpy_object.matrix_basis = (
            Matrix.Translation(location) @ rotation.to_matrix().to_4x4()
        )
        collider.bpy_object.empty_display_size = v

    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="TRANSLATION",  # noqa: F821
        unit="LENGTH",  # noqa: F821
        default=(0, 0, 0),
        get=get_offset,
        set=set_offset,
    )

    radius: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Radius",  # noqa: F821
        min=0.0,
        default=0.0,
        soft_max=1.0,
        unit="LENGTH",  # noqa: F821
        get=get_radius,
        set=set_radius,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        offset: Sequence[float]  # type: ignore[no-redef]
        radius: float  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.shape.schema.json#L28-L58
class SpringBone1ColliderShapeCapsulePropertyGroup(bpy.types.PropertyGroup):
    def find_armature_and_collider(
        self,
    ) -> tuple[bpy.types.Object, "SpringBone1ColliderPropertyGroup"]:
        for obj in bpy.data.objects:
            if obj.type != "ARMATURE":
                continue
            armature_data = obj.data
            if not isinstance(armature_data, bpy.types.Armature):
                continue
            for collider in armature_data.vrm_addon_extension.spring_bone1.colliders:
                if collider.shape.capsule == self:
                    return (obj, collider)
        raise ValueError("No armature")

    def get_offset(self) -> tuple[float, float, float]:
        armature, collider = self.find_armature_and_collider()
        if not collider.bpy_object:
            logger.error(f"Failed to get bpy object of {collider.name} in get_offset()")
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
        backup_radius = self.get_radius()
        armature, collider = self.find_armature_and_collider()
        collider.reset_bpy_object(bpy.context, armature)
        bone = armature.pose.bones.get(collider.node.bone_name)
        if not bone:
            if collider.bpy_object:
                collider.bpy_object.matrix_world = (
                    armature.matrix_world @ Matrix.Translation(offset)
                )
            self.set_radius(backup_radius)
            return
        if collider.bpy_object:
            collider.bpy_object.matrix_world = (
                armature.matrix_world @ bone.matrix @ Matrix.Translation(offset)
            )
        self.set_radius(backup_radius)

    def get_tail(self) -> tuple[float, float, float]:
        armature, collider = self.find_armature_and_collider()
        if not collider.bpy_object or not collider.bpy_object.children:
            logger.error(f"Failed to get bpy object of {collider.name} in get_tail()")
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
        backup_radius = self.get_radius()
        armature, collider = self.find_armature_and_collider()
        collider.reset_bpy_object(bpy.context, armature)
        bone = armature.pose.bones.get(collider.node.bone_name)
        if not bone:
            if collider.bpy_object:
                collider.bpy_object.children[
                    0
                ].matrix_world = armature.matrix_world @ Matrix.Translation(offset)
            self.set_radius(backup_radius)
            return
        if collider.bpy_object:
            collider.bpy_object.children[0].matrix_world = (
                armature.matrix_world @ bone.matrix @ Matrix.Translation(offset)
            )
        self.set_radius(backup_radius)

    def get_radius(self) -> float:
        _, collider = self.find_armature_and_collider()
        if not collider.bpy_object:
            logger.error(f"Failed to get bpy object of {collider.name} in get_radius()")
            return 0.0
        mean_scale = statistics.mean(
            abs(s) for s in collider.bpy_object.matrix_basis.to_scale()
        )
        return float(mean_scale * collider.bpy_object.empty_display_size)

    def set_radius(self, v: float) -> None:
        armature, collider = self.find_armature_and_collider()
        collider.reset_bpy_object(bpy.context, armature)
        if not collider.bpy_object:
            logger.error(f"Faild to reset bpy_object for collider: {collider.name}")
            return
        location, rotation, _ = collider.bpy_object.matrix_basis.decompose()
        collider.bpy_object.matrix_basis = (
            Matrix.Translation(location) @ rotation.to_matrix().to_4x4()
        )
        collider.bpy_object.empty_display_size = v
        collider.bpy_object.children[0].empty_display_size = v

    offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="TRANSLATION",  # noqa: F821
        unit="LENGTH",  # noqa: F821
        default=(0, 0, 0),
        get=get_offset,
        set=set_offset,
    )

    radius: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Radius",  # noqa: F821
        min=0.0,
        default=0.0,
        soft_max=1.0,
        unit="LENGTH",  # noqa: F821
        get=get_radius,
        set=set_radius,
    )

    tail: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        subtype="TRANSLATION",  # noqa: F821
        unit="LENGTH",  # noqa: F821
        default=(0, 0, 0),
        get=get_tail,
        set=set_tail,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        offset: Sequence[float]  # type: ignore[no-redef]
        radius: float  # type: ignore[no-redef]
        tail: Sequence[float]  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.shape.schema.json
class SpringBone1ColliderShapePropertyGroup(bpy.types.PropertyGroup):
    sphere: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=SpringBone1ColliderShapeSpherePropertyGroup  # noqa: F722
    )
    capsule: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=SpringBone1ColliderShapeCapsulePropertyGroup  # noqa: F821
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        sphere: SpringBone1ColliderShapeSpherePropertyGroup  # type: ignore[no-redef]
        capsule: SpringBone1ColliderShapeCapsulePropertyGroup  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.collider.schema.json
class SpringBone1ColliderPropertyGroup(bpy.types.PropertyGroup):
    def broadcast_bpy_object_name(self) -> None:
        if not self.bpy_object or not self.bpy_object.name:
            self.name = ""  # pylint: disable=attribute-defined-outside-init
            return
        if self.name == self.bpy_object.name:
            return
        self.name = (  # pylint: disable=attribute-defined-outside-init
            self.bpy_object.name
        )

        self.search_one_time_uuid = uuid.uuid4().hex
        for armature in bpy.data.armatures:
            if not hasattr(armature, "vrm_addon_extension"):
                continue

            spring_bone = armature.vrm_addon_extension.spring_bone1

            for collider in spring_bone.colliders:
                if collider.search_one_time_uuid != self.search_one_time_uuid:
                    continue

                for collider_group in spring_bone.collider_groups:
                    for collider_reference in collider_group.colliders:
                        if self.uuid != collider_reference.collider_uuid:
                            continue
                        collider_reference.collider_name = self.name

                return

    node: bpy.props.PointerProperty(type=BonePropertyGroup)  # type: ignore[valid-type]
    shape: bpy.props.PointerProperty(type=SpringBone1ColliderShapePropertyGroup)  # type: ignore[valid-type]

    # for UI
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]

    SHAPE_TYPE_SPHERE = "Sphere"
    SHAPE_TYPE_CAPSULE = "Capsule"
    shape_type_items = [
        (SHAPE_TYPE_SPHERE, "Sphere", "", 0),
        (SHAPE_TYPE_CAPSULE, "Capsule", "", 1),
    ]

    def update_shape_type(self, context: bpy.types.Context) -> None:
        if (
            self.bpy_object
            and self.bpy_object.parent
            and self.bpy_object.parent.type == "ARMATURE"
        ):
            self.reset_bpy_object(context, self.bpy_object.parent)

    shape_type: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=shape_type_items,
        name="Shape",  # noqa: F821
        update=update_shape_type,
    )

    # for View3D
    bpy_object: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Object  # noqa: F722
    )

    # for references
    uuid: bpy.props.StringProperty()  # type: ignore[valid-type]
    search_one_time_uuid: bpy.props.StringProperty()  # type: ignore[valid-type]

    def reset_bpy_object(
        self, context: bpy.types.Context, armature: bpy.types.Object
    ) -> None:
        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            return
        collider_prefix = armature_data.name
        if self.node and self.node.bone_name:
            collider_prefix = self.node.bone_name

        if not self.bpy_object or not self.bpy_object.name:
            obj = bpy.data.objects.new(
                name=f"{collider_prefix} Collider", object_data=None
            )
            obj.empty_display_size = 0.125
            context.scene.collection.objects.link(obj)
            self.bpy_object = obj

        if self.bpy_object.parent != armature:
            self.bpy_object.parent = armature
        if self.bpy_object.empty_display_type != "SPHERE":
            self.bpy_object.empty_display_type = "SPHERE"

        if self.shape_type == self.SHAPE_TYPE_SPHERE:
            children = list(self.bpy_object.children)
            for collection in bpy.data.collections:
                for child in children:
                    child.parent = None
                    if child.name in collection.objects:
                        collection.objects.unlink(child)
            for child in children:
                if child.users <= 1:
                    bpy.data.objects.remove(child, do_unlink=True)

        elif self.shape_type == self.SHAPE_TYPE_CAPSULE:
            if self.bpy_object.children:
                end_object = self.bpy_object.children[0]
            else:
                end_object = bpy.data.objects.new(
                    name=f"{self.bpy_object.name} End", object_data=None
                )
                end_object.empty_display_size = self.bpy_object.empty_display_size
                context.scene.collection.objects.link(end_object)
                end_object.parent = self.bpy_object
            if end_object.empty_display_type != "SPHERE":
                end_object.empty_display_type = "SPHERE"

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

        self.broadcast_bpy_object_name()

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        node: BonePropertyGroup  # type: ignore[no-redef]
        shape: SpringBone1ColliderShapePropertyGroup  # type: ignore[no-redef]
        show_expanded: bool  # type: ignore[no-redef]
        shape_type: str  # type: ignore[no-redef]
        bpy_object: Optional[bpy.types.Object]  # type: ignore[no-redef]
        uuid: str  # type: ignore[no-redef]
        search_one_time_uuid: str  # type: ignore[no-redef]


class SpringBone1ColliderReferencePropertyGroup(bpy.types.PropertyGroup):
    def get_collider_name(self) -> str:
        value = self.get("collider_name", "")
        return value if isinstance(value, str) else str(value)

    def set_collider_name(self, value: object) -> None:
        if not isinstance(value, str):
            value = str(value)
        self.name = value  # pylint: disable=attribute-defined-outside-init
        if self.get("collider_name") == value:
            return
        self["collider_name"] = value

        self.search_one_time_uuid = uuid.uuid4().hex
        for armature in bpy.data.armatures:
            spring_bone = armature.vrm_addon_extension.spring_bone1
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

    collider_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        get=get_collider_name, set=set_collider_name
    )
    collider_uuid: bpy.props.StringProperty()  # type: ignore[valid-type]
    search_one_time_uuid: bpy.props.StringProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        collider_name: str  # type: ignore[no-redef]
        collider_uuid: str  # type: ignore[no-redef]
        search_one_time_uuid: str  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/f2d8f158297fc883aef9c3071ca68fbe46b03f45/specification/0.0/schema/vrm.secondaryanimation.collidergroup.schema.json
class SpringBone1ColliderGroupPropertyGroup(bpy.types.PropertyGroup):
    def get_vrm_name(self) -> str:
        value = self.get("vrm_name", "")
        return value if isinstance(value, str) else str(value)

    def set_vrm_name(self, vrm_name: object) -> None:
        if not isinstance(vrm_name, str):
            vrm_name = str(vrm_name)
        self["vrm_name"] = vrm_name
        self.fix_index()

    def fix_index(self) -> None:
        self.search_one_time_uuid = uuid.uuid4().hex
        for armature in bpy.data.armatures:
            spring_bone = armature.vrm_addon_extension.spring_bone1

            for index, collider_group in enumerate(spring_bone.collider_groups):
                if collider_group.search_one_time_uuid != self.search_one_time_uuid:
                    continue

                name = f"{index}: {self.vrm_name}"
                self.name = name  # pylint: disable=attribute-defined-outside-init

                for spring in spring_bone.springs:
                    for collider_group_reference in spring.collider_groups:
                        if collider_group_reference.collider_group_uuid == self.uuid:
                            collider_group_reference.collider_group_name = name

                return

    vrm_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Name", get=get_vrm_name, set=set_vrm_name  # noqa: F722, F821
    )

    colliders: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Colliders", type=SpringBone1ColliderReferencePropertyGroup  # noqa: F821
    )

    # for UI
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]

    # for reference
    # オブジェクトをコピーした場合同じuuidをもつオブジェクトが複数ある可能性があるのに注意する。
    uuid: bpy.props.StringProperty()  # type: ignore[valid-type]

    search_one_time_uuid: bpy.props.StringProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        vrm_name: str  # type: ignore[no-redef]
        colliders: CollectionPropertyProtocol[  # type: ignore[no-redef]
            SpringBone1ColliderReferencePropertyGroup
        ]
        show_expanded: bool  # type: ignore[no-redef]
        uuid: str  # type: ignore[no-redef]
        search_one_time_uuid: str  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/tree/993a90a5bda9025f3d9e2923ad6dea7506f88553/specification/VRMC_springBone-1.0#initialization
class SpringBone1JointAnimationStatePropertyGroup(bpy.types.PropertyGroup):
    initialized_as_tail: bpy.props.BoolProperty()  # type: ignore[valid-type]

    previous_world_translation: bpy.props.FloatVectorProperty(size=3)  # type: ignore[valid-type]
    current_world_translation: bpy.props.FloatVectorProperty(size=3)  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        initialized_as_tail: bool  # type: ignore[no-redef]
        previous_world_translation: Sequence[float]  # type: ignore[no-redef]
        current_world_translation: Sequence[float]  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.joint.schema.json
class SpringBone1JointPropertyGroup(bpy.types.PropertyGroup):
    node: bpy.props.PointerProperty(type=BonePropertyGroup)  # type: ignore[valid-type]

    hit_radius: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Joint Radius",  # noqa: F722
        min=0.0,
        default=0.0,
        soft_max=0.5,
    )

    stiffness: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Stiffness Force",  # noqa: F722
        min=0.0,
        default=1.0,
        soft_max=4.0,
    )

    gravity_power: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Gravity Power",  # noqa: F722
        min=0.0,
        default=0.0,
        soft_max=2.0,
    )

    def update_gravity_dir(self, _context: bpy.types.Context) -> None:
        gravity_dir = Vector(self.gravity_dir)
        normalized_gravity_dir = gravity_dir.normalized()
        if abs(normalized_gravity_dir.length) < float_info.epsilon:
            self.gravity_dir = (0, 0, -1)
        elif (gravity_dir - normalized_gravity_dir).length > 0.0001:
            self.gravity_dir = normalized_gravity_dir

    gravity_dir: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        name="Gravity Dir",  # noqa: F722
        size=3,
        min=-1,
        max=1,
        default=(0, 0, -1),  # noqa: F722
        subtype="XYZ",  # noqa: F821
        update=update_gravity_dir,
    )

    drag_force: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Drag Force",  # noqa: F722
        default=0.5,
        min=0,
        max=1.0,
    )

    animation_state: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=SpringBone1JointAnimationStatePropertyGroup,
    )

    # for UI
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        node: BonePropertyGroup  # type: ignore[no-redef]
        hit_radius: float  # type: ignore[no-redef]
        stiffness: float  # type: ignore[no-redef]
        gravity_power: float  # type: ignore[no-redef]
        gravity_dir: Sequence[float]  # type: ignore[no-redef]
        drag_force: float  # type: ignore[no-redef]
        animation_state: SpringBone1JointAnimationStatePropertyGroup  # type: ignore[no-redef]
        show_expanded: bool  # type: ignore[no-redef]


class SpringBone1ColliderGroupReferencePropertyGroup(bpy.types.PropertyGroup):
    def get_collider_group_name(self) -> str:
        value = self.get("collider_group_name", "")
        return value if isinstance(value, str) else str(value)

    def set_collider_group_name(self, value: object) -> None:
        if not isinstance(value, str):
            value = str(value)
        self.name = value  # pylint: disable=attribute-defined-outside-init
        if self.get("collider_group_name") == value:
            return
        self["collider_group_name"] = value

        self.search_one_time_uuid = uuid.uuid4().hex
        for armature in bpy.data.armatures:
            spring_bone = armature.vrm_addon_extension.spring_bone1
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
                    return

    collider_group_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        get=get_collider_group_name, set=set_collider_group_name
    )
    collider_group_uuid: bpy.props.StringProperty()  # type: ignore[valid-type]
    search_one_time_uuid: bpy.props.StringProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        collider_group_name: str  # type: ignore[no-redef]
        collider_group_uuid: str  # type: ignore[no-redef]
        search_one_time_uuid: str  # type: ignore[no-redef]


class SpringBone1SpringAnimationStatePropertyGroup(bpy.types.PropertyGroup):
    use_center_space: bpy.props.BoolProperty()  # type: ignore[valid-type]

    previous_center_world_translation: bpy.props.FloatVectorProperty(size=3)  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        use_center_space: bool  # type: ignore[no-redef]
        previous_center_world_translation: Sequence[float]  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.spring.schema.json
class SpringBone1SpringPropertyGroup(bpy.types.PropertyGroup):
    vrm_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Name"  # noqa: F821
    )
    joints: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=SpringBone1JointPropertyGroup
    )
    collider_groups: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=SpringBone1ColliderGroupReferencePropertyGroup,
    )
    center: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=BonePropertyGroup,
    )

    # for UI
    show_expanded: bpy.props.BoolProperty()  # type: ignore[valid-type]
    show_expanded_bones: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Bones"  # noqa: F821
    )
    show_expanded_collider_groups: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Collider Groups"  # noqa: F722
    )

    animation_state: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=SpringBone1SpringAnimationStatePropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
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
        animation_state: SpringBone1SpringAnimationStatePropertyGroup  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.schema.json
class SpringBone1SpringBonePropertyGroup(bpy.types.PropertyGroup):
    colliders: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=SpringBone1ColliderPropertyGroup,
    )
    collider_groups: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=SpringBone1ColliderGroupPropertyGroup,
    )
    springs: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=SpringBone1SpringPropertyGroup,
    )

    def update_enable_animation(self, _context: bpy.types.Context) -> None:
        for spring in self.springs:
            for joint in spring.joints:
                joint.animation_state.initialized_as_tail = False

    enable_animation: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="[Experimental!] Enable Animation",  # noqa: F722
        update=update_enable_animation,
    )

    # for UI
    show_expanded_colliders: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Spring Bone Colliders"  # noqa: F722
    )
    show_expanded_collider_groups: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Spring Bone Collider Groups"  # noqa: F722
    )
    show_expanded_springs: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Spring Bone Springs"  # noqa: F722
    )
    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
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
