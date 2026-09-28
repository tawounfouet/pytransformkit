# PyTransformKit V1 — Target Architecture

> **Status:** NORMATIVE TARGET ARCHITECTURE BASELINE
> **Target release:** PyTransformKit 1.0.0
> **Date:** 2026-09-28
> **Architecture generation:** PyKit Ecosystem V2
> **Tagline:** Define transformations once. Execute them anywhere.
> **Primary bounded context:** logical data transformation and compute execution

## 1. Purpose

This document defines the target internal architecture of PyTransformKit for the 1.0.0 stable release.

It translates the ecosystem-wide V2 rules into concrete PyTransformKit module boundaries, domain objects, runtime services, ports, adapters, engine integrations, serialization boundaries, extension points and compatibility constraints.

> **PyTransformKit owns logical transformation semantics and compute execution, but not ingestion lifecycle and not workflow orchestration.**

> **The domain remains engine-neutral; engines are adapters, not the model.**

## 2. Product mission

PyTransformKit lets users define transformations once and execute them through compatible compute engines.

~~~text
logical transformation intent
        ↓
engine-neutral compilation
        ↓
engine-specific execution
~~~

Pandas, Polars, PyArrow, DuckDB and future engines are execution adapters rather than canonical domain models.

## 3. Bounded-context ownership

PyTransformKit owns:

~~~text
logical Dataset
logical Schema and DataType
Expression AST
Transformation objects
TransformationPlan
LogicalPlan
logical validation
schema propagation
capability requirements
logical and field lineage
engine capability model
InputBinding / OutputBinding
TransformationExecution
TransformationResult
engine adapters
physical transformation I/O
transformation diagnostics
transformation events and telemetry
portable transformation serialization where supported
~~~

PyTransformKit does not own:

~~~text
source acquisition lifecycle
immutable RAW capture
ingestion provenance
DatasetVersion repository
PublishedDataset pointer lifecycle
ingestion replay
workflow scheduling
TaskRun / TaskAttempt
workflow retry
worker scheduling
durable workflow recovery
cron semantics
enterprise catalog governance
IAM platform
secret management
~~~

## 4. Sibling dependency direction

~~~text
PyWorkflowKit
    └── optional integration → PyTransformKit

PyIngestKit
    └── optional integration → PyTransformKit

PyTransformKit
    └── NO sibling dependency
~~~

PyTransformKit core MUST import neither PyIngestKit nor PyWorkflowKit.

## 5. Canonical public lifecycle

~~~text
TransformationPlan
        ↓
compile
        ↓
LogicalPlan
        ↓
TransformationRuntime.execute(...)
        ↓
TransformationExecution
        ↓
TransformationResult
~~~

Engine-specific lowering remains adapter-owned.

There is no stable public TransformationGraph, OptimizedLogicalPlan or universal PhysicalPlan in V1.

## 6. Architectural layers

~~~text
AUTHORING
    user-facing construction and ergonomics

DOMAIN
    immutable engine-neutral semantic model

APPLICATION / PLANNING
    validation, compilation, optimization, capability analysis

RUNTIME
    execution identity, bindings, engine coordination, results

INFRASTRUCTURE / ADAPTERS
    engines, physical I/O, plugins and telemetry sinks
~~~

Dependencies point inward. Domain never depends on infrastructure.

## 7. Target package structure

~~~text
src/pytransformkit/
├── __init__.py
├── domain/
│   ├── datasets.py
│   ├── schema.py
│   ├── types.py
│   ├── expressions/
│   ├── transformations/
│   ├── plans.py
│   ├── lineage.py
│   └── errors.py
├── application/
│   ├── validation.py
│   ├── compiler.py
│   ├── optimizer.py
│   ├── capabilities.py
│   └── inspection.py
├── runtime/
│   ├── execution.py
│   ├── results.py
│   ├── bindings.py
│   ├── context.py
│   ├── registry.py
│   └── diagnostics.py
├── ports/
│   ├── engine.py
│   ├── resource.py
│   ├── telemetry.py
│   └── plugins.py
├── adapters/
│   ├── pandas/
│   ├── polars/
│   ├── pyarrow/
│   ├── duckdb/
│   └── io/
├── serialization/
├── observability/
└── plugins/
~~~

