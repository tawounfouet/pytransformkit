# Changelog

All notable changes to PyTransformKit will be documented in this file.

The project follows Semantic Versioning and PEP 440 for pre-release versions.

## [Unreleased]

No changes yet.

## [1.0.0] - 2026-10-01

### Added

- LOT-28 stable-release manifest and verifier, freezing the RC-to-stable promotion contract.
- Stable release review and final `1.0.0` release notes.
- Dedicated `stable-release-contract` CI gate preserving API hashes, wire contracts, error codes, plugin protocol and engine stability partition.

### Changed

- Promoted the qualified package from `1.0.0rc1` to `1.0.0`.
- Updated package maturity metadata to `Development Status :: 5 - Production/Stable`.
- Re-ran the full release qualification against stable wheel and sdist artifacts.

### Compatibility

- No public API category hash changed between `1.0.0rc1` and `1.0.0`.
- No serialization wire contract, public error code, plugin protocol or engine stability classification changed after RC freeze.

## [1.0.0rc1] - 2026-10-01

### Added

- LOT-27 release-candidate qualification baseline, advancing the qualification line to `0.9.0`.
- Machine-readable `contracts/release_qualification_v1.json` manifest pinning Python support, extras, engines, required CI gates, release evidence, LOT-26 public API hashes, artifact policy and the post-RC blocker-only rule.
- Deterministic `scripts/release_qualification.py` verifier that detects version, Python matrix, extras, CI-job, evidence-path, engine-partition and frozen-API drift.
- Dedicated `release-qualification-contract` CI gate that builds wheel and sdist, installs both in clean environments, runs metadata/import smoke checks, and proves the core wheel does not require Pandas, Polars, PyArrow or DuckDB.
- `docs/RELEASE_CANDIDATE_QUALIFICATION.md` defining the 0.9.0 → 1.0.0rc1 qualification sequence and blocker-only policy after rc1.
- Frozen V1 error-code catalogue with 53 public PyTransformKit exception identities, parent relationships and machine-readable `PTK-*` codes.
- Consumer compatibility snapshot covering the 0.8.0 baseline, legacy root aliases, wire contracts, error catalogue digest and plugin protocol contract.
- Dedicated `backwards-compatibility-contract` CI gate for error-code, consumer and plugin compatibility evidence.
- `docs/LOT_27_RC1_RELEASE_REVIEW.md` and `docs/RELEASE_NOTES_1_0_0rc1.md` completing the release-candidate review package.
- Promotion of the qualified package line from `0.9.0` to `1.0.0rc1`; post-RC changes are blocker-only.

### Fixed

- Extended the default plugin-protocol V1 host range from `>=0.5,<1.0` to `>=0.5,<2.0` so a default V1 plugin remains compatible with PyTransformKit `1.x`, including `1.0.0` stable. This was a controlled pre-RC compatibility correction; the LOT-26 signature baseline and consumer compatibility snapshot were amended explicitly before `1.0.0rc1`.

- LOT-25 performance and memory qualification, advancing the release line to `0.7.0`.
- Reproducible stdlib-first benchmark harness using `perf_counter_ns`, `tracemalloc`, deterministic warmups/repetitions and portable JSON reporting.
- Benchmark scenarios for plan compilation, logical optimization, expression compilation/lowering, direct adapter versus full runtime execution, native memory amplification, Polars eager/lazy execution, Pandas/Polars ↔ Arrow conversion, DuckDB eager/lazy materialization boundaries, Parquet full-scan versus source pushdown, lineage analysis and telemetry overhead.
- Native memory measurements using Pandas deep memory usage, Polars estimated size and Arrow table bytes instead of treating Python allocation peaks as total process memory.
- Explicit absolute and relative CI regression budgets in `benchmarks/budgets_ci.json`, including runtime/adapter, lazy/eager, DuckDB materialization, pushdown/full-scan and recording/null-telemetry ratios.
- Qualified `0.7.0` CI baseline committed in `benchmarks/baselines/0.7.0-ci.json`, sourced from workflow run `36817814955`.
- Performance qualification tests proving benchmarked execution-path comparisons retain equivalent results and that optimizer benchmarking preserves the logical output contract.
- Dedicated `performance-contract` CI gate that runs qualification tests, enforces budgets and uploads `performance-report.json` as an inspectable workflow artifact.


