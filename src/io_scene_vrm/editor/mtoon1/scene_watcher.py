# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import sys
from dataclasses import dataclass, field
from typing import Final, Optional

import bpy
from bpy.types import Context, Material, Mesh, ShaderNodeGroup, ShaderNodeOutputMaterial

from ...common import ops
from ...common.logger import get_logger
from ...common.scene_watcher import RunState, SceneWatcher
from ...common.shader import MTOON1_AUTO_SETUP_GROUP_NODE_TREE_CUSTOM_KEY
from ..extension import get_material_extension
from .ops import VRM_OT_refresh_mtoon1_outline, generate_mtoon1_outline_material_name

logger = get_logger(__name__)


HAS_AUTO_SMOOTH: Final = tuple(bpy.app.version) < (4, 1)


@dataclass
class ComparisonMaterial:
    name: str


@dataclass
class ComparisonObject:
    use_auto_smooth: Optional[bool] = None
    comparison_materials: list[Optional[ComparisonMaterial]] = field(
        default_factory=list[Optional[ComparisonMaterial]]
    )


@dataclass
class OutlineUpdater(SceneWatcher):
    comparison_objects: list[ComparisonObject] = field(
        default_factory=list[ComparisonObject]
    )
    outline_material_key_to_material_name: dict[int, str] = field(
        default_factory=dict[int, str]
    )

    object_index: int = 0
    comparison_object_index: int = 0
    material_slot_index: int = 0

    @staticmethod
    def get_outline_material_key(material: Material) -> int:
        return material.as_pointer() ^ 0x5F5FF5F5

    def reset_run_progress(self) -> None:
        self.object_index = 0
        self.comparison_object_index = 0
        self.material_slot_index = 0
        self.outline_material_key_to_material_name.clear()

    def run(self, context: Context) -> RunState:
        """Detect changes in material assignments to objects and assign outlines."""
        blend_data = context.blend_data

        # If this value becomes zero, return PREEMPT and interrupt the process.
        # If a change is detected, set a virtually infinite value so that the
        # process proceeds to the end.
        preempt_countdown = 15

        changed = False

        create_modifier = False

        objects = blend_data.objects
        if not objects:
            return RunState.FINISH

        # If the number of objects is less than the previous state and the index
        # range is exceeded, start over from the beginning
        objects_len = len(objects)
        if self.object_index >= objects_len:
            self.object_index = 0

        # Scan objects and check for differences with the comparison object
        next_object_index = self.object_index
        for obj in objects[self.object_index : objects_len]:
            self.object_index = next_object_index
            next_object_index += 1

            preempt_countdown -= 1
            if preempt_countdown <= 0:
                return RunState.PREEMPT

            # Only mesh objects are subject to investigation.
            # Skip if it is not a mesh object
            obj_data = obj.data
            if not isinstance(obj_data, Mesh):
                continue
            mesh = obj_data

            # If the number of comparison objects is insufficient, add a new
            # comparison object
            while self.comparison_object_index >= len(self.comparison_objects):
                self.comparison_objects.append(ComparisonObject())

            # Get a comparison object
            comparison_object = self.comparison_objects[self.comparison_object_index]

            # Comparison of use_auto_smooth
            if HAS_AUTO_SMOOTH and (
                (use_auto_smooth := comparison_object.use_auto_smooth) is None
                or (use_auto_smooth != mesh.use_auto_smooth)
            ):
                changed, preempt_countdown = True, sys.maxsize
                # Resolve change differences
                comparison_object.use_auto_smooth = mesh.use_auto_smooth

            # If the number of MaterialSlots is less than the previous state and
            # the index range is exceeded, start over from the beginning
            material_slots = obj.material_slots
            material_slots_len = len(material_slots)
            if self.material_slot_index >= material_slots_len:
                self.material_slot_index = 0

            # Match the number of MaterialSlots and the number of comparison Materials
            while material_slots_len > len(comparison_object.comparison_materials):
                comparison_object.comparison_materials.append(None)
            while material_slots_len < len(comparison_object.comparison_materials):
                comparison_object.comparison_materials.pop()

            # Scan MaterialSlots and check for differences with the comparison Material
            next_material_slot_index = self.material_slot_index
            for material_slot in material_slots[
                self.material_slot_index : material_slots_len
            ]:
                material_slot_index = self.material_slot_index = (
                    next_material_slot_index
                )
                next_material_slot_index += 1

                preempt_countdown -= 1
                if preempt_countdown <= 0:
                    return RunState.PREEMPT

                # If the number of comparison objects is insufficient, add a new
                # comparison object
                while material_slot_index >= len(
                    comparison_object.comparison_materials
                ):
                    comparison_object.comparison_materials.append(None)
                comparison_material = comparison_object.comparison_materials[
                    material_slot_index
                ]

                # Difference check
                if not (
                    (material := material_slot.material)
                    and (mtoon1 := get_material_extension(material).mtoon1)
                    and mtoon1.get_enabled()
                ):
                    # MToon of the material in the material slot is disabled
                    if comparison_material is None:
                        # No updates
                        continue
                    # if the comparison object is enabled, a change is detected
                    changed, preempt_countdown = True, sys.maxsize
                    # Resolve change differences
                    comparison_object.comparison_materials[material_slot_index] = None
                    continue

                # MToon of the material in the material slot is enabled

                outline_material = mtoon1.outline_material
                outline_material_name = generate_mtoon1_outline_material_name(material)

                if (
                    comparison_material
                    and comparison_material.name == material.name
                    and (
                        outline_material is None
                        or outline_material.name == outline_material_name
                    )
                ):
                    continue

                # MToon of the material in the material slot is enabled,
                # but if the comparison object does not exist or the name
                # does not match, a change is detected
                changed, preempt_countdown = True, sys.maxsize
                # Resolve change differences
                comparison_object.comparison_materials[material_slot_index] = (
                    ComparisonMaterial(material.name)
                )
                # A material with MToon enabled has been newly assigned
                # to the object so, if necessary, create a new outline
                # modifier.
                # Originally, True/False should be set for each object and
                # material pair, but for now, I think it's okay to fix it
                # for practical use.
                create_modifier = True

                if outline_material is None:
                    continue

                # When a material is copied, a single outline material may be
                # shared by multiple MToon materials. To resolve this, copy the
                # outline material and reassign it.
                outline_material_key = self.get_outline_material_key(outline_material)
                original_material_name = self.outline_material_key_to_material_name.get(
                    outline_material_key
                )
                if original_material_name is None:
                    self.outline_material_key_to_material_name[outline_material_key] = (
                        material.name
                    )
                elif original_material_name != material.name:
                    outline_material = outline_material.copy()
                    outline_material_key = self.get_outline_material_key(
                        outline_material
                    )
                    self.outline_material_key_to_material_name[outline_material_key] = (
                        material.name
                    )
                    mtoon1.outline_material = outline_material

                # The outline material name follows the naming changes of
                # the base MToon material.
                if outline_material.name != outline_material_name:
                    outline_material.name = outline_material_name

            # Since the scanning of MaterialSlots is complete,
            # reset the next scanning index to 0.
            self.material_slot_index = 0

            # Before scanning the next object,
            # advance the index of the next comparison object.
            self.comparison_object_index += 1

        # Since the number of elements in self.comparison_objects may be
        # unnecessarily large, reduce it to a sufficient size
        while len(self.comparison_objects) > self.comparison_object_index:
            self.comparison_objects.pop()

        if not changed:
            return RunState.FINISH

        VRM_OT_refresh_mtoon1_outline.refresh(context, create_modifier=create_modifier)
        return RunState.FINISH

    def create_fast_path_performance_test_objects(self, context: Context) -> None:
        blend_data = context.blend_data

        for i in range(100):
            blend_data.materials.new(f"Material#{i}")

        for i in range(100):
            mesh = blend_data.meshes.new(f"Mesh#{i}")
            obj = blend_data.objects.new(f"Object#{i}", mesh)
            context.scene.collection.objects.link(obj)
            for k in range(50):
                material = blend_data.materials[(k * 3) % len(blend_data.materials)]
                mesh.materials.append(material)
                if k % 5 == 0:
                    get_material_extension(material).mtoon1.enabled = True


