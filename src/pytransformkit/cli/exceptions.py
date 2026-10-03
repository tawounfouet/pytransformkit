"""CLI-local exceptions and conversion to safe error reports."""

from __future__ import annotations

from pathlib import Path

from pytransformkit.cli.exit_codes import ExitCode
from pytransformkit.cli.models.errors import CLIErrorReport, ErrorCategory
from pytransformkit.errors import (
    DeclarativeSchemaDependencyError,
    DeclarativeSchemaError,
    DeclarativeSchemaIOError,
    PyTransformKitError,
    SerializationError,
)


class CLIUsageError(ValueError):
    """Raised for semantically contradictory CLI arguments."""


class CLIUnsupportedOperationError(RuntimeError):
    """Raised for a recognized operation intentionally unsupported by the CLI."""


class CLIFileSystemError(OSError):
    """Raised for CLI-owned filesystem failures with an explicit public path."""

    def __init__(self, path: str | Path, message: str) -> None:
        self.path = str(path)
        super().__init__(message)


def _public_ptk_code(exc: PyTransformKitError) -> str:
    return str(exc.code)


def _declarative_path(exc: DeclarativeSchemaError) -> str | None:
    if isinstance(exc, DeclarativeSchemaIOError):
        return exc.path
    return exc.source


def error_report_from_exception(
    exc: BaseException,
    *,
    path: str | Path | None = None,
) -> CLIErrorReport:
    """Map an exception to the candidate CLI v1 error contract.

    Mapping is based on structured exception types and public PTK codes rather
    than message matching.
    """
    explicit_path = str(path) if path is not None else None

    if isinstance(exc, KeyboardInterrupt):
        return CLIErrorReport(
            category=ErrorCategory.INTERRUPTED,
            message="Operation interrupted.",
            exit_code=ExitCode.INTERRUPTED,
            path=explicit_path,
        )

    if isinstance(exc, BrokenPipeError):
        return CLIErrorReport(
            category=ErrorCategory.BROKEN_PIPE,
            message="Output consumer closed the pipe.",
            exit_code=ExitCode.BROKEN_PIPE,
            path=explicit_path,
        )

    if isinstance(exc, CLIUsageError):
        return CLIErrorReport(
            category=ErrorCategory.INVALID_USAGE,
            message=str(exc),
            exit_code=ExitCode.INVALID_USAGE,
            path=explicit_path,
        )

    if isinstance(exc, CLIUnsupportedOperationError):
        return CLIErrorReport(
            category=ErrorCategory.UNSUPPORTED_OPERATION,
            message=str(exc),
            exit_code=ExitCode.UNSUPPORTED_OPERATION,
            path=explicit_path,
        )

    if isinstance(exc, DeclarativeSchemaDependencyError):
        return CLIErrorReport(
            category=ErrorCategory.MISSING_OPTIONAL_DEPENDENCY,
            message=str(exc),
            exit_code=ExitCode.MISSING_OPTIONAL_DEPENDENCY,
            code=_public_ptk_code(exc),
            path=explicit_path or _declarative_path(exc),
        )

    if isinstance(exc, DeclarativeSchemaIOError):
        return CLIErrorReport(
            category=ErrorCategory.FILESYSTEM_ERROR,
            message=str(exc),
            exit_code=ExitCode.FILESYSTEM_ERROR,
            code=_public_ptk_code(exc),
            path=explicit_path or _declarative_path(exc),
        )

    if isinstance(exc, DeclarativeSchemaError):
        return CLIErrorReport(
            category=ErrorCategory.INVALID_SCHEMA,
            message=str(exc),
            exit_code=ExitCode.INVALID_SCHEMA,
            code=_public_ptk_code(exc),
            path=explicit_path or _declarative_path(exc),
        )

    if isinstance(exc, SerializationError):
        return CLIErrorReport(
            category=ErrorCategory.INVALID_SCHEMA,
            message=str(exc),
            exit_code=ExitCode.INVALID_SCHEMA,
            code=_public_ptk_code(exc),
            path=explicit_path,
        )

    if isinstance(exc, CLIFileSystemError):
        return CLIErrorReport(
            category=ErrorCategory.FILESYSTEM_ERROR,
            message=str(exc),
            exit_code=ExitCode.FILESYSTEM_ERROR,
            path=exc.path,
        )

    if isinstance(
        exc,
        (FileNotFoundError, PermissionError, IsADirectoryError, NotADirectoryError),
    ):
        return CLIErrorReport(
            category=ErrorCategory.FILESYSTEM_ERROR,
            message=str(exc),
            exit_code=ExitCode.FILESYSTEM_ERROR,
            path=explicit_path,
        )

    if isinstance(exc, PyTransformKitError):
        return CLIErrorReport(
            category=ErrorCategory.GENERAL_ERROR,
            message=str(exc),
            exit_code=ExitCode.GENERAL_ERROR,
            code=_public_ptk_code(exc),
            path=explicit_path,
        )

    if isinstance(exc, OSError):
        return CLIErrorReport(
            category=ErrorCategory.FILESYSTEM_ERROR,
            message=str(exc),
            exit_code=ExitCode.FILESYSTEM_ERROR,
            path=explicit_path,
        )

    return CLIErrorReport(
        category=ErrorCategory.INTERNAL_ERROR,
        message="PyTransformKit encountered an internal CLI error.",
        exit_code=ExitCode.INTERNAL_ERROR,
        path=explicit_path,
        hint="Run again with --debug for technical details.",
    )


__all__ = [
    "CLIFileSystemError",
    "CLIUnsupportedOperationError",
    "CLIUsageError",
    "error_report_from_exception",
]
