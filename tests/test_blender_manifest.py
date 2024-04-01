import re
from pathlib import Path
from unittest import TestCase

from io_scene_vrm.common import version


class TestBlenderManifest(TestCase):
    def test_version(self) -> None:
        path = (
            Path(__file__).parent.parent
            / "src"
            / "io_scene_vrm"
            / "blender_manifest.toml"
        )
        text = path.read_text()
        match = re.search(r'^version = "(.+)"$', text, re.MULTILINE)
        if match is None:
            message = "No version match"
            raise AssertionError(message)
        actual_version = match.group(1)
        expected_version = ".".join(map(str, version.addon_version()))
        self.assertEqual(expected_version, actual_version)
