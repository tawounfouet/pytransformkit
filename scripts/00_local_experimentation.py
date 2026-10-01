"""Local end-to-end experimentation with the canonical PyTransformKit V1 API.

Run from the repository root after installing the development and engine extras:

    pip install -e ".[dev,pandas,polars]"
    python "scripts/00_local_experimentation.py"
"""

from __future__ import annotations

import pandas as pd
import polars as pl

from pytransformkit import (
    DataType,
    Field,
    InputBinding,
    Schema,
    TransformationPlan,
    TransformationRuntime,
)
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.adapters.polars import PolarsEngineAdapter
from pytransformkit.engines import EngineRegistry
from pytransformkit.functions import col, lower, trim
from pytransformkit.planning import TransformationCompiler
from pytransformkit.runtime import ExecutionMode

RECORDS = [
    {
        "customer_id": 1,
        "email": " JOHN@EXAMPLE.COM ",
        "status": "ACTIVE",
    },
    {
        "customer_id": 2,
        "email": " ALICE@EXAMPLE.COM ",
        "status": "ACTIVE",
    },
    {
        "customer_id": 3,
        "email": None,
        "status": "INACTIVE",
    },
    {
        "customer_id": 4,
        "email": " BOB@EXAMPLE.COM ",
        "status": "ACTIVE",
    },
]


def build_schema() -> Schema:
    """Create the logical, engine-independent input Schema."""
    return Schema(
        fields=(
            Field("customer_id", DataType.int64(), nullable=False),
            Field("email", DataType.string(), nullable=True),
            Field("status", DataType.string(), nullable=False),
        )
    )


def build_plan(schema: Schema) -> TransformationPlan:
    """Build one TransformationPlan that can execute on multiple engines."""
    builder = TransformationPlan.builder("customers")
    customers = builder.input("customers", schema=schema)
    active = builder.filter(
        "active_customers",
        source=customers,
        where=col("status") == "ACTIVE",
    )
    normalized = builder.derive(
        "normalize_email",
        source=active,
        field_name="normalized_email",
        expression=lower(trim(col("email"))),
    )
    selected = builder.select(
        "customer_view",
        source=normalized,
        columns=("customer_id", "normalized_email"),
    )
    return builder.output("customers_out", selected).build()


def print_section(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def main() -> None:
    schema = build_schema()
    transformation_plan = build_plan(schema)

    pandas_df = pd.DataFrame(RECORDS)
    polars_df = pl.DataFrame(RECORDS)

    print_section("1. Logical Schema")
    print(schema)

    print_section("2. TransformationPlan")
    print(transformation_plan)

    print_section("3. LogicalPlan — no physical data execution")
    logical_plan = TransformationCompiler().compile(transformation_plan)
    print("Plan:", logical_plan.plan_name)
    print("Inputs:", logical_plan.input_names)
    print("Outputs:", logical_plan.output_names)
    print("Output Schema:", logical_plan.output_schema.names())
    print("Node kinds:", [node.kind.value for node in logical_plan.nodes])

    registry = EngineRegistry()
    registry.register(PandasEngineAdapter())
    registry.register(PolarsEngineAdapter())
    runtime = TransformationRuntime(engines=registry)

    print_section("4. Pandas execution")
    pandas_result = runtime.execute(
        transformation_plan,
        engine="pandas",
        inputs={
            "customers": InputBinding.from_native(
                "customers",
                pandas_df,
                engine="pandas",
            )
        },
    )
    pandas_output = pandas_result.output_handle.dataframe
    print(pandas_output)
    print("Execution id:", pandas_result.execution_id)
    print("Engine:", pandas_result.engine.id)
    print("Output Schema:", pandas_result.output_schema.names())

    print_section("5. Polars eager execution")
    polars_result = runtime.execute(
        transformation_plan,
        engine="polars",
        inputs={
            "customers": InputBinding.from_native(
                "customers",
                polars_df,
                engine="polars",
            )
        },
    )
    polars_output = polars_result.output_handle.frame
    print(polars_output)
    print("Execution id:", polars_result.execution_id)
    print("Engine:", polars_result.engine.id)
    print("Output Schema:", polars_result.output_schema.names())

    print_section("6. Pandas / Polars semantic comparison")
    pandas_records = pandas_output.to_dict(orient="records")
    polars_records = polars_output.to_dicts()

    print("Pandas records:", pandas_records)
    print("Polars records:", polars_records)
    print("Equivalent:", pandas_records == polars_records)

    if pandas_records != polars_records:
        raise AssertionError("Pandas and Polars produced different logical results.")

    print_section("7. Polars lazy execution")
    lazy_result = runtime.execute(
        transformation_plan,
        engine="polars",
        inputs={
            "customers": InputBinding.from_native(
                "customers",
                polars_df.lazy(),
                engine="polars",
            )
        },
        mode=ExecutionMode.LAZY,
    )
    lazy_frame = lazy_result.output_handle.frame

    print("Physical result type:", type(lazy_frame))
    print("Lazy plan:")
    print(lazy_frame)

    print("Collected result:")
    print(lazy_frame.collect())

    print_section("Experiment completed successfully")


if __name__ == "__main__":
    main()
