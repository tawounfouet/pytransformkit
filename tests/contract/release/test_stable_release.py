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
