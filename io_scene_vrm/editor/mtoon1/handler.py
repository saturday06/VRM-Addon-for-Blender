import time
from typing import Callable, List, Optional, Tuple

import bpy
from bpy.app.handlers import persistent

from ...common.logging import get_logger
from .ops import VRM_OT_refresh_mtoon1_outline

logger = get_logger(__name__)

if not persistent:  # for fake-bpy-modules

    def persistent(func: Callable[[object], None]) -> Callable[[object], None]:
        return func


previous_object_material_state: List[List[Optional[Tuple[str, bool, bool]]]] = []


def update_mtoon1_outline() -> Optional[float]:
    compare_start_time = time.perf_counter()

    # ここは最適化の必要がある
    object_material_state = [
        [
            (
                str(material_slot.material.name),
                bool(
                    material_slot.material.vrm_addon_extension.mtoon1.get_enabled_in_material(
                        material_slot.material
                    )
                ),
                bool(obj.data.use_auto_smooth),
            )
            if material_slot.material
            else None
            for material_slot in obj.material_slots
        ]
        for obj in bpy.data.objects
        if obj.type == "MESH"
    ]
    not_changed = object_material_state == previous_object_material_state

    compare_end_time = time.perf_counter()

    logger.debug(
        f"The duration to determine material updates is {compare_end_time - compare_start_time:.9f} seconds"
    )

    if not_changed:
        return None
    previous_object_material_state.clear()
    previous_object_material_state.extend(object_material_state)

    VRM_OT_refresh_mtoon1_outline.refresh(bpy.context)
    return None


def trigger_update_mtoon1_outline() -> None:
    if bpy.app.version < (3, 3):
        return
    if bpy.app.timers.is_registered(update_mtoon1_outline):
        return
    bpy.app.timers.register(update_mtoon1_outline, first_interval=0.2)


@persistent  # type: ignore[misc]
def save_pre(_dummy: object) -> None:
    update_mtoon1_outline()


@persistent  # type: ignore[misc]
def depsgraph_update_pre(_dummy: object) -> None:
    trigger_update_mtoon1_outline()
