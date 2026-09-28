# PyTransformKit Specifications

This directory contains the numbered functional and architectural specifications that define PyTransformKit.

Implementation should follow these specifications while allowing evidence from real code and tests to refine provisional design decisions.

The first implementation is driven by:

- repository bootstrap;
- shared kernel;
- logical data type and schema model;
- Dataset domain model;
- Expression AST;
- Select / Filter / Derive transformations;
- Pipeline and LogicalPlan.


## Frozen implementation roadmap

The normative path from the completed first multi-engine cycle to the stable release
is defined in:

- `../ROADMAP_LOT_11_TO_1_0.md`

This roadmap freezes `LOT-11` through `LOT-28`, with `LOT-28` producing
PyTransformKit `1.0.0`.

## Ecosystem architecture

Cross-framework architecture and vocabulary are defined in:

- `PYTRANSFORMKIT_PYINGESTKIT_PYWORKFLOWKIT_BOUNDARIES_AND_INTEGRATION.md` — bounded contexts, ownership and integration rules;
- `PYKIT_ECOSYSTEM_V2_ARCHITECTURE_AND_CANONICAL_VOCABULARY.md` — normative clean-slate V2 architecture and canonical public vocabulary for PyIngestKit, PyTransformKit and PyWorkflowKit.

The V2 vocabulary baseline is intended to drive the future PyIngestKit 2.0 and PyWorkflowKit 2.0 redesigns and the pre-1.0 PyTransformKit API cleanup.

- `PYKIT_ECOSYSTEM_V2_PUBLIC_API_DESIGN_PRINCIPLES.md` — normative cross-framework rules for authoring APIs, immutable domain values, runtime separation, validation layers, canonical verbs, package-root exports, typed results, errors, extensions and API conformance.

- `PYKIT_ECOSYSTEM_V2_SHARED_CONTRACTS_AND_REFERENCE_MODEL.md` — normative cross-framework contract vocabulary for references, identifiers, locators, execution references, correlation, ownership, resolution, versioning and anti-corruption boundaries without introducing a mandatory shared core package.

- `PYKIT_ECOSYSTEM_V2_EXECUTION_IDENTITY_AND_CORRELATION_MODEL.md` — normative execution identity model for WorkflowRunId, TaskRunId, TaskAttemptId, IngestionRunId, TransformationExecutionId, correlation, causation, retry/recovery identity and cross-runtime propagation.

- `PYKIT_ECOSYSTEM_V2_ERROR_FAILURE_RETRY_AND_UNCERTAINTY_MODEL.md` — normative failure semantics for error categories, retryability, idempotency, retry ownership, timeout, cancellation, unknown outcomes, reconciliation, recovery, replay and bounded retry across PyIngestKit, PyTransformKit and PyWorkflowKit.

- `PYKIT_ECOSYSTEM_V2_DATASET_RESOURCE_AND_ARTIFACT_INTEROPERABILITY.md` — normative interoperability model for Source, Resource, Artifact, RAW, Dataset, DatasetVersion, PhysicalHandle, bindings, materialization, publication, portability, retention and cross-framework data handoff.

- `PYKIT_ECOSYSTEM_V2_LINEAGE_PROVENANCE_AND_TRACEABILITY_MODEL.md` — normative model for ingestion provenance, logical and field-level transformation lineage, workflow/task execution lineage, replay/recovery traceability, cross-framework composition and lineage confidence.

- `PYKIT_ECOSYSTEM_V2_OBSERVABILITY_EVENTS_AND_TELEMETRY_MODEL.md` — normative observability model for events, logs, metrics, traces, diagnostics, manifests, correlation propagation, telemetry sinks, redaction, cardinality control and cross-framework aggregation.

- `PYKIT_ECOSYSTEM_V2_INTEGRATION_AND_ANTI_CORRUPTION_LAYER_MODEL.md` — normative cross-framework integration model defining allowed dependency directions, anti-corruption layers, provider/consumer responsibilities, adapter contracts, retry/cancellation/recovery boundaries, optional dependencies and producer-consumer conformance tests.

