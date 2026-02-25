# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from collections.abc import Sequence
from typing import Optional

from bpy.types import (
    Context,
    Object,
)

from ..common.logger import get_logger
from ..common.preferences import ExportPreferencesProtocol
from ..external.io_scene_gltf2_support import (
    init_extras_export,
)
from .abstract_base_vrm_exporter import (
    AbstractBaseVrmExporter,
)

logger = get_logger(__name__)


class KhrCharacterExporter(AbstractBaseVrmExporter):
    def __init__(
        self,
        context: Context,
        export_objects: Sequence[Object],
        armature: Object,
        _export_preferences: ExportPreferencesProtocol,
    ) -> None:
        super().__init__(context, export_objects, armature)

    def export(self) -> Optional[bytes]:
        init_extras_export()