- LOT-24 cross-engine conformance and Customer 360 transformation gate, advancing the release line to `0.6.0`.
- Public qualified `pytransformkit.conformance` namespace with EngineStability, ConformanceDimension, ConformanceStatus, EngineConformanceProfile, mandatory V1 capabilities and published official-engine profiles.
- Pandas and Polars labeled STABLE and mandatory for V1; PyArrow and DuckDB labeled PROVISIONAL with explicit unsupported/provisional dimensions rather than inferred parity.
- Published `docs/ENGINE_CONFORMANCE_MATRIX.md` covering NULL/NaN, numeric promotion, Decimal, timezone, nested data, Unicode, ordering, duplicates, empty data, joins, aggregates, windows, quality, lineage, serialization, capability failure and no-hidden-fallback behavior.
- Pandas logical Decimal casts backed by Python Decimal with precision/scale enforcement and NULL-on-error behavior.
- Pandas expression null predicates now distinguish preserved floating-point NaN from logical NULL instead of treating every NaN as null.
- New LOT-24 conformance contracts for NULL/NaN distinction, integer/float promotion, fixed-precision Decimal aggregation, Unicode normalization, deterministic ordering, duplicate elimination, empty datasets, explicit unsupported capability failure and explicit-engine no-fallback behavior.
- Canonical Customer 360 multi-input TransformationPlan covering paid-order filtering, aggregation, left join, email normalization, data quality, projection and deterministic ordering.
- Customer 360 qualified on Pandas eager, Polars eager and Polars lazy with equivalent normalized results, canonical serialization, transitive field lineage and Parquet ResourceReference output handoff.
- Dedicated `conformance-contract` CI gate running both the existing cross-engine suite and the new LOT-24 release contracts.


- LOT-23 extension and plugin architecture, completing the `0.5.0` line.
- Public qualified `pytransformkit.plugins` namespace exposing PluginRegistry, PluginDescriptor, PluginCompatibility, PluginKind, PluginActivationContext, EngineAdapter, Reader, Writer, ResourceResolver, FunctionExtension, OptimizerRule and TelemetrySink contracts.
- Entry-point discovery under `pytransformkit.plugins` that records metadata without importing plugin code; `EntryPoint.load()` is called only from explicit `activate(plugin_id)`.
- Machine-checkable framework and plugin-protocol compatibility ranges with plugin API version 1.
- Explicit FunctionRegistry, OptimizerRuleRegistry, ResourceResolverRegistry and TelemetrySinkRegistry with deterministic duplicate/conflict handling.
- Freeze semantics for PluginRegistry, EngineRegistry, ResourceIORegistry and extension registries so runtime configuration can become immutable before execution.
- Explicit extension optimizer rules integrated into LogicalOptimizer with rule provenance and bounded optimizer passes.
- LocalFilePathResolver conformance to the public ResourceResolver protocol while retaining configured-root confinement.
- Stable plugin error hierarchy for not-found, conflicts, compatibility failures, activation failures and frozen-registry mutation.
- Security tests proving PluginDescriptor is not accepted by the closed safe wire semantic registry and importing the plugin namespace does not trigger discovery.
- Built-in conformance tests for Pandas, Polars, PyArrow and DuckDB EngineAdapter implementations, local Reader/Writer/ResourceResolver implementations, and NullTelemetrySink.
- Dedicated plugin-contract CI gate covering discovery/activation separation, compatibility, conflicts, freezing, protocol conformance and wire-security boundaries.


- LOT-22 engine-neutral Logical Optimizer targeting `0.5.0a2`.
- Public `LogicalOptimizer`, `OptimizationResult`, `OptimizationReport`, rule-application provenance, optimizer diagnostics, and `ExpressionOptimizer` planning APIs without introducing a public `OptimizedLogicalPlan`.
- Conservative fixed-point rewrites for constant folding, boolean simplification, predicate pushdown through safe unbranched Select/Sort boundaries, projection pruning for successive selections, and dead-node elimination.
- Deterministic post-rewrite Schema resolution so every optimized LogicalPlan remains statically valid before physical lowering.
- Common-expression fingerprint analysis, safe-fusion hints, and explicit materialization-boundary diagnostics for multi-input, aggregate, quality, cardinality and reshape boundaries.
- Explicit optimizer disable mode preserving the original LogicalPlan and fingerprint.
- Hypothesis property tests for constant/boolean simplification, lineage-preservation regression tests, and Pandas execution-equivalence contracts for optimized versus original plans.
- Dedicated optimizer CI contract gate; optimizer implementation imports no physical engine libraries and leaves engine-specific lowering to adapters.


- LOT-21 versioned serialization and canonical IR targeting `0.5.0a1`.
- Public `pytransformkit.serialization` namespace with codecs for DataType, Field, Schema, Expression, TransformationPlan, LogicalPlan, ResourceReference, TransformationExecutionReference, TransformationLineage, Diagnostic, and ExecutionManifest.
- Canonical JSON with UTF-8, Unicode NFC normalization, deterministic key ordering, compact separators, strict finite-number handling, typed collections, and exact durable representations for UUID/Decimal/date/time/datetime/bytes.
- Closed semantic type registry with stable PyTransformKit semantic tags and no payload-controlled Python module/class imports.
- Strict envelope decoding with explicit `contract` and integer `contract_version`, duplicate-key rejection, unknown-field/type rejection, payload-size and nesting-depth limits, and fail-closed handling of future versions.
- Explicit contiguous wire migration hooks through `MigrationRegistry`; package version and wire contract version remain independent.
- Portable `TransformationExecutionReference` DTO for inter-framework execution references.
- Semantic SHA-256 fingerprints for Expression, TransformationPlan, and LogicalPlan codecs while preserving existing identity-independent plan semantics.
- Golden v1 fixtures for ResourceReference, Schema, and Expression plus deterministic round-trip, migration, security-negative, plan/logical-plan, lineage, diagnostic, and manifest conformance tests.
- Dedicated serialization CI contract gate and explicit prohibition of pickle/cloudpickle/dill/eval/exec reconstruction paths.

