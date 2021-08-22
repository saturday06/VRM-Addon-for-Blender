#!/usr/bin/env python3
# noqa: INP001

import sys
from os.path import dirname
from pathlib import Path

sys.path.insert(0, dirname(dirname(__file__)))

# pylint: disable=wrong-import-position;
from io_scene_vrm.importer.py_model import vrm_diff  # noqa: E402

# pylint: enable=wrong-import-position;


if __name__ == "__main__":
    float_tolerance = sys.float_info.epsilon
    if len(sys.argv) == 4:
        float_tolerance = float(sys.argv[3])
    diffs = vrm_diff(
        Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes(), float_tolerance
    )
    for diff in diffs:
        print(diff)
    sys.exit(1 if diffs else 0)
