"""Executable Pandas engine guide for the frozen PyTransformKit V1 API."""

from __future__ import annotations

import pandas as pd

from pytransformkit import (
    DataType,
    Field,
    InputBinding,
    Schema,
    TransformationPlan,
    TransformationRuntime,
)
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.engines import EngineRegistry
from pytransformkit.functions import col, lower, trim


def main() -> None:
    schema = Schema(
        (
            Field("customer_id", DataType.int64(), nullable=False),
            Field("email", DataType.string(), nullable=True),
            Field("status", DataType.string(), nullable=False),
        )
    )

    builder = TransformationPlan.builder("pandas_guide")
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
    engines.register(PandasEngineAdapter())
    runtime = TransformationRuntime(engines=engines)

    frame = pd.DataFrame(
        {
            "customer_id": [1, 2],
            "email": [" A@EXAMPLE.COM ", " B@EXAMPLE.COM "],
            "status": ["ACTIVE", "INACTIVE"],
        }
    )
    result = runtime.execute(
        plan,
        engine="pandas",
        inputs={
            "customers": InputBinding.from_native(
                "customers",
                frame,
                engine="pandas",
            )
        },
    )

    records = result.output_handle.dataframe.to_dict(orient="records")
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
