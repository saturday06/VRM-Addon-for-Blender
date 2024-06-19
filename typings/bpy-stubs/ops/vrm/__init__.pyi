def refresh_mtoon1_outline(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    material_name: str,
    create_modifier: bool = False,
) -> set[str]: ...
def update_spring_bone1_animation(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    delta_time: float = 1,
) -> set[str]: ...
def add_spring_bone1_spring(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str,
) -> set[str]: ...
def add_spring_bone1_spring_joint(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str,
    spring_index: int,
) -> set[str]: ...
def bones_rename(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str,
) -> set[str]: ...
def load_human_bone_mappings(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    filepath: str,
) -> set[str]: ...
def save_human_bone_mappings(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    filepath: str,
) -> set[str]: ...
def model_validate(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    show_successful_message: bool = False,
    armature_object_name: str = "",
) -> set[str]: ...
def assign_vrm0_humanoid_human_bones_automatically(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str,
) -> set[str]: ...
def assign_vrm1_humanoid_human_bones_automatically(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str,
) -> set[str]: ...
def add_spring_bone1_collider(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str,
) -> set[str]: ...
def add_spring_bone1_collider_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str,
) -> set[str]: ...
def add_spring_bone1_collider_group_collider(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str,
    collider_group_index: int,
) -> set[str]: ...
def add_spring_bone1_spring_collider_group(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    armature_name: str,
    spring_index: int,
) -> set[str]: ...
def convert_mtoon1_to_bsdf_principled(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    material_name: str,
) -> set[str]: ...
def convert_material_to_mtoon1(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    material_name: str,
) -> set[str]: ...
def update_vrm1_expression_ui_list_elements(
    execution_context: str = "EXEC_DEFAULT",
    /,
) -> set[str]: ...
