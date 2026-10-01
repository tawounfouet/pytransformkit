"""Command-line runner for the LOT-25 benchmark qualification suite."""

from __future__ import annotations

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from benchmarks.harness import (
    BenchmarkBudgetSet,
    BenchmarkConfig,
    BenchmarkSuiteReport,
    evaluate_budgets,
    run_benchmark,
)
from benchmarks.scenarios import PerformanceScenarios


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run reproducible PyTransformKit performance qualification."
    )
    parser.add_argument(
        "--profile",
        choices=("ci", "local"),
        default="ci",
        help="Dataset/repetition profile.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-report.json"),
        help="JSON report destination.",
    )
    parser.add_argument(
        "--budgets",
        type=Path,
        default=Path("benchmarks/budgets_ci.json"),
        help="Budget JSON used by --assert-budgets.",
    )
    parser.add_argument(
        "--assert-budgets",
        action="store_true",
        help="Exit non-zero when an absolute or ratio budget is exceeded.",
    )
    return parser.parse_args()


def _profile(name: str) -> tuple[int, BenchmarkConfig]:
    if name == "ci":
        return (
            10_000,
            BenchmarkConfig(
                warmups=1,
                repeats=3,
                trace_python_memory=True,
                gc_between_runs=True,
            ),
        )
    return (
        100_000,
        BenchmarkConfig(
            warmups=2,
            repeats=7,
            trace_python_memory=True,
            gc_between_runs=True,
        ),
    )


def main() -> int:
    args = _arguments()
    row_count, config = _profile(args.profile)

    with TemporaryDirectory(prefix="pytransformkit-benchmarks-") as directory:
        suite = PerformanceScenarios(
            row_count=row_count,
            root=Path(directory),
        )
        results = tuple(
            run_benchmark(name, operation, config)
            for name, operation in suite.scenarios()
        )

    report = BenchmarkSuiteReport.create(
        profile=args.profile,
        config=config,
        results=results,
    )
    report.write_json(args.output)

    _print_report(report)

    if not args.assert_budgets:
        return 0

    budgets = BenchmarkBudgetSet.from_json(args.budgets)
    violations = evaluate_budgets(report, budgets)
    if not violations:
        print("Budget qualification: PASS")
        return 0

    print("Budget qualification: FAIL")
    for violation in violations:
        print(
            f"- {violation.name}: observed={violation.observed:.4f}, "
            f"maximum={violation.maximum:.4f}"
        )
    return 1


def _print_report(report: BenchmarkSuiteReport) -> None:
    print(
        f"PyTransformKit {report.framework_version} | "
        f"profile={report.profile} | Python {report.python_version}"
    )
    print(f"{'scenario':36} {'median ms':>12} {'p95 ms':>12} {'peak MiB':>12}")
    print("-" * 76)
    for result in report.results:
        peak_mib = result.max_python_peak_bytes / (1024 * 1024)
        print(
            f"{result.name:36} "
            f"{result.median_ms:12.3f} "
            f"{result.p95_ms:12.3f} "
            f"{peak_mib:12.3f}"
        )
    print(f"Report: {report.generated_at.isoformat()}")


if __name__ == "__main__":
    raise SystemExit(main())
