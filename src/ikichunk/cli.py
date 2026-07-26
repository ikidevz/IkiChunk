from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import partition


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ikichunk")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("path")
    inspect_parser.set_defaults(func=_cmd_inspect)

    split_parser = subparsers.add_parser("split")
    split_parser.add_argument("path")
    split_parser.add_argument("--rows", type=int, default=100)
    split_parser.set_defaults(func=_cmd_split)

    return parser


def _cmd_inspect(args: argparse.Namespace) -> int:
    print(json.dumps(partition.inspect(args.path), indent=2))
    return 0


def _cmd_split(args: argparse.Namespace) -> int:
    parts = partition.split_file(args.path, by="rows", rows=args.rows, out_dir=str(
        Path(args.path).parent / "parts"))
    print(json.dumps(parts, indent=2))
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)
