import bpy


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.schema.json
class NodeConstraint1NodeConstraintPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    # for UI
    show_expanded_roll_constraints: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Roll Constraint"  # noqa: F722
    )
    show_expanded_aim_constraints: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Aim Constraint"  # noqa: F722
    )
    show_expanded_rotation_constraints: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Rotation Constraint"  # noqa: F722
    )
