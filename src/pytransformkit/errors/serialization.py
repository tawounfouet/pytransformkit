"""Versioned serialization and wire-contract errors."""

from typing import ClassVar

from pytransformkit.errors.base import PyTransformKitError
from pytransformkit.errors.codes import ErrorCode


class SerializationError(PyTransformKitError):
    """Base class for portable wire-contract failures."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-WIRE-000")


class WireParseError(SerializationError):
    """Raised when JSON cannot be parsed unambiguously."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-WIRE-001")


class UnknownContractError(SerializationError):
    """Raised when an envelope uses a different semantic contract."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-WIRE-002")


class UnsupportedContractVersionError(SerializationError):
    """Raised when no safe migration path exists for a wire version."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-WIRE-003")


class InvalidWirePayloadError(SerializationError):
    """Raised when a payload violates its structural or semantic schema."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-WIRE-004")


class PayloadTooLargeError(SerializationError):
    """Raised before parsing a payload larger than the configured bound."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-WIRE-005")


class NonPortableValueError(SerializationError):
    """Raised when durable encoding encounters executable/process-local state."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-WIRE-006")


class MigrationError(SerializationError):
    """Raised when an explicit wire migration cannot complete safely."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-WIRE-007")
