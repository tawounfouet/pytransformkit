"""Rich console construction for human CLI rendering."""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Console


@dataclass(frozen=True, slots=True)
class ConsolePair:
    """Separate Rich consoles for stdout and stderr."""

    stdout: Console
    stderr: Console


def create_console_pair(*, color: bool = True) -> ConsolePair:
    """Create consistently configured stdout and stderr consoles."""
    force_terminal = None if color else False
    return ConsolePair(
        stdout=Console(
            stderr=False,
            no_color=not color,
            force_terminal=force_terminal,
        ),
        stderr=Console(
            stderr=True,
            no_color=not color,
            force_terminal=force_terminal,
        ),
    )


__all__ = ["ConsolePair", "create_console_pair"]
