"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import json
import tkinter
import tkinter.filedialog
import struct
from collections import OrderedDict
read_path = tkinter.filedialog.askopenfilename(filetypes=[("vrm,json","*.vrm;*.json")])
loaded_json =""
with open(read_path, "rb") as f:
    filetype = read_path.split(".")[-1]
    if filetype == "vrm":
        bi = f.read()
        magic = 12 #offset from header
        bi_size = struct.unpack("<I", bi[magic:magic+4])[0]
        magic = 20 #offset from header
        loaded_json = json.loads(bi[magic:magic+bi_size].decode("utf-8"),object_pairs_hook=OrderedDict)
    elif filetype =="json":
        loaded_json = json.load(f)
    else:
        print("unsupported format :{}".format(filetype))
        exit()

#something do in below with loaded_json

with open(read_path+".json","wt")as f:
   f.write(json.dumps(loaded_json,indent=4))
#for scene in loaded_json["scenes"]:
nodes = loaded_json["nodes"]
for i,node in enumerate(nodes):
    nodes[i]["name"] = "{},{}".format(i,node["name"])
    if "children" in node.keys():
        for ch in node["children"]:
            nodes[i]["children"] = "{},{}".format(ch,loaded_json["nodes"][ch]["name"])
    del nodes[i]["rotation"]
    del nodes[i]["scale"]
    
skins = loaded_json["skins"]
for skin in skins:
    skin["skeleton"] = "{:>4}:{}".format(skin["skeleton"] , loaded_json["nodes"][skin["skeleton"]]["name"])
    for i,joint_id in enumerate(skin["joints"]) :
        skin["joints"][i] = "{:>4}:{}".format(joint_id , loaded_json["nodes"][joint_id]["name"])
    
#with open(read_path+"_skin"+".json","wt")as f:
#   f.write(json.dumps({"skins":skins,"nodes":nodes},indent=4))

