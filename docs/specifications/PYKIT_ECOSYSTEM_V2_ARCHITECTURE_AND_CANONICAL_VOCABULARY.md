# PyKit Ecosystem V2 — Architecture and Canonical Vocabulary

> **Status:** NORMATIVE ARCHITECTURE BASELINE  
> **Architecture generation:** V2  
> **Date:** 2026-09-28  
> **Scope:** PyIngestKit, PyTransformKit, PyWorkflowKit  
> **Compatibility posture:** clean-slate redesign; no legacy API preservation requirement  
> **Supersedes:** ad-hoc cross-project vocabulary inherited from the current implementations  
> **Related:** `PYTRANSFORMKIT_PYINGESTKIT_PYWORKFLOWKIT_BOUNDARIES_AND_INTEGRATION.md`

---

## 1. Purpose

This document freezes the target architecture and canonical vocabulary of the second-generation PyKit data-processing ecosystem formed by:

- **PyIngestKit** — reliable ingestion and governed dataset production;
- **PyTransformKit** — engine-agnostic logical data transformation;
- **PyWorkflowKit** — reliable operational execution of workload dependencies.

The V2 design is intentionally **not constrained by legacy APIs, class names, package internals, persistence schemas, decorators, CLI contracts, or compatibility aliases** from previous versions.

Existing implementations remain valuable as:

- executable knowledge;
- failure-mode evidence;
- test scenarios;
- integration experience;
- implementation reference;
- migration input.

They are **not** the source of truth for the V2 domain model.

The governing principle is:

> **Design from semantic ownership first; derive code from the model second.**

---

# 2. Why a V2 architecture is necessary

The three frameworks evolved independently enough that similar technical words naturally appeared in multiple places:

```text
Pipeline
DAG
Step
Task
Run
Execution
Result
Context
Plan
Validation
Lineage
Observability
```

This is not inherently incorrect. Many systems contain graphs, plans, runs, results, or validation.

The problem begins when a generic technical term becomes the primary public domain concept in several frameworks while referring to different semantics.

For example:

```text
PyIngestKit Pipeline
PyTransformKit Pipeline
PyWorkflowKit workflow DAG
```

may all be graph-shaped, but they answer different questions.

V2 resolves this by adopting:

1. explicit bounded contexts;
2. one semantic owner per major concern;
3. domain-qualified public vocabulary;
4. stable suffix semantics across the ecosystem;
5. structural terms such as DAG as implementation descriptors, not business concepts;
6. explicit integration boundaries;
7. independent versioning and release lifecycles.

---

# 3. Ecosystem architecture

The ecosystem is organized into three complementary planes.

```text
┌──────────────────────────────────────────────────────────────┐
│                     PyWorkflowKit                            │
│                                                              │
│                      CONTROL PLANE                           │
│                                                              │
│  WorkflowDefinition                                          │
│        ↓                                                     │
│  WorkflowGraph                                               │
│        ↓                                                     │
│  TaskDefinition                                              │
│        ↓                                                     │
│  ExecutionPlan                                               │
│        ↓                                                     │
│  WorkflowRun → TaskRun → TaskAttempt                        │
└──────────────────────────────┬───────────────────────────────┘
                               │
                    executes / coordinates
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
┌───────────────────────────────┐   ┌───────────────────────────────┐
│        PyIngestKit            │   │       PyTransformKit          │
│                               │   │                               │
│          DATA PLANE           │   │    COMPUTE / LOGICAL PLANE    │
│                               │   │                               │
│  IngestionDefinition          │   │  TransformationPlan           │
│        ↓                      │   │        ↓                      │
│  IngestionLifecycle           │   │  TransformationGraph          │
│        ↓                      │   │        ↓                      │
│  IngestionStage               │   │  LogicalPlan                  │
│        ↓                      │   │        ↓                      │
│  IngestionRun                 │   │  OptimizedLogicalPlan         │
│        ↓                      │   │        ↓                      │
│  DatasetVersion               │   │  PhysicalPlan                 │
│        ↓                      │   │        ↓                      │
│  PublishedDataset             │   │  EngineAdapter                │
└───────────────┬───────────────┘   └──────────────┬────────────────┘
                │                                  │
                │ may delegate transformation       │ executes on
                └──────────────────┐               │
                                   ▼               ▼
                             PyTransformKit    Pandas / Polars
                                               PyArrow / DuckDB
```

The compact interpretation is:

```text
PyIngestKit
    HOW DOES EXTERNAL DATA BECOME A RELIABLE DATASET?

PyTransformKit
    HOW IS A DATASET LOGICALLY TRANSFORMED?

PyWorkflowKit
    WHAT WORKLOADS MUST EXECUTE, AND UNDER WHAT OPERATIONAL RULES?
```

---

# 4. Canonical bounded contexts

## 4.1 PyIngestKit — ingestion domain

PyIngestKit owns the lifecycle that turns an external source into a reliable, reproducible, governed dataset.

Canonical flow:

```text
Source
  ↓
Acquire
  ↓
RAW
  ↓
Decode / Parse
  ↓
Validate
  ↓
Version
  ↓
Publish
```

