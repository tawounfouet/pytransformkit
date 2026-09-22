# PyTransformKit — Frozen Implementation Roadmap

> **Roadmap status:** FROZEN  
> **Roadmap version:** 1.0  
> **Frozen on:** 2026-09-22  
> **Scope:** LOT-11 through LOT-28 / PyTransformKit 1.0.0  
> **Baseline:** LOT-00 through LOT-10 completed and qualified

---

## 1. Purpose

This document is the normative implementation roadmap from the end of the first
engine-agnostic cycle through the first stable PyTransformKit release.

The roadmap is intentionally ordered by architectural dependency:

```text
Relational semantics
        ↓
Analytical semantics
        ↓
Quality / Lineage / Observability
        ↓
Arrow / DuckDB / I/O
        ↓
Serialization / IR / Optimization
        ↓
Plugins
        ↓
Cross-engine conformance
        ↓
Performance
        ↓
Public API stabilization
        ↓
Release qualification
        ↓
1.0.0
```

The objective is not to maximize feature count. The objective is to preserve one
canonical logical model while progressively increasing the number of capabilities
and execution backends that conform to it.

---

## 2. Baseline at roadmap freeze

The first implementation cycle is complete:

| Lot | Scope | Status |
|---|---|---|
| LOT-00 | Repository Bootstrap | DONE |
| LOT-01 | Shared Kernel | DONE |
| LOT-02 | Type System & Schema Core | DONE |
| LOT-03 | Dataset Domain Model | DONE |
| LOT-04 | Expression AST Core | DONE |
| LOT-05 | Transformation Model MVP | DONE |
| LOT-06 | Pipeline & DAG Core | DONE |
| LOT-07 | Engine Runtime Contracts | DONE |
| LOT-08 | Pandas Reference Adapter | DONE |
| LOT-09 | Application Execution Service | DONE |
| LOT-10 | Polars Adapter & Multi-Engine Contract | DONE |

The baseline therefore already proves:

- Domain independence from physical engines;
- immutable logical Schemas, Datasets, Expressions and Transformations;
- Pipeline/DAG and LogicalPlan generation;
- explicit engine registration and execution;
- Pandas eager execution;
- Polars eager and lazy execution;
- Pandas/Polars semantic conformance for the initial Transformation set;
- optional engine dependencies;
- CI qualification on Python 3.11 through 3.14.

---

## 3. Roadmap governance

This roadmap is **frozen**.

A lot may be refined internally, but its architectural purpose and exit criteria
must not be silently changed. Any material change to ordering, lot boundaries,
or the 1.0.0 acceptance criteria requires an explicit roadmap amendment.

Rules:

1. A lot is not DONE because code exists; it is DONE only when its exit criteria pass.
2. A capability is not SUPPORTED until its contract tests pass.
3. Cross-engine semantic equivalence takes precedence over native convenience.
4. No engine-specific type may leak into Domain.
5. No silent engine fallback is allowed.
6. Unsupported semantics must fail explicitly.
7. Logical lineage must survive physical optimization.
8. Observability must never fabricate metrics that the physical engine cannot provide.
9. Serialization formats are versioned independently from the Python package version.
10. Public API stabilization happens only after the engine and semantic model have been exercised by multiple adapters.

---

# Phase A — Relational and Analytical Semantics

## LOT-11 — Relational Transformations Core

**Target:** `0.2.0a1`

### Scope

Introduce portable multi-input relational transformations:

- `JoinTransformation`;
- `UnionTransformation`;
- `IntersectTransformation`;
- `ExceptTransformation`;
- `JoinType`: INNER, LEFT, RIGHT, FULL, SEMI, ANTI, CROSS;
- equality join keys;
- composite join keys;
- explicit NULL join semantics;
- output Schema resolution;
- collision/suffix policy;
- capability declarations;
- Pandas and Polars implementations;
- cross-engine contract tests.

### Architectural objective

Move Pipeline execution from the current unary linear transformation model toward
portable multi-input relational semantics without coupling the Domain to SQL or any
specific DataFrame API.

### Exit criteria

- Join/set operations are represented entirely in Domain.
- Schema resolution is static and deterministic.
- Pipeline DAG can represent the required multi-input dependencies.
- Pandas and Polars implementations pass the same semantic contract.
- NULL, collision, duplicate-column and empty-input behavior are explicitly tested.

---

## LOT-12 — Aggregation and Grouping

**Target:** `0.2.0a2`

