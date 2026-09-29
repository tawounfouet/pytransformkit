from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from pytransformkit import TransformationPlan, window
from pytransformkit.application.execution import EngineCapabilityAnalyzer
from pytransformkit.domain.data.data_types import (
    FloatType,
    IntegerType,
    StringType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.engines import EngineCapability
from pytransformkit.domain.expressions.dependencies import (
    ExpressionDependencyExtractor,
)
from pytransformkit.domain.expressions.fingerprint import canonical_expression
from pytransformkit.domain.expressions.typing import WindowExpressionTypeResolver
from pytransformkit.domain.expressions.window import (
    WindowDeterminism,
    WindowFrameKind,
)
from pytransformkit.errors.expression import ExpressionTypeError
from pytransformkit.functions import col
from pytransformkit.planning import TransformationCompiler


@pytest.fixture
def schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("ordered_at", IntegerType(), nullable=False),
            Field("status", StringType(), nullable=False),
            Field("amount", FloatType(), nullable=True),
        )
    )


def test_window_spec_is_immutable() -> None:
    spec = window.partition_by("customer_id").order_by("ordered_at")

    with pytest.raises(FrozenInstanceError):
        spec.frame = None  # type: ignore[misc]


def test_row_number_requires_explicit_ordering(schema: Schema) -> None:
    expression = window.row_number().over(
        window.partition_by("customer_id")
    )

    with pytest.raises(ExpressionTypeError, match="order_by"):
        WindowExpressionTypeResolver().resolve(expression, schema)


def test_row_number_has_non_nullable_int64_type(schema: Schema) -> None:
    expression = window.row_number().over(
        window.partition_by("customer_id").order_by("ordered_at")
    )

    resolved = WindowExpressionTypeResolver().resolve(expression, schema)

    assert resolved.data_type == IntegerType(bits=64)
    assert resolved.nullable is False
    assert expression.determinism is WindowDeterminism.ORDER_DEPENDENT


def test_rank_is_value_ordered(schema: Schema) -> None:
    expression = window.rank().over(
        window.partition_by("customer_id").order_by("ordered_at")
    )

    WindowExpressionTypeResolver().resolve(expression, schema)

    assert expression.determinism is WindowDeterminism.VALUE_ORDERED


def test_lag_preserves_argument_type_and_becomes_nullable(schema: Schema) -> None:
    expression = window.lag(col("status")).over(
        window.partition_by("customer_id").order_by("ordered_at")
    )

    resolved = WindowExpressionTypeResolver().resolve(expression, schema)

    assert resolved.data_type == StringType()
    assert resolved.nullable is True


def test_lag_rejects_incompatible_default(schema: Schema) -> None:
    expression = window.lag(
        col("status"),
        default=0,
    ).over(
        window.partition_by("customer_id").order_by("ordered_at")
    )

    with pytest.raises(ExpressionTypeError, match="same logical DataType"):
        WindowExpressionTypeResolver().resolve(expression, schema)


def test_cumulative_and_moving_frames_are_classified() -> None:
    cumulative = (
        window.partition_by("customer_id")
        .order_by("ordered_at")
        .rows_between(
            window.unbounded_preceding(),
            window.current_row(),
        )
    )
    moving = (
        window.partition_by("customer_id")
        .order_by("ordered_at")
        .rows_between(
            window.preceding(2),
            window.current_row(),
        )
    )

    assert window.sum(col("amount")).over(cumulative).frame_kind is (
        WindowFrameKind.ROWS_CUMULATIVE
    )
    assert window.mean(col("amount")).over(moving).frame_kind is (
        WindowFrameKind.ROWS_MOVING
    )


def test_arbitrary_and_range_frames_remain_explicit_capability_shapes() -> None:
    arbitrary = (
        window.partition_by("customer_id")
        .order_by("ordered_at")
        .rows_between(
            window.current_row(),
            window.following(1),
        )
    )
    ranged = (
        window.partition_by("customer_id")
        .order_by("ordered_at")
        .range_between(
            window.unbounded_preceding(),
            window.current_row(),
        )
    )

    assert window.sum(col("amount")).over(arbitrary).frame_kind is (
        WindowFrameKind.ROWS_ARBITRARY
    )
    assert window.sum(col("amount")).over(ranged).frame_kind is (
        WindowFrameKind.RANGE
    )


def test_window_dependencies_include_value_partition_order_and_default() -> None:
    expression = window.lag(
        col("amount"),
        default=col("customer_id"),
    ).over(
        window.partition_by("status").order_by("ordered_at")
    )

    dependencies = ExpressionDependencyExtractor().extract(expression)

    assert {str(path) for path in dependencies} == {
        "amount",
        "customer_id",
        "status",
        "ordered_at",
    }


def test_window_fingerprint_includes_specification() -> None:
    first = window.row_number().over(
        window.partition_by("customer_id").order_by("ordered_at")
    )
    second = window.row_number().over(
        window.partition_by("status").order_by("ordered_at")
    )

    assert canonical_expression(first) != canonical_expression(second)


def test_builder_derives_window_field_and_compiler_requires_window_capability(
    schema: Schema,
) -> None:
    builder = TransformationPlan.builder("ranked_orders")
    orders = builder.input("orders", schema=schema)
    ranked = builder.derive(
        "ranked",
        source=orders,
        field_name="order_number",
        expression=window.row_number().over(
            window.partition_by("customer_id").order_by("ordered_at")
        ),
    )
    plan = builder.output("ranked_orders", ranked).build()

    logical_plan = TransformationCompiler().compile(plan)
    required = EngineCapabilityAnalyzer().required_capabilities(logical_plan)

    assert ranked.schema.field("order_number").data_type == IntegerType(bits=64)
    assert required == frozenset(
        {
            EngineCapability.DERIVE,
            EngineCapability.WINDOW,
        }
    )


@pytest.mark.parametrize(
    ("spec", "capability"),
    [
        (
            window.order_by("ordered_at").rows_between(
                window.unbounded_preceding(),
                window.current_row(),
            ),
            EngineCapability.WINDOW_ROWS_CUMULATIVE,
        ),
        (
            window.order_by("ordered_at").rows_between(
                window.preceding(2),
                window.current_row(),
            ),
            EngineCapability.WINDOW_ROWS_MOVING,
        ),
        (
            window.order_by("ordered_at").rows_between(
                window.current_row(),
                window.following(1),
            ),
            EngineCapability.WINDOW_ROWS_ARBITRARY,
        ),
        (
            window.order_by("ordered_at").range_between(
                window.unbounded_preceding(),
                window.current_row(),
            ),
            EngineCapability.WINDOW_RANGE,
        ),
    ],
)
def test_window_frame_capability_is_derived(
    schema: Schema,
    spec: object,
    capability: EngineCapability,
) -> None:
    builder = TransformationPlan.builder("window_capability")
    orders = builder.input("orders", schema=schema)
    derived = builder.derive(
        "windowed",
        source=orders,
        field_name="metric",
        expression=window.sum(col("amount")).over(spec),  # type: ignore[arg-type]
    )
    plan = builder.output("result", derived).build()

    required = EngineCapabilityAnalyzer().required_capabilities(
        TransformationCompiler().compile(plan)
    )

    assert EngineCapability.DERIVE in required
    assert EngineCapability.WINDOW in required
    assert capability in required
