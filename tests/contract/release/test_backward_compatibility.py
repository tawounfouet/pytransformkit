from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from pytransformkit.domain.shared.version import Version
from pytransformkit.plugins import PLUGIN_API_VERSION, PluginCompatibility

ROOT = Path(__file__).parents[3]


def _run(script: str, contract: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / script),
            "--check",
            str(ROOT / "contracts" / contract),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def test_v1_error_code_catalogue_is_frozen() -> None:
    result = _run("error_code_catalog.py", "error_codes_v1.json")

    assert result.returncode == 0, result.stderr
    assert "V1 error catalogue: PASS" in result.stdout


def test_v1_consumer_compatibility_snapshot_is_frozen() -> None:
    result = _run(
        "consumer_compatibility.py",
        "consumer_compatibility_v1.json",
    )

    assert result.returncode == 0, result.stderr
    assert "V1 consumer compatibility: PASS" in result.stdout


def test_default_plugin_protocol_covers_stable_v1_line() -> None:
    compatibility = PluginCompatibility()

    assert compatibility.supports(Version(1, 0, 0), PLUGIN_API_VERSION)
    assert compatibility.supports(Version(1, 9, 9), PLUGIN_API_VERSION)
    assert not compatibility.supports(Version(2, 0, 0), PLUGIN_API_VERSION)
