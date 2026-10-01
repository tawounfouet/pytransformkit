"""Immutable TransformationPlan authoring aggregate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pytransformkit.domain.pipelines.dependencies import Dependency
from pytransformkit.domain.pipelines.nodes import (
    InputNode,
    OutputNode,
    PipelineNode,
    TransformationNode,
)
from pytransformkit.domain.plans.validation import TransformationPlanValidator
from pytransformkit.domain.shared.fingerprint import Fingerprint
from pytransformkit.domain.shared.identifiers import TransformationPlanId

if TYPE_CHECKING:
    from pytransformkit.authoring.plan_builder import TransformationPlanBuilder


@dataclass(frozen=True, slots=True, eq=False)
class TransformationPlan:
    """Engine-neutral immutable transformation declaration."""

    id: TransformationPlanId
    name: str
    nodes: tuple[PipelineNode, ...]
    dependencies: tuple[Dependency, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.id, TransformationPlanId):
            raise TypeError("TransformationPlan id must be a TransformationPlanId.")
        if not self.name or not self.name.strip():
            raise ValueError("TransformationPlan name must not be empty.")
        if not isinstance(self.nodes, tuple):
            raise TypeError("TransformationPlan nodes must be provided as a tuple.")
        if not isinstance(self.dependencies, tuple):
            raise TypeError(
                "TransformationPlan dependencies must be provided as a tuple."
            )
        TransformationPlanValidator().validate(
            self.nodes,
            self.dependencies,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TransformationPlan):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def builder(cls, name: str) -> TransformationPlanBuilder:
        """Create the canonical mutable authoring helper."""
        from pytransformkit.authoring.plan_builder import TransformationPlanBuilder

        return TransformationPlanBuilder(name)

    @property
    def input_nodes(self) -> tuple[InputNode, ...]:
        return tuple(node for node in self.nodes if isinstance(node, InputNode))

    @property
    def output_nodes(self) -> tuple[OutputNode, ...]:
        return tuple(node for node in self.nodes if isinstance(node, OutputNode))

    @property
    def transformation_nodes(self) -> tuple[TransformationNode, ...]:
        return tuple(
            node for node in self.nodes if isinstance(node, TransformationNode)
        )

    def validate(self) -> None:
        """Re-run structural validation without performing execution."""
        TransformationPlanValidator().validate(
            self.nodes,
            self.dependencies,
        )

    def fingerprint(self) -> Fingerprint:
        """Return the deterministic semantic fingerprint of this declaration."""
        from pytransformkit.serialization import TransformationPlanCodec

        return TransformationPlanCodec().fingerprint(self)

    def explain(self, *, format: str = "text") -> str:
        """Compile and explain this plan without executing physical data."""
        from pytransformkit.application.planning import TransformationCompiler

        return TransformationCompiler().compile(self).explain(format=format)
