# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import TestCase

from io_scene_vrm.common import version


class TestVersion(TestCase):
    def test_version(self) -> None:
        self.assertEqual(
            version.get_addon_version(),
            (
                3,  # x-release-please-major
                14,  # x-release-please-minor
                0,  # x-release-please-patch
            ),
        )
