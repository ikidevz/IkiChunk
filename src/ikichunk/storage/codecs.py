from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict


@dataclass(frozen=True)
class Codec:
    name: str
    default_ext: str
    compress_fn: Callable[[str, str], str]
    decompress_fn: Callable[[str, str], str]


_REGISTRY: Dict[str, Codec] = {}


def register_codec(name: str, codec: Codec) -> None:
    _REGISTRY[name] = codec
