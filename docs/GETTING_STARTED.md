# Getting Started with PyTransformKit

PyTransformKit lets you define engine-neutral transformation semantics once, compile them into a LogicalPlan, and execute them explicitly through supported physical engines.

The current development line targets **0.3.0a1** and includes LOT-15: transformation-owned data quality and validation on top of the V1 transformation-semantics baseline.

The canonical path is:

~~~text
Schema
  ↓
TransformationPlan
  ↓
TransformationCompiler
  ↓
LogicalPlan
  ↓
TransformationRuntime
  ↓
InputBinding
  ↓
EngineRegistry
  ├── PandasEngineAdapter
  └── PolarsEngineAdapter
  ↓
TransformationResult
~~~

The former Pipeline / RunPipelineService path is retained only as a pre-V1 compatibility surface.

---

## 1. Clone the repository

~~~bash
git clone https://github.com/tawounfouet/pytransformkit.git
cd pytransformkit
~~~

---

## 2. Create a virtual environment

### Linux / macOS

~~~bash
python -m venv .venv
source .venv/bin/activate
~~~

### Windows PowerShell

~~~powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
~~~

Then upgrade pip:

~~~bash
python -m pip install --upgrade pip
~~~

---

## 3. Install PyTransformKit locally

### Core development environment

~~~bash
pip install -e ".[dev]"
~~~

### Pandas

~~~bash
pip install -e ".[dev,pandas]"
~~~

### Polars

~~~bash
pip install -e ".[dev,polars]"
~~~

### Pandas + Polars

Recommended for local experimentation:

~~~bash
pip install -e ".[dev,pandas,polars]"
~~~

The core package has no mandatory physical-engine dependency.

---

## 4. First TransformationPlan

Start with a logical Schema:

~~~python
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema

schema = Schema(
    fields=(
        Field("customer_id", IntegerType(), nullable=False),
        Field("email", StringType(), nullable=True),
        Field("status", StringType(), nullable=False),
    )
)
~~~

Build the transformation declaration:

~~~python
from pytransformkit import TransformationPlan
from pytransformkit.functions import col, lower, trim

builder = TransformationPlan.builder("customers")

customers = builder.input(
    "customers",
    schema=schema,
)

active = builder.filter(
    "active_customers",
    source=customers,
    where=col("status") == "ACTIVE",
)

normalized = builder.derive(
    "normalize_email",
    source=active,
    field_name="normalized_email",
    expression=lower(trim(col("email"))),
)

selected = builder.select(
    "customer_view",
    source=normalized,
    columns=("customer_id", "normalized_email"),
)

plan = builder.output(
    "customers_out",
    selected,
).build()
~~~

TransformationPlan is immutable after build. The authoring builder is only a construction helper.

---

## 5. Inspect the LogicalPlan before execution

Compilation validates graph structure and propagates Schemas without touching physical data:

~~~python
from pytransformkit.planning import TransformationCompiler

logical_plan = TransformationCompiler().compile(plan)

print(logical_plan.plan_name)
print(logical_plan.input_names)
print(logical_plan.output_names)
print(logical_plan.output_schema.names())
print([node.kind.value for node in logical_plan.nodes])
~~~

LogicalPlan is engine-neutral. It describes what must happen, not how Pandas or Polars will perform it.

---

## 6. Execute with Pandas

Create physical data:

~~~python
import pandas as pd

pandas_df = pd.DataFrame(
    {
        "customer_id": [1, 2, 3],
        "email": [
            " JOHN@EXAMPLE.COM ",
            None,
            " BOB@EXAMPLE.COM ",
        ],
        "status": [
            "ACTIVE",
            "INACTIVE",
            "ACTIVE",
        ],
    }
)
~~~

Register the adapter and create the canonical runtime:

~~~python
from pytransformkit import InputBinding, TransformationRuntime
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.engines import EngineRegistry

registry = EngineRegistry()
registry.register(PandasEngineAdapter())

runtime = TransformationRuntime(
    engines=registry,
)
~~~

Execute explicitly:

~~~python
pandas_result = runtime.execute(
    plan,
    engine="pandas",
    inputs={
        "customers": InputBinding.from_native(
            "customers",
            pandas_df,
            engine="pandas",
        )
    },
)

