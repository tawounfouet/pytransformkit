"""Stable public error codes."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ErrorCode:
    """Stable machine-readable error identifier."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("Error code must not be empty.")

    def __str__(self) -> str:
        return self.value
