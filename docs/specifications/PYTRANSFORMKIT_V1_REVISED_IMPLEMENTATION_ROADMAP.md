# PyTransformKit V1 — Revised Implementation Roadmap

> **Status:** NORMATIVE REVISED IMPLEMENTATION ROADMAP  
> **Target release:** PyTransformKit 1.0.0  
> **Date:** 2026-09-29  
> **Supersedes for future implementation:** ROADMAP_LOT_11_TO_1_0.md dated 2026-09-22  
> **Completed baseline retained:** LOT-00 through LOT-10  
> **Remaining implementation sequence retained:** LOT-11 through LOT-28  
> **Architecture generation:** PyKit Ecosystem V2  
> **Depends on:** PYTRANSFORMKIT_V1_TARGET_ARCHITECTURE.md  
> **Depends on:** PYTRANSFORMKIT_V1_PUBLIC_API_SPEC.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_END_TO_END_ACCEPTANCE_CRITERIA.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_IMPLEMENTATION_SEQUENCE_AND_MIGRATION_PLAN.md

---

# 1. Purpose

This document replaces the future-facing implementation guidance of the original frozen LOT-11 to LOT-28 roadmap while preserving its completed LOT-00 to LOT-10 history and its final LOT-28 target.

The revision is required because the PyKit Ecosystem V2 architecture has now frozen:

- TransformationPlan as the canonical authoring root;
- LogicalPlan as the public engine-neutral compiled representation;
- TransformationRuntime as the canonical execution service;
- TransformationExecutionId and TransformationResult;
- InputBinding and OutputBinding;
- ResourceReference versus PhysicalHandle;
- no public TransformationGraph;
- no public OptimizedLogicalPlan;
- no universal public PhysicalPlan;
- explicit engine capability and fallback semantics;
- strict separation from ingestion and workflow responsibilities.

The governing rule is:

> **Preserve the useful implementation history, but let the V2 target architecture control every remaining lot.**

---

# 2. Baseline retained from LOT-00 through LOT-10

The existing implementation history remains valid evidence:

| Lot | Historical scope | Status |
|---|---|---|
| LOT-00 | Repository Bootstrap | DONE |
| LOT-01 | Shared Kernel | DONE |
| LOT-02 | Type System and Schema Core | DONE |
| LOT-03 | Dataset Domain Model | DONE |
| LOT-04 | Expression AST Core | DONE |
| LOT-05 | Transformation Model MVP | DONE |
| LOT-06 | Pipeline and DAG Core | DONE |
| LOT-07 | Engine Runtime Contracts | DONE |
| LOT-08 | Pandas Reference Adapter | DONE |
| LOT-09 | Application Execution Service | DONE |
| LOT-10 | Polars Adapter and Multi-Engine Contract | DONE |

These lots prove useful foundations but do not freeze legacy public naming.

In particular:

~~~text
legacy Pipeline
    does not override
TransformationPlan target API

legacy RunPipelineService
    does not override
TransformationRuntime target API
~~~

---

# 3. Revision strategy

The lot numbering remains LOT-11 through LOT-28 to preserve project continuity.

The architectural content of each remaining lot is revised where necessary.

The new dependency chain is:

~~~text
LOT-11  V1 Model Migration + Relational Foundation
   ↓
LOT-12  Aggregation
   ↓
LOT-13  Windows
   ↓
LOT-14  Reshape / Temporal / Nested
   ↓
LOT-15  Data Quality
   ↓
LOT-16  Logical + Field Lineage
   ↓
LOT-17  Runtime Evidence / Identity / Observability
   ↓
LOT-18  PyArrow
   ↓
LOT-19  DuckDB
   ↓
LOT-20  Physical I/O Boundary
   ↓
LOT-21  Serialization / Canonical IR
   ↓
LOT-22  Logical Optimizer
   ↓
LOT-23  Plugins / Extension Contracts
   ↓
LOT-24  Cross-Engine Conformance + Customer 360
   ↓
LOT-25  Performance Qualification
   ↓
LOT-26  Public API / Security / Migration Freeze
   ↓
LOT-27  1.0 Release Candidate
   ↓
LOT-28  1.0.0 Stable
~~~

---

# 4. Mandatory V1 migration gate

LOT-11 cannot close until the codebase aligns with the frozen V1 vocabulary.

Required refactors include:

~~~text
Pipeline
    → TransformationPlan

RunPipelineService
    → TransformationRuntime

runtime input data
    → InputBinding

runtime output destination
    → OutputBinding

native runtime object
    → PhysicalHandle where abstraction is needed

portable physical location
    → ResourceReference

execution invocation
    → TransformationExecutionId + TransformationResult
~~~

The migration gate also requires:

- no new public TransformationGraph;
- no new public OptimizedLogicalPlan;
- no stable universal PhysicalPlan;
- root exports aligned with the Public API Specification;
- legacy names treated as migration concerns, not architectural authorities.

---

# Phase A — Authoring Migration and Relational Semantics

# 5. LOT-11 — V1 Public Model Migration and Relational Core

**Target milestone:** 0.2.0a1

**Status:** DONE — implemented and qualified on 2026-09-29

## Scope

Implement the mandatory V1 migration gate and portable multi-input relational semantics.

Work includes:

~~~text
TransformationPlan canonical authoring root
TransformationPlanBuilder
migration from Pipeline public naming
TransformationRuntime canonical execution service
TransformationExecutionId
TransformationResult
InputBinding / OutputBinding
ResourceReference / PhysicalHandle separation

