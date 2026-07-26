from __future__ import annotations

import contextlib
import time as _stdlib_time
from datetime import datetime


def now(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return datetime.now().strftime(fmt)


@contextlib.contextmanager
def timer(name: str = "block"):
    start = _stdlib_time.perf_counter()
    try:
        yield
    finally:
        elapsed = _stdlib_time.perf_counter() - start
        print(f"[{name}] {elapsed:.2f}s")


def duration(seconds: float) -> str:
    seconds = int(seconds)
    parts = []
    if seconds >= 3600:
        parts.append(f"{seconds // 3600}h")
        seconds %= 3600
    if seconds >= 60:
        parts.append(f"{seconds // 60}m")
        seconds %= 60
    parts.append(f"{seconds}s")
    return " ".join(parts)
