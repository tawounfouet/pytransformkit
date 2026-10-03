"""Schema command group wiring."""

from __future__ import annotations

import sys
import traceback
import typer

from pytransformkit.cli.context import CLIContext, OutputMode
from pytransformkit.cli.exceptions import (
    CLIUsageError,
    error_report_from_exception,
)
from pytransformkit.cli.exit_codes import ExitCode
from pytransformkit.cli.rendering.console import create_console_pair
from pytransformkit.cli.rendering.human import HumanRenderer
from pytransformkit.cli.rendering.json import JSONRenderer
from pytransformkit.cli.services.schema import SchemaCLIService

VALIDATE_COMMAND_ID = "schema.validate"

schema_app = typer.Typer(
    name="schema",
    help="Validate and inspect declarative schemas.",
    invoke_without_command=True,
    no_args_is_help=False,
)


@schema_app.callback(invoke_without_command=True)
def schema_root(ctx: typer.Context) -> None:
    """Work with declarative schemas."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


def _context(
    *,
    json_output: bool,
    quiet: bool,
    verbose: bool,
    debug: bool,
    no_color: bool,
) -> CLIContext:
    try:
        return CLIContext(
            output_mode=OutputMode.JSON if json_output else OutputMode.HUMAN,
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            color=not no_color,
        )
    except CLIUsageError as exc:
        raise typer.BadParameter(str(exc)) from exc


def _render_validate_error(
    exc: BaseException,
    *,
    path: str,
    context: CLIContext,
) -> ExitCode:
    report = error_report_from_exception(exc, path=path)

    if context.output_mode is OutputMode.JSON:
        typer.echo(
            JSONRenderer().render_error(
                command=VALIDATE_COMMAND_ID,
                error=report,
            ),
            nl=False,
        )
    else:
        consoles = create_console_pair(color=context.color)
        HumanRenderer(
            stdout=consoles.stdout,
            stderr=consoles.stderr,
        ).render_error(report)

    if context.debug and report.exit_code is ExitCode.INTERNAL_ERROR:
        traceback.print_exception(exc, file=sys.stderr)

    return report.exit_code


def render_schema_validate(
    path: str,
    *,
    json_output: bool = False,
    quiet: bool = False,
    verbose: bool = False,
    debug: bool = False,
    no_color: bool = False,
) -> ExitCode:
    """Validate one explicit local schema and render the result."""
    context = _context(
        json_output=json_output,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        no_color=no_color,
    )
    path_text = str(path)

    try:
        report = SchemaCLIService().validate(path_text)
    except (Exception, KeyboardInterrupt) as exc:
        return _render_validate_error(
            exc,
            path=path_text,
            context=context,
        )

    if context.output_mode is OutputMode.JSON:
        typer.echo(
            JSONRenderer().render_success(
                command=VALIDATE_COMMAND_ID,
                data=report.to_data(),
            ),
            nl=False,
        )
    elif not context.quiet:
        consoles = create_console_pair(color=context.color)
        HumanRenderer(
            stdout=consoles.stdout,
            stderr=consoles.stderr,
        ).render_schema_validation(report)

    return ExitCode.SUCCESS


@schema_app.command("validate")
def validate_command(
    path: str = typer.Argument(
        ...,
        help="Explicit local declarative schema file.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit the CLI v1 machine-readable report.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        help="Suppress successful human output.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Include additional human diagnostics.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Include technical diagnostics for internal errors.",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable ANSI color in human output.",
    ),
) -> None:
    """Validate one local declarative schema file."""
    exit_code = render_schema_validate(
        path,
        json_output=json_output,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        no_color=no_color,
    )
    if exit_code is not ExitCode.SUCCESS:
        raise typer.Exit(code=int(exit_code))


__all__ = [
    "VALIDATE_COMMAND_ID",
    "render_schema_validate",
    "schema_app",
    "validate_command",
]
