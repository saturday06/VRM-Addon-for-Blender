# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import TestCase

from io_scene_vrm.common.human_bone_mapper.human_bone_mapper import (
    canonicalize_bone_name,
)


class TestHumanBoneMapper(TestCase):
    def test_canonicalize_bone_name(self) -> None:
        self.assertEqual(
            canonicalize_bone_name(
                "UpperArm"
                "L.\N{FULLWIDTH DIGIT ZERO}1\N{FULLWIDTH DIGIT TWO}MN"
                "__ABC  . de_\N{FULLWIDTH LATIN SMALL LETTER F}"
            ),
            "upper.arm.left.012.mn.abc.de.f",
        )
