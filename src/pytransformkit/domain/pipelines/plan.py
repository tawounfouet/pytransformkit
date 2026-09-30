"""Engine-independent compiled logical plans."""

from dataclasses import dataclass

from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.pipelines.nodes import PipelineNodeKind
from pytransformkit.domain.shared.identifiers import (
    DatasetId,
    NodeId,
    PipelineId,
    StepId,
    TransformationPlanId,
)
from pytransformkit.domain.transformations.base import TransformationSpec


@dataclass(frozen=True, slots=True)
class LogicalPlanNode:
    """One statically resolved node in a LogicalPlan."""

    node_id: NodeId
    kind: PipelineNodeKind
    input_schema: Schema | None
    output_schema: Schema
    dataset_id: DatasetId
    step_id: StepId | None = None
    transformation: TransformationSpec | None = None
    name: str | None = None
    input_node_ids: tuple[NodeId, ...] = ()
    input_schemas: tuple[Schema, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.dataset_id, DatasetId):
            raise TypeError("LogicalPlanNode dataset_id must be a DatasetId.")
        if self.input_schemas and len(self.input_schemas) != len(self.input_node_ids):
            raise ValueError(
                "LogicalPlanNode input_schemas and input_node_ids must align."
            )


@dataclass(frozen=True, slots=True)
class LogicalPlan:
    """Validated engine-independent plan ready for adapter lowering."""

    pipeline_id: PipelineId
    pipeline_name: str
    nodes: tuple[LogicalPlanNode, ...]
    output_schema: Schema
    output_schemas: tuple[tuple[str, Schema], ...] = ()

    def __post_init__(self) -> None:
        if not self.nodes:
            raise ValueError("LogicalPlan must contain at least one node.")
        if not self.output_schemas:
            object.__setattr__(
                self,
                "output_schemas",
                (("output", self.output_schema),),
            )

    @property
    def plan_id(self) -> TransformationPlanId:
        """Canonical V1 name for the plan declaration identity."""
        return self.pipeline_id

    @property
    def plan_name(self) -> str:
        """Canonical V1 name for the compiled declaration name."""
        return self.pipeline_name

    @property
    def input_names(self) -> tuple[str, ...]:
        return tuple(
            node.name
            for node in self.nodes
            if node.kind is PipelineNodeKind.INPUT and node.name is not None
        )

    @property
    def output_names(self) -> tuple[str, ...]:
        return tuple(name for name, _ in self.output_schemas)

    def schema_for_output(self, name: str) -> Schema:
        for output_name, schema in self.output_schemas:
            if output_name == name:
                return schema
        raise KeyError(name)
