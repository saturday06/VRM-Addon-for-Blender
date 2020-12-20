import collections
import pathlib
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

import bgl
import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix, Vector

from .. import vrm_types


class ICYP_OT_Draw_Model(bpy.types.Operator):  # noqa: N801
    bl_idname = "vrm.model_draw"
    bl_label = "Preview MToon"
    bl_description = "Draw selected with MToon of GLSL"
    bl_options = {"REGISTER"}

    def execute(self, context):
        GlslDrawObj()
        GlslDrawObj.draw_func_add()
        return {"FINISHED"}


class ICYP_OT_Remove_Draw_Model(bpy.types.Operator):  # noqa: N801
    bl_idname = "vrm.model_draw_remove"
    bl_label = "Remove MToon preview"
    bl_description = "remove draw function"
    bl_options = {"REGISTER"}

    def execute(self, context):
        GlslDrawObj.draw_func_remove()
        return {"FINISHED"}


class MtoonGlsl:
    white_texture = None
    black_texture = None
    normal_texture = None
    material = None
    main_node = None
    name = None
    alpha_method = None

    float_dic = Dict[str, float]
    vector_dic = Dict[str, List[float]]
    texture_dic = Dict[str, bpy.types.Image]
    cull_mode = "BACK"

    def make_small_image(self, name, color=(1, 1, 1, 1), color_space="sRGB"):
        image = bpy.data.images.new(name, 1, 1)
        image.colorspace_settings.name = color_space
        image.generated_color = color
        return image

    def __init__(self, material):
        shader_black = "shader_black"
        if shader_black not in bpy.data.images:
            self.black_texture = self.make_small_image(shader_black, (0, 0, 0, 0))
        else:
            self.black_texture = bpy.data.images[shader_black]
        shader_white = "shader_white"
        if shader_white not in bpy.data.images:
            self.white_texture = self.make_small_image(shader_white, (1, 1, 1, 1))
        else:
            self.white_texture = bpy.data.images[shader_white]
        shader_normal = "shader_normal"
        if shader_normal not in bpy.data.images:
            self.normal_texture = self.make_small_image(
                shader_normal, (0.5, 0.5, 1, 1), "Linear"
            )
        else:
            self.normal_texture = bpy.data.images[shader_normal]
        self.material = material
        self.name = material.name
        self.update()

    def get_texture(self, tex_name, default_color="white"):
        if tex_name == "ReceiveShadow_Texture":
            tex_name += "_alpha"
        links = self.main_node.inputs[tex_name].links
        if links and links[0].from_node.image is not None:
            if (
                default_color != "normal"
                and links[0].from_node.image.colorspace_settings.name != "Linear"
            ):  # TODO bugyyyyyyyyyyyyyyyyy
                links[0].from_node.image.colorspace_settings.name = "Linear"
            links[0].from_node.image.gl_load()
            return links[0].from_node.image
        if default_color == "white":
            self.white_texture.gl_load()
            return self.white_texture
        if default_color == "black":
            self.black_texture.gl_load()
            return self.black_texture
        if default_color == "normal":
            self.normal_texture.gl_load()
            return self.normal_texture
        raise Exception

    def get_value(self, val_name):
        if self.main_node.inputs[val_name].links:
            return (
                self.main_node.inputs[val_name]
                .links[0]
                .from_node.outputs[0]
                .default_value
            )
        return self.main_node.inputs[val_name].default_value

    def get_color(self, vec_name):
        if self.main_node.inputs[vec_name].links:
            return (
                self.main_node.inputs[vec_name]
                .links[0]
                .from_node.outputs[0]
                .default_value
            )
        return self.main_node.inputs[vec_name].default_value

    def update(self):
        if self.material.blend_method in ("OPAQUE", "CLIP"):
            self.alpha_method = self.material.blend_method
        else:
            self.alpha_method = "TRANSPARENT"
        if self.material.use_backface_culling:
            self.cull_mode = "BACK"
        else:
            self.cull_mode = "NO"
        for node in self.material.node_tree.nodes:
            if node.type == "OUTPUT_MATERIAL":
                self.main_node = node.inputs["Surface"].links[0].from_node

        self.float_dic = {}
        self.vector_dic = {}
        self.texture_dic = {}
        for k in vrm_types.MaterialMtoon.float_props_exchange_dic.values():
            if k is not None:
                self.float_dic[k] = self.get_value(k)
        for k in vrm_types.MaterialMtoon.vector_base_props_exchange_dic.values():
            if k is not None:
                self.vector_dic[k] = self.get_color(k)
        for k in vrm_types.MaterialMtoon.texture_kind_exchange_dic.values():
            if k is not None:
                if k == "SphereAddTexture":
                    self.texture_dic[k] = self.get_texture(k, "black")
                elif k == "NomalmapTexture":
                    self.texture_dic[k] = self.get_texture(k, "normal")
                else:
                    self.texture_dic[k] = self.get_texture(k)


