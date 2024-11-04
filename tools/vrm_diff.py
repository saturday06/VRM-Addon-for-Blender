#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import sys
from pathlib import Path

from io_scene_vrm.importer.vrm_diff import vrm_diff

if __name__ == "__main__":
    float_tolerance = sys.float_info.epsilon
    if len(sys.argv) == 4:
        float_tolerance = float(sys.argv[3])
    diffs = vrm_diff(
        Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes(), float_tolerance
    )
    sys.stdout.writelines(diffs)
    sys.exit(1 if diffs else 0)