print(pandas_result.execution_id)
print(pandas_result.engine.id)
print(pandas_result.output_schema.names())
print(pandas_result.output_handle.dataframe)
~~~

There is no implicit engine fallback. If the requested engine is not registered or lacks a required capability, execution fails before physical transformation begins.

---

## 7. Execute the same TransformationPlan with Polars

The logical declaration does not change:

~~~python
import polars as pl

from pytransformkit.adapters.polars import PolarsEngineAdapter

registry.register(PolarsEngineAdapter())

polars_df = pl.DataFrame(
    {
        "customer_id": [1, 2, 3],
        "email": [
            " JOHN@EXAMPLE.COM ",
            None,
            " BOB@EXAMPLE.COM ",
        ],
        "status": [
            "ACTIVE",
            "INACTIVE",
            "ACTIVE",
        ],
    }
)

polars_result = runtime.execute(
    plan,
    engine="polars",
    inputs={
        "customers": InputBinding.from_native(
            "customers",
            polars_df,
            engine="polars",
        )
    },
)

print(polars_result.output_handle.frame)
~~~

The same TransformationPlan, Expression AST and LogicalPlan semantics are reused.

---

## 8. Polars lazy execution

Polars explicitly advertises lazy capability:

~~~python
from pytransformkit.runtime import ExecutionMode

lazy_result = runtime.execute(
    plan,
    engine="polars",
    inputs={
        "customers": InputBinding.from_native(
            "customers",
            polars_df.lazy(),
            engine="polars",
        )
    },
    mode=ExecutionMode.LAZY,
)

lazy_frame = lazy_result.output_handle.frame

print(lazy_frame)
print(lazy_frame.collect())
~~~

PyTransformKit preserves the lazy physical result instead of materializing it implicitly.

---

## 9. Multi-input relational transformations

LOT-11 introduces portable multi-input relational semantics.

### Join

~~~python
orders_schema = Schema(
    fields=(
        Field("order_id", IntegerType(), nullable=False),
        Field("customer_id", IntegerType(), nullable=False),
        Field("amount", IntegerType(), nullable=False),
    )
)

builder = TransformationPlan.builder("customer_orders")

customers = builder.input(
    "customers",
    schema=schema,
)

orders = builder.input(
    "orders",
    schema=orders_schema,
)

joined = builder.join(
    "customer_orders",
    left=customers,
    right=orders,
    how="left",
    on=(("customer_id", "customer_id"),),
    right_suffix="_order",
)

relational_plan = builder.output(
    "result",
    joined,
).build()
~~~

Supported join types currently include:

- inner;
- left;
- right;
- full;
- semi;
- anti;
- cross.

Join semantics include explicit key mapping, deterministic output-schema collision handling and configurable NULL key behavior.

### Set operations

TransformationPlanBuilder also exposes:

~~~text
union
intersect
except_
~~~

Set operations require compatible logical Schemas.

---

## 10. Aggregation and grouping

LOT-12 adds a dedicated aggregate-expression context. Aggregate functions are authored through `pytransformkit.functions`:

~~~python
from pytransformkit import functions as fn
from pytransformkit.functions import col

builder = TransformationPlan.builder("order_stats")

orders = builder.input(
    "orders",
    schema=orders_schema,
)

stats = builder.aggregate(
    "order_stats",
    source=orders,
    group_by=(
        col("customer_id"),
    ),
    metrics={
        "order_count": fn.count(),
        "paid_order_count": fn.count(col("order_id")),
        "distinct_status_count": fn.count_distinct(col("status")),
        "revenue": fn.sum(col("amount")),
        "minimum_amount": fn.min(col("amount")),
        "maximum_amount": fn.max(col("amount")),
        "mean_amount": fn.mean(col("amount")),
    },
)

aggregate_plan = builder.output(
    "stats",
    stats,
).build()
~~~

The aggregate context is validated during logical compilation. Row-level expressions cannot embed aggregate functions accidentally, and aggregate arguments cannot contain nested aggregate expressions.

Current NULL semantics are explicit:

- `count()` counts rows;
- `count(expr)` counts non-null values;
- `count_distinct(expr)` counts distinct non-null values;
- `sum`, `min`, `max`, and `mean` ignore null inputs;
- groups containing only null values yield null for `sum`, `min`, `max`, and `mean`;
- global aggregation over an empty dataset returns one row, with counts equal to zero and nullable aggregates equal to null.

