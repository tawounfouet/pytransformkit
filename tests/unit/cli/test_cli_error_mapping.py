from __future__ import annotations

from pytransformkit.cli.exceptions import (
    CLIFileSystemError,
    CLIUnsupportedOperationError,
    CLIUsageError,
    error_report_from_exception,
)
from pytransformkit.cli.exit_codes import ExitCode
from pytransformkit.cli.models.errors import ErrorCategory
from pytransformkit.errors import (
    DeclarativeSchemaDependencyError,
    DeclarativeSchemaIOError,
    DeclarativeSchemaTypeError,
    WireParseError,
)


def test_usage_error_maps_to_exit_2() -> None:
    report = error_report_from_exception(CLIUsageError("invalid combination"))

    assert report.category is ErrorCategory.INVALID_USAGE
    assert report.exit_code is ExitCode.INVALID_USAGE
    assert report.message == "invalid combination"


def test_declarative_schema_error_preserves_public_ptk_code() -> None:
    report = error_report_from_exception(
        DeclarativeSchemaTypeError("money128"),
        path="schema.yml",
    )

    assert report.category is ErrorCategory.INVALID_SCHEMA
    assert report.exit_code is ExitCode.INVALID_SCHEMA
    assert report.code == "PTK-DECL-005"
    assert report.path == "schema.yml"


def test_declarative_dependency_error_maps_to_missing_optional_dependency() -> None:
    report = error_report_from_exception(DeclarativeSchemaDependencyError("PyYAML"))

    assert report.category is ErrorCategory.MISSING_OPTIONAL_DEPENDENCY
    assert report.exit_code is ExitCode.MISSING_OPTIONAL_DEPENDENCY
    assert report.code == "PTK-DECL-010"


def test_declarative_io_error_maps_to_filesystem_and_keeps_path() -> None:
    report = error_report_from_exception(
        DeclarativeSchemaIOError("schemas/customers.yml", "read")
    )

    assert report.category is ErrorCategory.FILESYSTEM_ERROR
    assert report.exit_code is ExitCode.FILESYSTEM_ERROR
    assert report.code == "PTK-DECL-011"
    assert report.path == "schemas/customers.yml"


def test_serialization_error_maps_to_invalid_schema_and_preserves_code() -> None:
    report = error_report_from_exception(
        WireParseError("invalid wire JSON"),
        path="schema.json",
    )

    assert report.category is ErrorCategory.INVALID_SCHEMA
    assert report.exit_code is ExitCode.INVALID_SCHEMA
    assert report.code == "PTK-WIRE-001"
    assert report.path == "schema.json"


def test_cli_filesystem_error_uses_its_explicit_output_path() -> None:
    report = error_report_from_exception(
        CLIFileSystemError("out/schema.json", "destination exists"),
        path="input.yml",
    )

    assert report.category is ErrorCategory.FILESYSTEM_ERROR
    assert report.exit_code is ExitCode.FILESYSTEM_ERROR
    assert report.path == "out/schema.json"


def test_known_filesystem_error_maps_to_exit_12() -> None:
    report = error_report_from_exception(
        FileNotFoundError("missing"),
        path="missing.yml",
    )

    assert report.category is ErrorCategory.FILESYSTEM_ERROR
    assert report.exit_code is ExitCode.FILESYSTEM_ERROR
    assert report.path == "missing.yml"


def test_unsupported_operation_maps_to_exit_13() -> None:
    report = error_report_from_exception(
        CLIUnsupportedOperationError("remote sources are unsupported")
    )

    assert report.category is ErrorCategory.UNSUPPORTED_OPERATION
    assert report.exit_code is ExitCode.UNSUPPORTED_OPERATION


def test_keyboard_interrupt_and_broken_pipe_have_dedicated_outcomes() -> None:
    interrupted = error_report_from_exception(KeyboardInterrupt())
    broken_pipe = error_report_from_exception(BrokenPipeError())

    assert interrupted.category is ErrorCategory.INTERRUPTED
    assert interrupted.exit_code is ExitCode.INTERRUPTED
    assert broken_pipe.category is ErrorCategory.BROKEN_PIPE
    assert broken_pipe.exit_code is ExitCode.BROKEN_PIPE


def test_unexpected_exception_does_not_leak_raw_message() -> None:
    report = error_report_from_exception(RuntimeError("SECRET_TOKEN_DO_NOT_RENDER"))

    assert report.category is ErrorCategory.INTERNAL_ERROR
    assert report.exit_code is ExitCode.INTERNAL_ERROR
    assert "SECRET_TOKEN_DO_NOT_RENDER" not in report.message
    assert report.hint is not None