PyIngestKit owns:

- source description;
- source acquisition;
- transport-level acquisition policy;
- immutable RAW evidence;
- source provenance;
- decoding / parsing;
- ingestion contracts;
- ingestion quality decisions;
- artifact persistence;
- DatasetVersion creation;
- publication;
- target delivery;
- replay from preserved source evidence;
- ingestion idempotency;
- source-to-dataset provenance.

PyIngestKit does not own:

- generic workflow scheduling;
- generic task state machines;
- general-purpose transformation ASTs;
- relational optimizer semantics;
- engine-agnostic analytical transformation languages.

---

## 4.2 PyTransformKit — transformation domain

PyTransformKit owns logical data transformation semantics independently from physical engines.

Canonical flow:

```text
TransformationPlan
        ↓
TransformationGraph
        ↓
LogicalPlan
        ↓
OptimizedLogicalPlan
        ↓
PhysicalPlan
        ↓
EngineAdapter
        ↓
TransformationExecution
```

PyTransformKit owns:

- logical DataTypes;
- Field and Schema semantics;
- logical Dataset identity;
- Expression AST;
- transformation specifications;
- relational transformations;
- grouping and aggregation;
- window / analytical operations;
- reshaping;
- transformation graph semantics;
- static schema propagation;
- logical planning;
- logical optimization;
- physical planning;
- engine capability negotiation;
- engine adapters;
- transformation-level validation;
- logical and field-level lineage;
- execution diagnostics;
- portable transformation IR;
- cross-engine conformance.

PyTransformKit does not own:

- immutable ingestion RAW;
- DatasetVersion repositories;
- publication lifecycle;
- ingestion replay;
- workflow task retries;
- workflow recovery;
- distributed workflow scheduling.

---

## 4.3 PyWorkflowKit — workflow execution domain

PyWorkflowKit owns reliable execution of generic workloads and their operational dependencies.

Canonical flow:

```text
WorkflowDefinition
        ↓
WorkflowGraph
        ↓
ExecutionPlan
        ↓
WorkflowRun
        ↓
TaskRun
        ↓
TaskAttempt
        ↓
Executor
        ↓
Runtime Evidence
```

PyWorkflowKit owns:

- workflow definition;
- task definition;
- operational dependency graph;
- execution planning;
- task readiness;
- workflow/task/attempt state;
- retry policy;
- retry backoff;
- timeout;
- cancellation;
- concurrency;
- executor capabilities;
- durable workflow metadata;
- workflow runtime events;
- recovery;
- reconciliation;
- resume;
- workflow manifests;
- external workload references;
- workflow-level execution lineage.

PyWorkflowKit does not own:

- ingestion semantics;
- RAW;
- DatasetVersion semantics;
- transformation expressions;
- schema derivation;
- relational optimization;
- transformation engine compilation.

---

# 5. Canonical vocabulary

The public vocabulary MUST make the bounded context visible.

## 5.1 Root concepts

| Meaning | PyIngestKit | PyTransformKit | PyWorkflowKit |
|---|---|---|---|
| User-authored root definition | `IngestionDefinition` | `TransformationPlan` | `WorkflowDefinition` |
| Domain structure | `IngestionLifecycle` | `TransformationGraph` | `WorkflowGraph` |
| Smallest semantic unit | `IngestionStage` | `Transformation` | `TaskDefinition` |
| Derived executable plan | `IngestionPlan` if needed | `LogicalPlan` / `PhysicalPlan` | `ExecutionPlan` |
| Runtime instance | `IngestionRun` | `TransformationExecution` | `WorkflowRun` |
| Sub-runtime record | `StageRun` | `TransformationExecutionRecord` if needed | `TaskRun` |
| Attempt | domain-specific acquisition attempt if needed | engine-operation attempt only if needed | `TaskAttempt` |
| Terminal result | `IngestionResult` | `TransformationResult` | `WorkflowResult` |

This table is normative.

---

# 6. Reserved semantic prefixes

The ecosystem reserves three public prefixes.

## 6.1 `Ingestion*`

Reserved for PyIngestKit domain semantics.

Examples:

```text
IngestionDefinition
IngestionLifecycle
IngestionStage
IngestionPlan
IngestionRun
IngestionResult
IngestionError
```

---

## 6.2 `Transformation*`

Reserved for PyTransformKit domain semantics.

Examples:

```text
TransformationPlan
TransformationGraph
Transformation
TransformationExecution
TransformationResult
TransformationError
```

---

## 6.3 `Workflow*` and `Task*`

Reserved for PyWorkflowKit operational semantics.

Examples:

```text
WorkflowDefinition
WorkflowGraph
WorkflowRun
WorkflowResult

TaskDefinition
TaskRun
TaskAttempt
TaskResult
```

A sibling framework MUST NOT introduce public concepts such as:

```text
IngestionWorkflow
TransformationWorkflow
TransformTask
WorkflowTransformation
```

unless the name explicitly describes an integration adapter rather than a native domain object.