### Scope

Add:

- `AggregateTransformation`;
- grouping keys;
- aggregate expressions;
- COUNT, SUM, MIN, MAX, MEAN;
- COUNT DISTINCT;
- null-aware aggregation semantics;
- output type inference;
- aggregation Expression context;
- post-aggregation filtering through ordinary logical composition;
- Pandas and Polars compilers/executors.

### Architectural objective

Prove that the Expression AST can represent row, aggregate and grouped semantics
without introducing engine-native expressions into Domain.

### Exit criteria

- Aggregate expressions are statically typed.
- Illegal row/aggregate expression mixing is rejected before execution.
- Result Schemas are statically resolved.
- Cross-engine aggregate semantics pass.

---

## LOT-13 — Window and Analytical Transformations

**Target:** `0.2.0b1`

### Scope

Add portable window semantics:

- partition specification;
- ordering specification;
- window frame model;
- ROW_NUMBER;
- RANK / DENSE_RANK;
- LAG / LEAD;
- cumulative SUM / COUNT / MIN / MAX;
- moving aggregates;
- null and ordering semantics;
- Pandas and Polars execution where semantically equivalent.

### Architectural objective

Extend the Expression model from row/aggregate contexts to analytical contexts while
keeping window definitions serializable and engine-independent.

### Exit criteria

- Window specifications are immutable Domain values.
- Ordering requirements are explicit.
- Non-deterministic windows are diagnosed.
- Pandas/Polars contract suite covers ranking, offsets and cumulative operations.

---

## LOT-14 — Reshaping, Temporal and Nested Data

**Target:** `0.2.0`

### Scope

Complete the main transformation vocabulary:

- pivot;
- unpivot;
- explode;
- flatten;
- nested FieldPath resolution;
- List / Struct / Map semantics where supported;
- date/time extraction;
- timestamp normalization;
- timezone conversion;
- duration handling;
- explicit unsupported cases per engine.

### Architectural objective

Close the first broad transformation-capability layer before quality and metadata
become first-class runtime concerns.

### Exit criteria

- Transformation capability matrix is updated.
- Unsupported nested/temporal operations fail explicitly.
- Schema changes are predictable and tested.
- `0.2.x` relational/analytical line is qualified end-to-end.

---

# Phase B — Data Quality, Lineage and Runtime Evidence

## LOT-15 — Data Quality and Validation

**Target:** `0.3.0a1`

### Scope

Implement the validation model:

- `ValidationRule`;
- immutable Validation specs;
- NotNull;
- Unique;
- Range;
- AllowedValues;
- Regex;
- Schema validation;
- RowCount;
- expression-based validation;
- ValidationResult;
- ValidationPolicy;
- FAIL_FAST / FAIL_AT_END / WARN_ONLY / IGNORE;
- threshold support;
- QualityGate;
- validation Pipeline nodes.

### Architectural objective

Make expected data-quality failures structured results rather than technical
exceptions, and only convert them into execution failure when policy requires it.

### Exit criteria

- Validation results are engine-independent.
- Validation execution failures and data violations are distinct.
- Pandas and Polars implement the same core validation contracts.
- Quality gates integrate with Pipeline execution.

---

## LOT-16 — Lineage and Metadata

**Target:** `0.3.0a2`

### Scope

Implement:

- Dataset lineage;
- field-level lineage;
- Expression dependency extraction integration;
- derivation kinds;
- selection / grouping / join / window dependencies;
- physical resource references;
- execution provenance;
- metadata propagation;
- classification propagation;
- lineage completeness;
- impact analysis primitives.

### Architectural objective

Make logical lineage derivable without executing data, while recording runtime
physical provenance separately.

### Exit criteria

- Every built-in Transformation has a lineage resolver.
- Field lineage survives rename, cast, derive, aggregate, join and window operations.
- Physical engine conversion does not create false logical Dataset lineage.
- Sensitive raw values are never required for lineage.

---

## LOT-17 — Observability, Metrics and Audit

**Target:** `0.3.0`

### Scope

Implement:

- execution metrics;
- step metrics;
- diagnostics;
- structured warnings;
- runtime lifecycle events;
- execution summaries;
- audit events;
- Actor model;
- ObservabilitySink;
- AuditSink;
- redaction;
- clock/timer abstraction;
- BASIC / DETAILED observability levels.

### Architectural objective

Provide runtime evidence without forcing materialization and without fabricating
per-step measurements for fused/lazy physical execution.

