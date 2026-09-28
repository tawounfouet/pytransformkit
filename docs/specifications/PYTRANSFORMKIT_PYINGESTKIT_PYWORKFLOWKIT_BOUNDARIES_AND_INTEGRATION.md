# PyTransformKit × PyIngestKit × PyWorkflowKit — Boundaries and Integration

> **Status:** Architecture Contract  
> **Date:** 2026-09-28  
> **Scope:** PyTransformKit, PyIngestKit, PyWorkflowKit  
> **Purpose:** Prevent semantic overlap while defining explicit integration boundaries between the three frameworks.

---

## 1. Purpose

This document defines the architectural boundaries between:

- **PyIngestKit** — reliable and traceable data ingestion;
- **PyTransformKit** — engine-agnostic logical data transformation;
- **PyWorkflowKit** — reliable execution of generic dependency graphs.

The objective is not to merge the three projects into one framework.

The objective is to make them composable while preserving one clear owner for every major responsibility.

The governing principle is:

> **Composition is encouraged. Duplicate semantic ownership is forbidden.**

The three frameworks may expose concepts that look structurally similar — such as pipelines, graphs, runs, lineage, validation, events, or adapters — but those concepts belong to different bounded contexts and must not silently converge into competing implementations of the same responsibility.

---

## 2. Architectural summary

The ecosystem is organized into three complementary planes.

```text
┌─────────────────────────────────────────────────────────────┐
│                     PyWorkflowKit                           │
│                                                             │
│                      CONTROL PLANE                          │
│                                                             │
│ workflow • task • dependency • retry • state • recovery    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               │ executes / coordinates
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      PyIngestKit                            │
│                                                             │
│                        DATA PLANE                           │
│                                                             │
│ source • RAW • provenance • version • publish • replay     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               │ may transform through
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    PyTransformKit                           │
│                                                             │
│                 COMPUTE / LOGICAL PLANE                     │
│                                                             │
│ schema • AST • transform • plan • optimizer • engines      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                  ┌────────────┼──────────────┐
                  ▼            ▼              ▼
               Pandas       Polars         DuckDB
                                  \
                                   └──── PyArrow
```

A shorter formulation is:

```text
PyIngestKit
    HOW TO INGEST

PyTransformKit
    HOW TO TRANSFORM DATA

PyWorkflowKit
    HOW TO EXECUTE WORKLOAD DEPENDENCIES RELIABLY
```

---

## 3. Bounded contexts

### 3.1 PyIngestKit

PyIngestKit owns the ingestion lifecycle.

Its canonical responsibility is:

```text
External Source
      ↓
Acquisition
      ↓
Immutable RAW
      ↓
Parsing
      ↓
Validation / Profiling
      ↓
Dataset Version
      ↓
Publication / Target
```

PyIngestKit owns concepts such as:

- source acquisition;
- RAW preservation;
- ingestion provenance;
- parsing of ingestion formats;
- ingestion-level validation;
- reproducible Dataset versions;
- artifact persistence;
- publication pointers;
- ingestion replay;
- target loading;
- idempotent ingestion;
- source-to-dataset traceability.

PyIngestKit does **not** own generic workflow orchestration.

PyIngestKit does **not** own a general engine-agnostic transformation language.

---

### 3.2 PyTransformKit

PyTransformKit owns logical data transformation semantics independently from a physical execution engine.

Its canonical responsibility is:

```text
Logical Dataset
      ↓
Expressions
      ↓
Transformations
      ↓
Logical Pipeline / DAG
      ↓
Logical Plan
      ↓
Engine Adapter
      ↓
Physical Execution
```

PyTransformKit owns concepts such as:

- logical DataTypes;
- Field and Schema semantics;
- logical Dataset identity;
- Expression AST;
- transformation specifications;
- relational semantics;
- grouping and aggregation;
- analytical/window semantics;
- logical Pipeline/DAG;
- LogicalPlan;
- schema propagation;
- field-level lineage;
- transformation-level validation;
- logical optimization;
- engine capability negotiation;
- engine adapters;
- cross-engine semantic conformance;
- portable transformation IR.

