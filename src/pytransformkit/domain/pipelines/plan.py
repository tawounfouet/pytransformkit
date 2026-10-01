"""Engine-independent compiled logical plans."""

from dataclasses import dataclass

from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.pipelines.nodes import PipelineNodeKind
from pytransformkit.domain.shared.fingerprint import Fingerprint
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

    @property
    def required_capabilities(self):
        """Return the engine capabilities required by this LogicalPlan."""
        from pytransformkit.application.execution.compatibility import (
            EngineCapabilityAnalyzer,
        )

        return EngineCapabilityAnalyzer().required_capabilities(self)

    @property
    def lineage(self):
        """Return engine-independent logical lineage for this compiled plan."""
        from pytransformkit.domain.lineage import LineageAnalyzer

        return LineageAnalyzer().analyze(self)

    def fingerprint(self) -> Fingerprint:
        """Return a deterministic semantic fingerprint for this LogicalPlan."""
        from pytransformkit.application.planning.fingerprint import (
            logical_plan_fingerprint,
        )

        return logical_plan_fingerprint(self)

    def explain(self, *, format: str = "text") -> str:
        """Explain the compiled plan without invoking an execution engine."""
        import json

        capabilities = tuple(
            sorted(capability.value for capability in self.required_capabilities)
        )
        payload = {
            "format_version": 1,
            "name": self.plan_name,
            "inputs": self.input_names,
            "outputs": self.output_names,
            "node_count": len(self.nodes),
            "required_capabilities": capabilities,
            "fingerprint": str(self.fingerprint()),
        }

        if format == "json":
            return json.dumps(payload, sort_keys=True, separators=(",", ":"))
        if format != "text":
            raise ValueError("LogicalPlan explain format must be 'text' or 'json'.")

        return (
            f"LogicalPlan {self.plan_name!r}\n"
            f"inputs: {', '.join(self.input_names) or '<none>'}\n"
            f"outputs: {', '.join(self.output_names) or '<none>'}\n"
            f"nodes: {len(self.nodes)}\n"
            "required_capabilities: "
            f"{', '.join(capabilities) or '<none>'}\n"
            f"fingerprint: {self.fingerprint()}"
        )
