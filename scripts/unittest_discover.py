#!/usr/bin/env python3

"""
# noqa: INP001
"""

import platform
import sys
import unittest
from os.path import dirname
from typing import TextIO


def run(stream: TextIO) -> None:
    test = unittest.TestLoader().discover(start_dir=dirname(dirname(__file__)))
    runner = unittest.runner.TextTestRunner(stream=stream)
    result = runner.run(test)
    if not result.wasSuccessful():
        sys.exit(1)


if platform.system() == "Windows":
    with open(
        sys.stderr.fileno(), mode="w", encoding="ansi", buffering=1
    ) as windows_stderr:
        run(windows_stderr)
else:
    run(sys.stderr)
