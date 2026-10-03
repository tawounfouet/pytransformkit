"""Output classification for CLI command contracts."""

from __future__ import annotations

from enum import StrEnum


class OutputKind(StrEnum):
    """Whether a command produces a CLI report or a canonical payload."""

    REPORT = "report"
    PAYLOAD = "payload"


__all__ = ["OutputKind"]
