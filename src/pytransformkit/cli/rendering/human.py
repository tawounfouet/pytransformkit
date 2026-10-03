"""Human-oriented Rich rendering for CLI reports."""

from __future__ import annotations

from rich.console import Console

from pytransformkit.cli.models.errors import CLIErrorReport
from pytransformkit.cli.models.reports import (
    DoctorReport,
    SchemaValidationReport,
    VersionReport,
)
from pytransformkit.cli.rendering.tables import build_table


class HumanRenderer:
    """Render safe, copyable human output through explicit Rich consoles."""

    def __init__(self, *, stdout: Console, stderr: Console) -> None:
        self._stdout = stdout
        self._stderr = stderr

    def write(self, message: str) -> None:
        """Write a success/report line without interpreting user markup."""
        self._stdout.print(message, markup=False, highlight=False)

    def render_version(self, report: VersionReport) -> None:
        """Render compact version information to stdout."""
        self.write(f"PyTransformKit {report.pytransformkit}")
        self.write(f"Python {report.python}")

    def render_doctor(
        self,
        report: DoctorReport,
        *,
        quiet: bool = False,
        include_detail: bool = False,
    ) -> None:
        """Render local environment diagnostics to stdout."""
        self.write(f"Doctor: {report.status.value}")
        if quiet:
            return

        columns = ["Check", "Status", "Version"]
        if include_detail:
            columns.append("Detail")

        rows: list[tuple[str, ...]] = []
        for check in report.checks:
            values = [
                check.name,
                check.status.value.upper(),
                check.version or "-",
            ]
            if include_detail:
                values.append(check.detail or "-")
            rows.append(tuple(values))

        self._stdout.print(
            build_table(
                columns=columns,
                rows=rows,
            )
        )

    def render_schema_validation(self, report: SchemaValidationReport) -> None:
        """Render a successful schema validation report."""
        self.write(f"Valid schema: {report.path}")

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