Pandas and Polars are qualified against the same normalized semantics.

---

## 11. Analytical windows

LOT-13 adds a dedicated `pytransformkit.window` namespace for portable analytical expressions.

~~~python
from pytransformkit import window
from pytransformkit.functions import col

ordered = (
    window.partition_by("customer_id")
    .order_by("ordered_at")
)

ranked = builder.derive(
    "ranked_orders",
    source=orders,
    field_name="order_number",
    expression=window.row_number().over(ordered),
)

cumulative = ordered.rows_between(
    window.unbounded_preceding(),
    window.current_row(),
)

with_revenue = builder.derive(
    "cumulative_revenue",
    source=ranked,
    field_name="cumulative_revenue",
    expression=window.sum(col("amount")).over(cumulative),
)
~~~

The current portable analytical vocabulary includes:

- `row_number()`;
- `rank()`;
- `dense_rank()`;
- `lag()`;
- `lead()`;
- window `count()`, `sum()`, `min()`, `max()`, and `mean()` / `avg()`;
- partition-wide aggregates;
- cumulative ROWS frames from unbounded preceding to current row;
- moving ROWS frames from N preceding to current row.

Ordering is explicit for order-sensitive functions. Window specifications are immutable, and partition/order dependencies are available to the logical dependency model.

Arbitrary ROWS frames and RANGE frames already have explicit logical representations and engine capabilities. Pandas and Polars currently do not advertise these capabilities, so such plans fail during compatibility validation instead of falling back silently.

Polars supports the qualified window subset in eager and lazy execution.

---

## 12. Reshaping, nested data and temporal semantics

LOT-14 completes the 0.2.x transformation-semantics line.

### Reshaping

TransformationPlanBuilder exposes deterministic reshape operations:

~~~python
from pytransformkit.domain.transformations.reshaping import PivotAggregation

pivoted = builder.pivot(
    "revenue_by_status",
    source=orders,
    index=("customer_id",),
    columns="status",
    values="amount",
    categories=("PAID", "OPEN"),
    aggregation=PivotAggregation.SUM,
)

unpivoted = builder.unpivot(
    "quarter_rows",
    source=wide_orders,
    id_vars=("customer_id",),
    value_vars=("q1", "q2"),
    variable_name="quarter",
    value_name="revenue",
)

exploded = builder.explode(
    "one_tag_per_row",
    source=customers,
    field="tags",
)

flattened = builder.flatten(
    "customer_profile",
    source=customers,
    field="profile",
)
~~~

Pivot categories are declared explicitly so output Schemas remain deterministic without inspecting runtime data.

### Nested Struct paths

Logical Schemas can contain List, Struct, Map and Duration types. Portable nested access is currently defined for Struct paths:

~~~python
city = builder.derive(
    "customer_city",
    source=customers,
    field_name="city",
    expression=col("profile.address.city"),
)
~~~

Nested nullability propagates through the complete path.

### Temporal expressions

Portable temporal functions are available through pytransformkit.functions:

~~~python
from pytransformkit import functions as fn

year_value = fn.year(col("event_at"))
event_date = fn.to_date(col("event_at"))

normalized = fn.normalize_timestamp(
    col("event_at"),
    timezone="UTC",
    unit="us",
)

paris_time = fn.convert_timezone(
    col("event_at"),
    "Europe/Paris",
)

elapsed = fn.duration_between(
    col("started_at"),
    col("finished_at"),
    unit="s",
)
~~~

Timestamp normalization and timezone conversion are separate operations. Duration units are logical PyTransformKit semantics; adapters may lower them to a different native precision while preserving the declared logical result.

Pandas and Polars pass the same LOT-14 cross-engine suite, and the supported reshape subset also runs through Polars LazyFrame execution.

---

## 13. Data quality and validation

LOT-15 introduces transformation-owned quality checkpoints through the public `pytransformkit.quality` namespace.

~~~python
from pytransformkit import quality
from pytransformkit.domain.quality import ValidationPolicy, ValidationSpec
from pytransformkit.functions import col