Exact filenames may evolve, but the dependency direction is normative.

## 8. Root package philosophy

The package root is curated rather than exhaustive.

Primary root concepts SHOULD include TransformationPlan, LogicalPlan, TransformationRuntime, TransformationExecution, TransformationResult, Dataset, Schema, Field, DataType, Expression, col, lit and stable transformation primitives.

Internal graph classes, optimizer implementation types, engine-native helpers, private serializers and plugin machinery stay out of the root API.

## 9. Domain purity

Pure domain modules MUST be importable with no optional engine installed.

They MUST NOT import:

~~~text
pandas
polars
pyarrow
duckdb
sqlalchemy
database drivers
cloud SDKs
PyIngestKit
PyWorkflowKit
~~~

This invariant is CI-enforced.

## 10. Dataset

Dataset is a logical object describing semantic data in a transformation plan.

It MUST NOT store DataFrames, LazyFrames, Arrow Tables, DuckDB relations, open files, cursors or provider clients.

A Dataset may own logical identity, Schema, semantic metadata and lineage identity.

Physical data enters only through runtime bindings.

## 11. Schema and DataType

Schema is an ordered portable logical contract composed of Field values.

The logical type system SHOULD cover the stable common denominator required by official engines, including boolean, integer, floating point, decimal, string, binary, date/time/timestamp, duration, list/array, struct, map where supported and null/unknown.

Adapters own mapping between native engine types and logical DataType values.

Lossy mapping must be explicit.

## 12. Expression AST

Expression is an immutable portable AST, not executable Python source.

Representative node families include ColumnReference, Literal, unary/binary operations, functions, casts, conditionals, aggregate expressions, window expressions and nested-field access where supported.

Portable expressions SHOULD support type inference, nullability inference, dependency extraction, deterministic equality, canonical fingerprints, lineage derivation and safe serialization.

Arbitrary eval-based execution is forbidden.

## 13. Authoring helpers

Helpers such as col and lit are syntax sugar returning canonical Expression values.

They do not create a second expression system.

## 14. Transformation model

Core transformation families include:

~~~text
projection
filter
derive
cast
sort
deduplicate
join
aggregate
window
reshape
temporal and nested operations where supported
~~~

Every transformation declares semantic inputs, output behavior, schema behavior, capability requirements and lineage behavior.

Transformation objects SHOULD be immutable.

## 15. TransformationPlan

TransformationPlan is the canonical authoring root.

It owns logical inputs, transformation nodes, dependency topology, logical outputs and runtime-independent semantic options.

The topology is part of TransformationPlan semantics.

A separate stable public TransformationGraph is therefore unnecessary.

## 16. Plan topology

The plan topology MUST be acyclic, deterministic, inspectable and validated before execution.

Topological ordering must not depend on object addresses or incidental map ordering.

Multi-input transformations such as joins use explicit logical input edges.

Those edges model data semantics, not workflow scheduling.

## 17. Validation layers

~~~text
STRUCTURAL
    object shape and DAG integrity

SEMANTIC
    field/type/expression correctness

CAPABILITY
    selected engine can support required semantics

RUNTIME PREFLIGHT
    bindings and physical resources are resolvable and safe
~~~

Diagnostics must preserve these distinctions.

## 18. Compilation

Compilation converts TransformationPlan into LogicalPlan.

It may normalize topology, propagate schemas, type-check expressions, derive capability requirements, derive lineage, canonicalize ordering and compute fingerprints.

Compilation MUST NOT execute transformations against physical data or create runtime execution IDs.

## 19. LogicalPlan

LogicalPlan is the public engine-neutral compiled representation.

It provides independent value for engine adapters, explainability, optimization, capability analysis, lineage, fingerprints and serialization.

It may contain normalized logical nodes, resolved schemas, normalized expressions, dependencies, capability requirements, logical lineage and diagnostics.

It MUST NOT contain DataFrames, engine sessions, provider clients, runtime retry state or secret values.

## 20. Optimization

Optimization preserves the LogicalPlan contract:

~~~text
LogicalPlan
    ↓ optimizer
LogicalPlan
~~~

