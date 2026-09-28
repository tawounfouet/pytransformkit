# PyKit Ecosystem V2 — Dataset, Resource and Artifact Interoperability

> **Status:** NORMATIVE DATA INTEROPERABILITY BASELINE
> **Architecture generation:** V2
> **Date:** 2026-09-28
> **Scope:** PyIngestKit, PyTransformKit, PyWorkflowKit
> **Compatibility posture:** clean-slate interoperability model
> **Depends on:** PYKIT_ECOSYSTEM_V2_ARCHITECTURE_AND_CANONICAL_VOCABULARY.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_PUBLIC_API_DESIGN_PRINCIPLES.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_SHARED_CONTRACTS_AND_REFERENCE_MODEL.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_EXECUTION_IDENTITY_AND_CORRELATION_MODEL.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_ERROR_FAILURE_RETRY_AND_UNCERTAINTY_MODEL.md

---

# 1. Purpose

This document defines the V2 semantics for Dataset, DatasetVersion, Resource, Artifact, RAW, Source, Sink, PhysicalHandle, logical and physical bindings, materialization, publication and cross-framework data handoff.

The governing principle is:

> **A dataset is not an artifact, an artifact is not a resource, a resource is not a runtime handle, and none of them should cross a framework boundary without explicit semantics.**

---

# 2. Why the distinctions matter

The following objects may all refer to related data, but they are not equivalent:

~~~text
s3://bucket/customers.parquet
customers@52
a logical Dataset named customers
a Pandas DataFrame
a DuckDB Relation
an immutable RAW object
a PublishedDataset pointer
~~~

They differ in ownership, mutability, reproducibility, lifetime and portability.

---

# 3. Canonical concept flow

~~~text
External Source
      ↓
Resource
      ↓
Acquisition
      ↓
RAW Artifact
      ↓
Decode
      ↓
DatasetVersion
      ↓
DatasetVersionReference
      ↓
PyTransformKit InputBinding
      ↓
Logical Dataset
      ↓
TransformationExecution
      ↓
PhysicalHandle / Output Resource
      ↓
PyIngestKit Publication
      ↓
New DatasetVersion
      ↓
PublishedDataset
~~~

PyWorkflowKit may orchestrate this chain through references without owning the data model.

---

# 4. Semantic ownership

| Concept | Canonical owner |
|---|---|
| Source acquisition | PyIngestKit |
| RAW lifecycle | PyIngestKit |
| DatasetVersion | PyIngestKit |
| PublishedDataset | PyIngestKit |
| Logical Dataset | PyTransformKit |
| Portable logical Schema | PyTransformKit |
| InputBinding / OutputBinding | PyTransformKit runtime |
| PhysicalHandle | PyTransformKit runtime / adapter |
| Workflow attachment/reference | PyWorkflowKit |
| ResourceReference | boundary contract |
| ArtifactReference | producing/governing domain |

---

# 5. Resource

A Resource is anything addressable or resolvable for I/O.

Examples:

~~~text
file
object-store object
HTTP endpoint
database table
database view
network location
manifest
queryable external dataset
~~~

A Resource MAY be mutable or immutable.

A Resource MAY or MAY NOT represent a dataset.

Therefore:

~~~text
Resource != Dataset
~~~

---

# 6. Resource identity and location

Resource identity and physical location are separate.

~~~text
resource_id != resource_locator
~~~

A stable resource identity may move.

A stable locator may expose changing content.

Consumers MUST NOT infer one from the other.

---

# 7. ResourceReference

ResourceReference is the portable boundary representation of a Resource.

Conceptually:

~~~text
ResourceReference
    namespace
    resource_id
    locator?
    kind?
    format?
    media_type?
    schema_reference?
    checksum?
    metadata?
    contract_version
~~~

It MUST be serializable, side-effect free, credential-safe and process-independent.

---

# 8. Source

Source is a PyIngestKit concept describing where acquisition begins.

A Source may define:

- physical locator or provider;
- acquisition protocol;
- authentication reference;
- pagination;
- extraction mode;
- consistency semantics;
- source contract;
- watermark;
- rate limiting;
- source metadata.

