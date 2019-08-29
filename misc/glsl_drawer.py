import bpy
import gpu
import bgl

from mathutils import Matrix,Vector,Euler
from math import sqrt,radians
import collections 
from gpu_extras.batch import batch_for_shader
from .. import V_Types

class ICYP_OT_Draw_Model(bpy.types.Operator):
    bl_idname = "vrm.model_draw"
    bl_label = "Preview MToon"
    bl_description = "Draw selected with MToon of GLSL"
    bl_options = {'REGISTER'}

    def execute(self,context):
        gdo = glsl_draw_obj()
        glsl_draw_obj.draw_func_add()
        return {"FINISHED"}
class ICYP_OT_Remove_Draw_Model(bpy.types.Operator):
    bl_idname = "vrm.model_draw_remove"
    bl_label = "remove MToon preview"
    bl_description = "remove draw function"
    bl_options = {'REGISTER'}

    def execute(self,context):
        glsl_draw_obj.draw_func_remove()
        return {"FINISHED"}

class MToon_glsl():
    white_texture = None
    black_texture = None
    normal_texture = None
    material = None
    main_node = None
    name = None
    alpha_method = None

    float_dic = {}
    vector_dic = {}
    texture_dic = {}
    cull_mode = "BACK"
    def make_small_image(self,name,color = (1,1,1,1),color_space = "sRGB"):
        image = bpy.data.images.new(name,1,1)
        image.colorspace_settings.name = color_space
        image.generated_color = color
        return image
    def __init__(self,material):
        shader_black = "shader_black"
        if shader_black not in bpy.data.images:
            self.black_texture = self.make_small_image(shader_black,(0,0,0,0))
        else :
            self.black_texture = bpy.data.images[shader_black]
        shader_white = "shader_white"
        if shader_white not in bpy.data.images:
            self.white_texture = self.make_small_image(shader_white,(1,1,1,1))
        else :
            self.white_texture = bpy.data.images[shader_white]
        shader_normal = "shader_normal"
        if shader_normal not in bpy.data.images:
            self.normal_texture = self.make_small_image(shader_normal,(0.5,0.5,1,1),"Linear")
        else :
            self.normal_texture = bpy.data.images[shader_normal]
        self.material = material
        self.name = material.name
        self.update()

        
    def get_texture(self,tex_name,default_color = "white"):
        if tex_name == "ReceiveShadow_Texture":
            tex_name += "_alpha"
        if self.main_node.inputs[tex_name].links:
            if self.main_node.inputs[tex_name].links[0].from_node.image is not None:
                if default_color != "normal" and \
                        self.main_node.inputs[tex_name].links[0].from_node.image.colorspace_settings.name != "Linear": ###############TODO bugyyyyyyyyyyyyyyyyy
                    self.main_node.inputs[tex_name].links[0].from_node.image.colorspace_settings.name = "Linear"
                self.main_node.inputs[tex_name].links[0].from_node.image.gl_load()
                return self.main_node.inputs[tex_name].links[0].from_node.image
            else:
                if default_color == "white":
                    self.white_texture.gl_load()
                    return self.white_texture
                elif default_color == "black":
                    self.black_texture.gl_load()
                    return self.black_texture
                elif default_color == "normal":
                    self.normal_texture.gl_load()
                    return self.normal_texture
                else:
                    raise Exception
        else:
            if default_color == "white":
                self.white_texture.gl_load()
                return self.white_texture
            elif default_color == "black":
                self.black_texture.gl_load()
                return self.black_texture
            elif default_color == "normal":
                self.normal_texture.gl_load()
                return self.normal_texture
            else:
                raise Exception

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
                if k == "SphereAddTexture":
                    self.texture_dic[k] = self.get_texture(k,"black")
                elif k == "NomalmapTexture":
                    self.texture_dic[k] = self.get_texture(k,"normal")
                else:
                    self.texture_dic[k] = self.get_texture(k)




