from __future__ import annotations

from pytransformkit.diagnostics import MetricKind, RuntimeMetric, TelemetryRedactor


def test_telemetry_redactor_removes_secret_keys_and_signed_values() -> None:
    redactor = TelemetryRedactor()

    values = redactor.redact_pairs(
        (
            ("password", "super-secret"),
            ("endpoint", "https://example.test/object?sig=abc123"),
            ("engine", "pandas"),
        )
    )

    assert values == (
        ("password", "[REDACTED]"),
        ("endpoint", "[REDACTED]"),
        ("engine", "pandas"),
    )


def test_runtime_metric_rejects_execution_identity_as_default_label() -> None:
    try:
        RuntimeMetric(
            name="transformation_executions_total",
            value=1.0,
            kind=MetricKind.COUNTER,
            labels=(("execution_id", "high-cardinality"),),
        )
    except ValueError as error:
        assert "high-cardinality" in str(error)
    else:
        raise AssertionError("execution_id metric label should be rejected")
