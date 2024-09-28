# This code is auto generated.
# To regenerate, run the `uv run tools/property_typing.py` command.


import bpy


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