JoinTransformation
UnionTransformation
IntersectTransformation
ExceptTransformation
multi-input plan dependencies
deterministic schema resolution
join-key model
column collision policy
NULL join semantics
Pandas implementation
Polars implementation
~~~

## Architectural objective

Move from the initial pre-1.0 Pipeline implementation to the stable V1 declaration/runtime vocabulary while proving that multi-input relational semantics remain engine-neutral.

## Exit criteria

- TransformationPlan can express all prior LOT-00 to LOT-10 functionality.
- Legacy Pipeline is no longer the canonical root API.
- TransformationRuntime replaces RunPipelineService as the target execution API.
- Multi-input dependencies compile deterministically into LogicalPlan.
- InputBinding separates logical Dataset from native data.
- Pandas and Polars pass join/set-operation conformance.
- No engine-native type enters domain objects.
- root import remains engine-optional.

## Implementation evidence

LOT-11 is closed by the 0.2.0a1 implementation baseline:

- TransformationPlan and TransformationPlanBuilder are canonical authoring contracts;
- TransformationCompiler produces deterministic multi-input LogicalPlan values;
- TransformationRuntime, TransformationExecutionId and TransformationResult are implemented;
- InputBinding, OutputBinding, ResourceReference and PhysicalHandle boundaries are explicit;
- Join, Union, Intersect and Except are implemented for Pandas and Polars;
- join types include inner, left, right, full, semi, anti and cross;
- NULL join policy and deterministic collision handling are covered by tests;
- root exports promote the V1 model while legacy Pipeline / RunPipelineService remain compatibility-only;
- README, Getting Started, script and experimentation notebook use the V1 path;
- Python 3.11, 3.12, 3.13 and 3.14 tests pass;
- Ruff lint, Ruff format, mypy, build, Pandas contract, Polars contract and cross-engine contract jobs pass.

---

# 6. LOT-12 — Aggregation and Grouping

**Target milestone:** 0.2.0a2

**Status:** DONE — implemented and qualified on 2026-09-29

## Scope

Implement:

~~~text
AggregateTransformation
grouping expressions
COUNT
COUNT DISTINCT
SUM
MIN
MAX
MEAN
null-aware aggregate semantics
aggregate expression validation
result-type inference
grouped schema propagation
Pandas execution
Polars execution
~~~

## Architectural objective

Extend the Expression AST with a typed aggregate context without introducing engine-specific expressions.

## Exit criteria

- illegal row/aggregate expression mixing fails during compilation;
- output schemas are deterministic;
- grouping dependencies appear in lineage;
- aggregate capabilities are advertised explicitly;
- Pandas and Polars return equivalent normalized logical results.

## Implementation evidence

LOT-12 is closed by the 0.2.0a2 implementation baseline:

- AggregateExpression and AggregateFunction define a dedicated aggregate context;
- the public function DSL exposes count, count_distinct, sum, min, max, mean and avg;
- AggregateTransformation carries ordered grouping expressions and named metrics;
- aggregate type inference distinguishes row-level and aggregate contexts;
- nested aggregate expressions and row/aggregate mixing fail during logical validation;
- COUNT returns non-null Int64 semantics;
- SUM, MIN, MAX and MEAN preserve explicit nullable aggregate semantics;
- TransformationPlanBuilder.aggregate authors grouped and global aggregates;
- grouped output Schemas are deterministic, including deterministic names for derived grouping expressions;
- aggregate field dependencies are extractable from the Expression AST in preparation for LOT-16 lineage;
- Pandas and Polars both advertise AGGREGATE capability;
- grouped/global aggregation is implemented for both adapters;
- NULL groups, all-null metrics, count-distinct, empty global inputs and grouping expressions are covered by cross-engine tests;
- Python 3.11, 3.12, 3.13 and 3.14 test matrices pass;
- Ruff lint, Ruff format, mypy, package build, wheel install, Pandas contract, Polars contract and cross-engine contract jobs pass.

---

# 7. LOT-13 — Window and Analytical Semantics

**Target milestone:** 0.2.0b1

**Status:** DONE — implemented and qualified on 2026-09-29

## Scope

Implement:

~~~text
window specification
partition keys
ordering specification
frame model
ROW_NUMBER
RANK
DENSE_RANK
LAG
LEAD
cumulative aggregates
moving aggregates
determinism diagnostics
Pandas support
Polars support
~~~

## Exit criteria

- window specs are immutable;
- ordering requirements are explicit;
- unsupported frame semantics fail through capability validation;
- field lineage records ordering/partition dependencies;
- common window suite passes on Pandas and Polars.

## Implementation evidence

LOT-13 is closed by the 0.2.0b1 implementation baseline:

