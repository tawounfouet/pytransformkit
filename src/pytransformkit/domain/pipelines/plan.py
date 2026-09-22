"""Engine-independent logical Pipeline plans."""

from dataclasses import dataclass

from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.pipelines.nodes import PipelineNodeKind
from pytransformkit.domain.shared.identifiers import (
    NodeId,
    PipelineId,
    StepId,
)
from pytransformkit.domain.transformations.base import TransformationSpec


@dataclass(frozen=True, slots=True)
class LogicalPlanNode:
    """One statically resolved node in a LogicalPlan."""

    node_id: NodeId
    kind: PipelineNodeKind
    input_schema: Schema | None
    output_schema: Schema
    step_id: StepId | None = None
    transformation: TransformationSpec | None = None


@dataclass(frozen=True, slots=True)
class LogicalPlan:
    """Validated engine-independent plan ready for physical planning."""

    pipeline_id: PipelineId
    pipeline_name: str
    nodes: tuple[LogicalPlanNode, ...]
    output_schema: Schema

    def __post_init__(self) -> None:
        if not self.nodes:
            raise ValueError("LogicalPlan must contain at least one node.")