quality_spec = ValidationSpec(
    name="customers_quality",
    policy=ValidationPolicy.WARN_ONLY,
    rules=(
        quality.not_null("customer_id"),
        quality.unique("customer_id"),
        quality.regex("email", r"[^@]+@[^@]+\\.[^@]+"),
        quality.allowed_values(
            "status",
            ("ACTIVE", "INACTIVE"),
        ),
        quality.range_(
            "score",
            minimum=0.0,
            maximum=100.0,
        ),
        quality.row_count(minimum=1),
        quality.expression(
            col("score") >= 0,
            name="score_non_negative",
        ),
    ),
)

validated = builder.validate(
    "validate_customers",
    source=customers,
    spec=quality_spec,
)
~~~

A QualityGate preserves the logical rows and Schema. It produces structured validation evidence rather than silently filtering invalid records.

The supported policies are:

~~~text
FAIL_FAST
    first rejected rule raises QualityGateError

FAIL_AT_END
    all rules are evaluated before a blocking QualityGateError

WARN_ONLY
    execution continues and ValidationResult records failed rules

IGNORE
    rules are skipped and an ignored, non-blocking ValidationResult is emitted
~~~

Rules use a strict zero-violation threshold by default. `ValidationThreshold` can also declare an absolute violation budget, a violation-rate budget, or a rate-only budget.

Successful or non-blocking execution exposes evidence on `TransformationResult`:

~~~python
result = runtime.execute(...)

quality_result = result.validation("customers_quality")

print(quality_result.passed)
print(quality_result.failed_rule_count)

for rule_result in quality_result.rule_results:
    print(
        rule_result.rule_name,
        rule_result.violation_count,
        rule_result.violation_rate,
    )
~~~

Data-quality rejection is represented by `QualityGateError`; adapter and execution failures remain separate technical failures.

SchemaValidation compares the logical transformation Schema at the gate. It does not replace PyIngestKit source-decoding or ingestion-publication contracts.

On Polars LazyFrame inputs, LOT-15 materializes data when quality evidence requires physical evaluation, while preserving a lazy output handle for continued execution.

---

## 14. InputBinding, ResourceReference and OutputBinding

InputBinding separates the logical Dataset model from physical data supplied at runtime.

Native in-memory bindings remain supported:

~~~python
binding = InputBinding.from_native(
    "customers",
    pandas_df,
    engine="pandas",
)
~~~

LOT-20 also supports explicit resource-backed bindings through a configured Reader/Writer registry:

~~~python
from pytransformkit import (
    InputBinding,
    OutputBinding,
    ResourceReference,
    RetrySafety,
    WriteMode,
)
from pytransformkit.application.io import ResourceIORegistry
from pytransformkit.readers import LocalFileReader
from pytransformkit.writers import LocalFileWriter

resources = ResourceIORegistry()
resources.register_reader(LocalFileReader("./data"))
resources.register_writer(LocalFileWriter("./data"))

runtime = TransformationRuntime(
    engines=registry,
    resources=resources,
)

result = runtime.execute(
    plan,
    engine="pandas",
    inputs={
        "customers": InputBinding.from_resource(
            "customers",
            ResourceReference(
                scheme="file",
                locator="customers.csv",
                media_type="text/csv",
            ),
        )
    },
    outputs={
        "result": OutputBinding.to_resource(
            "result",
            ResourceReference(
                scheme="file",
                locator="active_customers.parquet",
                media_type="application/vnd.apache.parquet",
            ),
            mode=WriteMode.CREATE_NEW,
            retry_safety=RetrySafety.SAFE,
        )
    },
)
~~~

The local reference profile supports CSV, JSONL, Parquet and Arrow IPC. Resource resolution remains an explicit runtime concern: `TransformationPlan` and `LogicalPlan` stay side-effect free, a `ResourceReference` remains distinct from a process-local `PhysicalHandle`, and physical writes never imply governed publication. Uncertain writes preserve `UNKNOWN_OUTCOME` so callers reconcile before retrying.

---

## 15. Transformations currently available

Current portable Transformation semantics include:

- select;
- drop;
- rename;
- filter;
- limit;
- distinct;
- cast;
- derive;
- sort;
- deduplicate;
- join;
- union;
- intersect;
- except;
- aggregate/group by;
- analytical windows;
- pivot;
- unpivot;
- explode;
- flatten;
- quality gates.

