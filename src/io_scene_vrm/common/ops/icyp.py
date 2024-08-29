# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.


import bpy


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def make_mesh_from_envelopes(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    resolution: int = 5,
    max_distance_between_mataballs: float = 0.1,
    use_selected_bones: bool = False,
    may_vrm_humanoid: bool = True,
    with_auto_weight: bool = False,
    not_to_mesh: bool = True,
) -> set[str]:
    return bpy.ops.icyp.make_mesh_from_envelopes(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        resolution=resolution,
        max_distance_between_mataballs=max_distance_between_mataballs,
        use_selected_bones=use_selected_bones,
        may_vrm_humanoid=may_vrm_humanoid,
        with_auto_weight=with_auto_weight,
        not_to_mesh=not_to_mesh,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def make_basic_armature(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    skip_heavy_armature_setup: bool = False,
    wip_with_template_mesh: bool = False,
    tall: float = 1.7,
    head_ratio: float = 8.0,
    head_width_ratio: float = 0.6666666666666666,
    aging_ratio: float = 0.5,
    eye_depth: float = -0.03,
    shoulder_in_width: float = 0.05,
    shoulder_width: float = 0.08,
    arm_length_ratio: float = 1,
    hand_ratio: float = 1,
    finger_1_2_ratio: float = 0.75,
    finger_2_3_ratio: float = 0.75,
    nail_bone: bool = False,
    leg_length_ratio: float = 0.5,
    leg_width_ratio: float = 1,
    leg_size: float = 0.26,
    custom_property_name: str = "",
) -> set[str]:
    return bpy.ops.icyp.make_basic_armature(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        skip_heavy_armature_setup=skip_heavy_armature_setup,
        wip_with_template_mesh=wip_with_template_mesh,
        tall=tall,
        head_ratio=head_ratio,
        head_width_ratio=head_width_ratio,
        aging_ratio=aging_ratio,
        eye_depth=eye_depth,
        shoulder_in_width=shoulder_in_width,
        shoulder_width=shoulder_width,
        arm_length_ratio=arm_length_ratio,
        hand_ratio=hand_ratio,
        finger_1_2_ratio=finger_1_2_ratio,
        finger_2_3_ratio=finger_2_3_ratio,
        nail_bone=nail_bone,
        leg_length_ratio=leg_length_ratio,
        leg_width_ratio=leg_width_ratio,
        leg_size=leg_size,
        custom_property_name=custom_property_name,
    )


# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.
def make_mesh_detail(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    face_center_ratio: float = 1,
    eye_width_ratio: float = 2,
    nose_head_height: float = 1,
    nose_top_pos: float = 0.2,
    nose_height: float = 0.015,
    nose_width: float = 0.5,
    eye_depth: float = 0.01,
    eye_angle: float = 0.2617993877991494,
    eye_rotate: float = 0.43,
    cheek_ratio: float = 0.5,
    cheek_width: float = 0.85,
    mouth_width_ratio: float = 0.5,
    mouth_corner_nodule: float = 0.1,
    mouth_position_ratio: float = 0.6666666666666666,
    mouth_flatten: float = 0.1,
) -> set[str]:
    return bpy.ops.icyp.make_mesh_detail(  # type: ignore[attr-defined, no-any-return]
        execution_context,
        face_center_ratio=face_center_ratio,
        eye_width_ratio=eye_width_ratio,
        nose_head_height=nose_head_height,
        nose_top_pos=nose_top_pos,
        nose_height=nose_height,
        nose_width=nose_width,
        eye_depth=eye_depth,
        eye_angle=eye_angle,
        eye_rotate=eye_rotate,
        cheek_ratio=cheek_ratio,
        cheek_width=cheek_width,
        mouth_width_ratio=mouth_width_ratio,
        mouth_corner_nodule=mouth_corner_nodule,
        mouth_position_ratio=mouth_position_ratio,
        mouth_flatten=mouth_flatten,
    )
