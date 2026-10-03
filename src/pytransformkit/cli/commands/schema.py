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
from pytransformkit.cli.rendering.errors import render_cli_error
from pytransformkit.cli.rendering.human import HumanRenderer
from pytransformkit.cli.rendering.json import JSONRenderer
from pytransformkit.cli.rendering.output import emit_stdout
from pytransformkit.cli.services.schema import SchemaCLIService

VALIDATE_COMMAND_ID = "schema.validate"
INSPECT_COMMAND_ID = "schema.inspect"
FORMAT_COMMAND_ID = "schema.format"
CONVERT_COMMAND_ID = "schema.convert"

schema_app = typer.Typer(
    name="schema",
    help="Validate, inspect, format, and convert declarative schemas.",
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
    return CLIContext.from_options(
        json_output=json_output,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        no_color=no_color,
    )


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
            command=VALIDATE_COMMAND_ID,
            json_output=json_output,
            debug=debug,
            no_color=no_color,
            path=path,
        )
    path_text = str(path)

    try:
        report = SchemaCLIService().validate(path_text)
    except (Exception, KeyboardInterrupt) as exc:
        return render_cli_error(
            exc,
            command=VALIDATE_COMMAND_ID,
            json_output=json_output,
            debug=debug,
            no_color=no_color,
            path=path_text,
        )

    if context.output_mode is OutputMode.JSON:
        output_code = emit_stdout(
            lambda: typer.echo(
                JSONRenderer().render_success(
                    command=VALIDATE_COMMAND_ID,
                    data=report.to_data(),
                ),
                nl=False,
            )
        )
        if output_code is not ExitCode.SUCCESS:
            return output_code
    elif not context.quiet:
        consoles = create_console_pair(color=context.color)
        output_code = emit_stdout(
            lambda: HumanRenderer(
                stdout=consoles.stdout,
                stderr=consoles.stderr,
            ).render_schema_validation(report)
        )
        if output_code is not ExitCode.SUCCESS:
            return output_code

    return ExitCode.SUCCESS


def render_schema_inspect(
    path: str,
    *,
    json_output: bool = False,
    quiet: bool = False,
    verbose: bool = False,
    debug: bool = False,
    no_color: bool = False,
) -> ExitCode:
    """Inspect one explicit local schema and render the result."""
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
            command=INSPECT_COMMAND_ID,
            json_output=json_output,
            debug=debug,
            no_color=no_color,
            path=path,
        )
    path_text = str(path)

    try:
        report = SchemaCLIService().inspect(path_text)
    except (Exception, KeyboardInterrupt) as exc:
        return render_cli_error(
            exc,
            command=INSPECT_COMMAND_ID,
            json_output=json_output,
            debug=debug,
            no_color=no_color,
            path=path_text,
        )

    if context.output_mode is OutputMode.JSON:
        output_code = emit_stdout(
            lambda: typer.echo(
                JSONRenderer().render_success(
                    command=INSPECT_COMMAND_ID,
                    data=report.to_data(),
                ),
                nl=False,
            )
        )
        if output_code is not ExitCode.SUCCESS:
            return output_code
    elif not context.quiet:
        consoles = create_console_pair(color=context.color)
        output_code = emit_stdout(
            lambda: HumanRenderer(
                stdout=consoles.stdout,
                stderr=consoles.stderr,
            ).render_schema_inspection(
                report,
                include_details=context.verbose,
            )
        )
        if output_code is not ExitCode.SUCCESS:
            return output_code

    return ExitCode.SUCCESS


