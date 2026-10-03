"""Dependency-light bootstrap for the optional PyTransformKit CLI."""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Sequence

from pytransformkit.cli.exit_codes import ExitCode

CLI_DEPENDENCIES = ("typer", "rich")
MISSING_OPTIONAL_DEPENDENCY_EXIT_CODE = int(ExitCode.MISSING_OPTIONAL_DEPENDENCY)


def _missing_cli_dependencies() -> tuple[str, ...]:
    """Return CLI dependencies that are not importable."""
    return tuple(
        dependency
        for dependency in CLI_DEPENDENCIES
        if importlib.util.find_spec(dependency) is None
    )


def _render_missing_dependency_message(missing: Sequence[str]) -> str:
    """Build a stdlib-only installation hint for an incomplete CLI install."""
    missing_list = ", ".join(missing)
    return (
        "PyTransformKit CLI dependencies are not installed.\n"
        f"Missing: {missing_list}\n\n"
        "Install the CLI extra with:\n"
        '  pip install "pytransformkit[cli]"'
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run ptk while keeping optional CLI imports behind the bootstrap."""
    missing = _missing_cli_dependencies()
    if missing:
        print(_render_missing_dependency_message(missing), file=sys.stderr)
        return MISSING_OPTIONAL_DEPENDENCY_EXIT_CODE

    from pytransformkit.cli.app import app

    args = list(argv) if argv is not None else None
    try:
        app(args=args, prog_name="ptk", standalone_mode=True)
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else 1
    return 0


__all__ = ["main"]