- WindowSpec provides an immutable partition, ordering and frame model;
- the public pytransformkit.window namespace exposes row_number, rank, dense_rank, lag, lead and window aggregates;
- WindowBoundary and WindowFrame model ROWS and RANGE boundaries explicitly;
- row-number, ranking and offset functions require explicit ordering during logical validation;
- WindowDeterminism distinguishes order-independent, value-ordered and order-dependent semantics;
- full-partition, cumulative ROWS and moving ROWS aggregate semantics are implemented;
- count, sum, min, max and mean window aggregates preserve explicit NULL behavior;
- WindowExpressionTypeResolver propagates deterministic output DataTypes and nullability;
- expression dependency extraction records value, partition, ordering and default dependencies;
- window specifications participate in canonical expression fingerprints;
- engine compatibility distinguishes WINDOW, cumulative ROWS, moving ROWS, arbitrary ROWS and RANGE capabilities;
- unsupported arbitrary ROWS and RANGE semantics fail before physical execution on Pandas and Polars;
- Pandas implements the qualified analytical-window subset while preserving original row order;
- Polars implements the same qualified subset in eager and lazy modes;
- row_number, rank, dense_rank, lag, lead, partition aggregates, cumulative aggregates, moving aggregates and descending ordering pass Pandas/Polars conformance;
- Python 3.11, 3.12, 3.13 and 3.14 test matrices pass;
- Ruff lint, Ruff format, mypy, package build, wheel install, Pandas contract, Polars contract and cross-engine contract jobs pass.

---

# 8. LOT-14 — Reshaping, Temporal and Nested Semantics

**Target milestone:** 0.2.0

**Status:** DONE — implemented and qualified on 2026-09-29

## Scope

Implement the remaining stable 1.0 transformation vocabulary needed before quality/metadata layers:

~~~text
pivot
unpivot
explode
flatten where portable
nested field access
list / struct / map handling where supported
date extraction
timestamp normalization
timezone conversion
duration semantics
explicit unsupported capability reporting
~~~

## Exit criteria

- 0.2 transformation semantics are documented;
- type/schema changes are deterministic;
- engine capability gaps are explicit;
- no hidden fallback occurs;
- relational/analytical V1 authoring examples are green.

## Implementation evidence

LOT-14 closes the 0.2.0 transformation-semantics line:

- DurationType, ListType, StructType, StructField and MapType extend the engine-neutral logical type system;
- Schema.resolve_path resolves nested Struct FieldPath values without native engine types;
- nested path nullability is propagated deterministically;
- the public functions namespace exposes year, month, day, hour, minute, second, to_date, normalize_timestamp, convert_timezone and duration_between;
- timestamp normalization is distinct from timezone conversion;
- duration expressions carry explicit logical time units;
- PivotTransformation requires explicit categories so pivot output Schema is static and deterministic;
- UnpivotTransformation requires an explicit and type-compatible value-field set;
- ExplodeTransformation converts ListType fields to nullable element fields;
- FlattenTransformation expands StructType fields with deterministic naming and collision checks;
- TransformationPlanBuilder exposes pivot, unpivot, explode and flatten authoring methods;
- engine capabilities distinguish PIVOT, UNPIVOT, EXPLODE, FLATTEN, NESTED, TEMPORAL and DURATION;
- Pandas and Polars implement the qualified LOT-14 subset;
- Polars supports the reshape subset in eager and lazy modes;
- MapType is represented logically but no portable map-access operation is falsely advertised;
- unsupported engine/native mappings fail explicitly instead of silently degrading;
- Pandas/Polars cross-engine tests cover pivot, unpivot, explode, flatten, nested Struct access, date extraction, timestamp normalization, timezone conversion and durations;
- Python 3.11, 3.12, 3.13 and 3.14 test matrices pass;
- Ruff lint, Ruff format, mypy, package build, wheel install, Pandas contract, Polars contract and cross-engine contract jobs pass.

---

# Phase B — Quality, Lineage and Runtime Evidence

# 9. LOT-15 — Data Quality and Validation

**Target milestone:** 0.3.0a1

**Status:** DONE — implemented and qualified on 2026-09-30

## Scope

Implement transformation-owned quality semantics:

~~~text
ValidationRule
ValidationSpec
ValidationPolicy
ValidationResult
NotNull
Unique
Range
AllowedValues
Regex
SchemaValidation
RowCount
expression-based validation
QualityGate
FAIL_FAST
FAIL_AT_END
WARN_ONLY
IGNORE
threshold policy
~~~

## Boundary rule

This lot validates logical transformation data.

It does not absorb PyIngestKit source-decoding contract validation or ingestion publication policy.

## Exit criteria

- data violations differ from technical execution failures;
- quality semantics remain engine-neutral;
- core rules pass Pandas/Polars conformance;
- quality evidence is structured and lineage-compatible.

## Implementation evidence

LOT-15 is closed by the 0.3.0a1 implementation baseline:

- ValidationRule and ValidationSpec define an immutable engine-neutral quality declaration model;
- ValidationPolicy defines FAIL_FAST, FAIL_AT_END, WARN_ONLY and IGNORE behavior;
- ValidationThreshold supports absolute and violation-rate budgets;
- ValidationRuleResult and ValidationResult provide structured quality evidence without log parsing;
- built-in rules include NotNull, Unique, Range, AllowedValues, Regex, SchemaValidation, RowCount and ExpressionValidation;
- QualityGate is a deterministic, portable, pure transformation checkpoint that preserves rows and Schema;
- TransformationPlanBuilder.validate authors QualityGate nodes without introducing an ingestion-contract abstraction;
- expression-based validation is statically required to resolve to BooleanType;
- Regex validation is statically restricted to StringType fields;
- nested quality field references participate in engine capability analysis;
- QUALITY is an explicit EngineCapability;
- Pandas and Polars execute the common quality contract and emit equivalent ValidationResult evidence;
- FAIL_FAST raises QualityGateError on the first rejected rule;
- FAIL_AT_END evaluates the complete rule set before raising QualityGateError;
- WARN_ONLY preserves execution while retaining failed-rule evidence;
- IGNORE skips rule evaluation explicitly and records an ignored result;
- blocking data-quality violations are represented separately from AdapterError and ExecutionError;
- TransformationResult exposes validation evidence by gate name;
- Polars LazyFrame validation produces real physical evidence while preserving a lazy output handle;
- SchemaValidation validates the transformation-owned logical Schema and does not absorb PyIngestKit decode/publication policy;
- Python 3.11, 3.12, 3.13 and 3.14 test matrices pass;
- Ruff lint, Ruff format, mypy, package build, wheel install, Pandas contract, Polars contract and cross-engine contract jobs pass.

