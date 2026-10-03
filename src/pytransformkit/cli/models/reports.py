"""Shared primitives for presentation-neutral CLI reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

ReportData: TypeAlias = dict[str, object]


@dataclass(frozen=True, slots=True)
class VersionReport:
    """Installed PyTransformKit and Python version metadata."""

    pytransformkit: str
    python: str

    def to_data(self) -> ReportData:
        """Return the machine-facing version report payload."""
        return {
            "pytransformkit": self.pytransformkit,
            "python": self.python,
        }


__all__ = ["ReportData", "VersionReport"]
