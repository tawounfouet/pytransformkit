from __future__ import annotations

import pytest

from pytransformkit.domain.data.data_types import StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.pipelines.dependencies import Dependency
from pytransformkit.domain.pipelines.nodes import (
    InputNode,
    OutputNode,
    TransformationNode,
)
from pytransformkit.domain.pipelines.validation import (
    PipelineGraphValidator,
    topological_order,
)
from pytransformkit.domain.shared.identifiers import NodeId
from pytransformkit.domain.transformations.filtering import FilterTransformation
from pytransformkit.errors.pipeline import (
    InvalidPipelineError,
    PipelineCycleError,
    PipelineNodeNotFoundError,
)
from pytransformkit.functions import col


def _schema() -> Schema:
    return Schema(fields=(Field("email", StringType()),))


def _filter_node() -> TransformationNode:
    return TransformationNode.create(
        FilterTransformation(condition=col("email").is_not_null())
    )


def test_graph_validator_accepts_linear_dag() -> None:
    input_node = InputNode.create("input", _schema())
    transformation = _filter_node()
    output_node = OutputNode.create("output")
    nodes = (input_node, transformation, output_node)
    dependencies = (
        Dependency(input_node.id, transformation.id),
        Dependency(transformation.id, output_node.id),
    )

    PipelineGraphValidator().validate(nodes, dependencies)


def test_graph_validator_rejects_duplicate_node_ids() -> None:
    input_node = InputNode.create("input", _schema())
    duplicate_input = InputNode(
        id=input_node.id,
        kind=input_node.kind,
        name="other",
        schema=_schema(),
    )
    output_node = OutputNode.create("output")

    with pytest.raises(InvalidPipelineError, match="ids"):
        PipelineGraphValidator().validate(
            (input_node, duplicate_input, output_node),
            (),
        )


def test_graph_validator_rejects_unknown_dependency_node() -> None:
    input_node = InputNode.create("input", _schema())
    output_node = OutputNode.create("output")

    with pytest.raises(PipelineNodeNotFoundError):
        PipelineGraphValidator().validate(
            (input_node, output_node),
            (
                Dependency(
                    source=input_node.id,
                    target=NodeId.new(),
                ),
            ),
        )


def test_topological_order_detects_cycle() -> None:
    input_node = InputNode.create("input", _schema())
    transformation = _filter_node()

    with pytest.raises(PipelineCycleError):
        topological_order(
            (input_node, transformation),
            (
                Dependency(input_node.id, transformation.id),
                Dependency(transformation.id, input_node.id),
            ),
        )


def test_topological_order_preserves_linear_dependency_order() -> None:
    input_node = InputNode.create("input", _schema())
    first = _filter_node()
    second = _filter_node()
    output_node = OutputNode.create("output")
    nodes = (input_node, first, second, output_node)
    dependencies = (
        Dependency(input_node.id, first.id),
        Dependency(first.id, second.id),
        Dependency(second.id, output_node.id),
    )

    assert topological_order(nodes, dependencies) == (
        input_node.id,
        first.id,
        second.id,
        output_node.id,
    )


def test_graph_validator_rejects_branching_in_initial_mvp() -> None:
    input_node = InputNode.create("input", _schema())
    first = _filter_node()
    second = _filter_node()
    output_node = OutputNode.create("output")

    with pytest.raises(InvalidPipelineError, match="outgoing"):
        PipelineGraphValidator().validate(
            (input_node, first, second, output_node),
            (
                Dependency(input_node.id, first.id),
                Dependency(input_node.id, second.id),
                Dependency(first.id, output_node.id),
            ),
        )
