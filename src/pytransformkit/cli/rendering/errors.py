"""Helpers for routing CLI errors to the selected presentation mode."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

import typer

from pytransformkit.cli.context import CLIContext, OutputMode
from pytransformkit.cli.exceptions import error_report_from_exception
from pytransformkit.cli.exit_codes import ExitCode
from pytransformkit.cli.models.errors import CLIErrorReport
from pytransformkit.cli.rendering.console import create_console_pair
from pytransformkit.cli.rendering.human import HumanRenderer
from pytransformkit.cli.rendering.json import JSONRenderer
from pytransformkit.cli.rendering.output import emit_stdout


def render_error_json(
    report: CLIErrorReport,
    *,
    command: str,
    renderer: JSONRenderer,
) -> str:
    """Render an error using the machine report contract."""
    return renderer.render_error(command=command, error=report)


def render_error_human(
    report: CLIErrorReport,
    *,
    renderer: HumanRenderer,
) -> None:
    """Render an error through the human stderr channel."""
    renderer.render_error(report)


def render_cli_error(
    exc: BaseException,
    *,
    command: str,
    json_output: bool,
    debug: bool,
    no_color: bool,
    path: str | Path | None = None,
) -> ExitCode:
    """Render one controlled CLI error with stable stream semantics."""
    context = CLIContext.from_options(
        json_output=json_output,
        debug=debug,
        no_color=no_color,
    )
    report = error_report_from_exception(exc, path=path)

    if context.output_mode is OutputMode.JSON:
        output_code = emit_stdout(
            lambda: typer.echo(
                JSONRenderer().render_error(
                    command=command,
                    error=report,
                ),
                nl=False,
            )
        )
        if output_code is not ExitCode.SUCCESS:
            return output_code
    else:
        consoles = create_console_pair(color=context.color)
        HumanRenderer(
            stdout=consoles.stdout,
            stderr=consoles.stderr,
        ).render_error(report)

    if context.debug and report.exit_code is ExitCode.INTERNAL_ERROR:
        traceback.print_exception(exc, file=sys.stderr)

    return report.exit_code


__all__ = [
    "render_cli_error",
    "render_error_human",
    "render_error_json",
]
