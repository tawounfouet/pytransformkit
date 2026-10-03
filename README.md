# PyTransformKit

**Define transformations once. Execute them anywhere.**

PyTransformKit is an engine-agnostic Python framework for defining typed, composable data transformations independently from their physical execution engine.

> Status: PyTransformKit 1.0.0 is stable. The additive 1.1 declarative-schema line is currently qualified at **1.1.0rc2**.

## Goals

- Define logical transformations independently from Pandas, Polars, PyArrow, DuckDB, or future engines.
- Keep the Domain model free from engine-specific types.
- Make schema propagation, validation, lineage, observability, and optimization first-class concerns.
- Prove semantic consistency through contract and cross-engine tests.
- Keep ingestion lifecycle and workflow orchestration outside PyTransformKit ownership.

## Current implementation status

The implementation baseline now covers:

- **LOT-00 — Repository Bootstrap**
- **LOT-01 — Shared Kernel**
- **LOT-02 — Type System & Schema Core**
- **LOT-03 — Dataset Domain Model**
- **LOT-04 — Expression AST Core**
- **LOT-05 — Transformation Model MVP**
- **LOT-06 — Initial DAG Core**
- **LOT-07 — Engine Runtime Contracts**
- **LOT-08 — Pandas Reference Adapter**
- **LOT-09 — Initial Application Execution Service**
- **LOT-10 — Polars Adapter & Multi-Engine Contract**
- **LOT-11 — V1 Public Model Migration & Relational Core**
- **LOT-12 — Aggregation & Grouping**
- **LOT-13 — Window & Analytical Semantics**
- **LOT-14 — Reshaping, Temporal & Nested Semantics**
- **LOT-15 — Data Quality & Validation**
- **LOT-16 — Logical & Field Lineage**
- **LOT-17 — Runtime Identity, Diagnostics & Observability**
- **LOT-18 — PyArrow Adapter & Interchange**
- **LOT-19 — DuckDB Adapter & SQL Lowering**
- **LOT-20 — Physical I/O & Resource Boundary**
- **LOT-21 — Versioned Serialization & Canonical IR**
- **LOT-22 — Logical Optimizer**
- **LOT-23 — Extension and Plugin Architecture**
- **LOT-24 — Cross-Engine Conformance & Customer 360 Gate**
- **LOT-25 — Performance & Memory Qualification**
- **LOT-26 — Public API, Documentation, Security & Compatibility**
- **LOT-27 — 1.0 Release Candidate Qualification**
- **LOT-28 — PyTransformKit 1.0.0 Stable Release**

The current release line is **1.0.0**. LOT-28 stable qualification is the final step of the frozen V1 roadmap.

### Canonical V1 model

The canonical public path is now:

~~~text
TransformationPlan
        ↓
TransformationCompiler
        ↓
LogicalPlan
        ↓
TransformationRuntime
        ↓
explicit EngineAdapter
        ↓
TransformationResult
~~~

The package root promotes:

- `TransformationPlan`;
- `LogicalPlan`;
- `TransformationRuntime`;
- `TransformationExecutionId`;
- `TransformationResult`;
- `InputBinding`;
- `OutputBinding`;
- `ResourceReference`;
- `Dataset`, `Schema`, `Field`, `DataType`;
- `Expression`, `col()`, `lit()`;
- `quality` as the public data-quality authoring namespace;
- `lineage` as the public logical and field-lineage namespace;
- `diagnostics` as the public runtime observability namespace.

The former `Pipeline` / `RunPipelineService` path is retained only as a pre-V1 compatibility surface and is no longer the canonical API.

### Logical data and expressions

The logical data layer provides engine-independent primitive DataTypes, immutable Fields and Schemas, logical Dataset identity and portable Dataset references. A logical Dataset never stores a Pandas DataFrame, Polars DataFrame, Arrow Table or other native engine object.

The Expression layer provides a portable immutable AST, `col/lit` DSL, string functions, static logical typing, NULL-aware nullability propagation, dependency extraction and canonical structural fingerprints.

### Transformations and relational semantics

The portable Transformation model currently includes:

- select, drop and rename;
- filter, limit and distinct;
- cast and derive;
- sort and deduplicate;
- join;
- union;
- intersect;
- except;
- aggregate/group by;
- analytical windows;
- pivot, unpivot, explode and flatten;
- nested Struct field access;
- temporal extraction, timestamp normalization, timezone conversion and duration expressions.

LOT-11 adds multi-input logical dependencies, deterministic relational schema resolution, explicit join-key semantics, column-collision handling and configurable NULL join behavior.

