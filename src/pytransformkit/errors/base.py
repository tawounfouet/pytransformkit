"""Base exception for PyTransformKit."""

from typing import ClassVar

from pytransformkit.errors.codes import ErrorCode


class PyTransformKitError(Exception):
    """Root exception for all expected PyTransformKit failures."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-CORE-000")

    @property
    def code(self) -> ErrorCode:
        """Return the stable machine-readable error code."""
        return self.error_code
