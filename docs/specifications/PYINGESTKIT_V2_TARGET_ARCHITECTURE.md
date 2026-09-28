# PyIngestKit V2 — Target Architecture

> **Status:** NORMATIVE TARGET ARCHITECTURE BASELINE
> **Target release:** PyIngestKit 2.0.0
> **Date:** 2026-09-28
> **Architecture generation:** PyKit Ecosystem V2
> **Primary bounded context:** reliable, traceable batch ingestion and governed dataset publication
> **Depends on:** PYKIT_ECOSYSTEM_V2_DECLARATION_PLAN_RUNTIME_MODEL.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_END_TO_END_ACCEPTANCE_CRITERIA.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_IMPLEMENTATION_SEQUENCE_AND_MIGRATION_PLAN.md
> **Depends on:** PYTRANSFORMKIT_V1_TARGET_ARCHITECTURE.md
> **Depends on:** all normative PyKit Ecosystem V2 cross-framework specifications

---

# 1. Purpose

This document defines the target internal architecture of PyIngestKit for the 2.0.0 stable release.

It translates the ecosystem-wide V2 rules into concrete PyIngestKit module boundaries, domain objects, lifecycle semantics, runtime services, ports, adapters, durable evidence, publication semantics, replay behavior, serialization contracts, extension points and migration constraints.

> **PyIngestKit owns how data is acquired, preserved, decoded, validated, versioned and published; it does not own when ingestion is scheduled or how arbitrary business transformations are orchestrated.**

> **Ingestion evidence is first-class: acquisition, RAW, provenance, DatasetVersion and publication must remain explainable after the process that created them has disappeared.**

# 2. Product mission

PyIngestKit provides reliable, traceable and repeatable batch ingestion.

Its canonical responsibility is:

~~~text
External Source
      ↓
Acquire
      ↓
RAW
      ↓
Decode
      ↓
Validate
      ↓
Version
      ↓
DatasetVersion
      ↓
Publish
      ↓
PublishedDataset
~~~

The framework turns external source material into governed, reproducible dataset versions while preserving evidence of how that happened.

# 3. Bounded-context ownership

PyIngestKit owns:

~~~text
Source semantics
source acquisition
RAW capture
Artifact and ArtifactReference
decode / parser semantics
ingestion contract validation
profiling and quality evidence
content and schema fingerprints
DatasetVersion
DatasetVersionReference
PublishedDataset
publication lifecycle
publication idempotency
replay from preserved evidence
ingestion provenance
IngestionRun
IngestionResult
bounded transport/storage retry
ingestion diagnostics
ingestion events and telemetry
ArtifactStore
DatasetVersionStore
Target
portable ingestion manifests
~~~

PyIngestKit does not own:

~~~text
workflow scheduling
cron
TaskRun / TaskAttempt
generic workload DAG execution
worker fleet management
arbitrary business transformation DAGs
logical joins / aggregations / windows
generic transformation engine semantics
PyTransformKit LogicalPlan
enterprise IAM
secret management
cloud infrastructure provisioning
universal data catalog governance
~~~

# 4. Relationship to sibling frameworks

Canonical dependency direction:

~~~text
PyWorkflowKit
    └── optional integration → PyIngestKit

PyIngestKit
    └── optional integration → PyTransformKit

PyTransformKit
    └── no dependency on PyIngestKit
~~~

PyIngestKit core MUST NOT require PyTransformKit.

PyIngestKit MUST NOT import PyWorkflowKit.

Optional transformation delegation belongs to an explicit integration namespace and optional extra.

# 5. Canonical public lifecycle

The target user-facing model is:

~~~text
IngestionDefinition
        ↓
IngestionRuntime.run(...)
        ↓
IngestionRun
        ↓
IngestionResult
~~~

The semantic lifecycle executed by the runtime is:

~~~text
Source
    ↓ Acquire
RAW
    ↓ Decode
Validate
    ↓ Version
DatasetVersion
    ↓ Publish
PublishedDataset
~~~

There is no mandatory public IngestionPlan or IngestionLifecycle class in V2.

# 6. Architectural layers

PyIngestKit V2 uses five principal layers:

~~~text
AUTHORING
    user-facing ingestion declarations and policies

DOMAIN
    Source, RAW, Artifact, DatasetVersion, publication and provenance semantics

APPLICATION
    lifecycle services, validation, versioning, replay and publication coordination

