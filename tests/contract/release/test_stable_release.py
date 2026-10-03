from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[3]


def test_stable_release_manifest_is_frozen() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "stable_release.py"),
            "--check",
            str(ROOT / "contracts" / "stable_release_v1.json"),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    assert "Stable release freeze: PASS" in result.stdout


def test_declarative_schema_v1_1_stable_release_manifest_is_frozen() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "stable_release.py"),
            "--check",
            str(ROOT / "contracts" / "stable_release_v1_1.json"),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    assert "Stable release freeze: PASS" in result.stdout



def test_developer_cli_v1_2_stable_release_manifest_is_frozen() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "stable_release.py"),
            "--check",
            str(ROOT / "contracts" / "stable_release_v1_2.json"),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    assert "Stable release freeze: PASS" in result.stdout
