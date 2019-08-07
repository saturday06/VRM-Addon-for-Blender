import bpy
import gpu
import bgl
from mathutils import Matrix,Vector,Euler
from math import sqrt,radians
from gpu_extras.batch import batch_for_shader


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
    layout(triangle_strip, max_vertices = 6) out;
    uniform mat4 depthMVP;
    uniform mat4 viewProjectionMatrix;
    uniform mat4 obj_matrix;

    in vec4 posa[3];
    in vec2 uva[3];
    in vec3 na[3];

    out vec2 uv;
    out vec3 n;
    out vec4 shadowCoord;
    flat out int is_outline;
    void main(){

        mat4 biasMat4 = mat4(0.5, 0.0, 0.0, 0.0,
                            0.0, 0.5, 0.0, 0.0,
                            0.0, 0.0, 0.5, 0.0,
                            0.5, 0.5, 0.5, 1.0);
        mat4 depthBiasMVP = biasMat4 * depthMVP;
        
            
        for (int i = 0 ; i<3 ; i++){
                uv = uva[i];
                n = na[i];
                gl_Position = viewProjectionMatrix * obj_matrix * posa[i];
                is_outline = 0;
                shadowCoord = depthBiasMVP * vec4(obj_matrix * posa[i]);
                EmitVertex();
            }
        EndPrimitive();
        for (int i = 2 ; i>=0 ; i--){
                uv = uva[i];
                n = na[i]*-1;
                gl_Position = viewProjectionMatrix * obj_matrix * (posa[i] + vec4(na[i],0)*0.01);
                is_outline = 1;
                shadowCoord = depthBiasMVP * vec4(obj_matrix * posa[i]);
                EmitVertex();
            }
        EndPrimitive();
    }
    '''

    toon_fragment_shader = '''
        uniform vec3 lightpos;
        uniform float lighting_shift;
        uniform mat4 viewProjectionMatrix;

        uniform sampler2D image;
        uniform sampler2D depth_image;
        in vec2 uv;
        in vec3 n;
        in vec4 shadowCoord;
        flat in int is_outline;

        void main()
        {
            vec3 light_dir = normalize(lightpos);
            vec4 col = texture(image, uv);
            //if (col.a < 0.5) discard;
            
            float is_shine= 1;
            if (is_outline == 0){
                float bias = 0.2*tan(acos(dot(n,light_dir)));
                if (texture(depth_image,shadowCoord.xy).z < shadowCoord.z - bias){
                    gl_FragColor = vec4(1,0,0,1);
                    
                }
                else {
                    gl_FragColor = vec4(col.rgb*(dot(light_dir,n)+lighting_shift)*is_shine,col.a);
                }
            }
            else{
                gl_FragColor = vec4(0,1,0,1);
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

    obj = None
    images = []
    offscreen = None
    def __init__(self,context):
        obj = glsl_draw_obj.obj  = bpy.data.objects['Face.baked']
        for mat_slot in obj.material_slots:
            img = mat_slot.material.node_tree.nodes["Image Texture"].image
            glsl_draw_obj.images.append(img)
            img.gl_load() # if faliled return false
        self.build_sub_index(None)
        self.build_batches()
        glsl_draw_obj.offscreen = gpu.types.GPUOffScreen(2048,2048)

    class gl_mesh():
        pos = []
        normals = []
        uvs = []
        sub_index = {} #mat_index:verices index
    ho = gl_mesh()

    @staticmethod
    def build_sub_index(dum):
        ob_eval = glsl_draw_obj.obj.evaluated_get(bpy.context.view_layer.depsgraph)
        mesh = ob_eval.to_mesh()
        mesh.calc_loop_triangles()
        st = mesh.uv_layers["TEXCOORD_0"].data
        vertex_count = 0
        for tri in mesh.loop_triangles:
            for l in tri.loops:
                glsl_draw_obj.ho.uvs.append([st[l].uv[0],st[l].uv[1]])
            for vid in tri.vertices:
                co = list(mesh.vertices[vid].co)
                glsl_draw_obj.ho.pos.append(co )
                glsl_draw_obj.ho.normals.append(list(mesh.vertices[vid].normal))    
            if tri.material_index in glsl_draw_obj.ho.sub_index.keys():
                glsl_draw_obj.ho.sub_index[tri.material_index].append([vertex_count,vertex_count+1,vertex_count+2])
            else:
                glsl_draw_obj.ho.sub_index[tri.material_index] = [[vertex_count,vertex_count+1,vertex_count+2]]
            vertex_count +=3
        return

    batches = []
    def build_batches(self):
        batchs = glsl_draw_obj.batches
        for mat_index,vert_indices in glsl_draw_obj.ho.sub_index.items():
            maintex_id = glsl_draw_obj.images[mat_index].bindcode
            toon_batch = batch_for_shader(self.toon_shader, 'TRIS', {
                "position": glsl_draw_obj.ho.pos,
                "normal":glsl_draw_obj.ho.normals,
                "rawuv":glsl_draw_obj.ho.uvs
                },
                indices = vert_indices
            )
            depth_batch = batch_for_shader(self.depth_shader, 'TRIS', {
                "position": glsl_draw_obj.ho.pos
                },
                indices = vert_indices
            )
            if glsl_draw_obj.obj.material_slots[mat_index].material.blend_method in ("OPAQUE",'CLIP'):
                batchs.append((maintex_id,toon_batch,"O",depth_batch))
            else:
                batchs.insert(0,(maintex_id,toon_batch,"T",depth_batch))
            
       
    @staticmethod
    def glsl_draw():
        batchs = glsl_draw_obj.batches
        depth_shader = glsl_draw_obj.depth_shader
        toon_shader = glsl_draw_obj.toon_shader
        obj = glsl_draw_obj.obj
        offscreen = glsl_draw_obj.offscreen
        #need bone etc changed only update
        depth_matrix = None
        #-----------shade path -----------
        with offscreen.bind():
        #if True:
            bgl.glClearColor(0,0,0,1)
            bgl.glClear(bgl.GL_COLOR_BUFFER_BIT | bgl.GL_DEPTH_BUFFER_BIT)
            for bat in batchs:        
                depth_bat = bat[3]
                depth_shader.bind()
                bgl.glEnable(bgl.GL_DEPTH_TEST)
                bgl.glEnable(bgl.GL_BLEND)
                if bat[2] == "T":
                    bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
                    bgl.glDepthMask(bgl.GL_FALSE)
                elif bat[2] == "O" :
                    bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ZERO)
                    bgl.glDepthMask(bgl.GL_TRUE)
                bgl.glEnable(bgl.GL_CULL_FACE);
                bgl.glCullFace(bgl.GL_BACK)        

                light = bpy.data.objects["Light"]
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
                depth_shader.uniform_float("obj_matrix",obj.matrix_world)
                depth_shader.uniform_float("depthMVP", depth_matrix)

                depth_bat.draw(depth_shader)  
            """buff = bgl.Buffer(bgl.GL_BYTE,2048*2048*4)
            bgl.glReadBuffer(bgl.GL_BACK)
            bgl.glReadPixels(0, 0, 2048, 2048, bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, buff)
            imgname = "x"
            if not imgname in bpy.data.images:
                bpy.data.images.new(imgname, 2048, 2048)
            iop = bpy.data.images[imgname]
            iop.scale(2048, 2048)
            iop.pixels = [v for v in buff]"""
            
        #-------shader main------------------
        for bat in batchs:        
            
            toon_bat = bat[1]
            toon_shader.bind()
            
            bgl.glActiveTexture(bgl.GL_TEXTURE0)
            bgl.glBindTexture(bgl.GL_TEXTURE_2D, offscreen.color_texture)
            bgl.glActiveTexture(bgl.GL_TEXTURE1)
            bgl.glBindTexture(bgl.GL_TEXTURE_2D, bat[0])
            bgl.glEnable(bgl.GL_DEPTH_TEST)
            bgl.glEnable(bgl.GL_BLEND)
            if bat[2] == "T":
                bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
                bgl.glDepthMask(bgl.GL_FALSE)
            elif bat[2] == "O" :
                bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ZERO)
                bgl.glDepthMask(bgl.GL_TRUE)
            bgl.glEnable(bgl.GL_CULL_FACE);
            bgl.glCullFace(bgl.GL_BACK)
            matrix = bpy.context.region_data.perspective_matrix
            
            toon_shader.uniform_float("obj_matrix",obj.matrix_world)
            toon_shader.uniform_float("viewProjectionMatrix", matrix)
            toon_shader.uniform_float("depthMVP", depth_matrix)
            toon_shader.uniform_float("lightpos", bpy.data.objects["Light"].location)
            toon_shader.uniform_float("lighting_shift",bpy.data.objects["Empty"].location[0])
            toon_shader.uniform_int("depth_image",0)
            toon_shader.uniform_int("image",1)

            toon_bat.draw(toon_shader)

        #bgl.glClear(bgl.GL_COLOR_BUFFER_BIT | bgl.GL_DEPTH_BUFFER_BIT)
    def draw_register():
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')
        bpy.app.handlers.depsgraph_update_post.append(build_sub_index)
        #bpy.app.handlers.frame_change_post.append(build_sub_index)
    draw_func = None

    @staticmethod
    def draw_func_add():
        if glsl_draw_obj.draw_func is not None:
            glsl_draw_obj.draw_func_remove()
        glsl_draw_obj.draw_func = bpy.types.SpaceView3D.draw_handler_add(
            glsl_draw_obj.glsl_draw,
            (), 'WINDOW', 'POST_PIXEL')

    @staticmethod
    def draw_func_remove():
        if glsl_draw_obj.draw_func is not None:
            bpy.types.SpaceView3D.draw_handler_remove(
                glsl_draw_obj.draw_func, 'WINDOW')
            glsl_draw_obj.draw_func = None
    

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