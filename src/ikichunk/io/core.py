from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, List, Optional

from .atomic import atomic_write
from .formats import detect_fmt, get_handler


def read(path: str, fmt: Optional[str] = None, **kwargs) -> Any:
    p = Path(path)
    handler = get_handler(detect_fmt(p, fmt))
    return handler.read(p, kwargs)


def write(path: str, data: Any, *, atomic: bool = True, backup: bool = False, fmt: Optional[str] = None, **kwargs) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    resolved_fmt = fmt or detect_fmt(p, None)
    if atomic:
        atomic_write(p, lambda tmp: _serialize(
            tmp, data, fmt=resolved_fmt, **kwargs))
    else:
        _serialize(p, data, fmt=resolved_fmt, **kwargs)
    if backup and p.exists():
        backup_path = p.with_suffix(p.suffix + ".bak")
        shutil.copy2(p, backup_path)
    return str(p)


def _serialize(path: Path, data: Any, *, fmt: Optional[str] = None, **kwargs) -> None:
    handler = get_handler(detect_fmt(path, fmt))
    handler.write(path, data, kwargs)


def exists(path: str) -> bool:
    return Path(path).exists()


def ensure_dir(path: str) -> str:
    Path(path).mkdir(parents=True, exist_ok=True)
    return str(path)


def list_files(path: str = ".", pattern: str = "*", recursive: bool = False) -> List[str]:
    base = Path(path)
    if recursive:
        matches = [p for p in base.rglob(pattern) if p.is_file()]
    else:
        matches = [p for p in base.glob(pattern) if p.is_file()]
    return sorted(str(p) for p in matches)


def cat(path: str) -> str:
    return read(path, fmt="text")
