"""Structural validation for TransformationPlan DAGs."""

from __future__ import annotations

from collections import defaultdict

from pytransformkit.domain.pipelines.dependencies import Dependency
from pytransformkit.domain.pipelines.nodes import (
    InputNode,
    OutputNode,
    PipelineNode,
    TransformationNode,
)
from pytransformkit.domain.pipelines.validation import topological_order
from pytransformkit.domain.shared.identifiers import NodeId
from pytransformkit.domain.transformations.relational import relational_input_count
from pytransformkit.errors.pipeline import (
    InvalidPipelineError,
    PipelineNodeNotFoundError,
)


class TransformationPlanValidator:
    """Validate a multi-input/multi-output transformation DAG."""

    def validate(
        self,
        nodes: tuple[PipelineNode, ...],
        dependencies: tuple[Dependency, ...],
    ) -> None:
        node_by_id = {node.id: node for node in nodes}
        if not nodes:
            raise InvalidPipelineError("TransformationPlan must contain nodes.")
        if len(node_by_id) != len(nodes):
            raise InvalidPipelineError("TransformationPlan node ids must be unique.")

        inputs = tuple(node for node in nodes if isinstance(node, InputNode))
        outputs = tuple(node for node in nodes if isinstance(node, OutputNode))
        if not inputs:
            raise InvalidPipelineError(
                "TransformationPlan requires at least one input."
            )
        if not outputs:
            raise InvalidPipelineError(
                "TransformationPlan requires at least one output."
            )

        _validate_unique_names(inputs, "input")
        _validate_unique_names(outputs, "output")

        incoming: dict[NodeId, list[Dependency]] = defaultdict(list)
        outgoing: dict[NodeId, list[Dependency]] = defaultdict(list)
        seen_edges: set[tuple[NodeId, NodeId, int]] = set()

        for dependency in dependencies:
            if dependency.source not in node_by_id:
                raise PipelineNodeNotFoundError(str(dependency.source))
            if dependency.target not in node_by_id:
                raise PipelineNodeNotFoundError(str(dependency.target))

            edge = (
                dependency.source,
                dependency.target,
                dependency.input_index,
            )
            if edge in seen_edges:
                raise InvalidPipelineError(
                    "Duplicate TransformationPlan dependencies are not allowed."
                )
            seen_edges.add(edge)
            incoming[dependency.target].append(dependency)
            outgoing[dependency.source].append(dependency)

        for node in nodes:
            node_incoming = incoming[node.id]
            node_outgoing = outgoing[node.id]

            if isinstance(node, InputNode):
                if node_incoming:
                    raise InvalidPipelineError(
                        "TransformationPlan input nodes cannot have predecessors."
                    )
                if not node_outgoing:
                    raise InvalidPipelineError(
                        f"TransformationPlan input {node.name!r} is unused."
                    )
                continue

            if isinstance(node, OutputNode):
                if len(node_incoming) != 1:
                    raise InvalidPipelineError(
                        f"Output {node.name!r} requires exactly one predecessor."
                    )
                if node_incoming[0].input_index != 0:
                    raise InvalidPipelineError(
                        f"Output {node.name!r} predecessor must use input_index 0."
                    )
                if node_outgoing:
                    raise InvalidPipelineError(
                        "TransformationPlan output nodes cannot have successors."
                    )
                continue

            if isinstance(node, TransformationNode):
                required = relational_input_count(node.transformation)
                if len(node_incoming) != required:
                    raise InvalidPipelineError(
                        f"Transformation {node.name or node.step_id!s} requires "
                        f"{required} input(s), got {len(node_incoming)}."
                    )
                indexes = sorted(edge.input_index for edge in node_incoming)
                if indexes != list(range(required)):
                    raise InvalidPipelineError(
                        "Transformation input_index values must be contiguous "
                        "starting at zero."
                    )
                if not node_outgoing:
                    raise InvalidPipelineError(
                        "Every TransformationPlan transformation must contribute "
                        "to at least one output."
                    )
                continue

            raise InvalidPipelineError(
                f"Unsupported logical node {type(node).__name__!r}."
            )

        topological_order(nodes, dependencies)
        _validate_reachability(
            nodes,
            dependencies,
            input_ids={node.id for node in inputs},
            output_ids={node.id for node in outputs},
        )


def ordered_predecessors(
    node_id: NodeId,
    dependencies: tuple[Dependency, ...],
) -> tuple[NodeId, ...]:
    """Return predecessor node ids ordered by target input_index."""
    relevant = [edge for edge in dependencies if edge.target == node_id]
    relevant.sort(key=lambda edge: edge.input_index)
    return tuple(edge.source for edge in relevant)


def _validate_unique_names(
    nodes: tuple[InputNode, ...] | tuple[OutputNode, ...],
    kind: str,
) -> None:
    names = tuple(node.name for node in nodes)
    if len(names) != len(set(names)):
        raise InvalidPipelineError(
            f"TransformationPlan {kind} names must be unique."
        )


def _validate_reachability(
    nodes: tuple[PipelineNode, ...],
    dependencies: tuple[Dependency, ...],
    *,
    input_ids: set[NodeId],
    output_ids: set[NodeId],
) -> None:
    targets: dict[NodeId, list[NodeId]] = defaultdict(list)
    sources: dict[NodeId, list[NodeId]] = defaultdict(list)
    for edge in dependencies:
        targets[edge.source].append(edge.target)
        sources[edge.target].append(edge.source)

    reachable_from_inputs = _walk(input_ids, targets)
    if reachable_from_inputs != {node.id for node in nodes}:
        raise InvalidPipelineError(
            "Every TransformationPlan node must be reachable from an input."
        )

    reaches_output = _walk(output_ids, sources)
    if reaches_output != {node.id for node in nodes}:
        raise InvalidPipelineError(
            "Every TransformationPlan node must contribute to an output."
        )


def _walk(
    starts: set[NodeId],
    edges: dict[NodeId, list[NodeId]],
) -> set[NodeId]:
    seen: set[NodeId] = set()
    stack = list(starts)
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(edges[current])
    return seen