LOT-12 adds a typed aggregate-expression context with `count`, `count_distinct`, `sum`, `min`, `max`, `mean`/`avg`, deterministic grouped-schema propagation, NULL-aware aggregate semantics, and Pandas/Polars conformance for grouped and global aggregation.

LOT-13 adds immutable window specifications, explicit partition/order semantics, `row_number`, `rank`, `dense_rank`, `lag`, `lead`, partition aggregates, cumulative aggregates and moving ROWS aggregates. Window frame support is capability-gated so unsupported ROWS/RANGE shapes fail before physical execution.

LOT-14 closes the 0.2.x transformation vocabulary with deterministic reshape semantics, logical `ListType`, `StructType`, `MapType` and `DurationType`, nested Struct paths, portable temporal functions, and explicit engine capabilities for reshape, nested and temporal execution.

LOT-15 introduces transformation-owned data quality through `ValidationSpec`, typed validation rules, `QualityGate`, threshold policies and structured `ValidationResult` evidence. Quality gates preserve rows and Schema; blocking violations raise `QualityGateError`, while technical adapter/execution failures remain distinct.

LOT-16 makes logical derivation inspectable without executing data. `TransformationLineage` records logical Dataset derivation, exact field ancestry for built-in transformations, and operational field dependencies such as filtering, grouping, joining, ordering, window partition/order, deduplication and quality checks. `ResourceReference` linkage remains declarative, while `LineageImpactAnalyzer` provides transitive upstream/downstream impact traversal.

LOT-17 makes runtime evidence first-class. Every `TransformationRuntime.execute()` allocates a distinct `TransformationExecutionId`, propagates an independent `CorrelationContext`, fingerprints the compiled `LogicalPlan`, records a `TransformationExecution`, and produces an `ExecutionManifest`. Structured `FailureEvidence`, `Diagnostic`, bounded provider-retry evidence, explicit `UNKNOWN_OUTCOME`, cancellation semantics, lifecycle events, low-cardinality metrics and trace spans are available without parsing logs. Telemetry remains best-effort: sink failures become diagnostics and never cause transformation replay.

LOT-18 introduces the optional PyArrow backend without changing the canonical Domain model. `PyArrowDatasetHandle` accepts `Table` and `RecordBatch`, Arrow Schema inspection maps nested/temporal types back to logical `Schema`, and the adapter advertises only capabilities backed by contract tests. Arrow remains an eager physical engine in this lot. Pandas ↔ Arrow and Polars ↔ Arrow conversions go through an explicit interchange API with strict-by-default lossiness policy and structured diagnostics.

LOT-19 adds DuckDB as the first relational SQL execution backend. `DuckDBPlanCompiler` lowers the engine-neutral `LogicalPlan` to parameterized CTE-backed SQL, values remain separate from SQL text, identifiers are quoted safely, and join/aggregate/window semantics are qualified against the existing Pandas contract. `DuckDBAdapter` distinguishes framework-owned from caller-owned connections, never commits implicitly, supports Arrow binding, eager and lazy relational execution, and exposes native `EXPLAIN` without introducing SQL into the Domain model.

LOT-20 closes the `0.4.x` physical-data line with explicit Reader/Writer ports around portable `ResourceReference` values. The local reference profile supports CSV, JSONL, Parquet and Arrow IPC; Parquet scans can push projection/predicate work to the source and prune Hive partitions, while non-Parquet post-scan work is reported explicitly. `TransformationRuntime` can resolve resource-backed inputs and materialize bound outputs without moving I/O into `TransformationPlan` or `LogicalPlan`. `CredentialReference` contains identifiers only, write modes remain physical storage semantics, and uncertain side effects preserve `UNKNOWN_OUTCOME` / reconciliation-required evidence.

LOT-21 introduces versioned, safe, deterministic wire contracts. `pytransformkit.serialization` provides explicit codecs for DataType, Field, Schema, Expression, TransformationPlan, LogicalPlan, ResourceReference, TransformationExecutionReference, lineage, diagnostics and execution manifests. Canonical JSON uses UTF-8/NFC text, deterministic key ordering and explicit type tags from a closed semantic registry; decoders reject duplicate keys, unknown semantic tags, unsupported versions, non-standard numbers, oversized/deep payloads and arbitrary Python object reconstruction. Plan/expression fingerprints remain semantic rather than identity-based, migrations are explicit, and golden fixtures freeze representative v1 bytes.

