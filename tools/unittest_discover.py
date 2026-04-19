#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import argparse
import os
import sys
from io import TextIOWrapper
from pathlib import Path
from threading import Thread
from typing import TextIO
from unittest import TestLoader
from unittest.runner import TextTestRunner

import bpy

# This is not necessary if executed from uv
sys.path.append(str(Path(__file__).parent.parent / "src"))


def reader_task(reader_io: TextIO) -> None:
    """Merge direct output from bpy and output from TextTestRunner as much as possible.

    Without any measures, the timing of logs output directly from bpy and logs output
    from TextTestRunner will be significantly misaligned. By calling the flush() method
    at high frequency, we make those outputs appear simultaneously as much as possible.
    """
    stderr_encoding = sys.stderr.encoding
    if not isinstance(stderr_encoding, str):
        stderr_encoding = "mbcs" if sys.platform == "win32" else "utf-8"

    while char := reader_io.read(1):
        safe_char = char.encode(stderr_encoding, errors="replace").decode(
            stderr_encoding, errors="replace"
        )

        # Process output one character at a time. Normally, line-based processing or
        # buffering is preferable, but TextTestRunner may print "." as progress output,
        # which cannot be handled accurately line by line and can drift from bpy output
        # timing. Character-by-character handling is less efficient, but if stdout or
        # stderr volume is high enough for this to become a bottleneck, that output
        # volume itself is likely a bug, so this trade-off is acceptable.
        sys.stdout.flush()
        sys.stderr.write(safe_char)
        sys.stderr.flush()


def discover_and_run_test_suite() -> int:
    argv = list(sys.argv)
    if bpy.app.binary_path:
        argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    else:
        argv = argv[1:]

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

    reader_fd, writer_fd = os.pipe()
    try:
        with os.fdopen(reader_fd, "r", encoding="utf-8") as reader_io:
            reader_fd = None
            reader_thread = Thread(target=reader_task, args=(reader_io,), daemon=True)
            try:
                with os.fdopen(writer_fd, "wb", buffering=0) as writer_binary_io:
                    writer_fd = None
                    with TextIOWrapper(
                        writer_binary_io,
                        encoding="utf-8",
                        write_through=True,
                    ) as writer_io:
                        reader_thread.start()
                        test_runner = TextTestRunner(
                            stream=writer_io,
                            failfast=args.failfast,
                            verbosity=2 if args.verbose else 1,
                        )
                        test_result = test_runner.run(test_suite)
                        return 0 if test_result.wasSuccessful() else 1
            finally:
                if reader_thread.is_alive():
                    reader_thread.join()
    finally:
        if reader_fd is not None:
            os.close(reader_fd)
        if writer_fd is not None:
            os.close(writer_fd)


if __name__ == "__main__":
    sys.exit(discover_and_run_test_suite())