---

# 10. LOT-16 — Logical and Field Lineage

**Target milestone:** 0.3.0a2

**Status:** DONE — implemented and qualified on 2026-09-30

## Scope

Implement:

~~~text
logical dataset lineage
field lineage
expression dependency extraction
selection dependency
grouping dependency
join dependency
ordering dependency
window dependency
derivation kind
lineage confidence
impact analysis primitives
ResourceReference linkage
~~~

Stable confidence model:

~~~text
EXACT
DECLARED
INFERRED
PARTIAL
UNKNOWN
~~~

## Exit criteria

- every stable built-in transformation has lineage behavior;
- rename/cast/derive/join/aggregate/window lineage is tested;
- logical lineage is derivable without data execution;
- native engine conversion creates no false logical lineage;
- Customer 360 field lineage shape can be expressed.

## Implementation evidence

LOT-16 is closed by the 0.3.0a2 implementation baseline:

- authored logical DatasetId values survive TransformationPlan compilation into LogicalPlan;
- FieldReference identifies one FieldPath within one logical DatasetReference;
- TransformationLineage separates dataset derivation, field value derivation and operational field dependencies;
- LineageConfidence freezes EXACT, DECLARED, INFERRED, PARTIAL and UNKNOWN as the confidence vocabulary;
- built-in declarative transformations currently emit EXACT lineage where semantics are statically known;
- rename, cast and ordinary derivation distinguish RENAMED, CAST and DERIVED field ancestry;
- filter dependencies are represented separately from value ancestry;
- sort, deduplication and distinct expose ordering/selection dependencies without fabricating field derivation;
- aggregate lineage separates grouping dependencies from AGGREGATED metric ancestry;
- join lineage preserves input-side field origin, suffix resolution and JOIN-key dependencies;
- analytical-window lineage separates value, partition and ordering dependencies;
- union exposes both value sources while intersect/except preserve left value ancestry and record right-side set-membership dependency;
- pivot, unpivot, explode and flatten have deterministic static lineage for the current explicit transformation semantics;
- QualityGate preserves direct field lineage and exposes quality-rule dependencies without turning validation fields into value ancestors;
- ResourceReference linkage connects logical inputs/outputs without performing physical resolution or I/O;
- LineageImpactAnalyzer provides transitive upstream/downstream field and Dataset traversal;
- pytransformkit.lineage exposes public static analysis over TransformationPlan or LogicalPlan;
- unsupported future/opaque semantics fail through UnsupportedLineageError rather than inventing exact ancestry;
- Pandas and Polars execution of the same logical plan produces identical logical lineage evidence;
- Python 3.11, 3.12, 3.13 and 3.14 test matrices pass;
- Ruff lint, Ruff format, mypy, package build, installed-wheel smoke, Pandas contract, Polars contract and cross-engine contract jobs pass.

---

# 11. LOT-17 — Runtime Identity, Diagnostics and Observability

**Target milestone:** 0.3.0

**Status:** DONE — implemented and qualified on 2026-09-30

## Scope

Complete the V1 runtime evidence model:

~~~text
TransformationExecutionId
TransformationExecution runtime record
ExecutionStatus
CorrelationContext propagation
FailureEvidence mapping
structured Diagnostic
runtime lifecycle events
metrics
tracing hooks
execution manifest
engine descriptor in results
plan fingerprint in results
bounded provider retry evidence
UNKNOWN_OUTCOME
cancellation capability model
telemetry redaction
~~~

## Architectural objective

Make TransformationRuntime fully conform to the ecosystem execution/failure/observability contracts before additional backends are stabilized.

## Exit criteria

- every execute call has a TransformationExecutionId;
- correlation remains distinct from execution identity;
- structured failures are available without parsing logs;
- telemetry failure does not replay computation;
- unknown write outcomes remain explicit;
- lazy execution never fabricates step metrics.

## Implementation evidence

LOT-17 is closed by the 0.3.0 runtime-evidence baseline:

