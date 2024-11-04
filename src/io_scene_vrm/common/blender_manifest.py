# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class BlenderManifest:
    version: tuple[int, int, int]
    blender_version_min: tuple[int, int, int]
    blender_version_max: Optional[tuple[int, int, int]]

    @classmethod
    def default_blender_manifest_path(cls) -> Path:
        return Path(__file__).parent.parent / "blender_manifest.toml"

    @classmethod
    def read_3_tuple_version(
        cls, blender_manifest: str, key: str
    ) -> Optional[tuple[int, int, int]]:
        # When the version of Python used by the minimum supported version of Blender
        # exceeds 3.11, it is rewritten in the tomli library.
        lines = list(map(str.strip, blender_manifest.splitlines()))

        pattern = key + r' = "(\d+)\.(\d+)\.(\d+)"'
        for line in lines:
            match = re.fullmatch(pattern, line)
            if not match:
                continue
            return (int(match[1]), int(match[2]), int(match[3]))

        return None

    @classmethod
    def read(cls, blender_manifest: Optional[str] = None) -> "BlenderManifest":
        if blender_manifest is None:
            blender_manifest = cls.default_blender_manifest_path().read_text(
                encoding="UTF-8"
            )

        version = cls.read_3_tuple_version(blender_manifest, "version")
        if version is None:
            message = "'version' does not found in blender manifest"
            raise ValueError(message)

        blender_version_min = cls.read_3_tuple_version(
            blender_manifest, "blender_version_min"
        )
        if blender_version_min is None:
            message = "'blender_version_min' does not found in blender manifest"
            raise ValueError(message)

        return BlenderManifest(
            version=version,
            blender_version_min=blender_version_min,
            blender_version_max=cls.read_3_tuple_version(
                blender_manifest, "blender_version_max"
            ),
        )
