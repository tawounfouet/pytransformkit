"""Retry-safety semantics for bounded physical I/O operations."""

from enum import StrEnum


class RetrySafety(StrEnum):
    """Whether repeating one provider I/O operation is known to be safe."""

    SAFE = "safe"
    UNSAFE = "unsafe"
    UNKNOWN = "unknown"
    REQUIRES_RECONCILIATION = "requires_reconciliation"
