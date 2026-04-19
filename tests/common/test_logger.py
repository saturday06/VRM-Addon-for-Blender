# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import logging
from unittest import TestCase
from unittest.mock import patch

import bpy

from io_scene_vrm.common.logger import VrmAddonLoggerAdapter, environ, get_logger


class TestLogger(TestCase):
    def test_get_logger(self) -> None:
        original_debug = bpy.app.debug
        original_environ_debug = environ.get("BLENDER_VRM_LOGGING_LEVEL_DEBUG")

        try:
            # Test default behavior (INFO or higher level)
            bpy.app.debug = False
            with patch.dict(environ, {"BLENDER_VRM_LOGGING_LEVEL_DEBUG": "no"}):
                # When getEffectiveLevel() is WARNING (30),
                #     max(INFO, 30) is WARNING (30)
                # When getEffectiveLevel() is NOTSET (0, root is WARNING),
                #     max(INFO, 30) is 30
                logger = get_logger("test_logger_info")
                self.assertIsInstance(logger, VrmAddonLoggerAdapter)
                self.assertEqual(
                    logger.logger.level,
                    max(
                        logging.INFO,
                        logging.getLogger("test_logger_info").getEffectiveLevel(),
                    ),
                )

                # Set level to DEBUG to verify max(INFO, DEBUG(10)) == INFO(20)
                raw_logger = logging.getLogger("test_logger_info_forced")
                raw_logger.setLevel(logging.DEBUG)
                logger = get_logger("test_logger_info_forced")
                self.assertEqual(logger.logger.level, logging.INFO)

            # Test bpy.app.debug = True (DEBUG level)
            bpy.app.debug = True
            with patch.dict(environ, {"BLENDER_VRM_LOGGING_LEVEL_DEBUG": "no"}):
                logger = get_logger("test_logger_debug_bpy")
                self.assertIsInstance(logger, VrmAddonLoggerAdapter)
                self.assertEqual(logger.logger.level, logging.DEBUG)

            # Test BLENDER_VRM_LOGGING_LEVEL_DEBUG = "yes" (DEBUG level)
            bpy.app.debug = False
            with patch.dict(environ, {"BLENDER_VRM_LOGGING_LEVEL_DEBUG": "yes"}):
                logger = get_logger("test_logger_debug_env")
                self.assertIsInstance(logger, VrmAddonLoggerAdapter)
                self.assertEqual(logger.logger.level, logging.DEBUG)

            # Test both True (DEBUG level)
            bpy.app.debug = True
            with patch.dict(environ, {"BLENDER_VRM_LOGGING_LEVEL_DEBUG": "yes"}):
                logger = get_logger("test_logger_debug_both")
                self.assertIsInstance(logger, VrmAddonLoggerAdapter)
                self.assertEqual(logger.logger.level, logging.DEBUG)

        finally:
            bpy.app.debug = original_debug
            if original_environ_debug is not None:
                environ["BLENDER_VRM_LOGGING_LEVEL_DEBUG"] = original_environ_debug
            elif "BLENDER_VRM_LOGGING_LEVEL_DEBUG" in environ:
                del environ["BLENDER_VRM_LOGGING_LEVEL_DEBUG"]