There is no distinct stable public OptimizedLogicalPlan type.

Optimizer rules must preserve logical semantics and lineage.

## 21. Physical planning

V1 does not freeze a universal public PhysicalPlan.

Engine adapters may lower LogicalPlan into backend-specific representations such as Pandas operations, Polars LazyFrame plans, DuckDB SQL/relations or Arrow compute pipelines.

These physical forms remain adapter-internal or provisional.

## 22. EngineAdapter

EngineAdapter is the primary compute extension boundary.

Its stable responsibilities include engine description, capability declaration, plan compatibility validation, execution, binding compatibility, output production and native error translation.

Exact method signatures are frozen later in PYTRANSFORMKIT_V1_PUBLIC_API_SPEC.md.

## 23. EngineDescriptor and capabilities

Each adapter SHOULD expose engine ID, engine version when available, adapter version, execution mode and capability set.

Capabilities are semantic and may include FILTER, PROJECT, DERIVE, JOIN_INNER, JOIN_LEFT, AGGREGATE, WINDOW, PIVOT, NESTED_TYPES, PREDICATE_PUSHDOWN, PROJECTION_PUSHDOWN, PARQUET_READ and PARQUET_WRITE.

Package presence alone is not a capability declaration.

## 24. No hidden fallback

If an engine lacks a required capability, execution fails explicitly unless the user configured an explicit fallback strategy.

PyTransformKit MUST NOT silently materialize data into another engine to make execution succeed.

## 25. EngineRegistry

EngineRegistry maps engine IDs to configured adapters.

It SHOULD support explicit registration, lookup, capability inspection, duplicate protection and optional plugin activation.

Global import-time registration is prohibited.

## 26. InputBinding

InputBinding connects a logical Dataset input to runtime physical data.

It may reference ResourceReference, PhysicalHandle, ownership/lifetime information and resolved schema evidence.

InputBinding belongs to runtime, not TransformationPlan.

## 27. OutputBinding

OutputBinding describes physical output materialization or write targets.

It may include logical output identity, ResourceReference, format, write mode and ownership/lifetime.

It MUST NOT claim PyIngestKit DatasetVersion publication semantics.

## 28. PhysicalHandle

PhysicalHandle is an opaque runtime wrapper around native engine data such as DataFrame, LazyFrame, Arrow Table or DuckDB relation.

It is process/runtime scoped unless explicitly documented otherwise.

It is not a portable wire contract.

## 29. ResourceReference

ResourceReference is the portable identity/location contract for a physical resource.

ResourceReference and PhysicalHandle are intentionally distinct.

Resolvers translate portable references into usable runtime resources under explicit security policy.

## 30. TransformationRuntime

TransformationRuntime is the main execution service.

It coordinates validation, compilation, optimization, engine lookup, capability preflight, binding resolution, execution identity, engine execution, output materialization, failure translation, lineage evidence, diagnostics, events and result construction.

It MUST NOT become a workflow runtime.

## 31. TransformationExecutionId

Each semantic execute operation receives a fresh TransformationExecutionId.

Bounded internal provider retries preserve that execution identity.

A new independent execution receives a new ID.

A WorkflowKit TaskAttempt retry normally creates a new TransformationExecutionId unless recovery reattaches to existing work.

## 32. CorrelationContext

TransformationRuntime accepts or creates CorrelationContext.

CorrelationId connects broader operations while TransformationExecutionId remains native identity.

TraceId and SpanId remain observational.

## 33. TransformationExecution

TransformationExecution is the runtime record for one compute execution.

It may contain or reference the execution ID, plan fingerprints, engine descriptor, input/output bindings, status, timestamps, FailureEvidence, diagnostics, lineage evidence and CorrelationContext.

## 34. TransformationResult

TransformationResult is the caller-facing outcome.

A successful result SHOULD expose portable output references, output Schema, diagnostics, lineage evidence, engine identity, execution reference and relevant fingerprints.

It MAY also expose a clearly marked process-local PhysicalHandle for ergonomic local use.

A PhysicalHandle is never serialized as durable state.

## 35. Failure model

PyTransformKit maps native failures into stable framework semantics such as validation, capability, configuration, transient, timeout, cancelled, resource exhausted, rate limited, integrity, contract violation, external provider, unknown outcome and internal failure.