Therefore:

~~~text
Source != ResourceReference
~~~

A Source may contain or resolve ResourceReference values.

---

# 9. SourceSpec

SourceSpec is the declarative description of a source.

It expresses intent and configuration.

It is not acquired data and does not prove that the source is currently reachable.

SourceSpec construction MUST remain side-effect free.

---

# 10. Sink

Sink describes a physical delivery target.

The same physical target may participate in different semantic contexts.

~~~text
PyTransformKit Sink
    physical transformation output

PyIngestKit publication target
    governed publication lifecycle
~~~

These meanings MUST NOT be collapsed simply because both may target the same database or object store.

---

# 11. Artifact

Artifact is a durable object produced or preserved during processing.

Examples:

~~~text
RAW payload
manifest
validation report
profile report
serialized plan
checkpoint
physical output file
~~~

Artifact describes durable material evidence.

It does not automatically mean DatasetVersion.

---

# 12. ArtifactReference

ArtifactReference identifies one durable artifact.

Conceptually:

~~~text
ArtifactReference
    artifact_id
    artifact_kind
    locator
    media_type?
    format?
    size_bytes?
    checksum?
    checksum_algorithm?
    created_at?
    owner
    contract_version
~~~

For immutable artifacts the emitted identity SHOULD remain immutable.

---

# 13. RAW

RAW is a special PyIngestKit artifact representing preserved source evidence before business transformation.

RAW SHOULD be immutable and retain enough evidence for:

- replay;
- source traceability;
- checksum verification;
- audit;
- reproducibility.

RAW is not:

~~~text
cleaned output
transformed business dataset
temporary engine spill
PublishedDataset
~~~

---

# 14. RAW versus staging

A staging file is an implementation mechanism.

RAW is a provenance concept.

~~~text
staging_file != RAW
~~~

A staging object may be execution-scoped and disposable.

A RAW artifact may have durable retention guarantees.

---

# 15. Dataset is domain-specific

The ecosystem deliberately rejects one universal Dataset class.

The term has at least two different valid meanings.

~~~text
PyTransformKit Dataset
    logical transformation-domain value

PyIngestKit DatasetVersion
    durable governed immutable data-product version
~~~

A portable reference may connect them.

Their internal domain models remain distinct.

---

# 16. PyTransformKit Dataset

A PyTransformKit Dataset represents logical data semantics.

It SHOULD express:

- logical identity;
- Schema;
- upstream dependency;
- producer transformation;
- logical properties.

It MUST NOT use a Pandas DataFrame, Polars LazyFrame, Arrow Table or DuckDB Relation as its domain identity.

Native objects belong to runtime handles.

---

# 17. DatasetVersion

DatasetVersion is a PyIngestKit-owned durable governed version.

Conceptually:

~~~text
DatasetVersion
    dataset_id
    version_id
    created_at
    schema_reference?
    content_fingerprint?
    provenance
    resource/artifact bindings
    publication state
~~~

A published immutable DatasetVersion MUST NOT change semantic content in place.

Changed content creates a new version.

---

# 18. PublishedDataset

PublishedDataset represents the governed published dataset concept.

It may contain or resolve a current DatasetVersionReference.

The publication pointer may evolve.

The immutable DatasetVersion does not.

~~~text
PublishedDataset pointer may change
DatasetVersion content does not
~~~

---

# 19. DatasetReference

DatasetReference identifies a logical dataset without necessarily pinning an immutable version.

Its resolution semantics MUST be explicit.

Possible semantics include:

~~~text
CURRENT
LATEST
NAMED
FIXED
SNAPSHOT
~~~

Ambiguous implicit latest behavior is discouraged.

---

# 20. DatasetVersionReference

DatasetVersionReference identifies one immutable governed version.

It is the preferred cross-framework input when reproducibility matters.

~~~text
IngestionResult
    ↓
DatasetVersionReference customers@52
    ↓
PyTransformKit adapter
~~~

---

# 21. Latest is not a version

A mutable expression such as:

~~~text
customers:latest
~~~

