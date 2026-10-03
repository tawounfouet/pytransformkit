"""Contract inspection command group wiring."""

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
from pytransformkit.cli.services.contracts import ContractInspectionService

COMMAND_ID = "contract.inspect"

contract_app = typer.Typer(
    name="contract",
    help="Inspect packaged PyTransformKit compatibility contracts.",
    invoke_without_command=True,
    no_args_is_help=False,
)


@contract_app.callback(invoke_without_command=True)
def contract_root(ctx: typer.Context) -> None:
    """Inspect compatibility contracts shipped with PyTransformKit."""
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
    context: CLIContext,
) -> ExitCode:
    report = error_report_from_exception(exc)

    if context.output_mode is OutputMode.JSON:
        typer.echo(
            JSONRenderer().render_error(
                command=COMMAND_ID,
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


def render_contract_inspect(
    contract_id: str | None = None,
    *,
    json_output: bool = False,
    quiet: bool = False,
    verbose: bool = False,
    debug: bool = False,
    no_color: bool = False,
) -> ExitCode:
    """Render the contract catalogue or inspect one named contract."""
    context = _context(
        json_output=json_output,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        no_color=no_color,
    )
    service = ContractInspectionService()

    try:
        report = (
            service.list()
            if contract_id is None
            else service.inspect(contract_id)
        )
    except (Exception, KeyboardInterrupt) as exc:
        return _render_error(exc, context=context)

    if context.output_mode is OutputMode.JSON:
        typer.echo(
            JSONRenderer().render_success(
                command=COMMAND_ID,
                data=report.to_data(),
            ),
            nl=False,
        )
        return ExitCode.SUCCESS

    consoles = create_console_pair(color=context.color)
    renderer = HumanRenderer(
        stdout=consoles.stdout,
        stderr=consoles.stderr,
    )

    if contract_id is None:
        renderer.render_contract_list(
            report,
            quiet=context.quiet,
        )
    elif context.quiet:
        typer.echo(report.contract.id)
    else:
        renderer.render_contract_inspection(
            report,
            include_document=context.verbose or context.debug,
        )

    return ExitCode.SUCCESS


@contract_app.command("inspect")
def inspect_command(
    contract_id: str | None = typer.Argument(
        None,
        help="Optional contract ID: public-api, errors, schema-wire, or cli.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit the CLI v1 machine-readable report.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        help="Emit only contract IDs.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Include the full contract document in human output.",
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
    """List inspectable contracts or inspect one packaged contract."""
    exit_code = render_contract_inspect(
        contract_id,
        json_output=json_output,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        no_color=no_color,
    )
    if exit_code is not ExitCode.SUCCESS:
        raise typer.Exit(code=int(exit_code))


__all__ = [
    "COMMAND_ID",
    "contract_app",
    "contract_root",
    "inspect_command",
    "render_contract_inspect",
]
