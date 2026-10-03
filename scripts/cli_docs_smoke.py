"""Execute the published PyTransformKit 1.2 CLI documentation examples."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    return parser.parse_args()


def _ptk() -> str:
    executable_name = "ptk.exe" if sys.platform == "win32" else "ptk"
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


def _assert_documentation_surface(root: Path) -> None:
    paths = {
        "getting_started": root / "docs" / "CLI_GETTING_STARTED.md",
        "reference": root / "docs" / "CLI_REFERENCE.md",
        "release_notes": root / "docs" / "RELEASE_NOTES_1_2_0.md",
        "readme": root / "README.md",
        "changelog": root / "CHANGELOG.md",
    }
    for name, path in paths.items():
        assert path.is_file(), f"Missing {name}: {path}"

    reference = paths["reference"].read_text(encoding="utf-8")
    getting_started = paths["getting_started"].read_text(encoding="utf-8")
    readme = paths["readme"].read_text(encoding="utf-8")

    commands = (
        "ptk version",
        "ptk doctor",
        "ptk schema validate",
        "ptk schema inspect",
        "ptk schema format",
        "ptk schema convert",
        "ptk engines list",
        "ptk engines inspect",
        "ptk contract inspect",
    )
    for command in commands:
        assert command in reference, command

    for command in (
        "ptk version",
        "ptk doctor --json",
        "ptk schema validate",
        "ptk schema inspect",
        "ptk schema format",
        "ptk schema convert",
        "ptk engines list",
        "ptk contract inspect cli --json",
    ):
        assert command in getting_started or command in readme, command

    for document in (reference, getting_started, readme):
        assert "--install-completion" not in document
        assert "--show-completion" not in document or "not" in document.lower()


def _assert_completion_contract() -> None:
    help_result = _run("--help")
    assert "--install-completion" not in help_result.stdout
    assert "--show-completion" not in help_result.stdout


def _assert_report_examples() -> None:
    version_result = _run("version", "--json")
    version_payload = json.loads(version_result.stdout)
    assert version_payload["contract_version"] == 1
    assert version_payload["ok"] is True
    assert version_payload["command"] == "version"

    doctor_result = _run("doctor", "--json")
    doctor_payload = json.loads(doctor_result.stdout)
    assert doctor_payload["command"] == "doctor"

    engines_result = _run("engines", "list", "--json")
    engines_payload = json.loads(engines_result.stdout)
    assert engines_payload["command"] == "engines.list"

    contract_result = _run("contract", "inspect", "cli", "--json")
    contract_payload = json.loads(contract_result.stdout)
    assert contract_payload["data"]["status"] == "stable"
    assert contract_payload["data"]["document"]["contract"] == "pytransformkit.cli"


def _assert_schema_examples() -> None:
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
        validation = _run("schema", "validate", str(source), "--json")
        assert json.loads(validation.stdout)["data"]["valid"] is True

        inspection = _run("schema", "inspect", str(source), "--json")
        inspected = json.loads(inspection.stdout)
        assert inspected["data"]["schema"]["name"] == "customers"

        formatted = _run("schema", "format", str(source))
        assert "name: customers" in formatted.stdout

        writable = root / "customers-write.yml"
        writable.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        _run("schema", "format", str(writable), "--write")
        _run("schema", "validate", str(writable))

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
        assert wire.is_file()

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

        overwrite = _run(
            "schema",
            "convert",
            str(source),
            "--to",
            "json",
            "--output",
            str(wire),
            expected=12,
        )
        assert "already exists" in overwrite.stderr.lower()

        _run(
            "schema",
            "convert",
            str(source),
            "--to",
            "json",
            "--output",
            str(wire),
            "--force",
        )


def main() -> int:
    args = _args()
    root = args.root.resolve()

    _assert_documentation_surface(root)
    _assert_completion_contract()
    _assert_report_examples()
    _assert_schema_examples()

    print(
        json.dumps(
            {
                "cli_docs_smoke": "PASS",
                "platform": sys.platform,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