PyTransformKit may execute a logical transformation plan.

PyTransformKit must **not** become a general-purpose workflow runtime.

---

### 3.3 PyWorkflowKit

PyWorkflowKit owns reliable execution of generic workloads and their dependency graph.

Its canonical responsibility is:

```text
WorkflowDefinition
       ↓
DependencyGraph
       ↓
ExecutionPlan
       ↓
TaskRun
       ↓
TaskAttempt
       ↓
Executor
       ↓
Runtime Evidence
```

PyWorkflowKit owns concepts such as:

- workflow definitions;
- task definitions;
- operational dependency graphs;
- workflow/task state machines;
- retries;
- retry backoff;
- timeout;
- cancellation;
- concurrency;
- executor capabilities;
- durable runtime state;
- runtime events;
- recovery;
- reconciliation;
- resume;
- execution manifests;
- external workload references;
- workflow execution lineage.

PyWorkflowKit treats PyIngestKit and PyTransformKit workloads as external or embedded workload types.

It must not reproduce their domain semantics.

---

## 4. Responsibility matrix

| Capability | PyIngestKit | PyTransformKit | PyWorkflowKit |
|---|:---:|:---:|:---:|
| External source acquisition | **OWNER** | — | — |
| Immutable RAW | **OWNER** | — | — |
| Ingestion provenance | **OWNER** | — | reference only |
| Parsing for ingestion | **OWNER** | limited physical scan only | — |
| Dataset versioning | **OWNER** | — | reference only |
| Publication lifecycle | **OWNER** | — | coordinate only |
| Historical ingestion replay | **OWNER** | — | coordinate only |
| Target loading | **OWNER** | limited physical write only | coordinate only |
| Schema semantics | consumer | **OWNER** | opaque metadata only |
| Expression AST | — | **OWNER** | — |
| Transformation semantics | — | **OWNER** | opaque workload only |
| Logical transformation DAG | — | **OWNER** | — |
| Logical optimizer | — | **OWNER** | — |
| Engine adapters | — | **OWNER** | — |
| Field-level lineage | partial source mapping | **OWNER** | — |
| Workflow DAG | — | — | **OWNER** |
| Task state machine | — | — | **OWNER** |
| Retry ownership | local ingestion operation only | physical engine operation only | **OWNER for workflow task retry** |
| Concurrency orchestration | — | engine-local only | **OWNER** |
| Workflow timeout / cancellation | — | — | **OWNER** |
| Durable workflow runtime state | — | — | **OWNER** |
| Recovery / resume | ingestion replay semantics only | — | **OWNER** |
| Workflow manifest | — | — | **OWNER** |
| Runtime execution lineage | ingestion run | transformation execution | **OWNER at workflow level** |

The word **OWNER** means that the framework defines the canonical semantics for that concern.

Another framework may reference, wrap, or adapt the concept, but must not independently redefine its meaning.

---

## 5. The Pipeline / DAG distinction

All three projects may legitimately contain graph-like structures.

This is not duplication if the graphs represent different things.

### 5.1 PyIngestKit pipeline

A PyIngestKit pipeline describes an ingestion lifecycle.

```text
fetch
  ↓
persist RAW
  ↓
parse
  ↓
validate
  ↓
version
  ↓
publish
```

Question answered:

> **How does an external source become a reliable governed dataset?**

---

### 5.2 PyTransformKit pipeline

A PyTransformKit pipeline describes logical data derivation.

```text
Dataset A ──┐
            ├── Join
Dataset B ──┘
              ↓
            Filter
              ↓
            Derive
              ↓
           Aggregate
```

Question answered:

> **How is an output dataset logically derived from one or more input datasets?**

---

### 5.3 PyWorkflowKit workflow

A PyWorkflowKit workflow describes operational workload dependencies.

```text
ingest_customers ─────┐
                      ├── build_customer_mart ── publish
ingest_orders ────────┘
```

Question answered:

