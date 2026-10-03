from __future__ import annotations

from io import StringIO

import pytest

pytest.importorskip("rich")
from rich.console import Console

from pytransformkit.cli.exit_codes import ExitCode
from pytransformkit.cli.models.errors import CLIErrorReport, ErrorCategory
from pytransformkit.cli.rendering.human import HumanRenderer


def _renderer() -> tuple[HumanRenderer, StringIO, StringIO]:
    stdout = StringIO()
    stderr = StringIO()
    renderer = HumanRenderer(
        stdout=Console(
            file=stdout,
            force_terminal=False,
            no_color=True,
            width=120,
        ),
        stderr=Console(
            file=stderr,
            force_terminal=False,
            no_color=True,
            width=120,
        ),
    )
    return renderer, stdout, stderr


def test_human_renderer_writes_success_to_stdout() -> None:
    renderer, stdout, stderr = _renderer()

    renderer.write("PyTransformKit [bold]literal[/bold]")

    assert "PyTransformKit [bold]literal[/bold]" in stdout.getvalue()
    assert stderr.getvalue() == ""


def test_human_renderer_routes_errors_to_stderr_without_markup_injection() -> None:
    renderer, stdout, stderr = _renderer()
    report = CLIErrorReport(
        category=ErrorCategory.INVALID_SCHEMA,
        message="[bold red]user supplied text[/bold red]",
        exit_code=ExitCode.INVALID_SCHEMA,
        code="PTK-DECL-005",
        path="[link]schema.yml[/link]",
        hint="Use [yaml] syntax literally.",
    )

    renderer.render_error(report)

    rendered = stderr.getvalue()
    assert stdout.getvalue() == ""
    assert "[bold red]user supplied text[/bold red]" in rendered
    assert "[link]schema.yml[/link]" in rendered
    assert "PTK-DECL-005" in rendered
    assert "\x1b[" not in rendered
