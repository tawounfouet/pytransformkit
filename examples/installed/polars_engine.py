"""Installed-artifact Polars guide smoke."""

import polars as pl

from pytransformkit import (
    DataType,
    Field,
    InputBinding,
    Schema,
    TransformationPlan,
    TransformationRuntime,
    col,
)
from pytransformkit.adapters.polars import PolarsEngineAdapter
from pytransformkit.engines import EngineRegistry
from pytransformkit.runtime import ExecutionMode


schema = Schema(
    fields=(
        Field("customer_id", DataType.int64(), nullable=False),
        Field("status", DataType.string(), nullable=False),
    )
)

builder = TransformationPlan.builder("active_customers")
customers = builder.input("customers", schema=schema)
active = builder.filter(
    "active_only",
    source=customers,
    where=col("status") == "ACTIVE",
)
plan = builder.output("result", active).build()

registry = EngineRegistry()
registry.register(PolarsEngineAdapter())
runtime = TransformationRuntime(engines=registry)

result = runtime.execute(
    plan,
    engine="polars",
    inputs={
        "customers": InputBinding.from_native(
            "customers",
            pl.DataFrame(
                {
                    "customer_id": [1, 2, 3],
                    "status": ["ACTIVE", "INACTIVE", "ACTIVE"],
                }
            ),
            engine="polars",
        )
    },
    mode=ExecutionMode.LAZY,
)

frame = result.output_handle.frame
materialized = frame.collect() if isinstance(frame, pl.LazyFrame) else frame
assert materialized["customer_id"].to_list() == [1, 3]
print("polars-engine-guide: OK")
