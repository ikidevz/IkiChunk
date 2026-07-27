from __future__ import annotations

import functools
from os import PathLike
from pathlib import Path
from typing import Any

from ..io import read as _io_read

_SECRET_KEY_PATTERNS = ("_key", "_token", "_secret",
                        "_password", "password", "secret", "token")


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if any(pattern in str(key).lower() for pattern in _SECRET_KEY_PATTERNS):
                out[key] = "<redacted>"
            else:
                out[key] = redact(item)
        return out
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    if isinstance(value, set):
        return {redact(item) for item in value}
    return value


@functools.singledispatch
def _inspect_obj(obj: Any, sample: int = 3) -> dict:
    return {"type": type(obj).__name__, "repr": repr(obj)[:200]}


@_inspect_obj.register
def _inspect_list(obj: list, sample: int = 3) -> dict:
    info = {"type": "list", "length": len(obj)}
    if obj:
        info["sample"] = redact(obj[:sample])
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


def _inspect_dataframe(obj: Any, sample: int = 3) -> dict:
    sample_rows = [redact(row) for row in obj.head(sample).to_dicts()]
    return {
        "type": "DataFrame",
        "shape": tuple(obj.shape),
        "columns": list(obj.columns),
        "dtypes": {name: str(dtype) for name, dtype in zip(obj.columns, obj.dtypes)},
        "sample": sample_rows,
    }


def _register_polars_inspector() -> None:
    try:
        import polars as pl
    except ImportError:
        return
    if pl.DataFrame not in _inspect_obj.registry:
        register_inspector(pl.DataFrame, _inspect_dataframe)


_register_polars_inspector()


def inspect(obj_or_path: Any, sample: int = 3, **kwargs) -> dict:
    if isinstance(obj_or_path, (str, PathLike)):
        path = Path(obj_or_path)
        if path.exists():
            return _inspect_obj(_io_read(str(path)), sample=sample)
    return _inspect_obj(obj_or_path, sample=sample)


def head(obj_or_path: Any, n: int = 5, **kwargs) -> Any:
    info = inspect(obj_or_path, sample=n, **kwargs)
    return info.get("sample", info)
