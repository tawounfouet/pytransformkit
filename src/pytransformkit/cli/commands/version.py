"""Version command wiring."""

from __future__ import annotations

import typer

from pytransformkit.cli.context import CLIContext, OutputMode
from pytransformkit.cli.exit_codes import ExitCode
from pytransformkit.cli.rendering.console import create_console_pair
from pytransformkit.cli.rendering.errors import render_cli_error
from pytransformkit.cli.rendering.human import HumanRenderer
from pytransformkit.cli.rendering.json import JSONRenderer
from pytransformkit.cli.rendering.output import emit_stdout
from pytransformkit.cli.services.version import VersionService

COMMAND_ID = "version"


def render_version(
    *,
    json_output: bool = False,
    no_color: bool = False,
) -> ExitCode:
    """Collect and render version metadata in the requested output mode."""
    context = CLIContext.from_options(
        json_output=json_output,
        no_color=no_color,
    )
    try:
        report = VersionService().inspect()
    except (Exception, KeyboardInterrupt) as exc:
        return render_cli_error(
            exc,
            command=COMMAND_ID,
            json_output=json_output,
            debug=False,
            no_color=no_color,
        )

    if context.output_mode is OutputMode.JSON:
        return emit_stdout(
            lambda: typer.echo(
                JSONRenderer().render_success(
                    command=COMMAND_ID,
                    data=report.to_data(),
                ),
                nl=False,
            )
        )

    consoles = create_console_pair(color=context.color)
    return emit_stdout(
        lambda: HumanRenderer(
            stdout=consoles.stdout,
            stderr=consoles.stderr,
        ).render_version(report)
    )


def version_command(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit the CLI v1 machine-readable report.",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable ANSI color in human output.",
    ),
) -> None:
    """Show the installed PyTransformKit and Python versions."""
    exit_code = render_version(json_output=json_output, no_color=no_color)
    if exit_code is not ExitCode.SUCCESS:
        raise typer.Exit(code=int(exit_code))


__all__ = ["COMMAND_ID", "render_version", "version_command"]
