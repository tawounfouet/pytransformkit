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
- Optional `pytransformkit[polars]` dependency extra with dedicated Polars and cross-engine CI jobs.
- `PolarsDatasetHandle` supporting both eager `DataFrame` and lazy `LazyFrame`.
- `PolarsTypeMapper` and non-materializing `PolarsSchemaInspector` using lazy Schema inspection.
- Portable Expression compilation to native Polars expressions, including canonical three-valued NULL comparison semantics.
- Polars eager and lazy execution for select, drop, rename, filter, limit, distinct, cast, derive, sort, and deduplicate.
- Explicit Polars `LAZY` capability integrated with `RunPipelineService`.
- Polars adapter contracts covering type mapping, Schema inspection, expressions, eager execution, lazy execution, and application-service integration.
- Pandas/Polars cross-engine contract tests proving equivalent results for the same logical Pipeline and equivalent UNKNOWN/NULL filter semantics.
- Completion of the initial implementation roadmap, LOT-00 through LOT-10.
- Frozen implementation roadmap for LOT-11 through LOT-28, ending with PyTransformKit 1.0.0 stable.
- Local experimentation notebook under `notebooks/`.
- Equivalent executable local experimentation script under `scripts/`.
- `docs/GETTING_STARTED.md` covering installation, first Pipeline, Pandas/Polars execution, lazy execution, and test commands.
- Immutable analytical window specifications and Pandas/Polars window execution for LOT-13.
- Logical `DurationType`, `ListType`, `StructType`, `StructField`, and `MapType` values.
- Nested Struct `FieldPath` resolution with nullability propagation.
- Portable temporal functions for date/time extraction, date conversion, timestamp normalization, timezone conversion, and duration calculation.
- Portable pivot, unpivot, explode, and flatten Transformation specifications with deterministic output Schema resolution.
- Pandas and Polars reshape, nested-Struct, and temporal execution with cross-engine conformance tests.
- Explicit `PIVOT`, `UNPIVOT`, `EXPLODE`, `FLATTEN`, `NESTED`, `TEMPORAL`, and `DURATION` engine capabilities.
- Completion of LOT-14 and the PyTransformKit 0.2.x transformation-semantics line.
- Engine-neutral `ValidationRule`, `ValidationSpec`, `ValidationPolicy`, `ValidationThreshold`, `ValidationRuleResult`, and `ValidationResult` contracts.
- Built-in `NotNull`, `Unique`, `Range`, `AllowedValues`, `Regex`, `SchemaValidation`, `RowCount`, and expression-based validation rules.
- `QualityGate` as a row- and Schema-preserving transformation checkpoint.
- Public `pytransformkit.quality` authoring DSL and `TransformationPlanBuilder.validate()`.
- Structured `QualityGateError` for blocking data-quality violations, distinct from technical execution failures.
- `FAIL_FAST`, `FAIL_AT_END`, `WARN_ONLY`, and `IGNORE` validation policies with count/rate thresholds.
- Quality evidence propagated through `EngineExecutionResult` and `TransformationResult`.
- Pandas and Polars quality evaluators with cross-engine conformance, including Polars lazy quality evaluation.
- Explicit `QUALITY` engine capability and nested-path capability propagation for quality rules.
- Logical Dataset identity preservation from `TransformationPlan` authoring through `LogicalPlan` compilation.
- Engine-neutral lineage contracts including `FieldReference`, `DatasetLineageEdge`, `FieldLineageEdge`, `FieldDependency`, `TransformationLineage`, derivation kinds and confidence levels.
- Stable lineage-confidence vocabulary: `EXACT`, `DECLARED`, `INFERRED`, `PARTIAL`, and `UNKNOWN`.
- Static `LineageAnalyzer` covering every current built-in transformation without executing physical data.
- Explicit separation between value derivation and operational field dependencies for filters, grouping, joins, ordering, windows, deduplication, distinct, quality checks, pivoting and set membership.
- Exact field lineage for rename, cast, derive, aggregate, window, join, pivot, unpivot, explode and flatten semantics.
- Declarative `ResourceReference` linkage for logical inputs and outputs without resource resolution.
- `LineageImpactAnalyzer` for transitive upstream/downstream field and logical Dataset impact analysis.
- Public `pytransformkit.lineage` namespace and `lineage.analyze()` convenience entry point.
- `LineageError` / `UnsupportedLineageError` hierarchy preventing fabricated lineage for unsupported semantics.
- Cross-engine conformance proving Pandas and Polars execution do not alter logical lineage.

### Changed

### Deprecated

### Removed

### Fixed

### Security
