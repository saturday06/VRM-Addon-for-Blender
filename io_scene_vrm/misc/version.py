from typing import Tuple


# To avoid circular reference
def version() -> Tuple[int, int, int]:
    v = __import__(".".join(__name__.split(".")[:-3])).bl_info.get("version")
    if (
        not isinstance(v, tuple)
        or len(v) != 3
        or not isinstance(v[0], int)
        or not isinstance(v[1], int)
        or not isinstance(v[2], int)
    ):
        raise Exception(f"{v} is not valid type")
    return (v[0], v[1], v[2])
