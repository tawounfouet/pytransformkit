# Changelog

All notable changes to PyTransformKit will be documented in this file.

The project follows Semantic Versioning and PEP 440 for pre-release versions.

## [Unreleased]

### Added

- Repository bootstrap.
- Python package skeleton using a `src/` layout.
- Static quality, test, build, and CI configuration.
- Typed UUID-backed Shared Kernel identifiers.
- Immutable Domain `Version` and `Fingerprint` value objects.
- Initial public PyTransformKit error hierarchy and stable Schema error codes.
- Engine-independent logical DataTypes for strings, booleans, integers, floats, decimals, dates, times, timestamps, binary values, and unknown values.
- Immutable `FieldPath`, `Field`, and ordered `Schema` models.
- Schema operations for lookup, selection, drop, rename, append, and replacement.
- Immutable `DatasetMetadata` and lightweight `DatasetStatistics`.
- Portable `DatasetReference` and `LogicalDatasetReference`.
- Logical immutable `Dataset` aggregate with identity-based equality and no physical data payload.
- Unit tests for Shared Kernel, DataTypes, FieldPath, Field, Schema, Dataset metadata/statistics/references, Dataset identity, and Schema errors.
- Architecture tests preventing Domain imports from engine libraries or Infrastructure.
- Engine-independent immutable Expression AST with column references, literals, binary/unary operators, NULL predicates, and logical function calls.
- Public Expression DSL with `col()`, `lit()`, `lower()`, `upper()`, `trim()`, and `concat()`.
- Python operator overloading for comparisons, arithmetic, boolean composition, and unary logical/negation operations.
- Expression static type resolution with nullability propagation and basic numeric promotion.
- Expression dependency extraction for future lineage, projection analysis, and optimization.
- Canonical SHA-256 structural Expression fingerprints.
- Expression error hierarchy with stable `PTK-EXPR-*` error codes.
- Tests covering AST construction, bool-coercion protection, literal inference, functions, dependencies, fingerprints, and non-finite Decimal rejection.
- Immutable Transformation specifications for select, drop, rename, filter, limit, distinct, cast, derive, sort, and deduplicate.
- Explicit Transformation semantic properties for determinism, portability, purity, cardinality effects, and Schema effects.
- Cast, sort, and deduplication policies represented as engine-independent Domain values.
- Static `OutputSchemaResolver` covering the full initial Transformation set without executing data.
- Transformation error hierarchy with stable `PTK-TRANSFORM-*` codes.
- Contract tests for Transformation invariants and output Schema propagation.
- Immutable single-input/single-output Pipeline DAG with typed Input, Transformation, and Output nodes.
- Explicit data dependencies, structural graph validation, cycle detection, and deterministic topological ordering.
- Sequential immutable Pipeline DSL for select, drop, rename, filter, limit, distinct, cast, derive, sort, and deduplicate.
- Engine-independent `LogicalPlan` and `LogicalPlanNode` with statically propagated input/output Schemas.
- `PipelinePlanner` that validates and resolves the complete logical chain before physical execution.
- Public `Pipeline` export from the top-level `pytransformkit` package.
- Stable `PTK-PIPE-*` Pipeline error codes and DAG/planner contract tests.
- Portable `EngineCapability` and immutable `EngineDescriptor`.
- Runtime `DatasetHandle` and `EngineAdapter` protocols with no physical-engine dependency.
- Immutable `ExecutionContext`, `ExecutionMode`, and `EngineExecutionResult`.
- Explicit `EngineRegistry` that never performs silent engine fallback.
- Logical-plan capability analysis and pre-execution `EngineCompatibilityService`.
- Stable `PTK-ENGINE-*` and `PTK-EXEC-*` error codes.
- Engine runtime contract tests including structural protocols, explicit lookup, and missing-capability rejection.
- Optional `pytransformkit[pandas]` dependency extra with a dedicated Pandas contract CI job.
- `PandasDatasetHandle`, `PandasTypeMapper`, and conservative `PandasSchemaInspector`.
- Portable Expression compilation to Pandas Series/scalars with explicit NULL/UNKNOWN filter semantics.
- Pandas eager execution for select, drop, rename, filter, limit, distinct, cast, derive, sort, and deduplicate.
- Explicit rejection of unsupported Pandas lazy execution and mixed per-key NULL sort ordering.
- Pandas adapter contract tests covering type/schema mapping, expressions, end-to-end execution, input immutability, and unsupported semantics.
- `RunPipelineService` for explicit end-to-end application execution.
- `PipelineExecutionResult` retaining execution identity, engine descriptor, LogicalPlan, output handle, and output Schema.
- Pre-execution enforcement of requested engine identity, plan capabilities, and LAZY capability.
- Post-execution enforcement of adapter output-engine identity and LogicalPlan Schema consistency.
- Unit tests with structural fake adapters plus a Pandas integration contract for the application service.

### Changed

### Deprecated

### Removed

### Fixed

### Security
