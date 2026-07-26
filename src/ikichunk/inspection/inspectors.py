from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

from ..io import read as _io_read

_SECRET_KEY_PATTERNS = ("_key", "_token", "_secret",
                        "_password", "password", "secret", "token")


def redact(d: dict) -> dict:
    out = {}
    for key, value in d.items():
        if any(pattern in str(key).lower() for pattern in _SECRET_KEY_PATTERNS):
            out[key] = "<redacted>"
        else:
            out[key] = value
    return out


@functools.singledispatch
def _inspect_obj(obj: Any, sample: int = 3) -> dict:
    return {"type": type(obj).__name__, "repr": repr(obj)[:200]}


@_inspect_obj.register
def _inspect_list(obj: list, sample: int = 3) -> dict:
    info = {"type": "list", "length": len(obj)}
    if obj:
        info["sample"] = obj[:sample]
    return info


@_inspect_obj.register
def _inspect_dict(obj: dict, sample: int = 3) -> dict:
    return {"type": "dict", "keys": list(obj.keys()), "sample": redact(dict(list(obj.items())[:sample]))}


@_inspect_obj.register
def _inspect_str(obj: str, sample: int = 3) -> dict:
    lines = obj.splitlines()
    return {"type": "text", "length": len(obj), "lines": len(lines), "sample": lines[:sample]}


def register_inspector(python_type, func) -> None:
    _inspect_obj.register(python_type, func)


def inspect(obj_or_path: Any, sample: int = 3, **kwargs) -> dict:
    if isinstance(obj_or_path, str) and Path(obj_or_path).exists():
        return _inspect_obj(_io_read(obj_or_path), sample=sample)
    return _inspect_obj(obj_or_path, sample=sample)


def head(obj_or_path: Any, n: int = 5, **kwargs) -> Any:
    info = inspect(obj_or_path, sample=n, **kwargs)
    return info.get("sample", info)
