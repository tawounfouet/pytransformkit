# PyTransformKit Performance Qualification

LOT-25 keeps performance qualification separate from semantic correctness tests.

The harness is intentionally small and stdlib-first:

- `time.perf_counter_ns()` for duration;
- `tracemalloc` for Python allocation peaks;
- native engine memory measurements where available;
- fixed deterministic synthetic data;
- warmups plus repeated samples;
- JSON reports;
- explicit absolute and relative regression budgets.

No benchmark result is used to redefine transformation semantics. Correctness remains
owned by the normal unit, contract, cross-engine, optimizer and conformance suites.

## Profiles

The CI profile uses:

~~~text
rows       10,000
warmups    1
repeats    3
~~~

The local profile uses:

~~~text
rows       100,000
warmups    2
repeats    7
~~~

Run the CI-sized suite locally:

~~~bash
pip install -e ".[dev,performance]"

python -m benchmarks.run \
  --profile ci \
  --output performance-report.json \
  --assert-budgets
~~~

Run the larger local profile without enforcing CI budgets:

~~~bash
python -m benchmarks.run \
  --profile local \
  --output performance-report-local.json
~~~

## Scenario coverage

The benchmark suite measures:

~~~text
planning_compile
planning_optimize

expression_duckdb_compile
expression_polars_compile
expression_pandas_compile_eval

pandas_adapter_execution
pandas_runtime_execution
pandas_memory_amplification

polars_eager_execution
polars_lazy_execution
polars_memory_amplification

pandas_to_arrow
arrow_to_pandas
polars_to_arrow
arrow_to_polars

duckdb_eager_execution
duckdb_lazy_dispatch
duckdb_lazy_materialized

parquet_full_scan
parquet_pushdown

lineage_analysis

runtime_null_telemetry
runtime_recording_telemetry
~~~

Pandas expression lowering is inherently coupled to vectorized Series evaluation,
so its scenario is named `expression_pandas_compile_eval` rather than pretending
that Pandas exposes a separate pure compilation phase.

## Memory interpretation

`tracemalloc` captures Python allocations but does not observe all allocations made
inside Pandas, Polars, Arrow or DuckDB native code.

Therefore the memory qualification also records engine-native sizes:

- Pandas: `DataFrame.memory_usage(index=True, deep=True)`;
- Polars: `DataFrame.estimated_size()`;
- Arrow: `Table.nbytes`.

The `native_amplification_ratio` budgets use those native measurements rather than
claiming that Python allocation peaks represent total process RSS.

## Regression budgets

`benchmarks/budgets_ci.json` contains two kinds of gate:

1. absolute ceilings for median duration, p95 duration, Python peak allocation or
   native amplification;
2. relative ratios for abstraction or boundary costs.

The key relative budgets are:

~~~text
Pandas runtime / direct adapter            <= 3.00x
Polars lazy materialized / eager           <= 2.00x
DuckDB lazy materialized / eager           <= 2.00x
Parquet pushdown / full scan               <= 2.50x
recording telemetry / null telemetry       <= 1.75x
~~~

These are regression tripwires, not performance promises or public SLAs. They are
deliberately looser than the observed baseline to tolerate shared CI runner noise.

## 0.7.0 CI baseline

The first qualified CI baseline is committed at:

~~~text
benchmarks/baselines/0.7.0-ci.json
~~~

Source workflow run:

~~~text
36817814955
~~~

Selected observed medians on the 10,000-row CI profile:

| Scenario | Median |
| --- | ---: |
| Plan compilation | 1.37 ms |
| Logical optimization | 10.52 ms |
| Pandas direct adapter | 33.86 ms |
| Pandas full runtime | 52.78 ms |
| Polars eager | 24.02 ms |
| Polars lazy + collect | 22.63 ms |
| Pandas → Arrow | 2.80 ms |
| Polars → Arrow | 0.58 ms |
| DuckDB eager | 38.67 ms |
| DuckDB lazy + materialize | 38.84 ms |
| Parquet full scan | 3.15 ms |
| Parquet pushdown | 2.13 ms |
| Lineage analysis | 1.63 ms |
| Runtime with null telemetry | 27.79 ms |
| Runtime with recording telemetry | 29.37 ms |

Observed relative results in that run:

~~~text
Pandas runtime / direct adapter          1.56x
Polars lazy materialized / eager         0.94x
DuckDB lazy materialized / eager         1.00x
Parquet pushdown / full scan             0.68x
recording telemetry / null telemetry     1.06x
~~~

These numbers describe one GitHub-hosted runner and are not portable latency
guarantees. Future qualification should compare trends and budget violations, not
assume identical wall-clock values across machines.

## CI

The `performance-contract` job:

1. installs `.[dev,performance]`;
2. runs `tests/performance`;
3. executes the CI benchmark profile;
4. fails if a budget is exceeded;
5. uploads `performance-report.json` as `pytransformkit-performance-report`.

This keeps performance evidence inspectable while leaving the ordinary correctness
suite deterministic and semantics-focused.
