"""Lineage-related PyTransformKit errors."""

from typing import ClassVar

from pytransformkit.errors.base import PyTransformKitError
from pytransformkit.errors.codes import ErrorCode


class LineageError(PyTransformKitError):
    """Base class for logical-lineage failures."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-LINEAGE-000")


class UnsupportedLineageError(LineageError):
    """Raised when exact lineage is unavailable for a transformation."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-LINEAGE-001")
