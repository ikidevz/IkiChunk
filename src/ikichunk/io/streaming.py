from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterator, Optional

from ..exceptions import UnknownFormatError
from .formats import detect_fmt


def stream(path: str, fmt: Optional[str] = None, chunk_size: Optional[int] = None) -> Iterator[Any]:
    p = Path(path)
    fmt_name = detect_fmt(p, fmt)
    if fmt_name == "json":
        with p.open("r", encoding="utf-8") as fh:
            for line in fh:
                yield json.loads(line)
    elif fmt_name in {"csv", "tsv"}:
        delimiter = "," if fmt_name == "csv" else "\t"
        with p.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh, delimiter=delimiter)
            for row in reader:
                yield row
    else:
        raise UnknownFormatError(
            f"Streaming unsupported for format '{fmt_name}'")
