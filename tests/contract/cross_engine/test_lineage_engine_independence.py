# ruff: noqa: E402

from __future__ import annotations

import pytest

pd = pytest.importorskip("pandas")
pl = pytest.importorskip("polars")

from pytransformkit import (
    InputBinding,
    TransformationPlan,
    TransformationRuntime,
    lineage,
)
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.adapters.polars import PolarsEngineAdapter
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.engines import EngineRegistry
from pytransformkit.functions import col, lower


def _schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("email", StringType(), nullable=True),
            Field("status", StringType(), nullable=False),
        )
    )


def _plan() -> TransformationPlan:
    builder = TransformationPlan.builder("lineage_engine_independence")
    customers = builder.input("customers", schema=_schema())
    active = builder.filter(
        "active",
        source=customers,
        where=col("status") == "ACTIVE",
    )
    normalized = builder.derive(
        "normalized",
        source=active,
        field_name="normalized_email",
        expression=lower(col("email")),
    )
    return builder.output("out", normalized).build()


def _runtime(adapter: object) -> TransformationRuntime:
    registry = EngineRegistry()
    registry.register(adapter)  # type: ignore[arg-type]
    return TransformationRuntime(engines=registry)


def test_logical_lineage_is_identical_after_pandas_and_polars_execution() -> None:
    plan = _plan()
    records = [
        {
            "customer_id": 1,
            "email": "ALICE@EXAMPLE.COM",
            "status": "ACTIVE",
        },
        {
            "customer_id": 2,
            "email": "BOB@EXAMPLE.COM",
            "status": "INACTIVE",
        },
    ]

    pandas_result = _runtime(PandasEngineAdapter()).execute(
        plan,
        engine="pandas",
        inputs={
            "customers": InputBinding.from_native(
                "customers",
                pd.DataFrame(records),
                engine="pandas",
            )
        },
    )
    polars_result = _runtime(PolarsEngineAdapter()).execute(
        plan,
        engine="polars",
        inputs={
            "customers": InputBinding.from_native(
                "customers",
                pl.DataFrame(records),
                engine="polars",
            )
        },
    )

    pandas_lineage = lineage.analyze(pandas_result.logical_plan)
    polars_lineage = lineage.analyze(polars_result.logical_plan)

    assert pandas_lineage == polars_lineage
    assert pandas_lineage.output("out") == polars_lineage.output("out")
    assert {dependency.kind for dependency in pandas_lineage.dependencies} == {
        dependency.kind for dependency in polars_lineage.dependencies
    }