Human-readable exception text is diagnostic rather than contractual.

## 36. Retry ownership

PyTransformKit may retry only bounded engine/provider operations when retry safety is known.

Whole-workload retry belongs to PyWorkflowKit.

Provider SDK retries count toward the effective retry budget.

## 37. UNKNOWN_OUTCOME

Side-effecting writes may have uncertain outcomes.

If a provider may have committed after a timeout, the runtime preserves UNKNOWN_OUTCOME or reconciliation-required semantics.

Blind replay of a possibly committed write is prohibited.

## 38. Cancellation

TransformationRuntime may expose cancellation when the selected engine/provider supports it.

Cancellation request and confirmed cancellation remain distinct.

## 39. Physical I/O boundary

PyTransformKit may support physical I/O required by transformations:

~~~text
CSV / JSONL / Parquet / Arrow reads
engine-native scans
projection pushdown
predicate pushdown
partition pruning
physical result writes
~~~

It MUST NOT own RAW lifecycle, source acquisition provenance, DatasetVersion repositories, publication pointers or ingestion replay.

## 40. Reader and Writer ports

Physical I/O SHOULD use explicit Reader/Writer-style ports or equivalent small interfaces.

They consume and produce ResourceReference, bindings or PhysicalHandle concepts rather than PyIngestKit domain types.

Write modes are physical storage semantics, not governed publication semantics.

## 41. Lineage

PyTransformKit owns logical dataset and field lineage.

It SHOULD represent value derivation, row-selection dependencies, grouping dependencies, join dependencies and ordering dependencies where relevant.

Built-in declarative operations SHOULD produce EXACT lineage when the semantics are fully known.

Opaque UDF/raw SQL may produce DECLARED, INFERRED, PARTIAL or UNKNOWN lineage.

## 42. Logical versus physical lineage

Logical lineage expresses transformation meaning.

Physical runtime evidence may record engine, resource, execution ID, materialization and cache reuse.

Physical evidence does not replace logical lineage.

## 43. Observability

PyTransformKit emits framework-owned events, diagnostics, metrics and traces.

Potential event families cover execution start, plan compilation, engine selection, success, failure and cancellation.

Exact stable event names are frozen separately if promoted to public contracts.

## 44. Diagnostics

Structured diagnostics SHOULD cover validation, schema propagation, capabilities, optimizer decisions, engine warnings, I/O warnings and lineage confidence.

Users should not need to parse logs to understand execution.

## 45. Metrics and telemetry isolation

Default metrics avoid high-cardinality execution IDs, full URIs and raw SQL.

Telemetry sink failure MUST NOT replay business computation.

Core execution works without an external telemetry backend.

## 46. Serialization

Stable portable surfaces use explicit contract IDs and versions.

Candidate portable surfaces include Expression AST, TransformationPlan, LogicalPlan, ResourceReference, TransformationExecutionReference, CorrelationContext, FailureEvidence, lineage evidence and manifests.

Serialization MUST reject or explicitly mark arbitrary Python closures, lambdas, engine sessions, native dataframes, provider clients and raw secrets as non-portable.

## 47. LogicalPlan wire IR

A stable LogicalPlan wire representation SHOULD carry contract/version, logical nodes, expressions, schemas, input identities, semantic options, capability requirements, lineage metadata as appropriate and fingerprint.

Wire compatibility evolves independently from package version.

## 48. Fingerprints

Public fingerprints are deterministic and scoped.

Potential forms include schema_fingerprint, expression_fingerprint, transformation_plan_fingerprint and logical_plan_fingerprint.

Runtime IDs and timestamps are not semantic fingerprints.

## 49. Plugin architecture

Plugins MAY extend EngineAdapter, Reader/Writer, ResourceResolver, expression/function registries, optimizer rules and telemetry sinks.

Discovery does not imply activation.

Core import MUST NOT eagerly import every installed plugin.

Stable plugin Protocols require versioning, lifecycle rules, capability declarations and conformance tests.

## 50. Optional dependencies

The base package remains lightweight.

Target capability extras may include:

~~~text
[pandas]
[polars]
[pyarrow]
[duckdb]
~~~

