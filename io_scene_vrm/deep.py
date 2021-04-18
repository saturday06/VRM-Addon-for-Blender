from typing import Any, Dict, List, Optional, Union, cast


def make_return_value(
    v: Any,
) -> Union[int, bool, float, str, List[Any], Dict[str, Any], None]:
    if v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return v
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return v
    if isinstance(v, dict):
        return v

    print(f"WARNING: {v} is unrecognized type")
    return cast(Optional[Union[int, bool, float, str, List[Any], Dict[str, Any]]], v)


def get(
    json: Optional[Union[Dict[str, Any], List[Any]]],
    attrs: List[Union[int, str]],
    default: Optional[Union[int, float, str, List[Any], Dict[str, Any]]] = None,
) -> Union[int, bool, float, str, List[Any], Dict[str, Any], None]:
    if json is None:
        return default

    attr = attrs.pop(0)

    if isinstance(json, list) and isinstance(attr, int) and 0 <= attr < len(json):
        if not attrs:
            return make_return_value(json[attr])
        return get(json[attr], attrs, default)

    if isinstance(json, dict) and isinstance(attr, str) and attr in json:
        if not attrs:
            return make_return_value(json[attr])
        return get(json[attr], attrs, default)

    return default


def get_list(
    json: Optional[Union[Dict[str, Any], List[Any]]],
    attrs: List[Union[int, str]],
    default: List[Any],
) -> List[Any]:
    result = get(json, attrs, default)
    return result if isinstance(result, list) else default