- LOT-20 physical I/O and resource boundary, completing the `0.4.0` line.
- Portable `CredentialReference`, `ResourceFormat`, `RetrySafety`, `WriteMode`, and `WriteStatus` values with no raw secret material.
- Explicit `ReadRequest` / `ReadResult` and `WriteRequest` / `WriteResult` contracts plus Reader/Writer protocols and `ResourceIORegistry`.
- Local filesystem Reader/Writer profile with configured-root confinement for CSV, JSONL, Parquet, and Arrow IPC.
- Parquet projection/predicate pushdown and Hive partition pruning with structured pushdown evidence; non-Parquet post-scan filtering/projection is reported explicitly.
- Arrow I/O bridge protocols allowing resource reads and physical writes across Pandas, Polars, PyArrow, and DuckDB without engine types entering the Domain.
- Resource-backed `InputBinding` resolution and physical `OutputBinding` materialization in `TransformationRuntime`.
- Physical input/output ResourceReference links preserved in transformation lineage.
- Typed physical write modes, explicit retry-safety declarations, and reconciliation-required `UNKNOWN_OUTCOME` propagation for uncertain writes.
- Optional `pytransformkit[io]` dependency and dedicated physical-I/O contract gate in CI.

- LOT-19 DuckDB relational SQL backend targeting `0.4.0a2`.
- Optional `pytransformkit[duckdb]` dependency with Arrow-backed relation binding.
- `DuckDBDatasetHandle`, logical/native type mapping, conservative relation Schema inspection, and safe SQL identifier quoting.
- Parameterized logical-expression lowering that keeps runtime values outside generated SQL text.
- CTE-backed lowering for projections, filters, limits, distinct, casts, derivations, sorting, joins, set operations, grouped/global aggregates, and analytical windows.
- Explicit SQL NULL join lowering using `IS NOT DISTINCT FROM` for MATCH and ordinary equality for NEVER_MATCH.
- Explicit caller-owned versus framework-owned connection lifecycle with no implicit commit and no closing of user-owned connections.
- Eager materialized and lazy relational execution paths, Arrow interchange, and native DuckDB `EXPLAIN`.
- Dedicated DuckDB adapter and DuckDB/Pandas cross-engine conformance jobs in CI.

- LOT-18 PyArrow adapter and interchange line targeting `0.4.0a1`.
- Optional `pytransformkit[pyarrow]` dependency with `PyArrowDatasetHandle` for `Table` and `RecordBatch`.
- Arrow logical/native type mapping and Schema inspection covering nested, decimal, temporal, duration, binary, list, struct, and map types.
- Eager PyArrow execution for the explicitly qualified select/drop/rename/filter/limit/derive/sort capability subset.
- Chunk-preserving Arrow execution with no implicit `combine_chunks()`.
- Strict-by-default Pandas ↔ Arrow and Polars ↔ Arrow interchange with structured conversion-lossiness diagnostics.
- Dedicated PyArrow and Arrow-interchange contract jobs in CI.

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
- First-class `TransformationExecution` records with terminal `ExecutionStatus`, timestamps, engine descriptor, diagnostics, failure evidence, retry evidence and cancellation metadata.
- `CorrelationContext` / `CorrelationId` propagation kept distinct from native `TransformationExecutionId` identity.
- Deterministic SHA-256 `LogicalPlan` fingerprints excluding random execution, node, step and Dataset identities while preserving transformation semantics.
- Structured `FailureEvidence` with stable failure categories, retryability and uncertainty, including reconciliation-required `UNKNOWN_OUTCOME`.
- Typed runtime failures for timeout, confirmed cancellation, unknown outcome and adapter contract violations, with structured execution evidence attached to public PyTransformKit exceptions.
- Immutable `ExecutionManifest` containing portable execution evidence without active handles or raw secrets.
- Vendor-neutral runtime lifecycle events, low-cardinality metrics, completed trace spans and a `TelemetrySink` protocol.
- Conservative telemetry redaction and explicit rejection of execution/correlation IDs as default metric labels.
- Best-effort telemetry isolation: sink failures emit diagnostics and never replay transformation computation.
- `ProviderRetryEvidence` propagation for bounded engine/provider retries without adding workflow-level retry ownership to PyTransformKit.
- Process-local `CancellationToken` plus `CancellationSupport` capability metadata distinguishing requests, unsupported cancellation and confirmed cancellation.
- `TransformationResult` now carries runtime execution evidence, logical lineage, plan fingerprint and execution manifest.
- Public `pytransformkit.diagnostics` namespace and expanded `pytransformkit.runtime` evidence surface.
- Completion of LOT-17 and the PyTransformKit 0.3.x runtime-evidence line.

### Changed

### Deprecated

### Removed

### Fixed

### Security
