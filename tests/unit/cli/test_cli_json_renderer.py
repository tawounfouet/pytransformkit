from __future__ import annotations

import json

from pytransformkit.cli.exit_codes import ExitCode
from pytransformkit.cli.models.errors import CLIErrorReport, ErrorCategory
from pytransformkit.cli.rendering.json import JSONRenderer


def test_json_renderer_success_uses_v1_envelope() -> None:
    rendered = JSONRenderer().render_success(
        command="version",
        data={"pytransformkit": "1.2.0a1", "label": "Créé à Paris"},
    )

    payload = json.loads(rendered)

    assert payload == {
        "contract_version": 1,
        "ok": True,
        "command": "version",
        "data": {
            "pytransformkit": "1.2.0a1",
            "label": "Créé à Paris",
        },
    }
    assert "\x1b[" not in rendered
    assert "Créé à Paris" in rendered


def test_json_renderer_error_uses_error_envelope() -> None:
    error = CLIErrorReport(
        category=ErrorCategory.INVALID_SCHEMA,
        message="Unsupported type.",
        exit_code=ExitCode.INVALID_SCHEMA,
        code="PTK-DECL-005",
        path="schema.yml",
    )

    rendered = JSONRenderer().render_error(
        command="schema.validate",
        error=error,
    )
    payload = json.loads(rendered)

    assert payload["contract_version"] == 1
    assert payload["ok"] is False
    assert payload["command"] == "schema.validate"
    assert "data" not in payload
    assert payload["error"] == {
        "category": "invalid_schema",
        "message": "Unsupported type.",
        "code": "PTK-DECL-005",
        "path": "schema.yml",
    }
    assert "\x1b[" not in rendered


def test_json_renderer_is_deterministic_for_equivalent_input() -> None:
    renderer = JSONRenderer()

    first = renderer.render_success(
        command="doctor",
        data={"status": "healthy", "count": 2},
    )
    second = renderer.render_success(
        command="doctor",
        data={"status": "healthy", "count": 2},
    )

    assert first == second


def test_json_renderer_normalizes_nested_mapping_order_and_unicode() -> None:
    renderer = JSONRenderer()

    first = renderer.render_success(
        command="contract.inspect",
        data={
            "zeta": {"beta": 2, "alpha": 1},
            "alpha": "Créé à Paris — 東京",
        },
    )
    second = renderer.render_success(
        command="contract.inspect",
        data={
            "alpha": "Créé à Paris — 東京",
            "zeta": {"alpha": 1, "beta": 2},
        },
    )

    assert first == second
    assert "Créé à Paris — 東京" in first
    assert "\\u6771" not in first
    assert "\x1b[" not in first
