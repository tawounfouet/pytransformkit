from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("typer")
pytest.importorskip("rich")

from pytransformkit.cli.public_contract import (
    RESERVED_FUTURE_COMMANDS,
    build_cli_contract,
)

ROOT = Path(__file__).resolve().parents[3]
SNAPSHOT = ROOT / "contracts" / "cli_contract_v1.json"


def _snapshot() -> dict[str, object]:
    payload = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_runtime_cli_contract_matches_frozen_snapshot_exactly() -> None:
    assert build_cli_contract() == _snapshot()


def test_cli_contract_verifier_accepts_frozen_snapshot() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "cli_contract_snapshot.py"),
            "--check",
            str(SNAPSHOT),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "CLI v1 contract: PASS\n"
    assert result.stderr == ""


def test_frozen_contract_covers_complete_stable_command_surface() -> None:
    snapshot = _snapshot()

    assert snapshot["command_tree"] == {
        "version": None,
        "doctor": None,
        "schema": ["validate", "inspect", "format", "convert"],
        "engines": ["list", "inspect"],
        "contract": ["inspect"],
    }
    commands = snapshot["commands"]
    assert isinstance(commands, dict)
    assert list(commands) == [
        "version",
        "doctor",
        "schema.validate",
        "schema.inspect",
        "schema.format",
        "schema.convert",
        "engines.list",
        "engines.inspect",
        "contract.inspect",
    ]
    assert commands["schema.format"]["classification"] == "payload"
    assert commands["schema.convert"]["classification"] == "payload"
    assert commands["contract.inspect"]["classification"] == "report"


def test_schema_convert_public_options_are_frozen() -> None:
    snapshot = _snapshot()
    commands = snapshot["commands"]
    assert isinstance(commands, dict)

    convert = commands["schema.convert"]
    assert isinstance(convert, dict)
    options = convert["options"]
    assert isinstance(options, list)

    public_flags = [
        option["flags"][0] for option in options if isinstance(option, dict)
    ]
    assert public_flags == [
        "--to",
        "--from",
        "--name",
        "--output",
        "--force",
        "--debug",
        "--no-color",
    ]
    assert options[0]["required"] is True


def test_exit_codes_error_categories_and_json_envelope_are_frozen() -> None:
    snapshot = _snapshot()

    assert snapshot["exit_codes"] == {
        "success": 0,
        "general_error": 1,
        "invalid_usage": 2,
        "invalid_schema": 10,
        "missing_optional_dependency": 11,
        "filesystem_error": 12,
        "unsupported_operation": 13,
        "internal_error": 70,
        "interrupted": 130,
        "broken_pipe": 141,
    }
    assert snapshot["error_categories"] == [
        "general_error",
        "invalid_usage",
        "invalid_schema",
        "missing_optional_dependency",
        "filesystem_error",
        "unsupported_operation",
        "internal_error",
        "interrupted",
        "broken_pipe",
    ]
    assert snapshot["json_envelope"] == {
        "contract_version": 1,
        "common_required": ["contract_version", "ok", "command"],
        "success_member": "data",
        "error_member": "error",
        "error_required": ["category", "message"],
        "error_optional": ["code", "path", "hint", "details"],
    }


def test_reserved_future_commands_remain_outside_v1_surface() -> None:
    snapshot = _snapshot()
    command_tree = snapshot["command_tree"]
    assert isinstance(command_tree, dict)

    assert snapshot["reserved_future_commands"] == list(RESERVED_FUTURE_COMMANDS)
    assert not set(RESERVED_FUTURE_COMMANDS).intersection(command_tree)


def test_security_and_filesystem_guarantees_are_frozen_fail_closed() -> None:
    snapshot = _snapshot()

    assert snapshot["security_filesystem"] == {
        "remote_sources": False,
        "recursive_discovery": False,
        "implicit_overwrite": False,
        "format_write_requires_flag": True,
        "convert_output_requires_path": True,
        "convert_overwrite_requires_force": True,
        "mutable_symlinks": False,
        "implicit_include": False,
        "env_expansion": False,
        "plugin_command_injection": False,
        "project_discovery": False,
        "shell_execution": False,
    }
