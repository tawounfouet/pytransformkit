# ruff: noqa: E402,I001
from __future__ import annotations

import pytest

pd = pytest.importorskip("pandas")
import pandas.testing as pdt

from pytransformkit import InputBinding, TransformationPlan, TransformationRuntime
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.application.execution.registry import EngineRegistry
from pytransformkit.application.planning.optimizer import LogicalOptimizer
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.functions import col, lit
from pytransformkit.planning import TransformationCompiler


def _schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("status", StringType(), nullable=False),
            Field("amount", IntegerType(), nullable=False),
        )
    )


def _logical_plan():
    builder = TransformationPlan.builder("optimizer_equivalence")
    source = builder.input("customers", schema=_schema())
    sorted_rows = builder.sort(
        "sorted_rows",
        source=source,
        by=("amount",),
    )
    selected = builder.select(
        "selected",
        source=sorted_rows,
        columns=("customer_id", "amount"),
    )
    filtered = builder.filter(
        "filtered",
        source=selected,
        where=(col("amount") > (lit(5) + lit(5))) & lit(True),
    )
    return TransformationCompiler().compile(builder.output("result", filtered).build())


def _runtime() -> TransformationRuntime:
    registry = EngineRegistry()
    registry.register(PandasEngineAdapter())
    return TransformationRuntime(engines=registry)


def _input() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4],
            "status": ["A", "B", "A", "C"],
            "amount": [25, 5, 15, 10],
        }
    )


def test_optimized_plan_matches_original_pandas_result() -> None:
    original = _logical_plan()
    optimized = LogicalOptimizer().optimize(original)

    original_result = _runtime().execute(
        original,
        engine="pandas",
        inputs={
            "customers": InputBinding.from_native(
                "customers",
                _input(),
                engine="pandas",
            )
        },
    )
    optimized_result = _runtime().execute(
        optimized,
        engine="pandas",
        inputs={
            "customers": InputBinding.from_native(
                "customers",
                _input(),
                engine="pandas",
            )
        },
    )

    left = original_result.output_handle.dataframe.reset_index(drop=True)
    right = optimized_result.output_handle.dataframe.reset_index(drop=True)
    pdt.assert_frame_equal(left, right)
