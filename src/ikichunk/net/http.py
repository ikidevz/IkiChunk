from __future__ import annotations

import urllib.request


def fetch(url: str, *, timeout: float = 5.0) -> str:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read().decode("utf-8")
