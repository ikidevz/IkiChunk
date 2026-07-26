from __future__ import annotations

import os
from typing import Any, Optional

from ..io import cat as _io_cat
from ..io import read as _io_read


def load_config(*sources: str, secrets: Optional[str] = None, env_prefix: str = "", **kwargs) -> dict:
    merged: dict = {}
    for source in sources:
        if os.path.exists(source):
            data = _io_read(source)
            if isinstance(data, dict):
                merged.update(data)
    if secrets and os.path.exists(secrets):
        merged.update(_parse_dotenv(secrets))
    if env_prefix:
        env_items = {k[len(env_prefix):]: v for k,
                     v in os.environ.items() if k.startswith(env_prefix)}
        merged.update(env_items)
    return merged


def _parse_dotenv(path: str) -> dict:
    out: dict = {}
    for line in _io_cat(path).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def env(key: str, default: Any = None, cast=str) -> Any:
    if key not in os.environ:
        return default
    value = os.environ[key]
    if cast is str:
        return value
    return cast(value)