Exact final names are frozen by packaging/public API documents.

Missing optional dependencies fail only when their feature is activated.

## 51. Security

PyTransformKit follows the ecosystem trust model:

~~~text
identity != authorization
secrets referenced rather than serialized
resource targets validated
deserialization non-executable
raw SQL / UDF trust explicit
plugins explicitly activated
telemetry redacted
~~~

TransformationPlan and LogicalPlan MUST NOT contain raw credentials.

## 52. Pandas adapter

Pandas is an official V1 engine target.

It SHOULD pass the stable common semantic suite and normalize eager/native behavior into PyTransformKit logical semantics.

## 53. Polars adapter

Polars is an official V1 engine target.

It SHOULD pass the same common suite where capabilities permit.

Lazy execution may be used internally without changing logical semantics.

## 54. PyArrow and DuckDB

PyArrow and DuckDB may be stable or provisional at 1.0 depending on conformance readiness.

Stable status requires explicit capability coverage and semantic parity tests.

## 55. Engine capability parity rule

~~~text
capability advertised
    ⇒ equivalent logical semantics

capability not advertised
    ⇒ explicit unsupported result
~~~

Not every engine must support every operator.

## 56. Performance

Optimization may use lazy execution, pushdown, pruning, caching, vectorized execution and expression simplification.

Performance work MUST preserve semantics and lineage.

No performance optimization may introduce hidden engine fallback.

## 57. Caching

Caches are runtime optimization artifacts, not DatasetVersions.

Cache identity must include enough semantic/input fingerprinting to avoid stale reuse.

Cache reuse must remain visible in runtime evidence when relevant.

## 58. Concurrency and async posture

Runtime services, registries and adapters MUST document thread safety, process safety, async behavior and resource ownership.

V1 may use synchronous execute as the canonical baseline.

Async support may be added when provider I/O benefits from it, but must preserve equivalent domain semantics.

## 59. Public exception architecture

PyTransformKit SHOULD expose a coherent public error hierarchy covering validation, compilation, unsupported capability, binding, resource resolution, execution, serialization and plugin failures.

Exact names are frozen in the public API specification.

Native provider exceptions are translated at adapter boundaries.

## 60. Migration from existing Pipeline

The pre-1.0 Pipeline API is re-evaluated against this target.

The target canonical authoring root is TransformationPlan.

A permanent Pipeline alias SHOULD NOT survive into 1.0 unless concrete compatibility evidence justifies it.

## 61. Migration from RunPipelineService

Existing RunPipelineService or equivalent application services are refactored toward TransformationRuntime semantics.

Existing implementation is evidence, not the 1.0 naming authority.

## 62. Migration from current adapters

Existing Pandas and Polars adapter code SHOULD be reused when semantics already match the new EngineAdapter contract.

Refactoring focuses on domain isolation, capability declarations, failure translation, binding semantics and shared conformance tests.

## 63. Migration from existing LogicalPlan

Existing LogicalPlan functionality is retained and consolidated when aligned with this architecture.

No second stable TransformationGraph or OptimizedLogicalPlan layer is introduced.

## 64. Architecture conformance

PyTransformKit 1.0 requires:

~~~text
domain purity tests
public API snapshot
schema and expression tests
plan determinism
engine conformance
cross-engine differential tests
I/O boundary tests
wire golden fixtures
failure and retry tests
security negative tests
built-wheel smoke
Customer 360 transformation path
~~~

## 65. Target architecture invariants

### PTK-ARCH-INV-01 — The domain is engine-neutral

No engine-native type defines domain semantics.

### PTK-ARCH-INV-02 — TransformationPlan is the authoring root

Transformation topology belongs to the plan.

### PTK-ARCH-INV-03 — LogicalPlan is the public compiled IR

It owns normalized engine-neutral semantics.

### PTK-ARCH-INV-04 — Physical planning is adapter-owned

No premature universal PhysicalPlan is frozen.

### PTK-ARCH-INV-05 — Runtime state is separate from plans

TransformationExecution owns execution identity and state.

### PTK-ARCH-INV-06 — Engine capabilities are explicit

Unsupported behavior fails rather than silently falling back.

