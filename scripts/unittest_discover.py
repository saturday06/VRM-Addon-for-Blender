#!/usr/bin/env python3

import argparse
import contextlib
import platform
import sys
import unittest
from os.path import basename, dirname
from typing import TextIO


def run(stream: TextIO) -> None:
    argv = sys.argv
    in_blender = False
    with contextlib.suppress(ImportError):
        import bpy

        in_blender = bool(bpy.app.binary_path)

    if in_blender:
        if "--" in argv:
            argv = argv[argv.index("--") + 1 :]
        else:
            argv = []

    parser = argparse.ArgumentParser(prog=basename(__file__))
    parser.add_argument("-f", "--failfast", action="store_true")
    args = parser.parse_args(argv)

    test = unittest.TestLoader().discover(start_dir=dirname(dirname(__file__)))
    runner = unittest.runner.TextTestRunner(stream=stream, failfast=args.failfast)
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
