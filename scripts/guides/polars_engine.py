"""Executable Polars engine guide for the frozen PyTransformKit V1 API."""

from __future__ import annotations

import polars as pl

from pytransformkit import (
    DataType,
    Field,
    InputBinding,
    Schema,
    TransformationPlan,
    TransformationRuntime,
)
from pytransformkit.adapters.polars import PolarsEngineAdapter
from pytransformkit.engines import EngineRegistry
from pytransformkit.functions import col, lower, trim
from pytransformkit.runtime import ExecutionMode


def main() -> None:
    schema = Schema(
        (
            Field("customer_id", DataType.int64(), nullable=False),
            Field("email", DataType.string(), nullable=True),
            Field("status", DataType.string(), nullable=False),
        )
    )

    builder = TransformationPlan.builder("polars_guide")
    source = builder.input("customers", schema=schema)
    active = builder.filter(
        "active",
        source=source,
        where=col("status") == "ACTIVE",
    )
    normalized = builder.derive(
        "normalized",
        source=active,
        field_name="normalized_email",
        expression=lower(trim(col("email"))),
    )
    plan = builder.output("result", normalized).build()

    engines = EngineRegistry()
    engines.register(PolarsEngineAdapter())
    runtime = TransformationRuntime(engines=engines)

    frame = pl.DataFrame(
        {
            "customer_id": [1, 2],
            "email": [" A@EXAMPLE.COM ", " B@EXAMPLE.COM "],
            "status": ["ACTIVE", "INACTIVE"],
        }
    )
    result = runtime.execute(
        plan,
        engine="polars",
        inputs={
            "customers": InputBinding.from_native(
                "customers",
                frame.lazy(),
                engine="polars",
            )
        },
        mode=ExecutionMode.LAZY,
    )

    output = result.output_handle.frame
    records = output.collect().to_dicts()
    assert records == [
        {
            "customer_id": 1,
            "email": " A@EXAMPLE.COM ",
            "status": "ACTIVE",
            "normalized_email": "a@example.com",
        }
    ]


if __name__ == "__main__":
    main()