> **Which workloads must execute, and under what operational dependency rules?**

---

## 6. Non-negotiable invariants

### INV-01 — Single semantic owner

Every major capability must have one canonical owner.

No framework may duplicate another framework's domain semantics merely for convenience.

---

### INV-02 — PyTransformKit is not an orchestrator

PyTransformKit may own a logical transformation DAG.

It must not own:

- workflow scheduling;
- TaskAttempt state;
- workflow retries;
- durable workflow state;
- recovery daemons;
- distributed workers;
- worker leases;
- workflow heartbeats;
- operational resume semantics.

Those concerns belong to PyWorkflowKit.

---

### INV-03 — PyTransformKit is not an ingestion framework

PyTransformKit must not own:

- immutable RAW capture;
- source acquisition lifecycle;
- ingestion DatasetVersion repositories;
- publication pointers;
- ingestion replay;
- ingestion artifact stores;
- ingestion idempotency semantics.

Those concerns belong to PyIngestKit.

---

### INV-04 — PyWorkflowKit sees workloads, not domain internals

PyWorkflowKit may execute a PyIngestKit job or PyTransformKit pipeline.

It must not understand or reimplement:

- RAW semantics;
- DatasetVersion semantics;
- Expression AST;
- transformation semantics;
- Schema propagation;
- field lineage.

---

### INV-05 — No hidden retry stacking

Exactly one layer owns the operational retry of a given side effect.

A retry policy must never be silently active simultaneously at:

```text
PyWorkflowKit Task
        +
PyIngestKit Job
        +
PyTransformKit Engine operation
```

without an explicit ownership decision.

Nested retry may exist only when the inner retry is for a clearly different failure class and has bounded semantics.

---

### INV-06 — References cross boundaries; internal objects do not

Framework boundaries should exchange stable references and contract DTOs rather than leaking internal runtime objects.

Preferred:

```text
DatasetRef
DatasetVersionRef
TransformationExecutionRef
ExternalRunRef
ArtifactURI
ResourceReference
```

Avoid:

```text
Pandas DataFrame crossing every layer
SQLAlchemy session crossing every layer
Workflow internal state object imported by PyTransformKit
PyIngestKit persistence model imported by PyWorkflowKit
```

---

## 7. Allowed dependency directions

The preferred dependency graph is:

```text
PyWorkflowKit
    │
    ├──── optional adapter ───► PyIngestKit
    │
    └──── optional adapter ───► PyTransformKit

PyIngestKit
    │
    └──── optional adapter ───► PyTransformKit

PyTransformKit
    │
    └──── NO dependency on PyIngestKit or PyWorkflowKit
```

This preserves PyTransformKit as the lowest-level compute abstraction of the three.

### Forbidden dependency cycles

The following are forbidden:

```text
PyTransformKit → PyWorkflowKit
PyTransformKit → PyIngestKit

PyIngestKit → PyWorkflowKit → PyIngestKit

PyTransformKit → PyIngestKit → PyTransformKit core cycle
```

Integration must happen through optional adapters, ports, plugins, or anti-corruption layers.

---

## 8. PyIngestKit ↔ PyTransformKit integration

The primary integration pattern is:

```text
External Source
      ↓
PyIngestKit
      ↓
DatasetVersion / portable dataset reference
      ↓
PyTransformKit
      ↓
Transformation execution
      ↓
transformed result
      ↓
PyIngestKit publication / target
```

Example conceptual flow:

```python
ingested = ingest_job.run(...)

result = transform_service.run(
    pipeline=customer_pipeline,
    input_ref=ingested.dataset_ref,
    engine="polars",
)

publish_job.run(input_ref=result.output_ref)
```

The integration contract should not require PyTransformKit to understand the PyIngestKit persistence model.

A dedicated adapter may translate:

```text
PyIngestKit DatasetVersion
        ↓
portable ResourceReference
        ↓
PyTransformKit DatasetHandle
```

---

## 9. PyWorkflowKit ↔ PyIngestKit integration

