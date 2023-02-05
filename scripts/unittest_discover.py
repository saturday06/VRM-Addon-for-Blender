#!/usr/bin/env python3

import argparse
import contextlib
import sys
import unittest
from pathlib import Path
from typing import TextIO


def run(stream: TextIO) -> None:
    argv = sys.argv
    in_blender = False
    with contextlib.suppress(ImportError):
        import bpy

        in_blender = bool(bpy.app.binary_path)

    if in_blender:
        if "--" in argv:
            argv = argv[slice(argv.index("--") + 1, len(argv))]
        else:
            argv = []

    parser = argparse.ArgumentParser(prog=Path(__file__).name)
    parser.add_argument("-f", "--failfast", action="store_true")
    args = parser.parse_args(argv)

    test = unittest.TestLoader().discover(start_dir=str(Path(__file__).parent.parent))
    runner = unittest.runner.TextTestRunner(stream=stream, failfast=args.failfast)
    result = runner.run(test)
    if not result.wasSuccessful():
        sys.exit(1)


if sys.platform == "win32":
    with open(
        sys.stderr.fileno(), mode="w", encoding="ansi", buffering=1
    ) as windows_stderr:
        run(windows_stderr)
else:
    run(sys.stderr)