### Exit criteria

- Pandas and Polars emit the minimum observability contract.
- Lazy execution never invents unavailable step metrics.
- sensitive data is redacted by default.
- `0.3.x` quality/lineage/observability line is qualified.

---

# Phase C — Columnar, Relational and I/O Backends

## LOT-18 — PyArrow Adapter and Interchange Layer

**Target:** `0.4.0a1`

### Scope

Implement:

- `PyArrowDatasetHandle`;
- Table and RecordBatch support;
- Arrow Schema inspection;
- TypeMapper;
- Expression compiler;
- Transformation compiler;
- eager execution;
- nested types;
- chunk-aware execution;
- Arrow conversion bridge;
- conversion diagnostics;
- strict conversion policy;
- Pandas ↔ Arrow and Polars ↔ Arrow paths.

### Architectural objective

Use Arrow as an optional execution and interchange backend without making Arrow the
Domain's canonical representation.

### Exit criteria

- Core imports with no Arrow dependency.
- Arrow contracts pass for supported capabilities.
- conversions report lossiness explicitly.
- nested and temporal type mappings are qualified.

---

## LOT-19 — DuckDB Adapter and Relational SQL Backend

**Target:** `0.4.0a2`

### Scope

Implement:

- DuckDB relation handle;
- connection/session ownership model;
- TypeMapper;
- parameterized SQL expression compilation;
- safe identifier quoting;
- relational Transformation compilation;
- joins;
- aggregations;
- windows;
- CTE/subquery physical planning;
- Arrow interchange;
- lazy relational execution;
- native explain support.

### Architectural objective

Prove that the same LogicalPlan can target a relational/SQL engine, not only
DataFrame-style engines.

### Exit criteria

- No raw value interpolation into generated SQL.
- user-owned connections are not closed or committed implicitly.
- SQL is a physical representation, never a Domain primitive.
- DuckDB contract suite passes relational and analytical semantics.

---

## LOT-20 — I/O and Connectors

**Target:** `0.4.0`

### Scope

Implement the I/O model:

- SourceSpec;
- SinkSpec;
- Reader / Writer ports;
- ResourceReference;
- ReadRequest / ReadResult;
- WriteRequest / WriteResult;
- CSV;
- JSON / JSONL;
- Parquet;
- Arrow IPC;
- local filesystem;
- projection pushdown;
- predicate pushdown;
- partition pruning where available;
- write modes;
- credential references;
- explicit retry safety.

### Architectural objective

Separate where data lives from how transformations execute.

### Exit criteria

- I/O is not modeled as Transformation.
- credentials are absent from serializable portable specs.
- pushdown preserves logical lineage.
- writes expose uncertain outcome explicitly.
- `0.4.x` backend/I/O line is qualified.

---

# Phase D — Portable Plans, Optimization and Extensibility

## LOT-21 — Serialization and Canonical Transformation IR

**Target:** `0.5.0a1`

### Scope

Implement:

- canonical serializable Transformation IR;
- Pipeline serialization;
- Expression AST serialization;
- Schema serialization;
- versioned format envelope;
- JSON representation;
- deterministic canonical ordering;
- semantic fingerprints;
- round-trip validation;
- compatibility/version checks;
- safe deserialization.

### Architectural objective

Make a Pipeline portable across processes and environments without Python pickle or
engine-native objects.

### Exit criteria

- equivalent logical plans serialize identically.
- serialization is deterministic.
- unsafe arbitrary Python imports are impossible through the portable format.
- format version is independent from package version.

---

## LOT-22 — Lazy Planner and Logical Optimizer

**Target:** `0.5.0a2`

### Scope

Implement optimizer infrastructure and safe rules:

- dead-node elimination;
- projection pushdown;
- predicate pushdown;
- limit/slice pushdown;
- constant folding;
- boolean simplification;
- transformation fusion hints;
- common expression analysis;
- materialization boundaries;
- logical/physical plan distinction;
- explain logical vs optimized plan;
- optimizer rule provenance.

### Architectural objective

Optimize the logical plan without changing semantic results or corrupting lineage.

### Exit criteria

- every optimization rule has equivalence tests.
- optimizer can be disabled.
- lineage maps optimized physical work back to logical nodes.
- no optimizer rule depends on one engine's native syntax.

---

## LOT-23 — Extension and Plugin Architecture

**Target:** `0.5.0`

### Scope

Implement:

