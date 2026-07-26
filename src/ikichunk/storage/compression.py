from __future__ import annotations

import gzip
import os
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import Optional

from ..exceptions import MissingDependencyError, UnsafeArchiveError

_REGISTRY = {}


def register_codec(name: str, codec) -> None:
    _REGISTRY[name] = codec


def compress(path: str, *, algo: str = "gzip", out: Optional[str] = None, keep_original: bool = True) -> str:
    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(path)
    if algo == "gzip":
        target = Path(out or str(src) + ".gz")
        with src.open("rb") as fh_in, gzip.open(target, "wb") as fh_out:
            shutil.copyfileobj(fh_in, fh_out)
    elif algo == "zip":
        target = Path(out or str(src) + ".zip")
        with zipfile.ZipFile(target, "w") as zf:
            zf.write(src, arcname=src.name)
    elif algo == "zstd":
        try:
            import zstandard as zstd  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise MissingDependencyError(
                "Optional dependency missing; install with: pip install -e '.[zstd]'") from exc
        target = Path(out or str(src) + ".zst")
        cctx = zstd.ZstdCompressor()
        with src.open("rb") as fh_in, open(target, "wb") as fh_out:
            fh_out.write(cctx.compress(fh_in.read()))
    else:
        raise ValueError("unsupported algo")
    if not keep_original:
        src.unlink(missing_ok=True)
    return str(target)


def decompress(path: str, *, out: Optional[str] = None) -> str:
    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(path)
    if src.suffix == ".gz":
        target = Path(out or str(src).removesuffix(".gz"))
        with gzip.open(src, "rb") as fh_in, target.open("wb") as fh_out:
            shutil.copyfileobj(fh_in, fh_out)
    elif src.suffix == ".zip":
        target = Path(out or src.with_suffix(""))
        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(src, "r") as zf:
            zf.extractall(target)
    elif src.suffix == ".zst":
        try:
            import zstandard as zstd  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise MissingDependencyError(
                "Optional dependency missing; install with: pip install -e '.[zstd]'") from exc
        target = Path(out or str(src).removesuffix(".zst"))
        dctx = zstd.ZstdDecompressor()
        with open(src, "rb") as fh_in, open(target, "wb") as fh_out:
            fh_out.write(dctx.decompress(fh_in.read()))
    else:
        raise ValueError("unsupported archive type")
    return str(target)


def archive(source: str, out_path: str, *, fmt: str = "tar.gz") -> str:
    src = Path(source)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "tar.gz":
        with tarfile.open(out, "w:gz") as tar:
            tar.add(src, arcname=src.name)
    elif fmt == "zip":
        with zipfile.ZipFile(out, "w") as zf:
            if src.is_dir():
                for path in src.rglob("*"):
                    if path.is_file():
                        zf.write(path, arcname=str(path.relative_to(src)))
            else:
                zf.write(src, arcname=src.name)
    else:
        raise ValueError("unsupported format")
    return str(out)


def extract(archive_path: str, *, out_dir: Optional[str] = None) -> str:
    src = Path(archive_path)
    target_dir = Path(out_dir or src.parent / src.stem)
    target_dir.mkdir(parents=True, exist_ok=True)
    if src.suffix == ".gz" and src.name.endswith(".tar.gz"):
        with tarfile.open(src, "r:gz") as tar:
            for member in tar.getmembers():
                _validate_member(member.name)
                member_path = _member_path(target_dir, member.name)
                member_path.parent.mkdir(parents=True, exist_ok=True)
                if member.isdir():
                    member_path.mkdir(parents=True, exist_ok=True)
                else:
                    with tar.extractfile(member) as fh_in, member_path.open("wb") as fh_out:
                        shutil.copyfileobj(fh_in, fh_out)
    elif src.suffix == ".zip":
        with zipfile.ZipFile(src, "r") as zf:
            for member in zf.namelist():
                _validate_member(member)
                member_path = _member_path(target_dir, member)
                member_path.parent.mkdir(parents=True, exist_ok=True)
                if member.endswith("/"):
                    member_path.mkdir(parents=True, exist_ok=True)
                else:
                    with zf.open(member) as fh_in, member_path.open("wb") as fh_out:
                        shutil.copyfileobj(fh_in, fh_out)
    else:
        raise ValueError("unsupported archive")
    return str(target_dir)


def _member_path(target_dir: Path, member_name: str) -> Path:
    parts = Path(member_name).parts
    if len(parts) > 1:
        return target_dir.joinpath(*parts[1:])
    return target_dir / member_name


def _validate_member(member_name: str) -> None:
    if not member_name or member_name in {".", "./"}:
        return
    normalized = member_name.replace("\\", "/")
    if normalized.startswith("/") or normalized.startswith("../") or normalized == ".." or "/../" in normalized or normalized.endswith("/.."):
        raise UnsafeArchiveError(
            "Archive member would escape the target directory")
    parts = [part for part in Path(normalized).parts if part not in {".", ""}]
    if any(part == ".." for part in parts):
        raise UnsafeArchiveError(
            "Archive member would escape the target directory")
    # A directory entry like 'evil' is safe only if it resolves under the target root.
    # For this implementation, any archive member that introduces a root-level path outside
    # the extraction directory is considered unsafe; we reject members whose first component
    # is a path traversal or absolute prefix.
    if parts and parts[0] in {"..", ""}:
        raise UnsafeArchiveError(
            "Archive member would escape the target directory")
