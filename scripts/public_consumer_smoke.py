"""Public-consumer smoke for the published PyTransformKit 1.2 CLI."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

import pytransformkit


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-version", default="1.2.0")
    return parser.parse_args()


def _ptk() -> str:
    executable_name = "ptk.exe" if os.name == "nt" else "ptk"
    sibling = Path(sys.executable).with_name(executable_name)
    if sibling.is_file():
        return str(sibling)

    executable = shutil.which("ptk")
    if executable is None:
        raise AssertionError("Installed console script 'ptk' is not available.")
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


def _assert_identity(expected_version: str) -> None:
    assert version("pytransformkit") == expected_version
    assert pytransformkit.__version__ == expected_version

    payload = json.loads(_run("version", "--json").stdout)
    assert payload["ok"] is True
    assert payload["data"]["pytransformkit"] == expected_version


def _assert_contract() -> None:
    result = _run("contract", "inspect", "cli", "--json")
    payload = json.loads(result.stdout)
    document = payload["data"]["document"]

    assert payload["data"]["status"] == "stable"
    assert document["contract"] == "pytransformkit.cli"
    assert document["contract_version"] == 1
    assert document["status"] == "stable"

    help_text = _run("--help").stdout
    assert "--install-completion" not in help_text
    assert "--show-completion" not in help_text


def _assert_schema_round_trip() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        source = root / "customers.yml"
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
        inspected = json.loads(
            _run("schema", "inspect", str(source), "--json").stdout
        )
        assert inspected["data"]["schema"]["name"] == "customers"

        wire = root / "customers.json"
        _run(
            "schema",
            "convert",
            str(source),
            "--to",
            "json",
            "--output",
            str(wire),
        )

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
    expected_version = _args().expected_version

    _assert_identity(expected_version)
    _run("doctor", "--json")
    _run("engines", "list", "--json")
    _assert_contract()
    _assert_schema_round_trip()

    print(
        json.dumps(
            {
                "public_consumer_smoke": "PASS",
                "version": expected_version,
                "python": sys.version.split()[0],
                "platform": sys.platform,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