is not equivalent to a concrete DatasetVersionReference.

For reproducible execution:

~~~text
latest
  ↓ resolve
customers@52
  ↓ persist resolved input
execute
~~~

The execution evidence SHOULD record the concrete resolved version.

---

# 22. ResourceReference versus DatasetVersionReference

ResourceReference describes resolvable physical/resource identity.

DatasetVersionReference describes governed semantic dataset version identity.

One DatasetVersion may reference several resources.

~~~text
customers@52
├── part-0001.parquet
├── part-0002.parquet
└── manifest.json
~~~

---

# 23. ArtifactReference versus DatasetVersionReference

ArtifactReference identifies durable material evidence.

DatasetVersionReference identifies a governed data version.

A DatasetVersion may be backed by artifacts.

An artifact may instead be a RAW payload, report, manifest or checkpoint.

Therefore:

~~~text
ArtifactReference != DatasetVersionReference
~~~

---

# 24. Artifact versus Resource

Artifact is semantic provenance.

Resource is addressability.

Most durable artifacts have a ResourceReference.

Not every Resource is an Artifact.

For example, an HTTP endpoint is a Resource but not necessarily a produced Artifact.

---

# 25. PhysicalHandle

PhysicalHandle represents engine-specific runtime data.

Examples:

~~~text
Pandas DataFrame
Polars DataFrame
Polars LazyFrame
Arrow Table
DuckDB Relation
Snowpark DataFrame
~~~

A PhysicalHandle is normally process-local and non-portable.

It MUST NOT be used as a durable DatasetVersionReference, ArtifactReference, ResourceReference or WorkflowRun persistence payload.

---

# 26. DatasetHandle

PyTransformKit MAY define DatasetHandle as runtime infrastructure.

Conceptually:

~~~text
DatasetHandle
    engine_id
    native_object
    schema?
    ownership
    lifetime
~~~

DatasetHandle is not the logical Dataset.

It is the runtime binding to physical data.

---

# 27. Materialization

Materialization means resolving or producing physical data.

~~~text
DatasetVersionReference
    ↓ resolve
ResourceReference
    ↓ adapter scan
PhysicalHandle
~~~

or:

~~~text
TransformationPlan
    ↓ execute
PhysicalHandle / durable output resource
~~~

Materialization MUST be explicit.

Creating a logical Dataset MUST NOT materialize data.

---

# 28. InputBinding

PyTransformKit MAY define InputBinding to connect logical input with runtime data.

Conceptually:

~~~text
InputBinding
    logical_dataset_id
    DatasetVersionReference?
    ResourceReference?
    PhysicalHandle?
    resolved_schema?
    metadata?
~~~

Portable references and process-local handles MUST remain distinguishable.

---

# 29. OutputBinding

PyTransformKit MAY define OutputBinding.

Conceptually:

~~~text
OutputBinding
    logical_dataset_id
    ResourceReference?
    ArtifactReference?
    PhysicalHandle?
    schema
    statistics?
    lifetime
~~~

Outputs may be ephemeral or durable.

The binding must state which.

---

# 30. Ephemeral and durable output

Ephemeral output exists only inside one process, session or execution.

Examples:

~~~text
in-memory DataFrame
temporary Arrow Table
temporary DuckDB Relation
~~~

Durable output is represented through a portable ResourceReference or ArtifactReference.

Durability alone does not create governance.

---

# 31. Transformation output is not automatically DatasetVersion

This invariant is central.

~~~text
PyTransformKit output != PyIngestKit DatasetVersion
~~~

To create a governed version:

~~~text
TransformationResult
    ↓
portable output reference
    ↓
PyIngestKit publication
    ↓
DatasetVersion
~~~

Publication is explicit.

---

# 32. Physical write versus publication

A physical write means:

~~~text
materialize/serialize output to a target
~~~

Publication means:

~~~text
register and commit governed dataset semantics
~~~

Therefore:

~~~text
WRITE != PUBLISH
~~~

PyTransformKit may write.

PyIngestKit publishes.

---

# 33. Decode versus transform

Representation decoding belongs to ingestion.

