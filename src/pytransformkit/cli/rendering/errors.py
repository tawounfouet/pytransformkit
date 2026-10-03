"""Helpers for routing CLI errors to the selected presentation mode."""

from __future__ import annotations

from pytransformkit.cli.models.errors import CLIErrorReport
from pytransformkit.cli.rendering.human import HumanRenderer
from pytransformkit.cli.rendering.json import JSONRenderer


def render_error_json(
    report: CLIErrorReport,
    *,
    command: str,
    renderer: JSONRenderer,
) -> str:
    """Render an error using the machine report contract."""
    return renderer.render_error(command=command, error=report)


def render_error_human(
    report: CLIErrorReport,
    *,
    renderer: HumanRenderer,
) -> None:
    """Render an error through the human stderr channel."""
    renderer.render_error(report)


__all__ = ["render_error_human", "render_error_json"]
