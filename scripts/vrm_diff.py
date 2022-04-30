#!/usr/bin/env python3

import sys
from pathlib import Path

from io_scene_vrm.external.fake_bpy_module_support import is_fake_bpy_module
from io_scene_vrm.importer.vrm_diff import vrm_diff

if __name__ == "__main__":
    if is_fake_bpy_module():
        print("bpy module is 'fake_bpy_module'. Real Blender bpy is required.")
        sys.exit(1)
    float_tolerance = sys.float_info.epsilon
    if len(sys.argv) == 4:
        float_tolerance = float(sys.argv[3])
    diffs = vrm_diff(
        Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes(), float_tolerance
    )
    for diff in diffs:
        print(diff)
    sys.exit(1 if diffs else 0)
