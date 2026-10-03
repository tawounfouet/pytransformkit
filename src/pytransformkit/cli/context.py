"""Presentation-only context for PyTransformKit CLI commands."""

from __future__ import annotations

import os
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

    @classmethod
    def from_options(
        cls,
        *,
        json_output: bool = False,
        quiet: bool = False,
        verbose: bool = False,
        debug: bool = False,
        no_color: bool = False,
    ) -> "CLIContext":
        """Build a presentation context from public CLI output options."""
        return cls(
            output_mode=OutputMode.JSON if json_output else OutputMode.HUMAN,
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            color=not no_color and "NO_COLOR" not in os.environ,
        )

    def __post_init__(self) -> None:
        if self.quiet and self.verbose:
            raise CLIUsageError("--quiet and --verbose cannot be used together.")
        if self.quiet and self.debug:
            raise CLIUsageError("--quiet and --debug cannot be used together.")
        if self.output_mode is OutputMode.JSON and self.verbose:
            raise CLIUsageError("--json and --verbose cannot be used together.")


__all__ = ["CLIContext", "OutputMode"]
