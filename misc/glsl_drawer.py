import bpy
import gpu
import bgl

from mathutils import Matrix,Vector,Euler
from math import sqrt,radians
from gpu_extras.batch import batch_for_shader
from .. import V_Types

class ICYP_OT_Draw_Model(bpy.types.Operator):
    bl_idname = "vrm.model_draw"
    bl_label = "(InDev not working )Draw VRM model"
    bl_description = "Draw selected with GLSL"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        gdo = glsl_draw_obj(context)
        glsl_draw_obj.draw_func_add()
        return {"FINISHED"}
class ICYP_OT_Remove_Draw_Model(bpy.types.Operator):
    bl_idname = "vrm.model_draw_remove"
    bl_label = "(InDev not working ) remove Draw VRM model"
    bl_description = "Draw selected with GLSL"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        glsl_draw_obj.draw_func_remove()
        return {"FINISHED"}

class MToon_glsl():
    material = None
    main_node = None
    name = None
    alpha_method = None

    float_dic = {}
    vector_dic = {}
    texture_dic = {}
    cull_mode = "BACK"
    def __init__(self,material):
        self.material = material
        self.name = material.name
        self.update()
    def get_texture(self,tex_name):
        if tex_name == "ReceiveShadow_Texture":
            tex_name += "_alpha"
        if self.main_node.inputs[tex_name].links:
            self.main_node.inputs[tex_name].links[0].from_node.image.gl_load()
            return self.main_node.inputs[tex_name].links[0].from_node.image
        else:
            return None
    def get_value(self,val_name):
        if self.main_node.inputs[val_name].links:
            return self.main_node.inputs[val_name].links[0].from_node.outputs[0].default_value
        else:
            return self.main_node.inputs[val_name].default_value

    def get_color(self,vec_name):
        if self.main_node.inputs[vec_name].links:
            return self.main_node.inputs[vec_name].links[0].from_node.outputs[0].default_value
        else:
            return self.main_node.inputs[vec_name].default_value       
    
    def update(self):
        if self.material.blend_method in ("OPAQUE",'CLIP'):
            self.alpha_method = self.material.blend_method
        else:
            self.alpha_method = "TRANSPARENT"
        if self.material.use_backface_culling:
            self.cull_mode = "BACK"
        else:
            self.cull_mode = "NO"
        for node in self.material.node_tree.nodes:
            if node.type =="OUTPUT_MATERIAL":
                self.main_node = node.inputs['Surface'].links[0].from_node

        self.float_dic = {}
        self.vector_dic = {}
        self.texture_dic = {}
        for k in V_Types.Material_MToon.float_props_exchange_dic.values():
            if k is not None:
                self.float_dic[k] = self.get_value(k)
        for k in V_Types.Material_MToon.vector_base_props_exchange_dic.values():
            if k is not None:
                self.vector_dic[k] = self.get_color(k)
        for k in V_Types.Material_MToon.texture_kind_exchange_dic.values():
            if k is not None:
                self.texture_dic[k] = self.get_texture(k)

        self.maintex = self.get_texture("MainTexture")

        self.shade_shift = self.get_value("ShadeShift")