---

# 7. The status of `Pipeline`

## 7.1 Decision

`Pipeline` is a **generic descriptive term**, not a preferred canonical public domain type in V2.

It may appear in documentation:

> "This application builds a customer data pipeline."

It should not be the primary root type of more than one bounded context.

V2 therefore avoids canonical root APIs such as:

```python
pyingestkit.Pipeline
pytransformkit.Pipeline
pyworkflowkit.Pipeline
```

The intended replacements are:

```text
PyIngestKit      → IngestionLifecycle
PyTransformKit   → TransformationPlan / TransformationGraph
PyWorkflowKit    → WorkflowDefinition / WorkflowGraph
```

---

# 8. The status of `DAG`

`DAG` is a **structural property**, not a bounded-context domain concept.

Correct usage:

```text
TransformationGraph is a DAG.
WorkflowGraph is a DAG.
An IngestionLifecycle may compile to an acyclic graph.
```

Discouraged public root types:

```text
DAG
DataDAG
WorkflowDAG
IngestionDAG
```

unless the object genuinely represents a generic graph abstraction internal to implementation code.

A domain name should answer **what the graph means**, not merely what mathematical shape it has.

---

# 9. Canonical suffix semantics

V2 standardizes common suffixes.

## 9.1 `Definition`

A user-authored declarative description of a domain object.

Properties:

- immutable where practical;
- side-effect free;
- not an execution;
- may be validated;
- may be compiled into another representation.

Examples:

```text
IngestionDefinition
WorkflowDefinition
TaskDefinition
```

---

## 9.2 `Graph`

A domain graph expressing semantic dependencies.

Examples:

```text
TransformationGraph
WorkflowGraph
```

A Graph is not automatically an execution plan.

---

## 9.3 `Plan`

A derived representation prepared for a later stage.

A Plan MUST state what level it represents.

Examples:

```text
TransformationPlan
LogicalPlan
OptimizedLogicalPlan
PhysicalPlan
ExecutionPlan
IngestionPlan
```

Unqualified public `Plan` SHOULD be avoided.

---

## 9.4 `Run`

A durable or identifiable runtime instance of a domain process.

Examples:

```text
IngestionRun
WorkflowRun
TaskRun
```

`Run` is preferred when runtime lifecycle identity matters.

---

## 9.5 `Execution`

A computation-oriented runtime occurrence.

Primary canonical use:

```text
TransformationExecution
```

This differentiates compute execution from workflow lifecycle identity.

Unqualified public `Execution` SHOULD be avoided.

---

## 9.6 `Result`

A terminal or returned outcome of a specific operation.

All public Result types SHOULD be domain-qualified when exported at package root:

```text
IngestionResult
TransformationResult
WorkflowResult
TaskResult
```

Avoid:

```text
Result
ExecutionResult
RunResult
```

without bounded-context qualification.

---

## 9.7 `Spec`

A declarative specification of a subordinate component or policy.

Examples:

```text
SourceSpec
SinkSpec
RetrySpec
WindowSpec
ValidationSpec
```

`Spec` SHOULD NOT replace the root domain concepts `Definition`, `Plan`, or `WorkflowDefinition` merely to shorten names.

---

## 9.8 `Ref` / `Reference`

A stable portable reference that may cross process or framework boundaries.

Examples:

```text
ResourceReference
DatasetReference
DatasetVersionReference
ArtifactReference
ExecutionReference
ExternalRunRef
```

References MUST NOT silently imply ownership of the referenced object's internal model.

---

## 9.9 `Context`

A runtime context supplied to an operation.

Public Context types MUST be domain-qualified.

Examples:

```text
IngestionContext
TransformationContext
WorkflowRunContext
TaskContext
```

Avoid exporting a bare:

```text
Context
```

---

# 10. Discouraged generic public names

At package root, the following names SHOULD NOT be introduced without qualification:

```text
Pipeline
DAG
Manager
Service
Engine
Runner
Job
Step
Run
Result
Context
Plan
Resource
Event
State
Config
Adapter
Registry
```

This does not ban these words internally.

It means the public API should prefer names that reveal semantics.

Examples:

```text
EngineRegistry                acceptable in PyTransformKit
WorkflowRuntime               acceptable in PyWorkflowKit
IngestionRun                  acceptable in PyIngestKit
TransformationResult          acceptable in PyTransformKit
```

---

# 11. PyIngestKit V2 domain model

## 11.1 Root model

```text
IngestionDefinition
        ↓
IngestionLifecycle
        ↓
┌─────────────────────────────────────────────┐
│ Acquisition                                │
│ RawPersistence                             │
│ Decoding                                   │
│ Validation                                 │
│ Versioning                                 │
│ Publication                                │
└─────────────────────────────────────────────┘
        ↓
IngestionRun
        ↓
DatasetVersion
        ↓
PublishedDataset
```

The V2 model deliberately does **not** begin with:

```text
Job
Pipeline
Step
```

Those names are orchestration-shaped abstractions and are too generic for the ingestion domain.

---

## 11.2 Stage model

