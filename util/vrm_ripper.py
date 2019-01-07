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
    writedir = os.path.join(dir,"ripped")
    if not os.path.exists(writedir):
        os.mkdir(writedir)
    return writedir


model_path = filedialog.askopenfilename(filetypes=[("", "*vrm")])
with open(model_path,"rb") as f:
    vrm_json,bin = parse_glb(f.read())
if messagebox.askyesno(message = "write VRM.json?"):
    writedir = exsitOrMakedir(model_path)
    writejsonpath = os.path.join(writedir,"vrm.json")
    with open(writejsonpath,"w")as f:
        json.dump(vrm_json,f,indent = 4)
if messagebox.askyesno(message = "rip images?"):
    writedir = exsitOrMakedir(model_path)
    binaly = Binaly_Reader(bin)
    bufferViews = vrm_json["bufferViews"]
    accessors = vrm_json["accessors"]
    for id,image_prop in enumerate(vrm_json["images"]):
        if "extra" in image_prop:
            image_name = image_prop["extra"]["name"]
        else :
            image_name = image_prop["name"]
        if image_name == "":
            image_name = "texture_" +str(id)
        binaly.set_pos(bufferViews[image_prop["bufferView"]]["byteOffset"])
        image_binary = binaly.read_binaly(bufferViews[image_prop["bufferView"]]["byteLength"])
        image_type = image_prop["mimeType"].split("/")[-1]
        image_path = os.path.join(writedir, image_name + "." + image_type)
        if not os.path.exists(image_path):
            with open(image_path, "wb") as imageWriter:
                imageWriter.write(image_binary)
        else:
            print(image_name + " Image is already exists. NOT OVER WRITTEN")