- every TransformationRuntime.execute call allocates a TransformationExecutionId before planning or provider execution;
- CorrelationContext and CorrelationId remain distinct from TransformationExecutionId and propagate into adapter ExecutionContext;
- trace context preserves an upstream trace ID while allocating a PyTransformKit child span;
- LogicalPlan has a deterministic SHA-256 semantic fingerprint that excludes random declaration/node/Dataset identities;
- TransformationExecution records status, timestamps, engine descriptor, plan identity/fingerprint, diagnostics, failure evidence, provider-retry evidence and cancellation metadata;
- successful TransformationResult carries TransformationExecution, TransformationLineage and ExecutionManifest alongside physical outputs;
- typed PyTransformKit exceptions retain their original public type and receive FailureEvidence, TransformationExecution, ExecutionManifest and Diagnostic evidence;
- UNKNOWN_OUTCOME remains distinct from FAILED and is classified as requiring reconciliation before safe retry;
- timeout, cancellation and engine-contract violations have dedicated execution failure types and stable PTK-EXEC codes;
- bounded ProviderRetryEvidence is disclosed without adding workload/task retry ownership to TransformationRuntime;
- CancellationToken provides process-local request signalling while EngineDescriptor declares NONE, COOPERATIVE or PROVIDER cancellation support;
- runtime lifecycle events cover execution start, plan compilation/validation, engine selection, input binding, engine execution, outputs, success/failure, unknown outcome, cancellation and provider-retry evidence;
- execution-level counters/histograms avoid execution ID, correlation ID, full URI, raw error and SQL labels by default;
- completed vendor-neutral trace spans preserve parent trace linkage;
- TelemetryRedactor removes credential/token/signed-value material before telemetry leaves the runtime;
- telemetry sink failures become PTK-OBS-001 diagnostics and never replay business computation;
- lazy execution emits execution-level evidence only and does not fabricate per-step metrics;
- Python 3.11, 3.12, 3.13 and 3.14 test matrices, Pandas/Polars contracts, cross-engine contracts, Ruff, format, mypy and built-wheel qualification form the LOT-17 release gate.

---

# Phase C — Additional Engines and Physical I/O

# 12. LOT-18 — PyArrow Adapter and Interchange

**Status:** DONE — `0.4.0a1`


**Target milestone:** 0.4.0a1

## Scope

Implement:

~~~text
PyArrowEngineAdapter
Arrow type mapper
Table / RecordBatch runtime handles
expression compilation
stable supported transformation subset
Arrow schema inspection
chunk-aware execution
Arrow interchange
Pandas ↔ Arrow bridge
Polars ↔ Arrow bridge
conversion diagnostics
lossiness policy
~~~

## Exit criteria

- base package imports without PyArrow;
- Arrow native types remain outside domain;
- supported capabilities pass engine conformance;
- conversion lossiness is explicit;
- adapter stability is STABLE or explicitly PROVISIONAL.

## Implementation closure

LOT-18 closes with an explicitly **PROVISIONAL** PyArrow adapter surface:

- `PyArrowDatasetHandle` supports both `Table` and `RecordBatch`;
- Arrow logical/native type mapping qualifies nested, decimal and temporal types;
- eager execution is chunk-aware and does not force chunk combination;
- only contract-backed capabilities are advertised;
- Pandas ↔ Arrow and Polars ↔ Arrow bridges expose strict-by-default lossiness handling;
- conversion warnings use structured `Diagnostic` evidence;
- PyArrow remains an optional dependency and the base package imports without it;
- dedicated CI jobs qualify the Arrow adapter alone and the multi-engine interchange paths.

The next implementation lot is **LOT-19 — DuckDB Adapter and Relational SQL Backend**.

---

# 13. LOT-19 — DuckDB Adapter and SQL Lowering

**Status:** DONE — `0.4.0a2`

**Target milestone:** 0.4.0a2

## Scope

Implement:

~~~text
DuckDBEngineAdapter
connection ownership
logical-type mapping
safe identifier quoting
parameterized value handling
join/aggregate/window lowering
CTE/subquery lowering
Arrow interchange
lazy relational execution
native explain diagnostics
~~~

## Exit criteria

- SQL remains physical representation only;
- raw values are not interpolated unsafely;
- user-owned connections are not closed/committed unexpectedly;
- supported relational/analytical semantics pass conformance;
- unsupported semantics fail explicitly.

## Implementation closure

LOT-19 closes the first SQL-backed execution proof with:

- `DuckDBEngineAdapter` and opaque `DuckDBDatasetHandle` relations;
- explicit framework-owned versus caller-owned connection semantics;
- no implicit commit and no closing of caller-owned connections;
- logical-to-DuckDB type mapping and conservative relation Schema inspection;
- safe identifier quoting and parameterized runtime values;
- CTE-backed physical lowering while SQL remains outside the Domain;
- qualified inner/left/right/full/semi/anti/cross join semantics;
- explicit MATCH versus NEVER_MATCH NULL join lowering;
- UNION / UNION ALL / INTERSECT / EXCEPT support;
- grouped/global aggregate lowering;
- analytical window lowering with partition/order and ROWS/RANGE frames;
- Arrow binding and materialization paths;
- eager execution plus DuckDB lazy relation execution;
- native `EXPLAIN`;
- dedicated DuckDB and DuckDB/Pandas cross-engine contract suites.

The next implementation lot is **LOT-20 — Physical I/O and Resource Boundary**,
targeting **`0.4.0`**.

---

# 14. LOT-20 — Physical I/O and Resource Boundary

**Status:** DONE — `0.4.0`

**Target milestone:** 0.4.0

## Scope

Implement the constrained PyTransformKit I/O boundary:

~~~text
ResourceReference
Reader port
Writer port
read request/result
write request/result
CSV
JSONL
Parquet
Arrow IPC
local filesystem
projection pushdown
predicate pushdown
partition pruning where supported
typed write modes
CredentialReference
retry-safety declaration
UNKNOWN_OUTCOME for writes
~~~

## Non-goals

LOT-20 MUST NOT implement:

~~~text
immutable RAW lifecycle
source acquisition provenance
DatasetVersionStore
PublishedDataset
ingestion replay
governed publication
~~~

## Exit criteria

- I/O is not modeled as Transformation;
- ResourceReference is portable;
- PhysicalHandle remains process-local;
- credentials are absent from serialized references;
- write and publication semantics remain distinct;
- pushdown does not corrupt lineage.

