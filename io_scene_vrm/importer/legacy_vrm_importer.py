import itertools
import sys
from collections.abc import Callable, Sequence
from math import radians, sqrt

import bpy
from mathutils import Matrix, Vector

from ..common.vrm0 import human_bone
from .abstract_base_vrm_importer import AbstractBaseVrmImporter
from .vrm_parser import PyMesh


class LegacyVrmImporter(AbstractBaseVrmImporter):
    def import_vrm(self) -> None:
        wm = self.context.window_manager

        def prog(z: int) -> int:
            wm.progress_update(z)
            return z + 1

        wm.progress_begin(0, 11)
        try:
            i = 1
            affected_object = self.scene_init()
            i = prog(i)
            self.texture_load()
            i = prog(i)
            self.make_armature()
            i = prog(i)
            self.use_fake_user_for_thumbnail()
            i = prog(i)
            self.make_material()
            i = prog(i)
            self.make_primitive_mesh_objects(wm, i)
            # i=prog(i) ↑関数内でやる
            self.load_vrm0_extensions()
            i = prog(i)
            self.cleaning_data()
            i = prog(i)
            self.set_bone_roll()
            i = prog(i)
            self.finishing(affected_object)
            i = prog(i)
            self.viewport_setup()
        finally:
            wm.progress_end()

    def texture_load(self) -> None:
        for image_index, image_props in enumerate(self.parse_result.image_properties):
            img = bpy.data.images.load(str(image_props.filepath))
            if not self.extract_textures_into_folder:
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/blender-v2.82-release/addons/io_scene_gltf2/blender/imp/gltf2_blender_image.py#L100
                img.pack()
            self.images[image_index] = img

    def make_armature(self) -> None:
        # build bones as armature
        armature_data = bpy.data.armatures.new("Armature")
        self.armature = bpy.data.objects.new(armature_data.name, armature_data)
        self.context.scene.collection.objects.link(self.armature)
        self.context.view_layer.objects.active = self.armature
        bpy.ops.object.mode_set(mode="EDIT")
        bones: dict[int, bpy.types.Bone] = {}
        armature_edit_bones: dict[int, bpy.types.Bone] = {}

        # bone recursive func
        def bone_chain(node_id: int, parent_node_id: int) -> None:
            if node_id == -1:  # 自身がrootのrootの時
                return

            py_bone = self.parse_result.nodes_dict[node_id]
            if py_bone.blend_bone:  # すでに割り当て済みのボーンが出てきたとき、その親の位置に動かす
                if parent_node_id == -1 or py_bone.blend_bone.parent is not None:
                    return
                py_bone.blend_bone.parent = bones[parent_node_id]
                li = [py_bone.blend_bone]
                while li:
                    bo = li.pop()
                    bo.translate(bones[parent_node_id].head)
                    for ch in bo.children:
                        li.append(ch)
                return
            if py_bone.mesh_id is not None and py_bone.children is None:
                return  # 子がなく、mesh属性を持つnodeはboneを生成しない
            b = armature_edit_bones[node_id]
            py_bone.name = b.name
            py_bone.blend_bone = b
            if parent_node_id == -1:
                parent_pos = [0, 0, 0]
            else:
                parent_pos = bones[parent_node_id].head
            b.head = tuple(
                Vector(parent_pos) + Vector(self.axis_glb_to_blender(py_bone.position))
            )

            # temporary tail pos(glTF doesn't have bone. there defines as joints )
            def vector_length(bone_vector: list[float]) -> float:
                return sqrt(
                    pow(bone_vector[0], 2)
                    + pow(bone_vector[1], 2)
                    + pow(bone_vector[2], 2)
                )

            # glTFは関節で定義されていて骨の長さとか向きとかないからまあなんかそれっぽい方向にボーンを向けて伸ばしたり縮めたり
            if py_bone.children is None:
                if parent_node_id == -1:  # 唯我独尊:上向けとけ
                    b.tail = [b.head[0], b.head[1] + 0.05, b.head[2]]
                else:  # normalize length to 0.03 末代:親から距離をちょっととる感じ
                    # 0除算除けと気分
                    length = max(
                        0.01,
                        vector_length(self.axis_glb_to_blender(py_bone.position)) * 30,
                    )
                    pos_diff = [
                        self.axis_glb_to_blender(py_bone.position)[i] / length
                        for i in range(3)
                    ]
                    if vector_length(pos_diff) <= 0.001:
                        # ボーンの長さが1mm以下なら上に10cm延ばす 長さが0だとOBJECT MODEに戻った時にボーンが消えるので上向けとく
                        pos_diff[1] += 0.01
                    b.tail = [b.head[i] + pos_diff[i] for i in range(3)]
            else:  # 子供たちの方向の中間を見る
                mean_relate_pos = Vector([0.0, 0.0, 0.0])
                for child_id in py_bone.children:
                    mean_relate_pos += Vector(
                        self.axis_glb_to_blender(
                            self.parse_result.nodes_dict[child_id].position
                        )
                    )
                children_len = len(py_bone.children)
                if children_len > 0:
                    mean_relate_pos = mean_relate_pos / children_len
                    if (
                        vector_length(mean_relate_pos) <= 0.001
                    ):  # ボーンの長さが1mm以下なら上に10cm延ばす
                        mean_relate_pos[1] += 0.1

                b.tail = tuple(Vector(b.head) + mean_relate_pos)

            bones[node_id] = b

            if parent_node_id != -1:
                b.parent = bones[parent_node_id]
            if py_bone.children is not None:
                for x in py_bone.children:
                    bone_nodes.append((x, node_id))

        root_node_set = list(dict.fromkeys(self.parse_result.skins_root_node_list))
        if root_node_set:
            root_nodes = root_node_set
        else:
            root_nodes = []
            scene_dicts = self.parse_result.json_dict.get("scenes")
            if not isinstance(scene_dicts, list):
                scene_dicts = []
            for scene_dict in scene_dicts:
                if not isinstance(scene_dict, dict):
                    continue
                nodes = scene_dict.get("nodes")
                if not isinstance(nodes, list):
                    continue
                for node in nodes:
                    if not isinstance(node, int):
                        continue
                    root_nodes.append(node)

        # generate edit_bones sorted by node_id for deterministic vrm output
        def find_connected_node_ids(parent_node_ids: Sequence[int]) -> set[int]:
            node_ids = set(parent_node_ids)
            for parent_node_id in parent_node_ids:
                py_bone = self.parse_result.nodes_dict[parent_node_id]
                if py_bone.children is not None:
                    node_ids |= find_connected_node_ids(py_bone.children)
            return node_ids

        for node_id in sorted(find_connected_node_ids(root_nodes)):
            bone_name = self.parse_result.nodes_dict[node_id].name
            armature_edit_bones[node_id] = self.armature.data.edit_bones.new(bone_name)

        bone_nodes = [(root_node, -1) for root_node in root_nodes]
        while bone_nodes:
            bone_chain(*bone_nodes.pop())
        # call when bone built
        self.context.scene.view_layers.update()
        bpy.ops.object.mode_set(mode="OBJECT")

        self.bone_names = {
            index: py_bone.name
            for index, py_bone in self.parse_result.nodes_dict.items()
            if py_bone.blend_bone
        }

        self.save_bone_child_object_world_matrices(self.armature)

    def make_primitive_mesh_objects(
        self, wm: bpy.types.WindowManager, progress: int
    ) -> None:
        armature = self.armature
        if armature is None:
            raise ValueError("armature is None")
        self.primitive_obj_dict = {
            pymesh[0].object_id: [] for pymesh in self.parse_result.meshes
        }
        morph_cache_dict: dict[
            tuple[int, int], list[list[float]]
        ] = {}  # key:tuple(POSITION,targets.POSITION),value:points_data
        # mesh_obj_build
        mesh_progress = 0.0
        mesh_progress_unit = 1 / max(1, len(self.parse_result.meshes))
        for pymesh in self.parse_result.meshes:
            b_mesh = bpy.data.meshes.new(pymesh[0].name)

            # FB_ngon_encoding実装
            # 前のポリゴンの最初の頂点が今回の最初の頂点と同じ場合、そのポリゴンを一つのポリゴン(ngon)としてインデックスを再構築する
            face_indices = []
            primitive_length_list = []
            for prim in pymesh:
                face_count = len(prim.face_indices)
                face_indices.append(prim.face_indices[0])
                face_offset = len(face_indices)
                for i in range(1, face_count):
                    if (
                        face_indices[-1][0] == prim.face_indices[i][0]
                        and prim.has_FB_ngon_encoding
                    ):
                        face_indices[-1].append(prim.face_indices[i][2])
                    else:
                        face_indices.append(prim.face_indices[i])
                primitive_length_list.append(
                    [
                        prim.material_index,
                        len(face_indices) - face_offset,
                    ]
                )
            # face_index = [tri for prim in pymesh for tri in prim.face_indices]
            if pymesh[0].POSITION is None:
                continue
            pos = list(map(self.axis_glb_to_blender, pymesh[0].POSITION))
            b_mesh.from_pydata(pos, [], face_indices)
            b_mesh.update()
            obj = bpy.data.objects.new(pymesh[0].name, b_mesh)
            obj.parent = self.armature
            self.meshes[pymesh[0].object_id] = obj
            # obj setting
            # origin 0:Vtype_Node 1:mesh 2:skin
            origin = None
            for key_is_node_id, node in self.parse_result.origin_nodes_dict.items():
                if node[1] != pymesh[0].object_id:
                    continue
                # origin boneの場所に移動
                obj.location = self.axis_glb_to_blender(node[0].position)
                if len(node) == 3:
                    origin = node
                    continue
                # len=2 ≒ skinがない場合
                parent_node_id = None
                for node_id, py_node in self.parse_result.nodes_dict.items():
                    if py_node.children is None:
                        continue
                    if key_is_node_id in py_node.children:
                        parent_node_id = node_id
                obj.parent_type = "BONE"
                if parent_node_id is not None:
                    obj.parent_bone = armature.data.bones[
                        self.parse_result.nodes_dict[parent_node_id].name
                    ].name
                if (
                    obj.parent_bone is None
                    or obj.parent_bone not in armature.data.bones
                ):
                    continue
                # boneのtail側にparentされるので、根元からmesh nodeのpositionに動かしなおす
                obj.matrix_world = Matrix.Translation(
                    [
                        armature.matrix_world.to_translation()[i]
                        + armature.data.bones[
                            obj.parent_bone
                        ].matrix_local.to_translation()[i]
                        + self.axis_glb_to_blender(node[0].position)[i]
                        for i in range(3)
                    ]
                )
            scene = self.context.scene
            scene.collection.objects.link(obj)

            # vertex groupの作成
            if origin is not None:
                skin_index = list(origin)[2]
                if not isinstance(skin_index, int):
                    raise ValueError

                # TODO bone名の不具合などでリネームが発生してるとうまくいかない
                nodes_index_list = self.parse_result.skins_joints_list[skin_index]
                # TODO bone名の不具合などでリネームが発生してるとうまくいかない
                # VertexGroupに頂点属性から一個ずつウェイトを入れる用の辞書作り
                for prim in pymesh:
                    if prim.JOINTS_0 is not None and prim.WEIGHTS_0 is not None:
                        # 使うkey(bone名)のvalueを空のリストで初期化(中身まで全部内包表記で?キモすぎるからしない。
                        vg_dict: dict[str, list[tuple[int, float]]] = {
                            self.parse_result.nodes_dict[
                                nodes_index_list[joint_id]
                            ].name: []
                            for joint_id in [
                                joint_id
                                for joint_ids in prim.JOINTS_0
                                for joint_id in joint_ids
                            ]
                        }
                        for v_index, (joint_ids, weights) in enumerate(
                            zip(prim.JOINTS_0, prim.WEIGHTS_0)
                        ):
                            # VRoidがJoints:[18,18,0,0]とかで格納してるからその処理を
                            normalized_joint_ids = list(dict.fromkeys(joint_ids))

                            # for deterministic export
                            def sort_by_vg_dict_key(
                                sort_data: tuple[
                                    int,
                                    list[int],
                                    list[int],
                                    dict[str, list[tuple[int, float]]],
                                ]
                            ) -> int:
                                (
                                    sort_joint_id,
                                    sort_joint_ids,
                                    sort_nodes_index_list,
                                    sort_vg_dict,
                                ) = sort_data
                                name = self.parse_result.nodes_dict[
                                    sort_nodes_index_list[sort_joint_id]
                                ].name
                                keys = list(sort_vg_dict.keys())
                                if name in keys:
                                    return keys.index(name)
                                return len(keys) + sort_joint_ids.index(sort_joint_id)

                            get_first_element: Callable[
                                [tuple[int, object, object, object]], int
                            ] = lambda input: input[0]
                            sorted_joint_ids = map(
                                get_first_element,
                                sorted(
                                    zip(
                                        normalized_joint_ids,
                                        itertools.repeat(joint_ids),
                                        itertools.repeat(nodes_index_list),
                                        itertools.repeat(vg_dict),
                                    ),
                                    key=sort_by_vg_dict_key,
                                ),
                            )

                            normalized_joint_dict: dict[int, float] = {
                                joint_id: 0 for joint_id in sorted_joint_ids
                            }

                            for i, k in enumerate(joint_ids):
                                normalized_joint_dict[k] += weights[i]

                            for joint_id, weight in normalized_joint_dict.items():
                                node_id = nodes_index_list[joint_id]
                                # TODO bone名の不具合などでリネームが発生してるとうまくいかない
                                vg_dict[
                                    self.parse_result.nodes_dict[node_id].name
                                ].append((v_index, weight))
                        vg_list = []  # VertexGroupのリスト
                        for vg_key in vg_dict.keys():
                            if vg_key not in obj.vertex_groups:
                                vg_list.append(obj.vertex_groups.new(name=vg_key))
                        # 頂点リストに辞書から書き込む
                        for vg in vg_list:
                            joint_id_and_weights = vg_dict[vg.name]
                            for joint_id, weight in joint_id_and_weights:
                                if weight != 0.0:
                                    # 頂点はまとめてリストで追加できるようにしかなってない
                                    vg.add([joint_id], weight, "REPLACE")
                obj.modifiers.new("amt", "ARMATURE").object = self.armature

            # uv
            flatten_vrm_mesh_vert_index = [v for verts in face_indices for v in verts]

            for prim in pymesh:
                texcoord_num = 0
                uv_flag = True
                while uv_flag:
                    channel_name = "TEXCOORD_" + str(texcoord_num)
                    if hasattr(prim, channel_name):
                        if channel_name not in b_mesh.uv_layers:
                            b_mesh.uv_layers.new(name=channel_name)
                        blender_uv_data = b_mesh.uv_layers[channel_name].data
                        vrm_texcoord = getattr(prim, channel_name)
                        for node_id, v_index in enumerate(flatten_vrm_mesh_vert_index):
                            blender_uv_data[node_id].uv = vrm_texcoord[v_index]
                            # to blender axis (上下反転)
                            blender_uv_data[node_id].uv[1] = (
                                blender_uv_data[node_id].uv[1] * -1 + 1
                            )
                        texcoord_num += 1
                    else:
                        uv_flag = False
                        break

            # Normal #TODO
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")
            self.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.shade_smooth()  # this is need
            b_mesh.create_normals_split()
            # bpy.ops.mesh.customdata_custom_splitnormals_add()
            for prim in pymesh:
                if prim.NORMAL is None:
                    continue
                normalized_normal = prim.NORMAL
                if (
                    prim.vert_normal_normalized is None
                    or not prim.vert_normal_normalized
                ):
                    normalized_normal = [
                        Vector(n)
                        if abs(Vector(n).magnitude - 1.0) < sys.float_info.epsilon
                        else Vector(n).normalized()
                        for n in prim.NORMAL
                    ]
                    prim.vert_normal_normalized = True
                    prim.NORMAL = normalized_normal
                b_mesh.normals_split_custom_set_from_vertices(
                    list(map(self.axis_glb_to_blender, normalized_normal))
                )
            b_mesh.use_auto_smooth = True

            # material適用
            face_length = 0
            for i, prim in enumerate(pymesh):
                if (
                    prim.material_index is None
                    or prim.material_index not in self.materials
                ):
                    continue
                if self.materials[prim.material_index].name not in obj.data.materials:
                    obj.data.materials.append(self.materials[prim.material_index])
                mat_index = 0
                for j, mat in enumerate(obj.material_slots):
                    if mat.material.name == self.materials[prim.material_index].name:
                        mat_index = j

                for n in range(primitive_length_list[i][1]):
                    b_mesh.polygons[face_length + n].material_index = mat_index
                face_length += primitive_length_list[i][1] + 1

            # vertex_color
            # なぜかこれだけ面基準で、loose verts and edgesに色は塗れない
            # また、2.79では頂点カラーにalpha(4要素目)がないから完全対応は無理だったが
            # 2.80では4要素になった模様
            # TODO: テスト (懸案:cleaningで頂点結合でデータ物故割れる説)
            flat_non_reducted_vert_index = [
                ind
                for prim in pymesh
                for ind in itertools.chain.from_iterable(prim.face_indices)
            ]
            for prim in pymesh:
                vcolor_count = 0
                vc_flag = True
                while vc_flag:
                    vc_color_name = f"COLOR_{vcolor_count}"
                    if hasattr(prim, vc_color_name):
                        vc = b_mesh.vertex_colors.get(vc_color_name)
                        if vc is None:
                            vc = b_mesh.vertex_colors.new(name=vc_color_name)
                        for v_index, _ in enumerate(vc.data):
                            vc.data[v_index].color = getattr(prim, vc_color_name)[
                                flat_non_reducted_vert_index[v_index]
                            ]
                        vcolor_count += 1
                    else:
                        vc_flag = False
                        break

            # shape_key
            # shapekey_data_factory with cache
            def absolutize_morph_positions(
                base_points: list[list[float]],
                morph_target_pos_and_index: list[object],
                prim: PyMesh,
            ) -> list[list[float]]:
                shape_key_positions = []
                morph_target_pos = morph_target_pos_and_index[0]
                morph_target_index = morph_target_pos_and_index[1]

                if prim.POSITION_accessor is None:
                    return []

                # すでに変換したことがあるならそれを使う
                if (
                    prim.POSITION_accessor,
                    morph_target_index,
                ) in morph_cache_dict:
                    return morph_cache_dict[
                        (prim.POSITION_accessor, morph_target_index)  # type: ignore[index]
                    ]

                for base_pos, morph_pos in zip(base_points, morph_target_pos):  # type: ignore[call-overload]
                    shape_key_positions.append(
                        self.axis_glb_to_blender(
                            [base_pos[i] + morph_pos[i] for i in range(3)]  # noqa: B023
                        )
                    )
                morph_cache_dict[
                    (prim.POSITION_accessor, morph_target_index)  # type: ignore[index]
                ] = shape_key_positions
                return shape_key_positions

            # shapeKeys
            for prim in pymesh:
                if (
                    prim.morph_target_point_list_and_accessor_index_dict is None
                    or b_mesh is None
                ):
                    continue
                if b_mesh.shape_keys is None:
                    obj.shape_key_add(name="Basis")
                for (
                    morph_name,
                    morph_pos_and_index,
                ) in prim.morph_target_point_list_and_accessor_index_dict.items():
                    if (
                        b_mesh.shape_keys is None
                        or morph_name not in b_mesh.shape_keys.key_blocks
                    ):
                        obj.shape_key_add(name=morph_name)
                    if b_mesh.shape_keys is None:
                        continue
                    keyblock = b_mesh.shape_keys.key_blocks[morph_name]
                    if prim.POSITION is not None:
                        shape_data = absolutize_morph_positions(
                            prim.POSITION, morph_pos_and_index, prim
                        )
                    else:
                        shape_data = []
                    for i, co in enumerate(shape_data):
                        keyblock.data[i].co = co
            # progress update
            mesh_progress += mesh_progress_unit
            wm.progress_update(progress + mesh_progress)
        wm.progress_update(progress + 1)

    def set_bone_roll(self) -> None:
        armature = self.armature
        if armature is None:
            raise ValueError("armature is None")

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        armature.select_set(True)
        self.context.view_layer.objects.active = self.armature
        bpy.ops.object.mode_set(mode="EDIT")
        hb = human_bone.HumanBoneSpecifications
        stop_bone_names = set(armature.data.values())

        def set_children_roll(bone_name: str, roll: float) -> None:
            armature = self.armature
            if armature is None:
                raise ValueError("armature is None")

            if bone_name in armature.data and armature.data[bone_name] != "":
                bone = armature.data.edit_bones[armature.data[bone_name]]
                bone.roll = radians(roll)
                roll_list = [*bone.children]
                while roll_list:
                    bone = roll_list.pop()
                    if bone.name in stop_bone_names:
                        continue
                    bone.roll = radians(roll)
                    roll_list.extend(bone.children)
                return

        for b in hb.center_req + hb.center_def:
            if b == "hips":
                set_children_roll(b, 90)
            else:
                set_children_roll(b, -90)
        for deg, bs in zip(
            [0, 180],
            [hb.left_arm_req + hb.left_arm_def, hb.right_arm_req + hb.right_arm_def],
        ):
            for b in bs:
                set_children_roll(b, deg)
        for b in (
            hb.left_leg_req + hb.right_leg_req + hb.left_leg_def + hb.right_leg_def
        ):
            set_children_roll(b, 90)
        bpy.ops.object.mode_set(mode="OBJECT")
