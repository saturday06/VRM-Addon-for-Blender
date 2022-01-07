from typing import Optional

from .abstract_base_vrm_exporter import AbstractBaseVrmExporter


class Gltf2AddonVrmExporter(AbstractBaseVrmExporter):
    def export_vrm(self) -> Optional[bytes]:
        raise NotImplementedError()