`IngestionStage` is acceptable where a uniform lifecycle abstraction is useful.

Canonical built-in stage kinds may include:

```text
ACQUIRE
PERSIST_RAW
DECODE
VALIDATE
VERSION
PUBLISH
```

However, each stage remains semantically constrained by ingestion.

`IngestionStage` is not a generic arbitrary-workload task abstraction.

If a user needs arbitrary task orchestration, that belongs to PyWorkflowKit.

---

# 12. PyTransformKit V2 domain model

## 12.1 Root model

```text
TransformationPlan
        ↓
TransformationGraph
        ↓
LogicalPlan
        ↓
OptimizedLogicalPlan
        ↓
PhysicalPlan
        ↓
EngineAdapter
        ↓
TransformationExecution
        ↓
TransformationResult
```

The former generic `Pipeline` concept is replaced by domain-specific terminology.

---

## 12.2 Transformation vocabulary

Examples:

```text
SelectTransformation
FilterTransformation
DeriveTransformation
CastTransformation
JoinTransformation
AggregateTransformation
WindowTransformation
SortTransformation
DeduplicateTransformation
PivotTransformation
UnpivotTransformation
```

The public root concept remains `Transformation`.

---

## 12.3 Planning layers

The planning vocabulary is intentionally explicit.

### TransformationPlan

User-facing declarative intent.

### TransformationGraph

Canonical dependency structure between transformations and logical datasets.

### LogicalPlan

Normalized engine-independent executable semantics.

### OptimizedLogicalPlan

Semantically equivalent logical plan after optimizer rules.

### PhysicalPlan

Engine-targeted execution representation.

This establishes the invariant:

```text
intent
  ↓
logical semantics
  ↓
optimization
  ↓
physical realization
```

No physical engine object may leak backward into the Domain model.

---

# 13. PyWorkflowKit V2 domain model

## 13.1 Root model

```text
WorkflowDefinition
        ↓
WorkflowGraph
        ↓
TaskDefinition
        ↓
ExecutionPlan
        ↓
WorkflowRun
        ↓
TaskRun
        ↓
TaskAttempt
```

This vocabulary is preserved because it already maps cleanly to the operational domain.

---

## 13.2 Public vs internal graph terminology

Public concept:

```text
WorkflowGraph
```

Possible internal implementation:

```text
DependencyGraph
TopologicalSorter
ReadinessIndex
```

This separates user-facing semantics from graph mechanics.

---

# 14. Decode is not Transform

One of the most important V2 rules is:

> **Decoding external representation is ingestion. Deriving new data semantics is transformation.**

Examples owned by PyIngestKit:

```text
CSV bytes → rows
JSON bytes → structured records
Excel sheet → typed input dataset
Parquet artifact → decoded dataset
character encoding → Unicode values
```

Examples owned by PyTransformKit:

```text
rename
cast
derive
filter
join
aggregate
window
pivot
unpivot
deduplicate
sort
business normalization
```

The key rule is:

```text
DECODE != TRANSFORM
```

A parser may perform representation-level conversion required to interpret the source format.

It must not silently become a second transformation framework.

---

# 15. Three different graph semantics

## 15.1 IngestionLifecycle

Question:

> How does an external source become a governed dataset?

```text
Acquire
  ↓
Persist RAW
  ↓
Decode
  ↓
Validate
  ↓
Version
  ↓
Publish
```

---

## 15.2 TransformationGraph

Question:

> How is this output dataset derived from its inputs?

```text
Customers ─┐
           ├── Join ── Filter ── Derive ── Aggregate
Orders ────┘
```

---

## 15.3 WorkflowGraph

Question:

> What workloads must execute, under what dependency order?

```text
ingest_customers ─────┐
                      ├── build_customer_mart ── publish
ingest_orders ────────┘
```

These graphs may all be DAGs.

They are not interchangeable.

---

# 16. Semantic ownership matrix

| Capability | PyIngestKit | PyTransformKit | PyWorkflowKit |
|---|:---:|:---:|:---:|
| External source acquisition | **OWNER** | — | — |
| RAW preservation | **OWNER** | — | — |
| Source provenance | **OWNER** | — | reference only |
| Decode / parse external format | **OWNER** | limited physical scan | — |
| DatasetVersion | **OWNER** | — | reference only |
| Publication lifecycle | **OWNER** | — | coordinate only |
| Ingestion replay | **OWNER** | — | coordinate only |
| Schema semantics | consumer | **OWNER** | opaque metadata |
| Expression AST | — | **OWNER** | — |
| Transformations | — | **OWNER** | workload only |
| TransformationGraph | — | **OWNER** | — |
| Logical planning | — | **OWNER** | — |
| Physical engine planning | — | **OWNER** | — |
| Engine adapters | — | **OWNER** | — |
| Field lineage | source mapping | **OWNER** | — |
| WorkflowGraph | — | — | **OWNER** |
| Task lifecycle | — | — | **OWNER** |
| Task retry | — | — | **OWNER** |
| Workflow concurrency | — | engine-local only | **OWNER** |
| Workflow timeout | — | — | **OWNER** |
| Workflow cancellation | — | — | **OWNER** |
| Durable workflow runtime state | — | — | **OWNER** |
| Recovery / resume | ingestion replay only | — | **OWNER** |
| Workflow manifest | — | — | **OWNER** |

