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
class TransformationPlanId(Identifier):
    """Identity of a TransformationPlan authoring value."""


# Pre-1.0 internal compatibility name. The canonical V1 name is
# TransformationPlanId.
PipelineId = TransformationPlanId


@dataclass(frozen=True, slots=True)
class NodeId(Identifier):
    """Identity of an internal logical-plan node."""


@dataclass(frozen=True, slots=True)
class StepId(Identifier):
    """Identity of one logical transformation occurrence."""


@dataclass(frozen=True, slots=True)
class TransformationExecutionId(Identifier):
    """Identity of one semantic TransformationRuntime execution."""


@dataclass(frozen=True, slots=True)
class CorrelationId(Identifier):
    """Identity grouping related work without replacing native execution IDs."""


@dataclass(frozen=True, slots=True)
class RuntimeEventId(Identifier):
    """Identity of one runtime observability event."""


# Pre-1.0 internal compatibility name. The canonical V1 name is
# TransformationExecutionId.
ExecutionId = TransformationExecutionId