~~~text
CSV bytes → rows
JSON bytes → structured records
Excel cells → typed input
Parquet bytes → decoded tabular input
~~~

Logical derivation belongs to PyTransformKit.

~~~text
filter
derive
join
aggregate
window
pivot
business normalization
~~~

Canonical invariant:

~~~text
DECODE != TRANSFORM
~~~

---

# 34. Cast semantics

Casting can occur in two contexts.

Decode-level cast:

~~~text
CSV token "42" → integer 42
~~~

Transformation cast:

~~~text
integer customer_id → string customer_key
~~~

The API must preserve which semantic layer owns the conversion.

---

# 35. Schema ownership

PyTransformKit owns the canonical portable logical Schema model.

PyIngestKit may consume, reference and persist schema fingerprints.

PyIngestKit SHOULD NOT independently create a competing logical type system.

Source schema and logical Schema MAY differ.

The mapping must remain explicit and traceable.

---

# 36. Fingerprints

The ecosystem distinguishes:

~~~text
schema_fingerprint
content_fingerprint
plan_fingerprint
artifact_checksum
~~~

These values have different owners and semantics.

A framework may persist another framework's fingerprint as evidence.

It MUST NOT redefine its calculation.

---

# 37. Manifest

A Manifest is an Artifact describing other objects.

Examples:

~~~text
DatasetVersionManifest
TransformationExecutionManifest
WorkflowRunManifest
~~~

Each bounded context owns its own manifest semantics.

The ecosystem does not require one universal Manifest class.

---

# 38. DatasetVersion manifest

A PyIngestKit dataset manifest may include:

~~~text
dataset_id
version_id
schema reference
content fingerprint
artifact references
source provenance
creation execution
publication metadata
~~~

The manifest describes the DatasetVersion.

It is not the DatasetVersion itself.

---

# 39. Transformation execution manifest

A PyTransformKit manifest may include:

~~~text
transformation_execution_id
plan fingerprint
logical plan fingerprint
engine
input references
output references
diagnostics
~~~

This is transformation execution evidence, not ingestion governance.

---

# 40. Workflow attachments

PyWorkflowKit may persist references such as:

~~~text
ArtifactReference
DatasetVersionReference
TransformationExecutionReference
ExternalRunRef
~~~

WorkflowKit stores references.

It does not gain ownership of the underlying data or artifact.

---

# 41. Storage neutrality

The model MUST remain independent from one storage technology.

Possible backends include:

~~~text
local filesystem
S3-compatible object storage
Azure Blob
GCS
PostgreSQL
Snowflake
network filesystem
HTTP
~~~

Portable reference semantics remain stable across providers.

---

# 42. URI safety

A locator does not imply credentials.

ResourceReference SHOULD prefer credential-free locators.

Credential access belongs to:

~~~text
CredentialReference
runtime credential provider
ambient identity
connection provider
~~~

Signed URLs, SAS tokens and credential-bearing URLs require redaction and SHOULD NOT become long-lived canonical references.

---

# 43. URI does not imply accessibility

A syntactically valid URI does not prove that the current runtime can access the resource.

Accessibility is runtime preflight.

Reference construction MUST NOT perform network I/O.

---

# 44. Resolver model

Portable references are resolved through explicit runtime ports.

Examples:

~~~text
ResourceResolver
ArtifactResolver
DatasetVersionResolver
CredentialResolver
~~~

Resolution MAY produce:

~~~text
resolved locator
connection
PhysicalHandle
provider metadata
~~~

Resolvers MUST NOT become universal service locators.

---

# 45. Resolution outcomes

Resolvers SHOULD distinguish:

~~~text
FOUND
NOT_FOUND
NOT_AUTHORIZED
TEMPORARILY_UNAVAILABLE
INVALID_REFERENCE
UNSUPPORTED_REFERENCE
EXPIRED
~~~

Returning None for every resolution failure is insufficient.

Uncertain provider state MUST follow the ecosystem failure and uncertainty model.

---

# 46. Portability classes

References MAY declare portability where useful.

