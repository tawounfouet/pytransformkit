from __future__ import annotations

from pytransformkit import TransformationPlan
from pytransformkit.application.planning import TransformationCompiler
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.pipelines.nodes import PipelineNodeKind
from pytransformkit.domain.transformations.relational import JoinTransformation


def _customers() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("email", StringType()),
        )
    )


def _orders() -> Schema:
    return Schema(
        fields=(
            Field("order_id", IntegerType(), nullable=False),
            Field("customer_id", IntegerType(), nullable=False),
            Field("amount", IntegerType()),
        )
    )


def _plan() -> TransformationPlan:
    builder = TransformationPlan.builder("customer_mart")
    customers = builder.input("customers", schema=_customers())
    orders = builder.input("orders", schema=_orders())
    joined = builder.join(
        "joined",
        left=customers,
        right=orders,
        how="left",
        on=(("customer_id", "customer_id"),),
    )
    return builder.output("customer_mart", joined).build()


def test_compiler_preserves_named_inputs_and_outputs() -> None:
    logical = TransformationCompiler().compile(_plan())

    assert logical.input_names == ("customers", "orders")
    assert logical.output_names == ("customer_mart",)
    assert logical.plan_name == "customer_mart"


def test_compiler_orders_relational_inputs_by_input_index() -> None:
    logical = TransformationCompiler().compile(_plan())
    join_node = next(
        node
        for node in logical.nodes
        if isinstance(node.transformation, JoinTransformation)
    )

    assert len(join_node.input_node_ids) == 2
    assert join_node.input_schemas == (
        _customers(),
        _orders(),
    )


def test_compiler_resolves_join_output_schema() -> None:
    logical = TransformationCompiler().compile(_plan())

    assert logical.output_schema.names() == (
        "customer_id",
        "email",
        "order_id",
        "amount",
    )
    assert logical.schema_for_output("customer_mart") == logical.output_schema


def test_compiler_is_deterministic_for_one_immutable_plan() -> None:
    plan = _plan()
    compiler = TransformationCompiler()

    first = compiler.compile(plan)
    second = compiler.compile(plan)

    assert first == second
    assert tuple(node.kind for node in first.nodes) == (
        PipelineNodeKind.INPUT,
        PipelineNodeKind.INPUT,
        PipelineNodeKind.TRANSFORMATION,
        PipelineNodeKind.OUTPUT,
    )
