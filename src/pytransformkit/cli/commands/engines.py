"""Engine inspection command group wiring."""

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
from pytransformkit.cli.services.engines import EngineService

LIST_COMMAND_ID = "engines.list"
INSPECT_COMMAND_ID = "engines.inspect"

engines_app = typer.Typer(
    name="engines",
    help="Inspect official PyTransformKit execution engines.",
    invoke_without_command=True,
    no_args_is_help=False,
)


@engines_app.callback(invoke_without_command=True)
def engines_root(ctx: typer.Context) -> None:
    """Inspect official PyTransformKit engines without activating them."""
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


def _render_error(
    exc: BaseException,
    *,
    engine_id: str | None,
    command: str,
    context: CLIContext,
) -> ExitCode:
    report = error_report_from_exception(exc)

    if context.output_mode is OutputMode.JSON:
        typer.echo(
            JSONRenderer().render_error(
                command=command,
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


def render_engines_list(
    *,
    json_output: bool = False,
    quiet: bool = False,
    verbose: bool = False,
    debug: bool = False,
    no_color: bool = False,
) -> ExitCode:
    """Render deterministic official-engine availability metadata."""
    context = _context(
        json_output=json_output,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        no_color=no_color,
    )

    try:
        report = EngineService().list()
    except (Exception, KeyboardInterrupt) as exc:
        return _render_error(
            exc,
            engine_id=None,
            command=LIST_COMMAND_ID,
            context=context,
        )

    if context.output_mode is OutputMode.JSON:
        typer.echo(
            JSONRenderer().render_success(
                command=LIST_COMMAND_ID,
                data=report.to_data(),
            ),
            nl=False,
        )
    else:
        consoles = create_console_pair(color=context.color)
        HumanRenderer(
            stdout=consoles.stdout,
            stderr=consoles.stderr,
        ).render_engine_list(
            report,
            quiet=context.quiet,
            include_detail=context.verbose or context.debug,
        )

    return ExitCode.SUCCESS


def render_engines_inspect(
    engine_id: str,
    *,
    json_output: bool = False,
    quiet: bool = False,
    verbose: bool = False,
    debug: bool = False,
    no_color: bool = False,
) -> ExitCode:
    """Render static qualification and capability metadata for one engine."""
    context = _context(
        json_output=json_output,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        no_color=no_color,
    )

    try:
        report = EngineService().inspect(engine_id)
    except (Exception, KeyboardInterrupt) as exc:
        return _render_error(
            exc,
            engine_id=engine_id,
            command=INSPECT_COMMAND_ID,
            context=context,
        )

    if context.output_mode is OutputMode.JSON:
        typer.echo(
            JSONRenderer().render_success(
                command=INSPECT_COMMAND_ID,
                data=report.to_data(),
            ),
            nl=False,
        )
    elif context.quiet:
        typer.echo(report.engine.id)
    else:
        consoles = create_console_pair(color=context.color)
        HumanRenderer(
            stdout=consoles.stdout,
            stderr=consoles.stderr,
        ).render_engine_inspection(
            report,
            include_detail=context.verbose or context.debug,
        )

    return ExitCode.SUCCESS


@engines_app.command("list")
def list_command(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit the CLI v1 machine-readable report.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        help="Emit only official engine IDs.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Include local dependency details.",
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
    """List official engines and local availability."""
    exit_code = render_engines_list(
        json_output=json_output,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        no_color=no_color,
    )
    if exit_code is not ExitCode.SUCCESS:
        raise typer.Exit(code=int(exit_code))


@engines_app.command("inspect")
def inspect_command(
    engine_id: str = typer.Argument(
        ...,
        help="Official engine ID.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit the CLI v1 machine-readable report.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        help="Emit only the normalized engine ID.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Include the conformance dimension matrix.",
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
    """Inspect one official engine without activating its adapter."""
    exit_code = render_engines_inspect(
        engine_id,
        json_output=json_output,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        no_color=no_color,
    )
    if exit_code is not ExitCode.SUCCESS:
        raise typer.Exit(code=int(exit_code))


__all__ = [
    "INSPECT_COMMAND_ID",
    "LIST_COMMAND_ID",
    "engines_app",
    "engines_root",
    "inspect_command",
    "list_command",
    "render_engines_inspect",
    "render_engines_list",
]
