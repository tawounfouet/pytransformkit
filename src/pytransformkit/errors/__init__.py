"""Public PyTransformKit exception hierarchy."""

from pytransformkit.errors.base import PyTransformKitError
from pytransformkit.errors.codes import ErrorCode
from pytransformkit.errors.engine import (
    AdapterError,
    BindingError,
    EngineContractViolationError,
    EngineError,
    EngineNotFoundError,
    ExecutionCancelledError,
    ExecutionError,
    ExecutionTimeoutError,
    ResourceResolutionError,
    TransformationExecutionError,
    UnknownOutcomeExecutionError,
    UnsupportedEngineCapabilityError,
)
from pytransformkit.errors.expression import (
    ExpressionError,
    ExpressionTypeError,
    FunctionNotFoundError,
    InvalidBooleanUsageError,
)
from pytransformkit.errors.io import (
    ResourceIOError,
    ResourcePathViolationError,
    ResourceReadError,
    ResourceWriteError,
    UnsupportedResourceFormatError,
    UnsupportedResourceSchemeError,
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
from pytransformkit.errors.serialization import (
    InvalidWirePayloadError,
    MigrationError,
    NonPortableValueError,
    PayloadTooLargeError,
    SerializationError,
    UnknownContractError,
    UnsupportedContractVersionError,
    WireParseError,
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
    "EngineContractViolationError",
    "EngineError",
    "EngineNotFoundError",
    "ErrorCode",
    "ExecutionCancelledError",
    "ExecutionError",
    "ExecutionTimeoutError",
    "ExpressionError",
    "ExpressionTypeError",
    "FieldCollisionError",
    "FieldNotFoundError",
    "FunctionNotFoundError",
    "InvalidBooleanUsageError",
    "InvalidPipelineError",
    "InvalidTransformationError",
    "InvalidValidationError",
    "InvalidWirePayloadError",
    "LineageError",
    "MigrationError",
    "NonPortableValueError",
    "PipelineCycleError",
    "PipelineError",
    "PayloadTooLargeError",
    "PipelineNodeNotFoundError",
    "PyTransformKitError",
    "QualityError",
    "QualityGateError",
    "ResourceIOError",
    "ResourcePathViolationError",
    "ResourceReadError",
    "ResourceResolutionError",
    "ResourceWriteError",
    "SchemaError",
    "SerializationError",
    "TransformationError",
    "TransformationExecutionError",
    "UnknownContractError",
    "UnknownOutcomeExecutionError",
    "UnsupportedContractVersionError",
    "UnsupportedEngineCapabilityError",
    "UnsupportedResourceFormatError",
    "UnsupportedResourceSchemeError",
    "UnsupportedLineageError",
    "UnsupportedTransformationError",
    "WireParseError",
]
