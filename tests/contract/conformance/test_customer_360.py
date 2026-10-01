# ruff: noqa: E402

from __future__ import annotations

import math
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
pl = pytest.importorskip("polars")
pytest.importorskip("pyarrow")

from pytransformkit import (
    EngineRegistry,
    InputBinding,
    OutputBinding,
    TransformationPlan,
    TransformationRuntime,
    quality,
)
from pytransformkit import functions as fn
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.adapters.polars import PolarsEngineAdapter
from pytransformkit.application.io import ResourceIORegistry
from pytransformkit.domain.data.data_types import FloatType, IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.lineage import FieldReference, LineageImpactAnalyzer
from pytransformkit.domain.resources import ResourceReference, RetrySafety, WriteMode
from pytransformkit.domain.runtime import ExecutionStatus
from pytransformkit.functions import col, lower, trim
from pytransformkit.planning import TransformationCompiler
from pytransformkit.runtime import ExecutionMode, WriteStatus
from pytransformkit.serialization import TransformationPlanCodec
from pytransformkit.writers import LocalFileWriter


def _customers_schema() -> Schema:
    return Schema(
        (
            Field("customer_id", IntegerType(), nullable=False),
            Field("customer_name", StringType(), nullable=False),
            Field("country", StringType(), nullable=False),
            Field("email", StringType(), nullable=True),
        )
    )


def _orders_schema() -> Schema:
    return Schema(
        (
            Field("order_id", IntegerType(), nullable=False),
            Field("customer_id", IntegerType(), nullable=False),
            Field("amount", FloatType(), nullable=False),
            Field("status", StringType(), nullable=False),
        )
    )


def _customer_360_plan() -> TransformationPlan:
    builder = TransformationPlan.builder("customer_360")
    customers = builder.input("customers", schema=_customers_schema())
    orders = builder.input("orders", schema=_orders_schema())

    paid = builder.filter(
        "paid_orders",
        source=orders,
        where=col("status") == "PAID",
    )
    stats = builder.aggregate(
        "paid_order_stats",
        source=paid,
        group_by=(col("customer_id"),),
        metrics={
            "paid_order_count": fn.count(col("order_id")),
            "paid_revenue": fn.sum(col("amount")),
        },
    )
    joined = builder.join(
        "customer_stats",
        left=customers,
        right=stats,
        how="left",
        on=(("customer_id", "customer_id"),),
    )
    normalized = builder.derive(
        "normalized_email",
        source=joined,
        field_name="normalized_email",
        expression=lower(trim(col("email"))),
    )
    validated = builder.validate(
        "customer360_quality",
        source=normalized,
        spec=quality.ValidationSpec(
            name="customer360_quality",
            rules=(
                quality.not_null("customer_id"),
                quality.unique("customer_id"),
            ),
            policy=quality.ValidationPolicy.FAIL_FAST,
        ),
    )
    selected = builder.select(
        "customer360_projection",
        source=validated,
        columns=(
            "customer_id",
            "customer_name",
            "country",
            "normalized_email",
            "paid_order_count",
            "paid_revenue",
        ),
    )
    ordered = builder.sort(
        "customer360_ordered",
        source=selected,
        by=("customer_id",),
    )
    return builder.output("customer_360", ordered).build()


def _customers_records() -> list[dict[str, object]]:
    return [
        {
            "customer_id": 3,
            "customer_name": "Chloé",
            "country": "FR",
            "email": None,
        },
        {
            "customer_id": 1,
            "customer_name": "Alice",
            "country": "FR",
            "email": " ALICE@EXAMPLE.COM ",
        },
        {
            "customer_id": 2,
            "customer_name": "Björk",
            "country": "IS",
            "email": " BJORK@EXAMPLE.COM ",
        },
    ]


def _orders_records() -> list[dict[str, object]]:
    return [
        {
            "order_id": 101,
            "customer_id": 1,
            "amount": 10.5,
            "status": "PAID",
        },
        {
            "order_id": 102,
            "customer_id": 1,
            "amount": 5.0,
            "status": "PAID",
        },
        {
            "order_id": 103,
            "customer_id": 1,
            "amount": 99.0,
            "status": "CANCELLED",
        },
        {
            "order_id": 104,
            "customer_id": 2,
            "amount": 20.0,
            "status": "PAID",
        },
        {
            "order_id": 105,
            "customer_id": 2,
            "amount": 2.0,
            "status": "PENDING",
        },
    ]


def _runtime(adapter: object, root: Path | None = None) -> TransformationRuntime:
    engines = EngineRegistry()
    engines.register(adapter)  # type: ignore[arg-type]

    resources = None
    if root is not None:
        resources = ResourceIORegistry()
        resources.register_writer(LocalFileWriter(root))

    return TransformationRuntime(
        engines=engines,
        resources=resources,
    )


def _normalize_value(value: object) -> object:
    if value is None or value is pd.NA:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _normalize(records: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {key: _normalize_value(value) for key, value in record.items()}
        for record in records
    ]


def _pandas_inputs() -> dict[str, InputBinding]:
    return {
        "customers": InputBinding.from_native(
            "customers",
            pd.DataFrame(_customers_records()),
            engine="pandas",
        ),
        "orders": InputBinding.from_native(
            "orders",
            pd.DataFrame(_orders_records()),
            engine="pandas",
        ),
    }


