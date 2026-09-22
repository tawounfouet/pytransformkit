"""Public PyTransformKit exception hierarchy."""

from pytransformkit.errors.base import PyTransformKitError
from pytransformkit.errors.codes import ErrorCode
from pytransformkit.errors.engine import (
    AdapterError,
    EngineError,
    EngineNotFoundError,
    ExecutionError,
    UnsupportedEngineCapabilityError,
)
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
    "AdapterError",
    "DuplicateFieldError",
    "EngineError",
    "EngineNotFoundError",
    "ErrorCode",
    "ExecutionError",
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
    "UnsupportedEngineCapabilityError",
    "UnsupportedTransformationError",
]
