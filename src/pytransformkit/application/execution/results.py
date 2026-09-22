"""Physical execution result contracts."""

from dataclasses import dataclass

from pytransformkit.application.ports.engines import DatasetHandle
from pytransformkit.domain.data.schema import Schema


@dataclass(frozen=True, slots=True)
class EngineExecutionResult:
    """Result returned by an EngineAdapter before public Dataset wrapping."""

    output_handle: DatasetHandle
    output_schema: Schema

    def __post_init__(self) -> None:
        if not isinstance(self.output_schema, Schema):
            raise TypeError("Execution result output_schema must be a Schema.")
