"""Logical field paths."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FieldPath:
    """Immutable path to a logical field, including future nested fields."""

    parts: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.parts, tuple):
            raise TypeError("Field path parts must be provided as a tuple.")
        if not self.parts:
            raise ValueError("Field path must contain at least one part.")
        if any(not part or not part.strip() for part in self.parts):
            raise ValueError("Field path parts must not be empty.")

    @classmethod
    def of(cls, value: str) -> FieldPath:
        """Parse a dot-separated field path."""
        if not value or not value.strip():
            raise ValueError("Field path must not be empty.")
        return cls(tuple(value.split(".")))

    @property
    def name(self) -> str:
        """Return the final component of the path."""
        return self.parts[-1]

    def __str__(self) -> str:
        return ".".join(self.parts)
