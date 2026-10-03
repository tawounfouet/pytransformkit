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
from pytransformkit.cli.rendering.errors import render_cli_error
from pytransformkit.cli.rendering.human import HumanRenderer
from pytransformkit.cli.rendering.json import JSONRenderer
from pytransformkit.cli.rendering.output import emit_stdout
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
    return CLIContext.from_options(
        json_output=json_output,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        no_color=no_color,
    )


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
    service = ContractInspectionService()

    if contract_id is None:
        try:
            report = service.list()
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
            if output_code is not ExitCode.SUCCESS:
                return output_code
        else:
            consoles = create_console_pair(color=context.color)
            output_code = emit_stdout(
                lambda: HumanRenderer(
                    stdout=consoles.stdout,
                    stderr=consoles.stderr,
                ).render_contract_list(
                    report,
                    quiet=context.quiet,
                )
            )
            if output_code is not ExitCode.SUCCESS:
                return output_code
        return ExitCode.SUCCESS

    try:
        inspection = service.inspect(contract_id)
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
                    data=inspection.to_data(),
                ),
                nl=False,
            )
        )
        if output_code is not ExitCode.SUCCESS:
            return output_code
    elif context.quiet:
        output_code = emit_stdout(lambda: typer.echo(inspection.contract.id))
        if output_code is not ExitCode.SUCCESS:
            return output_code
    else:
        consoles = create_console_pair(color=context.color)
        output_code = emit_stdout(
            lambda: HumanRenderer(
                stdout=consoles.stdout,
                stderr=consoles.stderr,
            ).render_contract_inspection(
                inspection,
                include_document=context.verbose,
            )
        )
        if output_code is not ExitCode.SUCCESS:
            return output_code

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
