from __future__ import annotations

import pytest

from pytransformkit.application.extensions import (
    PLUGIN_API_VERSION,
    PluginCompatibility,
)
from pytransformkit.domain.shared.version import Version


def test_plugin_compatibility_checks_package_and_protocol_ranges() -> None:
    compatibility = PluginCompatibility(
        framework_min=Version(0, 5, 0),
        framework_max_exclusive=Version(1, 0, 0),
        protocol_min=1,
        protocol_max=2,
    )

    assert compatibility.supports(Version(0, 5, 0), 1)
    assert compatibility.supports(Version(0, 9, 9), 2)
    assert not compatibility.supports(Version(1, 0, 0), 1)
    assert not compatibility.supports(Version(0, 4, 9), 1)
    assert not compatibility.supports(Version(0, 5, 0), 3)
    assert PLUGIN_API_VERSION == 1


def test_default_plugin_compatibility_covers_framework_v1_line() -> None:
    compatibility = PluginCompatibility()

    assert compatibility.supports(Version(1, 0, 0), PLUGIN_API_VERSION)
    assert compatibility.supports(Version(1, 9, 9), PLUGIN_API_VERSION)
    assert not compatibility.supports(Version(2, 0, 0), PLUGIN_API_VERSION)


def test_invalid_compatibility_range_fails_fast() -> None:
    with pytest.raises(ValueError):
        PluginCompatibility(
            framework_min=Version(1, 0, 0),
            framework_max_exclusive=Version(1, 0, 0),
        )
