"""Public PyTransformKit exception hierarchy."""

from pytransformkit.errors.base import PyTransformKitError
from pytransformkit.errors.codes import ErrorCode
from pytransformkit.errors.engine import (
    AdapterError,
    BindingError,
    EngineError,
    EngineNotFoundError,
    ExecutionError,
    ResourceResolutionError,
    UnsupportedEngineCapabilityError,
)
from pytransformkit.errors.expression import (
    ExpressionError,
    ExpressionTypeError,
    FunctionNotFoundError,
    InvalidBooleanUsageError,
)
from pytransformkit.errors.lineage import LineageError, UnsupportedLineageError
from pytransformkit.errors.pipeline import (
    InvalidPipelineError,
    PipelineCycleError,
    PipelineError,
    PipelineNodeNotFoundError,
)
from pytransformkit.errors.quality import (
    InvalidValidationError,
    QualityError,
    QualityGateError,
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
    "BindingError",
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
    "InvalidValidationError",
    "LineageError",
    "PipelineCycleError",
    "PipelineError",
    "PipelineNodeNotFoundError",
    "PyTransformKitError",
    "QualityError",
    "QualityGateError",
    "ResourceResolutionError",
    "SchemaError",
    "TransformationError",
    "UnsupportedEngineCapabilityError",
    "UnsupportedLineageError",
    "UnsupportedTransformationError",
]