~~~text
PROCESS_LOCAL
HOST_LOCAL
CLUSTER_LOCAL
ENVIRONMENT_LOCAL
CROSS_HOST
EXTERNAL
~~~

A local temp path MUST NOT be advertised as cross-host portable.

---

# 47. Lifetime classes

Resources and handles MAY declare lifetime semantics.

~~~text
EPHEMERAL
EXECUTION_SCOPED
SESSION_SCOPED
DURABLE
IMMUTABLE_DURABLE
~~~

Lifetime is separate from location and accessibility.

---

# 48. Ownership classes

Active runtime resources SHOULD define ownership when relevant.

~~~text
BORROWED
OWNED
TRANSFERRED
~~~

A runtime MUST NOT close or destroy a borrowed user resource unless ownership was transferred.

---

# 49. Mutable resources and snapshots

A mutable table or path is weaker evidence than an immutable version.

If reproducibility matters, resolve mutable input to a snapshot.

Examples:

~~~text
object version ID
warehouse time-travel snapshot
DatasetVersionReference
immutable checksum-pinned file
~~~

Execution evidence SHOULD record the resolved snapshot.

---

# 50. Database tables

A database table reference MAY contain:

~~~text
catalog
schema
table
snapshot/version?
~~~

If no snapshot is provided, the input is mutable.

The result should not claim stronger reproducibility than the reference guarantees.

---

# 51. Query inputs

A query is not automatically a stable Dataset identity.

For reproducibility, record what the provider supports:

~~~text
query fingerprint
snapshot/time-travel context
provider query ID
materialized output reference
~~~

A mutable query result should not masquerade as an immutable DatasetVersion.

---

# 52. Files and object-store objects

Where reproducibility matters, a file reference SHOULD capture integrity evidence.

~~~text
locator
object version?
checksum
size?
media_type
~~~

A bare mutable object key is weaker than a versioned or checksum-pinned reference.

---

# 53. Local files

Local file references are valid but may be HOST_LOCAL.

WorkflowKit MUST NOT assume another worker or host can resolve the same path.

Portable workflow state should prefer cross-host references for durable execution.

---

# 54. Streams

This specification primarily targets dataset-oriented batch interoperability.

A stream may be represented as ResourceReference, but unbounded stream semantics require explicit offset/checkpoint contracts.

DatasetVersion MUST NOT be overloaded to represent an unbounded stream.

---

# 55. Multi-file datasets

A DatasetVersion may be backed by multiple artifacts.

~~~text
customers@52
├── part-0001.parquet
├── part-0002.parquet
├── part-0003.parquet
└── manifest.json
~~~

DatasetVersionReference identifies the semantic version.

ArtifactReferences identify physical pieces.

---

# 56. Multiple physical representations

One DatasetVersion MAY have more than one declared equivalent representation.

~~~text
customers@52
├── Parquet representation
└── Arrow IPC representation
~~~

Representation equivalence MUST be explicit.

Different physical format does not automatically imply different semantic version.

---

# 57. Format and compression

Format describes representation.

~~~text
CSV
JSONL
PARQUET
ARROW_IPC
DATABASE_TABLE
~~~

Compression and text encoding are representation metadata.

They do not define dataset identity by themselves.

---

# 58. Physical I/O in PyTransformKit

PyTransformKit may own physical I/O required to execute transformations.

Examples:

~~~text
scan Parquet
scan CSV
scan JSONL
scan Arrow IPC
projection pushdown
predicate pushdown
partition pruning
physical output write
~~~

This MUST NOT expand into RAW capture, dataset version registration, ingestion replay or publication governance.

---

# 59. PyTransformKit read boundary

PyTransformKit runtime reads from explicit bindings.

Supported binding sources may include:

~~~text
ResourceReference
DatasetVersionReference through adapter
PhysicalHandle
~~~

PyTransformKit does not need PyIngestKit to read ordinary local or external data.

---

# 60. PyTransformKit write boundary

A transformation write may produce:

~~~text
ResourceReference
ArtifactReference
PhysicalHandle
~~~

It MUST NOT silently create:

~~~text
DatasetVersion
PublishedDataset
RAW
~~~

