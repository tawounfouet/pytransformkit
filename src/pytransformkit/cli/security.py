"""Security helpers for safe CLI diagnostics."""

from __future__ import annotations

import re
import traceback
from collections.abc import Mapping

from pytransformkit.cli.models.errors import CLIErrorReport

REDACTED = "[REDACTED]"

_SENSITIVE_NAME = (
    r"(?:password|passwd|token|secret|api[_-]?key|authorization|"
    r"credential|private[_-]?key|client[_-]?secret)"
)
_BEARER_PATTERN = re.compile(
    r"(?i)(\b(?:authorization|token)\b\s*[:=]\s*bearer\s+)([^\s,;]+)"
)
_ASSIGNMENT_PATTERN = re.compile(
    rf"""(?ix)
    (
        ["']?{_SENSITIVE_NAME}["']?
        \s*[:=]\s*
    )
    (
        "(?:\\.|[^"])*"
        |
        '(?:\\.|[^'])*'
        |
        [^\s,;]+
    )
    """
)
_URI_USERINFO_PATTERN = re.compile(
    r"(?i)\b([a-z][a-z0-9+.-]*://)([^/@\s]+)@"
)


def _replacement(prefix: str, value: str) -> str:
    if value.startswith('"') and value.endswith('"'):
        return f'{prefix}"{REDACTED}"'
    if value.startswith("'") and value.endswith("'"):
        return f"{prefix}'{REDACTED}'"
    return f"{prefix}{REDACTED}"


def redact_text(value: str) -> str:
    """Redact common credential-bearing forms from one diagnostic string."""
    redacted = _URI_USERINFO_PATTERN.sub(
        lambda match: f"{match.group(1)}{REDACTED}@",
        value,
    )
    redacted = _BEARER_PATTERN.sub(
        lambda match: f"{match.group(1)}{REDACTED}",
        redacted,
    )
    return _ASSIGNMENT_PATTERN.sub(
        lambda match: _replacement(match.group(1), match.group(2)),
        redacted,
    )


def _is_sensitive_name(name: str) -> bool:
    return re.fullmatch(_SENSITIVE_NAME, name, flags=re.IGNORECASE) is not None


def redact_details(details: Mapping[str, str] | None) -> dict[str, str] | None:
    """Return a redacted copy of structured diagnostic details."""
    if details is None:
        return None
    return {
        key: REDACTED if _is_sensitive_name(key) else redact_text(value)
        for key, value in details.items()
    }


def redact_error_report(report: CLIErrorReport) -> CLIErrorReport:
    """Return a renderer-safe error report with sensitive text removed."""
    return CLIErrorReport(
        category=report.category,
        message=redact_text(report.message),
        exit_code=report.exit_code,
        code=report.code,
        path=redact_text(report.path) if report.path is not None else None,
        hint=redact_text(report.hint) if report.hint is not None else None,
        details=redact_details(report.details),
    )


def redacted_traceback(exc: BaseException) -> str:
    """Format one traceback and redact it before it crosses stderr."""
    return redact_text("".join(traceback.format_exception(exc)))


__all__ = [
    "REDACTED",
    "redact_details",
    "redact_error_report",
    "redact_text",
    "redacted_traceback",
]
