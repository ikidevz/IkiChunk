from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def hash(path_or_bytes, algo: str = "sha256") -> str:
    hasher = hashlib.new(algo)
    if isinstance(path_or_bytes, (bytes, bytearray)):
        hasher.update(bytes(path_or_bytes))
        return hasher.hexdigest()
    path = Path(path_or_bytes)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify(path: str, expected_hash: str, algo: str = "sha256") -> bool:
    return hash(path, algo=algo) == expected_hash
