"""Pipeline-related PyTransformKit errors."""

from typing import ClassVar

from pytransformkit.errors.base import PyTransformKitError
from pytransformkit.errors.codes import ErrorCode


class PipelineError(PyTransformKitError):
    """Base class for logical Pipeline failures."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-PIPE-000")


class InvalidPipelineError(PipelineError):
    """Raised when a Pipeline graph violates a structural invariant."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-PIPE-001")


class PipelineCycleError(PipelineError):
    """Raised when a Pipeline graph contains a directed cycle."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-PIPE-002")


class PipelineNodeNotFoundError(PipelineError):
    """Raised when a dependency references an unknown Pipeline node."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-PIPE-003")

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        super().__init__(f"Pipeline node {node_id!r} was not found.")
