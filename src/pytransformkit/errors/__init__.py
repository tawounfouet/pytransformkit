"""Public PyTransformKit exception hierarchy."""

from pytransformkit.errors.base import PyTransformKitError
from pytransformkit.errors.codes import ErrorCode
from pytransformkit.errors.expression import (
    ExpressionError,
    ExpressionTypeError,
    FunctionNotFoundError,
    InvalidBooleanUsageError,
)
from pytransformkit.errors.schema import (
    DuplicateFieldError,
    FieldCollisionError,
    FieldNotFoundError,
    SchemaError,
)

__all__ = [
    "DuplicateFieldError",
    "ErrorCode",
    "ExpressionError",
    "ExpressionTypeError",
    "FieldCollisionError",
    "FieldNotFoundError",
    "FunctionNotFoundError",
    "InvalidBooleanUsageError",
    "PyTransformKitError",
    "SchemaError",
]
