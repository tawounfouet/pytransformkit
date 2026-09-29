"""Physical execution result contracts."""

from dataclasses import dataclass

from pytransformkit.application.ports.engines import PhysicalHandle
from pytransformkit.domain.data.schema import Schema


@dataclass(frozen=True, slots=True)
class NamedEngineOutput:
    """One named physical output produced by an engine adapter."""

    name: str
    output_handle: PhysicalHandle
    output_schema: Schema

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("NamedEngineOutput name must not be empty.")
        if not isinstance(self.output_schema, Schema):
            raise TypeError("NamedEngineOutput output_schema must be a Schema.")


@dataclass(frozen=True, slots=True)
class EngineExecutionResult:
    """Result returned by an EngineAdapter before public result wrapping."""

    output_handle: PhysicalHandle
    output_schema: Schema
    named_outputs: tuple[NamedEngineOutput, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.output_schema, Schema):
            raise TypeError("Execution result output_schema must be a Schema.")
        if not isinstance(self.named_outputs, tuple):
            raise TypeError("Execution result named_outputs must be a tuple.")
        if any(
            not isinstance(output, NamedEngineOutput) for output in self.named_outputs
        ):
            raise TypeError(
                "Execution result named_outputs must contain NamedEngineOutput."
            )

    def output(self, name: str) -> NamedEngineOutput:
        """Return one named output."""
        for output in self.named_outputs:
            if output.name == name:
                return output
        raise KeyError(name)
