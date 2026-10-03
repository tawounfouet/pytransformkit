"""Low-level output guards for stable CLI process semantics."""

from __future__ import annotations

import errno
from collections.abc import Callable

from pytransformkit.cli.exit_codes import ExitCode


def emit_stdout(action: Callable[[], None]) -> ExitCode:
    """Run one stdout write and normalize broken-pipe outcomes to exit 141."""
    try:
        action()
    except BrokenPipeError:
        return ExitCode.BROKEN_PIPE
    except OSError as exc:
        if exc.errno == errno.EPIPE:
            return ExitCode.BROKEN_PIPE
        raise
    return ExitCode.SUCCESS


__all__ = ["emit_stdout"]
