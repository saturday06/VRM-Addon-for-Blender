#!/usr/bin/env python3

# Copyright (c) 2018 iCyP
# Released under the MIT license
# https://opensource.org/licenses/mit-license.php

import json
from pathlib import Path
from tkinter import filedialog, messagebox

from io_scene_vrm.common import gltf


def exist_or_makedir(path: Path) -> Path:
    ripped_dir = path.absolute().parent / "ripped"
    ripped_dir.mkdir(exist_ok=True)
    return ripped_dir


model_path = Path(filedialog.askopenfilename(filetypes=[("", "*vrm")]))
vrm_json, binary = gltf.parse_glb(model_path.read_bytes())
if messagebox.askyesno(message="write VRM.json?"):
    writedir = exist_or_makedir(model_path)
    writejsonpath = writedir / "vrm.json"
    writejsonpath.write_text(json.dumps(vrm_json, indent=4), encoding="UTF-8")
