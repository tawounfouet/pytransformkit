"""Typer application for the optional PyTransformKit developer CLI."""

from __future__ import annotations

import typer

from pytransformkit.cli.commands.contract import contract_app
from pytransformkit.cli.commands.doctor import doctor_command
from pytransformkit.cli.commands.engines import engines_app
from pytransformkit.cli.commands.schema import schema_app
from pytransformkit.cli.commands.version import render_version, version_command
from pytransformkit.cli.exit_codes import ExitCode

app = typer.Typer(
    name="ptk",
    help="PyTransformKit developer CLI.",
    add_completion=False,
    invoke_without_command=True,
    no_args_is_help=False,
    pretty_exceptions_enable=False,
)


@app.callback(invoke_without_command=True)
def root(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        is_eager=True,
        help="Show the installed PyTransformKit and Python versions.",
    ),
) -> None:
    """PyTransformKit developer CLI."""
    if version:
        exit_code = render_version()
        raise typer.Exit(code=0 if exit_code is ExitCode.SUCCESS else int(exit_code))

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


app.command("version")(version_command)
app.command("doctor")(doctor_command)
app.add_typer(schema_app, name="schema")
app.add_typer(engines_app, name="engines")
app.add_typer(contract_app, name="contract")
