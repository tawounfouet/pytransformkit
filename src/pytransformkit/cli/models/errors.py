"""Presentation-neutral CLI error models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from pytransformkit.cli.exit_codes import ExitCode


class ErrorCategory(StrEnum):
    """Stable error categories for the CLI v1 contract."""

    GENERAL_ERROR = "general_error"
    INVALID_USAGE = "invalid_usage"
    INVALID_SCHEMA = "invalid_schema"
    MISSING_OPTIONAL_DEPENDENCY = "missing_optional_dependency"
    FILESYSTEM_ERROR = "filesystem_error"
    UNSUPPORTED_OPERATION = "unsupported_operation"
    INTERNAL_ERROR = "internal_error"
    INTERRUPTED = "interrupted"
    BROKEN_PIPE = "broken_pipe"

@dataclass(frozen=True, slots=True)
class CLIErrorReport:
    """Safe, renderer-neutral description of a CLI failure."""

    category: ErrorCategory
    message: str
    exit_code: ExitCode
    code: str | None = None
    path: str | None = None
    hint: str | None = None
    details: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("CLI error message must not be empty.")
        if self.code is not None and not self.code.strip():
            raise ValueError("CLI error code must contain non-whitespace text.")
        if self.path is not None and not self.path.strip():
            raise ValueError("CLI error path must contain non-whitespace text.")
        if self.hint is not None and not self.hint.strip():
            raise ValueError("CLI error hint must contain non-whitespace text.")
        if self.details is not None:
            object.__setattr__(
                self,
                "details",
                MappingProxyType(dict(self.details)),
            )

    def to_public_dict(self) -> dict[str, object]:
        """Return the stable machine-facing error payload."""
        payload: dict[str, object] = {
            "category": self.category.value,
            "message": self.message,
        }
        if self.code is not None:
            payload["code"] = self.code
        if self.path is not None:
            payload["path"] = self.path
        if self.hint is not None:
            payload["hint"] = self.hint
        if self.details is not None:
            payload["details"] = dict(self.details)
        return payload

__all__ = ["CLIErrorReport", "ErrorCategory"]
