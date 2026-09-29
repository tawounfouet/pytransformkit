from __future__ import annotations

import pytest

from pytransformkit import TransformationPlan
from pytransformkit.domain.data.data_types import (
    FloatType,
    IntegerType,
    StringType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.expressions.aggregate import AggregateExpression
from pytransformkit.domain.transformations.aggregation import (
    AggregateMetric,
    AggregateTransformation,
)
from pytransformkit.domain.transformations.properties import (
    CardinalityEffect,
    SchemaEffect,
)
from pytransformkit.domain.transformations.schema_resolution import (
    OutputSchemaResolver,
)
from pytransformkit.errors.expression import ExpressionTypeError
from pytransformkit.errors.schema import FieldCollisionError
from pytransformkit.errors.transformation import InvalidTransformationError
from pytransformkit.functions import (
    col,
    count,
    count_distinct,
    lower,
    max,
    mean,
    min,
    sum,
)


@pytest.fixture
def schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("country", StringType(), nullable=True),
            Field("status", StringType(), nullable=False),
            Field("amount", FloatType(), nullable=True),
        )
    )


def test_aggregate_transformation_has_stable_semantic_properties() -> None:
    transformation = AggregateTransformation.from_mapping(
        group_by=(col("customer_id"),),
        metrics={"row_count": count()},
    )

    assert transformation.identifier == "core.aggregate"
    assert transformation.properties.cardinality is CardinalityEffect.REDUCE
    assert transformation.properties.schema is SchemaEffect.MODIFY


def test_aggregate_requires_at_least_one_metric() -> None:
    with pytest.raises(InvalidTransformationError, match="at least one metric"):
        AggregateTransformation(
            group_by=(col("customer_id"),),
            metrics=(),
        )


def test_aggregate_metric_requires_aggregate_expression() -> None:
    with pytest.raises(TypeError, match="AggregateExpression"):
        AggregateMetric(
            "invalid",
            col("amount"),  # type: ignore[arg-type]
        )


def test_grouped_schema_is_deterministic(schema: Schema) -> None:
    transformation = AggregateTransformation.from_mapping(
        group_by=(
            col("customer_id"),
            lower(col("country")),
        ),
        metrics={
            "row_count": count(),
            "non_null_amount_count": count(col("amount")),
            "distinct_status_count": count_distinct(col("status")),
            "total_amount": sum(col("amount")),
            "min_amount": min(col("amount")),
            "max_amount": max(col("amount")),
            "mean_amount": mean(col("amount")),
        },
    )

    output = OutputSchemaResolver().resolve(
        transformation,
        schema,
    )

    assert output.names() == (
        "customer_id",
        "group_1",
        "row_count",
        "non_null_amount_count",
        "distinct_status_count",
        "total_amount",
        "min_amount",
        "max_amount",
        "mean_amount",
    )
    assert output.field("customer_id").data_type == IntegerType()
    assert output.field("group_1").data_type == StringType()
    assert output.field("row_count").data_type == IntegerType(bits=64)
    assert output.field("row_count").nullable is False
    assert output.field("total_amount").data_type == FloatType(bits=64)
    assert output.field("total_amount").nullable is True
    assert output.field("mean_amount").data_type == FloatType(bits=64)


def test_metric_name_cannot_collide_with_group_output(schema: Schema) -> None:
    transformation = AggregateTransformation.from_mapping(
        group_by=(col("customer_id"),),
        metrics={
            "customer_id": count(),
        },
    )

    with pytest.raises(FieldCollisionError, match="customer_id"):
        OutputSchemaResolver().resolve(
            transformation,
            schema,
        )


def test_group_by_rejects_aggregate_context(schema: Schema) -> None:
    transformation = AggregateTransformation.from_mapping(
        group_by=(sum(col("amount")),),
        metrics={"row_count": count()},
    )

    with pytest.raises(ExpressionTypeError, match="only valid"):
        OutputSchemaResolver().resolve(
            transformation,
            schema,
        )


def test_metric_rejects_nested_aggregate(schema: Schema) -> None:
    nested = sum(count(col("amount")))
    assert isinstance(nested, AggregateExpression)

    transformation = AggregateTransformation.from_mapping(
        group_by=(),
        metrics={"invalid": nested},
    )

    with pytest.raises(ExpressionTypeError, match="only valid"):
        OutputSchemaResolver().resolve(
            transformation,
            schema,
        )


def test_builder_adds_aggregate_to_transformation_plan(schema: Schema) -> None:
    builder = TransformationPlan.builder("order_stats")
    orders = builder.input("orders", schema=schema)

    stats = builder.aggregate(
        "stats",
        source=orders,
        group_by=(col("customer_id"),),
        metrics={
            "order_count": count(),
            "revenue": sum(col("amount")),
        },
    )
    plan = builder.output("order_stats", stats).build()

    assert stats.schema.names() == (
        "customer_id",
        "order_count",
        "revenue",
    )
    assert isinstance(
        plan.transformation_nodes[0].transformation,
        AggregateTransformation,
    )
