"""Stable process exit codes for the PyTransformKit CLI."""

from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    """Process exit codes defined by the CLI v1 candidate contract."""

    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_USAGE = 2
    INVALID_SCHEMA = 10
    MISSING_OPTIONAL_DEPENDENCY = 11
    FILESYSTEM_ERROR = 12
    UNSUPPORTED_OPERATION = 13
    INTERNAL_ERROR = 70
    INTERRUPTED = 130
    BROKEN_PIPE = 141


__all__ = ["ExitCode"]
