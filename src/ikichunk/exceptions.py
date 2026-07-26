from __future__ import annotations


class IkichunkError(Exception):
    """Base exception for intentionally raised ikichunk errors."""


class UnknownFormatError(IkichunkError):
    """Raised when a file format cannot be determined safely."""


class MissingDependencyError(IkichunkError, ImportError):
    """Raised when an optional dependency is missing."""


class UnsafeCommandError(IkichunkError):
    """Raised when a shell command string is considered unsafe."""


class PartitionParallelError(IkichunkError):
    """Raised when process-based parallel execution cannot be pickled."""


class UnsafeArchiveError(IkichunkError):
    """Raised when an archive would extract outside the target directory."""
