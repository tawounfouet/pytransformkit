from __future__ import annotations

import pytest

pytest.importorskip("rich")

from pytransformkit.cli.rendering.console import create_console_pair


def test_no_color_console_is_explicitly_non_terminal() -> None:
    consoles = create_console_pair(color=False)

    assert consoles.stdout.is_terminal is False
    assert consoles.stderr.is_terminal is False
