#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import argparse
import os
import sys
import warnings
from pathlib import Path
from typing import TextIO
from unittest import TestLoader
from unittest.runner import TextTestRunner

import bpy

# This is not necessary if executed from uv
sys.path.append(str(Path(__file__).parent.parent / "src"))


def discover_and_run_test_suite(argv: list[str], stream: TextIO) -> int:
    if bpy.app.binary_path:
        argv = argv[argv.index("--") + 1 :] if "--" in argv else []

    parser = argparse.ArgumentParser(prog=Path(__file__).name)
    parser.add_argument("-f", "--failfast", action="store_true")
    parser.add_argument("-p", "--pattern", default="test*.py")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    test_loader = TestLoader()
    test_suite = test_loader.discover(
        start_dir=str(Path(__file__).parent.parent),
        pattern=args.pattern,
    )
    test_runner = TextTestRunner(
        stream=stream,
        failfast=args.failfast,
        verbosity=2 if args.verbose else 1,
    )
    test_result = test_runner.run(test_suite)
    return 0 if test_result.wasSuccessful() else 1


def main(argv: list[str]) -> int:
    # if os.environ.get("BLENDER_VRM_TEST_DEP_WARNINGS") == "true":
    warnings.simplefilter("always", DeprecationWarning)

    if sys.platform == "win32":
        with open(  # noqa: PTH123
            sys.stderr.fileno(), mode="w", encoding="ansi", buffering=1
        ) as windows_stderr:
            return discover_and_run_test_suite(argv, windows_stderr)
    return discover_and_run_test_suite(argv, sys.stderr)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