**OWNER** means the framework defines the canonical semantics.

---

# 17. Dependency direction

The preferred package dependency direction is:

```text
PyWorkflowKit
    │
    ├──── optional integration ───► PyIngestKit
    │
    └──── optional integration ───► PyTransformKit

PyIngestKit
    │
    └──── optional integration ───► PyTransformKit

PyTransformKit
    │
    └──── no sibling dependency
```

Core modules MUST remain independently importable.

---

# 18. Forbidden dependency cycles

The following are forbidden:

```text
PyTransformKit → PyWorkflowKit
PyTransformKit → PyIngestKit

PyIngestKit core → PyWorkflowKit

PyWorkflowKit core → PyIngestKit domain internals
PyWorkflowKit core → PyTransformKit domain internals

PyTransformKit → PyIngestKit → PyTransformKit
```

Cross-framework behavior must use:

- optional integration modules;
- ports;
- adapters;
- plugin contracts;
- portable references;
- anti-corruption layers.

---

# 19. Integration modules

Recommended integration surfaces:

```text
pyingestkit.integrations.pytransformkit

pyworkflowkit.integrations.pyingestkit
pyworkflowkit.integrations.pytransformkit
```

Optional package extras may expose them:

```bash
pip install "pyingestkit[transform]"
pip install "pyworkflowkit[ingest,transform]"
```

These names are illustrative; exact packaging may evolve without changing semantic ownership.

Integration rules:

1. no sibling framework required for core import;
2. compatibility ranges declared explicitly;
3. adapters preserve correlation identifiers;
4. adapters preserve uncertainty states;
5. adapters do not reinterpret domain failures as successes;
6. adapters do not reach into private implementation modules.

---

# 20. Cross-framework reference model

Framework boundaries SHOULD exchange references instead of internal objects.

Preferred concepts:

```text
ResourceReference
ArtifactReference
DatasetReference
DatasetVersionReference
TransformationExecutionReference
ExternalRunRef
```

Example:

```text
PyIngestKit DatasetVersion
        ↓
DatasetVersionReference
        ↓
PyTransformKit input resolution
```

Another example:

```text
PyWorkflowKit TaskRun
        ↓
ExternalRunRef(provider="pytransformkit", ...)
        ↓
TransformationExecution
```

References connect identities.

They do not merge domain models.

---

# 21. Execution identity

Each framework keeps its own runtime identity.

Example:

```text
WorkflowRunId                  W-42
TaskRunId                      TR-17
IngestionRunId                 I-288
TransformationExecutionId      T-913
PublishIngestionRunId          I-289
```

Correlation links these identifiers.

They MUST NOT be collapsed into one global `RunId`.

---

# 22. Retry ownership

Retry is explicitly layered.

## 22.1 PyWorkflowKit

Owns retry of a **workload/task**.

```text
TaskAttempt #1
    ↓ failure
RetryPolicy
    ↓
TaskAttempt #2
```

---

## 22.2 PyIngestKit

May retry a bounded acquisition/transport operation when:

- repeat safety is known;
- source semantics permit it;
- the retry does not duplicate a higher-level task side effect.

It does not silently own whole-workload retries when PyWorkflowKit already does.

---

## 22.3 PyTransformKit

May retry a bounded physical engine operation only when:

- it is safe;
- retryability is explicit;
- uncertain write outcomes are surfaced rather than hidden.

---

## 22.4 Prohibited retry stacking

The following must not happen implicitly:

```text
Workflow task retry
        ×
Ingestion whole-run retry
        ×
Transformation whole-execution retry
```

Every retry MUST declare its failure domain.

---

# 23. Validation vocabulary

Validation exists in all three bounded contexts, but means different things.

## PyIngestKit

Question:

> Is this source acquisition and ingestion product acceptable?

Examples:

- source contract;
- parsing validity;
- artifact integrity;
- required columns;
- ingestion quality threshold;
- reproducibility.

Canonical names should reveal ingestion scope where ambiguity exists:

```text
IngestionValidationPolicy
SourceContract
DatasetAcceptanceResult
```

---

## PyTransformKit

Question:

> Does this logical transformation satisfy transformation-domain expectations?

Examples:

- expression constraints;
- post-transform NotNull;
- uniqueness after join;
- schema compatibility;
- row-count expectation;
- transformation QualityGate.

---

## PyWorkflowKit

Question:

> Is this workflow definition and runtime configuration executable?

Examples:

- cycle detection;
- unknown task dependency;
- executor capability mismatch;
- invalid timeout;
- incompatible plugin.

WorkflowKit does not perform data-quality validation as a framework concern.

---

# 24. Three lineage domains

## 24.1 Ingestion lineage

```text
External Resource
    ↓
RAW
    ↓
Decoded Dataset
    ↓
DatasetVersion
    ↓
PublishedDataset
```