- RuntimeBuilder;
- typed registries;
- engine plugins;
- connector plugins;
- Transformation plugins;
- function plugins;
- Validation plugins;
- serializer/exporter/sink plugins;
- explicit registration;
- optional Python entry-point discovery;
- namespace policy;
- compatibility checks;
- plugin provenance;
- registry freezing;
- dependency and conflict errors.

### Architectural objective

Allow ecosystem extension without adding engine/vendor-specific conditionals to Core.

### Exit criteria

- built-ins can use the same extension contracts.
- plugin discovery is optional and side-effect controlled.
- duplicate registrations fail explicitly.
- plugin requirements can be preflighted before execution.
- `0.5.x` portable-plan/optimization/plugin line is qualified.

---

# Phase E — Conformance and Performance Qualification

## LOT-24 — Cross-Engine Conformance Matrix

**Target:** `0.6.0`

### Scope

Expand the semantic contract suite across:

- Pandas;
- Polars eager;
- Polars lazy;
- PyArrow;
- DuckDB.

Qualify:

- NULL / NaN;
- numeric promotion;
- Decimal;
- temporal/timezone;
- nested data;
- string/Unicode;
- ordering;
- duplicates;
- empty datasets;
- joins;
- aggregates;
- windows;
- validation;
- lineage invariance;
- serialization invariance.

### Architectural objective

Turn engine-agnostic semantics from an architectural claim into a continuously
verified compatibility matrix.

### Exit criteria

- one published capability/conformance matrix exists.
- supported capabilities have cross-engine contract evidence.
- partial/unsupported capabilities are explicit.
- no silent semantic downgrade is accepted.

---

## LOT-25 — Performance, Memory and Benchmark Qualification

**Target:** `0.7.0`

### Scope

Implement and qualify:

- benchmark datasets;
- benchmark scenarios;
- planner overhead measurement;
- expression compilation overhead;
- memory amplification checks;
- conversion-cost measurement;
- eager vs lazy comparison;
- Arrow chunk behavior;
- DuckDB relational materialization boundaries;
- performance budgets;
- regression thresholds;
- benchmark reporting.

### Architectural objective

Ensure abstraction overhead remains controlled and observability does not accidentally
force expensive materialization.

### Exit criteria

- reproducible benchmark suite exists.
- performance regressions are detectable in CI or scheduled qualification.
- conversion and materialization costs are observable.
- no optimization changes public semantics.

---

# Phase F — Public API Stabilization

## LOT-26 — Public API, Documentation, Security and Compatibility

**Target:** `0.8.0`

### Scope

Stabilize:

- public imports;
- naming;
- exceptions and error codes;
- function signatures;
- typing;
- package extras;
- plugin API;
- serialization compatibility policy;
- deprecation policy;
- migration guidance;
- security model;
- threat-model review;
- documentation site;
- tutorials;
- API reference;
- engine capability documentation;
- examples.

### Architectural objective

Convert the internally coherent framework into a supportable public library contract.

### Exit criteria

- intended 1.0 public symbols are explicitly listed.
- accidental internal symbols are not public API.
- deprecation and compatibility policies are documented.
- security assumptions are explicit.
- all examples execute in CI.
- documentation covers Pandas, Polars, Arrow and DuckDB paths.

---

# Phase G — Release Qualification

## LOT-27 — 1.0 Release Candidate Qualification

**Target:** `0.9.0` → `1.0.0rc1`

### Scope

Final qualification:

- full CI matrix;
- full engine contract matrix;
- serialization compatibility suite;
- plugin compatibility suite;
- package installation from built artifacts;
- clean-environment tests;
- Python 3.11–3.14 qualification;
- optional-dependency isolation;
- backwards-compatibility snapshots;
- error-code catalog validation;
- security review;
- performance regression review;
- documentation review;
- release notes;
- migration notes;
- release-candidate publication.

### Exit criteria

- no open blocker-class defects.
- all 1.0 mandatory capabilities are STABLE.
- all release artifacts install and execute in clean environments.
- rc package is exercised without architecture changes.
- only blocker fixes are permitted after rc1.

---

## LOT-28 — PyTransformKit 1.0.0 Stable Release

**Target:** `1.0.0`

### Scope

- resolve rc blocker defects only;
- rerun the complete qualification matrix;
- freeze public API;
- freeze serialization format version for 1.0;
- finalize changelog;
- finalize release notes;
- build signed/reproducible release artifacts where supported;
- create Git tag `v1.0.0`;
- publish the stable package;
- publish the final capability matrix and compatibility policy.