class BaseGlslDrawObjForStaticTyping:
    pass


class GlslDrawObj(BaseGlslDrawObjForStaticTyping):
    toon_vertex_shader = (
        pathlib.Path(__file__).with_name("toon.vert.glsl").read_text(encoding="UTF-8")
    )
    toon_geometry_shader = (
        pathlib.Path(__file__).with_name("toon.geom.glsl").read_text(encoding="UTF-8")
    )
    toon_fragment_shader = (
        pathlib.Path(__file__).with_name("toon.frag.glsl").read_text(encoding="UTF-8")
    )
    depth_vertex_shader = (
        pathlib.Path(__file__).with_name("depth.vert.glsl").read_text(encoding="UTF-8")
    )
    depth_fragment_shader = (
        pathlib.Path(__file__).with_name("depth.frag.glsl").read_text(encoding="UTF-8")
    )
    executor = None
    toon_shader = None
    depth_shader = None
    objs = List[BaseGlslDrawObjForStaticTyping]
    light = None
    offscreen = None
    materials = None
    myinstance = None
    draw_objs = List[bpy.types.Object]
    shadowmap_res = 2048
    draw_x_offset = 0.3
    bounding_center = [0, 0, 0]
    bounding_size = [1, 1, 1]

    def __init__(self):
        GlslDrawObj.myinstance = self
        self.offscreen = gpu.types.GPUOffScreen(self.shadowmap_res, self.shadowmap_res)
        self.materials = {}
        self.main_executor = ThreadPoolExecutor()
        self.sub_executor = ThreadPoolExecutor()

    scene_meshes = None

    @staticmethod
    def build_scene(dummy=None):
        if GlslDrawObj.myinstance is None and GlslDrawObj.draw_func is None:
            glsl_draw_obj = GlslDrawObj()
        else:
            glsl_draw_obj = GlslDrawObj.myinstance
        glsl_draw_obj.objs = [obj for obj in glsl_draw_obj.draw_objs if obj is not None]
        lights = [obj for obj in bpy.data.objects if obj.type == "LIGHT"]
        if not lights:
            raise Exception("Please add a light to scene")
        glsl_draw_obj.light = lights[0]
        for obj in glsl_draw_obj.objs:
            for mat_slot in obj.material_slots:
                if mat_slot.material.name not in glsl_draw_obj.materials.keys():
                    glsl_draw_obj.materials[mat_slot.material.name] = MtoonGlsl(
                        mat_slot.material
                    )
        # if bpy.context.mode != 'POSE' or self.scene_meshes == None: #need skin mesh modifier implementation
        glsl_draw_obj.scene_meshes = []
        glsl_draw_obj.draw_x_offset = 0
        for obj in glsl_draw_obj.objs:
            if glsl_draw_obj.draw_x_offset < obj.bound_box[4][0] * 2:
                glsl_draw_obj.draw_x_offset = obj.bound_box[4][0] * 2
            bounding_box_xyz = [[1, 1, 1], [-1, -1, -1]]
            for point in obj.bound_box:
                for i, xyz in enumerate(point):
                    if bounding_box_xyz[0][i] < xyz:
                        bounding_box_xyz[0][i] = xyz
                    if bounding_box_xyz[1][i] > xyz:
                        bounding_box_xyz[1][i] = xyz
            glsl_draw_obj.bounding_center = [
                (i + n) / 2 for i, n in zip(bounding_box_xyz[0], bounding_box_xyz[1])
            ]
            glsl_draw_obj.bounding_size = [
                i - n for i, n in zip(bounding_box_xyz[0], bounding_box_xyz[1])
            ]

        def build_mesh(obj):
            scene_mesh = GlMesh()
            ob_eval = obj.evaluated_get(bpy.context.view_layer.depsgraph)
            tmp_mesh = ob_eval.to_mesh()
            tmp_mesh.calc_tangents()
            tmp_mesh.calc_loop_triangles()
            st = tmp_mesh.uv_layers[0].data

            scene_mesh.mat_list = [
                glsl_draw_obj.materials[ms.material.name] for ms in obj.material_slots
            ]
            count_list = collections.Counter(
                [tri.material_index for tri in tmp_mesh.loop_triangles]
            )
            scene_mesh.index_per_mat = {
                scene_mesh.mat_list[i]: [
                    (n * 3, n * 3 + 1, n * 3 + 2) for n in range(v)
                ]
                for i, v in count_list.items()
            }

            def job_pos():
                return {
                    k: [
                        tmp_mesh.vertices[vid].co
                        for tri in tmp_mesh.loop_triangles
                        for vid in tri.vertices
                        if tri.material_index == i
                    ]
                    for i, k in enumerate(scene_mesh.index_per_mat.keys())
                }

            def job_normal():
                if tmp_mesh.has_custom_normals:
                    return {
                        k: [
                            tri.split_normals[x]
                            for tri in tmp_mesh.loop_triangles
                            if tri.material_index == i
                            for x in range(3)
                        ]
                        for i, k in enumerate(scene_mesh.index_per_mat.keys())
                    }
                return {
                    k: [
                        tmp_mesh.vertices[vid].normal
                        for tri in tmp_mesh.loop_triangles
                        for vid in tri.vertices
                        if tri.material_index == i
                    ]
                    for i, k in enumerate(scene_mesh.index_per_mat.keys())
                }

            def job_uv():
                return {
                    k: [
                        st[lo].uv
                        for tri in tmp_mesh.loop_triangles
                        for lo in tri.loops
                        if tri.material_index == i
                    ]
                    for i, k in enumerate(scene_mesh.index_per_mat.keys())
                }

            def job_tangent():
                return {
                    k: [
                        tmp_mesh.loops[lo].tangent
                        for tri in tmp_mesh.loop_triangles
                        for lo in tri.loops
                        if tri.material_index == i
                    ]
                    for i, k in enumerate(scene_mesh.index_per_mat.keys())
                }

            scene_mesh.pos = glsl_draw_obj.sub_executor.submit(job_pos)
            scene_mesh.normals = glsl_draw_obj.sub_executor.submit(job_normal)
            scene_mesh.uvs = glsl_draw_obj.sub_executor.submit(job_uv)
            scene_mesh.tangents = glsl_draw_obj.sub_executor.submit(job_tangent)

            scene_mesh.pos = scene_mesh.pos.result()
            scene_mesh.normals = scene_mesh.normals.result()
            scene_mesh.uvs = scene_mesh.uvs.result()
            scene_mesh.tangents = scene_mesh.tangents.result()
            return scene_mesh

        meshes = glsl_draw_obj.main_executor.map(build_mesh, glsl_draw_obj.objs)
        for mesh in meshes:
            unneeded_mat = []
            for k in mesh.index_per_mat.keys():
                if len(mesh.index_per_mat[k]) == 0:
                    unneeded_mat.append(k)
            for k in unneeded_mat:
                del mesh.index_per_mat[k]
            glsl_draw_obj.scene_meshes.append(mesh)

        glsl_draw_obj.build_batches()

    batches = None

    def build_batches(self):
        if self.toon_shader is None:
            self.toon_shader = gpu.types.GPUShader(
                vertexcode=self.toon_vertex_shader,
                fragcode=self.toon_fragment_shader,
                geocode=self.toon_geometry_shader,
            )

        if self.depth_shader is None:
            self.depth_shader = gpu.types.GPUShader(
                vertexcode=self.depth_vertex_shader, fragcode=self.depth_fragment_shader
            )

        batches = self.batches = []
        for scene_mesh in self.scene_meshes:
            for mat, vert_indices in scene_mesh.index_per_mat.items():
                toon_batch = batch_for_shader(
                    self.toon_shader,
                    "TRIS",
                    {
                        "position": scene_mesh.pos[mat],
                        "normal": scene_mesh.normals[mat],
                        "rawtangent": scene_mesh.tangents[mat],
                        "rawuv": scene_mesh.uvs[mat],
                    },
                    indices=vert_indices,
                )
                depth_batch = batch_for_shader(
                    self.depth_shader,
                    "TRIS",
                    {"position": scene_mesh.pos[mat]},
                    indices=vert_indices,
                )
                if mat.alpha_method not in ("OPAQUE", "CLIP"):
                    batches.append((mat, toon_batch, depth_batch))
                else:
                    batches.insert(0, (mat, toon_batch, depth_batch))

    def glsl_draw(self):
        if GlslDrawObj.myinstance is None and GlslDrawObj.draw_func is None:
            glsl_draw_obj = GlslDrawObj()
            glsl_draw_obj.build_scene()
        else:
            glsl_draw_obj = GlslDrawObj.myinstance
        model_offset = Matrix.Translation((glsl_draw_obj.draw_x_offset, 0, 0))
        light_pos = [
            i + n
            for i, n in zip(
                glsl_draw_obj.light.location, [-glsl_draw_obj.draw_x_offset, 0, 0]
            )
        ]
        batches = glsl_draw_obj.batches
        depth_shader = glsl_draw_obj.depth_shader
        toon_shader = glsl_draw_obj.toon_shader
        offscreen = glsl_draw_obj.offscreen
        # need bone etc changed only update
        depth_matrix = None

        light = glsl_draw_obj.light
        light_lookat = light.rotation_euler.to_quaternion() @ Vector((0, 0, -1))
        # TODO このへん
        tar = light_lookat.normalized()
        up = light.rotation_euler.to_quaternion() @ Vector((0, 1, 0))
        tmp_bound_len = Vector(glsl_draw_obj.bounding_center).length
        camera_bias = 0.2
        loc = Vector(
            [
                glsl_draw_obj.bounding_center[i]
                + tar[i] * (tmp_bound_len + camera_bias)
                for i in range(3)
            ]
        )

        loc = model_offset @ loc
        v_matrix = lookat_cross(loc, tar, up)
        const_proj = 2 * max(glsl_draw_obj.bounding_size) / 2
        p_matrix = ortho_proj_mat(
            -const_proj, const_proj, -const_proj, const_proj, -const_proj, const_proj
        )
        depth_matrix = v_matrix @ p_matrix  # reuse in main shader
        depth_matrix.transpose()

        # region shader depth path
        with offscreen.bind():
            bgl.glClearColor(10, 10, 10, 1)
            bgl.glClear(bgl.GL_COLOR_BUFFER_BIT | bgl.GL_DEPTH_BUFFER_BIT)
            for bat in batches:
                mat = bat[0]
                mat.update()
                depth_bat = bat[2]
                depth_shader.bind()

                bgl.glEnable(bgl.GL_BLEND)
                if mat.alpha_method == "TRANSPARENT":
                    bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
                    bgl.glDepthMask(bgl.GL_TRUE)
                    bgl.glEnable(bgl.GL_DEPTH_TEST)
                elif mat.alpha_method == "OPAQUE":
                    bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ZERO)
                    bgl.glDepthMask(bgl.GL_TRUE)
                    bgl.glEnable(bgl.GL_DEPTH_TEST)
                elif mat.alpha_method == "CLIP":
                    bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ZERO)
                    bgl.glDepthMask(bgl.GL_TRUE)
                    bgl.glEnable(bgl.GL_DEPTH_TEST)

                if mat.cull_mode == "BACK":
                    bgl.glEnable(bgl.GL_CULL_FACE)
                    bgl.glCullFace(bgl.GL_BACK)
                else:
                    bgl.glDisable(bgl.GL_CULL_FACE)
                bgl.glEnable(bgl.GL_CULL_FACE)  # そも輪郭線がの影は落ちる?
                bgl.glCullFace(bgl.GL_BACK)

                depth_shader.uniform_float(
                    "obj_matrix", model_offset
                )  # obj.matrix_world)
                depth_shader.uniform_float("depthMVP", depth_matrix)

                depth_bat.draw(depth_shader)
        # endregion shader depth path

        # region shader main
        vp_mat = bpy.context.region_data.perspective_matrix
        projection_mat = bpy.context.region_data.window_matrix
        view_dir = bpy.context.region_data.view_matrix[2][:3]
        view_up = bpy.context.region_data.view_matrix[1][:3]
        normal_world_to_view_matrix = (
            bpy.context.region_data.view_matrix.inverted_safe().transposed()
        )
        aspect = bpy.context.area.width / bpy.context.area.height

        for is_outline in [0, 1]:
            for bat in batches:

                toon_bat = bat[1]
                toon_shader.bind()
                mat = bat[0]

                if is_outline == 1 and mat.float_dic["OutlineWidthMode"] == 0:
                    continue
                # mat.update() #already in depth path
                bgl.glEnable(bgl.GL_BLEND)
                bgl.glDepthMask(bgl.GL_TRUE)
                bgl.glEnable(bgl.GL_DEPTH_TEST)
                if mat.alpha_method == "TRANSPARENT":
                    bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
                elif mat.alpha_method == "OPAQUE":
                    bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ZERO)
                elif mat.alpha_method == "CLIP":
                    bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ZERO)

                if is_outline == 0:
                    if mat.cull_mode == "BACK":
                        bgl.glEnable(bgl.GL_CULL_FACE)
                        bgl.glCullFace(bgl.GL_BACK)
                    else:
                        bgl.glDisable(bgl.GL_CULL_FACE)
                else:
                    bgl.glEnable(bgl.GL_CULL_FACE)
                    bgl.glCullFace(bgl.GL_BACK)

                toon_shader.uniform_float(
                    "obj_matrix", model_offset
                )  # obj.matrix_world)
                toon_shader.uniform_float("projectionMatrix", projection_mat)
                toon_shader.uniform_float("viewProjectionMatrix", vp_mat)
                toon_shader.uniform_float("viewDirection", view_dir)
                toon_shader.uniform_float("viewUpDirection", view_up)
                toon_shader.uniform_float(
                    "normalWorldToViewMatrix", normal_world_to_view_matrix
                )
                toon_shader.uniform_float("depthMVP", depth_matrix)
                toon_shader.uniform_float("lightpos", light_pos)
                toon_shader.uniform_float("aspect", aspect)
                toon_shader.uniform_float("is_outline", is_outline)
                toon_shader.uniform_float("isDebug", 0.0)

                toon_shader.uniform_float(
                    "is_cutout", 1.0 if mat.alpha_method == "CLIP" else 0.0
                )

                float_keys = [
                    "CutoffRate",
                    "BumpScale",
                    "ReceiveShadowRate",
                    "ShadeShift",
                    "ShadeToony",
                    "RimLightingMix",
                    "RimFresnelPower",
                    "RimLift",
                    "ShadingGradeRate",
                    "LightColorAttenuation",
                    "IndirectLightIntensity",
                    "OutlineWidth",
                    "OutlineScaleMaxDistance",
                    "OutlineLightingMix",
                    "UV_Scroll_X",
                    "UV_Scroll_Y",
                    "UV_Scroll_Rotation",
                    "OutlineWidthMode",
                    "OutlineColorMode",
                ]

                for k in float_keys:
                    toon_shader.uniform_float(k, mat.float_dic[k])

                for k, v in mat.vector_dic.items():
                    toon_shader.uniform_float(k, v)

                bgl.glActiveTexture(bgl.GL_TEXTURE0)
                bgl.glBindTexture(bgl.GL_TEXTURE_2D, offscreen.color_texture)
                bgl.glTexParameteri(
                    bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_S, bgl.GL_CLAMP_TO_EDGE
                )  # TODO
                bgl.glTexParameteri(
                    bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_T, bgl.GL_CLAMP_TO_EDGE
                )
                toon_shader.uniform_int("depth_image", 0)

                for i, k in enumerate(mat.texture_dic.keys()):
                    bgl.glActiveTexture(bgl.GL_TEXTURE1 + i)
                    texture = mat.texture_dic[k]
                    bgl.glBindTexture(bgl.GL_TEXTURE_2D, texture.bindcode)
                    bgl.glTexParameteri(
                        bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_S, bgl.GL_CLAMP_TO_EDGE
                    )  # TODO
                    bgl.glTexParameteri(
                        bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_T, bgl.GL_CLAMP_TO_EDGE
                    )
                    toon_shader.uniform_int(k, 1 + i)

                toon_bat.draw(toon_shader)
        # endregion shader main

    draw_func = None
    build_mesh_func = None

    @staticmethod
    def draw_func_add():
        GlslDrawObj.draw_func_remove()
        GlslDrawObj.draw_objs = [
            obj for obj in bpy.context.selected_objects if obj.type == "MESH"
        ]
        if GlslDrawObj.myinstance is None or GlslDrawObj.draw_func is None:
            GlslDrawObj.myinstance = GlslDrawObj()
        GlslDrawObj.build_scene()
        if GlslDrawObj.draw_func is not None:
            GlslDrawObj.draw_func_remove()
        GlslDrawObj.draw_func = bpy.types.SpaceView3D.draw_handler_add(
            GlslDrawObj.myinstance.glsl_draw, (), "WINDOW", "POST_PIXEL"
        )

        if (
            GlslDrawObj.build_mesh_func is not None
            and GlslDrawObj.build_mesh_func in bpy.app.handlers.depsgraph_update_post
        ):
            bpy.app.handlers.depsgraph_update_post.remove(GlslDrawObj.build_mesh_func)
        bpy.app.handlers.depsgraph_update_post.append(GlslDrawObj.build_scene)
        GlslDrawObj.build_mesh_func = bpy.app.handlers.depsgraph_update_post[-1]
        # bpy.app.handlers.frame_change_post.append(build_sub_index)

    @staticmethod
    def draw_func_remove():
        if GlslDrawObj.draw_func is not None:
            bpy.types.SpaceView3D.draw_handler_remove(GlslDrawObj.draw_func, "WINDOW")
            GlslDrawObj.draw_func = None

        if (
            GlslDrawObj.build_mesh_func is not None
            and GlslDrawObj.build_mesh_func in bpy.app.handlers.depsgraph_update_post
        ):
            bpy.app.handlers.depsgraph_update_post.remove(GlslDrawObj.build_mesh_func)
            GlslDrawObj.build_mesh_func = None
        GlslDrawObj.draw_objs = []

    # endregion 3Dview drawer