The Expression DSL currently includes:

- col();
- lit();
- comparisons;
- arithmetic operators;
- logical operators;
- is_null();
- is_not_null();
- lower();
- upper();
- trim();
- concat();
- count();
- count_distinct();
- sum();
- min();
- max();
- mean() / avg();
- window row/rank/offset and aggregate expressions;
- nested Struct field references;
- year/month/day/hour/minute/second extraction;
- date conversion;
- timestamp normalization;
- timezone conversion;
- duration calculation.

---

## 16. Logical and field lineage

LOT-16 adds static lineage analysis to the engine-neutral plan model. Lineage is derived from transformation semantics; it does not execute data and it does not depend on Pandas, Polars or another physical engine.

~~~python
from pytransformkit import lineage

evidence = lineage.analyze(plan)

customers_ref = evidence.input("customers")
result_ref = evidence.output("result")

for edge in evidence.field_edges:
    print(
        edge.source,
        edge.derivation,
        edge.target,
        edge.confidence,
    )

for dependency in evidence.dependencies:
    print(
        dependency.kind,
        dependency.field,
        dependency.target_dataset,
    )
~~~

PyTransformKit deliberately distinguishes value ancestry from operational dependencies. For example, a filter on `status` changes row membership but does not falsely make every output field derived from `status`. Likewise, sort keys, join keys, grouping keys, window partition/order keys, deduplication keys and quality-rule fields remain explicit dependencies.

Built-in declarative transformations currently produce `EXACT` lineage when semantics are statically knowable. The stable confidence vocabulary is:

~~~text
EXACT
DECLARED
INFERRED
PARTIAL
UNKNOWN
~~~

The current built-in lineage model covers direct projection, rename, cast, expression derivation, joins, aggregation, analytical windows, set operations, pivot/unpivot, explode/flatten and quality gates.

Portable resources may be connected explicitly without resolving or opening them:

~~~python
from pytransformkit import lineage
from pytransformkit import ResourceReference

evidence = lineage.analyze(
    plan,
    input_resources={
        "customers": ResourceReference(
            scheme="file",
            locator="/data/customers.parquet",
        ),
    },
)
~~~

This is logical traceability, not ingestion provenance. PyTransformKit does not create a governed DatasetVersion or take ownership of RAW/source provenance.

Impact analysis is available over the typed lineage projection:

~~~python
from pytransformkit.lineage import FieldReference, LineageImpactAnalyzer

impact = LineageImpactAnalyzer()

target = FieldReference.of(
    evidence.output("result"),
    "normalized_email",
)

upstream = impact.upstream_fields(evidence, target)
~~~

Because lineage is derived from the logical plan, running the same plan through Pandas or Polars does not create different logical ancestry.

---

## 17. Runtime identity, evidence and observability

LOT-17 makes each call to `TransformationRuntime.execute()` an explicitly identifiable semantic execution.

~~~python
from pytransformkit.runtime import CorrelationContext, CorrelationId

correlation = CorrelationContext(
    correlation_id=CorrelationId.new(),
    workflow_run_id="workflow-42",
    task_attempt_id="attempt-3",
)

result = runtime.execute(
    plan,
    engine="pandas",
    inputs=bindings,
    correlation=correlation,
)
~~~

Execution identity and correlation identity are deliberately different:

~~~text
CorrelationId
    groups related work across boundaries
          │
          └──► TransformationExecutionId
                 identifies exactly one PyTransformKit execution
~~~

A successful result now exposes structured runtime evidence:

~~~python
print(result.execution_id)
print(result.status)
print(result.correlation.correlation_id)
print(result.plan_fingerprint)
print(result.execution.engine)
print(result.diagnostics)
print(result.lineage)
print(result.manifest)
~~~

The execution manifest is portable evidence. It records the execution identity, correlation context, terminal status, timestamps, plan identity/fingerprint, engine/adapter identity, input/output names, diagnostic codes and bounded provider-retry evidence. It does not serialize active engine handles or raw credentials.

### Structured failures

Expected PyTransformKit failures retain their typed exception while receiving structured evidence:

~~~python
from pytransformkit.errors import PyTransformKitError

try:
    runtime.execute(
        plan,
        engine="pandas",
        inputs=bindings,
    )