## Implementation closure

LOT-20 closes the `0.4.x` line with:

- explicit Reader and Writer Protocols plus scheme-based `ResourceIORegistry`;
- portable `ResourceReference`, `CredentialReference`, `RetrySafety`, `WriteMode` and `WriteStatus` semantics;
- `ReadRequest` / `ReadResult` and `WriteRequest` / `WriteResult` runtime contracts;
- local filesystem root confinement;
- CSV, JSONL, Parquet and Arrow IPC reads/writes;
- Parquet projection/predicate pushdown and Hive partition pruning;
- explicit POST_SCAN evidence when non-Parquet projection/filtering cannot be source-pushed;
- Arrow interchange as the physical bridge into Pandas, Polars, PyArrow and DuckDB;
- resource-backed runtime input resolution and explicit output materialization;
- physical ResourceReference linkage in lineage without changing logical derivation semantics;
- typed write modes kept distinct from publication semantics;
- explicit write retry-safety declarations;
- reconciliation-required `UNKNOWN_OUTCOME` propagation for uncertain side effects;
- no RAW lifecycle, DatasetVersion store, publication pointer or ingestion replay ownership.

The next implementation lot is **LOT-21 — Versioned Serialization and Canonical IR**,
targeting **`0.5.0a1`**.

---

# Phase D — Portable IR, Optimizer and Extensibility

# 15. LOT-21 — Versioned Serialization and Canonical IR

**Status:** DONE — `0.5.0a1`

**Target milestone:** 0.5.0a1

## Scope

Implement explicit safe codecs for:

~~~text
DataType
Field
Schema
Expression
TransformationPlan
LogicalPlan
ResourceReference
TransformationExecutionReference
lineage records
selected diagnostics/manifests
~~~

Requirements:

~~~text
contract ID
contract_version
canonical JSON
deterministic ordering
semantic fingerprints
golden fixtures
strict decoding
round-trip tests
migration hooks
payload limits
no pickle/cloudpickle/dill fallback
~~~

## Exit criteria

- portable plan subset round-trips deterministically;
- non-portable UDF/callback constructs fail explicitly;
- wire versions are independent from package version;
- golden fixtures are committed and compatibility-tested.

## Implementation closure

LOT-21 establishes the first durable PyTransformKit wire-contract layer with:

- a public `pytransformkit.serialization` namespace;
- explicit v1 contract IDs independent from Python module paths and package version;
- deterministic canonical JSON using UTF-8, NFC normalization, sorted object keys and compact separators;
- a closed semantic type registry that only reconstructs pre-registered PyTransformKit domain types;
- strict duplicate-key, envelope, field, enum, UUID, timestamp, size and nesting validation;
- explicit typed collection markers so tuple/list/set/frozenset/map semantics survive round-trip;
- exact portable handling for Decimal, UUID, date/time/datetime and bytes;
- codecs for DataType, Field, Schema, Expression, TransformationPlan, LogicalPlan, ResourceReference, TransformationExecutionReference, TransformationLineage, Diagnostic and ExecutionManifest;
- identity-independent semantic fingerprints for Expression, TransformationPlan and LogicalPlan;
- explicit contiguous migration hooks with no silent fallback between wire versions;
- a minimal portable `TransformationExecutionReference` contract for inter-framework boundaries;
- committed golden v1 byte fixtures and compatibility tests;
- negative tests proving arbitrary semantic tags, duplicate JSON keys, oversized payloads, future versions, callbacks and pickle-like object graphs fail closed;
- no pickle, cloudpickle, dill, eval or exec deserialization fallback.

The next implementation lot is **LOT-22 — Logical Optimizer**,
targeting **`0.5.0a2`**.

---

# 16. LOT-22 — Logical Optimizer

**Status:** DONE — `0.5.0a2`

**Target milestone:** 0.5.0a2

## Scope

Implement semantics-preserving LogicalPlan optimization:

~~~text
projection pruning
predicate pushdown
constant folding
boolean simplification
dead-node elimination
common expression analysis
safe fusion hints
materialization-boundary analysis
optimizer diagnostics
rule provenance
~~~

The public contract remains:

~~~text
LogicalPlan
    ↓ optimize
LogicalPlan
~~~

No public OptimizedLogicalPlan is introduced.

## Exit criteria

- every stable rule has equivalence/property tests;
- optimizer can be disabled;
- lineage remains correct after optimization;
- rules are engine-neutral;
- physical lowering remains adapter-owned.

## Implementation closure

LOT-22 establishes an engine-neutral optimization layer with:

- public `LogicalOptimizer.optimize(LogicalPlan) -> LogicalPlan` semantics;
- optional `optimize_with_report()` evidence without introducing a public OptimizedLogicalPlan type;
- an explicit disable switch that returns the original plan unchanged;
- bounded fixed-point passes to avoid unbounded optimizer loops;
- constant folding over safe literal arithmetic/comparison expressions;
- three-valued-logic-safe boolean simplification for AND/OR/NOT patterns;
- predicate pushdown through unbranched Select and Sort transformations only when dependencies remain valid;
- projection pruning across successive Select transformations;
- dead-node elimination for LogicalPlan nodes unreachable from declared outputs;
- deterministic Schema re-resolution after every structural rewrite;
- common-expression analysis based on existing semantic expression fingerprints;
- safe-fusion hints for adjacent pure deterministic transformations;
- explicit materialization-boundary diagnostics for multi-input, aggregate, quality, cardinality and reshape semantics;
- rule-level provenance through OptimizationRuleApplication;
- optimizer diagnostics and before/after semantic fingerprints;
- Hypothesis property tests for stable expression rules;
- Pandas end-to-end equivalence tests proving original and optimized plans return the same physical result for representative rewrites;
- lineage regression tests proving optimized output fields retain the same transitive logical input sources;
- no engine-specific imports or physical lowering logic inside the optimizer.