### PTK-ARCH-INV-07 — Physical I/O is not ingestion lifecycle

Read/write support never becomes RAW, versioning or publication ownership.

### PTK-ARCH-INV-08 — Portable references differ from active handles

ResourceReference and PhysicalHandle are not interchangeable.

### PTK-ARCH-INV-09 — Logical lineage is framework-owned

PyTransformKit owns transformation and field lineage only.

### PTK-ARCH-INV-10 — Retry is bounded to engine/provider scope

Whole-workload retry remains outside PyTransformKit.

### PTK-ARCH-INV-11 — Serialization is explicit and non-executable

Portable contracts never rely on arbitrary Python object deserialization.

### PTK-ARCH-INV-12 — PyTransformKit has no sibling dependency

It remains the lowest-level sibling package.

## 66. Canonical execution flow

~~~text
TransformationPlan
        ↓
Structural + semantic validation
        ↓
TransformationCompiler
        ↓
LogicalPlan
        ↓
Optimizer
        ↓
LogicalPlan
        ↓
Capability validation
        ↓
InputBinding resolution
        ↓
EngineAdapter lowering
        ↓
TransformationExecution
        ↓
Physical output / OutputBinding
        ↓
TransformationResult
        ↓
ResourceReference + lineage + diagnostics
~~~

At no point does this flow create a governed DatasetVersion by itself.

## 67. Internal dependency flow

~~~text
domain
  ↑
application / planning
  ↑
runtime
  ↑
adapters / infrastructure
~~~

Ports are defined inward and implemented outward.

## 68. 1.0 acceptance

PyTransformKit 1.0 is ready when:

1. TransformationPlan is the canonical authoring API;
2. LogicalPlan is the canonical compiled engine-neutral IR;
3. domain purity is enforced;
4. Pandas and Polars pass common conformance;
5. Dataset/Schema/Expression semantics are stable;
6. InputBinding and OutputBinding are explicit;
7. TransformationExecution identity is stable;
8. TransformationResult is typed and portable where intended;
9. engine capabilities are explicit;
10. hidden fallback is absent;
11. physical I/O boundaries are constrained;
12. field lineage exists for stable operations;
13. wire contracts have golden fixtures;
14. plugin activation is explicit;
15. optional dependencies are isolated;
16. root exports are curated;
17. public exceptions are stable;
18. built wheels pass installed smoke;
19. Customer 360 transformation passes on two engines;
20. public API and compatibility freeze tests are green.

## 69. Out of scope for 1.0

PyTransformKit 1.0 does not require:

~~~text
distributed workflow scheduling
worker fleet management
cron
RAW archive lifecycle
DatasetVersion catalog
enterprise IAM
catalog governance
mandatory cloud services
every transformation operator
universal PhysicalPlan
universal storage platform
~~~

These exclusions protect bounded-context clarity.

## 70. Relationship to the revised roadmap

The existing LOT-11 to LOT-28 roadmap must now be reconciled against this target architecture.

The revised roadmap must map every existing lot, remove or reshape cross-boundary work, insert missing work for runtime identity/bindings/serialization/conformance, close migration from Pipeline to TransformationPlan and define the RC/1.0 freeze gates.

Target document:

~~~text
PYTRANSFORMKIT_V1_REVISED_IMPLEMENTATION_ROADMAP.md
~~~

## 71. Relationship to the public API specification

This architecture defines which concepts exist and where they belong.

The public API specification will freeze how users import and call them:

~~~text
PYTRANSFORMKIT_V1_PUBLIC_API_SPEC.md
~~~

It MUST NOT contradict this architecture.

## 72. Final architecture statement

PyTransformKit 1.0 is an engine-neutral logical transformation framework with explicit runtime execution boundaries.

~~~text
AUTHORING
    TransformationPlan
        ↓
COMPILATION
    LogicalPlan
        ↓
ENGINE ADAPTER
    engine-specific lowering
        ↓
RUNTIME
    TransformationExecution
        ↓
RESULT
    TransformationResult
~~~

> **PyTransformKit models transformation meaning first, compiles that meaning into an engine-neutral logical plan, and delegates physical execution to explicit adapters without absorbing ingestion or workflow semantics.**