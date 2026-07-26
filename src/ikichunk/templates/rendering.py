from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional


class RenderResult(str):
    def __new__(cls, value: str, *, path: Optional[str] = None):
        obj = super().__new__(cls, value)
        obj.path = path
        return obj


def render(template: str, variables: dict[str, Any], *, out: Optional[str] = None, strict: bool = True) -> str:
    pattern = re.compile(r"\$(\w+)")

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in variables:
            if strict:
                raise KeyError(
                    f"Missing template variable: '{key}'. Pass strict=False to allow partial renders.")
            return match.group(0)
        return str(variables[key])

    rendered = pattern.sub(replace, template)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(rendered, encoding="utf-8")
    return rendered