The existing conceptual boundary remains:

```text
PyWorkflowKit Task
        ↓
PyIngestKit Adapter
        ↓
PyIngestKit Job
        ↓
TaskResult + ExternalRunRef
```

PyWorkflowKit owns:

- task dispatch;
- operational retry ownership;
- timeout;
- cancellation;
- workflow dependency handling;
- workflow recovery.

PyIngestKit owns:

- ingestion semantics;
- source acquisition;
- RAW;
- ingestion quality;
- versioning;
- replay;
- publication.

---

## 10. PyWorkflowKit ↔ PyTransformKit integration

The equivalent transformation boundary is:

```text
PyWorkflowKit Task
        ↓
PyTransformKit Adapter
        ↓
PyTransformKit Pipeline
        ↓
Engine Adapter
        ↓
TransformationExecutionResult
```

A workflow task treats a complete PyTransformKit pipeline execution as one workload unless an explicit advanced integration requires a different granularity.

PyWorkflowKit should not decompose a PyTransformKit logical Pipeline into WorkflowKit tasks automatically.

Doing so would confuse logical data dependencies with operational workload dependencies.

---

## 11. Three forms of lineage

The three frameworks expose different and complementary forms of lineage.

### 11.1 PyIngestKit lineage

```text
External Resource
      ↓
RAW artifact
      ↓
parsed Dataset
      ↓
DatasetVersion
      ↓
PublishedDataset
```

This is **provenance and dataset-version lineage**.

---

### 11.2 PyTransformKit lineage

```text
source.customer_id ───────┐
                          ├── expression
source.country_code ──────┘
                          ↓
                 target.customer_key
```

This is **logical transformation and field-level lineage**.

---

### 11.3 PyWorkflowKit lineage

```text
WorkflowRun
    ↓
TaskRun
    ↓
TaskAttempt
    ↓
ExternalRunRef
```

This is **execution lineage**.

---

### 11.4 Composed lineage

An end-to-end system may combine the three:

```text
WorkflowRun W-42
│
├── Task ingest_customers
│      └── PyIngestKit Run I-288
│             └── DatasetVersion customers@52
│
├── Task transform_customers
│      └── PyTransformKit Execution T-913
│             ├── input  customers@52
│             ├── field lineage
│             └── output customers_clean
│
└── Task publish_customers
       └── PyIngestKit Run I-289
              └── PublishedDataset customers_clean@53
```

The composed view does not require one framework to absorb the others' lineage model.

---

## 12. Validation boundaries

Validation exists in more than one framework, but with different meanings.

### PyIngestKit validation

Concern:

> Is the acquired dataset acceptable as an ingestion product?

Examples:

- expected source format;
- source contract;
- parsing validity;
- quality thresholds associated with ingestion;
- reproducibility and artifact integrity.

### PyTransformKit validation

Concern:

> Does this logical transformation produce data satisfying transformation-level expectations?

Examples:

- expression-based constraints;
- post-transform NotNull;
- uniqueness after derive/join;
- row-count constraints after filtering;
- schema compatibility;
- transformation QualityGate.

### PyWorkflowKit validation

Concern:

> Is this workflow definition and runtime configuration executable?

Examples:

- DAG validity;
- missing dependencies;
- executor capability mismatch;
- invalid timeout;
- incompatible plugins;
- invalid runtime configuration.

These are complementary validation domains and must remain separate.

---

## 13. Observability boundaries

Observability must follow the same ownership rule.

### PyIngestKit

May emit:

- bytes acquired;
- source URI class;
- RAW artifact id;
- rows parsed;
- quality result;
- DatasetVersion;
- target load result.

### PyTransformKit

May emit:

- logical plan id;
- engine descriptor;
- transformation diagnostics;
- materialization events;
- conversion lossiness;
- execution metrics that the engine can actually provide.

Lazy engines must not fabricate per-step metrics.

### PyWorkflowKit

May emit:

- workflow start/end;
- TaskRun state transitions;
- TaskAttempt state;
- retry decisions;
- cancellation;
- timeout;
- external workload reference;
- workflow manifest.

