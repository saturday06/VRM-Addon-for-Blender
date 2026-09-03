# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import TestCase

from io_scene_vrm.common.logger import get_logger


class TestLogger(TestCase):
    def test_log_output_match(self) -> None:
        logger = get_logger("test_log_output_match")
        matching_pattern = "Test error"
        non_matching_pattern = "Not found"
        logger.register_log_output_match(matching_pattern)
        logger.register_log_output_match(non_matching_pattern)

        logger.error("Test %s", "error")
        logger.info("Test info: %d", 1)
        logger.error("Test error")

        self.assertEqual(logger.get_log_output_match_count(matching_pattern), 2)
        self.assertEqual(logger.get_log_output_match_count(non_matching_pattern), 0)

        logger.clear_log_output_match_count()
        self.assertEqual(logger.get_log_output_match_count(matching_pattern), 0)