RUNTIME
    IngestionRun identity, execution context, diagnostics and results

INFRASTRUCTURE / ADAPTERS
    files, HTTP, databases, object stores, targets, artifact stores and persistence
~~~

Dependencies point inward.

The domain layer MUST NOT depend on transport, database, cloud or sibling-framework implementations.

# 7. Target package structure

~~~text
src/pyingestkit/
├── __init__.py
├── domain/
│   ├── ingestion.py
│   ├── sources.py
│   ├── artifacts.py
│   ├── raw.py
│   ├── datasets.py
│   ├── publication.py
│   ├── provenance.py
│   ├── quality.py
│   ├── fingerprints.py
│   └── errors.py
├── application/
│   ├── acquire.py
│   ├── decode.py
│   ├── validate.py
│   ├── version.py
│   ├── publish.py
│   ├── replay.py
│   └── inspect.py
├── runtime/
│   ├── ingestion_runtime.py
│   ├── runs.py
│   ├── results.py
│   ├── context.py
│   └── diagnostics.py
├── ports/
│   ├── source.py
│   ├── decoder.py
│   ├── artifact_store.py
│   ├── dataset_version_store.py
│   ├── target.py
│   ├── resource.py
│   ├── telemetry.py
│   └── plugins.py
├── adapters/
│   ├── filesystem/
│   ├── http/
│   ├── databases/
│   ├── object_storage/
│   ├── formats/
│   └── targets/
├── serialization/
├── observability/
├── plugins/
└── integrations/
    └── pytransformkit/
~~~

Exact module names may evolve, but the responsibility split is normative.

# 8. Root package philosophy

The package root is curated rather than exhaustive.

Target root exports should center on IngestionDefinition, IngestionRuntime, IngestionRun, IngestionResult, stable source declarations, DatasetVersion, DatasetVersionReference, PublishedDataset, ArtifactReference, ResourceReference, selected policies and public exceptions.

Private repositories, persistence entities, provider clients and internal lifecycle machinery stay out of the root API.

# 9. Domain purity

Pure domain modules MUST be importable with no optional transport/provider dependency installed.

They MUST NOT import:

~~~text
HTTP client implementation details
boto3
Azure SDKs
database drivers
SQLAlchemy
Pandas
Polars
PyArrow
PyTransformKit
PyWorkflowKit
~~~

Optional format libraries and providers remain adapter dependencies.

# 10. IngestionDefinition

IngestionDefinition is the canonical public authoring root.

It owns runtime-independent ingestion intent such as:

~~~text
source declaration
decoder/format intent
declared representation or schema expectations
validation policy
RAW policy
dataset identity
versioning policy
publication intent
runtime-independent ingestion options
~~~

It MUST NOT own an IngestionRunId, active provider client, resolved credentials, current status, retry attempt counter, workflow scheduling state, TaskAttempt or transformation DAG.

# 11. No mandatory public IngestionPlan

V2 does not initially expose a public IngestionPlan.

The runtime MAY internally prepare or normalize an IngestionDefinition to resolve decoders, stores, targets, resource locators, capabilities and policy defaults.

That representation remains internal unless future evidence proves independent public value.

# 12. Source

Source is an ingestion-domain concept describing acquisition origin and acquisition semantics.

A Source may represent:

~~~text
local file
HTTP endpoint
SFTP-like provider
object-store object or prefix
database query or table
warehouse export
custom connector
~~~

Source is not equivalent to ResourceReference.

# 13. Source versus ResourceReference

~~~text
Source
    ingestion intent + acquisition semantics

ResourceReference
    portable resource identity or location
~~~

A Source may resolve to one or more resources.

ResourceReference is a boundary contract, not the complete ingestion source model.

# 14. Acquisition

Acquisition obtains source bytes or records under ingestion semantics.

It may involve HTTP calls, file reads, object-store downloads, database extraction, pagination or provider-side export jobs.

Acquisition creates durable evidence and is not an invisible precursor to decode.

# 15. Acquisition evidence

A successful acquisition SHOULD preserve, where available:

~~~text
source identity
source locator/reference
acquisition timestamp
provider metadata
content length
checksum
provider request/page/export identifiers
CorrelationContext
IngestionRunId
~~~

Sensitive provider metadata must be redacted.

# 16. RAW

RAW is immutable or effectively immutable source evidence captured before business transformation.

RAW exists for provenance, replay, integrity verification, debugging, retention and auditability.