Owner: PyIngestKit.

Meaning: provenance and dataset version history.

---

## 24.2 Transformation lineage

```text
input.customer_id ───┐
                     ├── expression ──► output.customer_key
input.country ───────┘
```

Owner: PyTransformKit.

Meaning: logical and field-level derivation.

---

## 24.3 Workflow lineage

```text
WorkflowRun
   ↓
TaskRun
   ↓
TaskAttempt
   ↓
ExternalRunRef
```

Owner: PyWorkflowKit.

Meaning: execution provenance.

---

## 24.4 Composed lineage

```text
WorkflowRun W-42
│
├── TaskRun ingest_customers
│      └── IngestionRun I-288
│             └── DatasetVersion customers@52
│
├── TaskRun transform_customers
│      └── TransformationExecution T-913
│             ├── input customers@52
│             ├── field lineage
│             └── output customers_clean
│
└── TaskRun publish_customers
       └── IngestionRun I-289
              └── PublishedDataset customers_clean@53
```

No framework must absorb another framework's lineage model to produce this composition.

---

# 25. Observability vocabulary

Observability remains local to the producing bounded context.

## PyIngestKit may emit

```text
source acquisition duration
bytes acquired
RAW artifact id
rows decoded
quality outcome
DatasetVersion id
publication outcome
```

## PyTransformKit may emit

```text
logical plan fingerprint
engine descriptor
optimizer rule evidence
materialization events
conversion diagnostics
supported physical metrics
```

Lazy engines MUST NOT fabricate unavailable per-transformation metrics.

## PyWorkflowKit may emit

```text
workflow lifecycle
task state changes
attempt state
retry decision
timeout
cancellation
external workload reference
workflow manifest
```

One telemetry backend may aggregate all three.

Semantic ownership remains local.

---

# 26. Error vocabulary

Errors SHOULD be domain-qualified and preserve origin.

Examples:

```text
PyIngestKit
    SourceAcquisitionError
    RawPersistenceError
    DecodeError
    IngestionValidationError
    DatasetVersionError
    PublicationError

PyTransformKit
    SchemaResolutionError
    InvalidExpressionError
    UnsupportedCapabilityError
    PlanningError
    TransformationExecutionError
    EngineContractViolation

PyWorkflowKit
    WorkflowDefinitionError
    WorkflowPlanningError
    TaskExecutionError
    TaskTimeoutError
    WorkflowCancelledError
    RecoveryError
```

Avoid reducing cross-framework failures to:

```text
RuntimeError
ExecutionError
Error
```

without stable origin information.

---

# 27. I/O boundary

PyTransformKit may own physical I/O required for transformation execution.

Examples:

```text
scan CSV
scan Parquet
scan Arrow IPC
scan JSONL
projection pushdown
predicate pushdown
partition pruning
engine-native physical write
```

This is:

> **physical transformation I/O**

PyTransformKit does not own:

```text
source acquisition lifecycle
immutable RAW
source provenance
DatasetVersion repository
publication pointers
ingestion replay
ingestion artifact governance
```

Those remain PyIngestKit responsibilities.

---

# 28. End-to-end composition

Canonical example:

```text
                         PyWorkflowKit
                              │
                         WorkflowRun
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
 ingest_customers       ingest_orders        publish
          │                   │                   ▲
          ▼                   ▼                   │
     PyIngestKit          PyIngestKit              │
          │                   │                   │
          ▼                   ▼                   │
 customers@52           orders@117                │
          │                   │                   │
          └──────────┬────────┘                   │
                     ▼                            │
               PyTransformKit                     │
                     │                            │
             TransformationPlan                   │
                     │                            │
             TransformationGraph                  │
                     │                            │
                 LogicalPlan                      │
                     │                            │
                 EngineAdapter                    │
                     │                            │
                     └──── transformed dataset ───┘
```

---

# 29. Canonical user-facing imports

A central V2 usability objective is that imports explain the architecture.

Preferred:

```python
from pyingestkit import IngestionDefinition
from pytransformkit import TransformationPlan
from pyworkflowkit import WorkflowDefinition
```

The names are intentionally different.

Users should not need:

```python
from pyingestkit import Pipeline as IngestionPipeline
from pytransformkit import Pipeline as TransformationPipeline
```

to disambiguate the ecosystem.

---

# 30. Canonical verbs

The three frameworks SHOULD expose domain-specific verbs.

Conceptually:

```text
ingest
transform
run workflow
```

Typical object-oriented forms:

```python
ingestion_service.ingest(definition)

transformation_service.execute(plan)

workflow_runtime.run(definition)
```

Exact APIs remain to be specified.

The key rule is that identical method names must not hide substantially different semantics without context.

---

# 31. No shared PyCoreKit in the initial V2 architecture

V2 deliberately does not introduce:

```text
PyCoreKit
PyCommonKit
PyBaseKit
```

as mandatory dependencies.

A common package containing vague abstractions such as:

```text
Dataset
Result
Run
Event
Context
Manager
Resource
```