- `PYKIT_ECOSYSTEM_V2_DEPENDENCY_PACKAGING_AND_OPTIONAL_EXTRAS_STRATEGY.md` — normative packaging strategy for core versus optional dependencies, sibling integration extras, backend extras, plugin discovery/activation, version ranges, import isolation, CI compatibility matrices and package-graph enforcement.

- `PYKIT_ECOSYSTEM_V2_SERIALIZATION_AND_WIRE_CONTRACTS.md` — normative wire-contract model for explicit contract IDs and versions, canonical JSON, strict decoding, fingerprints, migrations, golden fixtures, safe serialization, historical compatibility and cross-framework payload conformance.

- `PYKIT_ECOSYSTEM_V2_ARCHITECTURE_CONFORMANCE_AND_TEST_STRATEGY.md` — normative architecture-as-code strategy covering invariant traceability, import boundaries, domain purity, engine/connector conformance, retry/recovery fault injection, wire golden fixtures, packaging matrices, reference-application scenarios and release qualification evidence.

- `PYKIT_ECOSYSTEM_V2_SECURITY_AND_TRUST_BOUNDARIES.md` — normative security baseline for trust boundaries, credential references, least privilege, resource validation, plugin activation, executable-code surfaces, subprocess isolation, telemetry redaction, multi-tenant posture and security conformance.

- `PYKIT_ECOSYSTEM_V2_REFERENCE_APPLICATION_SPEC.md` — normative Customer 360 reference application proving end-to-end composition across PyIngestKit, PyTransformKit and PyWorkflowKit, including DatasetVersion handoff, publication boundaries, execution identity, lineage, observability, serialization, retry, recovery and security scenarios.

- `PYKIT_ECOSYSTEM_V2_RELEASE_COMPATIBILITY_AND_VERSIONING_POLICY.md` — normative policy for independent package versioning, stability levels, SemVer, wire/plugin/event version separation, tested sibling compatibility ranges, deprecation, migration, release candidates, artifact qualification and auditable release evidence.

- `PYKIT_ECOSYSTEM_V2_IMPLEMENTATION_SEQUENCE_AND_MIGRATION_PLAN.md` — normative implementation order for PyTransformKit 1.0, PyIngestKit 2.0 and PyWorkflowKit 2.0, including public-model rationalization, portable contracts, migration strategy, sibling-integration gates, Customer 360, conformance phases and stable-release sequencing.

- `PYKIT_ECOSYSTEM_V2_END_TO_END_ACCEPTANCE_CRITERIA.md` — normative ecosystem release gate aggregating public-model, dependency, identity, retry/uncertainty, data, lineage, observability, serialization, security, packaging, migration, Customer 360 and auditable release qualification criteria.

- `PYKIT_ECOSYSTEM_V2_DECLARATION_PLAN_RUNTIME_MODEL.md` — normative Phase 0 rationalization of authoring declarations, compiled plans and runtime records across PyIngestKit, PyTransformKit and PyWorkflowKit, explicitly removing artificial public graph/plan symmetry.

## PyTransformKit V1 target architecture

- `PYTRANSFORMKIT_V1_TARGET_ARCHITECTURE.md` — normative PyTransformKit 1.0 target architecture covering engine-neutral domain boundaries, TransformationPlan and LogicalPlan, runtime execution, bindings, engine adapters, physical I/O limits, lineage, observability, serialization, plugins, migration from legacy Pipeline/RunPipelineService and 1.0 acceptance gates.

## PyIngestKit V2 target architecture

- `PYINGESTKIT_V2_TARGET_ARCHITECTURE.md` — normative PyIngestKit 2.0 target architecture covering acquisition, RAW, Artifact, decoding, validation, DatasetVersion, publication, replay, ArtifactStore/Target/DatasetVersionStore separation, runtime identity, provenance, observability, serialization, security, optional PyTransformKit integration and V1-to-V2 migration.

## PyWorkflowKit V2 target architecture

- `PYWORKFLOWKIT_V2_TARGET_ARCHITECTURE.md` — normative PyWorkflowKit 2.0 target architecture covering WorkflowDefinition/TaskDefinition, ExecutionPlan, WorkflowRun/TaskRun/TaskAttempt state machines, retry, timeout, cancellation, ExternalRunRef, recovery/reconciliation, executors, metadata stores, observability, serialization, security, optional sibling integrations and V1-to-V2 migration.
