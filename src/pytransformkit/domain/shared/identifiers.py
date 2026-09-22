"""Typed identifiers used across the PyTransformKit domain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class Identifier:
    """Immutable UUID-backed domain identifier."""

    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise TypeError("Identifier value must be a UUID.")

    @classmethod
    def new(cls) -> Self:
        """Create a new identifier of the concrete identifier type."""
        return cls(uuid4())

    @classmethod
    def parse(cls, value: str) -> Self:
        """Parse a canonical UUID string into the concrete identifier type."""
        return cls(UUID(value))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class DatasetId(Identifier):
    """Identity of a logical Dataset."""


@dataclass(frozen=True, slots=True)
class SchemaId(Identifier):
    """Identity of a registered or versioned Schema."""


@dataclass(frozen=True, slots=True)
class TransformationId(Identifier):
    """Identity of a reusable Transformation."""


@dataclass(frozen=True, slots=True)
class PipelineId(Identifier):
    """Identity of a Pipeline."""


@dataclass(frozen=True, slots=True)
class NodeId(Identifier):
    """Identity of a Pipeline node."""


@dataclass(frozen=True, slots=True)
class StepId(Identifier):
    """Identity of a logical or runtime step."""


@dataclass(frozen=True, slots=True)
class ExecutionId(Identifier):
    """Identity of an execution."""