# region util func
def ortho_proj_mat(left, right, bottom, top, near, far):
    mat4 = Matrix.Identity(4)
    mat4[0][0] = 2 / (right - left)
    mat4[1][1] = 2 / (top - bottom)
    mat4[2][2] = -2 / (far - near)

    def tmpfunc(a, b):
        return -(a + b) / (a - b)

    mat4[3][0] = tmpfunc(right, left)
    mat4[3][1] = tmpfunc(top, bottom)
    mat4[3][2] = tmpfunc(far, near)
    mat4[3][3] = 1
    return mat4


def lookat_cross(loc, tar, up):
    lv = Vector(loc)
    tv = Vector(tar)
    uv = Vector(up)
    # z = l-t
    z = -tv  # 注視点ではなく、注視方角だからこう
    z.normalize()
    x = uv.cross(z)
    x.normalize()
    y = z.cross(x)
    y.normalize()
    n = [-(x.dot(lv)), -(y.dot(lv)), -(z.dot(lv))]
    mat4 = Matrix.Identity(4)
    for i in range(3):
        mat4[i][0] = x[i]
        mat4[i][1] = y[i]
        mat4[i][2] = z[i]
        mat4[3][i] = n[i]
    return mat4


class GlMesh:
    pos = None
    normals = None
    uvs = None
    index_per_mat = None  # material : vert index

    def __init__(self):
        self.pos = []
        self.normals = []
        self.uvs = []
        self.tangents = []
        self.index_per_mat = {}
        self.mat_list = None
