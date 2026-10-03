from __future__ import annotations

import pytest

from pytransformkit.cli.exit_codes import ExitCode
from pytransformkit.cli.models.errors import CLIErrorReport, ErrorCategory


def test_error_report_public_dict_excludes_process_only_exit_code() -> None:
    report = CLIErrorReport(
        category=ErrorCategory.INVALID_SCHEMA,
        message="Invalid schema.",
        exit_code=ExitCode.INVALID_SCHEMA,
        code="PTK-DECL-003",
        path="schema.yml",
        hint="Fix the document.",
        details={"field": "customer_id"},
    )

    assert report.to_public_dict() == {
        "category": "invalid_schema",
        "message": "Invalid schema.",
        "code": "PTK-DECL-003",
        "path": "schema.yml",
        "hint": "Fix the document.",
        "details": {"field": "customer_id"},
    }


def test_error_report_details_are_defensively_copied() -> None:
    details = {"field": "customer_id"}
    report = CLIErrorReport(
        category=ErrorCategory.INVALID_SCHEMA,
        message="Invalid schema.",
        exit_code=ExitCode.INVALID_SCHEMA,
        details=details,
    )

    details["field"] = "mutated"

    assert report.to_public_dict()["details"] == {"field": "customer_id"}


@pytest.mark.parametrize("message", ["", "   "])
def test_error_report_rejects_empty_message(message: str) -> None:
    with pytest.raises(ValueError):
        CLIErrorReport(
            category=ErrorCategory.GENERAL_ERROR,
            message=message,
            exit_code=ExitCode.GENERAL_ERROR,
        )
