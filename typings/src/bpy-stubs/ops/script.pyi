# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
def execute_preset(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    filepath: str = "",
    menu_idname: str = "",
) -> set[str]: ...
def python_file_run(
    execution_context: str = "EXEC_DEFAULT", /, *, filepath: str = ""
) -> set[str]: ...
def reload(execution_context: str = "EXEC_DEFAULT") -> set[str]: ...