Those remain PyIngestKit concepts.

---

# 61. PyIngestKit transformation boundary

PyIngestKit MAY delegate logical transformations to PyTransformKit.

~~~text
decoded input
    ↓
TransformationPlan
    ↓
TransformationResult
    ↓
PyIngestKit validation/version/publication
~~~

PyIngestKit SHOULD NOT become a second relational transformation engine.

---

# 62. Independent usability

PyIngestKit remains useful without PyTransformKit:

~~~text
Source → Acquire → RAW → Decode → Validate → Version → Publish
~~~

PyTransformKit remains useful without PyIngestKit:

~~~text
Resource/Handle → InputBinding → TransformationPlan → execute
~~~

PyWorkflowKit remains useful without dataset semantics:

~~~text
arbitrary TaskDefinition → WorkflowRun
~~~

Sibling integrations are optional.

---

# 63. Ingestion to transformation handoff

Canonical flow:

~~~text
IngestionRuntime.run
        ↓
IngestionResult
        ↓
DatasetVersionReference
        ↓
PyTransformKit integration adapter
        ↓
InputBinding
        ↓
TransformationExecution
~~~

The adapter maps governed durable identity into transformation runtime semantics.

---

# 64. Transformation to publication handoff

Canonical flow:

~~~text
TransformationRuntime.execute
        ↓
TransformationResult
        ↓
OutputBinding
        ↓
ResourceReference / ArtifactReference
        ↓
PyIngestKit publication adapter
        ↓
DatasetVersion
        ↓
PublishedDataset
~~~

Publication is explicit and remains PyIngestKit-owned.

---

# 65. Workflow data handoff

WorkflowKit SHOULD pass durable references rather than large in-memory payloads.

Preferred:

~~~text
Task A
    ↓
DatasetVersionReference
    ↓
Task B
~~~

Discouraged as durable workflow state:

~~~text
Task A
    ↓
Pandas DataFrame
    ↓
TaskRun metadata
~~~

In-process optimizations MAY use handles, but the durable contract remains reference-based.

---

# 66. Large payload rule

Large datasets MUST NOT be embedded directly into workflow manifests, execution references or metadata records.

Use durable resources and references.

This keeps metadata small, restart-safe and portable.

---

# 67. Artifact retention

The artifact owner defines retention and garbage collection.

A consumer holding ArtifactReference does not automatically guarantee indefinite retention.

Resolution SHOULD distinguish expired/tombstoned resources from invalid references where useful.

---

# 68. Cache semantics

A transformation cache is not automatically a DatasetVersion.

A cache may be keyed by:

~~~text
plan fingerprint
input fingerprints
engine compatibility
runtime options
~~~

Cache reuse is an optimization.

Governed publication requires explicit PyIngestKit semantics.

---

# 69. Temporary spill and intermediates

Engine spill files and temporary intermediates are normally:

~~~text
EPHEMERAL
EXECUTION_SCOPED
~~~

They MUST NOT leak into durable public contracts unless intentionally promoted to artifacts.

Intermediate logical Datasets remain distinct from physical materializations.

---

# 70. Multiple outputs

TransformationResult SHOULD support multiple named outputs when plan semantics require it.

~~~text
customer_mart
invalid_rows
statistics
~~~

Each output receives an explicit semantic classification and binding.

A side output must not ambiguously alternate between Artifact and Dataset.

---

# 71. Quality and profiling output

Quality reports and profiles are normally Artifacts.

Examples:

~~~text
validation report
row-count report
null profile
distribution profile
~~~

They may be attached to DatasetVersion or TransformationExecution evidence.

They become DatasetVersions only through explicit application/governance choice.

---

# 72. Resource capabilities

ResourceReference MAY declare expected capabilities.

~~~text
READABLE
WRITABLE
SEEKABLE
VERSIONED
IMMUTABLE
TRANSACTIONAL
SNAPSHOTTABLE
~~~

These are declarations until runtime validation confirms provider support.

Capability mismatch is an explicit contract/configuration error.

---

# 73. Content addressing and deduplication

Content-addressed storage is useful for immutable artifacts, RAW and caches.