RAW is not equivalent to a staging table.

# 17. RAW invariants

RAW MUST preserve:

~~~text
ArtifactReference
checksum/integrity evidence
source provenance
capture timestamp
representation metadata
retention metadata
security classification when used
replay eligibility
~~~

Business transformation MUST NOT mutate RAW.

# 18. Artifact

Artifact is durable material evidence.

Examples include RAW source files, quality reports, profile reports, rejected-record reports, publication manifests, migration reports and diagnostic bundles.

An Artifact is not automatically a DatasetVersion.

# 19. ArtifactStore

ArtifactStore persists and resolves durable artifacts.

Typical responsibilities include put, get/open, integrity metadata, existence checks, lifecycle/deletion policy and portable ArtifactReference generation.

# 20. ArtifactStore != Target

This distinction is normative:

~~~text
ArtifactStore
    stores evidence and artifacts

Target
    receives governed publication output
~~~

A physical backend may implement both roles, but lifecycle, retention and authorization semantics remain distinct.

# 21. Decoder

Decoder converts acquired representation into a typed ingestion representation.

Examples include CSV bytes to records, JSON/NDJSON to records, Excel workbook to tabular representation and Parquet to typed tabular representation.

Decoder semantics belong to PyIngestKit.

# 22. Decode != transform

~~~text
DECODE != TRANSFORM
~~~

Representation-level coercion needed to instantiate declared types may remain decoding.

Joins, aggregations, windows, pivots, business derivations and complex relational restructuring belong to PyTransformKit or application logic.

# 23. Neutral decoded representation

PyIngestKit core SHOULD avoid making one engine-native dataframe the canonical decoded domain representation.

Implementations may use records, iterable batches, portable tabular structures, Arrow-compatible optional representations or streaming batches.

Domain semantics remain dependency-neutral.

# 24. Ingestion contract validation

Validation checks decoded data against declared ingestion expectations.

Possible rules include required fields, type compatibility, nullability, shape, allowed values, uniqueness where declared, row-count constraints, schema fingerprint expectations and provider-specific integrity rules.

Validation remains distinct from arbitrary business transformation.

# 25. Quality and profiling

PyIngestKit MAY produce quality/profile evidence such as row counts, null counts, distinct counts, min/max summaries, schema summaries and quality-rule outcomes.

Quality/profile evidence is normally structured diagnostics or Artifact output rather than DatasetVersion identity itself.

# 26. Schema semantics

PyIngestKit should consume portable logical schema contracts without creating a competing transformation type system.

If PyTransformKit schema contracts become the ecosystem-stable logical schema model, PyIngestKit may interoperate through portable wire contracts or an optional integration while keeping core independent.

# 27. Fingerprints

PyIngestKit distinguishes:

~~~text
artifact_checksum
content_fingerprint
schema_fingerprint
dataset_version_identity
source_fingerprint when useful
~~~

These values are not interchangeable.

Fingerprint semantics must be deterministic and scoped.

# 28. DatasetVersion

DatasetVersion is a durable governed immutable version of a dataset.

It owns semantic version identity distinct from physical storage identity.

A DatasetVersion may reference:

~~~text
DatasetVersionId
dataset identity
ArtifactReference values
ResourceReference values
schema fingerprint
content fingerprint
provenance
quality evidence
publication evidence
creation timestamp
originating IngestionRunId
optional TransformationExecutionReference
~~~

# 29. DatasetVersion invariants

A DatasetVersion MUST be immutable in identity, traceable to producing evidence, distinguishable from latest/current aliases, reproducible within declared portability constraints and serializable through a stable DatasetVersionReference.

Changing governed content produces a new DatasetVersion identity.

# 30. DatasetVersionReference

DatasetVersionReference is the portable cross-framework contract for a concrete governed version.

It MUST NOT contain active sessions, provider clients, raw secrets, mutable repository objects or process-local addresses.

# 31. DatasetVersionStore

DatasetVersionStore persists governed DatasetVersion metadata and lookup semantics.

Typical responsibilities include saving immutable version metadata, looking up concrete versions, enumerating versions, persisting provenance references and resolving current/latest pointers only when explicitly requested.

# 32. DatasetVersionStore != ArtifactStore

~~~text
ArtifactStore
    stores durable material evidence

DatasetVersionStore
    stores governed version identity and metadata
~~~

One backend may implement both, but the ports and domain semantics remain separate.

