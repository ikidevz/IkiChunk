from __future__ import annotations

import pickle
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Optional

from ..exceptions import PartitionParallelError


def _call_with_retries(func, item, retries):
    for attempt in range(retries + 1):
        try:
            return func(item)
        except Exception:
            if attempt >= retries:
                raise


def pmap(func, items, *, workers: Optional[int] = None, backend: str = "thread", retries: int = 0, progress: bool = False, ordered: bool = True):
    items = list(items)
    if workers is None:
        workers = max(
            1, min(32, len(items) if hasattr(items, '__len__') else 1))
    if backend not in {"thread", "process"}:
        raise ValueError("backend must be 'thread' or 'process'")
    if backend == "process":
        try:
            pickle.dumps(func)
            for item in items:
                pickle.dumps(item)
        except Exception as exc:
            raise PartitionParallelError(
                "func and items must be picklable for backend='process'") from exc

    if backend == "process":
        executor_cls = ProcessPoolExecutor
    else:
        executor_cls = ThreadPoolExecutor

    with executor_cls(max_workers=workers) as executor:
        futures = [executor.submit(
            _call_with_retries, func, item, retries) for item in items]
        return [future.result() for future in futures]
