"""Physical resource I/O errors."""

from typing import ClassVar

from pytransformkit.errors.base import PyTransformKitError
from pytransformkit.errors.codes import ErrorCode


class ResourceIOError(PyTransformKitError):
    """Base class for bounded physical resource I/O failures."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-IO-000")


class UnsupportedResourceSchemeError(ResourceIOError):
    """Raised when no Reader/Writer is registered for a resource scheme."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-IO-001")


class UnsupportedResourceFormatError(ResourceIOError):
    """Raised when a physical resource format is not supported."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-IO-002")


class ResourceReadError(ResourceIOError):
    """Raised when a physical resource cannot be read safely."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-IO-003")


class ResourceWriteError(ResourceIOError):
    """Raised when a physical write is known to have failed."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-IO-004")


class ResourcePathViolationError(ResourceIOError):
    """Raised when a local resource escapes its configured filesystem root."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-IO-005")