# 33. PublishedDataset

PublishedDataset represents a named governed publication whose pointer may move to newer DatasetVersion values under explicit policy.

~~~text
DatasetVersion
    immutable concrete version

PublishedDataset
    named publication / pointer semantics
~~~

Current/latest semantics MUST remain explicit.

# 34. Publication

Publication turns eligible ingestion output or external transformation output into governed dataset state.

It may involve target write, registration, DatasetVersion creation, PublishedDataset pointer update, manifest creation, provenance linkage and idempotency enforcement.

Publication is a first-class domain operation.

# 35. Target

Target is the publication-side endpoint receiving ingested data.

Examples include filesystem locations, object-store prefixes, database tables, warehouse tables, APIs and custom sinks.

Target semantics may include write mode, transaction behavior, idempotency and reconciliation capability.

# 36. Target != ArtifactStore

A Target is not an ArtifactStore by definition.

A publication target may be a database table or API side effect that is not an artifact repository.

The architecture therefore keeps these domain roles separate.

# 37. Write != publish

~~~text
physical write
    !=
governed publication
~~~

A physical target write may be one operation inside publication.

Publication additionally establishes governed identity, provenance and version semantics.

# 38. Publication modes

Publication policy SHOULD make intended behavior explicit.

Possible semantics include create-new, fail-if-exists, append-new-version, replace-publication-pointer, register-existing-resource and materialize-and-register.

Exact public names are frozen later.

# 39. Publication idempotency

Publication MUST state whether repetition is naturally idempotent, key-idempotent, conditionally idempotent, non-idempotent or unknown.

Idempotency depends on real provider semantics, not merely a generated key.

# 40. UNKNOWN_OUTCOME

Publication may produce uncertainty:

~~~text
request sent
    ↓
provider may commit
    ↓
acknowledgement lost
    ↓
UNKNOWN_OUTCOME
~~~

The runtime MUST reconcile when possible before repeating a potentially side-effecting publication.

# 41. Reconciliation

Publication and acquisition adapters MAY expose reconciliation when provider truth can be inspected.

Reconciliation can resolve confirmed success, confirmed failure, still unknown, eventual-consistency not-found and conflict/already-exists states.

Reconciliation is not retry.

# 42. Replay

Replay reprocesses preserved evidence without pretending that source acquisition happened again.

~~~text
Original IngestionRun
        ↓
preserved RAW
        ↓
Replay request
        ↓
new IngestionRun
        ↓
Decode / Validate / Version / Publish
~~~

Replay always receives a new IngestionRunId.

# 43. Replay != reacquisition

~~~text
REACQUISITION
    contacts the source again
    may observe changed source state

REPLAY
    starts from preserved prior evidence
    source acquisition is not repeated
~~~

This distinction must remain visible in provenance.

# 44. Replay != workflow retry

Workflow retry repeats a workload according to orchestration policy.

Replay is an ingestion-domain operation over preserved evidence.

A TaskAttempt retry does not become replay unless replay semantics are explicitly requested.

# 45. IngestionRuntime

IngestionRuntime is the main execution service.

It coordinates definition validation, source lookup, credential/resource resolution, acquisition, RAW persistence, decode, validation, profiling, DatasetVersion creation, publication, bounded retry, reconciliation, provenance, diagnostics, events and result construction.

It MUST NOT become a workflow scheduler.

# 46. IngestionRunId

Every semantic ingestion execution receives a fresh IngestionRunId.

Bounded internal provider retries preserve that ID.

A replay gets a new ID.

A WorkflowKit task retry normally creates a new IngestionRunId unless existing work is being recovered or reconciled.

# 47. CorrelationContext

IngestionRuntime accepts or creates CorrelationContext.

CorrelationId links the broader operation while IngestionRunId remains native ingestion identity.

Trace identifiers remain observational.

# 48. IngestionRun

IngestionRun is the durable or inspectable runtime record of one ingestion execution.

It may contain or reference:

~~~text
IngestionRunId
definition fingerprint
CorrelationContext
source reference
acquisition evidence
RAW ArtifactReference
decode evidence
validation/quality evidence
DatasetVersionReference
publication evidence
status
timestamps
FailureEvidence
replay origin when applicable
~~~

# 49. IngestionResult

IngestionResult is the caller-facing outcome.

A successful result SHOULD expose enough for safe composition: execution reference, status, DatasetVersionReference, relevant ArtifactReferences, publication evidence, diagnostics and FailureEvidence when applicable.

