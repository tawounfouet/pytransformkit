"""Engine, binding and adapter related PyTransformKit errors."""

from typing import ClassVar

from pytransformkit.errors.base import PyTransformKitError
from pytransformkit.errors.codes import ErrorCode


class EngineError(PyTransformKitError):
    """Base class for engine-related failures."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-ENGINE-000")


class EngineNotFoundError(EngineError):
    """Raised when an explicitly requested engine is not registered."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-ENGINE-001")

    def __init__(self, engine_id: str) -> None:
        self.engine_id = engine_id
        super().__init__(f"Engine {engine_id!r} is not registered.")


class UnsupportedEngineCapabilityError(EngineError):
    """Raised when an engine cannot execute required logical capabilities."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-ENGINE-002")

    def __init__(
        self,
        engine_id: str,
        missing_capabilities: tuple[str, ...],
    ) -> None:
        self.engine_id = engine_id
        self.missing_capabilities = missing_capabilities
        joined = ", ".join(missing_capabilities)
        super().__init__(
            f"Engine {engine_id!r} does not support required capabilities: {joined}."
        )


class AdapterError(EngineError):
    """Base class for physical engine adapter failures."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-ENGINE-100")


class BindingError(PyTransformKitError):
    """Raised when logical/physical runtime bindings are invalid."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-BIND-001")


class ResourceResolutionError(BindingError):
    """Raised when a portable resource cannot be resolved for execution."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-BIND-002")


class ExecutionError(PyTransformKitError):
    """Base class for logical-to-physical execution failures."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-EXEC-000")
