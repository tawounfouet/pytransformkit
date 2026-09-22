"""Transformation-related PyTransformKit errors."""

from typing import ClassVar

from pytransformkit.errors.base import PyTransformKitError
from pytransformkit.errors.codes import ErrorCode


class TransformationError(PyTransformKitError):
    """Base class for logical Transformation failures."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-TRANSFORM-000")


class InvalidTransformationError(TransformationError):
    """Raised when a Transformation definition is invalid."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-TRANSFORM-001")


class UnsupportedTransformationError(TransformationError):
    """Raised when a Transformation has no resolver implementation."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-TRANSFORM-002")