It does not automatically create DatasetVersion semantics.

Two DatasetVersions MAY reference the same physical content if governance allows it.

~~~text
physical deduplication != logical version identity
~~~

---

# 74. Copy, move, register and publish

The following verbs have distinct semantics:

~~~text
COPY
MOVE
REGISTER
MATERIALIZE
PUBLISH
~~~

REGISTER records an existing resource.

MATERIALIZE creates physical data from logical/runtime computation.

PUBLISH commits governed availability/version semantics.

They MUST NOT be treated as synonyms.

---

# 75. Tombstones and expiry

A reference may remain historically meaningful after material data becomes unavailable.

Possible lifecycle states may include:

~~~text
ACTIVE
EXPIRED
TOMBSTONED
DELETED
UNKNOWN
~~~

The exact lifecycle belongs to the owning domain.

---

# 76. Security and sensitivity

Cross-framework handoff does not bypass authorization.

References may carry sensitivity metadata, but ordinary IDs and locators SHOULD remain free from secrets and personal payloads.

Materialization must still use the receiving runtime's authorized security context.

---

# 77. Serialization boundary

Portable references serialize through explicit versioned wire contracts.

PhysicalHandle does not.

A logical PyTransformKit Dataset or Plan may later have a portable IR, but that serialization remains separate from PyIngestKit DatasetVersion publication.

---

# 78. Equality and fingerprinting

Reference equality follows semantic identity, not incidental metadata.

A DatasetVersionReference is equal according to its stable dataset/version identity and namespace.

A ResourceReference SHOULD use stable resource identity rather than only physical locator where possible.

Fingerprints used for caching or signatures MUST document their semantic scope.

---

# 79. Anti-corruption layer

Every cross-framework mapping SHOULD occur through a consumer-owned adapter.

Example:

~~~text
DatasetVersionReference
        ↓
PyTransformKitDatasetInputAdapter
        ↓
InputBinding
        ↓
Logical Dataset
~~~

PyIngestKit core MUST NOT construct PyTransformKit internal objects.

The consumer maps external references into its own domain.

---

# 80. Interoperability error categories

Typical boundary failures include:

~~~text
RESOURCE_NOT_FOUND
RESOURCE_NOT_AUTHORIZED
RESOURCE_EXPIRED
RESOURCE_UNSUPPORTED
ARTIFACT_INTEGRITY_FAILED
DATASET_VERSION_NOT_FOUND
SCHEMA_INCOMPATIBLE
HANDLE_NOT_PORTABLE
REFERENCE_INVALID
REFERENCE_UNRESOLVABLE
~~~

They map into owning framework error hierarchies while preserving portable failure evidence.

---

# 81. Publication uncertainty

Publication may produce UNKNOWN_OUTCOME if a target commit may have succeeded but acknowledgment was lost.

The dataset/version target must be reconciled before unsafe duplicate publication.

This specification therefore relies on the V2 failure, retry and uncertainty model.

---

# 82. Lineage hooks

Every significant handoff SHOULD be able to produce lineage/provenance relationships.

Examples:

~~~text
DatasetVersionReference
    consumed by
TransformationExecution

Transformation output ResourceReference
    published as
DatasetVersion
~~~

Exact semantics are deferred to the lineage specification.

---

# 83. Observability hooks

Resolution and materialization MAY emit events such as:

~~~text
ResourceResolutionStarted
ResourceResolved
ResourceResolutionFailed
DatasetVersionBound
MaterializationStarted
MaterializationCompleted
PublicationStarted
PublicationCompleted
~~~

Exact event contracts belong to the observability specification.

---

# 84. Performance and zero-copy

Adapters MAY optimize with:

- locality-aware resolution;
- predicate pushdown;
- projection pushdown;
- zero-copy Arrow;
- in-process handle sharing;
- cache reuse.

Optimization MUST NOT change ownership or durability semantics.

Zero-copy is an optimization, not a portable contract requirement.

---

# 85. Engine compatibility

A ResourceReference need not be consumable by every PyTransformKit engine.

Capability negotiation decides whether the selected adapter can read/write a representation.

