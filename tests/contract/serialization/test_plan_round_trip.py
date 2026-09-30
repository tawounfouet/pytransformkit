from __future__ import annotations

from pytransformkit import TransformationPlan
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.lineage import LineageAnalyzer
from pytransformkit.functions import col
from pytransformkit.planning import TransformationCompiler
from pytransformkit.serialization import (
    LineageCodec,
    LogicalPlanCodec,
    TransformationPlanCodec,
)


def _customers() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("status", StringType(), nullable=False),
        )
    )


def _orders() -> Schema:
    return Schema(
        fields=(
            Field("order_id", IntegerType(), nullable=False),
            Field("customer_id", IntegerType(), nullable=False),
            Field("amount", IntegerType(), nullable=False),
        )
    )


def _plan(threshold: int = 10) -> TransformationPlan:
    builder = TransformationPlan.builder("customer_orders")
    customers = builder.input("customers", schema=_customers())
    orders = builder.input("orders", schema=_orders())
    paid = builder.filter(
        "large_orders",
        source=orders,
        where=col("amount") > threshold,
    )
    joined = builder.join(
        "joined",
        left=customers,
        right=paid,
        how="left",
        on=(("customer_id", "customer_id"),),
    )
    return builder.output("result", joined).build()


def test_transformation_plan_round_trip_is_canonical_and_identity_preserving() -> None:
    plan = _plan()
    codec = TransformationPlanCodec()

    encoded = codec.to_json(plan)
    decoded = codec.from_json(encoded)

    assert decoded.id == plan.id
    assert decoded.name == plan.name
    assert codec.to_json(decoded) == encoded
    assert codec.fingerprint(decoded) == codec.fingerprint(plan)


def test_plan_semantic_fingerprint_ignores_random_graph_identity() -> None:
    first = _plan()
    second = _plan()

    assert first.id != second.id
    assert TransformationPlanCodec().to_json(first) != (
        TransformationPlanCodec().to_json(second)
    )
    assert TransformationPlanCodec().fingerprint(first) == (
        TransformationPlanCodec().fingerprint(second)
    )


def test_plan_semantic_fingerprint_changes_with_transformation_semantics() -> None:
    assert TransformationPlanCodec().fingerprint(_plan(10)) != (
        TransformationPlanCodec().fingerprint(_plan(100))
    )


def test_logical_plan_round_trip_preserves_compiled_graph_and_fingerprint() -> None:
    logical = TransformationCompiler().compile(_plan())
    codec = LogicalPlanCodec()

    encoded = codec.to_json(logical)
    decoded = codec.from_json(encoded)

    assert decoded.plan_id == logical.plan_id
    assert decoded.input_names == logical.input_names
    assert decoded.output_names == logical.output_names
    assert codec.to_json(decoded) == encoded
    assert codec.fingerprint(decoded) == logical.fingerprint()


def test_lineage_round_trip_preserves_graph_evidence() -> None:
    logical = TransformationCompiler().compile(_plan())
    lineage = LineageAnalyzer().analyze(logical)
    codec = LineageCodec()

    encoded = codec.to_json(lineage)
    decoded = codec.from_json(encoded)

    assert codec.to_json(decoded) == encoded
    assert decoded.plan_id == lineage.plan_id
    assert len(decoded.dataset_edges) == len(lineage.dataset_edges)
    assert len(decoded.field_edges) == len(lineage.field_edges)
    assert len(decoded.dependencies) == len(lineage.dependencies)
