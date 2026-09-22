"""Public PyTransformKit exception hierarchy."""

from pytransformkit.errors.base import PyTransformKitError
from pytransformkit.errors.codes import ErrorCode
from pytransformkit.errors.expression import (
    ExpressionError,
    ExpressionTypeError,
    FunctionNotFoundError,
    InvalidBooleanUsageError,
)
from pytransformkit.errors.pipeline import (
    InvalidPipelineError,
    PipelineCycleError,
    PipelineError,
    PipelineNodeNotFoundError,
)
from pytransformkit.errors.schema import (
    DuplicateFieldError,
    FieldCollisionError,
    FieldNotFoundError,
    SchemaError,
)
from pytransformkit.errors.transformation import (
    InvalidTransformationError,
    TransformationError,
    UnsupportedTransformationError,
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
    "InvalidPipelineError",
    "InvalidTransformationError",
    "PipelineCycleError",
    "PipelineError",
    "PipelineNodeNotFoundError",
    "PyTransformKitError",
    "SchemaError",
    "TransformationError",
    "UnsupportedTransformationError",
]
