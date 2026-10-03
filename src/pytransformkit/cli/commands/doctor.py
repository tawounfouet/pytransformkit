"""Doctor command wiring."""

from __future__ import annotations

import typer

from pytransformkit.cli.context import CLIContext, OutputMode
from pytransformkit.cli.exceptions import CLIUsageError
from pytransformkit.cli.exit_codes import ExitCode
from pytransformkit.cli.rendering.console import create_console_pair
from pytransformkit.cli.rendering.errors import render_cli_error
from pytransformkit.cli.rendering.human import HumanRenderer
from pytransformkit.cli.rendering.json import JSONRenderer
from pytransformkit.cli.rendering.output import emit_stdout
from pytransformkit.cli.services.doctor import DoctorService

COMMAND_ID = "doctor"


def _context(
    *,
    json_output: bool,
    quiet: bool,
    verbose: bool,
    debug: bool,
    no_color: bool,
) -> CLIContext:
    return CLIContext.from_options(
        json_output=json_output,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        no_color=no_color,
    )


def render_doctor(
    *,
    json_output: bool = False,
    quiet: bool = False,
    verbose: bool = False,
    debug: bool = False,
    no_color: bool = False,
) -> ExitCode:
    """Collect and render deterministic local environment diagnostics."""
    try:
        context = _context(
            json_output=json_output,
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            no_color=no_color,
        )
    except CLIUsageError as exc:
        return render_cli_error(
            exc,
            command=COMMAND_ID,
            json_output=json_output,
            debug=debug,
            no_color=no_color,
        )

    try:
        report = DoctorService().inspect()
    except (Exception, KeyboardInterrupt) as exc:
        return render_cli_error(
            exc,
            command=COMMAND_ID,
            json_output=json_output,
            debug=debug,
            no_color=no_color,
        )

    if context.output_mode is OutputMode.JSON:
        output_code = emit_stdout(
            lambda: typer.echo(
                JSONRenderer().render_success(
                    command=COMMAND_ID,
                    data=report.to_data(),
                ),
                nl=False,
            )
        )
    else:
        consoles = create_console_pair(color=context.color)
        output_code = emit_stdout(
            lambda: HumanRenderer(
                stdout=consoles.stdout,
                stderr=consoles.stderr,
            ).render_doctor(
                report,
                quiet=context.quiet,
                include_detail=context.verbose,
            )
        )

    if output_code is not ExitCode.SUCCESS:
        return output_code
    if report.is_fatal:
        return ExitCode.GENERAL_ERROR
    return ExitCode.SUCCESS


def doctor_command(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit the CLI v1 machine-readable report.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        help="Show only the overall diagnostic status.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Include additional diagnostic details.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Include technical diagnostic details.",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable ANSI color in human output.",
    ),
) -> None:
    """Check the local PyTransformKit environment without network access."""
    exit_code = render_doctor(
        json_output=json_output,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        no_color=no_color,
    )
    if exit_code is not ExitCode.SUCCESS:
        raise typer.Exit(code=int(exit_code))


__all__ = ["COMMAND_ID", "doctor_command", "render_doctor"]
