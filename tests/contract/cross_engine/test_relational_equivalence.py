# ruff: noqa: E402

from __future__ import annotations

import math

import pytest

pd = pytest.importorskip("pandas")
pl = pytest.importorskip("polars")

from pytransformkit import (
    InputBinding,
    TransformationPlan,
    TransformationRuntime,
)
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.adapters.polars import PolarsEngineAdapter
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.transformations.relational import NullJoinPolicy
from pytransformkit.engines import EngineRegistry


def _left_schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=True),
            Field("status", StringType(), nullable=False),
        )
    )


def _right_schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=True),
            Field("status", StringType(), nullable=False),
            Field("amount", IntegerType(), nullable=False),
        )
    )


def _set_schema() -> Schema:
    return Schema(fields=(Field("value", IntegerType(), nullable=False),))


def _runtime(adapter: object) -> TransformationRuntime:
    registry = EngineRegistry()
    registry.register(adapter)  # type: ignore[arg-type]
    return TransformationRuntime(engines=registry)


def _normalize_value(value: object) -> object:
    if value is None:
        return None
    try:
        if bool(pd.isna(value)):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _normalize(
    records: list[dict[str, object]],
) -> list[dict[str, object]]:
    normalized = [
        {key: _normalize_value(value) for key, value in record.items()}
        for record in records
    ]
    return sorted(
        normalized,
        key=repr,
    )


def _execute_pandas(
    plan: TransformationPlan,
    left: list[dict[str, object]],
    right: list[dict[str, object]],
) -> list[dict[str, object]]:
    result = _runtime(PandasEngineAdapter()).execute(
        plan,
        engine="pandas",
        inputs={
            "left": InputBinding.from_native(
                "left",
                pd.DataFrame(left),
                engine="pandas",
            ),
            "right": InputBinding.from_native(
                "right",
                pd.DataFrame(right),
                engine="pandas",
            ),
        },
    )
    return _normalize(result.output_handle.dataframe.to_dict(orient="records"))


def _execute_polars(
    plan: TransformationPlan,
    left: list[dict[str, object]],
    right: list[dict[str, object]],
) -> list[dict[str, object]]:
    result = _runtime(PolarsEngineAdapter()).execute(
        plan,
        engine="polars",
        inputs={
            "left": InputBinding.from_native(
                "left",
                pl.DataFrame(left),
                engine="polars",
            ),
            "right": InputBinding.from_native(
                "right",
                pl.DataFrame(right),
                engine="polars",
            ),
        },
    )
    return _normalize(result.output_handle.frame.to_dicts())


def _join_plan(
    *,
    how: str = "inner",
    nulls: NullJoinPolicy = NullJoinPolicy.MATCH,
) -> TransformationPlan:
    builder = TransformationPlan.builder("join")
    left = builder.input(
        "left",
        schema=_left_schema(),
    )
    right = builder.input(
        "right",
        schema=_right_schema(),
    )
    joined = builder.join(
        "joined",
        left=left,
        right=right,
        how=how,
        on=(("customer_id", "customer_id"),),
        nulls=nulls,
        right_suffix="_right",
    )
    return builder.output("out", joined).build()


def _set_plan(operation: str, *, all: bool = False) -> TransformationPlan:
    builder = TransformationPlan.builder(operation)
    left = builder.input("left", schema=_set_schema())
    right = builder.input("right", schema=_set_schema())

    if operation == "union":
        output = builder.union(
            "set_result",
            left=left,
            right=right,
            all=all,
        )
    elif operation == "intersect":
        output = builder.intersect(
            "set_result",
            left=left,
            right=right,
        )
    elif operation == "except":
        output = builder.except_(
            "set_result",
            left=left,
            right=right,
        )
    else:
        raise AssertionError(operation)

    return builder.output("out", output).build()


