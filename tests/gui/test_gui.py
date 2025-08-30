# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import os
from unittest import TestCase

from io_scene_vrm.common.logger import get_logger

logger = get_logger(__name__)


class TestGui(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

    def setUp(self) -> None:
        super().setUp()
        if os.name != "linux2":
            self.skipTest("Skipping GUI tests")

    def tearDown(self) -> None:
        super().tearDown()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
