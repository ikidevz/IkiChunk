from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Callable


def atomic_write(target: Path, serialize: Callable[[Path], None]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=target.name + ".", dir=str(target.parent))
    os.close(fd)
    tmp = Path(tmp_path)
    try:
        serialize(tmp)
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
