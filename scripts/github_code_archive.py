#!/usr/bin/env python3

import importlib
import pathlib
import platform
import sys
import zipfile
from os import path

import bpy

addon_path = sys.argv[sys.argv.index("--") + 1]

with zipfile.ZipFile(addon_path) as z:
    module_name = path.commonpath([f.filename for f in z.filelist])

bpy.ops.preferences.addon_install(filepath=addon_path)
bpy.ops.preferences.addon_enable(module=module_name)

repository_root_dir = path.dirname(path.dirname(__file__))
input_path = path.join(
    repository_root_dir, "tests", "resources", "vrm", "in", "triangle.vrm"
)
expected_path = path.join(
    repository_root_dir, "tests", "resources", "vrm", "2.83", "out", "triangle.vrm"
)
actual_path = path.join(repository_root_dir, "out.vrm")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
while bpy.data.collections:
    bpy.data.collections.remove(bpy.data.collections[0])

bpy.ops.import_scene.vrm(filepath=input_path)
bpy.ops.export_scene.vrm(filepath=actual_path)

float_tolerance = 0.000001

vrm_diff = importlib.import_module(module_name + ".importer.vrm_diff")
diffs = vrm_diff.vrm_diff(
    pathlib.Path(actual_path).read_bytes(),
    pathlib.Path(expected_path).read_bytes(),
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
    if platform.system() == "Windows":
        sys.stderr.buffer.write(message.encode())
        raise AssertionError
    raise AssertionError(message)
