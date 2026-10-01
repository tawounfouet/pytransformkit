"""Installed-artifact Pandas guide smoke."""

import pandas as pd

from pytransformkit import (
    DataType,
    Field,
    InputBinding,
    Schema,
    TransformationPlan,
    TransformationRuntime,
    col,
)
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.engines import EngineRegistry


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
registry.register(PandasEngineAdapter())
runtime = TransformationRuntime(engines=registry)

result = runtime.execute(
    plan,
    engine="pandas",
    inputs={
        "customers": InputBinding.from_native(
            "customers",
            pd.DataFrame(
                {
                    "customer_id": [1, 2, 3],
                    "status": ["ACTIVE", "INACTIVE", "ACTIVE"],
                }
            ),
            engine="pandas",
        )
    },
)

assert result.output_handle.dataframe["customer_id"].tolist() == [1, 3]
print("pandas-engine-guide: OK")
