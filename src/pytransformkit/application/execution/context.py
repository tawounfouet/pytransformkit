"""Execution context, mode and process-local cancellation control."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from threading import Event

from pytransformkit.domain.runtime.context import CorrelationContext
from pytransformkit.domain.shared.identifiers import TransformationExecutionId


class ExecutionMode(StrEnum):
    EAGER = "eager"
    LAZY = "lazy"
    AUTO = "auto"


class CancellationToken:
    """Process-local cooperative cancellation signal.

    The token is deliberately not serializable durable state. Runtime/provider
    support still determines whether an in-flight request can be interrupted.
    """

    __slots__ = ("_event",)

    def __init__(self) -> None:
        self._event = Event()

    def request(self) -> None:
        self._event.set()

    @property
    def requested(self) -> bool:
        return self._event.is_set()


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """Immutable context frozen for one physical execution."""

    execution_id: TransformationExecutionId = field(
        default_factory=TransformationExecutionId.new
    )
    mode: ExecutionMode = ExecutionMode.AUTO
    correlation: CorrelationContext = field(default_factory=CorrelationContext)
    cancellation: CancellationToken | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.execution_id, TransformationExecutionId):
            raise TypeError("Execution context id must be a TransformationExecutionId.")
        if not isinstance(self.mode, ExecutionMode):
            raise TypeError("Execution context mode must be an ExecutionMode.")
        if not isinstance(self.correlation, CorrelationContext):
            raise TypeError(
                "Execution context correlation must be a CorrelationContext."
            )
        if self.cancellation is not None and not isinstance(
            self.cancellation,
            CancellationToken,
        ):
            raise TypeError(
                "Execution context cancellation must be a CancellationToken."
            )
