from __future__ import annotations

import json

from benchmarks.harness import (
    BenchmarkBudgetSet,
    BenchmarkConfig,
    BenchmarkSuiteReport,
    ScenarioOutcome,
    evaluate_budgets,
    metric_pairs,
    run_benchmark,
)


def test_harness_aggregates_timings_memory_and_custom_metrics(tmp_path) -> None:
    result = run_benchmark(
        "example",
        lambda: ScenarioOutcome(
            value=42,
            metrics=metric_pairs({"rows": 10, "bytes": 100}),
        ),
        BenchmarkConfig(warmups=1, repeats=3),
    )

    assert result.name == "example"
    assert len(result.durations_ms) == 3
    assert result.median_ms >= 0.0
    assert result.p95_ms >= result.median_ms
    assert result.max_python_peak_bytes >= 0
    assert result.metric("rows") == 10.0
    assert result.metric("bytes") == 100.0

    report = BenchmarkSuiteReport.create(
        profile="test",
        config=BenchmarkConfig(warmups=0, repeats=1),
        results=(result,),
    )
    destination = tmp_path / "report.json"
    report.write_json(destination)

    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["framework_version"]
    assert payload["profile"] == "test"
    assert payload["results"][0]["name"] == "example"


def test_budget_evaluation_reports_absolute_and_ratio_regressions(tmp_path) -> None:
    fast = run_benchmark(
        "fast",
        lambda: ScenarioOutcome(metrics=metric_pairs({"size": 10})),
        BenchmarkConfig(warmups=0, repeats=1, trace_python_memory=False),
    )
    slow = run_benchmark(
        "slow",
        lambda: ScenarioOutcome(metrics=metric_pairs({"size": 20})),
        BenchmarkConfig(warmups=0, repeats=1, trace_python_memory=False),
    )
    report = BenchmarkSuiteReport.create(
        profile="test",
        config=BenchmarkConfig(warmups=0, repeats=1),
        results=(fast, slow),
    )

    budget_path = tmp_path / "budgets.json"
    budget_path.write_text(
        json.dumps(
            {
                "absolute": {"slow": {"size": 15}},
                "ratios": [
                    {
                        "name": "slow_vs_fast_size",
                        "numerator": "slow",
                        "denominator": "fast",
                        "metric": "size",
                        "maximum": 1.5,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    violations = evaluate_budgets(
        report,
        BenchmarkBudgetSet.from_json(budget_path),
    )

    assert {violation.name for violation in violations} == {
        "slow.size",
        "slow_vs_fast_size",
    }
