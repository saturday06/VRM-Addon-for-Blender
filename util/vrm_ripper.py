"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

from ..importer.vrm_load import parse_glb
import os
import json
from .binaly_loader import Binaly_Reader
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox


def exsitOrMakedir(path):
    dir = os.path.dirname(os.path.abspath(path))
    writedir = os.path.join(dir, "ripped")
    if not os.path.exists(writedir):
        os.mkdir(writedir)
    return writedir


model_path = filedialog.askopenfilename(filetypes=[("", "*vrm")])
with open(model_path, "rb") as f:
    vrm_json, bin = parse_glb(f.read())
if messagebox.askyesno(message="write VRM.json?"):
    writedir = exsitOrMakedir(model_path)
    writejsonpath = os.path.join(writedir, "vrm.json")
    with open(writejsonpath, "w") as f:
        json.dump(vrm_json, f, indent=4)
