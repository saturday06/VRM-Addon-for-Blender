"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
from ..gl_const import GL_CONSTANS
import json
from collections import OrderedDict
class Glb_bin_collection:
	def __init__(self):
		self.vertex_attribute_bins = []  #Glb_bin list
		self.image_bins = []
		self.bin = b""
	def pack_all(self):
		bin_dic = OrderedDict()
		byteOffset = 0
		bin_dic["bufferViews"] = []
		bin_dic["images"] = []
		for img in self.image_bins:
			self.bin +=img.bin
			bin_dic["images"].append(OrderedDict({
				"name": img.name,
				"bufferView": img.buffer_view_id,
				"mimeType": img.image_type
				}))
			bin_dic["bufferViews"].append(OrderedDict({
				"buffer": 0,
				"byteOffset": byteOffset,
				"byteLength": img.bin_length
			}))
			byteOffset += img.bin_length
		bin_dic["accessors"] = []
		for vab in self.vertex_attribute_bins:
			self.bin += vab.bin
			vab_dic = OrderedDict({
			    "bufferView": vab.buffer_view_id,
				"byteOffset": 0,
				"type": vab.array_type,
				"componentType": vab.component_type,
				"count": vab.array_count,
				"normalized": False
			})
			if vab.min_max:
				vab_dic["min"] = vab.min_max[0]
				vab_dic["max"] = vab.min_max[1]
			bin_dic["accessors"].append(vab_dic)
			bin_dic["bufferViews"].append(OrderedDict({
				"buffer": 0,
				"byteOffset": byteOffset,
				"byteLength": vab.bin_length
			}))
			byteOffset += vab.bin_length
		bin_dic["buffers"] = [{"byteLength":byteOffset}]

		buffer_view_and_accessors_orderd_dic = bin_dic
		return buffer_view_and_accessors_orderd_dic,self.bin

	def get_new_buffer_view_id(self):
		return len(self.vertex_attribute_bins) + len(self.image_bins)

	def get_new_image_id(self):
		return len(self.image_bins)

	def get_new_glb_bin_id(self):
		return len(self.vertex_attribute_bins)
		
class Base_bin():
	def __init__(self,bin,glb_bin_collection):
		self.bin = bin
		self.bin_length = len(bin)
		self.buffer_view_id = glb_bin_collection.get_new_buffer_view_id()

class Image_bin(Base_bin):
	def __init__(self,
			image_bin="", name="", image_type="image/png",
			glb_bin_collection = None):
		super().__init__(image_bin,glb_bin_collection)
		self.name = name
		self.image_type = image_type
		self.image_id = glb_bin_collection.get_new_image_id()
		glb_bin_collection.image_bins.append(self)

class Glb_bin(Base_bin):
	def __init__(self,
			bin="",
			array_type="SCALAR", component_type=GL_CONSTANS.FLOAT,
			array_count=0,
			min_max_tuple = None,
			glb_bin_collection = None):
		super().__init__(bin,glb_bin_collection)
		self.array_type = array_type #String:scalar,VEC3 etc...
		self.component_type = component_type  #GL_CONSTANS:FLOAT, uint etc...
		self.array_count = array_count  #array num
		self.min_max = min_max_tuple # position attribute must need min_max
		self.accessor_id = glb_bin_collection.get_new_glb_bin_id()
		glb_bin_collection.vertex_attribute_bins.append(self)
		
		

		