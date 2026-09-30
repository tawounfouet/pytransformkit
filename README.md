# PyTransformKit

**Define transformations once. Execute them anywhere.**

PyTransformKit is an engine-agnostic Python framework for defining typed, composable data transformations independently from their physical execution engine.

> Status: early pre-1.0 implementation. Public APIs may still evolve while the V1 contracts are being qualified.

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

The current development line targets **0.4.0a1**.

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

### Runtime and engines

Runtime input is expressed through `InputBinding`, separating logical Dataset values from physical native values. The runtime resolves one explicitly requested engine from `EngineRegistry`; there is no implicit engine fallback. Runtime identity and correlation are distinct: a `TransformationExecutionId` identifies one semantic execution, while `CorrelationId` can connect that execution to surrounding PyKit or external work.

Pandas, Polars, and PyArrow are optional extras. Pandas and Polars implement the relational, aggregation, analytical-window, reshape, nested-Struct, temporal and quality contracts. PyArrow currently exposes the explicitly qualified LOT-18 eager columnar subset plus interchange bridges. Dedicated Pandas/Polars cross-engine tests verify semantic equivalence for joins, set operations, grouped/global aggregates, ranking, offsets, cumulative and moving windows, reshape, nested fields, temporal operations, quality evidence, NULL handling and capability failures. Logical lineage remains engine-neutral, while PyArrow capabilities stay conservative until broader conformance is proven.

Public engine namespaces are available under:

~~~text
pytransformkit.engines
pytransformkit.adapters.pandas
pytransformkit.adapters.polars
pytransformkit.adapters.pyarrow
pytransformkit.planning
pytransformkit.runtime
pytransformkit.diagnostics
~~~

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

Current count:

- Total roadmap: **29 lots** (`LOT-00` → `LOT-28`)
- Completed after LOT-18: **19 lots** (`LOT-00` → `LOT-18`)
- Remaining: **10 lots** (`LOT-19` → `LOT-28`)
- Next lot: **LOT-19 — DuckDB Adapter and Relational SQL Backend**
- Final lot: **LOT-28 — PyTransformKit 1.0.0 Stable Release**

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

- `docs/GETTING_STARTED.md` — canonical V1 authoring and execution path;
- `notebooks/00 - Local Experimentation.ipynb` — interactive first experiment;
- `scripts/00_local_experimentation.py` — executable equivalent;
- `docs/specifications/PYTRANSFORMKIT_V1_TARGET_ARCHITECTURE.md` — V1 target architecture;
- `docs/specifications/PYTRANSFORMKIT_V1_PUBLIC_API_SPEC.md` — V1 public API contract;
- `docs/specifications/PYTRANSFORMKIT_V1_REVISED_IMPLEMENTATION_ROADMAP.md` — normative roadmap to 1.0.0.

## License

License selection is pending and should be made explicitly before a public stable release.
