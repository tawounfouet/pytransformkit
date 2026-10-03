"""Dependency-light bootstrap for the optional PyTransformKit CLI."""

from __future__ import annotations

import errno
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

    from click import Abort, ClickException

    from pytransformkit.cli.app import app

    args = list(argv) if argv is not None else None
    try:
        result = app(args=args, prog_name="ptk", standalone_mode=False)
    except BrokenPipeError:
        return int(ExitCode.BROKEN_PIPE)
    except OSError as exc:
        if exc.errno == errno.EPIPE:
            return int(ExitCode.BROKEN_PIPE)
        raise
    except ClickException as exc:
        exc.show()
        return int(exc.exit_code)
    except Abort:
        print("Aborted!", file=sys.stderr)
        return 1

    return result if isinstance(result, int) else 0


__all__ = ["main"]