def _polars_inputs(*, lazy: bool) -> dict[str, InputBinding]:
    customers = pl.DataFrame(_customers_records())
    orders = pl.DataFrame(_orders_records())
    return {
        "customers": InputBinding.from_native(
            "customers",
            customers.lazy() if lazy else customers,
            engine="polars",
        ),
        "orders": InputBinding.from_native(
            "orders",
            orders.lazy() if lazy else orders,
            engine="polars",
        ),
    }


def _expected_records() -> list[dict[str, object]]:
    return [
        {
            "customer_id": 1,
            "customer_name": "Alice",
            "country": "FR",
            "normalized_email": "alice@example.com",
            "paid_order_count": 2,
            "paid_revenue": 15.5,
        },
        {
            "customer_id": 2,
            "customer_name": "Björk",
            "country": "IS",
            "normalized_email": "bjork@example.com",
            "paid_order_count": 1,
            "paid_revenue": 20.0,
        },
        {
            "customer_id": 3,
            "customer_name": "Chloé",
            "country": "FR",
            "normalized_email": None,
            "paid_order_count": None,
            "paid_revenue": None,
        },
    ]


def test_customer_360_plan_is_canonical_and_serializable() -> None:
    plan = _customer_360_plan()
    codec = TransformationPlanCodec()

    payload = codec.to_json(plan)
    decoded = codec.from_json(payload)

    assert codec.to_json(decoded) == payload
    assert codec.fingerprint(decoded) == codec.fingerprint(plan)

    logical = TransformationCompiler().compile(decoded)
    assert logical.output_names == ("customer_360",)
    assert logical.output_schema.names() == (
        "customer_id",
        "customer_name",
        "country",
        "normalized_email",
        "paid_order_count",
        "paid_revenue",
    )


@pytest.mark.parametrize("engine_id", ["pandas", "polars"])
def test_customer_360_eager_result_lineage_and_resource_handoff(
    engine_id: str,
    tmp_path: Path,
) -> None:
    plan = _customer_360_plan()
    output_resource = ResourceReference(
        scheme="file",
        locator=f"customer-360-{engine_id}.parquet",
        media_type="application/vnd.apache.parquet",
    )

    if engine_id == "pandas":
        runtime = _runtime(PandasEngineAdapter(), tmp_path)
        inputs = _pandas_inputs()
    else:
        runtime = _runtime(PolarsEngineAdapter(), tmp_path)
        inputs = _polars_inputs(lazy=False)

    result = runtime.execute(
        plan,
        engine=engine_id,
        inputs=inputs,
        outputs={
            "customer_360": OutputBinding.to_resource(
                "customer_360",
                output_resource,
                mode=WriteMode.CREATE_NEW,
                retry_safety=RetrySafety.SAFE,
            )
        },
        mode=ExecutionMode.EAGER,
    )

    if engine_id == "pandas":
        records = result.output_handle.dataframe.to_dict(orient="records")
    else:
        records = result.output_handle.frame.to_dicts()

    assert _normalize(records) == _expected_records()
    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.validation("customer360_quality").passed is True
    assert len(result.writes) == 1
    assert result.writes[0].status is WriteStatus.SUCCEEDED
    assert result.writes[0].resource == output_resource
    assert (tmp_path / output_resource.locator).exists()

    output_links = {
        (link.name, link.resource, link.role.value) for link in result.lineage.resources
    }
    assert ("customer_360", output_resource, "output") in output_links

    impact = LineageImpactAnalyzer()
    output_dataset = result.lineage.output("customer_360")

    revenue_sources = impact.upstream_fields(
        result.lineage,
        FieldReference.of(output_dataset, "paid_revenue"),
    )
    email_sources = impact.upstream_fields(
        result.lineage,
        FieldReference.of(output_dataset, "normalized_email"),
    )

    assert (
        result.lineage.input("orders"),
        "amount",
    ) in {
        (reference.dataset, str(reference.field_path)) for reference in revenue_sources
    }
    assert (
        result.lineage.input("customers"),
        "email",
    ) in {(reference.dataset, str(reference.field_path)) for reference in email_sources}


def test_customer_360_polars_lazy_matches_eager() -> None:
    plan = _customer_360_plan()
    runtime = _runtime(PolarsEngineAdapter())

    eager = runtime.execute(
        plan,
        engine="polars",
        inputs=_polars_inputs(lazy=False),
        mode=ExecutionMode.EAGER,
    )
    lazy = runtime.execute(
        plan,
        engine="polars",
        inputs=_polars_inputs(lazy=True),
        mode=ExecutionMode.LAZY,
    )

    eager_records = eager.output_handle.frame.to_dicts()
    lazy_frame = lazy.output_handle.frame
    lazy_records = (
        lazy_frame.collect().to_dicts()
        if isinstance(lazy_frame, pl.LazyFrame)
        else lazy_frame.to_dicts()
    )

    assert _normalize(lazy_records) == _normalize(eager_records)
    assert _normalize(lazy_records) == _expected_records()
    assert lazy.validation("customer360_quality").passed is True