except PyTransformKitError as error:
    print(error.failure_evidence)
    print(error.execution)
    print(error.execution_manifest)
    print(error.diagnostics)
~~~

`UNKNOWN_OUTCOME` is not flattened into ordinary failure. When PyTransformKit cannot establish whether an external side effect happened, the evidence marks reconciliation as required rather than encouraging an unsafe blind retry.

### Provider retries versus workflow retries

PyTransformKit may record bounded engine/provider retry evidence, but `TransformationRuntime` does not become a workflow retry engine:

~~~text
engine/provider retry
        └── PyTransformKit may own and disclose

workload/task retry
        └── outside PyTransformKit ownership
~~~

This keeps retry scope explicit and avoids accidental retry stacking with PyWorkflowKit or another orchestrator.

### Cancellation

A process-local `CancellationToken` can signal cancellation:

~~~python
from pytransformkit.runtime import CancellationToken

token = CancellationToken()
token.request()

runtime.execute(
    plan,
    engine="pandas",
    inputs=bindings,
    cancellation=token,
)
~~~

A cancellation request and a confirmed cancellation are separate facts. `EngineDescriptor.cancellation_support` declares whether an engine advertises no in-flight support, cooperative support, or provider-native support.

### Telemetry

A runtime may receive a vendor-neutral telemetry sink:

~~~python
runtime = TransformationRuntime(
    engines=registry,
    telemetry=my_sink,
)
~~~

Lifecycle events, metrics and trace spans are emitted through the sink. Default metric labels remain low-cardinality: execution IDs, correlation IDs, full URIs and raw error messages are not default metric labels.

Telemetry delivery is best-effort. If the telemetry backend fails, PyTransformKit records a warning diagnostic and does not replay the transformation.

---


### Versioned serialization and canonical wire contracts

LOT-21 adds a side-effect-free serialization boundary for portable logical state:

~~~python
from pytransformkit.serialization import (
    LogicalPlanCodec,
    TransformationPlanCodec,
)

plan_codec = TransformationPlanCodec()

payload = plan_codec.to_json(plan)
same_plan = plan_codec.from_json(payload)

logical = TransformationCompiler().compile(plan)

logical_codec = LogicalPlanCodec()

canonical_bytes = logical_codec.to_bytes(logical)
fingerprint = logical_codec.fingerprint(logical)
~~~

Every top-level wire value uses an explicit envelope:

~~~json
{
  "contract": "pytransformkit.transformation_plan",
  "contract_version": 1,
  "payload": {}
}
~~~

The wire version is deliberately independent from the PyTransformKit package version. Decoding is strict: duplicate JSON keys, unknown semantic type tags, unknown fields, unsupported future versions, oversized/deep payloads and non-standard numeric values fail explicitly.

The decoder uses a closed semantic registry and never imports a Python module or reconstructs an arbitrary class based on payload text. Callbacks, closures and other executable Python state fail with `NonPortableValueError`; pickle/cloudpickle/dill are not supported durable formats.

Shared boundaries can use the minimal execution reference instead of serializing a full runtime object:

~~~python
from pytransformkit.runtime import TransformationExecutionReference
from pytransformkit.serialization import TransformationExecutionReferenceCodec

reference = TransformationExecutionReference.from_execution(
    result.execution,
)

wire = TransformationExecutionReferenceCodec().to_json(reference)
~~~

Golden fixtures under `tests/fixtures/wire/` freeze representative v1 canonical bytes for compatibility testing.



### Logical optimization

LOT-22 introduces an explicit engine-neutral optimization step:

~~~python
from pytransformkit.planning import (
    LogicalOptimizer,
    TransformationCompiler,
)

logical = TransformationCompiler().compile(plan)

optimizer = LogicalOptimizer()
optimized = optimizer.optimize(logical)
~~~

The public type does not change:

~~~text
LogicalPlan
    ↓ optimize
LogicalPlan
~~~

To inspect optimizer evidence:

~~~python
result = optimizer.optimize_with_report(logical)

print(result.report.original_fingerprint)
print(result.report.optimized_fingerprint)

for application in result.report.applications:
    print(application.rule_id, application.affected_node_ids)

for diagnostic in result.report.diagnostics:
    print(diagnostic.code, diagnostic.summary)
