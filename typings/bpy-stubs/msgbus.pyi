# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
# TODO: Correct type
def subscribe_rna(
    key: object,
    owner: object,
    args: object,
    notify: object,
    options: set[str] = ...,
) -> None: ...
def publish_rna(key: object) -> None: ...
def clear_by_owner(owner: object) -> None: ...
