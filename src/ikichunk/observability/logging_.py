from __future__ import annotations

import logging

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_configured: set = set()


def get_logger(name: str = "partition", level: str = "INFO", **kwargs) -> logging.Logger:
    logger = logging.getLogger(name)
    if name not in _configured:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        logger.propagate = False
        _configured.add(name)
    return logger
