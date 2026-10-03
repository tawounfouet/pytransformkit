"""Typer application for the optional PyTransformKit developer CLI."""

from __future__ import annotations

import typer

from pytransformkit import __version__

app = typer.Typer(
    name="ptk",
    help="PyTransformKit developer CLI.",
    add_completion=False,
    invoke_without_command=True,
    no_args_is_help=False,
    pretty_exceptions_enable=False,
)


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context) -> None:
    """PyTransformKit developer CLI."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command("version")
def version_command() -> None:
    """Show the installed PyTransformKit version."""
    typer.echo(f"PyTransformKit {__version__}")
