"""Version command wiring."""

from __future__ import annotations

import typer

from pytransformkit.cli.rendering.console import create_console_pair
from pytransformkit.cli.rendering.human import HumanRenderer
from pytransformkit.cli.rendering.json import JSONRenderer
from pytransformkit.cli.services.version import VersionService

COMMAND_ID = "version"


def render_version(
    *,
    json_output: bool = False,
    no_color: bool = False,
) -> None:
    """Collect and render version metadata in the requested output mode."""
    report = VersionService().inspect()

    if json_output:
        typer.echo(
            JSONRenderer().render_success(
                command=COMMAND_ID,
                data=report.to_data(),
            ),
            nl=False,
        )
        return

    consoles = create_console_pair(color=not no_color)
    HumanRenderer(
        stdout=consoles.stdout,
        stderr=consoles.stderr,
    ).render_version(report)


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
    render_version(json_output=json_output, no_color=no_color)


__all__ = ["COMMAND_ID", "render_version", "version_command"]
