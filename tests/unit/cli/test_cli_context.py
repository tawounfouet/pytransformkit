from __future__ import annotations

import pytest

from pytransformkit.cli.context import CLIContext, OutputMode
from pytransformkit.cli.exceptions import CLIUsageError


def test_default_cli_context_is_human_and_non_verbose() -> None:
    context = CLIContext()

    assert context.output_mode is OutputMode.HUMAN
    assert context.quiet is False
    assert context.verbose is False
    assert context.debug is False
    assert context.color is True
    assert not hasattr(context, "project")
    assert not hasattr(context, "profile")
    assert not hasattr(context, "target")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"quiet": True, "verbose": True},
        {"quiet": True, "debug": True},
        {"output_mode": OutputMode.JSON, "verbose": True},
    ],
)
def test_cli_context_rejects_contradictory_modes(
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(CLIUsageError):
        CLIContext(**kwargs)  # type: ignore[arg-type]