It SHOULD NOT expose private repository entities.

# 50. Failure model

PyIngestKit maps provider errors into stable ecosystem categories including validation, configuration, authentication, authorization, not-found, conflict, transient, timeout, cancelled, resource-exhausted, rate-limited, integrity, contract-violation, side-effect-failed, unknown-outcome, external-provider and internal errors.

Human-readable text remains diagnostic rather than contractual.

# 51. Retry ownership

PyIngestKit may retry bounded ingestion-internal operations when it can determine retry safety.

Examples include HTTP page fetches, object-store downloads, artifact uploads, database COPY calls and idempotent/reconcilable publication requests.

Generic whole-workload retry belongs to PyWorkflowKit.

# 52. Effective retry budget

Provider SDK retries count toward the actual retry budget.

Hidden nested retries are prohibited.

Diagnostics SHOULD expose provider-level attempts where practical.

# 53. Acquisition idempotency

Read-like acquisition is not always naturally idempotent.

Provider export APIs may create new remote jobs or temporary resources.

Adapters MUST declare repetition safety rather than assuming all acquisition is harmless.

# 54. Publication transactions

Targets MAY support transactions such as database transactions, atomic object rename, staged manifest commits or compare-and-swap pointer updates.

Transactional guarantees are adapter capabilities.

PyIngestKit MUST NOT claim stronger guarantees than the target provides.

# 55. Exactly-once posture

PyIngestKit SHOULD NOT claim universal exactly-once semantics.

It may provide strong idempotency, immutable versions and reconciliation where provider capabilities support them.

Exactly-once claims must be scoped to concrete adapters and providers.

# 56. Provenance ownership

PyIngestKit owns ingestion provenance:

~~~text
Source
    → Acquisition
    → RAW Artifact
    → Decode
    → Validation
    → DatasetVersion
    → Publication
~~~

If a PyTransformKit execution produced publication input, PyIngestKit stores a TransformationExecutionReference rather than taking ownership of transformation lineage.

# 57. Transformation provenance link

~~~text
TransformationExecutionReference
        ↓
ResourceReference
        ↓
PyIngestKit publication
        ↓
DatasetVersion
~~~

The resulting DatasetVersion SHOULD retain the transformation execution reference in provenance.

# 58. Quality evidence

Validation reports, profiles, rejected-record reports and schema comparisons may be stored as Artifacts and linked from provenance.

This avoids bloating DatasetVersion metadata while keeping evidence durable.

# 59. Rejected records

Where partial acceptance is supported, rejected-record policy MUST be explicit.

Possible policies include fail-all, quarantine-rejects, allow-with-threshold and custom policy.

Silent row loss is prohibited.

# 60. Partial ingestion

Partial success semantics MUST be explicit.

An ingestion run must not report ordinary success if data was dropped or a target was only partially updated unless the declared policy explicitly defines that outcome.

# 61. Manifests

Ingestion manifests provide durable execution evidence.

They may contain IngestionRunId, definition fingerprint, source reference, RAW ArtifactReference, checksums, decoder identity, validation summary, DatasetVersionReference, publication result, CorrelationContext, FailureEvidence, timestamps and contract version.

Manifests MUST NOT contain raw secrets or active handles.

# 62. Observability

PyIngestKit emits framework-owned events, diagnostics, metrics and traces.

Potential event families include run-started, acquisition-started, raw-persisted, decode-completed, validation-completed, dataset-version-created, publication-completed, run-failed and replay-started.

Exact stable names are frozen separately if promoted to public contracts.

# 63. Diagnostics

Structured diagnostics SHOULD cover source resolution, acquisition retries, decoder warnings, schema mismatches, quality failures, artifact persistence, versioning decisions, publication conflicts, reconciliation and replay.

Users should not need to parse logs to understand an ingestion outcome.

# 64. Metrics

Default metric labels should be bounded dimensions such as source kind, decoder kind, target kind, status, failure category and publication mode.

Run IDs, DatasetVersion IDs, full URIs and exception messages MUST NOT be default labels.

# 65. Telemetry isolation

Telemetry sink failure MUST NOT replay acquisition or publication.

Core ingestion must work without an external observability backend.

Audit-grade evidence requires explicitly stronger semantics than best-effort telemetry.

# 66. Serialization

Stable portable contracts use explicit contract IDs and versions.

