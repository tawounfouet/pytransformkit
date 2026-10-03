"""Portable smoke tests for installed PyTransformKit CLI artifacts."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

import pytransformkit


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        required=True,
        choices=("core", "cli", "cli-yaml", "cli-no-yaml"),
    )
    return parser.parse_args()


def _installed(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def _ptk() -> str:
    executable = shutil.which("ptk")
    if executable is None:
        raise AssertionError("Installed console script 'ptk' is not available on PATH.")
    return executable


def _run(*args: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [_ptk(), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != expected:
        raise AssertionError(
            f"ptk {' '.join(args)} returned {result.returncode}, expected {expected}.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result


def _assert_version_identity() -> None:
    installed = version("pytransformkit")
    assert pytransformkit.__version__ == installed

    result = _run("version", "--json")
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["command"] == "version"
    assert payload["data"]["pytransformkit_version"] == installed


def _assert_common_cli() -> None:
    assert _installed("typer")
    assert _installed("rich")

    _run("--help")
    _run("--version")
    _assert_version_identity()

    doctor = _run("doctor", "--json")
    doctor_payload = json.loads(doctor.stdout)
    assert doctor_payload["command"] == "doctor"

    engines = _run("engines", "list", "--json")
    engines_payload = json.loads(engines.stdout)
    assert engines_payload["command"] == "engines.list"

    contract = _run("contract", "inspect", "cli", "--json")
    contract_payload = json.loads(contract.stdout)
    assert contract_payload["command"] == "contract.inspect"
    assert contract_payload["data"]["status"] == "stable"
    assert contract_payload["data"]["document"]["contract"] == "pytransformkit.cli"


def _assert_core_only() -> None:
    assert not _installed("typer")
    assert not _installed("rich")
    assert not _installed("yaml")
    assert version("pytransformkit") == pytransformkit.__version__

    result = _run("--help", expected=11)
    combined = result.stdout + result.stderr
    assert 'pip install "pytransformkit[cli]"' in combined


def _assert_cli_without_yaml() -> None:
    _assert_common_cli()
    assert not _installed("yaml")

    with tempfile.TemporaryDirectory() as temp:
        source = Path(temp) / "schema.yml"
        source.write_text(
            """version: 1
schema:
  name: customers
  fields:
    - name: customer_id
      type: int64
      nullable: false
""",
            encoding="utf-8",
        )

        result = _run("schema", "validate", str(source), expected=11)
        assert "PTK-DECL-010" in result.stderr


def _assert_cli_with_yaml() -> None:
    _assert_common_cli()
    assert _installed("yaml")

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        source = root / "schema.yml"
        source.write_text(
            """version: 1
schema:
  name: customers
  fields:
    - name: customer_id
      type: int64
      nullable: false
    - name: email
      type: string
      nullable: true
""",
            encoding="utf-8",
        )

        _run("schema", "validate", str(source))

        inspected = _run("schema", "inspect", str(source), "--json")
        inspected_payload = json.loads(inspected.stdout)
        assert inspected_payload["data"]["schema"]["name"] == "customers"

        formatted = _run("schema", "format", str(source))
        assert "version: 1" in formatted.stdout
        assert "name: customers" in formatted.stdout

        wire = root / "schema.json"
        _run(
            "schema",
            "convert",
            str(source),
            "--to",
            "json",
            "--output",
            str(wire),
        )
        assert wire.exists()
        assert '"contract":"pytransformkit.schema"' in wire.read_text(encoding="utf-8")

        restored = root / "restored.yml"
        _run(
            "schema",
            "convert",
            str(wire),
            "--to",
            "yaml",
            "--name",
            "customers",
            "--output",
            str(restored),
        )
        _run("schema", "validate", str(restored))


def main() -> int:
    mode = _args().mode

    if mode == "core":
        _assert_core_only()
    elif mode in {"cli", "cli-no-yaml"}:
        _assert_cli_without_yaml()
    else:
        _assert_cli_with_yaml()

    print(
        json.dumps(
            {
                "artifact_smoke": "PASS",
                "mode": mode,
                "python": sys.version.split()[0],
                "platform": sys.platform,
                "version": pytransformkit.__version__,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
