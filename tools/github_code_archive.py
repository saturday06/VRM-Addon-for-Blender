#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import sys
import zipfile
from os.path import commonpath
from pathlib import Path

import bpy

# This is not necessary if executed from uv
sys.path.append(str(Path(__file__).parent.parent / "src"))

from io_scene_vrm.common import ops
from io_scene_vrm.importer.vrm_diff import vrm_diff

context = bpy.context

addon_path = sys.argv[sys.argv.index("--") + 1]

with zipfile.ZipFile(addon_path) as z:
    module_name = commonpath([f.filename for f in z.filelist])

bpy.ops.preferences.addon_install(filepath=addon_path)
bpy.ops.preferences.addon_enable(module=module_name)

repository_root_dir = Path(__file__).parent.parent
input_path = repository_root_dir / "tests" / "resources" / "vrm" / "in" / "triangle.vrm"
expected_path = (
    repository_root_dir
    / "tests"
    / "resources"
    / "vrm"
    / "2.93"
    / "out"
    / "triangle.vrm"
)
actual_path = repository_root_dir / "out.vrm"

bpy.ops.wm.read_homefile(use_empty=True)

if ops.import_scene.vrm(filepath=str(input_path)) != {"FINISHED"}:
    message = f"Import failure: {input_path}"
    raise AssertionError(message)
if ops.export_scene.vrm(filepath=str(actual_path)) != {"FINISHED"}:
    message = f"Export failure: {actual_path}"
    raise AssertionError(message)

float_tolerance = 0.000001

diffs = vrm_diff(
    actual_path.read_bytes(),
    expected_path.read_bytes(),
    float_tolerance,
)

if diffs:
    diffs_str = "\n".join(diffs)
    message = (
        f"Exceeded the VRM diff threshold:{float_tolerance:19.17f}\n"
        + f"input={input_path}\n"
        + f"left ={actual_path}\n"
        + f"right={expected_path}\n"
        + f"{diffs_str}\n"
    )
    if sys.platform == "win32":
        sys.stderr.buffer.write(message.encode())
        raise AssertionError
    raise AssertionError(message)