The next implementation lot is **LOT-23 — Extension and Plugin Architecture**,
targeting **`0.5.0`**.

---

# 17. LOT-23 — Extension and Plugin Architecture

**Status:** DONE — `0.5.0`

**Target milestone:** 0.5.0

## Scope

Stabilize extension contracts for:

~~~text
EngineAdapter
Reader / Writer
ResourceResolver
function registry
optimizer rules
telemetry sinks
PluginRegistry
entry-point discovery
compatibility declaration
explicit activation
registry freezing
duplicate/conflict handling
~~~

## Exit criteria

- discovery does not equal activation;
- core import remains side-effect free;
- built-ins can conform to public extension Protocols;
- plugin compatibility is machine-checkable;
- untrusted wire payload cannot activate code.

## Implementation closure

LOT-23 stabilizes the extension boundary with:

- a public qualified `pytransformkit.plugins` namespace without promoting plugin machinery to the package root;
- `PluginRegistry.discover()` over the `pytransformkit.plugins` entry-point group;
- discovery that captures only entry-point metadata and never calls `load()`;
- explicit `activate(plugin_id)` as the only plugin-code loading path;
- `PluginDescriptor` and `PluginCompatibility` with machine-checkable framework and plugin-protocol ranges;
- plugin API protocol version 1;
- public extension Protocols for EngineAdapter, Reader, Writer, ResourceResolver, FunctionExtension, OptimizerRule and TelemetrySink;
- FunctionRegistry, OptimizerRuleRegistry, ResourceResolverRegistry and TelemetrySinkRegistry;
- explicit duplicate/conflict rejection with opt-in replacement only on direct registry APIs;
- freeze semantics across PluginRegistry, EngineRegistry, ResourceIORegistry and new extension registries;
- PluginActivationContext as the explicit set of registries a trusted activated plugin may mutate;
- extension optimizer rules wired into LogicalOptimizer without moving physical lowering into planning;
- LocalFilePathResolver adapted to the ResourceResolver contract;
- built-in protocol-conformance tests across official engine adapters, local I/O/resolver and NullTelemetrySink;
- a plugin-specific public error hierarchy;
- security tests proving PluginDescriptor remains outside the closed semantic wire registry;
- import tests proving neither core import nor public plugin-namespace import performs entry-point discovery;
- a dedicated plugin-contract CI gate.

The next implementation lot is **LOT-24 — Cross-Engine Conformance and Customer 360 Transformation Gate**,
targeting **`0.6.0`**.

---

# Phase E — Ecosystem Conformance and Performance

# 18. LOT-24 — Cross-Engine Conformance and Customer 360 Transformation Gate

**Target milestone:** 0.6.0

## Scope

Qualify stable semantic behavior across:

~~~text
Pandas
Polars eager
Polars lazy where applicable
PyArrow when declared stable
DuckDB when declared stable
~~~

Conformance matrix includes:

~~~text
NULL / NaN
numeric promotion
Decimal
timezone
nested data
Unicode
ordering
duplicates
empty data
joins
aggregates
windows
quality
lineage
serialization
capability failure
no hidden fallback
~~~

Customer 360 requirements:

- one TransformationPlan;
- Pandas execution;
- Polars execution;
- equivalent normalized result;
- expected field lineage;
- ResourceReference output handoff suitable for PyIngestKit publication.

## Exit criteria

- published capability matrix exists;
- Pandas and Polars are fully green for mandatory 1.0 semantics;
- optional engines are labeled STABLE or PROVISIONAL honestly;
- Customer 360 transform path is green.

---

# 19. LOT-25 — Performance and Memory Qualification

**Target milestone:** 0.7.0

## Scope

Implement reproducible benchmarks for:

~~~text
planning overhead
expression compilation
execution overhead
memory amplification
eager versus lazy
native conversion costs
Arrow interchange
DuckDB materialization boundaries
I/O pushdown
lineage/diagnostic overhead
~~~

## Exit criteria

- repeatable benchmark harness exists;
- regression thresholds are defined;
- no optimization changes public semantics;
- observability does not force unnecessary materialization;
- abstraction overhead is measured rather than assumed.

---

# Phase F — API and Compatibility Freeze

# 20. LOT-26 — Public API, Security and Migration Freeze

**Target milestone:** 0.8.0

## Scope

Freeze the public V1 contract defined by PYTRANSFORMKIT_V1_PUBLIC_API_SPEC.md.

Required work includes:

~~~text
curated root exports
qualified stable namespaces
public signatures
DataType / Schema / Expression API
TransformationPlan builder
TransformationCompiler
LogicalPlan
TransformationRuntime
InputBinding / OutputBinding
EngineRegistry / EngineAdapter
public exception hierarchy
status/capability enums
stable extras
plugin contracts
serialization contract versions
security review
threat model
documentation
migration guide
Pipeline migration
RunPipelineService migration
~~~

## Exit criteria

