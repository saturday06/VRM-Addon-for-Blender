# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
def addon_install(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    overwrite: bool = True,
    target: str = "DEFAULT",
    filepath: str = "",
    filter_folder: bool = True,
    filter_python: bool = True,
    filter_glob: str = "*.py;*.zip",
) -> set[str]: ...
def addon_enable(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    module: str = "",
) -> set[str]: ...