class glsl_draw_obj():

    toon_vertex_shader = '''
        in vec3 position;
        in vec3 normal;
        in vec2 rawuv;
        out vec4 posa;
        out vec2 uva;
        out vec3 na;
        void main()
        {
            na = normal;
            uva = rawuv;
            gl_Position = vec4(position,1);
            posa = gl_Position;
        }
    '''

    toon_geometry_shader = '''
    layout(triangles) in;
    layout(triangle_strip, max_vertices = 3) out;
    uniform mat4 depthMVP;
    uniform mat4 viewProjectionMatrix;
    uniform mat4 obj_matrix;
    uniform float is_outline;

    in vec4 posa[3];
    in vec2 uva[3];
    in vec3 na[3];

    out vec2 uv;
    out vec3 n;
    out vec4 shadowCoord;
    void main(){

        mat4 biasMat4 = mat4(0.5, 0.0, 0.0, 0.0,
                            0.0, 0.5, 0.0, 0.0,
                            0.0, 0.0, 0.5, 0.0,
                            0.5, 0.5, 0.5, 1.0);
        mat4 depthBiasMVP = biasMat4 * depthMVP;
        
        if (is_outline == 0){
            for (int i = 0 ; i<3 ; i++){
                    uv = uva[i];
                    n = na[i];
                    gl_Position = viewProjectionMatrix * obj_matrix * posa[i];
                    shadowCoord = depthBiasMVP * vec4(obj_matrix * posa[i]);
                    EmitVertex();
            }
             EndPrimitive();
        }
       
        else {
            for (int i = 2 ; i>=0 ; i--){
                uv = uva[i];
                n = na[i]*-1;
                gl_Position = viewProjectionMatrix * obj_matrix * (posa[i] + vec4(na[i],0)*0.01);
                shadowCoord = depthBiasMVP * vec4(obj_matrix * posa[i]);
                EmitVertex();
            }
            EndPrimitive();
        }
    }
    '''

    toon_fragment_shader = '''
        uniform vec3 lightpos;
        uniform mat4 viewProjectionMatrix;
        uniform float is_outline;

        uniform float CutoffRate ;
        uniform float BumpScale ;
        uniform float ReceiveShadowRate ;
        uniform float ShadeShift ;
        uniform float ShadeToony ;
        uniform float RimLightingMix ;
        uniform float RimFresnelPower ;
        uniform float RimLift ;
        uniform float ShadingGradeRate ;
        uniform float LightColorAttenuation ;
        uniform float IndirectLightIntensity ;
        uniform float OutlineWidth ;
        uniform float OutlineScaleMaxDistance ;
        uniform float OutlineLightingMix ;
        uniform float UV_Scroll_X ;
        uniform float UV_Scroll_Y ;
        uniform float UV_Scroll_Rotation ;
        uniform float OutlineWidthMode ;
        uniform float OutlineColorMode ;

        uniform vec4 DiffuseColor;
        uniform vec4 ShadeColor;
        uniform vec4 EmissionColor;
        uniform vec4 RimColor;
        uniform vec4 OutlineColor;

        uniform sampler2D depth_image;
        uniform sampler2D MainTexture ;
        uniform sampler2D ShadeTexture ;
        uniform sampler2D NomalmapTexture ;
        uniform sampler2D ReceiveShadow_Texture ;
        uniform sampler2D ShadingGradeTexture ;
        uniform sampler2D Emission_Texture ;
        uniform sampler2D SphereAddTexture ;
        uniform sampler2D RimTexture ;
        uniform sampler2D OutlineWidthTexture ;
        uniform sampler2D UV_Animation_Mask_Texture ;

        in vec2 uv;
        in vec3 n;
        in vec4 shadowCoord;
        void main()
        {
            float debug_unused_float =
                                    0.00001 *
                                    (CutoffRate
                                    +BumpScale
                                    +ReceiveShadowRate
                                    +ShadeShift
                                    +ShadeToony
                                    +RimLightingMix
                                    +RimFresnelPower
                                    +RimLift
                                    +ShadingGradeRate
                                    +LightColorAttenuation
                                    +IndirectLightIntensity
                                    +OutlineWidth
                                    +OutlineScaleMaxDistance
                                    +OutlineLightingMix
                                    +UV_Scroll_X
                                    +UV_Scroll_Y
                                    +UV_Scroll_Rotation
                                    +OutlineWidthMode
                                    +OutlineColorMode
                                    );
            vec4 debug_unused_tex = 
                            texture( MainTexture,uv) +
                            texture( ShadeTexture,uv) +
                            texture( NomalmapTexture,uv) +
                            texture( ReceiveShadow_Texture,uv) +
                            texture( ShadingGradeTexture,uv) +
                            texture( Emission_Texture,uv) +
                            texture( SphereAddTexture,uv) +
                            texture( RimTexture,uv) +
                            texture( OutlineWidthTexture,uv) +
                            texture( UV_Animation_Mask_Texture,uv);

            vec4 debug_unused_vec4 = vec4(0.00001)*debug_unused_tex*debug_unused_float;
            mat4 debug_unused_mat4 = mat4(0.00001);
            debug_unused_vec4 *= DiffuseColor 
                                 + ShadeColor
                                 + EmissionColor 
                                 + RimColor 
                                 + OutlineColor;
            debug_unused_vec4 = debug_unused_mat4 * debug_unused_vec4;

            vec3 light_dir = normalize(lightpos);
            vec4 col = texture(MainTexture, uv);
            //if (col.a < 0.5) discard;
            
            float is_shine= 1;
            if (is_outline == 0){
                float bias = 0.2*tan(acos(dot(n,light_dir)));
                if (texture(depth_image,shadowCoord.xy).z < shadowCoord.z - bias){
                    is_shine = 0.5;
                }
                float ss = (ShadeShift +1) /2 ;
                gl_FragColor = vec4(col.rgb*(dot(light_dir,n)+ss)*is_shine,col.a);
            } 
            else{ //is_outline
                gl_FragColor = vec4(0,1,0,1) + debug_unused_vec4;
            }
        }
    '''

    depth_vertex_shader = '''
        in vec3 position;
        uniform mat4 depthMVP;
        uniform mat4 obj_matrix;
        void main()
        {
            gl_Position = depthMVP * obj_matrix * vec4(position,1);
        }
    '''

    depth_fragment_shader = '''
        void main(){
            gl_FragColor = vec4(vec3(gl_FragCoord.z),1);
        }

    '''

    toon_shader = gpu.types.GPUShader(
        vertexcode = toon_vertex_shader,
        fragcode = toon_fragment_shader,
        geocode = toon_geometry_shader)
        
        
    depth_shader = gpu.types.GPUShader(
        vertexcode = depth_vertex_shader,
        fragcode = depth_fragment_shader)

    objs = []
    light = None
    images = []
    offscreen = None
    materials = {}


    def __init__(self,context):
        objs = glsl_draw_obj.objs = [obj for obj in context.selected_objects if obj.type == "MESH"]
        glsl_draw_obj.light = [obj for obj in bpy.data.objects if obj.type == "LIGHT" ][0]
        for ob in objs:
            for mat_slot in ob.material_slots:
                if mat_slot.material.name not in glsl_draw_obj.materials.keys():
                    glsl_draw_obj.materials[mat_slot.material.name] = MToon_glsl(mat_slot.material)
        self.build_sub_index(None)
        self.build_batches()
        glsl_draw_obj.offscreen = gpu.types.GPUOffScreen(2048,2048)

    class gl_mesh():
        pos = []
        normals = []
        uvs = []
        sub_index = {} #mat_index:verices index
        index_per_mat = {} #matrial : vert index
    scene_meshes = None
    @staticmethod
    def build_sub_index(dum):
        glsl_draw_obj.scene_meshes = []
        vertex_count = 0
        for obj in glsl_draw_obj.objs:
            scene_mesh = glsl_draw_obj.gl_mesh()
            ob_eval = obj.evaluated_get(bpy.context.view_layer.depsgraph)
            tmp_mesh = ob_eval.to_mesh()
            tmp_mesh.calc_loop_triangles()
            st = tmp_mesh.uv_layers[0].data
            for tri in tmp_mesh.loop_triangles:
                for lo in tri.loops:
                    scene_mesh.uvs.append([st[lo].uv[0],st[lo].uv[1]])
                for vid in tri.vertices:
                    co = list(tmp_mesh.vertices[vid].co)
                    scene_mesh.pos.append(co)
                    scene_mesh.normals.append(list(tmp_mesh.vertices[vid].normal))   
                key_mat = glsl_draw_obj.materials[obj.material_slots[tri.material_index].material.name] 
                if key_mat in scene_mesh.index_per_mat.keys():
                    scene_mesh.index_per_mat[key_mat].append([vertex_count,vertex_count+1,vertex_count+2])
                else:
                    scene_mesh.index_per_mat[key_mat] = [[vertex_count,vertex_count+1,vertex_count+2]]
                vertex_count +=3
            glsl_draw_obj.scene_meshes.append(scene_mesh)

        return

    batchs = []
    def build_batches(self):
        batchs = glsl_draw_obj.batchs
        
        for scene_mesh in glsl_draw_obj.scene_meshes:
            for mat, vert_indices in scene_mesh.index_per_mat.items():
                toon_batch = batch_for_shader(self.toon_shader, 'TRIS', {
                    "position": scene_mesh.pos,
                    "normal":scene_mesh.normals,
                    "rawuv":scene_mesh.uvs
                    },
                    indices = vert_indices
                )
                depth_batch = batch_for_shader(self.depth_shader, 'TRIS', {
                    "position": scene_mesh.pos
                    },
                    indices = vert_indices
                )            
                if mat.alpha_method in ("OPAQUE",'CLIP'):
                    batchs.append((mat,toon_batch,depth_batch))
                else:
                    batchs.insert(0,(mat,toon_batch,depth_batch))         
    
    @staticmethod
    def glsl_draw():

        model_offset = Matrix.Translation((2,0,0))

        batchs = glsl_draw_obj.batchs
        depth_shader = glsl_draw_obj.depth_shader
        toon_shader = glsl_draw_obj.toon_shader
        offscreen = glsl_draw_obj.offscreen
        #need bone etc changed only update
        depth_matrix = None
        #region shader depth path
        with offscreen.bind():
            bgl.glClearColor(0,0,0,1)
            bgl.glClear(bgl.GL_COLOR_BUFFER_BIT | bgl.GL_DEPTH_BUFFER_BIT)
            for bat in batchs:
                mat = bat[0]
                mat.update()
                depth_bat = bat[2]
                depth_shader.bind()
                bgl.glEnable(bgl.GL_DEPTH_TEST)
                bgl.glEnable(bgl.GL_BLEND)
                if mat.alpha_method == "TRANSPARENT":
                    bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
                    bgl.glDepthMask(bgl.GL_FALSE)
                elif mat.alpha_method in ("OPAQUE",'CLIP') :
                    bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ZERO)
                    bgl.glDepthMask(bgl.GL_TRUE)
                if mat.cull_mode == "BACK":
                    bgl.glEnable(bgl.GL_CULL_FACE)
                    bgl.glCullFace(bgl.GL_BACK)
                else :
                    bgl.glDisable(bgl.GL_CULL_FACE)  
                bgl.glEnable(bgl.GL_CULL_FACE) #そも輪郭線がの影は落ちる？
                bgl.glCullFace(bgl.GL_BACK) 

                light = glsl_draw_obj.light
                light_lookat = light.rotation_euler.to_quaternion() @ Vector((0,0,-1))
                loc = [0,0,0]
                tar = light_lookat.normalized()
                up = light.rotation_euler.to_quaternion() @ Vector((0,1,0))
                v_matrix = lookat_cross(loc,tar,up)
                const_proj = 0.3
                p_matrix = ortho_proj_mat(
                    -const_proj*10, 10*const_proj,
                    -const_proj*10, 10*const_proj,
                    -const_proj*10, const_proj*10)        
                depth_matrix = v_matrix @ p_matrix #reuse in main shader
                depth_matrix.transpose()
                depth_shader.uniform_float("obj_matrix",model_offset)#obj.matrix_world)
                depth_shader.uniform_float("depthMVP", depth_matrix)

                depth_bat.draw(depth_shader)
        #endregion shader depth path

        #region shader main
        for is_outline in [0,1]:
            for bat in batchs:        
                
                toon_bat = bat[1]
                toon_shader.bind()
                mat = bat[0]
                mat.update()

                bgl.glEnable(bgl.GL_DEPTH_TEST)
                bgl.glEnable(bgl.GL_BLEND)
                if mat.alpha_method == "TRANSPARENT":
                    bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
                    bgl.glDepthMask(bgl.GL_FALSE)
                elif mat.alpha_method in ("OPAQUE",'CLIP') :
                    bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ZERO)
                    bgl.glDepthMask(bgl.GL_TRUE)
                if is_outline == 0:
                    if mat.cull_mode == "BACK":
                        bgl.glEnable(bgl.GL_CULL_FACE)
                        bgl.glCullFace(bgl.GL_BACK)
                    else :
                        bgl.glDisable(bgl.GL_CULL_FACE)
                else:
                    bgl.glEnable(bgl.GL_CULL_FACE)
                    bgl.glCullFace(bgl.GL_BACK)
                matrix = bpy.context.region_data.perspective_matrix
                
                toon_shader.uniform_float("obj_matrix",model_offset)#obj.matrix_world)
                toon_shader.uniform_float("viewProjectionMatrix", matrix)
                toon_shader.uniform_float("depthMVP", depth_matrix)
                toon_shader.uniform_float("lightpos", glsl_draw_obj.light.location)
                toon_shader.uniform_float("is_outline", is_outline)
                

                float_keys = [  "CutoffRate" ,
                                "BumpScale" ,
                                "ReceiveShadowRate" ,
                                "ShadeShift",
                                "ShadeToony" ,
                                "RimLightingMix" ,
                                "RimFresnelPower" ,
                                "RimLift" ,
                                "ShadingGradeRate" ,
                                "LightColorAttenuation" ,
                                "IndirectLightIntensity" ,
                                "OutlineWidth" ,
                                "OutlineScaleMaxDistance" ,
                                "OutlineLightingMix" ,
                                "UV_Scroll_X" ,
                                "UV_Scroll_Y" ,
                                "UV_Scroll_Rotation" ,
                                "OutlineWidthMode" ,
                                "OutlineColorMode" ]
                
                for k in float_keys:
                    toon_shader.uniform_float(k,mat.float_dic[k])
                
                toon_shader.uniform_float("DiffuseColor",(0,0,3,1))
                toon_shader.uniform_float("ShadeColor",(0,0,0,0))
                toon_shader.uniform_float("EmissionColor",(0,0,0,0))
                toon_shader.uniform_float("RimColor",(0,0,0,0))
                toon_shader.uniform_float("OutlineColor",(0,0,0,0))

                bgl.glActiveTexture(bgl.GL_TEXTURE0)
                bgl.glBindTexture(bgl.GL_TEXTURE_2D, offscreen.color_texture)
                toon_shader.uniform_int("depth_image",0)

                for i,k in enumerate(mat.texture_dic.keys()):
                    bgl.glActiveTexture(bgl.GL_TEXTURE1 + i)
                    texture = mat.texture_dic[k]
                    if texture is not None:
                        bgl.glBindTexture(bgl.GL_TEXTURE_2D,texture.bindcode)
                    toon_shader.uniform_int(k,i+1)

                toon_bat.draw(toon_shader)
        #endregion shader main

    draw_func = None
    build_mesh_func = None
    @staticmethod
    def draw_func_add():
        if glsl_draw_obj.draw_func is not None:
            glsl_draw_obj.draw_func_remove()
        glsl_draw_obj.draw_func = bpy.types.SpaceView3D.draw_handler_add(
            glsl_draw_obj.glsl_draw,
            (), 'WINDOW', 'POST_PIXEL')

        if glsl_draw_obj.build_mesh_func is not None \
                and glsl_draw_obj.build_mesh_func in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(glsl_draw_obj.build_mesh_func)
        bpy.app.handlers.depsgraph_update_post.append(glsl_draw_obj.build_sub_index)
        glsl_draw_obj.build_mesh_func = bpy.app.handlers.depsgraph_update_post[-1]
        #bpy.app.handlers.frame_change_post.append(build_sub_index)

    @staticmethod
    def draw_func_remove():
        if glsl_draw_obj.draw_func is not None:
            bpy.types.SpaceView3D.draw_handler_remove(
                glsl_draw_obj.draw_func, 'WINDOW')
            glsl_draw_obj.draw_func = None

        if glsl_draw_obj.build_mesh_func is not None \
                and glsl_draw_obj.build_mesh_func in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(glsl_draw_obj.build_mesh_func)
            glsl_draw_obj.build_mesh_func = None


    #endregion 3Dview drawer

#region util func
def ortho_proj_mat(left,right,bottom,top,near,far):
    mat4 = Matrix.Identity(4)
    mat4[0][0] = 2 / (right-left)
    mat4[1][1] = 2 / (top-bottom)
    mat4[2][2] = -2 / (far-near)
    def tmpfunc(a,b):
        return - (a+b)/(a-b)
    mat4[3][0] = tmpfunc(right,left)
    mat4[3][1] = tmpfunc(top,bottom)
    mat4[3][2] = tmpfunc(far,near)
    mat4[3][3] = 1
    return mat4

def lookat_cross(loc,tar,up):
    l = Vector(loc)
    t = Vector(tar)
    u = Vector(up)
    z = l-t
    z.normalize()
    x = u.cross(z)
    x.normalize()
    y = z.cross(x)
    y.normalize()
    n = [-(x.dot(l)),-(y.dot(l)),-(z.dot(l)) ]
    mat4 = Matrix.Identity(4)
    for i in range(3):
        mat4[i][0] = x[i]
        mat4[i][1] = y[i]
        mat4[i][2] = z[i]
        mat4[3][i] = n[i]
    return mat4