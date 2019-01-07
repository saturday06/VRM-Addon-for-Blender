"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
class VRM_pydata(object):
    def __init__(
            self,
            filepath = None,json = None,decoded_binary = None,
            image_propaties = None,meshes =None,materials = None,
            nodes_dict = None,origine_nodes_dict = None,
            skins_joints_list = None , skins_root_node_list = None
            ):
        self.filepath = filepath
        self.json = json
        self.decoded_binary = decoded_binary

        self.image_propaties = image_propaties if image_propaties is not None else []
        self.meshes = meshes if meshes is not None else []
        self.materials = materials if materials is not None else []
        self.nodes_dict = nodes_dict if nodes_dict is not None else {}
        self.origine_nodes_dict = origine_nodes_dict if origine_nodes_dict is not None else {}
        self.skins_joints_list = skins_joints_list if skins_joints_list is not None else []
        self.skins_root_node_list = skins_root_node_list if skins_root_node_list is not None else []


class Mesh(object):
    def __init__(self):
        self.name = ""
        self.face_indices = []
        self.skin_id = None
        self.object_id = None



class Node(object):
    def __init__(self):
        self.name = ""
        self.position = None
        self.rotation = None
        self.scale = None
        self.children = None
        self.blend_bone = None
        self.mesh_id = None
        self.skin_id = None



class Image_props(object):
    def __init__(self,name,filepath,fileType):
        self.name = name
        self.filePath = filepath
        self.fileType = fileType




class Material(object):
    def __init__(self):
        self.name = ""
        self.shader_name = ""



class Material_GLTF(Material):
    def __init__(self):
        super().__init__()
        self.color_texture_index = None
        self.color_texcood_index = None
        self.base_color = None
        self.metallic_factor = None
        self.roughnessFactor = None
        self.emissiveFactor = None
        self.metallic_roughness_texture_index = None
        self.metallic_roughness_texture_texcood = None
        self.normal_texture_index = None
        self.normal_texture_texcoord_index = None
        self.emissive_texture_index = None
        self.emissive_texture_texcoord_index = None
        self.occlusion_texture_index = None
        self.occlusion_texture_texcood_index = None
        self.double_sided = None
        self.alphaMode = "OPAQUE"
        self.shadeless = False


class Material_Transparent_Z_write(Material):
    float_props = [
            "_MainTex",
            "_Cutoff",
            "_BlendMode",
            "_CullMode",
            "_VColBlendMode",
            "_SrcBlend",
            "_DstBlend",
            "_ZWrite",
            ]
    texture_index_list = [
        "_MainTex"
        ]
    vector_props = [
        "_Color"
        ]

    def __init__(self):
        super().__init__()
        self.float_prop_dic = {prop: None for prop in self.float_props}
        self.vector_props_dic = {prop: None for prop in self.vector_props}
        self.texture_index_dic = {tex:None for tex in self.texture_index_list}



class Material_MToon(Material):
    float_props = [
        "_Cutoff",
        "_BumpScale",
        "_ReceiveShadowRate",
        "_ShadeShift",
        "_ShadeToony",
        "_ShadingGradeRate",
        "_LightColorAttenuation",
        "_IndirectLightIntensity",
        "_OutlineWidth",
        "_OutlineScaledMaxDistance",
        "_OutlineLightingMix",
        "_DebugMode",
        "_BlendMode",
        "_OutlineWidthMode",
        "_OutlineColorMode",
        "_CullMode",
        "_OutlineCullMode",
        "_SrcBlend",
        "_DstBlend",
        "_ZWrite",
        "_IsFirstSetup"
        ]

    texture_index_list = [
        "_MainTex",#use in BI
        "_ShadeTexture",#ignore in BI
        "_BumpMap",#use in BI
        "_ReceiveShadowTexture",#ignore in BI
        "_ShadingGradeTexture",#ignore in BI
        "_EmissionMap",#ignore in BI
        "_SphereAdd",#use in BI
        "_OutlineWidthTexture"#ignore in BI
        ]
    vector_props = [
        "_Color",
        "_EmissionColor",
        "_OutlineColor",
        "_ShadeColor"
        ]
    #texture offset and scaling props by texture
    vector_props.extend(texture_index_list)

    keyword_list = [
        "_NORMALMAP",
        "_ALPHATEST_ON",
        "_ALPHABLEND_ON",
        "_ALPHAPREMULTIPLY_ON",
        "MTOON_OUTLINE_WIDTH_WORLD",
        "MTOON_OUTLINE_WIDTH_SCREEN",
        "MTOON_OUTLINE_COLOR_FIXED",
        "MTOON_OUTLINE_COLOR_MIXED",
        "MTOON_DEBUG_NORMAL",
        "MTOON_DEBUG_LITSHADERATE"
    ]
    tagmap_list = [
        "RenderType"
    ]

    def __init__(self):
        super().__init__()
        self.float_props_dic = {prop:None for prop in self.float_props}
        self.vector_props_dic = {prop:None for prop in self.vector_props}
        self.texture_index_dic = {prop: None for prop in self.texture_index_list}
        self.keyword_dic = {kw:False for kw in self.keyword_list}
        self.tag_dic = {tag:None for tag in self.tagmap_list}
        

if "__main__" == __name__:
    pass
