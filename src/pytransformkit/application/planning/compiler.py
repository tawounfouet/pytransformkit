"""Compilation from TransformationPlan to engine-neutral LogicalPlan."""

from __future__ import annotations

from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.pipelines.nodes import (
    InputNode,
    OutputNode,
    PipelineNode,
    TransformationNode,
)
from pytransformkit.domain.pipelines.plan import LogicalPlan, LogicalPlanNode
from pytransformkit.domain.pipelines.validation import topological_order
from pytransformkit.domain.plans import (
    TransformationPlan,
    TransformationPlanValidator,
    ordered_predecessors,
)
from pytransformkit.domain.shared.identifiers import NodeId
from pytransformkit.domain.transformations.schema_resolution import (
    OutputSchemaResolver,
)
from pytransformkit.errors.pipeline import InvalidPipelineError


class TransformationCompiler:
    """Validate and normalize a TransformationPlan without executing data."""

    def __init__(
        self,
        schema_resolver: OutputSchemaResolver | None = None,
    ) -> None:
        self._schema_resolver = schema_resolver or OutputSchemaResolver()

    def compile(self, plan: TransformationPlan) -> LogicalPlan:
        if not isinstance(plan, TransformationPlan):
            raise TypeError("TransformationCompiler requires a TransformationPlan.")

        TransformationPlanValidator().validate(
            plan.nodes,
            plan.dependencies,
        )
        ordered_ids = topological_order(
            plan.nodes,
            plan.dependencies,
        )
        node_by_id = {node.id: node for node in plan.nodes}
        output_schema_by_node: dict[NodeId, Schema] = {}
        planned_nodes: list[LogicalPlanNode] = []

        for node_id in ordered_ids:
            node = node_by_id[node_id]
            predecessor_ids = ordered_predecessors(
                node_id,
                plan.dependencies,
            )
            predecessor_schemas = tuple(
                output_schema_by_node[item] for item in predecessor_ids
            )
            planned = self._compile_node(
                node,
                predecessor_ids,
                predecessor_schemas,
            )
            output_schema_by_node[node_id] = planned.output_schema
            planned_nodes.append(planned)

        outputs = tuple(
            (
                node.name,
                output_schema_by_node[node.id],
            )
            for node in plan.output_nodes
        )
        if not outputs:
            raise InvalidPipelineError(
                "TransformationPlan compilation requires an output."
            )

        return LogicalPlan(
            pipeline_id=plan.id,
            pipeline_name=plan.name,
            nodes=tuple(planned_nodes),
            output_schema=outputs[0][1],
            output_schemas=outputs,
        )

    def _compile_node(
        self,
        node: PipelineNode,
        predecessor_ids: tuple[NodeId, ...],
        predecessor_schemas: tuple[Schema, ...],
    ) -> LogicalPlanNode:
        if isinstance(node, InputNode):
            if predecessor_ids:
                raise InvalidPipelineError("Input nodes cannot have predecessors.")
            return LogicalPlanNode(
                node_id=node.id,
                kind=node.kind,
                input_schema=None,
                output_schema=node.schema,
                name=node.name,
            )

        if isinstance(node, TransformationNode):
            output_schema = self._schema_resolver.resolve_many(
                node.transformation,
                predecessor_schemas,
            )
            return LogicalPlanNode(
                node_id=node.id,
                kind=node.kind,
                input_schema=(
                    predecessor_schemas[0] if len(predecessor_schemas) == 1 else None
                ),
                output_schema=output_schema,
                step_id=node.step_id,
                transformation=node.transformation,
                name=node.name,
                input_node_ids=predecessor_ids,
                input_schemas=predecessor_schemas,
            )

        if isinstance(node, OutputNode):
            if len(predecessor_schemas) != 1:
                raise InvalidPipelineError(
                    "Output nodes require exactly one predecessor."
                )
            return LogicalPlanNode(
                node_id=node.id,
                kind=node.kind,
                input_schema=predecessor_schemas[0],
                output_schema=predecessor_schemas[0],
                name=node.name,
                input_node_ids=predecessor_ids,
                input_schemas=predecessor_schemas,
            )

        raise InvalidPipelineError(
            f"Unsupported TransformationPlan node {type(node).__name__!r}."
        )
