# ruff: noqa: E402

from __future__ import annotations

import pytest

pd = pytest.importorskip("pandas")
pa = pytest.importorskip("pyarrow")

from pytransformkit import (
    EngineRegistry,
    InputBinding,
    TransformationPlan,
    TransformationRuntime,
)
from pytransformkit import functions as fn
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.adapters.pyarrow import PyArrowEngineAdapter
from pytransformkit.domain.data.data_types import FloatType, IntegerType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.errors import EngineNotFoundError, UnsupportedEngineCapabilityError
from pytransformkit.functions import col


def _aggregate_plan() -> TransformationPlan:
    schema = Schema(
        (
            Field("customer_id", IntegerType(), nullable=False),
            Field("amount", FloatType(), nullable=False),
        )
    )
    builder = TransformationPlan.builder("unsupported_aggregate")
    source = builder.input("source", schema=schema)
    aggregate = builder.aggregate(
        "aggregate",
        source=source,
        group_by=(col("customer_id"),),
        metrics={"total_amount": fn.sum(col("amount"))},
    )
    return builder.output("result", aggregate).build()


def test_unsupported_capability_fails_before_pyarrow_execution() -> None:
    engines = EngineRegistry()
    engines.register(PyArrowEngineAdapter())
    runtime = TransformationRuntime(engines=engines)

    table = pa.table(
        {
            "customer_id": [1, 1],
            "amount": [10.0, 5.0],
        }
    )

    with pytest.raises(UnsupportedEngineCapabilityError) as captured:
        runtime.execute(
            _aggregate_plan(),
            engine="pyarrow",
            inputs={
                "source": InputBinding.from_native(
                    "source",
                    table,
                    engine="pyarrow",
                )
            },
        )

    assert captured.value.engine_id == "pyarrow"
    assert "aggregate" in captured.value.missing_capabilities


def test_runtime_never_falls_back_to_another_registered_engine() -> None:
    engines = EngineRegistry()
    engines.register(PandasEngineAdapter())
    runtime = TransformationRuntime(engines=engines)

    with pytest.raises(EngineNotFoundError):
        runtime.execute(
            _aggregate_plan(),
            engine="not-installed",
            inputs={
                "source": InputBinding.from_native(
                    "source",
                    pd.DataFrame(
                        {
                            "customer_id": [1],
                            "amount": [10.0],
                        }
                    ),
                    engine="pandas",
                )
            },
        )
