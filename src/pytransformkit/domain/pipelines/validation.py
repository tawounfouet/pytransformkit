"""Structural validation and topological ordering for Pipeline DAGs."""

from collections import defaultdict, deque

from pytransformkit.domain.pipelines.dependencies import Dependency
from pytransformkit.domain.pipelines.nodes import (
    InputNode,
    OutputNode,
    PipelineNode,
    TransformationNode,
)
from pytransformkit.domain.shared.identifiers import NodeId
from pytransformkit.errors.pipeline import (
    InvalidPipelineError,
    PipelineCycleError,
    PipelineNodeNotFoundError,
)


class PipelineGraphValidator:
    """Validate the current single-input/single-output Pipeline graph."""

    def validate(
        self,
        nodes: tuple[PipelineNode, ...],
        dependencies: tuple[Dependency, ...],
    ) -> None:
        node_by_id = _node_index(nodes)

        if len(node_by_id) != len(nodes):
            raise InvalidPipelineError("Pipeline node ids must be unique.")

        inputs = tuple(node for node in nodes if isinstance(node, InputNode))
        outputs = tuple(node for node in nodes if isinstance(node, OutputNode))

        if len(inputs) != 1:
            raise InvalidPipelineError(
                "The initial Pipeline MVP requires exactly one input node."
            )
        if len(outputs) != 1:
            raise InvalidPipelineError(
                "The initial Pipeline MVP requires exactly one output node."
            )

        seen_edges: set[tuple[NodeId, NodeId]] = set()
        incoming: dict[NodeId, int] = defaultdict(int)
        outgoing: dict[NodeId, int] = defaultdict(int)

        for dependency in dependencies:
            if dependency.source not in node_by_id:
                raise PipelineNodeNotFoundError(str(dependency.source))
            if dependency.target not in node_by_id:
                raise PipelineNodeNotFoundError(str(dependency.target))

            edge = (dependency.source, dependency.target)
            if edge in seen_edges:
                raise InvalidPipelineError(
                    "Duplicate Pipeline dependencies are not allowed."
                )
            seen_edges.add(edge)
            outgoing[dependency.source] += 1
            incoming[dependency.target] += 1

        input_node = inputs[0]
        output_node = outputs[0]

        if incoming[input_node.id] != 0:
            raise InvalidPipelineError(
                "The Pipeline input node cannot have incoming dependencies."
            )
        if outgoing[output_node.id] != 0:
            raise InvalidPipelineError(
                "The Pipeline output node cannot have outgoing dependencies."
            )

        for node in nodes:
            if isinstance(node, InputNode):
                continue
            if incoming[node.id] != 1:
                raise InvalidPipelineError(
                    "The initial Pipeline MVP requires exactly one incoming "
                    f"dependency for node {node.id}."
                )

        for node in nodes:
            if isinstance(node, OutputNode):
                continue
            if outgoing[node.id] != 1:
                raise InvalidPipelineError(
                    "The initial Pipeline MVP requires exactly one outgoing "
                    f"dependency for node {node.id}."
                )

        topological_order(nodes, dependencies)

        reachable = _reachable_from(input_node.id, dependencies)
        if set(node_by_id) != reachable:
            raise InvalidPipelineError(
                "Every Pipeline node must be reachable from the input node."
            )


def topological_order(
    nodes: tuple[PipelineNode, ...],
    dependencies: tuple[Dependency, ...],
) -> tuple[NodeId, ...]:
    """Return a deterministic topological ordering or raise on a cycle."""
    node_by_id = _node_index(nodes)
    indegree: dict[NodeId, int] = {node_id: 0 for node_id in node_by_id}
    targets: dict[NodeId, list[NodeId]] = defaultdict(list)

    for dependency in dependencies:
        if dependency.source not in node_by_id:
            raise PipelineNodeNotFoundError(str(dependency.source))
        if dependency.target not in node_by_id:
            raise PipelineNodeNotFoundError(str(dependency.target))
        indegree[dependency.target] += 1
        targets[dependency.source].append(dependency.target)

    node_position = {
        node.id: position
        for position, node in enumerate(nodes)
    }
    ready = deque(
        sorted(
            (
                node_id
                for node_id, degree in indegree.items()
                if degree == 0
            ),
            key=node_position.__getitem__,
        )
    )
    ordered: list[NodeId] = []

    while ready:
        node_id = ready.popleft()
        ordered.append(node_id)

        for target in sorted(
            targets[node_id],
            key=node_position.__getitem__,
        ):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)

    if len(ordered) != len(nodes):
        raise PipelineCycleError(
            "Pipeline dependencies must form an acyclic graph."
        )

    return tuple(ordered)


def _node_index(
    nodes: tuple[PipelineNode, ...],
) -> dict[NodeId, PipelineNode]:
    return {node.id: node for node in nodes}


def _reachable_from(
    start: NodeId,
    dependencies: tuple[Dependency, ...],
) -> set[NodeId]:
    targets: dict[NodeId, list[NodeId]] = defaultdict(list)
    for dependency in dependencies:
        targets[dependency.source].append(dependency.target)

    reachable: set[NodeId] = set()
    stack = [start]

    while stack:
        node_id = stack.pop()
        if node_id in reachable:
            continue
        reachable.add(node_id)
        stack.extend(targets[node_id])

    return reachable