Candidate portable surfaces include IngestionDefinition when portable, DatasetVersionReference, ArtifactReference, ResourceReference, IngestionExecutionReference, CorrelationContext, FailureEvidence, publication manifests, replay references and provenance records.

Arbitrary Python callbacks and provider clients are not portable contracts.

# 67. Safe decoding

Wire decoding MUST be schema-driven and non-executable.

Public/durable contracts MUST NOT depend on pickle, cloudpickle, dill, eval, exec or arbitrary Python class reconstruction.

Unsupported safety-sensitive semantics fail closed.

# 68. Plugin architecture

Plugins MAY extend:

~~~text
SourceConnector
Decoder
ArtifactStore
DatasetVersionStore
Target
Publisher
ResourceResolver
quality providers
telemetry sinks
~~~

Discovery does not imply activation.

# 69. Plugin namespaces

Potential entry-point groups may include:

~~~text
pyingestkit.sources
pyingestkit.decoders
pyingestkit.targets
pyingestkit.artifact_stores
pyingestkit.dataset_version_stores
~~~

Exact names are frozen later.

# 70. Optional dependencies

The base package SHOULD remain lightweight.

Potential extras may include:

~~~text
[http]
[excel]
[parquet]
[postgres]
[s3]
[transform]
~~~

Optional means optional in installation, import and activation.

# 71. PyTransformKit integration

The optional integration lives conceptually under:

~~~text
pyingestkit.integrations.pytransformkit
~~~

It may support:

~~~text
DatasetVersionReference
    → PyTransformKit InputBinding

TransformationResult
    → PyIngestKit publication input
~~~

PyIngestKit core remains usable without PyTransformKit installed.

# 72. No duplicated transformation engine

PyIngestKit MUST NOT reproduce PyTransformKit relational semantics.

Join, aggregation, window, pivot and reusable business derivation are delegated explicitly to PyTransformKit or application code.

# 73. Security boundaries

PyIngestKit follows the ecosystem security baseline:

~~~text
identity != authorization
CredentialReference instead of raw secret
safe source and target resolution
bounded decoders
archive/path traversal protection
explicit plugin activation
redacted telemetry
non-executable deserialization
publication authority distinct from read authority
~~~

# 74. Credential handling

IngestionDefinition and DatasetVersionReference MUST NOT embed raw credentials.

Credentials are resolved only at runtime by authorized providers.

Secret rotation should not require rewriting durable DatasetVersion references.

# 75. Source security

Source adapters SHOULD support policy for allowed schemes, hosts, filesystem roots, redirects, private-network restrictions, file types and maximum payload size.

Untrusted source configuration must not become unrestricted SSRF or filesystem access.

# 76. Decoder security

Decoders SHOULD enforce limits for payload size, record count, nesting, decompression size, archive depth and temporary disk usage.

Malformed input must not cause unbounded resource consumption.

# 77. Publication security

Publication authority is explicit.

Permission to read a source does not imply permission to publish to arbitrary targets.

Target credentials SHOULD be separately scoped.

# 78. Concurrency and resource ownership

Adapters and stores MUST document thread safety, process safety, async behavior, resource lifetime, connection ownership and cleanup.

Normal operation should not require implicit global mutable provider state.

# 79. Sync and async posture

V2 may use synchronous run as the canonical baseline.

Async adapters may be added where provider I/O benefits from them, but sync and async paths must preserve the same domain semantics and evidence model.

# 80. Public exception architecture

PyIngestKit SHOULD expose a coherent error hierarchy for validation, source configuration, acquisition, decode, integrity, artifact storage, dataset versioning, publication, replay, serialization and plugin/integration failures.

Native provider errors are translated at adapter boundaries.

# 81. Persistence boundaries

Durable ports may be required for Artifact metadata, DatasetVersion metadata, PublishedDataset pointers, IngestionRun metadata, manifests and provenance.

ORM entities remain infrastructure-private.

# 82. IngestionRun persistence

Durable IngestionRun persistence is recommended for traceability and reconciliation of uncertain publication.

The domain must not depend on one database implementation.

Local/in-memory implementations may support development and tests.

# 83. Recovery posture

PyIngestKit may recover or reconcile ingestion-owned external operations such as provider export jobs, artifact uploads, publication transactions and target registrations.

It does not own workflow-level recovery of arbitrary task graphs.

# 84. Root export discipline

