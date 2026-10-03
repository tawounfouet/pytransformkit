from __future__ import annotations

import errno

from pytransformkit.cli.exit_codes import ExitCode
from pytransformkit.cli.rendering.output import emit_stdout


def test_emit_stdout_returns_success_for_normal_writer() -> None:
    seen: list[str] = []

    result = emit_stdout(lambda: seen.append("ok"))

    assert result is ExitCode.SUCCESS
    assert seen == ["ok"]


def test_emit_stdout_maps_broken_pipe_to_exit_141() -> None:
    def fail() -> None:
        raise BrokenPipeError()

    assert emit_stdout(fail) is ExitCode.BROKEN_PIPE


def test_emit_stdout_maps_epipe_oserror_to_exit_141() -> None:
    def fail() -> None:
        raise OSError(errno.EPIPE, "broken pipe")

    assert emit_stdout(fail) is ExitCode.BROKEN_PIPE