An observability backend may aggregate all three, but ownership remains local to each framework.

---

## 14. Retry ownership model

Retry is one of the highest-risk overlap areas.

The rule is:

> **Retry the layer that can correctly determine whether the operation is safe to repeat.**

### PyWorkflowKit

Owns retry of a workload as a task.

Example:

```text
Task transform_customers failed
        ↓
RetryEngine
        ↓
TaskAttempt #2
```

### PyIngestKit

May internally retry safe transport-level operations such as a transient HTTP acquisition when the operation's semantics and idempotency are known.

It must not silently retry a complete ingestion job when PyWorkflowKit already owns that workload retry.

### PyTransformKit

May internally retry an engine request only when:

- the engine operation is explicitly known to be safe;
- the retry is bounded;
- the operation does not duplicate a workflow-level side effect.

A write with uncertain commit outcome must surface uncertainty instead of blindly retrying.

---

## 15. Dataset terminology

The term `Dataset` exists in multiple contexts and must be qualified.

### PyIngestKit Dataset

A dataset is an ingestion product with provenance and potentially durable version identity.

### PyTransformKit Dataset

A dataset is a logical transformation-domain value.

It must remain independent from Pandas DataFrame, Polars DataFrame, Arrow Table, or DuckDB Relation.

### PyWorkflowKit

A dataset should normally be opaque.

Workflow tasks may exchange dataset references or artifact references, but WorkflowKit does not define dataset semantics.

---

## 16. Resource references

Cross-framework integration should converge on reference-oriented boundaries.

A shared conceptual vocabulary may include:

```text
ResourceReference
ArtifactReference
DatasetReference
DatasetVersionReference
ExecutionReference
ExternalRunReference
```

This does **not** imply that the three projects must immediately share one package or one class hierarchy.

Semantic ownership is more important than type reuse.

A shared micro-package should be introduced only if independent usage proves that duplicated wire contracts have become a real maintenance problem.

Premature creation of a generic `pycorekit` or `pycommonkit` is explicitly discouraged.

---

## 17. LOT-20 clarification — I/O and Connectors

PyTransformKit LOT-20 is retained, but its boundary is constrained.

### Allowed PyTransformKit I/O

PyTransformKit may provide physical data access required to execute transformations:

- scan CSV;
- scan JSON/JSONL;
- scan Parquet;
- scan Arrow IPC;
- local filesystem access;
- projection pushdown;
- predicate pushdown;
- partition pruning;
- physical write of transformation output;
- engine-native scan/write support;
- conversion to/from supported physical engines.

This is **physical transformation I/O**.

### Forbidden PyTransformKit ingestion scope

LOT-20 must not expand into:

- immutable RAW lifecycle;
- source acquisition provenance;
- ingestion DatasetVersion repository;
- publication pointer semantics;
- ingestion replay;
- ingestion ArtifactStore;
- ingestion-specific idempotency contract;
- complete ingestion-job lifecycle.

Those remain PyIngestKit responsibilities.

The distinction is:

```text
PyTransformKit I/O
    "How can this engine read/write the physical data needed for this transformation?"

PyIngestKit ingestion
    "How does this external source become a reliable, reproducible, governed dataset?"
```

---

## 18. Integration architecture

The canonical end-to-end composition is:

```text
                          PyWorkflowKit
                               │
                     WorkflowRun / Tasks
                               │
          ┌────────────────────┴────────────────────┐
          │                                         │
          ▼                                         ▼
     PyIngestKit                              PyIngestKit
   ingest source                               publish
          │                                         ▲
          │ DatasetVersion                          │
          ▼                                         │
                    PyTransformKit                   │
                logical transformation               │
                          │                          │
                     EngineAdapter                   │
                          │                          │
             ┌────────────┼────────────┐             │
             ▼            ▼            ▼             │
          Pandas       Polars       DuckDB           │
                          │                          │
                          └──── transformed data ────┘
```

The frameworks compose by explicit adapters and references.

