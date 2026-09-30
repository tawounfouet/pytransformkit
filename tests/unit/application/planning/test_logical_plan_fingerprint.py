from __future__ import annotations

from pytransformkit import TransformationPlan
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.functions import col
from pytransformkit.planning import TransformationCompiler


def _schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("status", StringType(), nullable=False),
        )
    )


def _logical_plan(threshold: int):
    builder = TransformationPlan.builder("active_customers")
    source = builder.input("customers", schema=_schema())
    selected = builder.filter(
        "selected",
        source=source,
        where=col("customer_id") > threshold,
    )
    plan = builder.output("result", selected).build()
    return TransformationCompiler().compile(plan)


def test_logical_plan_fingerprint_ignores_random_plan_and_node_identity() -> None:
    first = _logical_plan(0)
    second = _logical_plan(0)

    assert first.plan_id != second.plan_id
    assert first.fingerprint() == second.fingerprint()


def test_logical_plan_fingerprint_changes_with_semantics() -> None:
    first = _logical_plan(0)
    second = _logical_plan(100)

    assert first.fingerprint() != second.fingerprint()


def test_logical_plan_fingerprint_is_sha256() -> None:
    fingerprint = _logical_plan(0).fingerprint()

    assert fingerprint.algorithm == "sha256"
    assert len(fingerprint.value) == 64
