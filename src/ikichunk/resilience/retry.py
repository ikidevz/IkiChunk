from __future__ import annotations

import functools
import time as _stdlib_time


def retry(tries: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(tries):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == tries - 1:
                        raise
                    _stdlib_time.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator
