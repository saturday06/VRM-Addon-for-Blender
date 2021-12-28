from abc import ABC, abstractmethod
from typing import Optional


class AbstractBaseVrmExporter(ABC):
    @abstractmethod
    def export_vrm(self) -> Optional[bytes]:
        pass
