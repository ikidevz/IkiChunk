from __future__ import annotations

from typing import Any, Optional


def validate(value: Any, schema: Optional[dict] = None) -> bool:
    if schema is None:
        return True
    if isinstance(schema, dict):
        if not isinstance(value, dict):
            return False
        for key, sub_schema in schema.items():
            if key not in value:
                return False
            if not validate(value[key], sub_schema):
                return False
        return True
    if isinstance(schema, list):
        return isinstance(value, list) and all(validate(item, schema[0]) for item in value)
    return isinstance(value, schema)
