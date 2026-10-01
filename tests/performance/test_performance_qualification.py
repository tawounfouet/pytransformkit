# ruff: noqa: E402, I001

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pandas")
pytest.importorskip("polars")
pytest.importorskip("pyarrow")
pytest.importorskip("duckdb")

from benchmarks.harness import BenchmarkBudgetSet
from benchmarks.scenarios import PerformanceScenarios
from pytransformkit.application.io import PushdownStatus


pytestmark = pytest.mark.performance


def _suite(tmp_path: Path) -> PerformanceScenarios:
    return PerformanceScenarios(
        row_count=1_000,
        root=tmp_path,
    )


def test_ci_budget_file_covers_every_published_performance_scenario(
    tmp_path: Path,
) -> None:
    suite = _suite(tmp_path)
    scenario_names = {name for name, _ in suite.scenarios()}
    budgets = BenchmarkBudgetSet.from_json("benchmarks/budgets_ci.json")
    budget_names = {name for name, _ in budgets.absolute}

    assert budget_names == scenario_names


def test_planning_optimizer_preserves_reference_output_contract(
    tmp_path: Path,
) -> None:
    suite = _suite(tmp_path)

    compiled = suite.planning_compile().value
    optimized = suite.planning_optimize().value

    assert optimized.plan.output_schema == compiled.output_schema
    assert optimized.plan.output_names == compiled.output_names


def test_pandas_runtime_matches_direct_adapter_result(
    tmp_path: Path,
) -> None:
    suite = _suite(tmp_path)

    direct = suite.pandas_adapter_execution().value
    runtime = suite.pandas_runtime_execution().value

    direct_records = direct.output_handle.dataframe.to_dict(orient="records")
    runtime_records = runtime.output_handle.dataframe.to_dict(orient="records")

    assert runtime_records == direct_records


def test_polars_lazy_materialization_matches_eager_result(
    tmp_path: Path,
) -> None:
    suite = _suite(tmp_path)

    eager = suite.polars_eager_execution().value
    lazy = suite.polars_lazy_execution().value

    eager_records = eager.output_handle.frame.to_dicts()
    lazy_records = lazy.to_dicts()

    assert lazy_records == eager_records


def test_arrow_interchange_preserves_row_counts(
    tmp_path: Path,
) -> None:
    suite = _suite(tmp_path)

    pandas_arrow = suite.pandas_to_arrow().value
    polars_arrow = suite.polars_to_arrow().value
    pandas_native = suite.arrow_to_pandas().value
    polars_native = suite.arrow_to_polars().value

    assert pandas_arrow.value.table.num_rows == suite.row_count
    assert polars_arrow.value.table.num_rows == suite.row_count
    assert len(pandas_native.value) == suite.row_count
    assert polars_native.value.height == suite.row_count


def test_duckdb_lazy_materialization_matches_eager_result(
    tmp_path: Path,
) -> None:
    suite = _suite(tmp_path)

    eager = suite.duckdb_eager_execution().value
    lazy = suite.duckdb_lazy_materialized().value

    assert eager.to_pylist() == lazy.to_pylist()


def test_parquet_pushdown_matches_full_scan_and_reports_source_evidence(
    tmp_path: Path,
) -> None:
    suite = _suite(tmp_path)

    full = suite.parquet_full_scan().value
    pushed = suite.parquet_pushdown().value

    assert full.to_pylist() == pushed.value.to_pylist()
    assert pushed.pushdown.projection is PushdownStatus.SOURCE
    assert pushed.pushdown.predicate is PushdownStatus.SOURCE


def test_native_memory_amplification_is_observed_for_stable_engines(
    tmp_path: Path,
) -> None:
    suite = _suite(tmp_path)

    pandas_metrics = dict(suite.pandas_memory_amplification().metrics)
    polars_metrics = dict(suite.polars_memory_amplification().metrics)

    assert pandas_metrics["native_input_bytes"] > 0
    assert pandas_metrics["native_output_bytes"] > 0
    assert pandas_metrics["native_amplification_ratio"] > 0
    assert polars_metrics["native_input_bytes"] > 0
    assert polars_metrics["native_output_bytes"] > 0
    assert polars_metrics["native_amplification_ratio"] > 0


def test_recording_telemetry_emits_evidence_without_changing_result(
    tmp_path: Path,
) -> None:
    suite = _suite(tmp_path)

    baseline = suite.runtime_null_telemetry().value
    observed = suite.runtime_recording_telemetry()

    assert observed.value.output_handle.dataframe.to_dict(
        orient="records"
    ) == baseline.output_handle.dataframe.to_dict(orient="records")
    metrics = dict(observed.metrics)
    assert metrics["events"] > 0
    assert metrics["metrics"] > 0
    assert metrics["spans"] > 0
