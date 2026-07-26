from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path
from typing import Any, Iterator, Optional

from ..exceptions import UnknownFormatError
from ..io import read as _io_read
from ..io import write as _io_write
from ..io.formats import detect_fmt

_GOALS = {}


def register_goal(name: str, fn) -> None:
    _GOALS[name] = fn


def split_file(path: str, *, by: str = "size", size: Optional[str] = None, rows: Optional[int] = None, count: Optional[int] = None, parts: Optional[int] = None, out_dir: Optional[str] = None, fmt: Optional[str] = None, prefix: Optional[str] = None) -> list[str]:
    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(path)
    if parts is not None:
        by = "count"
        count = parts
    out_dir_path = Path(out_dir or src.parent / "parts")
    out_dir_path.mkdir(parents=True, exist_ok=True)
    prefix = prefix or src.stem
    fmt_name = detect_fmt(src, fmt)
    if by == "rows":
        if rows is None or rows <= 0:
            raise ValueError("rows must be positive")
        return _split_rows(src, rows, out_dir_path, prefix, fmt_name)
    if by == "count":
        if count is None or count <= 0:
            raise ValueError("count must be positive")
        return _split_count(src, count, out_dir_path, prefix, fmt_name)
    if by == "size":
        return _split_size(src, size or "1MB", out_dir_path, prefix)
    raise ValueError("by must be one of: size, rows, count")


def _split_rows(src: Path, rows: int, out_dir: Path, prefix: str, fmt: Optional[str] = None) -> list[str]:
    fmt_name = fmt or "csv"
    delimiter = "\t" if fmt_name.lower() == "tsv" else ","
    results = []
    with src.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh, delimiter=delimiter)
        header = next(reader)
        batch = [header]
        for row in reader:
            batch.append(row)
            if len(batch) - 1 >= rows:
                target = out_dir / f"{prefix}.part{len(results)+1}.{fmt_name}"
                _write_rows(target, batch, delimiter)
                results.append(str(target))
                batch = [header]
        if len(batch) > 1:
            target = out_dir / f"{prefix}.part{len(results)+1}.{fmt or 'csv'}"
            _write_rows(target, batch, delimiter)
            results.append(str(target))
    return results


def _write_rows(path: Path, rows: list[list[str]], delimiter: str = ",") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter=delimiter)
        writer.writerows(rows)


def _split_count(src: Path, count: int, out_dir: Path, prefix: str, fmt: Optional[str] = None) -> list[str]:
    fmt_name = fmt or "csv"
    delimiter = "\t" if fmt_name.lower() == "tsv" else ","
    rows = []
    with src.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh, delimiter=delimiter)
        header = next(reader)
        for row in reader:
            rows.append(row)
    chunk_size = len(rows) // count
    remainder = len(rows) % count
    results = []
    start = 0
    for idx in range(count):
        take = chunk_size + (1 if idx < remainder else 0)
        target = out_dir / f"{prefix}.part{idx+1}.{fmt_name}"
        with target.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh, delimiter=delimiter)
            writer.writerow(header)
            writer.writerows(rows[start:start+take])
        start += take
        results.append(str(target))
    return results


def _split_size(src: Path, size: str, out_dir: Path, prefix: str) -> list[str]:
    size_bytes = _parse_size(size)
    with src.open("rb") as fh:
        data = fh.read(size_bytes)
        if not data:
            return []
        chunk = data
        parts = []
        index = 1
        while chunk:
            target = out_dir / f"{prefix}.part{index}.bin"
            target.write_bytes(chunk)
            parts.append(str(target))
            chunk = fh.read(size_bytes)
            index += 1
        return parts


def _parse_size(value: str | int) -> int:
    if isinstance(value, int):
        return value
    value = str(value).strip().upper()
    if value.endswith("MB"):
        return int(value[:-2]) * 1024 * 1024
    if value.endswith("KB"):
        return int(value[:-2]) * 1024
    if value.endswith("GB"):
        return int(value[:-2]) * 1024 * 1024 * 1024
    return int(value)


def smart_split(path: str, *, goal: str = "parallel", workers: Optional[int] = None, chunk_size: Optional[int] = None, out_dir: Optional[str] = None, fmt: Optional[str] = None, explain: bool = False):
    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(path)
    if chunk_size is not None:
        workers = chunk_size
    if goal == "parallel":
        count = workers or 1
        strategy = {"by": "count", "count": count}
    elif goal == "memory-safe":
        strategy = {"by": "size", "size": 256 * 1024 * 1024}
    elif goal == "storage":
        strategy = {"by": "size", "size": 100 * 1024 * 1024}
    else:
        strategy = _GOALS.get(goal, lambda *args, **kwargs: {"by": "size", "size": 1 * 1024 * 1024})(
            src.stat().st_size, {"goal": goal}, workers or 1)
    parts = split_file(path, by=strategy["by"], size=strategy.get(
        "size"), rows=strategy.get("rows"), count=strategy.get("count"), out_dir=out_dir)
    why = {"goal": goal, "cpu_count": 1, "partition_count": len(
        parts), "chosen_strategy": strategy}
    if explain:
        return parts, why
    return parts


def chunks(iterable, size: int) -> Iterator[list]:
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]


def manifest(paths, *, hash_algo: str = "sha256") -> dict:
    if isinstance(paths, (str, os.PathLike)):
        items = [paths]
    else:
        items = list(paths)

    files = []
    for path in items:
        p = Path(path)
        if not p.exists():
            continue
        h = hashlib.new(hash_algo)
        with p.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        files.append(
            {"path": str(p), "size_bytes": p.stat().st_size, "hash": h.hexdigest()})
    return {"algo": hash_algo, "files": files}
