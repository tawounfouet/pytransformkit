"""Logical Pipeline planning and Schema propagation."""

from collections import defaultdict

from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.pipelines.nodes import (
    InputNode,
    OutputNode,
    PipelineNode,
    TransformationNode,
)
from pytransformkit.domain.pipelines.pipeline import Pipeline
from pytransformkit.domain.pipelines.plan import LogicalPlan, LogicalPlanNode
from pytransformkit.domain.pipelines.validation import (
    PipelineGraphValidator,
    topological_order,
)
from pytransformkit.domain.shared.identifiers import NodeId
from pytransformkit.domain.transformations.schema_resolution import (
    OutputSchemaResolver,
)
from pytransformkit.errors.pipeline import InvalidPipelineError


class PipelinePlanner:
    """Validate a Pipeline and propagate Schemas through its DAG."""

    def __init__(
        self,
        output_schema_resolver: OutputSchemaResolver | None = None,
    ) -> None:
        self._output_schema_resolver = (
            output_schema_resolver or OutputSchemaResolver()
        )

    def plan(self, pipeline: Pipeline) -> LogicalPlan:
        PipelineGraphValidator().validate(
            pipeline.nodes,
            pipeline.dependencies,
        )
        ordered_ids = topological_order(
            pipeline.nodes,
            pipeline.dependencies,
        )
        node_by_id = {node.id: node for node in pipeline.nodes}
        predecessors = _predecessors(pipeline)
        output_schema_by_node: dict[NodeId, Schema] = {}
        planned_nodes: list[LogicalPlanNode] = []

        for node_id in ordered_ids:
            node = node_by_id[node_id]
            planned = self._plan_node(
                node,
                predecessors[node_id],
                output_schema_by_node,
            )
            output_schema_by_node[node_id] = planned.output_schema
            planned_nodes.append(planned)

        output_schema = output_schema_by_node[pipeline.output_node.id]

        return LogicalPlan(
            pipeline_id=pipeline.id,
            pipeline_name=pipeline.name,
            nodes=tuple(planned_nodes),
            output_schema=output_schema,
        )

    def _plan_node(
        self,
        node: PipelineNode,
        predecessor_ids: tuple[NodeId, ...],
        output_schema_by_node: dict[NodeId, Schema],
    ) -> LogicalPlanNode:
        if isinstance(node, InputNode):
            if predecessor_ids:
                raise InvalidPipelineError(
                    "Input nodes cannot have predecessors."
                )
            return LogicalPlanNode(
                node_id=node.id,
                kind=node.kind,
                input_schema=None,
                output_schema=node.schema,
            )

        if len(predecessor_ids) != 1:
            raise InvalidPipelineError(
                "The initial Pipeline planner requires exactly one "
                "predecessor for every non-input node."
            )

        input_schema = output_schema_by_node[predecessor_ids[0]]

        if isinstance(node, TransformationNode):
            output_schema = self._output_schema_resolver.resolve(
                node.transformation,
                input_schema,
            )
            return LogicalPlanNode(
                node_id=node.id,
                kind=node.kind,
                input_schema=input_schema,
                output_schema=output_schema,
                step_id=node.step_id,
                transformation=node.transformation,
            )

        if isinstance(node, OutputNode):
            return LogicalPlanNode(
                node_id=node.id,
                kind=node.kind,
                input_schema=input_schema,
                output_schema=input_schema,
            )

        raise InvalidPipelineError(
            f"Unsupported Pipeline node {type(node).__name__!r}."
        )


def _predecessors(
    pipeline: Pipeline,
) -> dict[NodeId, tuple[NodeId, ...]]:
    values: dict[NodeId, list[NodeId]] = defaultdict(list)
    for dependency in pipeline.dependencies:
        values[dependency.target].append(dependency.source)

    return {
        node.id: tuple(values[node.id])
        for node in pipeline.nodes
    }
