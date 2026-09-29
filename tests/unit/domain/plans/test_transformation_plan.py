from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from pytransformkit import TransformationPlan
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.pipelines.nodes import TransformationNode
from pytransformkit.domain.transformations.relational import JoinTransformation


def _customer_schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("email", StringType()),
        )
    )


def _order_schema() -> Schema:
    return Schema(
        fields=(
            Field("order_id", IntegerType(), nullable=False),
            Field("customer_id", IntegerType(), nullable=False),
            Field("amount", IntegerType()),
        )
    )


def test_builder_creates_multi_input_join_plan() -> None:
    builder = TransformationPlan.builder("customer_mart")
    customers = builder.input("customers", schema=_customer_schema())
    orders = builder.input("orders", schema=_order_schema())

    joined = builder.join(
        "customer_orders",
        left=customers,
        right=orders,
        how="left",
        on=(("customer_id", "customer_id"),),
    )
    plan = builder.output("customer_mart", joined).build()

    assert plan.name == "customer_mart"
    assert tuple(node.name for node in plan.input_nodes) == (
        "customers",
        "orders",
    )
    assert tuple(node.name for node in plan.output_nodes) == (
        "customer_mart",
    )

    join_node = next(
        node
        for node in plan.transformation_nodes
        if isinstance(node.transformation, JoinTransformation)
    )
    incoming = sorted(
        (
            edge.input_index,
            edge.source,
        )
        for edge in plan.dependencies
        if edge.target == join_node.id
    )
    assert [index for index, _ in incoming] == [0, 1]


def test_plan_allows_branching_to_multiple_outputs() -> None:
    builder = TransformationPlan.builder("branches")
    source = builder.input("source", schema=_customer_schema())
    only_ids = builder.select(
        "only_ids",
        source=source,
        columns=("customer_id",),
    )
    active = builder.filter(
        "has_email",
        source=source,
        where=__import__("pytransformkit").col("email").is_not_null(),
    )

    plan = (
        builder.output("ids", only_ids)
        .output("with_email", active)
        .build()
    )

    assert tuple(node.name for node in plan.output_nodes) == (
        "ids",
        "with_email",
    )


def test_builder_rejects_dataset_from_another_builder() -> None:
    left = TransformationPlan.builder("left")
    right = TransformationPlan.builder("right")
    external = left.input("source", schema=_customer_schema())
    right.input("right_source", schema=_customer_schema())

    with pytest.raises(Exception, match="does not belong"):
        right.select(
            "invalid",
            source=external,
            columns=("customer_id",),
        )


def test_built_plan_is_immutable() -> None:
    builder = TransformationPlan.builder("immutable")
    source = builder.input("source", schema=_customer_schema())
    plan = builder.output("out", source).build()

    with pytest.raises(FrozenInstanceError):
        plan.name = "changed"  # type: ignore[misc]


def test_root_api_promotes_transformation_plan_not_pipeline() -> None:
    import pytransformkit

    assert pytransformkit.TransformationPlan is TransformationPlan
    assert "TransformationPlan" in pytransformkit.__all__
    assert "Pipeline" not in pytransformkit.__all__


def test_transformation_nodes_can_have_authoring_names() -> None:
    builder = TransformationPlan.builder("named")
    source = builder.input("source", schema=_customer_schema())
    selected = builder.select(
        "customer_ids",
        source=source,
        columns=("customer_id",),
    )
    plan = builder.output("out", selected).build()

    node = next(
        item
        for item in plan.nodes
        if isinstance(item, TransformationNode)
    )
    assert node.name == "customer_ids"
