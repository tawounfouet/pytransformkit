from __future__ import annotations

import pytest

from pytransformkit.domain.data.data_types import (
    FloatType,
    IntegerType,
    StringType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.pipelines.nodes import PipelineNodeKind
from pytransformkit.domain.pipelines.pipeline import Pipeline
from pytransformkit.domain.pipelines.planner import PipelinePlanner
from pytransformkit.errors.expression import ExpressionTypeError
from pytransformkit.functions import col, lower


def _schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("email", StringType(), nullable=True),
            Field("status", StringType(), nullable=False),
            Field("amount", FloatType(), nullable=True),
        )
    )


def test_planner_propagates_schema_through_pipeline() -> None:
    pipeline = (
        Pipeline.create("customers", _schema())
        .select("customer_id", "email", "amount")
        .filter(col("customer_id").is_not_null())
        .derive(
            "normalized_email",
            lower(col("email")),
        )
        .drop("email")
    )

    plan = PipelinePlanner().plan(pipeline)

    assert plan.output_schema.names() == (
        "customer_id",
        "amount",
        "normalized_email",
    )
    assert plan.output_schema.field(
        "normalized_email"
    ).data_type == StringType()
    assert plan.output_schema.field(
        "normalized_email"
    ).nullable is True


def test_logical_plan_preserves_node_order_and_step_identity() -> None:
    pipeline = (
        Pipeline.create("customers", _schema())
        .filter(col("customer_id") > 0)
        .limit(10)
    )

    plan = PipelinePlanner().plan(pipeline)

    assert tuple(node.kind for node in plan.nodes) == (
        PipelineNodeKind.INPUT,
        PipelineNodeKind.TRANSFORMATION,
        PipelineNodeKind.TRANSFORMATION,
        PipelineNodeKind.OUTPUT,
    )

    planned_steps = tuple(
        node.step_id
        for node in plan.nodes
        if node.kind is PipelineNodeKind.TRANSFORMATION
    )
    pipeline_steps = tuple(
        node.step_id
        for node in pipeline.transformation_nodes
    )

    assert planned_steps == pipeline_steps


def test_output_node_preserves_final_schema() -> None:
    pipeline = Pipeline.create("customers", _schema()).select(
        "customer_id",
        "status",
    )

    plan = PipelinePlanner().plan(pipeline)
    output_node = plan.nodes[-1]

    assert output_node.kind is PipelineNodeKind.OUTPUT
    assert output_node.input_schema == plan.output_schema
    assert output_node.output_schema == plan.output_schema


def test_input_plan_node_has_no_input_schema() -> None:
    plan = PipelinePlanner().plan(
        Pipeline.create("customers", _schema())
    )

    assert plan.nodes[0].kind is PipelineNodeKind.INPUT
    assert plan.nodes[0].input_schema is None
    assert plan.nodes[0].output_schema == _schema()


def test_planner_rejects_non_boolean_filter() -> None:
    pipeline = Pipeline.create("customers", _schema()).filter(
        col("email")
    )

    with pytest.raises(ExpressionTypeError, match="BooleanType"):
        PipelinePlanner().plan(pipeline)


def test_original_pipeline_is_unchanged_after_composition() -> None:
    original = Pipeline.create("customers", _schema())
    transformed = original.select("customer_id")

    original_plan = PipelinePlanner().plan(original)
    transformed_plan = PipelinePlanner().plan(transformed)

    assert original_plan.output_schema.names() == _schema().names()
    assert transformed_plan.output_schema.names() == ("customer_id",)