### 1.0.0 acceptance criteria

PyTransformKit 1.0.0 is released only when:

1. Domain has zero imports from physical engine packages.
2. Pandas, Polars, PyArrow and DuckDB adapters are independently optional.
3. the canonical Transformation vocabulary is statically typed and serializable.
4. relational, aggregate and window semantics are contract-tested.
5. Data Quality, Lineage and Observability are first-class.
6. Pipeline and Transformation IR round-trip deterministically.
7. optimizer rules are semantics-preserving and test-backed.
8. plugin contracts are versioned and qualified.
9. the cross-engine conformance matrix is published.
10. public error codes are stable.
11. public API and deprecation policies are documented.
12. clean installs pass on supported Python versions.
13. all mandatory CI and contract gates are green.
14. no known blocker remains.
15. the release candidate required no architectural redesign.

---

# 4. Version map

| Version line | Lots | Theme |
|---|---|---|
| `0.1.x` | LOT-00 → LOT-10 | Core, Pandas, Polars, first multi-engine proof |
| `0.2.x` | LOT-11 → LOT-14 | Relational and analytical semantics |
| `0.3.x` | LOT-15 → LOT-17 | Quality, lineage, observability |
| `0.4.x` | LOT-18 → LOT-20 | Arrow, DuckDB, I/O |
| `0.5.x` | LOT-21 → LOT-23 | Serialization/IR, optimizer, plugins |
| `0.6.0` | LOT-24 | Cross-engine conformance |
| `0.7.0` | LOT-25 | Performance qualification |
| `0.8.0` | LOT-26 | Public API and documentation stabilization |
| `0.9.0 / 1.0.0rc1` | LOT-27 | Release candidate |
| `1.0.0` | LOT-28 | Stable release |

---

# 5. Final lot count

The frozen roadmap contains:

```text
LOT-00 → LOT-28
29 total implementation lots
```

At the time of this freeze:

```text
Completed : LOT-00 → LOT-10 = 11 lots
Remaining : LOT-11 → LOT-28 = 18 lots
Total     : 29 lots
```

Progress by lot count:

```text
11 / 29 complete
≈ 37.9 %
```

This percentage measures roadmap-lot completion only. It is not a claim about code
volume, effort, calendar duration, or product maturity.

---

# 6. Dependency chain

```text
LOT-11  Relational Transformations
   ↓
LOT-12  Aggregations
   ↓
LOT-13  Windows
   ↓
LOT-14  Reshaping / Temporal / Nested
   ↓
LOT-15  Data Quality
   ↓
LOT-16  Lineage / Metadata
   ↓
LOT-17  Observability / Audit
   ↓
LOT-18  PyArrow
   ↓
LOT-19  DuckDB
   ↓
LOT-20  I/O / Connectors
   ↓
LOT-21  Serialization / IR
   ↓
LOT-22  Lazy Planner / Optimizer
   ↓
LOT-23  Plugins
   ↓
LOT-24  Cross-Engine Conformance
   ↓
LOT-25  Performance Qualification
   ↓
LOT-26  Public API Stabilization
   ↓
LOT-27  Release Candidate
   ↓
LOT-28  1.0.0 Stable
```

Some implementation work may be prepared in parallel, but a lot is not formally
closed before the architectural dependencies needed by its acceptance criteria exist.

---

# 7. Definition of Done for every future lot

A future lot is DONE only when all applicable conditions hold:

- Domain/API design is explicit.
- implementation is typed.
- errors use canonical PyTransformKit exceptions.
- new capabilities are registered in the capability model.
- unit tests pass.
- architecture tests pass.
- adapter-specific contract tests pass.
- cross-engine tests pass where multiple engines support the capability.
- Ruff passes.
- formatting passes.
- mypy passes.
- package build passes.
- Python support matrix passes.
- optional dependency isolation is preserved.
- README/changelog/roadmap status is updated.
- no known semantic ambiguity remains undocumented.

---

# 8. Roadmap freeze statement

From this point onward, **LOT-11 through LOT-28 are the official PyTransformKit path
to 1.0.0**.

New ideas may be added to the backlog, but they do not enter the 1.0 roadmap unless
one of the following is true:

- they are required to satisfy an existing lot's acceptance criteria;
- they correct a semantic or architectural defect;
- the roadmap is explicitly amended.

Everything else is deferred beyond 1.0.

