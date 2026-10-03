from __future__ import annotations

from pytransformkit.cli.exit_codes import ExitCode
from pytransformkit.cli.models.errors import CLIErrorReport, ErrorCategory
from pytransformkit.cli.security import (
    REDACTED,
    redact_details,
    redact_error_report,
    redact_text,
    redacted_traceback,
)


def test_redact_text_covers_named_secrets_bearer_tokens_and_uri_userinfo() -> None:
    value = (
        'password=hunter2 token: abc123 '
        '"api_key": "json-secret" '
        "Authorization: Bearer bearer-secret "
        "https://user:pass@example.invalid/schema.yml"
    )

    redacted = redact_text(value)

    for secret in ("hunter2", "abc123", "json-secret", "bearer-secret", "user:pass"):
        assert secret not in redacted
    assert redacted.count(REDACTED) >= 5
    assert "example.invalid/schema.yml" in redacted


def test_redact_details_redacts_sensitive_keys_and_nested_text_values() -> None:
    redacted = redact_details(
        {
            "token": "raw-token",
            "context": "client_secret=raw-client-secret",
            "safe": "ordinary detail",
        }
    )

    assert redacted == {
        "token": REDACTED,
        "context": f"client_secret={REDACTED}",
        "safe": "ordinary detail",
    }


def test_redact_error_report_preserves_semantics_while_removing_secrets() -> None:
    report = CLIErrorReport(
        category=ErrorCategory.FILESYSTEM_ERROR,
        message="authorization=top-secret failed",
        exit_code=ExitCode.FILESYSTEM_ERROR,
        code="PTK-DECL-011",
        path="https://user:pass@example.invalid/schema.yml",
        hint="token=hint-secret",
        details={"api_key": "detail-secret"},
    )

    redacted = redact_error_report(report)

    assert redacted.category is report.category
    assert redacted.exit_code is report.exit_code
    assert redacted.code == report.code
    assert "top-secret" not in redacted.message
    assert "user:pass" not in (redacted.path or "")
    assert "hint-secret" not in (redacted.hint or "")
    assert redacted.details == {"api_key": REDACTED}


def test_redacted_traceback_keeps_debug_shape_without_secret_value() -> None:
    try:
        raise RuntimeError("token=trace-secret")
    except RuntimeError as exc:
        rendered = redacted_traceback(exc)

    assert "Traceback" in rendered
    assert "RuntimeError" in rendered
    assert "trace-secret" not in rendered
    assert f"token={REDACTED}" in rendered