The root package SHOULD NOT export private repositories, ORM models, provider clients, internal lifecycle state helpers, plugin-loader internals or temporary decoded representation classes.

# 85. Migration from V1 Job/Pipeline/Step

Legacy generic execution abstractions are not retained by default.

Semantic migration examples:

~~~text
V1 ingestion job
    → IngestionDefinition + IngestionRuntime

V1 acquisition step
    → SourceConnector / acquisition service

V1 transformation step
    → PyTransformKit integration when it is business transformation

V1 orchestration sequence
    → PyWorkflowKit when it is workload orchestration
~~~

A generic Job/Pipeline/Step alias layer is not part of V2 core.

# 86. Migration from V1 RAW behavior

Existing immutable RAW and SHA256 provenance behavior is valuable evidence and SHOULD be retained where aligned with V2.

V2 formalizes it through RAW, Artifact, ArtifactReference and provenance contracts.

# 87. Migration from V1 DatasetVersion behavior

Existing content-addressed snapshots and PublishedDataset pointer semantics are strong reuse candidates.

They must be aligned with:

~~~text
DatasetVersion != Artifact
DatasetVersionStore != ArtifactStore
PublishedDataset pointer != immutable DatasetVersion
~~~

# 88. Migration from V1 replay

Existing replay logic should be retained when it starts from preserved RAW without reacquisition.

Replay must create a new IngestionRunId and explicit replay provenance.

# 89. Migration from V1 PostgreSQL/COPY support

Transactional PostgreSQL/COPY capabilities may be retained as infrastructure adapters.

Provider SQL and transaction mechanics remain adapter-owned rather than defining core publication semantics.

# 90. Migration from V1 S3/MinIO support

Existing S3-compatible behavior may be reused behind ResourceResolver, ArtifactStore or Target ports as appropriate.

The adapter role must be explicit because one backend may implement several different domain roles.

# 91. Migration from V1 plugins and CLI

Existing plugin and CLI behavior may be reused only after V2 alignment:

~~~text
discovery != activation
plugins are capability-scoped
optional dependencies remain optional
CLI avoids private persistence coupling
machine-readable output is versioned when promised
~~~

# 92. Conformance strategy

PyIngestKit 2.0 requires:

~~~text
domain purity tests
public API snapshot
source connector conformance
decoder conformance
RAW immutability tests
ArtifactStore conformance
DatasetVersionStore conformance
Target/publication conformance
replay tests
failure/retry/reconciliation tests
wire golden fixtures
security negative tests
optional dependency absence tests
built-wheel smoke
Customer 360 ingestion/publication path
~~~

# 93. Adapter conformance families

Reusable behavioral suites SHOULD exist for stable extension ports such as SourceConnector, Decoder, ArtifactStore, DatasetVersionStore, Target and ResourceResolver.

Typing alone is insufficient.

# 94. Local reference profile

The V2 reference profile SHOULD run with local CSV files, filesystem ArtifactStore, local/SQLite metadata, a simple local publication target, JSON manifests and synthetic or absent credentials.

This keeps CI deterministic and independent of cloud services.

# 95. Production provider posture

Production adapters may include HTTP APIs, PostgreSQL, S3-compatible stores, Azure Blob, GCS, warehouses and enterprise APIs.

No provider becomes mandatory for core architecture.

# 96. Target architecture invariants

### PIK-ARCH-INV-01 — IngestionDefinition is the authoring root

No generic Job/Pipeline abstraction owns V2 ingestion semantics.

### PIK-ARCH-INV-02 — Acquisition creates evidence

Source access is traceable and not an invisible implementation detail.

### PIK-ARCH-INV-03 — RAW is immutable source evidence

RAW is preserved before business transformation and supports replay/provenance.

### PIK-ARCH-INV-04 — Decode is not transform

Representation decoding does not become a relational business transformation engine.

### PIK-ARCH-INV-05 — ArtifactStore differs from Target

Evidence storage and publication destinations remain distinct domain roles.

### PIK-ARCH-INV-06 — DatasetVersionStore differs from ArtifactStore

Governed version metadata is not material artifact storage.

### PIK-ARCH-INV-07 — DatasetVersion is immutable governed identity

Physical location and current/latest pointers do not define concrete version identity.

### PIK-ARCH-INV-08 — Write is not publish

Publication adds governed version/provenance semantics beyond physical writing.

### PIK-ARCH-INV-09 — Replay is a new ingestion execution