- public API snapshot is committed;
- accidental exports are removed;
- Pipeline is no longer canonical;
- no public TransformationGraph/OptimizedLogicalPlan/universal PhysicalPlan exists;
- import-time safety tests pass;
- security conformance is green;
- Getting Started and engine guides execute in CI;
- API docs match built artifacts.

---

# Phase G — Release Qualification

# 21. LOT-27 — 1.0 Release Candidate

**Target milestone:** 0.9.0 → 1.0.0rc1

## Scope

Run complete release qualification:

~~~text
Python support matrix
Ruff
format
mypy
unit tests
architecture tests
public API snapshot
engine conformance
wire golden fixtures
plugin conformance
optional dependency isolation
built wheel install
sdist install if published
Customer 360 transform path
security negative tests
performance review
migration examples
release notes
known limitations
release evidence manifest
~~~

## Exit criteria

- no blocker-class defect remains;
- intended stable surfaces are frozen;
- built artifacts, not source checkout, pass qualification;
- rc1 requires no architecture redesign;
- only blocker fixes are allowed after rc1 without resetting RC qualification.

---

# 22. LOT-28 — PyTransformKit 1.0.0 Stable

**Target:** 1.0.0

## Scope

- resolve RC blockers only;
- rerun full qualification;
- freeze stable public API baseline;
- freeze declared wire-contract versions;
- finalize capability matrix;
- finalize migration guide;
- finalize changelog and release notes;
- publish artifacts;
- create v1.0.0 tag;
- produce auditable release evidence.

## Stable acceptance

PyTransformKit 1.0.0 is released only when:

1. domain imports no physical-engine package;
2. TransformationPlan is the canonical authoring root;
3. LogicalPlan is the stable engine-neutral compiled IR;
4. TransformationRuntime is the canonical execution service;
5. InputBinding and OutputBinding are explicit;
6. native physical handles remain outside domain;
7. Pandas and Polars pass mandatory conformance;
8. optional engines are honestly classified;
9. relational, aggregate and window semantics are qualified;
10. logical and field lineage are first-class;
11. runtime identity and structured failure semantics are stable;
12. physical I/O remains separate from ingestion lifecycle;
13. serialization is deterministic and non-executable;
14. optimizer rules preserve semantics;
15. plugin activation is explicit;
16. public API snapshots are green;
17. clean built artifacts install on supported Python versions;
18. Customer 360 transformation path passes;
19. no blocker remains;
20. RC required no architecture redesign.

---

# 23. Revised version map

| Version line | Lots | Theme |
|---|---|---|
| 0.1.x | LOT-00 → LOT-10 | Existing baseline |
| 0.2.x | LOT-11 → LOT-14 | V1 authoring migration + relational/analytical semantics |
| 0.3.x | LOT-15 → LOT-17 | Quality, lineage, runtime evidence |
| 0.4.x | LOT-18 → LOT-20 | Arrow, DuckDB, physical I/O |
| 0.5.x | LOT-21 → LOT-23 | Wire IR, optimizer, plugins |
| 0.6.0 | LOT-24 | Cross-engine + Customer 360 transform gate |
| 0.7.0 | LOT-25 | Performance |
| 0.8.0 | LOT-26 | API/security/migration freeze |
| 1.0.0rc1 | LOT-27 | Release candidate |
| 1.0.0 | LOT-28 | Stable |

---

# 24. Current lot count

The historical numbering remains:

~~~text
LOT-00 → LOT-28
29 total lots

Completed implementation
    LOT-00 → LOT-17
    18 lots

Remaining revised roadmap
    LOT-18 → LOT-28
    11 lots
~~~

The current completion count is 18 / 29 lots. Future work continues to be judged against the revised V2 acceptance criteria rather than the old roadmap text.

---

# 25. Definition of Done for every remaining lot

A lot is DONE only when all applicable conditions hold:

- domain/API intent matches target architecture;
- implementation is typed;
- public and internal boundaries are explicit;
- architecture-import tests pass;
- unit tests pass;
- property tests pass where semantic invariants justify them;
- adapter conformance passes where applicable;
- cross-engine comparison passes where applicable;
- structured failures are used;
- security rules are covered;
- optional dependency isolation is preserved;
- Ruff/format/mypy pass;
- package builds;
- installed-wheel smoke passes;
- docs/examples are updated;
- acceptance evidence is recorded;
- no unresolved semantic ambiguity is hidden.

---

# 26. Roadmap governance

This revised roadmap is normative for LOT-11 through LOT-28.

The older ROADMAP_LOT_11_TO_1_0.md remains historical evidence of the first planning freeze but no longer controls future implementation where it conflicts with V2 architecture.

Changes to:

~~~text
lot ordering
public model
1.0 acceptance
sibling boundaries
retry ownership
serialization safety
engine-neutrality
~~~

require an explicit roadmap/specification amendment.

---

# 27. Final roadmap statement

The path to PyTransformKit 1.0 is now:

~~~text
migrate authoring/runtime vocabulary
        ↓
complete transformation semantics
        ↓
make lineage and runtime evidence first-class
        ↓
qualify additional engines and bounded I/O
        ↓
freeze portable IR and optimizer
        ↓
stabilize extensions
        ↓
prove cross-engine semantics
        ↓
freeze public API
        ↓
qualify built artifacts
        ↓
1.0.0
~~~

> **PyTransformKit reaches 1.0 by stabilizing transformation meaning first and execution backends second, while preserving a strict boundary against ingestion and workflow ownership.**