LOT-22 adds an engine-neutral `LogicalOptimizer` while preserving the public `LogicalPlan → LogicalPlan` contract. Stable rewrites cover constant folding, boolean simplification, safe predicate pushdown, projection pruning and dead-node elimination. Common-expression analysis, safe-fusion hints and materialization-boundary analysis produce explicit diagnostics rather than physical plans. Every rewrite carries rule provenance, optimization can be disabled, output Schemas are re-resolved after rewrites, lineage equivalence is regression-tested, and Pandas plus Hypothesis contracts prove representative semantic equivalence. No public `OptimizedLogicalPlan` is introduced.

LOT-23 closes the `0.5.x` extension line with the qualified `pytransformkit.plugins` surface. `PluginRegistry.discover()` enumerates entry-point metadata only; plugin modules are imported exclusively by explicit `activate(plugin_id)`. `PluginCompatibility` declares machine-checkable framework/protocol ranges, while EngineAdapter, Reader/Writer, ResourceResolver, FunctionExtension, OptimizerRule and TelemetrySink form the public extension contracts. Registries reject duplicates by default, can be frozen after configuration, and plugin metadata remains outside the safe wire semantic registry so deserialization cannot activate code.

LOT-24 publishes the cross-engine qualification baseline in `pytransformkit.conformance` and `docs/ENGINE_CONFORMANCE_MATRIX.md`. Pandas and Polars are the STABLE mandatory V1 engines; PyArrow and DuckDB remain deliberately PROVISIONAL for their qualified subsets. The release gate covers NULL/NaN, numeric promotion, Decimal, timezone/nested values, Unicode, ordering, duplicates, empty data, joins, aggregates, windows, quality, lineage, serialization, explicit capability failures and no hidden fallback. A canonical Customer 360 TransformationPlan is executed unchanged on Pandas and Polars, including Polars lazy execution, with equivalent normalized output, transitive field lineage, quality evidence, canonical serialization and Parquet ResourceReference handoff.

LOT-25 makes performance evidence reproducible instead of anecdotal. The `benchmarks/` harness measures planning, optimizer and expression overhead, stable-engine execution, native memory amplification, Polars eager/lazy behavior, Pandas/Polars ↔ Arrow interchange, DuckDB materialization boundaries, Parquet pushdown, lineage and telemetry. CI applies explicit absolute and relative regression budgets and uploads a JSON report. The first qualified `0.7.0` baseline is committed under `benchmarks/baselines/0.7.0-ci.json`; performance budgets remain regression tripwires rather than public latency SLAs.

### Runtime and engines

Runtime input is expressed through `InputBinding`, separating logical Dataset values from physical native values. The runtime resolves one explicitly requested engine from `EngineRegistry`; there is no implicit engine fallback. Runtime identity and correlation are distinct: a `TransformationExecutionId` identifies one semantic execution, while `CorrelationId` can connect that execution to surrounding PyKit or external work.

Pandas, Polars, PyArrow, and DuckDB are optional extras. Pandas and Polars implement the broad relational, analytical, reshape, temporal and quality contracts. PyArrow exposes the explicitly qualified LOT-18 eager columnar subset plus interchange bridges. DuckDB exposes the LOT-19 relational SQL subset, including joins, set operations, aggregates, analytical windows, Arrow interchange and lazy relational execution. Cross-engine contracts verify the semantics claimed by each adapter; unsupported capabilities remain explicit rather than silently downgraded.

Public engine namespaces are available under:

~~~text
pytransformkit.engines
pytransformkit.adapters.pandas
pytransformkit.adapters.polars
pytransformkit.adapters.pyarrow
pytransformkit.adapters.duckdb
pytransformkit.readers
pytransformkit.writers
pytransformkit.serialization
pytransformkit.planning
pytransformkit.runtime
pytransformkit.diagnostics
pytransformkit.plugins
pytransformkit.conformance
~~~

## Declarative Schema authoring (1.1)

PyTransformKit 1.1 adds a stable YAML authoring layer for the canonical Domain
`Schema` model. Install the optional capability explicitly:

~~~bash
pip install "pytransformkit[yaml]"
~~~

Then load a human-authored schema:

~~~yaml
version: 1
schema:
  name: customers
  fields:
    - name: customer_id
      type: int64
      nullable: false
    - name: status
      type: string
      nullable: true
~~~

~~~python
from pytransformkit.schema_io import load_schema

schema = load_schema("schemas/customers.yml")
~~~

Or emit canonical YAML from a Python `Schema`:

~~~python
from pytransformkit.schema_io import dumps_schema