Unsupported capability MUST fail explicitly.

No hidden fallback to another engine is allowed.

---

# 86. Contract testing

Cross-framework contract tests SHOULD cover:

~~~text
DatasetVersionReference → PyTransformKit InputBinding

TransformationResult ResourceReference
    → PyIngestKit publication

Workflow TaskRun
    → stores DatasetVersionReference without materializing it

durable ResourceReference
    → resolves after restart/cross-host movement

PhysicalHandle
    → rejected from durable WorkflowKit state
~~~

---

# 87. Acceptance criteria

This specification is implemented correctly when:

1. Resource, Artifact, Dataset, DatasetVersion and PhysicalHandle are distinct concepts;
2. PyTransformKit Dataset remains logical and engine-neutral;
3. PyIngestKit DatasetVersion remains durable, governed and versioned;
4. RAW remains immutable source evidence;
5. ResourceReference is portable and credential-safe;
6. ArtifactReference represents durable artifact evidence;
7. DatasetVersionReference identifies one immutable governed version;
8. PhysicalHandle is never treated as durable cross-framework identity;
9. transformation output does not automatically become DatasetVersion;
10. publication is explicit and PyIngestKit-owned;
11. decode remains distinct from transform;
12. write remains distinct from publish;
13. mutable latest inputs are resolved to concrete versions when reproducibility is required;
14. WorkflowKit passes references rather than large payloads;
15. durable references do not depend on process-local state;
16. resolution remains explicit and side-effect free at construction;
17. schema, content, plan and artifact fingerprints remain distinct;
18. local/ephemeral resources advertise limited portability;
19. multi-file DatasetVersions are representable;
20. integration tests validate handoff in both directions.

---

# 88. Normative invariants

### DATA-INV-01 — Dataset is domain-specific

There is no universal Dataset class across the ecosystem.

### DATA-INV-02 — DatasetVersion is PyIngestKit-owned

Durable governed version identity belongs to ingestion/publication semantics.

### DATA-INV-03 — Logical Dataset is PyTransformKit-owned

Transformation semantics remain independent from durable publication.

### DATA-INV-04 — Artifact is not DatasetVersion

Artifacts are durable evidence/materialization; dataset versions are governed semantic versions.

### DATA-INV-05 — Resource is not Artifact

Addressability and provenance remain distinct.

### DATA-INV-06 — PhysicalHandle is not portable

Native engine objects do not become durable references.

### DATA-INV-07 — RAW is immutable source evidence

RAW is not transformed business output.

### DATA-INV-08 — Decode is not transform

Representation interpretation and logical derivation remain distinct.

### DATA-INV-09 — Write is not publish

Physical I/O and governed publication remain separate.

### DATA-INV-10 — Latest is not a version

Reproducible execution records a concrete resolved version.

### DATA-INV-11 — Identity is not location

Resource identity remains distinguishable from locator.

### DATA-INV-12 — Consumer adapters own mapping

Providers do not construct sibling internals.

---

# 89. Final architecture statement

The PyKit V2 ecosystem does not move data as one undifferentiated object.

It composes explicit concepts:

~~~text
Source
Resource
Artifact
RAW
DatasetVersion
DatasetVersionReference
Logical Dataset
InputBinding
PhysicalHandle
OutputBinding
PublishedDataset
~~~

Each concept has a different owner, lifecycle, portability guarantee and meaning.

The central rule is:

> **Cross framework boundaries with portable references and explicit ownership; materialize physical data only inside the runtime that knows how to own it.**

This specification is the baseline for:

~~~text
PYKIT_ECOSYSTEM_V2_LINEAGE_PROVENANCE_AND_TRACEABILITY_MODEL.md
PYKIT_ECOSYSTEM_V2_OBSERVABILITY_EVENTS_AND_TELEMETRY_MODEL.md
PYKIT_ECOSYSTEM_V2_INTEGRATION_AND_ANTI_CORRUPTION_LAYER_MODEL.md
PYKIT_ECOSYSTEM_V2_SERIALIZATION_AND_WIRE_CONTRACTS.md
~~~