would risk erasing bounded contexts.

The ecosystem first shares:

- naming rules;
- reference conventions;
- correlation conventions;
- serialization principles;
- error origin rules;
- version compatibility policy.

A shared package may be extracted later only when repeated implementations prove a genuinely stable common abstraction.

---

# 32. Versioning strategy

The frameworks version independently.

## PyIngestKit

The clean-slate redesign targets:

```text
2.0.0
```

because semantic and public API compatibility with the 1.x line is not a goal.

## PyWorkflowKit

The clean-slate redesign targets:

```text
2.0.0
```

for the same reason.

## PyTransformKit

Because it is still pre-1.0, breaking vocabulary and model changes may be introduced before its first stable release.

Its V2 ecosystem vocabulary SHOULD be adopted before `1.0.0`.

Matching major versions across the three projects are not required.

---

# 33. Legacy posture

Legacy code is treated as a source of evidence, not as an architectural constraint.

The rewrite process may reuse:

- algorithms;
- test scenarios;
- fixture data;
- performance measurements;
- migration learnings;
- production failure cases;
- security controls.

It SHOULD NOT automatically reuse:

- public class names;
- package module layout;
- persistence schema;
- old generic abstractions;
- compatibility aliases;
- deprecated APIs.

V2 architecture wins over legacy convenience.

---

# 34. Implementation order

The recommended clean-slate implementation sequence is normative at the architecture level.

## Phase 1 — Ecosystem architecture freeze

Freeze:

- bounded contexts;
- ownership matrix;
- canonical vocabulary;
- dependency direction;
- integration rules;
- cross-framework references.

This document is the baseline.

---

## Phase 2 — Public API design before implementation

Design executable-looking examples for:

```text
PyIngestKit V2
PyTransformKit
PyWorkflowKit V2
```

without allowing implementation constraints to dictate the API.

Required proof:

- one minimal example per framework;
- one advanced example per framework;
- one composed end-to-end example.

---

## Phase 3 — Domain model rewrite

Implement only:

- immutable/value domain types;
- contracts;
- validation rules;
- graph semantics;
- errors;
- public typing.

Do not begin with:

- CLI;
- SQLAlchemy;
- cloud connectors;
- persistence;
- plugin discovery;
- compatibility shims.

---

## Phase 4 — PyTransformKit core first

Implement:

```text
Schema
  ↓
Expression
  ↓
Transformation
  ↓
TransformationGraph
  ↓
LogicalPlan
  ↓
Engine contracts
```

Reason:

PyTransformKit is the lowest-level compute abstraction and may be consumed by PyIngestKit.

---

## Phase 5 — PyIngestKit V2

Implement:

```text
Source
  ↓
Acquisition
  ↓
RAW
  ↓
Decode
  ↓
Validation
  ↓
DatasetVersion
  ↓
Publication
```

Then add the optional PyTransformKit integration.

---

## Phase 6 — PyWorkflowKit V2

Implement:

```text
WorkflowDefinition
  ↓
WorkflowGraph
  ↓
ExecutionPlan
  ↓
Runtime
  ↓
Persistence
  ↓
Recovery
```

Then add PyIngestKit and PyTransformKit workload adapters.

---

## Phase 7 — End-to-end reference application

A single reference application MUST prove all three frameworks together.

Suggested structure:

```text
examples/customer_360/
│
├── ingestion/
│   ├── customers.py
│   └── orders.py
│
├── transformations/
│   └── customer_mart.py
│
└── workflows/
    └── daily_customer_mart.py
```

The reference application is part of architecture qualification, not merely documentation.

---

# 35. Reference application semantics

Expected flow:

```text
WorkflowDefinition
        │
        ├── ingest_customers
        │      ↓
        │   PyIngestKit
        │      ↓
        │   customers@52
        │
        ├── ingest_orders
        │      ↓
        │   PyIngestKit
        │      ↓
        │   orders@117
        │
        ├── build_customer_mart
        │      ↓
        │   PyTransformKit
        │      ↓
        │   customer_mart
        │
        └── publish_customer_mart
               ↓
            PyIngestKit
               ↓
            customer_mart@8
```

PyWorkflowKit owns the operational orchestration.

PyIngestKit owns ingestion and publication semantics.

PyTransformKit owns transformation semantics.

---

# 36. Architecture tests

Each project SHOULD contain executable architecture tests.

## PyTransformKit

```text
domain MUST NOT import:
    pyingestkit
    pyworkflowkit
    pandas
    polars
    pyarrow
    duckdb
```

Physical engine imports belong only in adapter/infrastructure packages.

---

## PyIngestKit

```text
core domain MUST NOT import:
    pyworkflowkit

core domain SHOULD NOT import:
    pytransformkit concrete implementation

optional integration MAY depend on:
    pytransformkit public contracts
```

---

## PyWorkflowKit

```text
core domain MUST NOT import:
    pyingestkit
    pytransformkit

integration adapters MAY import:
    sibling public APIs
```

---

# 37. Package-root API rules