yaml_text = dumps_schema(schema, name="customers")
~~~

The stable `pytransformkit.schema_io` namespace exposes exactly eight helpers:
`load_schema`, `loads_schema`, `load_schemas`, `loads_schemas`,
`dump_schema`, `dumps_schema`, `dump_schemas`, and `dumps_schemas`.

Declarative YAML is a human-authoring format, not a replacement for the
versioned `SchemaCodec` JSON wire contract. The existing
`pytransformkit.schema` wire contract remains version 1 and byte-compatible.

The core package does not depend on PyYAML. Without the `yaml` extra,
`pytransformkit.schema_io` remains importable and YAML operations fail
explicitly with `PTK-DECL-010`.

See
`docs/specifications/41_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_GETTING_STARTED.md`
and
`docs/specifications/42_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_REFERENCE_EXAMPLES.md`
for the complete guide and executable examples.

## Quick example

~~~python
import pandas as pd

from pytransformkit import InputBinding, TransformationPlan, TransformationRuntime
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.engines import EngineRegistry
from pytransformkit.functions import col

schema = Schema(
    fields=(
        Field("customer_id", IntegerType(), nullable=False),
        Field("status", StringType(), nullable=False),
    )
)

builder = TransformationPlan.builder("active_customers")
customers = builder.input("customers", schema=schema)
active = builder.filter(
    "active_only",
    source=customers,
    where=col("status") == "ACTIVE",
)
plan = builder.output("result", active).build()

registry = EngineRegistry()
registry.register(PandasEngineAdapter())

runtime = TransformationRuntime(engines=registry)

result = runtime.execute(
    plan,
    engine="pandas",
    inputs={
        "customers": InputBinding.from_native(
            "customers",
            pd.DataFrame(
                {
                    "customer_id": [1, 2],
                    "status": ["ACTIVE", "INACTIVE"],
                }
            ),
            engine="pandas",
        )
    },
)

print(result.output_handle.dataframe)
~~~

## Revised roadmap to 1.0.0

The current normative implementation roadmap is:

`docs/specifications/PYTRANSFORMKIT_V1_REVISED_IMPLEMENTATION_ROADMAP.md`

The historical `docs/ROADMAP_LOT_11_TO_1_0.md` remains useful as project history but no longer governs future implementation where it conflicts with the PyKit Ecosystem V2 architecture.

Current roadmap status:

- V1 stable line: **LOT-00 → LOT-28 complete**;
- Declarative Schema 1.1 line: **LOT-29 → LOT-41 complete**;
- Current lot: **LOT-42 — Documentation and RC Closure**;
- Final 1.1 lot: **LOT-43 — Declarative Schema Stable Release Closure**.

## Development

~~~bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"

ruff check .
ruff format --check .
mypy src/pytransformkit
pytest
python -m build
~~~

On Windows PowerShell:

~~~powershell
.venv\Scripts\Activate.ps1
~~~

## Architectural invariants

- No engine-specific types in the Domain.
- A logical Dataset never stores native engine data.
- TransformationPlan owns logical transformation meaning, not workflow execution.
- No hidden engine fallback.
- Optional engines remain optional dependencies.
- Physical data enters execution through explicit bindings.
- ResourceReference is not a live physical handle.
- Public semantic behavior is test-driven.
- A capability is not supported until its contract tests pass.

## Documentation

Start with:

- `docs/GETTING_STARTED.md` — canonical transformation authoring and execution path;
- `docs/specifications/41_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_GETTING_STARTED.md` — declarative Schema quick start;
- `docs/specifications/42_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_REFERENCE_EXAMPLES.md` — declarative Schema reference examples;
- `docs/ENGINE_CONFORMANCE_MATRIX.md` — published engine stability and semantic qualification matrix;
- `benchmarks/README.md` — LOT-25 performance harness, budgets and qualified `0.7.0` baseline;
- `notebooks/00 - Local Experimentation.ipynb` — interactive first experiment;
- `scripts/00_local_experimentation.py` — executable equivalent;
- `docs/specifications/PYTRANSFORMKIT_V1_TARGET_ARCHITECTURE.md` — V1 target architecture;
- `docs/specifications/PYTRANSFORMKIT_V1_PUBLIC_API_SPEC.md` — V1 public API contract;
- `docs/specifications/PYTRANSFORMKIT_V1_REVISED_IMPLEMENTATION_ROADMAP.md` — normative roadmap to 1.0.0.

## License

License selection is pending and should be made explicitly before a public stable release.