Replay uses preserved evidence and gets a new IngestionRunId.

### PIK-ARCH-INV-10 — Retry is bounded to ingestion-owned operations

Generic workload retry remains outside PyIngestKit.

### PIK-ARCH-INV-11 — PyTransformKit integration is optional

PyIngestKit core remains usable without the transformation framework.

### PIK-ARCH-INV-12 — PyIngestKit does not own workflow orchestration

Scheduling, TaskAttempt and workflow recovery remain PyWorkflowKit responsibilities.

# 97. Canonical execution flow

~~~text
IngestionDefinition
        ↓
Definition validation
        ↓
Source resolution
        ↓
Acquire
        ↓
Persist RAW Artifact
        ↓
Decode
        ↓
Validate / Profile
        ↓
Compute fingerprints
        ↓
Create DatasetVersion
        ↓
Publish / Register
        ↓
Update PublishedDataset pointer when policy requires
        ↓
Persist provenance + manifest
        ↓
IngestionResult
~~~

Replay starts at preserved RAW rather than Source acquisition.

# 98. Internal dependency flow

~~~text
domain
  ↑
application
  ↑
runtime
  ↑
adapters / infrastructure
~~~

Ports are defined inward and implemented outward.

The optional PyTransformKit integration remains outside the core domain.

# 99. PyIngestKit 2.0 acceptance

PyIngestKit 2.0 is ready when:

1. IngestionDefinition is the canonical authoring API;
2. no mandatory public IngestionPlan exists without proven need;
3. Source, RAW, Artifact and DatasetVersion semantics are stable;
4. ArtifactStore and DatasetVersionStore are separate ports;
5. Target/publication semantics are explicit;
6. decode remains separate from business transformation;
7. DatasetVersionReference is portable and fixture-tested;
8. publication idempotency, uncertainty and reconciliation are implemented;
9. replay from preserved RAW creates a new IngestionRun;
10. IngestionRun identity and CorrelationContext are stable;
11. FailureEvidence and diagnostics are structured;
12. source/decoder/store/target conformance suites are green;
13. optional PyTransformKit integration is isolated;
14. core works without PyTransformKit or PyWorkflowKit;
15. plugin activation is explicit;
16. wire contracts are safe and versioned;
17. security tests cover source/target resolution and secrets;
18. built wheels pass clean installed smoke;
19. Customer 360 ingestion and publication paths are green;
20. migration from V1 semantics is documented and tested where supported.

# 100. Out of scope for 2.0 core architecture

PyIngestKit 2.0 does not require:

~~~text
cron scheduler
distributed worker platform
workflow DAG runtime
TaskAttempt semantics
generic business transformation engine
universal dataframe API
enterprise IAM
cloud provisioning
universal data catalog
every connector
exactly-once across every provider
~~~

These exclusions protect semantic ownership.

# 101. Relationship to implementation roadmap

The target architecture is the basis for:

~~~text
PYINGESTKIT_V2_IMPLEMENTATION_ROADMAP.md
~~~

That roadmap must order domain model, acquisition, RAW, decoders, validation, DatasetVersion, publication, replay, runtime, stores, serialization, observability, plugins, PyTransformKit integration, migration and release qualification.

# 102. Relationship to public API specification

This document defines what concepts exist and where they belong.

The public API specification will freeze how users import and call them:

~~~text
PYINGESTKIT_V2_PUBLIC_API_SPEC.md
~~~

That document MUST preserve this architecture.

# 103. Final architecture statement

PyIngestKit 2.0 is a batch-ingestion framework centered on durable evidence, reproducible dataset versions and explicit publication semantics.

~~~text
AUTHORING
    IngestionDefinition
        ↓
RUNTIME
    IngestionRuntime
        ↓
LIFECYCLE
    Acquire
      ↓
    RAW
      ↓
    Decode
      ↓
    Validate
      ↓
    DatasetVersion
      ↓
    Publish
        ↓
RUNTIME RECORD
    IngestionRun
        ↓
RESULT
    IngestionResult
~~~

> **PyIngestKit turns external source material into governed, traceable dataset versions while preserving acquisition evidence and publication semantics, without becoming either a transformation engine or a workflow orchestrator.**

This target architecture is the normative baseline for:

~~~text
PYINGESTKIT_V2_PUBLIC_API_SPEC.md
PYINGESTKIT_V2_IMPLEMENTATION_ROADMAP.md
~~~