"""Small deterministic benchmark harness used by LOT-25 qualification."""

from __future__ import annotations

import gc
import json
from collections.abc import Callable, Mapping
import platform
import statistics
import sys
import tracemalloc
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter_ns
from typing import TypeVar

from pytransformkit import __version__

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class BenchmarkConfig:
    """Execution controls shared by all benchmark scenarios."""

    warmups: int = 1
    repeats: int = 3
    trace_python_memory: bool = True
    gc_between_runs: bool = True

    def __post_init__(self) -> None:
        if self.warmups < 0:
            raise ValueError("warmups must be non-negative.")
        if self.repeats < 1:
            raise ValueError("repeats must be at least 1.")


@dataclass(frozen=True, slots=True)
class ScenarioOutcome:
    """One scenario result plus deterministic numeric observations."""

    value: object | None = None
    metrics: tuple[tuple[str, float], ...] = ()

    def __post_init__(self) -> None:
        names = tuple(name for name, _ in self.metrics)
        if len(names) != len(set(names)):
            raise ValueError("ScenarioOutcome metric names must be unique.")
        for name, value in self.metrics:
            if not name or not name.strip():
                raise ValueError("ScenarioOutcome metric names must not be empty.")
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError("ScenarioOutcome metric values must be numeric.")


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Aggregated measurements for one named scenario."""

    name: str
    durations_ms: tuple[float, ...]
    python_peak_bytes: tuple[int, ...]
    custom_metrics: tuple[tuple[str, float], ...]

    @property
    def median_ms(self) -> float:
        return float(statistics.median(self.durations_ms))

    @property
    def p95_ms(self) -> float:
        ordered = sorted(self.durations_ms)
        index = max(0, min(len(ordered) - 1, (95 * len(ordered) + 99) // 100 - 1))
        return float(ordered[index])

    @property
    def max_python_peak_bytes(self) -> int:
        return max(self.python_peak_bytes, default=0)

    def metric(self, name: str) -> float:
        if name == "median_ms":
            return self.median_ms
        if name == "p95_ms":
            return self.p95_ms
        if name == "max_python_peak_bytes":
            return float(self.max_python_peak_bytes)
        for metric_name, value in self.custom_metrics:
            if metric_name == name:
                return value
        raise KeyError(name)

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "median_ms": self.median_ms,
            "p95_ms": self.p95_ms,
            "min_ms": min(self.durations_ms),
            "max_ms": max(self.durations_ms),
            "durations_ms": list(self.durations_ms),
            "max_python_peak_bytes": self.max_python_peak_bytes,
            "custom_metrics": dict(self.custom_metrics),
        }


@dataclass(frozen=True, slots=True)
class BenchmarkSuiteReport:
    """Portable JSON benchmark report for one qualification run."""

    profile: str
    config: BenchmarkConfig
    results: tuple[BenchmarkResult, ...]
    generated_at: datetime
    framework_version: str
    python_version: str
    platform: str

    @classmethod
    def create(
        cls,
        *,
        profile: str,
        config: BenchmarkConfig,
        results: tuple[BenchmarkResult, ...],
    ) -> BenchmarkSuiteReport:
        return cls(
            profile=profile,
            config=config,
            results=results,
            generated_at=datetime.now(UTC),
            framework_version=__version__,
            python_version=platform.python_version(),
            platform=platform.platform(),
        )

    def result(self, name: str) -> BenchmarkResult:
        for item in self.results:
            if item.name == name:
                return item
        raise KeyError(name)

    def as_dict(self) -> dict[str, object]:
        return {
            "profile": self.profile,
            "generated_at": self.generated_at.isoformat(),
            "framework_version": self.framework_version,
            "python_version": self.python_version,
            "python_implementation": sys.implementation.name,
            "platform": self.platform,
            "config": {
                "warmups": self.config.warmups,
                "repeats": self.config.repeats,
                "trace_python_memory": self.config.trace_python_memory,
                "gc_between_runs": self.config.gc_between_runs,
            },
            "results": [result.as_dict() for result in self.results],
        }

    def write_json(self, path: str | Path) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


@dataclass(frozen=True, slots=True)
class RatioBudget:
    name: str
    numerator: str
    denominator: str
    metric: str
    maximum: float


@dataclass(frozen=True, slots=True)
class BenchmarkBudgetSet:
    """Absolute and relative regression budgets loaded from JSON."""

    absolute: tuple[tuple[str, tuple[tuple[str, float], ...]], ...]
    ratios: tuple[RatioBudget, ...]

    @classmethod
    def from_json(cls, path: str | Path) -> BenchmarkBudgetSet:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        raw_absolute = payload.get("absolute", {})
        raw_ratios = payload.get("ratios", [])
        if not isinstance(raw_absolute, dict) or not isinstance(raw_ratios, list):
            raise ValueError("Benchmark budget file has an invalid shape.")

        absolute: list[tuple[str, tuple[tuple[str, float], ...]]] = []
        for scenario, raw_limits in raw_absolute.items():
            if not isinstance(scenario, str) or not isinstance(raw_limits, dict):
                raise ValueError("Absolute benchmark budgets must be mappings.")
            limits = tuple(
                (str(metric), float(maximum))
                for metric, maximum in raw_limits.items()
            )
            absolute.append((scenario, limits))

        ratios = tuple(
            RatioBudget(
                name=str(item["name"]),
                numerator=str(item["numerator"]),
                denominator=str(item["denominator"]),
                metric=str(item["metric"]),
                maximum=float(item["maximum"]),
            )
            for item in raw_ratios
        )
        return cls(absolute=tuple(absolute), ratios=ratios)


@dataclass(frozen=True, slots=True)
class BudgetViolation:
    """One exceeded absolute or relative benchmark budget."""

    name: str
    observed: float
    maximum: float


def run_benchmark(
    name: str,
    operation: Callable[[], ScenarioOutcome | object],
    config: BenchmarkConfig,
) -> BenchmarkResult:
    """Warm a scenario, measure it repeatedly, and aggregate stable metrics."""
    if not name or not name.strip():
        raise ValueError("Benchmark name must not be empty.")

    for _ in range(config.warmups):
        operation()

    durations: list[float] = []
    peaks: list[int] = []
    custom_samples: dict[str, list[float]] = {}

    for _ in range(config.repeats):
        if config.gc_between_runs:
            gc.collect()

        if config.trace_python_memory:
            tracemalloc.start()

        started = perf_counter_ns()
        raw_outcome = operation()
        elapsed_ns = perf_counter_ns() - started

        peak = 0
        if config.trace_python_memory:
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

        outcome = (
            raw_outcome
            if isinstance(raw_outcome, ScenarioOutcome)
            else ScenarioOutcome(value=raw_outcome)
        )
        durations.append(elapsed_ns / 1_000_000)
        peaks.append(peak)
        for metric_name, value in outcome.metrics:
            custom_samples.setdefault(metric_name, []).append(float(value))

    custom_metrics = tuple(
        (metric_name, float(statistics.median(values)))
        for metric_name, values in sorted(custom_samples.items())
    )
    return BenchmarkResult(
        name=name,
        durations_ms=tuple(durations),
        python_peak_bytes=tuple(peaks),
        custom_metrics=custom_metrics,
    )


def evaluate_budgets(
    report: BenchmarkSuiteReport,
    budgets: BenchmarkBudgetSet,
) -> tuple[BudgetViolation, ...]:
    """Return all exceeded absolute and relative budgets."""
    violations: list[BudgetViolation] = []

    for scenario_name, limits in budgets.absolute:
        result = report.result(scenario_name)
        for metric_name, maximum in limits:
            observed = result.metric(metric_name)
            if observed > maximum:
                violations.append(
                    BudgetViolation(
                        name=f"{scenario_name}.{metric_name}",
                        observed=observed,
                        maximum=maximum,
                    )
                )

    for ratio in budgets.ratios:
        numerator = report.result(ratio.numerator).metric(ratio.metric)
        denominator = report.result(ratio.denominator).metric(ratio.metric)
        observed = numerator / max(denominator, 1e-9)
        if observed > ratio.maximum:
            violations.append(
                BudgetViolation(
                    name=ratio.name,
                    observed=observed,
                    maximum=ratio.maximum,
                )
            )

    return tuple(violations)


def metric_pairs(values: Mapping[str, int | float]) -> tuple[tuple[str, float], ...]:
    """Normalize scenario metrics into deterministic pairs."""
    return tuple(
        (name, float(value))
        for name, value in sorted(values.items())
    )
