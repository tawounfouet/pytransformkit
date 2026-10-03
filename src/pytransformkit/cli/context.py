"""Presentation-only context for PyTransformKit CLI commands."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pytransformkit.cli.exceptions import CLIUsageError


class OutputMode(StrEnum):
    """Supported report output modes."""

    HUMAN = "human"
    JSON = "json"


@dataclass(frozen=True, slots=True)
class CLIContext:
    """Command presentation context with no project or runtime state."""

    output_mode: OutputMode = OutputMode.HUMAN
    quiet: bool = False
    verbose: bool = False
    debug: bool = False
    color: bool = True

    def __post_init__(self) -> None:
        if self.quiet and self.verbose:
            raise CLIUsageError("--quiet and --verbose cannot be used together.")
        if self.quiet and self.debug:
            raise CLIUsageError("--quiet and --debug cannot be used together.")
        if self.output_mode is OutputMode.JSON and self.verbose:
            raise CLIUsageError("--json and --verbose cannot be used together.")


__all__ = ["CLIContext", "OutputMode"]