@pytest.mark.parametrize("how", ["inner", "left", "right", "full"])
def test_join_semantics_match_across_pandas_and_polars(how: str) -> None:
    left = [
        {"customer_id": 1, "status": "ACTIVE"},
        {"customer_id": 2, "status": "ACTIVE"},
        {"customer_id": 3, "status": "INACTIVE"},
    ]
    right = [
        {"customer_id": 1, "status": "PAID", "amount": 10},
        {"customer_id": 1, "status": "PAID", "amount": 20},
        {"customer_id": 3, "status": "OPEN", "amount": 30},
    ]
    plan = _join_plan(how=how)

    pandas_records = _execute_pandas(plan, left, right)
    polars_records = _execute_polars(plan, left, right)

    assert pandas_records == polars_records
    assert set(pandas_records[0]) == {
        "customer_id",
        "status",
        "status_right",
        "amount",
    }


@pytest.mark.parametrize("how", ["semi", "anti"])
def test_semi_and_anti_join_semantics_match_across_engines(
    how: str,
) -> None:
    left = [
        {"customer_id": 1, "status": "ACTIVE"},
        {"customer_id": 2, "status": "ACTIVE"},
        {"customer_id": 3, "status": "INACTIVE"},
    ]
    right = [
        {"customer_id": 1, "status": "PAID", "amount": 10},
        {"customer_id": 3, "status": "OPEN", "amount": 30},
    ]
    plan = _join_plan(how=how)

    pandas_records = _execute_pandas(plan, left, right)
    polars_records = _execute_polars(plan, left, right)

    assert pandas_records == polars_records
    assert all(set(record) == {"customer_id", "status"} for record in pandas_records)


def test_cross_join_semantics_match_across_engines() -> None:
    left = [
        {"customer_id": 1, "status": "ACTIVE"},
        {"customer_id": 2, "status": "INACTIVE"},
    ]
    right = [
        {"customer_id": 10, "status": "PAID", "amount": 5},
        {"customer_id": 20, "status": "OPEN", "amount": 8},
    ]

    builder = TransformationPlan.builder("cross")
    left_ds = builder.input("left", schema=_left_schema())
    right_ds = builder.input("right", schema=_right_schema())
    joined = builder.join(
        "joined",
        left=left_ds,
        right=right_ds,
        how="cross",
    )
    plan = builder.output("out", joined).build()

    pandas_records = _execute_pandas(plan, left, right)
    polars_records = _execute_polars(plan, left, right)

    assert pandas_records == polars_records
    assert len(pandas_records) == 4


def test_null_join_policy_match_is_cross_engine_equivalent() -> None:
    left = [
        {"customer_id": None, "status": "LEFT_NULL"},
        {"customer_id": 1, "status": "LEFT"},
    ]
    right = [
        {"customer_id": None, "status": "RIGHT_NULL", "amount": 99},
        {"customer_id": 1, "status": "RIGHT", "amount": 10},
    ]
    plan = _join_plan(nulls=NullJoinPolicy.MATCH)

    assert _execute_pandas(plan, left, right) == _execute_polars(
        plan,
        left,
        right,
    )


def test_null_join_policy_never_match_is_cross_engine_equivalent() -> None:
    left = [
        {"customer_id": None, "status": "LEFT_NULL"},
        {"customer_id": 1, "status": "LEFT"},
    ]
    right = [
        {"customer_id": None, "status": "RIGHT_NULL", "amount": 99},
        {"customer_id": 1, "status": "RIGHT", "amount": 10},
    ]
    plan = _join_plan(nulls=NullJoinPolicy.NEVER_MATCH)

    pandas_records = _execute_pandas(plan, left, right)
    polars_records = _execute_polars(plan, left, right)

    assert pandas_records == polars_records
    assert pandas_records == [
        {
            "customer_id": 1.0,
            "status": "LEFT",
            "status_right": "RIGHT",
            "amount": 10,
        }
    ]


@pytest.mark.parametrize(
    ("operation", "all"),
    [
        ("union", False),
        ("union", True),
        ("intersect", False),
        ("except", False),
    ],
)
def test_set_semantics_match_across_engines(
    operation: str,
    all: bool,
) -> None:
    left = [
        {"value": 1},
        {"value": 1},
        {"value": 2},
        {"value": 3},
    ]
    right = [
        {"value": 2},
        {"value": 4},
    ]
    plan = _set_plan(
        operation,
        all=all,
    )

    pandas_records = _execute_pandas(
        plan,
        left,
        right,
    )
    polars_records = _execute_polars(
        plan,
        left,
        right,
    )

    assert pandas_records == polars_records
