from math import atan2, cos, radians, sin
from typing import List, Set

import bmesh
import bpy
from mathutils import Matrix, Vector

from ..common.logging import get_logger
from .template_mesh_maker import IcypTemplateMeshMaker

logger = get_logger(__name__)


class ICYP_OT_detail_mesh_maker(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "icyp.make_mesh_detail"
    bl_label = "(Don't work currently)detail mesh"
    l_description = "Create mesh with a simple setup for VRM export"
    bl_options = {"REGISTER", "UNDO"}

    # init before execute
    # https://docs.blender.org/api/2.82/bpy.types.Operator.html#invoke-function
    # pylint: disable=W0201
    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> Set[str]:
        self.base_armature_name = [
            o for o in context.selected_objects if o.type == "ARMATURE"
        ][0].name
        self.face_mesh_name = [o for o in context.selected_objects if o.type == "MESH"][
            0
        ].name
        face_mesh = bpy.data.objects[self.face_mesh_name]
        face_mesh.display_type = "WIRE"
        rfd = face_mesh.bound_box[4]
        lfd = face_mesh.bound_box[0]
        rfu = face_mesh.bound_box[5]
        rbd = face_mesh.bound_box[7]
        self.neck_depth_offset = rfu[2]
        self.head_tall_size = rfu[2] - rfd[2]
        self.head_width_size = rfd[0] - lfd[0]
        self.head_depth_size = rfd[1] - rbd[1]
        return self.execute(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        self.base_armature = bpy.data.objects[self.base_armature_name]
        self.face_mesh = bpy.data.objects[self.face_mesh_name]
        head_bone = self.get_humanoid_bone("head")
        head_matrix = IcypTemplateMeshMaker.head_bone_to_head_matrix(
            head_bone, self.head_tall_size, self.neck_depth_offset
        )

        self.neck_tail_y = self.head_tall_size - (
            head_bone.tail_local[2] - head_bone.head_local[2]
        )

        self.mesh = bpy.data.meshes.new("template_face")
        self.make_face(context, self.mesh)
        obj = bpy.data.objects.new("template_face", self.mesh)
        scene = context.scene
        scene.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.matrix_local = head_matrix
        bpy.ops.object.modifier_add(type="MIRROR")
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        obj.scale[2] = -1
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        obj.select_set(False)
        context.view_layer.objects.active = self.face_mesh
        return {"FINISHED"}

    def get_humanoid_bone(self, bone: str) -> bpy.types.Bone:
        return self.base_armature.data.bones[self.base_armature.data[bone]]

    face_center_ratio: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=1, min=0.2, max=1, soft_min=0.6, name="Face center ratio"  # noqa: F722
    )
    eye_width_ratio: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=2, min=0.5, max=4, name="Eye width ratio"  # noqa: F722
    )
    nose_head_height: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=1, min=0, max=1, name="nose head"  # noqa: F722
    )
    nose_top_pos: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.2, min=0, max=0.6, name="nose top position"  # noqa: F722
    )
    nose_height: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.015, min=0.01, max=0.1, step=0.001, name="nose height"  # noqa: F722
    )
    nose_width: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.5, min=0.01, max=1, name="nose width"  # noqa: F722
    )
    eye_depth: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.01, min=0.01, max=0.1, name="Eye depth"  # noqa: F722
    )
    eye_angle: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=radians(15), min=0, max=0.55, name="Eye angle"  # noqa: F722
    )
    eye_rotate: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.43, min=0, max=0.86, name="Eye rotation"  # noqa: F722
    )
    cheek_ratio: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.5, min=0, max=1, name="cheek position"  # noqa: F722
    )
    cheek_width: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.85, min=0.5, max=1, name="cheek width ratio"  # noqa: F722
    )
    mouth_width_ratio: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.5, min=0.3, max=0.9, name="Mouth width"  # noqa: F722
    )
    # 口角結節
    mouth_corner_nodule: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.1, min=0.01, max=1, name="oris width"  # noqa: F722
    )
    mouth_position_ratio: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=2 / 3, min=0.3, max=0.7, name="Mouth position"  # noqa: F722
    )
    mouth_flatten: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.1, min=0.0, max=1, name="Mouth flat"  # noqa: F722
    )

    def make_face(self, _context: bpy.types.Context, mesh: bpy.types.Mesh) -> None:
        def add_point(point: Vector) -> bmesh.types.BMVert:
            return bm.verts.new(point)

        def make_circle(
            center: Vector,
            radius: float,
            axis: str,
            divide: int,
            angle: int = 360,
            x_ratio: float = 1,
            y_ratio: float = 1,
        ) -> None:
            if axis == "X":
                axis_n = (0, 1)
            elif axis == "Y":
                axis_n = (1, 2)
            else:
                axis_n = (2, 0)
            if divide < 3:
                logger.error("Wrong divide set")
                divide = 3
            if angle == 0:
                logger.error("Wrong angle set")
                angle = 180
            verts = []
            for i in range(divide + 1):
                pi2 = 3.14 * 2 * radians(angle) / radians(360)
                vert = add_point(center)
                xy = (sin(pi2 * i / divide) * y_ratio, cos(pi2 * i / divide) * x_ratio)
                for n, j in zip(axis_n, xy):
                    vert.co[n] = vert.co[n] + j * radius
                verts.append(vert)

            bm.faces.new(verts)

        def width_add(point: Vector, add_loc: float) -> Vector:
            return Vector([p + a for p, a in zip(point, [0, 0, add_loc])])

        def depth_add(point: Vector, add_loc: float) -> Vector:
            return Vector([p + a for p, a in zip(point, [add_loc, 0, 0])])
            # X depth Y up Z width

        bm = bmesh.new()

        face_tall = self.head_tall_size * self.face_center_ratio

        add_point([-self.head_depth_size / 2, 0, 0])

        eye_point = Vector(
            [
                -self.eye_depth - self.head_depth_size / 2,
                face_tall / 2,
                self.head_width_size / 5,
            ]
        )

        eye_iris_size = eye_point[2] * self.eye_width_ratio * 0.25 / 2
        eye_width = eye_iris_size * 5 / 3

        eye_height = eye_iris_size * 0.9
        eye_axis = -self.eye_angle
        eye_quad_lu_point = eye_point + Matrix.Rotation(eye_axis, 4, "Y") @ Vector(
            [0, eye_height, -eye_iris_size]
        )
        eye_quad_ld_point = eye_point + Matrix.Rotation(eye_axis, 4, "Y") @ Vector(
            [0, -eye_height, -eye_iris_size]
        )
        eye_quad_rd_point = eye_point + Matrix.Rotation(eye_axis, 4, "Y") @ Vector(
            [0, -eye_height, eye_iris_size]
        )
        eye_quad_ru_point = eye_point + Matrix.Rotation(eye_axis, 4, "Y") @ Vector(
            [0, eye_height, eye_iris_size]
        )
        eye_inner_point = eye_point + Matrix.Rotation(
            -eye_axis, 4, "Y"
        ) @ Matrix.Rotation(self.eye_rotate, 4, "X") @ Vector(
            [0, -eye_height, -eye_width]
        )
        eye_outer_point = eye_point + Matrix.Rotation(
            eye_axis, 4, "Y"
        ) @ Matrix.Rotation(self.eye_rotate, 4, "X") @ Vector(
            [0, eye_height, eye_width]
        )
        if eye_inner_point[2] < self.head_width_size / 12:
            eye_inner_point[2] = self.head_width_size / 12
        eye_quad_lu_vert = add_point(eye_quad_lu_point)
        eye_quad_ld_vert = add_point(eye_quad_ld_point)
        eye_quad_rd_vert = add_point(eye_quad_rd_point)
        eye_quad_ru_vert = add_point(eye_quad_ru_point)
        eye_inner_vert = add_point(eye_inner_point)
        eye_outer_vert = add_point(eye_outer_point)

        bm.edges.new([eye_inner_vert, eye_quad_lu_vert])
        bm.edges.new([eye_quad_lu_vert, eye_quad_ru_vert])
        bm.edges.new([eye_quad_ru_vert, eye_outer_vert])
        bm.edges.new([eye_outer_vert, eye_quad_rd_vert])
        bm.edges.new([eye_quad_rd_vert, eye_quad_ld_vert])
        bm.edges.new([eye_quad_ld_vert, eye_inner_vert])

        make_circle(
            depth_add(eye_point, eye_quad_ru_point[0] - eye_point[0]),
            eye_iris_size,
            "Y",
            12,
            360,
            1,
            1,
        )

        # 眉弓(でこの下ラインあたり)
        arcus_superciliaris_under_point = [
            -self.head_depth_size / 2,
            face_tall * 5 / 8,
            0,
        ]
        arcus_superciliaris_outer_under_point = [
            eye_point[0],
            face_tall * 5 / 8,
            eye_outer_point[2],
        ]

        arcus_superciliaris_under_vert = add_point(arcus_superciliaris_under_point)
        arcus_superciliaris_outer_under_vert = add_point(
            arcus_superciliaris_outer_under_point
        )

        # eye_brow_inner_point = width_add(eye_brow_point,eye_point[2] - eye_width*1.1)
        # eye_brow_outer_point = width_add(eye_brow_point,eye_point[2] + eye_width*1.1)
        # eye_brow_inner_vert = add_point(eye_brow_inner_point)
        # eye_brow_outer_vert = add_point(eye_brow_outer_point)
        # bm.edges.new([eye_brow_inner_vert,eye_brow_outer_vert])

        nose_head_height = (
            self.nose_head_height * eye_point[1]
            + (1 - self.nose_head_height) * eye_quad_rd_point[1]
        )
        nose_start_point = [
            -self.eye_depth / 2 - self.head_depth_size / 2,
            nose_head_height,
            0,
        ]
        nose_start_vert = add_point(nose_start_point)
        nose_end_point = [self.nose_height - self.head_depth_size / 2, face_tall / 3, 0]
        nose_top_point = [
            self.nose_height - self.head_depth_size / 2,
            face_tall / 3 + self.nose_top_pos * (eye_point[1] - nose_end_point[1]),
            0,
        ]
        nose_top_vert = add_point(nose_top_point)

        nose_end_side_point = depth_add(
            width_add(
                nose_end_point,
                max([eye_inner_point[2], self.head_width_size / 6]) * self.nose_width,
            ),
            -self.nose_height,
        )
        nose_end_side_vert = add_point(nose_end_side_point)

        otogai_point = [-self.head_depth_size / 2, 0, 0]
        otogai_vert = add_point(otogai_point)
        ear_hole_point = [0, eye_point[1], self.head_width_size / 2]
        ear_hole_vert = add_point(ear_hole_point)

        # mouth_point = Vector([-self.head_depth_size/2+self.nose_height*2/3,face_tall*2/9,0])
        mouth_point = Vector(
            [
                -self.head_depth_size / 2 + self.nose_height * 2 / 3,
                self.mouth_position_ratio * nose_top_point[1],
                0,
            ]
        )
        mouth_rotate_radian = atan2(self.nose_height, nose_top_point[1])
        rotated_height_up = Vector(
            (
                Matrix.Rotation(-mouth_rotate_radian, 4, "Z")
                @ Vector(
                    [
                        self.mouth_width_ratio * -0.01 * self.mouth_flatten,
                        self.mouth_width_ratio * 0.01,
                        0,
                    ]
                )
            )
        )
        rotated_height_down = Vector(
            (
                Matrix.Rotation(-mouth_rotate_radian, 4, "Z")
                @ Vector(
                    [
                        self.mouth_width_ratio * 0.01 * self.mouth_flatten,
                        self.mouth_width_ratio * 0.01 * 1.3,
                        0,
                    ]
                )
            )
        )
        rotated_height_mid_up = Vector(
            (
                Matrix.Rotation(-mouth_rotate_radian, 4, "Z")
                @ Vector([0, self.mouth_width_ratio * 0.005 * self.mouth_flatten, 0])
            )
        )
        rotated_height_mid_down = Vector(
            (
                Matrix.Rotation(-mouth_rotate_radian, 4, "Z")
                @ Vector(
                    [0, self.mouth_width_ratio * 0.005 * 1.3 * self.mouth_flatten, 0]
                )
            )
        )

        mouth_point_up_vert = add_point(mouth_point + rotated_height_up)
        mouth_point_mid_up_vert = add_point(mouth_point + rotated_height_mid_up)
        mouth_point_mid_down_vert = add_point(mouth_point - rotated_height_mid_down)
        mouth_point_down_vert = add_point(mouth_point - rotated_height_down)
        mouth_outer_point = depth_add(
            width_add(mouth_point, self.mouth_width_ratio * self.head_width_size / 5),
            (eye_point[0] - mouth_point[0]) * self.mouth_width_ratio,
        )
        mouth_outer_point_vert = add_point(mouth_outer_point)
        mouth_center_point = depth_add(mouth_point, rotated_height_up[0] / 2)
        mouth_center_vert = add_point(mouth_center_point)

        mouth_corner_nodule_point = (
            mouth_outer_point
            + (mouth_outer_point - mouth_point).normalized()
            * 0.2
            * self.mouth_corner_nodule
        )
        mouth_corner_nodule_vert = add_point(mouth_corner_nodule_point)

        jaw_point = [0, mouth_point[1], self.head_width_size * 3 / 8]
        jaw_vert = add_point(jaw_point)

        max_width_point = [
            0,
            arcus_superciliaris_under_point[1],
            self.head_width_size / 2,
        ]
        max_width_vert = add_point(max_width_point)

        cheek_point = Vector(
            [
                -self.head_depth_size / 2,
                0,
                eye_inner_point[2] + (eye_quad_lu_point[2] - eye_inner_point[2]) / 2,
            ]
        )
        cheek_point[1] = min(
            [eye_quad_ld_point[1], (nose_top_point[1] + nose_start_point[1]) / 2]
        )
        cheek_point[1] = (
            cheek_point[1] - (cheek_point[1] - nose_top_point[1]) * self.cheek_ratio
        )
        tmp_cheek = Matrix.Rotation(eye_axis, 4, "Y") @ Vector(
            [
                0,
                0,
                (eye_outer_point[2] - eye_inner_point[2] * 2 / 3)
                * cos(eye_axis)
                * self.cheek_width,
            ]
        )
        cheek_top_outer_vert = add_point(tmp_cheek + cheek_point)
        cheek_top_inner_vert = add_point(cheek_point)
        cheek_under_inner_point = Vector(
            [
                -self.head_depth_size / 2,
                nose_top_point[1],
                eye_inner_point[2] + (eye_quad_lu_point[2] - eye_inner_point[2]) / 2,
            ]
        )
        cheek_under_outer_point = cheek_under_inner_point + tmp_cheek
        cheek_under_inner_vert = add_point(cheek_under_inner_point)
        cheek_under_outer_vert = add_point(cheek_under_outer_point)

        # 目尻の端っこからちょっといったとこ
        orbit_end = eye_outer_point + Matrix.Rotation(eye_axis, 4, "Y") @ Vector(
            [0, 0, eye_iris_size]
        ) * cos(eye_axis)
        orbit_vert = add_point(orbit_end)

        bm.edges.new([otogai_vert, jaw_vert])
        bm.edges.new([jaw_vert, ear_hole_vert])

        def add_mesh(points: List[bmesh.types.BMVert]) -> None:
            bm.faces.new(points)

        add_mesh(
            [
                eye_quad_ld_vert,
                cheek_top_inner_vert,
                cheek_top_outer_vert,
                eye_quad_rd_vert,
            ]
        )
        add_mesh(
            [
                cheek_under_inner_vert,
                cheek_top_inner_vert,
                cheek_top_outer_vert,
                cheek_under_outer_vert,
            ]
        )
        # eye ring
        add_mesh(
            [
                arcus_superciliaris_under_vert,
                arcus_superciliaris_outer_under_vert,
                eye_quad_ru_vert,
                eye_quad_lu_vert,
            ]
        )
        add_mesh(
            [
                arcus_superciliaris_under_vert,
                eye_quad_lu_vert,
                eye_inner_vert,
                nose_start_vert,
            ]
        )
        add_mesh([nose_start_vert, eye_inner_vert, cheek_top_inner_vert])
        add_mesh([eye_inner_vert, eye_quad_ld_vert, cheek_top_inner_vert])
        add_mesh([eye_outer_vert, orbit_vert, cheek_top_outer_vert, eye_quad_rd_vert])

        add_mesh(
            [
                nose_start_vert,
                cheek_top_inner_vert,
                cheek_under_inner_vert,
                nose_end_side_vert,
            ]
        )
        add_mesh(
            [
                nose_end_side_vert,
                cheek_under_inner_vert,
                mouth_corner_nodule_vert,
                mouth_outer_point_vert,
            ]
        )
        add_mesh(
            [cheek_under_inner_vert, cheek_under_outer_vert, mouth_corner_nodule_vert]
        )

        add_mesh([cheek_under_outer_vert, jaw_vert, mouth_corner_nodule_vert])

        add_mesh([nose_start_vert, nose_top_vert, nose_end_side_vert])
        # add_mesh([nose_end_under_vert,nose_top_vert,nose_end_side_vert])
        add_mesh(
            [
                nose_top_vert,
                nose_end_side_vert,
                mouth_outer_point_vert,
                mouth_point_up_vert,
            ]
        )

        add_mesh([mouth_point_up_vert, mouth_point_mid_up_vert, mouth_outer_point_vert])
        add_mesh([mouth_point_mid_up_vert, mouth_center_vert, mouth_outer_point_vert])
        add_mesh([mouth_center_vert, mouth_point_mid_down_vert, mouth_outer_point_vert])
        add_mesh(
            [mouth_point_mid_down_vert, mouth_point_down_vert, mouth_outer_point_vert]
        )

        add_mesh(
            [
                eye_outer_vert,
                orbit_vert,
                arcus_superciliaris_outer_under_vert,
                eye_quad_ru_vert,
            ]
        )
        add_mesh(
            [cheek_top_outer_vert, cheek_under_outer_vert, jaw_vert, ear_hole_vert]
        )
        add_mesh([otogai_vert, jaw_vert, mouth_corner_nodule_vert])
        add_mesh(
            [
                otogai_vert,
                mouth_corner_nodule_vert,
                mouth_outer_point_vert,
                mouth_point_down_vert,
            ]
        )
        add_mesh([orbit_vert, ear_hole_vert, cheek_top_outer_vert])
        add_mesh(
            [
                arcus_superciliaris_outer_under_vert,
                max_width_vert,
                ear_hole_vert,
                orbit_vert,
            ]
        )

        # head
        make_circle(
            [0, max_width_point[1], 0],
            max_width_point[2],
            "Y",
            13,
            90,
            1,
            (self.head_tall_size - max_width_point[1]) / max_width_point[2],
        )
        make_circle(
            [0, arcus_superciliaris_under_point[1], 0],
            self.head_tall_size - arcus_superciliaris_outer_under_point[1],
            "X",
            13,
            90,
            1,
            arcus_superciliaris_under_point[0]
            / (self.head_tall_size - arcus_superciliaris_outer_under_point[1]),
        )

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
