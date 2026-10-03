"""Human-oriented Rich rendering for CLI reports."""

from __future__ import annotations

from rich.console import Console

from pytransformkit.cli.models.errors import CLIErrorReport


class HumanRenderer:
    """Render safe, copyable human output through explicit Rich consoles."""

    def __init__(self, *, stdout: Console, stderr: Console) -> None:
        self._stdout = stdout
        self._stderr = stderr

    def write(self, message: str) -> None:
        """Write a success/report line without interpreting user markup."""
        self._stdout.print(message, markup=False, highlight=False)

    def render_error(self, report: CLIErrorReport) -> None:
        """Render a controlled error to stderr."""
        self._stderr.print("Error", style="bold red", markup=False)
        if report.code is not None:
            self._stderr.print(report.code, style="bold", markup=False)
        self._stderr.print(report.message, markup=False, highlight=False)
        if report.path is not None:
            self._stderr.print(f"Path: {report.path}", markup=False, highlight=False)
        if report.hint is not None:
            self._stderr.print(
                f"Hint: {report.hint}",
                markup=False,
                highlight=False,
            )


__all__ = ["HumanRenderer"]
