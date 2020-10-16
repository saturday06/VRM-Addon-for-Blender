import bpy
import bmesh
from mathutils import Matrix, Vector
from ..vrm_types import HumanBones


class IcypTemplateMeshMaker:
    def make_mesh_obj(self, name, method):
        mesh = bpy.data.meshes.new(name)
        method(mesh)
        obj = bpy.data.objects.new(name, mesh)
        scene = bpy.context.scene
        scene.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_add(type="MIRROR")
        return obj

    def __init__(self, args):
        self.bm = None
        self.args = args
        self.head_size = args.tall / args.head_ratio
        self.make_mesh_obj("head", self.make_head)
        self.make_mesh_obj("body", self.make_humanoid)

    def get_humanoid_bone(self, bone):
        return self.args.armature_obj.data.bones[self.args.armature_obj.data[bone]]

    def make_head(self, mesh):
        args = self.args
        self.bm = bmesh.new()
        head_size = self.head_size

        head_bone = self.get_humanoid_bone("head")
        head_matrix = head_bone.matrix_local
        # ボーンマトリックスからY軸移動を打ち消して、あらためて欲しい高さ(上底が身長の高さ)にする変換(matrixはYupだけど、bone座標系はZup)
        head_matrix = (
            head_matrix
            @ Matrix(
                [
                    [1, 0, 0, 0],
                    [0, 1, 0, -head_bone.head_local[2]],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1],
                ]
            )
            @ Matrix.Translation(Vector([head_size / 16, args.tall - head_size, 0]))
        )
        self.make_half_trapezoid(
            [head_size * 7 / 8, head_size * args.head_width_ratio],
            [head_size * 7 / 8, head_size * args.head_width_ratio],
            head_size,
            head_matrix,
        )
        self.bm.to_mesh(mesh)
        self.bm.free()

    def make_humanoid(self, mesh):
        args = self.args
        self.bm = bmesh.new()
        head_size = self.head_size
        # region body

        # make neckneck
        neck_bone = self.get_humanoid_bone("neck")
        self.make_half_cube(
            [head_size / 2, head_size / 2, neck_bone.length], neck_bone.head_local
        )
        # make chest - upper and lower (肋骨の幅の最大値で分割)
        chest_bone = self.get_humanoid_bone("chest")
        shoulder_in = args.shoulder_in_width
        left_upper_arm_bone = self.get_humanoid_bone("leftUpperArm")
        # upper chest shell
        self.make_half_trapezoid(
            [head_size * 3 / 4, left_upper_arm_bone.head_local[0] * 2],
            [head_size * 3 / 4, shoulder_in],
            chest_bone.length,
            chest_bone.matrix_local,
        )
        # lower chest shell
        spine_bone = self.get_humanoid_bone("spine")
        self.make_half_trapezoid(
            [head_size * 3 / 4, (left_upper_arm_bone.head_local[0] - shoulder_in) * 2],
            [head_size * 3 / 4, left_upper_arm_bone.head_local[0] * 2],
            spine_bone.length * 3 / 5,
            spine_bone.matrix_local
            @ Matrix.Translation(Vector([0, spine_bone.length * 2 / 5, 0])),
        )

        # make spine
        # make hips
        hips_bone = self.get_humanoid_bone("hips")
        hips_size = left_upper_arm_bone.head_local[0] * 2 * 1.2
        self.make_half_cube(
            [hips_size, head_size * 3 / 4, hips_bone.length], hips_bone.head_local
        )
        # endregion body

        # region arm
        left_arm_bones = [
            self.get_humanoid_bone(v)
            for v in HumanBones.left_arm_req + HumanBones.left_arm_def
            if v in args.armature_obj.data
            and args.armature_obj.data[v] != ""
            and args.armature_obj.data[v] in args.armature_obj.data.bones
        ]
        left_hand_bone = self.get_humanoid_bone("leftHand")
        for b in left_arm_bones:
            base_xz = [
                b.head_radius if b != left_hand_bone else args.hand_size() / 2,
                b.head_radius,
            ]
            top_xz = [
                b.tail_radius if b != left_hand_bone else args.hand_size() / 2,
                b.tail_radius,
            ]
            self.make_trapezoid(base_xz, top_xz, b.length, [0, 0, 0], b.matrix_local)
        # TODO Thumb rotation
        # endregion arm

        # region leg
        # TODO
        left_leg_bones = [
            self.get_humanoid_bone(v)
            for v in HumanBones.left_leg_req + HumanBones.left_leg_def
            if v in args.armature_obj.data
            and args.armature_obj.data[v] != ""
            and args.armature_obj.data[v] in args.armature_obj.data.bones
        ]
        for b in left_leg_bones:
            bone_name = ""
            for k, v in self.args.armature_obj.data.items():
                if v == b.name:
                    bone_name = k
                    break
            if bone_name == "":
                head_x = b.head_radius
                head_z = b.head_radius
                tail_x = b.head_radius
                tail_z = b.head_radius
            elif "UpperLeg" in bone_name:
                head_x = hips_size / 2
                head_z = hips_size / 2
                tail_x = 0.71 * hips_size / 2
                tail_z = 0.71 * hips_size / 2
            elif "LowerLeg" in bone_name:
                head_x = 0.71 * hips_size / 2
                head_z = 0.71 * hips_size / 2
                tail_x = 0.54 * hips_size / 2
                tail_z = 0.6 * hips_size / 2
            elif "Foot" in bone_name:
                head_x = 0.54 * hips_size / 2
                head_z = 0.6 * hips_size / 2
                tail_x = 0.81 * hips_size / 2
                tail_z = 0.81 * hips_size / 2
            elif "Toes" in bone_name:
                head_x = 0.81 * hips_size / 2
                head_z = 0.81 * hips_size / 2
                tail_x = 0.81 * hips_size / 2
                tail_z = 0.81 * hips_size / 2
            self.make_trapezoid(
                [head_x, head_z], [tail_x, tail_z], b.length, [0, 0, 0], b.matrix_local
            )
        # endregion leg

        self.bm.to_mesh(mesh)
        self.bm.free()

    def make_cube(self, xyz, translation=None, rot_matrix=None):
        points = self.cubic_points(xyz, translation, rot_matrix)
        verts = []
        for p in points:
            verts.append(self.bm.verts.new(p))
        for poly in self.cube_loop:
            self.bm.faces.new([verts[i] for i in poly])

    def make_half_cube(self, xyz, translation=None):
        points = self.half_cubic_points(xyz, translation)
        verts = []
        for p in points:
            verts.append(self.bm.verts.new(p))
        for poly in self.cube_loop_half:
            self.bm.faces.new([verts[i] for i in poly])

    def cubic_points(self, xyz, translation=None, rot_matrix=None):
        if translation is None:
            translation = [0, 0, 0]
        if rot_matrix is None:
            rot_matrix = Matrix.Identity(4)
        x = xyz[0]
        y = xyz[1]
        z = xyz[2]
        tx = translation[0]
        ty = translation[1]
        tz = translation[2]
        points = (
            (-x / 2 + tx, -y / 2 + ty, 0 + tz),
            (-x / 2 + tx, y / 2 + ty, 0 + tz),
            (x / 2 + tx, y / 2 + ty, 0 + tz),
            (x / 2 + tx, -y / 2 + ty, 0 + tz),
            (-x / 2 + tx, -y / 2 + ty, z + tz),
            (-x / 2 + tx, y / 2 + ty, z + tz),
            (x / 2 + tx, y / 2 + ty, z + tz),
            (x / 2 + tx, -y / 2 + ty, z + tz),
        )

        return [rot_matrix @ Vector(p) for p in points]

    cube_loop = [
        [0, 1, 2, 3],
        [7, 6, 5, 4],
        [4, 5, 1, 0],
        [5, 6, 2, 1],
        [6, 7, 3, 2],
        [7, 4, 0, 3],
    ]

    def half_cubic_points(self, xyz, translation=None):
        if translation is None:
            translation = [0, 0, 0]
        x = xyz[0]
        y = xyz[1]
        z = xyz[2]
        tx = translation[0]
        ty = translation[1]
        tz = translation[2]
        return (
            (0, -y / 2 + ty, 0 + tz),
            (0, y / 2 + ty, 0 + tz),
            (x / 2 + tx, y / 2 + ty, 0 + tz),
            (x / 2 + tx, -y / 2 + ty, 0 + tz),
            (0, -y / 2 + ty, z + tz),
            (0, y / 2 + ty, z + tz),
            (x / 2 + tx, y / 2 + ty, z + tz),
            (x / 2 + tx, -y / 2 + ty, z + tz),
        )

    cube_loop_half = [
        [0, 1, 2, 3],
        [7, 6, 5, 4],
        [5, 6, 2, 1],
        [6, 7, 3, 2],
        [7, 4, 0, 3],
    ]

    def make_half_trapezoid(self, head_xz, tail_xz, height, matrix=None):
        points = self.half_trapezoid_points(head_xz, tail_xz, height, matrix)
        verts = []
        for p in points:
            verts.append(self.bm.verts.new(p))
        for poly in self.half_trapezoid_loop:
            self.bm.faces.new([verts[i] for i in poly])

    def half_trapezoid_points(self, head_xz, tail_xz, height, matrix=None):
        if matrix is None:
            matrix = Matrix.Identity(4)
        hx = head_xz[0]
        hz = head_xz[1]
        tx = tail_xz[0]
        tz = tail_xz[1]

        points = (
            (-hx / 2, 0, 0),  # 0
            (-hx / 2, 0, -hz / 2),  # 1
            (-tx / 2, height, -tz / 2),  # 2
            (-tx / 2, height, 0),  # 3
            (hx / 2, 0, -hz / 2),  # 4
            (hx / 2, 0, 0),  # 5
            (tx / 2, height, 0),  # 6
            (tx / 2, height, -tz / 2),  # 7
        )
        return [matrix @ Vector(p) for p in points]

    half_trapezoid_loop = [
        [3, 2, 1, 0],
        [7, 2, 3, 6],
        [6, 5, 4, 7],
        [7, 4, 1, 2],
        [5, 4, 1, 0],
    ]

    def make_trapezoid(
        self, head_xz, tail_xz, height, translation=None, rot_matrix=None
    ):
        points = self.trapezoid_points(
            head_xz, tail_xz, height, translation, rot_matrix
        )
        verts = []
        for p in points:
            verts.append(self.bm.verts.new(p))
        for poly in self.tpzoid_points:
            self.bm.faces.new([verts[i] for i in poly])

    # 台形 軸方向高さ
    def trapezoid_points(
        self, head_xz, tail_xz, height, translation=None, rot_matrix=None
    ):
        if translation is None:
            translation = [0, 0, 0]
        if rot_matrix is None:
            rot_matrix = Matrix.Identity(4)
        hx = head_xz[0]
        hz = head_xz[1]
        tx = tail_xz[0]
        tz = tail_xz[1]

        tlx = translation[0]
        tly = translation[1]
        tlz = translation[2]
        points = (
            (-hx / 2 + tlx, tly, -hz / 2 + tlz),
            (hx / 2 + tlx, tly, -hz / 2 + tlz),
            (hx / 2 + tlx, tly, hz / 2 + tlz),
            (-hx / 2 + tlx, tly, hz / 2 + tlz),
            (-tx / 2 + tlx, height + tly, -tz / 2 + tlz),
            (tx / 2 + tlx, height + tly, -tz / 2 + tlz),
            (tx / 2 + tlx, height + tly, tz / 2 + tlz),
            (-tx / 2 + tlx, height + tly, tz / 2 + tlz),
        )

        return [rot_matrix @ Vector(p) for p in points]

    tpzoid_points = [
        [3, 2, 1, 0],
        [6, 5, 4, 7],
        [5, 1, 0, 4],
        [6, 2, 1, 5],
        [7, 3, 2, 6],
        [4, 0, 3, 7],
    ]
