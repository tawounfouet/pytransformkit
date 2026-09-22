"""Execution context and mode."""

from dataclasses import dataclass, field
from enum import StrEnum

from pytransformkit.domain.shared.identifiers import ExecutionId


class ExecutionMode(StrEnum):
    EAGER = "eager"
    LAZY = "lazy"
    AUTO = "auto"


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """Immutable context frozen for one physical execution."""

    execution_id: ExecutionId = field(default_factory=ExecutionId.new)
    mode: ExecutionMode = ExecutionMode.AUTO

    def __post_init__(self) -> None:
        if not isinstance(self.execution_id, ExecutionId):
            raise TypeError("Execution context id must be an ExecutionId.")
        if not isinstance(self.mode, ExecutionMode):
            raise TypeError("Execution context mode must be an ExecutionMode.")
