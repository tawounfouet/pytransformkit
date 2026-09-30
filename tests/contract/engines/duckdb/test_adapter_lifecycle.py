# ruff: noqa: E402

from __future__ import annotations

import pytest

duckdb = pytest.importorskip("duckdb")
pa = pytest.importorskip("pyarrow")

from pytransformkit import InputBinding, TransformationPlan, TransformationRuntime
from pytransformkit.adapters.duckdb import DuckDBEngineAdapter
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.engines import EngineRegistry
from pytransformkit.functions import col, lower
from pytransformkit.planning import TransformationCompiler
from pytransformkit.runtime import ExecutionMode


def _schema() -> Schema:
    return Schema(
        (
            Field("customer_id", IntegerType(), nullable=False),
            Field("status", StringType(), nullable=False),
        )
    )


def _plan() -> TransformationPlan:
    builder = TransformationPlan.builder("duckdb_customers")
    source = builder.input("customers", schema=_schema())
    active = builder.filter(
        "active",
        source=source,
        where=col("customer_id") > 1,
    )
    derived = builder.derive(
        "normalized",
        source=active,
        field_name="normalized_status",
        expression=lower(col("status")),
    )
    sorted_result = builder.sort(
        "ordered",
        source=derived,
        by=("customer_id",),
    )
    return builder.output("result", sorted_result).build()


def _runtime(adapter: DuckDBEngineAdapter) -> TransformationRuntime:
    registry = EngineRegistry()
    registry.register(adapter)
    return TransformationRuntime(engines=registry)


def _table():
    return pa.table(
        {
            "customer_id": [3, 1, 2],
            "status": ["ACTIVE", "OPEN", "PAID"],
        }
    )


def test_arrow_input_executes_to_duckdb_relation() -> None:
    adapter = DuckDBEngineAdapter()

    result = _runtime(adapter).execute(
        _plan(),
        engine="duckdb",
        inputs={
            "customers": InputBinding.from_native(
                "customers",
                _table(),
                engine="duckdb",
            )
        },
    )

    assert result.output_handle.engine_id == "duckdb"
    assert result.output_handle.to_arrow_table().to_pydict() == {
        "customer_id": [2, 3],
        "status": ["PAID", "ACTIVE"],
        "normalized_status": ["paid", "active"],
    }
    adapter.close()


def test_lazy_mode_returns_relation_and_parameter_binding_diagnostic() -> None:
    adapter = DuckDBEngineAdapter()

    result = _runtime(adapter).execute(
        _plan(),
        engine="duckdb",
        inputs={
            "customers": InputBinding.from_native(
                "customers",
                _table(),
                engine="duckdb",
            )
        },
        mode=ExecutionMode.LAZY,
    )

    assert result.output_handle.engine_id == "duckdb"
    assert any(
        diagnostic.code == "PTK-DUCKDB-LAZY-001"
        for diagnostic in result.diagnostics
    )
    assert result.output_handle.to_arrow_table().num_rows == 2
    adapter.close()


def test_user_owned_connection_is_never_closed_by_adapter() -> None:
    connection = duckdb.connect()
    adapter = DuckDBEngineAdapter(connection)

    assert adapter.owns_connection is False

    adapter.close()

    assert connection.execute("SELECT 42").fetchone() == (42,)
    connection.close()


def test_native_explain_is_available_without_exposing_sql_to_domain() -> None:
    adapter = DuckDBEngineAdapter()
    handle = adapter.bind_native(_table())

    plan = TransformationCompiler().compile(_plan())
    explanations = adapter.explain(
        plan,
        {"customers": handle},
    )

    assert explanations["result"].strip()
    adapter.close()
