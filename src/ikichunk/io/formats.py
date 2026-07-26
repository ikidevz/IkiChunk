from __future__ import annotations

import csv
import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from ..exceptions import MissingDependencyError, UnknownFormatError


@dataclass(frozen=True)
class FormatHandler:
    name: str
    read: Callable[[Path, dict], Any]
    write: Callable[[Path, Any, dict], None]


def _read_json(p: Path, kwargs: dict) -> Any:
    return json.loads(p.read_text(encoding=kwargs.get("encoding", "utf-8")))


def _write_json(p: Path, data: Any, kwargs: dict) -> None:
    p.write_text(json.dumps(data, indent=kwargs.get(
        "indent", 2), default=str), encoding="utf-8")


def _read_yaml(p: Path, kwargs: dict) -> Any:
    text = p.read_text(encoding=kwargs.get("encoding", "utf-8"))
    return _simple_yaml_load(text)


def _write_yaml(p: Path, data: Any, kwargs: dict) -> None:
    p.write_text(_simple_yaml_dump(data), encoding="utf-8")


def _parse_yaml_scalar(value: str) -> Any:
    value = value.strip()
    if not value or value in {"null", "~"}:
        return None
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _simple_yaml_load(text: str) -> Any:
    result: Any = {}
    current_list: Optional[list] = None
    current_item: Optional[dict] = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- "):
            item_text = stripped[2:].strip()
            if current_list is None:
                current_list = []
                result = current_list
            if ":" in item_text:
                key, value = item_text.split(":", 1)
                current_item = {key.strip(): _parse_yaml_scalar(value)}
                current_list.append(current_item)
            else:
                current_item = None
                current_list.append(_parse_yaml_scalar(item_text))
            continue

        if current_list is not None and current_item is not None and isinstance(current_item, dict):
            key, value = stripped.split(":", 1)
            current_item[key.strip()] = _parse_yaml_scalar(value)
            continue

        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        if isinstance(result, dict):
            result[key.strip()] = _parse_yaml_scalar(value)
        else:
            result = {key.strip(): _parse_yaml_scalar(value)}

    return result


def _format_yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, str):
        return value
    return str(value)


def _simple_yaml_dump(data: Any) -> str:
    if isinstance(data, list):
        if not data:
            return "[]\n"
        lines = []
        for item in data:
            if isinstance(item, dict):
                for index, (key, value) in enumerate(item.items()):
                    prefix = "- " if index == 0 else "  "
                    lines.append(
                        f"{prefix}{key}: {_format_yaml_scalar(value)}")
            else:
                lines.append(f"- {_format_yaml_scalar(item)}")
        return "\n".join(lines) + "\n"
    if not isinstance(data, dict):
        return str(data)
    lines = []
    for key, value in data.items():
        lines.append(f"{key}: {_format_yaml_scalar(value)}")
    return "\n".join(lines) + "\n"


def _read_csv(p: Path, kwargs: dict) -> Any:
    with p.open("r", encoding=kwargs.get("encoding", "utf-8"), newline="") as fh:
        reader = csv.DictReader(fh)
        return [dict(row) for row in reader]


def _write_csv(p: Path, data: Any, kwargs: dict) -> None:
    with p.open("w", encoding=kwargs.get("encoding", "utf-8"), newline="") as fh:
        if not data:
            fh.write("")
            return
        writer = csv.DictWriter(fh, fieldnames=list(data[0].keys()))
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def _read_tsv(p: Path, kwargs: dict) -> Any:
    with p.open("r", encoding=kwargs.get("encoding", "utf-8"), newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        return [dict(row) for row in reader]


def _write_tsv(p: Path, data: Any, kwargs: dict) -> None:
    with p.open("w", encoding=kwargs.get("encoding", "utf-8"), newline="") as fh:
        if not data:
            fh.write("")
            return
        writer = csv.DictWriter(fh, fieldnames=list(
            data[0].keys()), delimiter="\t")
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def _read_parquet(p: Path, kwargs: dict) -> Any:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover
        raise MissingDependencyError(
            "Optional dependency missing; install with: pip install -e '.[parquet]'") from exc
    return pq.read_table(p).to_pandas()


def _write_parquet(p: Path, data: Any, kwargs: dict) -> None:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover
        raise MissingDependencyError(
            "Optional dependency missing; install with: pip install -e '.[parquet]'") from exc
    pq.write_table(pa.Table.from_pandas(data), p)


def _read_pickle(p: Path, kwargs: dict) -> Any:
    with p.open("rb") as fh:
        return pickle.load(fh)


def _write_pickle(p: Path, data: Any, kwargs: dict) -> None:
    with p.open("wb") as fh:
        pickle.dump(data, fh)


def _read_text(p: Path, kwargs: dict) -> Any:
    return p.read_text(encoding=kwargs.get("encoding", "utf-8"))


def _write_text(p: Path, data: Any, kwargs: dict) -> None:
    p.write_text(str(data), encoding="utf-8")


REGISTRY: Dict[str, FormatHandler] = {
    "json": FormatHandler("json", _read_json, _write_json),
    "yaml": FormatHandler("yaml", _read_yaml, _write_yaml),
    "csv": FormatHandler("csv", _read_csv, _write_csv),
    "tsv": FormatHandler("tsv", _read_tsv, _write_tsv),
    "parquet": FormatHandler("parquet", _read_parquet, _write_parquet),
    "pickle": FormatHandler("pickle", _read_pickle, _write_pickle),
    "text": FormatHandler("text", _read_text, _write_text),
}

_EXT_MAP = {
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".csv": "csv",
    ".tsv": "tsv",
    ".parquet": "parquet",
    ".pkl": "pickle",
    ".pickle": "pickle",
    ".txt": "text",
    ".md": "text",
    ".log": "text",
}


def register_format(name: str, handler: FormatHandler, extensions: Optional[list] = None) -> None:
    REGISTRY[name] = handler
    if extensions:
        for ext in extensions:
            _EXT_MAP[ext] = name


def detect_fmt(path: Path, fmt: Optional[str]) -> str:
    if fmt:
        return fmt
    candidate = Path(str(path))
    if candidate.exists():
        suffix = candidate.suffix.lower()
        if suffix in _EXT_MAP:
            return _EXT_MAP[suffix]
    suffix = candidate.suffix.lower()
    if suffix in _EXT_MAP:
        return _EXT_MAP[suffix]
    if str(candidate).endswith(".json") or str(candidate).endswith(".yaml") or str(candidate).endswith(".yml") or str(candidate).endswith(".csv") or str(candidate).endswith(".tsv") or str(candidate).endswith(".txt"):
        return _EXT_MAP[Path(str(candidate)).suffix.lower()]
    raise UnknownFormatError(f"Cannot determine format for '{path}'")


def get_handler(fmt: str) -> FormatHandler:
    if fmt not in REGISTRY:
        raise UnknownFormatError(f"Unsupported format '{fmt}'")
    return REGISTRY[fmt]