@dataclass
class MToon1AutoSetup(SceneWatcher):
    last_material_index: int = 0
    last_node_index: int = 0

    def reset_run_progress(self) -> None:
        self.last_material_index: int = 0
        self.last_node_index: int = 0

    def run(self, context: Context) -> RunState:
        """Monitor the appearance of MToon auto-setup node groups and set them up.

        Since this function is called frequently, keep the processing lightweight and
        be careful to minimize IO and GC Allocation.
        """
        # If this value becomes 0 or less, interrupt the process
        search_preempt_countdown = 100

        materials = context.blend_data.materials

        # Restore the material traversal start position from the last interrupted state.
        end_material_index = len(materials)
        start_material_index = self.last_material_index
        if start_material_index >= end_material_index:
            self.last_material_index = 0
            self.last_node_index = 0
            start_material_index = 0

        # Traverse the materials and enable MToon if necessary.
        next_material_index = start_material_index
        for material in materials[start_material_index:end_material_index]:
            self.last_material_index = next_material_index
            next_material_index += 1

            search_preempt_countdown -= 1
            if search_preempt_countdown <= 0:
                return RunState.PREEMPT

            if not material.use_nodes:
                continue
            node_tree = material.node_tree
            if node_tree is None:
                continue

            nodes = node_tree.nodes

            # Restore the node traversal start position from the last interrupted state.
            end_node_index = len(nodes)
            start_node_index = self.last_node_index
            if start_node_index >= end_node_index:
                start_node_index = 0

            # Traverse the nodes and convert the material to MToon if the MToon
            # placeholder node is connected to ShaderNodeOutputMaterial.
            next_node_index = start_node_index
            for node in nodes[start_node_index:end_node_index]:
                self.last_node_index = next_node_index
                next_node_index += 1

                search_preempt_countdown -= 1
                if search_preempt_countdown <= 0:
                    return RunState.PREEMPT

                if not isinstance(node, ShaderNodeGroup):
                    continue

                group_node_tree = node.node_tree
                if group_node_tree is None:
                    continue

                if not group_node_tree.get(
                    MTOON1_AUTO_SETUP_GROUP_NODE_TREE_CUSTOM_KEY
                ):
                    continue

                found = False
                for output in node.outputs:
                    for link in output.links:
                        if isinstance(link.to_node, ShaderNodeOutputMaterial):
                            found = True
                            break
                    if found:
                        break
                if not found:
                    continue

                mtoon1 = get_material_extension(material).mtoon1
                if mtoon1.enabled:
                    ops.vrm.reset_mtoon1_material_shader_node_group(
                        material_name=material.name
                    )
                else:
                    mtoon1.enabled = True
                break
            self.last_node_index = 0
        self.last_material_index = 0

        return RunState.FINISH

    def create_fast_path_performance_test_objects(self, context: Context) -> None:
        blend_data = context.blend_data

        for i in range(100):
            blend_data.materials.new(f"Material#{i}")

        for i in range(100):
            mesh = blend_data.meshes.new(f"Mesh#{i}")
            obj = blend_data.objects.new(f"Object#{i}", mesh)
            context.scene.collection.objects.link(obj)
            for k in range(50):
                material = blend_data.materials[(k * 3) % len(blend_data.materials)]
                mesh.materials.append(material)
                if k % 5 == 0:
                    get_material_extension(material).mtoon1.enabled = True