~~~

Stable rewrite rules currently include constant folding, boolean simplification, predicate pushdown through qualified Select/Sort boundaries, projection pruning across successive selections and dead-node elimination. Common-expression analysis, fusion opportunities and materialization boundaries are reported as diagnostics rather than converted into engine-specific physical instructions.

Optimization can be disabled explicitly:

~~~python
optimizer = LogicalOptimizer(enabled=False)

assert optimizer.optimize(logical) is logical
~~~

Every structural rewrite re-resolves logical Schemas. Engine adapters still own physical lowering, and lineage tests verify that optimized outputs preserve the same transitive logical input sources.



### Explicit plugins and extension registries

LOT-23 separates plugin discovery from activation:

~~~python
from pytransformkit.plugins import PluginRegistry

plugins = PluginRegistry.discover()

# Discovery only inspects entry-point metadata.
print(plugins.list())

# Plugin code is imported only here.
plugins.activate("my-engine-plugin")

# Freeze all owned registries after configuration.
plugins.freeze()
~~~

The canonical entry-point group is:

~~~text
pytransformkit.plugins
~~~

A plugin declares immutable compatibility metadata through `PluginDescriptor` and `PluginCompatibility`. Compatibility covers both the PyTransformKit framework version range and the plugin protocol version.

Activation receives a `PluginActivationContext` containing explicit registries for engines, Reader/Writer I/O, ResourceResolver implementations, named functions, optimizer rules and telemetry sinks. Duplicate registrations fail by default, and frozen registries reject further mutation.

Optimizer extensions are opt-in:

~~~python
from pytransformkit.planning import LogicalOptimizer

optimizer = LogicalOptimizer(
    extension_rules=plugins.context.optimizer_rules.rules(),
)
~~~

Plugin descriptors and provider objects are intentionally outside the safe serialization registry. A valid wire payload can describe transformation semantics or portable references, but cannot discover, import or activate plugin code.


## 18. Run the local experimentation script

The repository includes:

~~~text
scripts/
└── 00_local_experimentation.py
~~~

Run it from the repository root:

~~~bash
python "scripts/00_local_experimentation.py"
~~~

It demonstrates:

- Schema creation;
- TransformationPlan authoring;
- LogicalPlan compilation;
- Pandas execution;
- Polars eager execution;
- cross-engine result comparison;
- Polars lazy execution.

---

## 19. Run the notebook

An interactive equivalent is available at:

~~~text
notebooks/
└── 00 - Local Experimentation.ipynb
~~~

Start your preferred Jupyter frontend and open the notebook from the repository root.

---

## 20. Run the test suites

### Complete default suite

~~~bash
pytest
~~~

### Pandas contracts

~~~bash
pytest tests/contract/engines/pandas -ra
~~~

### Polars contracts

~~~bash
pytest tests/contract/engines/polars -ra
~~~

### Cross-engine contracts

~~~bash
pytest tests/contract/cross_engine -ra
~~~

### Static quality checks

~~~bash
ruff check .
ruff format --check .
mypy src/pytransformkit
python -m build
~~~

The CI matrix currently verifies Python 3.11, 3.12, 3.13 and 3.14 plus dedicated Pandas, Polars and cross-engine contracts.

---

## 21. What comes next

The revised V1 roadmap continues with:

- **LOT-24** — Cross-Engine Conformance + Customer 360;
- **LOT-25** — Performance Qualification;
- **LOT-26** — Public API / Security / Migration Freeze;
- **LOT-27** — 1.0 Release Candidate;
- **LOT-28** — 1.0.0 Stable.

The normative roadmap is:

~~~text
docs/specifications/PYTRANSFORMKIT_V1_REVISED_IMPLEMENTATION_ROADMAP.md
~~~

---

## 22. Recommended experimentation workflow

While PyTransformKit is pre-1.0:

1. define the logical input Schema;
2. author a TransformationPlan without native engine objects;
3. compile it into LogicalPlan;
4. inspect propagated output Schemas;
5. bind physical inputs explicitly;
6. execute against Pandas;
7. execute the same plan against Polars;
8. compare normalized semantic results;
9. turn every discovered ambiguity into a regression or conformance test.

This keeps PyTransformKit driven by transformation meaning rather than by any single physical engine API.