def render_schema_format(
    path: str,
    *,
    write: bool = False,
    debug: bool = False,
    no_color: bool = False,
) -> ExitCode:
    """Emit canonical declarative YAML or atomically replace the source."""
    context = _context(
        json_output=False,
        quiet=False,
        verbose=False,
        debug=debug,
        no_color=no_color,
    )
    path_text = str(path)

    try:
        payload = SchemaCLIService().format(path_text, write=write)
    except (Exception, KeyboardInterrupt) as exc:
        return render_cli_error(
            exc,
            command=FORMAT_COMMAND_ID,
            json_output=False,
            debug=debug,
            no_color=no_color,
            path=path_text,
        )

    if not write:
        return emit_stdout(lambda: typer.echo(payload, nl=False))

    return ExitCode.SUCCESS


def render_schema_convert(
    input_path: str,
    *,
    to_format: str,
    from_format: str | None = None,
    name: str | None = None,
    output: str | None = None,
    force: bool = False,
    debug: bool = False,
    no_color: bool = False,
) -> ExitCode:
    """Convert one local Schema between declarative YAML and SchemaCodec JSON."""
    context = _context(
        json_output=False,
        quiet=False,
        verbose=False,
        debug=debug,
        no_color=no_color,
    )
    input_text = str(input_path)

    try:
        from pytransformkit.cli.services.schema_convert import SchemaConversionService

        payload = SchemaConversionService().convert(
            input_text,
            to_format=to_format,
            from_format=from_format,
            name=name,
            output=output,
            force=force,
        )
    except (Exception, KeyboardInterrupt) as exc:
        return render_cli_error(
            exc,
            command=CONVERT_COMMAND_ID,
            json_output=False,
            debug=debug,
            no_color=no_color,
            path=input_text,
        )

    if payload is not None:
        return emit_stdout(lambda: typer.echo(payload, nl=False))

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


@schema_app.command("inspect")
def inspect_command(
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
        help="Include structured type details in human output.",
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
    """Inspect one local declarative schema file."""
    exit_code = render_schema_inspect(
        path,
        json_output=json_output,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        no_color=no_color,
    )
    if exit_code is not ExitCode.SUCCESS:
        raise typer.Exit(code=int(exit_code))


@schema_app.command("format")
def format_command(
    path: str = typer.Argument(
        ...,
        help="Explicit local declarative schema file.",
    ),
    write: bool = typer.Option(
        False,
        "--write",
        help="Atomically replace PATH with canonical YAML.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Include technical diagnostics for internal errors.",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable ANSI color in error output.",
    ),
) -> None:
    """Format one local declarative schema file."""
    exit_code = render_schema_format(
        path,
        write=write,
        debug=debug,
        no_color=no_color,
    )
    if exit_code is not ExitCode.SUCCESS:
        raise typer.Exit(code=int(exit_code))


@schema_app.command("convert")
def convert_command(
    input_path: str = typer.Argument(
        ...,
        help="Explicit local schema input file.",
    ),
    to_format: str = typer.Option(
        ...,
        "--to",
        help="Target payload format: yaml or json.",
    ),
    from_format: str | None = typer.Option(
        None,
        "--from",
        help="Override inferred input format: yaml or json.",
    ),
    name: str | None = typer.Option(
        None,
        "--name",
        help="Declarative schema name when YAML output needs one.",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        help="Write the payload to an explicit local file.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Replace an existing --output file.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Include technical diagnostics for internal errors.",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable ANSI color in error output.",
    ),
) -> None:
    """Convert one local schema between YAML and SchemaCodec JSON."""
    exit_code = render_schema_convert(
        input_path,
        to_format=to_format,
        from_format=from_format,
        name=name,
        output=output,
        force=force,
        debug=debug,
        no_color=no_color,
    )
    if exit_code is not ExitCode.SUCCESS:
        raise typer.Exit(code=int(exit_code))


__all__ = [
    "CONVERT_COMMAND_ID",
    "FORMAT_COMMAND_ID",
    "INSPECT_COMMAND_ID",
    "VALIDATE_COMMAND_ID",
    "convert_command",
    "format_command",
    "inspect_command",
    "render_schema_convert",
    "render_schema_format",
    "render_schema_inspect",
    "render_schema_validate",
    "schema_app",
    "validate_command",
]
