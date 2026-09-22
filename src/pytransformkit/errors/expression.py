"""Expression-related PyTransformKit errors."""

from typing import ClassVar

from pytransformkit.errors.base import PyTransformKitError
from pytransformkit.errors.codes import ErrorCode


class ExpressionError(PyTransformKitError):
    """Base class for logical Expression failures."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-EXPR-000")


class ExpressionTypeError(ExpressionError):
    """Raised when an Expression is not type-correct."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-EXPR-001")


class InvalidBooleanUsageError(ExpressionError):
    """Raised when Python attempts to coerce an Expression to bool."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-EXPR-002")

    def __init__(self) -> None:
        super().__init__(
            "PyTransformKit Expressions cannot be coerced to Python bool. "
            "Use '&', '|', and '~' for logical composition."
        )


class FunctionNotFoundError(ExpressionError):
    """Raised when an unknown logical function is resolved."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-EXPR-003")

    def __init__(self, function_name: str) -> None:
        self.function_name = function_name
        super().__init__(f"Logical function {function_name!r} is not registered.")
