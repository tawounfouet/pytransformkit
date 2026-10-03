from __future__ import annotations

import json

import pytest

pytest.importorskip("typer")
pytest.importorskip("rich")

from pytransformkit.cli.commands import schema as schema_command
from pytransformkit.cli.exit_codes import ExitCode
from pytransformkit.errors import DeclarativeSchemaDependencyError


def test_schema_inspect_missing_yaml_preserves_dependency_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail(self, path: str):
        raise DeclarativeSchemaDependencyError("PyYAML")

    monkeypatch.setattr(schema_command.SchemaCLIService, "inspect", fail)

    exit_code = schema_command.render_schema_inspect(
        "schema.yml",
        json_output=True,
    )

    assert exit_code is ExitCode.MISSING_OPTIONAL_DEPENDENCY
    captured = capsys.readouterr()
    assert captured.err == ""

    payload = json.loads(captured.out)
    assert payload["ok"] is False
    assert payload["command"] == "schema.inspect"
    assert payload["error"]["category"] == "missing_optional_dependency"
    assert payload["error"]["code"] == "PTK-DECL-010"
    assert payload["error"]["path"] == "schema.yml"
