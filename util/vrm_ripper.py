"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import json
import os
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox

from ..importer.vrm_load import parse_glb


def exist_or_makedir(path):
    ripped_dir = os.path.join(os.path.dirname(os.path.abspath(path)), "ripped")
    if not os.path.exists(ripped_dir):
        os.mkdir(ripped_dir)
    return ripped_dir


model_path = filedialog.askopenfilename(filetypes=[("", "*vrm")])
with open(model_path, "rb") as f:
    vrm_json, binary = parse_glb(f.read())
if messagebox.askyesno(message="write VRM.json?"):
    writedir = exist_or_makedir(model_path)
    writejsonpath = os.path.join(writedir, "vrm.json")
    with open(writejsonpath, "w") as f:
        json.dump(vrm_json, f, indent=4)