Each package root SHOULD export only deliberate domain concepts.

Avoid exposing internal implementation classes merely because they are convenient to import.

Examples of intended package-root concepts:

## PyIngestKit

```text
IngestionDefinition
IngestionRun
IngestionResult
SourceSpec
DatasetVersion
PublishedDataset
```

## PyTransformKit

```text
TransformationPlan
Transformation
Schema
Dataset
Expression
LogicalPlan
TransformationResult
```

## PyWorkflowKit

```text
WorkflowDefinition
TaskDefinition
WorkflowRun
TaskRun
TaskAttempt
WorkflowResult
```

Exact lists will be frozen separately per framework.

---

# 38. Vocabulary review gate

Every new public concept MUST answer the following before merge:

1. Which bounded context owns it?
2. Is its name domain-qualified?
3. Could the same unqualified name reasonably exist in another kit?
4. Does it duplicate an existing sibling concept?
5. Is it a domain concept or only a structural implementation detail?
6. Does it leak a physical engine into a logical model?
7. Does it create a new dependency direction?
8. Does it require a shared abstraction that has not yet been proven?

If ownership is unclear, implementation MUST pause until the architecture is clarified.

---

# 39. Naming review examples

## Accepted

```text
IngestionRun
TransformationPlan
TransformationGraph
WorkflowDefinition
WorkflowRun
TaskAttempt
DatasetVersionReference
TransformationExecutionReference
```

## Rejected or discouraged

```text
Pipeline
DAG
Job
Step
Execution
Run
Result
Context
Manager
Service
```

when exported as unqualified root domain concepts.

---

# 40. Architectural invariants

The following invariants are normative.

### V2-INV-01 — One semantic owner

Every major capability has one canonical bounded-context owner.

### V2-INV-02 — Vocabulary reveals ownership

Public root names should reveal whether the concept belongs to ingestion, transformation, or workflow execution.

### V2-INV-03 — DAG is structural

Graph structure does not determine semantic ownership.

### V2-INV-04 — Pipeline is non-normative

`Pipeline` may be used descriptively but is not the preferred root domain abstraction.

### V2-INV-05 — Decode is not transform

Representation decoding belongs to ingestion; logical derivation belongs to transformation.

### V2-INV-06 — Transformation is not workflow execution

A TransformationGraph may be a DAG but does not become a WorkflowGraph.

### V2-INV-07 — Workflow tasks treat sibling frameworks as workloads

WorkflowKit does not absorb their domain semantics.

### V2-INV-08 — References cross boundaries

Portable references are preferred over leaking internal runtime objects.

### V2-INV-09 — Retry ownership is explicit

No implicit stacked retry across sibling frameworks.

### V2-INV-10 — Core packages remain independently usable

No sibling framework is required for another sibling's core import.

### V2-INV-11 — Independent versioning

Release numbers need not align.

### V2-INV-12 — No premature shared core

Shared code is extracted only after proven semantic stability.

---

# 41. V2 architecture acceptance criteria

This architecture baseline is considered successfully implemented when:

1. PyIngestKit public V2 APIs no longer depend on generic `Job → Pipeline → Step` as their primary domain model.
2. PyTransformKit exposes `TransformationPlan` / `TransformationGraph` rather than a generic root `Pipeline`.
3. PyWorkflowKit exposes `WorkflowDefinition` / `WorkflowGraph` / `TaskDefinition`.
4. no package requires import aliases merely to distinguish sibling root concepts.
5. PyTransformKit has no dependency on PyIngestKit or PyWorkflowKit.
6. PyIngestKit core has no dependency on PyWorkflowKit.
7. PyWorkflowKit core has no dependency on PyIngestKit or PyTransformKit.
8. optional integrations are isolated from core domains.
9. one end-to-end example composes all three without duplicated semantic ownership.
10. retry ownership is explicit in that example.
11. the three lineage domains can be correlated without being merged.
12. the three execution identities remain independent.
13. architecture tests prevent forbidden imports.
14. public API reviews enforce canonical suffix semantics.
15. no shared common package is required merely to make the three frameworks coexist.

---

# 42. Final architecture statement

The V2 ecosystem is not three competing ways to build a pipeline.

It is three bounded contexts that compose:

```text
PyIngestKit
    external data → reliable dataset

PyTransformKit
    dataset → logically derived dataset

PyWorkflowKit
    workloads → reliable operational execution
```

The canonical public vocabulary is therefore:

```text
IngestionDefinition
IngestionLifecycle
IngestionRun

TransformationPlan
TransformationGraph
LogicalPlan
PhysicalPlan
TransformationExecution

WorkflowDefinition
WorkflowGraph
TaskDefinition
ExecutionPlan
WorkflowRun
TaskRun
TaskAttempt
```

And the central ecosystem rule is:

> **Never choose a public abstraction because it is technically generic. Choose it because its semantic owner is unambiguous.**

This document is the architecture baseline from which the PyIngestKit 2.0 roadmap, PyWorkflowKit 2.0 roadmap, and the revised pre-1.0 PyTransformKit roadmap should be derived.
