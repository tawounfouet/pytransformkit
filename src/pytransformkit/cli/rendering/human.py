"""Human-oriented Rich rendering for CLI reports."""

from __future__ import annotations

import json

from rich.console import Console

from pytransformkit.cli.models.errors import CLIErrorReport
from pytransformkit.cli.models.reports import (
    DoctorReport,
    EngineInspectionReport,
    EngineListReport,
    SchemaInspectionReport,
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

    def render_engine_list(
        self,
        report: EngineListReport,
        *,
        quiet: bool = False,
        include_detail: bool = False,
    ) -> None:
        """Render official engine availability and qualification."""
        if quiet:
            for engine in report.engines:
                self.write(engine.id)
            return

        columns = ["Engine", "Installed", "Qualification", "Version"]
        if include_detail:
            columns.append("Detail")

        rows: list[tuple[str, ...]] = []
        for engine in report.engines:
            values = [
                engine.id,
                "yes" if engine.installed else "no",
                engine.qualification.upper(),
                engine.version or "-",
            ]
            if include_detail:
                detail = engine.detail
                if detail is None and engine.missing_dependencies:
                    detail = (
                        "missing: " + ", ".join(engine.missing_dependencies)
                    )
                values.append(detail or "-")
            rows.append(tuple(values))

        self._stdout.print(build_table(columns=columns, rows=rows))

    def render_engine_inspection(
        self,
        report: EngineInspectionReport,
        *,
        include_detail: bool = False,
    ) -> None:
        """Render static metadata for one official engine."""
        engine = report.engine
        self.write(f"Engine: {engine.id}")
        self.write(f"Installed: {'yes' if engine.installed else 'no'}")
        self.write(f"Qualification: {engine.qualification.upper()}")
        self.write(f"Version: {engine.version or '-'}")
        self.write(
            "Mandatory for V1: "
            + ("yes" if report.mandatory_for_v1 else "no")
        )
        if engine.missing_dependencies:
            self.write(
                "Missing dependencies: "
                + ", ".join(engine.missing_dependencies)
            )
        if engine.detail is not None:
            self.write(f"Detail: {engine.detail}")

        self._stdout.print(
            build_table(
                columns=["Capability"],
                rows=((capability,) for capability in report.capabilities),
            )
        )

        if include_detail:
            self._stdout.print(
                build_table(
                    columns=["Conformance dimension", "Status"],
                    rows=(
                        (dimension.name, dimension.status.upper())
                        for dimension in report.conformance
                    ),
                )
            )

    def render_schema_validation(self, report: SchemaValidationReport) -> None:
        """Render a successful schema validation report."""
        self.write(f"Valid schema: {report.path}")

    def render_schema_inspection(
        self,
        report: SchemaInspectionReport,
        *,
        include_details: bool = False,
    ) -> None:
        """Render one logical schema and its fields."""
        self.write(f"Schema: {report.schema_name}")
        self.write(f"Path: {report.path}")

        columns = ["Name", "Type", "Nullable", "Description"]
        if include_details:
            columns.append("Type details")

        rows: list[tuple[str, ...]] = []
        for field in report.fields:
            values = [
                field.name,
                field.type,
                "yes" if field.nullable else "no",
                field.description or "-",
            ]
            if include_details:
                details = (
                    json.dumps(
                        field.type_details,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    if field.type_details is not None
                    else "-"
                )
                values.append(details)
            rows.append(tuple(values))

        self._stdout.print(
            build_table(
                columns=columns,
                rows=rows,
            )
        )

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
