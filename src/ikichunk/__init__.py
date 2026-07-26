from __future__ import annotations

from .facade import Partition, __version__, load_plugins

partition = Partition()
load_plugins(partition)

__all__ = ["partition", "Partition", "__version__"]
