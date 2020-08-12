"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import os
import json
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from ..importer.vrm_load import parse_glb


def exist_or_makedir(path):
    dirname = os.path.dirname(os.path.abspath(path))
    writedir = os.path.join(dirname, "ripped")
    if not os.path.exists(writedir):
        os.mkdir(writedir)
    return writedir


model_path = filedialog.askopenfilename(filetypes=[("", "*vrm")])
with open(model_path, "rb") as f:
    vrm_json, binary = parse_glb(f.read())
if messagebox.askyesno(message="write VRM.json?"):
    writedir = exist_or_makedir(model_path)
    writejsonpath = os.path.join(writedir, "vrm.json")
    with open(writejsonpath, "w") as f:
        json.dump(vrm_json, f, indent=4)