They do not call each other's internals.

---

## 19. Example end-to-end workflow

Conceptually:

```python
@workflow(id="customer.mart", version="1")
def customer_mart():
    customers = ingest_customers()
    orders = ingest_orders()

    transformed = build_customer_mart(
        customers=customers,
        orders=orders,
    )

    publish_customer_mart(transformed)
```

Operationally:

```text
PyWorkflowKit
    owns WorkflowRun
    owns dependency graph
    owns TaskAttempt
    owns retry
    owns recovery

ingest_customers()
    ↓
PyIngestKit
    owns acquisition
    owns RAW
    owns DatasetVersion

build_customer_mart()
    ↓
PyTransformKit
    owns expressions
    owns joins
    owns aggregation
    owns logical plan
    owns engine execution semantics

publish_customer_mart()
    ↓
PyIngestKit
    owns publication
    owns target semantics
```

---

## 20. Anti-patterns

The following designs are explicitly rejected.

### Anti-pattern A — PyTransformKit becomes Airflow-like

```text
PyTransformKit
    scheduler
    worker
    task retry
    cron
    recovery daemon
```

Rejected because workflow runtime semantics belong to PyWorkflowKit.

---

### Anti-pattern B — PyTransformKit reimplements ingestion

```text
PyTransformKit
    RAW store
    ingestion replay
    source run history
    DatasetVersion publication
```

Rejected because these semantics belong to PyIngestKit.

---

### Anti-pattern C — PyWorkflowKit understands transformation AST

```text
PyWorkflowKit Task
    introspects FilterTransformation
    rewrites JoinTransformation
    recompiles Expressions
```

Rejected because transformation semantics belong to PyTransformKit.

---

### Anti-pattern D — PyWorkflowKit parses ingestion formats

```text
Workflow Task
    read CSV
    create RAW
    validate source
    publish DatasetVersion
```

Rejected as framework behavior because ingestion semantics belong to PyIngestKit.

A user task may of course run arbitrary Python, but the framework itself must not absorb those domain semantics.

---

### Anti-pattern E — Generic common package too early

```text
pycommonkit
    Dataset
    Run
    Pipeline
    Event
    Result
    Adapter
```

Rejected unless concrete cross-project pressure proves a stable shared abstraction.

A vague shared kernel would erase bounded contexts and create coupling.

---

## 21. Integration adapter strategy

Cross-project integrations should be implemented as explicit optional adapters.

Recommended direction:

```text
pyworkflowkit.integrations.pyingestkit
pyworkflowkit.integrations.pytransformkit

pyingestkit.integrations.pytransformkit
```

Equivalent independently packaged adapters are also acceptable if release coupling becomes undesirable.

Rules:

1. Core packages must remain importable without the integrated framework installed.
2. Integration dependencies must be optional.
3. Version compatibility must be declared explicitly.
4. Adapter failures must be distinguishable from domain execution failures.
5. Adapters must preserve correlation identifiers.
6. Adapters must not translate away important uncertainty or failure semantics.

---

## 22. Correlation and execution identity

Each framework keeps its own execution identity.

Example:

```text
WorkflowRunId                  W-42
PyIngestKit RunId             I-288
PyTransformKit ExecutionId    T-913
PyIngestKit Publish RunId      I-289
```

Correlation may be represented as:

```json
{
  "workflow_run_id": "W-42",
  "task_run_id": "TR-17",
  "external_run_ref": {
    "provider": "pytransformkit",
    "run_id": "T-913"
  }
}
```

The identifiers are linked, not collapsed into one global id type.

---

## 23. Failure model

Framework failures should preserve their domain of origin.

Example:

```text
PyWorkflowKit
    TaskTimeoutError

PyIngestKit
    SourceAcquisitionError
    DatasetValidationFailure
    TargetLoadUncertainOutcome

PyTransformKit
    UnsupportedCapabilityError
    SchemaResolutionError
    TransformationExecutionError
    EngineContractViolation
```

An integration adapter may normalize a failure into a task result while retaining:

