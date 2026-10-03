from __future__ import annotations

import json
import re
import sys

import pytest

pytest.importorskip("typer")
pytest.importorskip("rich")

from typer.testing import CliRunner

from pytransformkit.cli.app import app
from pytransformkit.conformance.model import engine_capabilities
from pytransformkit.domain.engines import EngineCapability

runner = CliRunner()

ENGINE_IDS = ["pandas", "polars", "pyarrow", "duckdb"]


def test_engines_help_exposes_list_and_inspect() -> None:
    result = runner.invoke(app, ["engines", "--help"])

    assert result.exit_code == 0
    plain = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    assert "list" in plain
    assert "inspect" in plain


def test_engines_list_human_is_deterministic() -> None:
    result = runner.invoke(app, ["engines", "list", "--no-color"])

    assert result.exit_code == 0
    assert result.stderr == ""
    positions = [result.stdout.index(engine_id) for engine_id in ENGINE_IDS]
    assert positions == sorted(positions)
    assert "STABLE" in result.stdout
    assert "PROVISIONAL" in result.stdout
    assert "\x1b[" not in result.stdout


def test_engines_list_json_has_stable_minimum_contract() -> None:
    result = runner.invoke(app, ["engines", "list", "--json"])

    assert result.exit_code == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)

    assert payload["contract_version"] == 1
    assert payload["ok"] is True
    assert payload["command"] == "engines.list"
    engines = payload["data"]["engines"]
    assert [engine["id"] for engine in engines] == ENGINE_IDS
    assert [engine["qualification"] for engine in engines] == [
        "stable",
        "stable",
        "provisional",
        "provisional",
    ]
    for engine in engines:
        assert isinstance(engine["installed"], bool)


def test_engines_inspect_json_uses_conformance_capability_authority() -> None:
    result = runner.invoke(app, ["engines", "inspect", "polars", "--json"])

    assert result.exit_code == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    data = payload["data"]

    assert payload["command"] == "engines.inspect"
    assert data["id"] == "polars"
    assert data["qualification"] == "stable"
    assert data["mandatory_for_v1"] is True
    assert data["capabilities"] == [
        capability.value
        for capability in EngineCapability
        if capability in engine_capabilities("polars")
    ]
    assert data["capabilities"][-1] == "lazy"
    assert all(dimension["status"] == "qualified" for dimension in data["conformance"])


def test_engines_inspect_known_provisional_engine_without_activation() -> None:
    result = runner.invoke(app, ["engines", "inspect", "pyarrow", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)["data"]
    assert data["id"] == "pyarrow"
    assert data["qualification"] == "provisional"
    assert data["mandatory_for_v1"] is False
    assert "select" in data["capabilities"]
    assert "join_inner" not in data["capabilities"]


def test_engines_inspect_normalizes_engine_identifier() -> None:
    result = runner.invoke(
        app,
        ["engines", "inspect", "  PANDAS  ", "--quiet"],
    )

    assert result.exit_code == 0
    assert result.stdout == "pandas\n"
    assert result.stderr == ""


def test_engines_inspect_unknown_engine_is_usage_error() -> None:
    result = runner.invoke(app, ["engines", "inspect", "spark"])

    assert result.exit_code == 2
    assert result.stdout == ""
    assert "Unknown engine id" in result.stderr
    assert "pandas" in result.stderr


def test_engines_inspect_unknown_engine_json_is_error_report() -> None:
    result = runner.invoke(
        app,
        ["engines", "inspect", "spark", "--json"],
    )

    assert result.exit_code == 2
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["command"] == "engines.inspect"
    assert payload["error"]["category"] == "invalid_usage"


def test_engines_list_does_not_import_optional_engine_modules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    heavy_modules = ("pandas", "polars", "pyarrow", "duckdb")
    previous = {name: sys.modules.get(name) for name in heavy_modules}

    for name in heavy_modules:
        monkeypatch.setitem(sys.modules, name, None)

    result = runner.invoke(app, ["engines", "list", "--json"])

    assert result.exit_code == 0
    for name in heavy_modules:
        assert sys.modules[name] is None

    for name, module in previous.items():
        if module is not None:
            monkeypatch.setitem(sys.modules, name, module)


def test_engines_inspect_verbose_includes_conformance_matrix() -> None:
    result = runner.invoke(
        app,
        ["engines", "inspect", "duckdb", "--verbose", "--no-color"],
    )

    assert result.exit_code == 0
    assert "Conformance dimension" in result.stdout
    assert "null_nan" in result.stdout
    assert "PROVISIONAL" in result.stdout
    assert "\x1b[" not in result.stdout
