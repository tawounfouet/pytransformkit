from __future__ import annotations

import json

import pytest

pytest.importorskip("typer")
pytest.importorskip("rich")

from pytransformkit.cli.commands import schema as schema_command
from pytransformkit.cli.exit_codes import ExitCode
from pytransformkit.errors import (
    DeclarativeSchemaDependencyError,
    DeclarativeSchemaIOError,
    DeclarativeSchemaTypeError,
)


@pytest.mark.parametrize(
    ("error", "expected_exit", "expected_category", "expected_code"),
    [
        (
            DeclarativeSchemaTypeError("money128"),
            ExitCode.INVALID_SCHEMA,
            "invalid_schema",
            "PTK-DECL-005",
        ),
        (
            DeclarativeSchemaDependencyError("PyYAML"),
            ExitCode.MISSING_OPTIONAL_DEPENDENCY,
            "missing_optional_dependency",
            "PTK-DECL-010",
        ),
        (
            DeclarativeSchemaIOError("missing.yml", "read"),
            ExitCode.FILESYSTEM_ERROR,
            "filesystem_error",
            "PTK-DECL-011",
        ),
    ],
)
def test_schema_validate_json_preserves_error_identity(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    error: Exception,
    expected_exit: ExitCode,
    expected_category: str,
    expected_code: str,
) -> None:
    def fail(self, path: str):
        raise error

    monkeypatch.setattr(schema_command.SchemaCLIService, "validate", fail)

    exit_code = schema_command.render_schema_validate(
        "schema.yml",
        json_output=True,
    )

    assert exit_code is expected_exit
    captured = capsys.readouterr()
    assert captured.err == ""

    payload = json.loads(captured.out)
    assert payload["contract_version"] == 1
    assert payload["ok"] is False
    assert payload["command"] == "schema.validate"
    assert payload["error"]["category"] == expected_category
    assert payload["error"]["code"] == expected_code
    assert payload["error"]["path"] == "schema.yml"


def test_schema_validate_human_error_uses_stderr(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail(self, path: str):
        raise DeclarativeSchemaTypeError("money128")

    monkeypatch.setattr(schema_command.SchemaCLIService, "validate", fail)

    exit_code = schema_command.render_schema_validate(
        "schema.yml",
        no_color=True,
    )

    assert exit_code is ExitCode.INVALID_SCHEMA
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "PTK-DECL-005" in captured.err
    assert "schema.yml" in captured.err
    assert "\x1b[" not in captured.err
