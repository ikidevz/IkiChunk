from __future__ import annotations

from typing import Any, Callable, Iterator, Optional

from . import automation as _automation
from . import concurrency as _concurrency
from . import configuration as _configuration
from . import inspection as _inspection
from . import integrity as _integrity
from . import io as _io
from . import net as _net
from . import observability as _observability
from . import partitioning as _partitioning
from . import plugins as _plugins
from . import resilience as _resilience
from . import storage as _storage
from . import system as _system
from . import templates as _templates
from . import validation as _validation

__version__ = "0.2.0"


class Partition:
    def __init__(self, log_level: str = "INFO", env_prefix: str = "") -> None:
        self.log_level = log_level
        self.env_prefix = env_prefix

    # I/O
    def read(self, path: str, fmt: Optional[str] = None, **kwargs) -> Any:
        return _io.read(path, fmt=fmt, **kwargs)

    def write(self, path: str, data: Any, *, atomic: bool = True, backup: bool = False, fmt: Optional[str] = None, **kwargs) -> str:
        return _io.write(path, data, atomic=atomic, backup=backup, fmt=fmt, **kwargs)

    def exists(self, path: str) -> bool:
        return _io.exists(path)

    def ensure_dir(self, path: str) -> str:
        return _io.ensure_dir(path)

    def list_files(self, path: str = ".", pattern: str = "*", recursive: bool = False) -> list[str]:
        return _io.list_files(path, pattern=pattern, recursive=recursive)

    ls = list_files

    def cat(self, path: str) -> str:
        return _io.cat(path)

    def stream(self, path: str, fmt: Optional[str] = None, chunk_size: Optional[int] = None) -> Iterator[Any]:
        return _io.stream(path, fmt=fmt, chunk_size=chunk_size)

    # Inspect
    def inspect(self, obj_or_path: Any, sample: int = 3, **kwargs) -> dict:
        return _inspection.inspect(obj_or_path, sample=sample, **kwargs)

    def head(self, obj_or_path: Any, n: int = 5, **kwargs) -> Any:
        return _inspection.head(obj_or_path, n=n, **kwargs)

    def redact(self, data: dict) -> dict:
        return _inspection.redact(data)

    # Config
    def config(self, *sources: str, secrets: Optional[str] = None, env_prefix: Optional[str] = None, **kwargs) -> dict:
        return _configuration.load_config(*sources, secrets=secrets, env_prefix=env_prefix or self.env_prefix, **kwargs)

    def env(self, key: str, default: Any = None, cast=str) -> Any:
        return _configuration.env(key, default=default, cast=cast)

    # Logging / time
    def log(self, name: Optional[str] = None, level: Optional[str] = None, **kwargs):
        return _observability.get_logger(name or "partition", level or self.log_level, **kwargs)

    def now(self, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        return _observability.now(fmt)

    def timer(self, name: str = "block"):
        return _observability.timer(name)

    def duration(self, seconds: float) -> str:
        return _observability.duration(seconds)

    # Retry
    def retry(self, tries: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions=(Exception,)) -> Callable:
        return _resilience.retry(tries=tries, delay=delay, backoff=backoff, exceptions=exceptions)

    # Parallel
    def pmap(self, func: Callable, items, *, workers: Optional[int] = None, backend: str = "thread", retries: int = 0, progress: bool = False, ordered: bool = True):
        return _concurrency.pmap(func, items, workers=workers, backend=backend, retries=retries, progress=progress, ordered=ordered)

    # Partitioning
    def split_file(self, path: str, *, by: str = "size", size: Optional[str] = None, rows: Optional[int] = None, count: Optional[int] = None, parts: Optional[int] = None, out_dir: Optional[str] = None, fmt: Optional[str] = None, prefix: Optional[str] = None) -> list[str]:
        return _partitioning.split_file(path, by=by, size=size, rows=rows, count=count, parts=parts, out_dir=out_dir, fmt=fmt, prefix=prefix)

    def smart_split(self, path: str, *, goal: str = "parallel", workers: Optional[int] = None, chunk_size: Optional[int] = None, out_dir: Optional[str] = None, fmt: Optional[str] = None, explain: bool = False):
        return _partitioning.smart_split(path, goal=goal, workers=workers, chunk_size=chunk_size, out_dir=out_dir, fmt=fmt, explain=explain)

    def chunks(self, iterable, size: int):
        return _partitioning.chunks(iterable, size)

    def manifest(self, paths, *, hash_algo: str = "sha256") -> dict:
        return _partitioning.manifest(paths, hash_algo=hash_algo)

    # Integrity
    def hash(self, path_or_bytes, algo: str = "sha256") -> str:
        return _integrity.hash(path_or_bytes, algo=algo)

    def hash_file(self, path: str, algo: str = "sha256") -> str:
        return self.hash(path, algo=algo)

    def verify(self, path: str, expected_hash: str, algo: str = "sha256") -> bool:
        return _integrity.verify(path, expected_hash, algo=algo)

    # Storage
    def compress(self, path: str, *, algo: str = "gzip", out: Optional[str] = None, keep_original: bool = True) -> str:
        return _storage.compress(path, algo=algo, out=out, keep_original=keep_original)

    def decompress(self, path: str, *, out: Optional[str] = None) -> str:
        return _storage.decompress(path, out=out)

    def archive(self, source: str, out_path: str, *, fmt: str = "tar.gz") -> str:
        return _storage.archive(source, out_path, fmt=fmt)

    def extract(self, archive_path: str, *, out_dir: Optional[str] = None) -> str:
        return _storage.extract(archive_path, out_dir=out_dir)

    def register_codec(self, name: str, codec) -> None:
        _storage.register_codec(name, codec)

    # System/platform/process/net
    def platform_info(self) -> dict:
        return _system.platform_info()

    def which(self, cmd: str) -> Optional[str]:
        return _system.which(cmd)

    def normalize_path(self, path: str) -> str:
        return _system.normalize_path(path)

    def is_running(self, pid: int) -> bool:
        return _system.is_running(pid)

    def is_port_open(self, host: str, port: int, timeout: float = 0.2) -> bool:
        return _system.is_port_open(host, port, timeout=timeout)

    def run(self, command, *, check: bool = False, shell: bool = False, timeout: Optional[float] = None):
        return _system.run(command, check=check, shell=shell, timeout=timeout)

    def fetch(self, url: str, *, timeout: float = 5.0) -> str:
        return _net.fetch(url, timeout=timeout)

    def render(self, template: str, variables: dict, *, out: Optional[str] = None, strict: bool = True) -> str:
        return _templates.render(template, variables, out=out, strict=strict)

    # Validation and plugins
    def register_format(self, name: str, handler, extensions: Optional[list[str]] = None) -> None:
        _io.register_format(name, handler, extensions=extensions)

    def register_split_goal(self, name: str, fn: Callable[[int, dict, int], dict]) -> None:
        _partitioning.register_goal(name, fn)

    def validate(self, value: Any, schema: Optional[dict] = None) -> bool:
        return _validation.validate(value, schema=schema)


def load_plugins(instance: Partition) -> None:
    _plugins.load_plugins(instance)
