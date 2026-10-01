from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[3]
SCRIPT = ROOT / "scripts" / "release_qualification.py"
MANIFEST = ROOT / "contracts" / "release_qualification_v1.json"


def test_release_qualification_manifest_matches_repository() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--check",
            str(MANIFEST),
            "--root",
            str(ROOT),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Release qualification manifest: PASS" in result.stdout


def test_release_qualification_manifest_detects_version_drift(
    tmp_path: Path,
) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["project_version"] = "9.9.9"
    mutated = tmp_path / "release_qualification_v1.json"
    mutated.write_text(json.dumps(manifest), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--check",
            str(mutated),
            "--root",
            str(ROOT),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "project version drift" in result.stderr