- original framework;
- error category;
- stable error code where available;
- external execution reference;
- retryability decision;
- uncertainty state.

Do not collapse all failures into an untyped `RuntimeError`.

---

## 24. Compatibility policy

The three projects version independently.

No project release should require synchronized version numbers.

Example:

```text
PyIngestKit       1.x
PyTransformKit    0.x / 1.x
PyWorkflowKit     1.x
```

Integration adapters must publish compatibility ranges.

Example:

```text
pyworkflowkit integration:
    pytransformkit >=0.5,<1

later:
    pytransformkit >=1,<2
```

Compatibility is contractual, not inferred from matching version numbers.

---

## 25. Implications for PyTransformKit roadmap

The existing PyTransformKit roadmap remains valid with the following interpretation.

### LOT-15 — Data Quality

Allowed because it validates transformation outputs and transformation-domain expectations.

It must not duplicate the complete ingestion-quality lifecycle of PyIngestKit.

### LOT-16 — Lineage and Metadata

Allowed because PyTransformKit owns logical and field-level derivation lineage.

It must not become the canonical store for ingestion provenance or workflow execution history.

### LOT-17 — Observability, Metrics and Audit

Allowed for transformation execution evidence.

It must not absorb WorkflowKit's workflow event/state model.

### LOT-20 — I/O and Connectors

Retained with the physical-transformation-I/O boundary defined in section 17.

### LOT-23 — Plugins

Plugin APIs must remain transformation/runtime-extension plugins, not generic workflow plugins.

### LOT-24 — Cross-Engine Conformance

Entirely owned by PyTransformKit.

---

## 26. Definition of integration success

The ecosystem is considered correctly separated when the following statements remain true.

### PyIngestKit

Can be used without PyTransformKit and without PyWorkflowKit.

### PyTransformKit

Can be used without PyIngestKit and without PyWorkflowKit.

### PyWorkflowKit

Can be used without PyIngestKit and without PyTransformKit.

### Composition

A user may optionally compose all three without duplicated semantic ownership.

### Core import isolation

Installing one core package must not implicitly install the other two unless an explicit integration extra requires it.

### Testable boundaries

Architecture tests should prevent forbidden imports and dependency cycles.

---

## 27. Recommended architecture tests

PyTransformKit should eventually enforce rules such as:

```text
src/pytransformkit/domain/**
    MUST NOT import pyingestkit
    MUST NOT import pyworkflowkit
    MUST NOT import pandas
    MUST NOT import polars
    MUST NOT import pyarrow
    MUST NOT import duckdb
```

PyIngestKit core should enforce:

```text
core ingestion domain
    MUST NOT import pyworkflowkit
    SHOULD NOT import pytransformkit directly
    MAY depend on an internal port implemented by an optional adapter
```

PyWorkflowKit core should enforce:

```text
core workflow domain
    MUST NOT import pyingestkit
    MUST NOT import pytransformkit
```

Integration modules are the only allowed dependency edges.

---

## 28. Architectural decision

The three-framework structure is retained.

```text
PyIngestKit
    reliable ingestion

PyTransformKit
    portable transformation semantics

PyWorkflowKit
    reliable workload execution
```

The ecosystem must resist two forms of accidental convergence:

1. turning PyTransformKit into a workflow orchestrator;
2. turning PyTransformKit into a second ingestion framework.

The intended relationship is:

```text
                 DO NOT DUPLICATE OWNERSHIP

PyIngestKit   ──may call──► PyTransformKit

PyWorkflowKit ──may run───► PyIngestKit
              └─may run───► PyTransformKit

PyTransformKit never orchestrates either framework.
```

---

## 29. Final rule

When a new capability is proposed, the first question is not:

> "In which repository is it easiest to implement?"

The first question is:

> **"Which bounded context owns the semantics of this capability?"**

Only after that answer is explicit should implementation begin.

This rule is the primary safeguard against long-term overlap between PyTransformKit, PyIngestKit, and PyWorkflowKit.