class glsl_draw_obj():

    toon_vertex_shader = '''
        in vec3 position;
        in vec3 normal;
        in vec2 rawuv;
        in vec3 rawtangent;
        out vec4 posa;
        out vec2 uva;
        out vec3 na;
        out vec3 rtangent;
        void main()
        {
            na = normal;
            uva = rawuv;
            gl_Position = vec4(position,1);
            posa = gl_Position;
            rtangent = rawtangent;
        }
    '''

    toon_geometry_shader = '''
    layout(triangles) in;
    layout(triangle_strip, max_vertices = 3) out;
    uniform mat4 depthMVP;
    uniform mat4 projectionMatrix;
    uniform mat4 viewProjectionMatrix;
    uniform mat4 normalWorldToViewMatrix;
    uniform float aspect;
    uniform mat4 obj_matrix;
    uniform float is_outline;
    uniform float OutlineWidthMode ;
    
    uniform float OutlineWidth ;
    uniform float OutlineScaleMaxDistance ;
    uniform sampler2D OutlineWidthTexture ;

    in vec4 posa[3];
    in vec2 uva[3];
    in vec3 na[3];
    in vec3 rtangent[3];

    out vec2 uv;
    out vec3 n;
    out vec3 tangent;
    out vec3 bitangent;
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
                    tangent = rtangent[i];
                    bitangent = normalize(cross(n,tangent));
                    gl_Position = viewProjectionMatrix * obj_matrix * posa[i];
                    shadowCoord = depthBiasMVP * vec4(obj_matrix * posa[i]);
                    EmitVertex();
            }
             EndPrimitive();
        }
       
        else {
            if (OutlineWidthMode == 1){// world space outline
                for (int i = 2 ; i>=0 ; i--){
                    uv = uva[i];
                    n = na[i]*-1;
                    tangent = rtangent[i];
                    float outlinewidth_tex = texture(OutlineWidthTexture,uv).r;
                    gl_Position = viewProjectionMatrix * obj_matrix * (posa[i] + vec4(na[i],0)*OutlineWidth*outlinewidth_tex*0.01);
                    shadowCoord = depthBiasMVP * vec4(obj_matrix * posa[i]);
                    EmitVertex();
                }
                EndPrimitive();
            }
            else if (OutlineWidthMode == 2){ //screen space outline
                for (int i = 2 ; i>=0 ; i--){
                    uv = uva[i];
                    n = na[i]*-1;
                    tangent = rtangent[i];
                    gl_Position = viewProjectionMatrix * obj_matrix * posa[i];
                    vec3 view_normal = normalize(mat3(normalWorldToViewMatrix) * na[i]);
                    vec3 extend_dir = normalize(mat3(projectionMatrix) * view_normal);
                    extend_dir = extend_dir * min(gl_Position.w, OutlineScaleMaxDistance);
                    extend_dir.y = extend_dir.y * aspect; 
                    float outlinewidth_tex = texture(OutlineWidthTexture,uv).r;
                    gl_Position.xy += extend_dir.xy * 0.01 * OutlineWidth * outlinewidth_tex * clamp(1-abs(view_normal.z),0.0,1.0);
                    shadowCoord = depthBiasMVP * vec4(obj_matrix * posa[i]);
                    EmitVertex();
                }
                EndPrimitive();
            }
            else{// nothing come here ...maybe.
                for (int i = 0 ; i<3 ; i++){
                            uv = uva[i];
                            n = na[i];
                            tangent = rtangent[i];
                            bitangent = normalize(cross(n,tangent));
                            gl_Position = viewProjectionMatrix * obj_matrix * posa[i];
                            shadowCoord = depthBiasMVP * vec4(obj_matrix * posa[i]);
                            EmitVertex();
                    }
                EndPrimitive();
            }
        }
    }
    '''

    toon_fragment_shader = '''
        uniform vec3 lightpos;
        uniform vec3 viewDirection;
        uniform mat4 viewProjectionMatrix;
        uniform mat4 normalWorldToViewMatrix;
        uniform float is_outline;
        uniform float is_cutout;

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
        in vec3 tangent;
        in vec3 bitangent;
        in vec4 shadowCoord;
        vec4 color_linearlize(vec4 color){
            vec4 linear_color = color;
            for(int i = 0;i<3;i++){
                if (linear_color[i] <= 0.04045){
                    linear_color[i] = linear_color[i] / 12.92;
                } 
                else{
                    linear_color[i] = pow((linear_color[i]+0.055)/1.055,2.4);
                }
            }
            for(int i = 0;i<3;i++){
                linear_color[i]=pow(color[i],2.2);
            }
            return linear_color;
        }
        vec4 color_sRGBlize(vec4 color){
            vec4 sRGB_color = color;
            for(int i = 0;i<3;i++){
                if (sRGB_color[i] <= 0.0031308){
                    sRGB_color[i] = sRGB_color[i] * 12.92;
                } 
                else{
                    sRGB_color[i] = 1.055 * pow(sRGB_color[i],1.0/2.4) - 0.055;
                }
            }
            for(int i = 0;i<3;i++){
                sRGB_color[i]=pow(color[i],1/2.2);
            }
            return sRGB_color;

        }
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
                            //texture( depth_image,uv) +
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

            vec4 debug_unused_vec4 = vec4(0.00001)*debug_unused_tex*debug_unused_float*shadowCoord;
            mat4 debug_unused_mat4 = mat4(0.00001)*normalWorldToViewMatrix;
            debug_unused_vec4 *= DiffuseColor 
                                 + ShadeColor
                                 + EmissionColor 
                                 + RimColor 
                                 + OutlineColor
                                 + vec4(tangent+bitangent+viewDirection+lightpos,1);
            debug_unused_vec4 = debug_unused_mat4 * debug_unused_vec4;
    

            //start true main
            float const_less_val = 0.00001;
            vec3 light_dir = normalize(lightpos);
            vec2 mainUV = uv;
            vec4 col = texture(MainTexture, mainUV);
            if (is_cutout == 1 && col.a * DiffuseColor.a < CutoffRate) discard;
            
            vec3 output_color = vec3(0,0,0);
            vec3 outline_col = col.rgb;

            vec3 mod_n = n;
            vec3 normalmap = texture(NomalmapTexture,mainUV).rgb *2 -1;
            for (int i = 0;i<3;i++){
                mod_n[i] = dot(vec3(tangent[i],bitangent[i],n[i]),normalmap);
            }
            mod_n = normalize(mod_n);
            float dotNL = dot(light_dir , n);


            float is_shine= dotNL;
            float shadow_bias = 0.02*tan(acos(dot(n,light_dir)));
            if (texture(depth_image,shadowCoord.xy).z < shadowCoord.z - shadow_bias){
                is_shine = 0;
            }



            // Decide albedo color rate from Direct Light
            float shadingGrade = 1 - ShadingGradeRate * (1.0 - texture(ShadingGradeTexture,mainUV).r);
            float lightIntensity = dotNL;
            lightIntensity = lightIntensity * 0.5 + 0.5;
            lightIntensity = lightIntensity * is_shine;
            lightIntensity = lightIntensity * shadingGrade;
            lightIntensity = lightIntensity * 2.0 - 1.0;
            float maxIntensityThreshold = mix(1,ShadeShift,ShadeToony);
            float minIntensityThreshold = ShadeShift;
            float lerplightintensity = (lightIntensity - minIntensityThreshold) / max(const_less_val, (maxIntensityThreshold - minIntensityThreshold));
            lightIntensity = clamp(lerplightintensity,0.0,1.0);

            vec4 lit = color_linearlize(DiffuseColor) * color_linearlize(texture(MainTexture,mainUV));
            vec4 shade = color_linearlize(ShadeColor) * color_linearlize(texture(ShadeTexture,mainUV));
            vec3 albedo = mix(shade.rgb, lit.rgb, lightIntensity);

            output_color = albedo;
            outline_col = albedo;
            
            //Direct light
            vec3 lighting = vec3(1.0);//light color
            lighting = mix( lighting,
                            vec3(max(const_less_val,max(lighting.r,max(lighting.g,lighting.b)))),
                            LightColorAttenuation);
            //lighting *= min(0,dotNL) +1;
            //lighting *= is_shine;
            output_color *= lighting;
            outline_col *= lighting;

            //未実装＠Indirect Light

            //parametric rim
            vec3 p_rim_color = pow(clamp(1.0-dot(n,viewDirection)+RimLift,0.0,1.0),RimFresnelPower) * color_linearlize(RimColor).rgb * color_linearlize(texture(RimTexture,mainUV)).rgb;
            output_color += p_rim_color;
            //matcap
            vec3 view_normal = mat3(normalWorldToViewMatrix) * n;
            vec4 matcap_color = color_linearlize( texture( SphereAddTexture , view_normal.xy * 0.5 + 0.5 ));
            output_color += matcap_color.rgb;

            //emission
            vec3 emission = color_linearlize(texture(Emission_Texture,mainUV)).rgb * color_linearlize(EmissionColor).rgb;
            output_color += emission;


            if (is_outline ==0){
                gl_FragColor = color_sRGBlize(vec4(output_color,lit.a));
            }
            else{ //is_outline in (1,2)//world or screen
                if (OutlineWidthMode == 0){
                    discard;
                    }
                if (OutlineColorMode==0){
                    gl_FragColor = color_sRGBlize(color_linearlize(OutlineColor) + debug_unused_vec4);
                }
                else{
                    gl_FragColor = color_sRGBlize(
                        vec4(
                            color_linearlize(OutlineColor).rgb * 
                            color_linearlize(
                                vec4(mix(vec3(1.0),outline_col,OutlineLightingMix),1)
                            ).rgb
                            ,1
                        )
                    );
                }
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

    toon_shader = None 
        
        
    depth_shader = None 

    objs = []
    light = None
    offscreen = None
    materials = None
    myinstance = None
    draw_objs = []
    shadowmap_res = 2048
    draw_x_offset = 0.3
    bounding_center = [0,0,0]
    bounding_size = [1,1,1]
    def __init__(self):
        glsl_draw_obj.myinstance = self
        self.offscreen = gpu.types.GPUOffScreen(self.shadowmap_res,self.shadowmap_res)
        self.materials = {}
    scene_meshes = None
    def build_scene(scene=None,*args):
        if glsl_draw_obj.myinstance is None and glsl_draw_obj.draw_func is None:
            self = glsl_draw_obj()
        else:
            self = glsl_draw_obj.myinstance
        self.objs = [obj for obj in self.draw_objs if obj is not None]
        self.light = [obj for obj in bpy.data.objects if obj.type == "LIGHT" ][0]
        for obj in self.objs:
            for mat_slot in obj.material_slots:
                if mat_slot.material.name not in self.materials.keys():
                    self.materials[mat_slot.material.name] = MToon_glsl(mat_slot.material)

        self.scene_meshes = []
        self.draw_x_offset = 0
        for obj in self.objs:
            if  self.draw_x_offset < obj.bound_box[4][0]*2:
                self.draw_x_offset = obj.bound_box[4][0]*2
            bounding_box_xyz = [[1,1,1],[-1,-1,-1]]
            for point in obj.bound_box:
                for i,xyz in enumerate(point):
                    if bounding_box_xyz[0][i] < xyz:
                         bounding_box_xyz[0][i] = xyz
                    if bounding_box_xyz[1][i] > xyz:
                         bounding_box_xyz[1][i] = xyz
            self.bounding_center = [(i+n)/2 for i,n in zip(bounding_box_xyz[0],bounding_box_xyz[1])]
            self.bounding_size = [i-n for i,n in zip(bounding_box_xyz[0],bounding_box_xyz[1])]
            scene_mesh = Gl_mesh()
            ob_eval = obj.evaluated_get(bpy.context.view_layer.depsgraph)
            tmp_mesh = ob_eval.to_mesh()
            tmp_mesh.calc_tangents()
            tmp_mesh.calc_loop_triangles()
            st = tmp_mesh.uv_layers[0].data
            
            scene_mesh.index_per_mat = [self.materials[ms.material.name] for ms in obj.material_slots]
            count_list = collections.Counter([tri.material_index for tri in tmp_mesh.loop_triangles])
            scene_mesh.index_per_mat = { scene_mesh.index_per_mat[i]:[(n*3,n*3+1,n*3+2) for n in range(v)] for i,v in count_list.items() }
            scene_mesh.pos = { k:[tmp_mesh.vertices[vid].co for tri in tmp_mesh.loop_triangles for vid in tri.vertices if tri.material_index==i] for i,k in enumerate(scene_mesh.index_per_mat.keys())}
            if tmp_mesh.has_custom_normals:
                scene_mesh.normals = {k:[tri.split_normals[x] for tri in tmp_mesh.loop_triangles if tri.material_index == i for x in range(3)] for i,k in enumerate(scene_mesh.index_per_mat.keys())}
            else:
                scene_mesh.normals = {k:[tmp_mesh.vertices[vid].normal for tri in tmp_mesh.loop_triangles for vid in tri.vertices if tri.material_index == i]for i,k in enumerate(scene_mesh.index_per_mat.keys())}
            scene_mesh.uvs = {k:[st[lo].uv for tri in tmp_mesh.loop_triangles for lo in tri.loops if tri.material_index == i] for i,k in enumerate(scene_mesh.index_per_mat.keys())}
            scene_mesh.tangents = {k:[tmp_mesh.loops[lo].tangent for tri in tmp_mesh.loop_triangles for lo in tri.loops if tri.material_index == i] for i,k in enumerate(scene_mesh.index_per_mat.keys())}

            unneed_mat = []
            for k in scene_mesh.index_per_mat.keys():
                if len(scene_mesh.index_per_mat[k])==0:
                    unneed_mat.append(k)
            for k in unneed_mat:
                del scene_mesh.index_per_mat[k]
            self.scene_meshes.append(scene_mesh)

        self.build_batches()
        return

    batchs = None
    def build_batches(self):
        if self.toon_shader is None:
            self.toon_shader = gpu.types.GPUShader(
                                vertexcode = self.toon_vertex_shader,
                                fragcode = self.toon_fragment_shader,
                                geocode = self.toon_geometry_shader)
                                
        if self.depth_shader is None:
            self.depth_shader = gpu.types.GPUShader(
                                vertexcode = self.depth_vertex_shader,
                                fragcode = self.depth_fragment_shader)

        batchs = self.batchs = []
        for scene_mesh in self.scene_meshes:
            for mat, vert_indices in scene_mesh.index_per_mat.items():
                toon_batch = batch_for_shader(self.toon_shader, 'TRIS', {
                    "position": scene_mesh.pos[mat],
                    "normal":scene_mesh.normals[mat],
                    "rawtangent":scene_mesh.tangents[mat],
                    "rawuv":scene_mesh.uvs[mat]
                    },
                    indices = vert_indices
                )
                depth_batch = batch_for_shader(self.depth_shader, 'TRIS', {
                    "position": scene_mesh.pos[mat]
                    },
                    indices = vert_indices
                )            
                if mat.alpha_method not in ("OPAQUE",'CLIP'):
                    batchs.append((mat,toon_batch,depth_batch))
                else:
                    batchs.insert(0,(mat,toon_batch,depth_batch))      
        return   
    

    def glsl_draw(scene):
        if glsl_draw_obj.myinstance is None and glsl_draw_obj.draw_func is None:
            self = glsl_draw_obj()
            self.build_scene()
        else:
            self = glsl_draw_obj.myinstance
        model_offset = Matrix.Translation((self.draw_x_offset,0,0))
        light_pos = [i + n for i,n in zip(self.light.location , [-self.draw_x_offset,0,0])]
        batchs = self.batchs
        depth_shader = self.depth_shader
        toon_shader = self.toon_shader
        offscreen = self.offscreen
        #need bone etc changed only update
        depth_matrix = None

        light = self.light
        light_lookat = light.rotation_euler.to_quaternion() @ Vector((0,0,-1))
        #TODO このへん
        tar = light_lookat.normalized()
        up = light.rotation_euler.to_quaternion() @ Vector((0,1,0))
        tmp_bound_len = Vector(self.bounding_center).length
        camera_bias = 0.2
        loc = Vector([self.bounding_center[i] + tar[i] * (tmp_bound_len + camera_bias) for i in range(3)])

        loc = model_offset @ loc
        v_matrix = lookat_cross(loc,tar,up)
        const_proj = 2*max(self.bounding_size)/2
        p_matrix = ortho_proj_mat(
            -const_proj, const_proj,
            -const_proj, const_proj,
            -const_proj, const_proj)        
        depth_matrix = v_matrix @ p_matrix #reuse in main shader
        depth_matrix.transpose()

        #region shader depth path
        with offscreen.bind():
            bgl.glClearColor(10,10,10,1)
            bgl.glClear(bgl.GL_COLOR_BUFFER_BIT | bgl.GL_DEPTH_BUFFER_BIT)
            for bat in batchs:
                mat = bat[0]
                mat.update()
                depth_bat = bat[2]
                depth_shader.bind()
                
                bgl.glEnable(bgl.GL_BLEND)
                if mat.alpha_method == "TRANSPARENT":
                    bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
                    bgl.glDepthMask(bgl.GL_TRUE)
                    bgl.glEnable(bgl.GL_DEPTH_TEST)
                elif mat.alpha_method =="OPAQUE" :
                    bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ZERO)
                    bgl.glDepthMask(bgl.GL_TRUE)
                    bgl.glEnable(bgl.GL_DEPTH_TEST)
                elif mat.alpha_method =='CLIP' :
                    bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ZERO)
                    bgl.glDepthMask(bgl.GL_TRUE)
                    bgl.glEnable(bgl.GL_DEPTH_TEST)

                if mat.cull_mode == "BACK":
                    bgl.glEnable(bgl.GL_CULL_FACE)
                    bgl.glCullFace(bgl.GL_BACK)
                else :
                    bgl.glDisable(bgl.GL_CULL_FACE)  
                bgl.glEnable(bgl.GL_CULL_FACE) #そも輪郭線がの影は落ちる？
                bgl.glCullFace(bgl.GL_BACK) 

 
                depth_shader.uniform_float("obj_matrix",model_offset)#obj.matrix_world)
                depth_shader.uniform_float("depthMVP", depth_matrix)

                depth_bat.draw(depth_shader)
        #endregion shader depth path

        #region shader main
        vp_mat = bpy.context.region_data.perspective_matrix
        projection_mat = bpy.context.region_data.window_matrix
        view_dir = bpy.context.region_data.view_matrix[2][:3]
        normalWorldToViewMatrix = bpy.context.region_data.view_matrix.inverted_safe().transposed()
        aspect = bpy.context.area.width/bpy.context.area.height

        for is_outline in [0,1]:
            for bat in batchs:        
                
                toon_bat = bat[1]
                toon_shader.bind()
                mat = bat[0]
                #mat.update() #already in depth path
                bgl.glEnable(bgl.GL_BLEND)
                bgl.glDepthMask(bgl.GL_TRUE)
                bgl.glEnable(bgl.GL_DEPTH_TEST)
                if mat.alpha_method == "TRANSPARENT":
                    bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
                elif mat.alpha_method =="OPAQUE" :
                    bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ZERO)
                elif mat.alpha_method =='CLIP' :
                    bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ZERO)

                if is_outline == 0:
                    if mat.cull_mode == "BACK":
                        bgl.glEnable(bgl.GL_CULL_FACE)
                        bgl.glCullFace(bgl.GL_BACK)
                    else :
                        bgl.glDisable(bgl.GL_CULL_FACE)
                else:
                    bgl.glEnable(bgl.GL_CULL_FACE)
                    bgl.glCullFace(bgl.GL_BACK)
                            
                toon_shader.uniform_float("obj_matrix",model_offset)#obj.matrix_world)
                toon_shader.uniform_float("projectionMatrix",projection_mat)
                toon_shader.uniform_float("viewProjectionMatrix", vp_mat)
                toon_shader.uniform_float("viewDirection", view_dir)
                toon_shader.uniform_float("normalWorldToViewMatrix",normalWorldToViewMatrix)
                toon_shader.uniform_float("depthMVP", depth_matrix)
                toon_shader.uniform_float("lightpos", light_pos)
                toon_shader.uniform_float("aspect",aspect)
                toon_shader.uniform_float("is_outline", is_outline)
                
                toon_shader.uniform_float("is_cutout", 1.0 if mat.alpha_method == "CLIP" else 0.0)

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
                
                for k,v in mat.vector_dic.items():
                    toon_shader.uniform_float(k,v)

                bgl.glActiveTexture(bgl.GL_TEXTURE0)
                bgl.glBindTexture(bgl.GL_TEXTURE_2D, offscreen.color_texture)
                bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_S, bgl.GL_CLAMP_TO_EDGE) #TODO 
                bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_T, bgl.GL_CLAMP_TO_EDGE)
                toon_shader.uniform_int("depth_image",0)

                for i,k in enumerate(mat.texture_dic.keys()):
                    bgl.glActiveTexture(bgl.GL_TEXTURE1 + i)
                    texture = mat.texture_dic[k]
                    bgl.glBindTexture(bgl.GL_TEXTURE_2D,texture.bindcode)
                    bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_S, bgl.GL_CLAMP_TO_EDGE) #TODO 
                    bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_T, bgl.GL_CLAMP_TO_EDGE)
                    toon_shader.uniform_int(k , 1 + i)

                toon_bat.draw(toon_shader)
        #endregion shader main

    draw_func = None
    build_mesh_func = None
    @staticmethod
    def draw_func_add():
        glsl_draw_obj.draw_func_remove()
        glsl_draw_obj.draw_objs = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]
        if glsl_draw_obj.myinstance is None or glsl_draw_obj.draw_func is None:
            glsl_draw_obj.myinstance = glsl_draw_obj()     
        glsl_draw_obj.myinstance.build_scene()
        if glsl_draw_obj.draw_func is not None:
            glsl_draw_obj.draw_func_remove()
        glsl_draw_obj.draw_func = bpy.types.SpaceView3D.draw_handler_add(
            glsl_draw_obj.myinstance.glsl_draw,
            (), 'WINDOW', 'POST_PIXEL')

        if glsl_draw_obj.build_mesh_func is not None \
                and glsl_draw_obj.build_mesh_func in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(glsl_draw_obj.build_mesh_func)
        bpy.app.handlers.depsgraph_update_post.append(glsl_draw_obj.myinstance.build_scene)
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
        glsl_draw_obj.draw_objs = []

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
    #z = l-t
    z = -t # 注視点ではなく、注視方角だからこう
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

class Gl_mesh():
    pos = None
    normals = None
    uvs = None
    index_per_mat = None #matrial : vert index
    def __init__(self):
        self.pos = []
        self.normals = []
        self.uvs = []
        self.tangents = []
        self.index_per_mat = {}