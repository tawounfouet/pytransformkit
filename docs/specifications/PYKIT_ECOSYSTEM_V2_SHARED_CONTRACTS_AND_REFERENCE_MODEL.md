# PyKit Ecosystem V2 — Shared Contracts and Reference Model

> **Status:** NORMATIVE CROSS-FRAMEWORK CONTRACT BASELINE  
> **Architecture generation:** V2  
> **Date:** 2026-09-28  
> **Scope:** PyIngestKit, PyTransformKit, PyWorkflowKit  
> **Compatibility posture:** clean-slate inter-framework contracts; no legacy wire compatibility requirement  
> **Depends on:** PYKIT_ECOSYSTEM_V2_ARCHITECTURE_AND_CANONICAL_VOCABULARY.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_PUBLIC_API_DESIGN_PRINCIPLES.md  
> **Related:** PYTRANSFORMKIT_PYINGESTKIT_PYWORKFLOWKIT_BOUNDARIES_AND_INTEGRATION.md

---

# 1. Purpose

This document defines the shared **contract language** used when PyIngestKit, PyTransformKit and PyWorkflowKit exchange identities, locations, outputs, execution references and correlation metadata.

The objective is to allow the three frameworks to compose without:

- sharing one giant common domain model;
- importing sibling internals;
- passing active runtime objects across boundaries;
- depending on a premature PyCoreKit;
- collapsing distinct bounded contexts into generic abstractions.

The governing principle is:

> **Share contracts at boundaries, not domain ownership.**

A shared contract describes what may cross a boundary.

It does not transfer ownership of the underlying concept.

---

# 2. Core decision

The V2 ecosystem does **not** introduce a mandatory shared package such as:

~~~text
pykit-core
pykit-common
pykit-contracts
pycorekit
~~~

at this stage.

Instead, the ecosystem standardizes:

- semantic contract names;
- required fields;
- serialization rules;
- identity rules;
- namespace rules;
- correlation rules;
- ownership rules;
- adapter behavior.

A concrete shared package MAY be extracted later only if repeated implementation proves that the shared contract has become stable enough to justify independent versioning.

---

# 3. Boundary model

The preferred inter-framework shape is:

~~~text
DOMAIN OBJECT
    ↓
REFERENCE / CONTRACT DTO
    ↓
BOUNDARY
    ↓
ANTI-CORRUPTION ADAPTER
    ↓
TARGET DOMAIN OBJECT
~~~

For example:

~~~text
PyIngestKit DatasetVersion
        ↓
DatasetVersionReference
        ↓
integration boundary
        ↓
PyTransformKit input resolver
        ↓
logical Dataset / DatasetHandle
~~~

The domain object itself does not cross the boundary.

---

# 4. What a shared contract is

A shared contract is a small, portable, versionable description of identity or location.

Typical characteristics:

- immutable;
- serializable;
- side-effect free;
- process-independent;
- implementation-neutral;
- safe to validate without external I/O;
- explicit about provenance;
- explicit about type/kind;
- free of active resources.

Examples:

~~~text
ResourceReference
ArtifactReference
DatasetReference
DatasetVersionReference
TransformationExecutionReference
ExternalRunRef
CorrelationContext
~~~

---

# 5. What a shared contract is not

A shared contract is not:

- a DataFrame;
- an ORM entity;
- a database session;
- an engine connection;
- a workflow runtime;
- an ingestion repository object;
- a Polars LazyFrame;
- a DuckDB Relation;
- an Arrow Table;
- an arbitrary Python callback;
- a serialized Python object graph.

Boundary contracts intentionally carry less information than internal domain objects.

---

# 6. Contract design principles

All cross-framework contracts MUST follow these principles.

## CONTRACT-PRINCIPLE-01 — Minimality

Carry only information required to identify, locate, correlate, validate or consume the referenced object.

## CONTRACT-PRINCIPLE-02 — Explicit ownership

Every contract must state or imply which bounded context owns the referenced object.

## CONTRACT-PRINCIPLE-03 — No active resources

Contracts never own open connections, clients, sessions, handles or threads.

## CONTRACT-PRINCIPLE-04 — Stable serialization

Persisted contracts use explicit schema versions.

## CONTRACT-PRINCIPLE-05 — No secret material

Credentials and tokens never become ordinary contract fields.

## CONTRACT-PRINCIPLE-06 — Transport neutrality

A contract must not require one message bus, database, cloud provider or object store.

## CONTRACT-PRINCIPLE-07 — Forward evolution

Unknown optional metadata must not necessarily invalidate an otherwise compatible contract.

## CONTRACT-PRINCIPLE-08 — Fail closed on semantic ambiguity

Unknown required kind/version/ownership semantics are rejected explicitly.

---

# 7. Reference taxonomy

The V2 conceptual hierarchy is:

~~~text
Reference
│
├── ResourceReference
│
├── ArtifactReference
│
├── DatasetReference
│   └── DatasetVersionReference
│
├── ExecutionReference
│   ├── IngestionExecutionReference
│   ├── TransformationExecutionReference
│   └── WorkflowExecutionReference
│
└── ExternalRunRef
~~~

This hierarchy is conceptual.

It does not mandate Python inheritance across packages.

---

# 8. Reference versus identifier

An identifier answers:

> "Which object?"

A reference answers:

> "Which object, in which semantic namespace, and optionally how may another component resolve it?"

Example:

~~~text
DatasetVersionId
    customers@52

DatasetVersionReference
    owner            = pyingestkit
    dataset_id       = customers
    version_id       = 52
    locator          = ...
    contract_version = 1
~~~

Identifiers may be embedded inside references.

They are not interchangeable.

---

# 9. Identifier rules

Identifiers crossing package boundaries SHOULD be:

- strings or UUID-like value types;
- stable for the lifetime promised by the owner;
- opaque to consumers;
- case rules documented;
- namespace-qualified when collision is possible.

Consumers MUST NOT infer internal storage layout from an identifier.

Bad:

~~~text
id = "postgres.public.datasets.123"
~~~

if consumers are expected to parse database implementation details.

Preferred:

~~~text
dataset_version_id = "dsv_01J..."
~~~

with storage resolution owned elsewhere.

---

# 10. Namespace model

Every portable reference SHOULD identify a semantic namespace.

Examples:

~~~text
pyingestkit.dataset
pyingestkit.dataset_version
pyingestkit.artifact
pytransformkit.execution
pyworkflowkit.workflow_run
external.snowflake.query
external.http.request
~~~

A namespace:

- identifies semantic ownership;
- does not imply Python import path;
- does not imply package version;
- is stable independently from internal module layout.

---

# 11. Contract envelope

Persisted or transmitted shared contracts SHOULD use a common envelope shape conceptually similar to:

~~~json
{
  "contract": "pykit.dataset_version_reference",
  "contract_version": 1,
  "owner": "pyingestkit",
  "id": "dsv_01J...",
  "attributes": {}
}
~~~

The exact JSON schema will be frozen in the dedicated wire-contract specification.

The important distinction is:

~~~text
contract_version
    !=
package_version
~~~

---

# 12. ResourceReference

ResourceReference is the most general portable locator concept.

It represents a resource that may be consumed or resolved by another component.

Conceptual fields:

~~~text
ResourceReference
    namespace
    id
    uri / locator?
    media_type?
    format?
    schema_fingerprint?
    metadata?
    contract_version
~~~

ResourceReference MUST NOT contain credentials.

A URI may identify a local file, object-store object, HTTP resource, table, view, dataset endpoint, or another durable location.

---

# 13. Resource locator versus resource identity

Identity and location are separate.

A resource may retain the same semantic identity while its physical location changes.

Therefore:

~~~text
resource_id
    !=
resource_uri
~~~

A contract SHOULD distinguish:

~~~text
identity
location
~~~

rather than encode both into one opaque string when portability matters.

---

# 14. ArtifactReference

ArtifactReference represents a durable artifact produced or preserved by a framework.

Typical examples include:

- RAW object;
- validation report;
- manifest;
- serialized logical plan;
- exported dataset file;
- benchmark report.

Conceptual fields:

~~~text
ArtifactReference
    artifact_id
    kind
    uri
    media_type?
    size_bytes?
    checksum?
    checksum_algorithm?
    created_at?
    owner
    contract_version
~~~

ArtifactReference describes an artifact.

It does not imply dataset semantics.

---

# 15. Artifact integrity

Where integrity matters, references SHOULD use an explicit checksum pair:

~~~text
checksum_algorithm
checksum
~~~

For example:

~~~text
sha256
4f3c...
~~~

Consumers MUST NOT assume SHA-256 unless the algorithm is declared by contract.

Content-addressed identity MAY use the checksum as part of internal storage semantics, but consumers should still treat the reference contract as authoritative.

---

# 16. DatasetReference

DatasetReference represents a logical dataset identity without necessarily naming one immutable version.

Use when the consumer needs logical dataset identity, schema identity, a resolvable resource, or lineage connection.

Conceptual fields:

~~~text
DatasetReference
    dataset_id
    owner
    namespace
    schema_fingerprint?
    locator?
    metadata?
    contract_version
~~~

A DatasetReference is not automatically immutable in the versioning sense.

---

# 17. DatasetVersionReference

DatasetVersionReference represents a specific durable version of a dataset.

Its identity MUST be immutable once published.

Conceptual fields:

~~~text
DatasetVersionReference
    dataset_id
    version_id
    owner
    created_at?
    schema_fingerprint?
    content_fingerprint?
    artifact_reference?
    locator?
    contract_version
~~~

If two references share the same dataset_id but different version_id values, they are distinct versions.

---

# 18. Dataset identity ownership

PyIngestKit owns durable ingestion DatasetVersion semantics.

PyTransformKit owns logical Dataset semantics.

These concepts MUST NOT be collapsed into one universal Dataset class.

Boundary mapping is allowed:

~~~text
PyIngestKit DatasetVersionReference
        ↓
PyTransformKit resolver
        ↓
Logical Dataset + physical input binding
~~~

The resulting PyTransformKit Dataset is a transformation-domain value, not the original PyIngestKit object.

---

# 19. Schema references

A reference MAY carry a schema fingerprint or schema reference.

It SHOULD NOT embed a complete engine-native schema unless that is part of an explicitly versioned portable schema contract.

Preferred:

~~~text
schema_fingerprint = "..."
schema_reference   = "..."
~~~

over engine-native dtype dumps.

PyTransformKit remains the canonical owner of portable logical schema semantics.

---

# 20. ExecutionReference

ExecutionReference identifies a runtime execution owned by one bounded context.

Conceptual fields:

~~~text
ExecutionReference
    execution_id
    execution_kind
    owner
    started_at?
    terminal_status?
    external_locator?
    contract_version
~~~

Execution references allow correlation without copying runtime state.

---

# 21. IngestionExecutionReference

Represents one PyIngestKit IngestionRun when it must be referenced externally.

Conceptually:

~~~text
IngestionExecutionReference
    ingestion_run_id
    ingestion_definition_id?
    output_dataset_version?
    status?
    contract_version
~~~

PyWorkflowKit may retain this as evidence attached to a TaskRun.

It does not gain ownership of the ingestion lifecycle.

---

# 22. TransformationExecutionReference

Represents one PyTransformKit TransformationExecution.

Conceptually:

~~~text
TransformationExecutionReference
    transformation_execution_id
    transformation_plan_fingerprint?
    engine_id?
    output_reference?
    status?
    contract_version
~~~

PyWorkflowKit may record this as external workload evidence.

PyIngestKit may use it to attach transformation provenance before publication.

---

# 23. WorkflowExecutionReference

Represents one PyWorkflowKit WorkflowRun when another system needs to correlate against it.

Conceptually:

~~~text
WorkflowExecutionReference
    workflow_run_id
    workflow_definition_id
    status?
    started_at?
    contract_version
~~~

Sibling frameworks do not need to understand TaskRun or TaskAttempt internals merely to retain workflow correlation.

---

# 24. ExternalRunRef

ExternalRunRef is a WorkflowKit-facing portable reference to work executed by another provider.

Its primary purpose is operational evidence.

Conceptual fields:

~~~text
ExternalRunRef
    provider
    external_run_id
    kind
    status_locator?
    metadata?
    contract_version
~~~

Examples:

~~~text
provider = "pyingestkit"
external_run_id = "I-288"

provider = "pytransformkit"
external_run_id = "T-913"

provider = "snowflake"
external_run_id = "01b..."
~~~

ExternalRunRef is intentionally more generic than domain-specific execution references.

---

# 25. Domain-specific reference versus ExternalRunRef

Use a domain-specific reference when semantic interoperability matters.

Example:

~~~text
TransformationExecutionReference
~~~

Use ExternalRunRef when WorkflowKit only needs to track external execution evidence.

An adapter may preserve both without forcing WorkflowKit core to import provider-specific domain internals.

---

# 26. CorrelationContext

CorrelationContext is the portable set of identifiers used to connect activity across frameworks.

Conceptual fields:

~~~text
CorrelationContext
    correlation_id
    causation_id?
    parent_execution_id?
    workflow_run_id?
    task_run_id?
    ingestion_run_id?
    transformation_execution_id?
    trace_id?
~~~

Fields not relevant to a given boundary remain absent.

CorrelationContext does not replace native framework IDs.

---

# 27. Correlation ID

correlation_id groups activity belonging to one broader business or technical operation.

It SHOULD be opaque, safe to propagate, and stable across sibling calls for one composed operation.

It MUST NOT be overloaded as every framework's primary execution ID.

---

# 28. Causation ID

causation_id identifies the immediate event or execution that caused another action.

Example:

~~~text
Workflow TaskRun TR-17
        ↓ causes
IngestionRun I-288

causation_id = TR-17
correlation_id = C-42
~~~

This is optional but valuable for event and audit reconstruction.

---

# 29. Trace interoperability

If distributed tracing is enabled, a trace identifier MAY be included in correlation metadata.

Trace IDs remain observability identifiers.

They do not replace domain execution IDs.

~~~text
trace_id
    !=
workflow_run_id
    !=
ingestion_run_id
    !=
transformation_execution_id
~~~

---

# 30. Reference ownership

Every reference has one semantic owner.

Examples:

~~~text
DatasetVersionReference
    owner = PyIngestKit

TransformationExecutionReference
    owner = PyTransformKit

WorkflowExecutionReference
    owner = PyWorkflowKit
~~~

Consumers may persist a copy of the reference.

They do not become authoritative owners of the referenced object.

---

# 31. Reference resolution

Resolving a reference is an infrastructure concern.

A domain object SHOULD NOT resolve itself by performing network or database I/O.

Preferred:

~~~text
Reference
    ↓
Resolver / Port
    ↓
Resolved resource
~~~

Conceptually:

~~~text
DatasetVersionReference
    ↓
DatasetVersionResolver
    ↓
ResourceReference / physical binding
~~~

---

# 32. Resolver contracts

Resolvers SHOULD be small capabilities.

Examples:

~~~text
ResourceResolver
ArtifactResolver
DatasetReferenceResolver
DatasetVersionResolver
ExternalRunResolver
~~~

Resolvers SHOULD NOT become universal service locators.

---

# 33. Resolution result

Reference resolution SHOULD distinguish important outcomes such as:

~~~text
FOUND
NOT_FOUND
NOT_AUTHORIZED
TEMPORARILY_UNAVAILABLE
UNSUPPORTED_REFERENCE
INVALID_REFERENCE
~~~

Do not collapse all resolution failures into None.

---

# 34. Physical handles

A physical handle is process-local and engine-specific.

Examples:

- Pandas DataFrame handle;
- Polars LazyFrame handle;
- Arrow Table handle;
- DuckDB Relation handle.

Physical handles MAY exist inside PyTransformKit runtime contracts.

They MUST NOT be treated as portable cross-framework references.

~~~text
PhysicalHandle
    !=
ResourceReference
~~~

---

# 35. Reference materialization

Materialization means resolving a portable reference into a runtime object.

Example:

~~~text
DatasetVersionReference
        ↓
resolve
        ↓
ResourceReference
        ↓
engine adapter
        ↓
Physical DatasetHandle
~~~

Materialization is explicit.

Constructing a reference MUST NOT automatically materialize data.

---

# 36. Credentials

Contracts MUST NOT carry plaintext credentials.

Instead use:

~~~text
CredentialReference
SecretReference
~~~

A credential reference MAY identify an environment-backed secret, vault path, cloud identity or runtime provider key.

Credential resolution belongs to runtime/infrastructure composition.

---

# 37. URI safety

URIs embedded in references MUST be treated as potentially sensitive.

A URI may contain usernames, signed query parameters, SAS tokens or presigned credentials.

Logging and repr() MUST therefore apply URI redaction policy.

Credential-free locators are preferred whenever possible.

---

# 38. Metadata field

References MAY carry metadata for extension.

Metadata MUST NOT be used to smuggle required semantics outside the versioned contract.

Bad:

~~~json
{
  "metadata": {
    "real_version_id": "...",
    "must_retry": true
  }
}
~~~

when version identity or retry semantics are actually required fields.

Metadata is for optional descriptive extension.

---

# 39. Metadata namespace

Extension metadata SHOULD use namespaced keys when cross-project collision is possible.

Example:

~~~text
pyingestkit.source_etag
pytransformkit.logical_plan_fingerprint
pyworkflowkit.task_run_id
~~~

Unqualified metadata keys are acceptable only when their meaning is local, obvious and stable.

---

# 40. Contract versioning

Each serialized contract family has its own schema version.

Example:

~~~text
pykit.dataset_version_reference@1
pykit.external_run_ref@1
~~~

Package upgrades do not automatically increment contract versions.

A contract version changes only when the serialized semantic schema changes incompatibly.

---

# 41. Compatibility rules

Readers SHOULD:

- accept versions they explicitly support;
- reject unsupported major contract versions;
- tolerate unknown optional metadata;
- reject missing required fields;
- reject unknown required semantic kinds.

Writers SHOULD:

- emit one declared contract version;
- avoid version negotiation through guesswork;
- remain deterministic where canonical serialization is promised.

---

# 42. Contract evolution

Preferred evolution order:

1. add optional field;
2. define a new enum value only when readers have an unknown-value policy;
3. add a new contract kind;
4. increment incompatible contract version only when required.

Existing required field meaning MUST NOT change silently.

---

# 43. Reference immutability

Portable references SHOULD be immutable value objects.

If a referenced resource moves, either:

- its locator is resolved indirectly;
- a new reference is emitted;
- a mutable registry maps stable identity to current location.

Persisted historical references should not be mutated in place without explicit semantics.

---

# 44. Time fields

Portable timestamps SHOULD use timezone-aware UTC-compatible representations.

Persisted wire formats SHOULD use RFC 3339 / ISO 8601 compatible strings.

Naive local timestamps are prohibited in durable cross-framework contracts.

---

# 45. Status fields in references

References MAY include status as a convenience snapshot.

That status MUST be treated as observational metadata unless the contract explicitly guarantees immutability.

A RUNNING status may become stale.

Consumers needing authoritative state must query the owning system through an explicit resolver or verifier.

---

# 46. Content fingerprints

Where deterministic content identity matters, use explicit fingerprints.

Examples:

~~~text
schema_fingerprint
content_fingerprint
plan_fingerprint
artifact_checksum
~~~

Fingerprints MUST document algorithm, canonicalization rules and semantic scope.

---

# 47. Transformation plan fingerprints

PyTransformKit may expose a canonical plan fingerprint.

That fingerprint can cross boundaries as evidence.

PyWorkflowKit may persist it.

PyIngestKit may attach it as provenance.

Neither framework may reinterpret how the fingerprint is calculated.

The calculation remains owned by PyTransformKit.

---

# 48. Dataset content fingerprints

PyIngestKit may expose durable dataset/content fingerprints.

PyTransformKit may consume them for cache or provenance hints.

PyTransformKit MUST NOT redefine the meaning of a PyIngestKit dataset fingerprint.

If PyTransformKit needs a separate logical fingerprint, it uses its own named field and namespace.

---

# 49. Cross-framework result handoff

The preferred handoff pattern is:

~~~text
Provider Result
    ↓
portable output reference(s)
    ↓
Consumer Adapter
    ↓
Consumer domain binding
~~~

Example:

~~~text
IngestionResult
    output = DatasetVersionReference
        ↓
PyTransformKit adapter
        ↓
Transformation input binding
~~~

---

# 50. No direct internal object handoff

Forbidden as canonical integration:

~~~text
PyIngestKit ORM DatasetVersion object
    ↓
passed directly into PyTransformKit core
~~~

or:

~~~text
Polars LazyFrame
    ↓
stored directly inside WorkflowKit TaskRun metadata
~~~

Integration may optimize in-process transport internally, but the semantic contract must still be expressible through the portable reference model where durability matters.

---

# 51. In-process optimization

An integration adapter MAY share a native handle when:

- both sides explicitly support it;
- ownership is clear;
- lifecycle is bounded;
- a portable fallback/reference exists where persistence or recovery requires it.

Such optimization is not the canonical durable contract.

---

# 52. Cross-host requirement

Any contract intended to survive restart or cross-host execution MUST be resolvable without relying on:

- Python object identity;
- memory address;
- temporary process-local registry;
- unpersisted lambda or function object.

Durable references must identify durable resources or an owner capable of resolving them.

---

# 53. Reference security classification

References SHOULD be classifiable by sensitivity where needed.

Example:

~~~text
PUBLIC
INTERNAL
SENSITIVE
SECRET_BEARING
~~~

A well-designed reference SHOULD almost never be SECRET_BEARING.

If secret-bearing locators cannot be avoided, serialization and logging MUST redact them.

---

# 54. Serialization safety

Portable contracts MUST NOT require arbitrary import-and-instantiate behavior.

Forbidden durable strategy:

~~~json
{
  "class": "my.module.SomeClass",
  "pickle": "..."
}
~~~

Preferred strategy:

~~~json
{
  "contract": "pykit.dataset_version_reference",
  "contract_version": 1
}
~~~

Deserialization must be schema-driven, not arbitrary-code driven.

---

# 55. Contract DTOs

A Python contract DTO SHOULD be a small immutable value object.

Implementation options may include:

- frozen dataclass;
- frozen Pydantic model;
- frozen attrs class;
- equivalent typed immutable structure.

The ecosystem does not mandate one implementation library globally.

Wire semantics matter more than implementation symmetry.

---

# 56. Structural typing at boundaries

A consumer MAY accept a Protocol representing a contract shape when useful.

Durable interoperability MUST NOT depend only on duck typing.

Persisted contracts require explicit semantic kind and version.

---

# 57. Contract conversion

Adapters conceptually convert through:

~~~text
Provider domain
    ↕
Provider reference
    ↕
Shared boundary contract
    ↕
Consumer reference
    ↕
Consumer domain
~~~

Not every step requires a distinct Python class.

The semantic mappings must nevertheless remain explicit and testable.

---

# 58. Anti-corruption layer

Every sibling integration SHOULD have an anti-corruption layer that:

- validates inbound references;
- maps terminology;
- preserves source identity;
- preserves uncertainty;
- preserves error provenance;
- avoids provider internals.

Example:

~~~text
PyIngestKit DatasetVersionReference
        ↓
PyTransformKitDatasetInputAdapter
        ↓
PyTransformKit Dataset input binding
~~~

---

# 59. Ownership of mapping logic

The consuming integration layer generally owns mapping into its own domain.

Example:

~~~text
PyTransformKit integration adapter
    understands how to consume
    DatasetVersionReference
~~~

PyIngestKit should not construct PyTransformKit internal objects directly.

This preserves dependency direction.

---

# 60. Contract registration

If contract kinds become extensible, runtimes MAY maintain typed contract/resolver registries.

Registration MUST be explicit.

Unknown contract kinds MUST fail clearly.

Import-time global mutation is prohibited.

---

# 61. Contract discovery

Automatic discovery, if introduced, SHOULD be metadata-first and opt-in.

Discovery and activation remain distinct.

A discovered handler does not become trusted or active merely because its package is installed.

---

# 62. Example: ingestion to transformation

Canonical handoff:

~~~text
IngestionRuntime.run()
        ↓
IngestionResult
        ↓
DatasetVersionReference
        ↓
PyTransformKit integration adapter
        ↓
DatasetVersionResolver
        ↓
ResourceReference
        ↓
EngineAdapter
        ↓
TransformationExecution
~~~

PyTransformKit does not require access to PyIngestKit persistence internals.

---

# 63. Example: transformation to publication

Canonical handoff:

~~~text
TransformationRuntime.execute()
        ↓
TransformationResult
        ↓
output ResourceReference / DatasetReference
        ↓
PyIngestKit publication adapter
        ↓
DatasetVersion / PublishedDataset
~~~

Publishing transformed output as a governed dataset creates new PyIngestKit-owned version semantics.

---

# 64. Example: workflow to ingestion

Canonical handoff:

~~~text
WorkflowRuntime
    ↓
TaskRun
    ↓
PyIngestKit workload adapter
    ↓
IngestionRuntime.run()
    ↓
IngestionExecutionReference
    ↓
ExternalRunRef
    ↓
TaskRun evidence
~~~

WorkflowKit owns task lifecycle.

PyIngestKit owns ingestion lifecycle.

---

# 65. Example: workflow to transformation

Canonical handoff:

~~~text
WorkflowRuntime
    ↓
TaskRun
    ↓
PyTransformKit workload adapter
    ↓
TransformationRuntime.execute()
    ↓
TransformationExecutionReference
    ↓
ExternalRunRef
    ↓
TaskRun evidence
~~~

WorkflowKit does not inspect TransformationGraph to perform task scheduling.

---

# 66. No semantic tunneling through metadata

A recurring anti-pattern is avoiding formal contracts by placing opaque dictionaries into metadata.

Rejected:

~~~text
metadata = {
    "pytransformkit_everything": {...},
    "pyingestkit_internal_state": {...}
}
~~~

Required integration semantics deserve explicit fields or provider-specific contract types.

Metadata remains supplementary.

---

# 67. No shared universal Dataset type

The ecosystem explicitly rejects a premature universal Dataset base class.

Reason:

~~~text
PyIngestKit DatasetVersion
    durable governed data-product identity

PyTransformKit Dataset
    logical transformation-domain value

PyWorkflowKit
    no dataset semantic ownership
~~~

A portable DatasetReference connects them without erasing their differences.

---

# 68. No shared universal Run type

The following remain distinct:

~~~text
IngestionRun
TransformationExecution
WorkflowRun
TaskRun
TaskAttempt
~~~

A shared generic Run object would erase lifecycle differences.

CorrelationContext and execution references provide interoperability instead.

---

# 69. No shared universal Result type

Each framework owns its result semantics:

~~~text
IngestionResult
TransformationResult
WorkflowResult
~~~

A cross-framework adapter may define an envelope when needed.

The ecosystem does not require one BaseResult.

---

# 70. No shared universal Error hierarchy

Each package retains its own root error:

~~~text
PyIngestKitError
PyTransformKitError
PyWorkflowKitError
~~~

Adapters may normalize error metadata into boundary evidence.

They do not require one cross-package Python exception base class.

---

# 71. FailureReference

For durable execution evidence, an optional portable failure record MAY be defined.

Conceptual fields:

~~~text
FailureReference
    source_framework
    error_code
    category
    retryable?
    uncertain?
    diagnostic_id?
    message_summary?
    contract_version
~~~

This is durable evidence.

It is not a replacement for native exceptions during in-process execution.

---

# 72. Uncertainty representation

Where side-effect outcome is unknown, contracts MUST preserve uncertainty explicitly.

Examples:

~~~text
SUCCEEDED
FAILED
UNKNOWN_OUTCOME
REQUIRES_RECONCILIATION
~~~

Do not convert uncertain execution into generic failure if doing so could encourage unsafe replay.

---

# 73. Retryability metadata

A provider MAY expose retryability as evidence:

~~~text
retryable = true / false / unknown
~~~

The consumer remains responsible for deciding whether its own retry policy permits another attempt.

Provider retryability is advisory unless the integration contract defines stronger semantics.

---

# 74. IdempotencyReference

Where relevant, a boundary MAY carry an idempotency reference.

Conceptually:

~~~text
IdempotencyReference
    namespace
    key
    scope
    owner
~~~

The same raw key MUST NOT automatically be assumed valid across all frameworks.

Scope is essential.

---

# 75. Canonical encoding

Contracts used for fingerprints or signatures require deterministic encoding rules.

When canonical JSON is adopted, rules must define:

- key ordering;
- Unicode normalization;
- numeric representation;
- null omission/inclusion;
- timestamp normalization.

Exact encoding belongs to the future serialization/wire-contract specification.

---

# 76. Contract testing

Every contract family MUST have tests for:

- construction;
- validation;
- serialization;
- round-trip;
- unknown optional metadata;
- unsupported version;
- missing required field;
- invalid owner;
- redaction;
- stable equality;
- deterministic encoding where promised.

Cross-framework adapters MUST have producer-consumer contract tests.

---

# 77. Compatibility matrix

The ecosystem SHOULD eventually publish a machine-readable compatibility matrix.

Conceptually:

~~~text
pyworkflowkit 2.1
    dataset_version_reference: v1
    transformation_execution_reference: v1

pyingestkit 2.0
    pytransformkit resource reference contract: v1
~~~

Compatibility is defined through package ranges and contract versions, not matching release numbers.

---

# 78. Package dependency implications

Because contracts are semantic rather than necessarily implemented in one shared package:

- PyTransformKit core keeps zero sibling dependencies;
- PyIngestKit core keeps zero PyWorkflowKit dependency;
- PyWorkflowKit core keeps zero PyIngestKit/PyTransformKit dependency;
- integration extras may depend on sibling public APIs.

If a shared contract package is later extracted, it must remain dependency-light and domain-neutral.

---

# 79. Criteria for extracting a shared package later

A pykit-contracts-like package may be considered only when all conditions hold:

1. at least two frameworks independently implement the same boundary contract;
2. the wire schema has remained stable across releases;
3. duplication creates measurable maintenance cost;
4. ownership semantics are already clear;
5. extraction does not introduce circular dependencies;
6. the package contains contracts only, not domain services;
7. each framework remains understandable without shared domain inheritance.

Until then, shared specification is preferred over shared code.

---

# 80. Reference model acceptance criteria

This reference model is correctly implemented when:

1. sibling boundaries exchange portable references rather than private objects;
2. references are immutable and serializable;
3. references contain no active resources;
4. credentials are represented only by references/providers;
5. DatasetVersionReference remains owned by PyIngestKit;
6. TransformationExecutionReference remains owned by PyTransformKit;
7. WorkflowExecutionReference remains owned by PyWorkflowKit;
8. WorkflowKit can retain ExternalRunRef without importing provider internals;
9. correlation does not collapse native execution identities;
10. reference resolution is explicit;
11. physical handles are not mistaken for durable references;
12. persisted contract versions are independent from package versions;
13. unsupported required versions fail explicitly;
14. contract DTOs round-trip deterministically where promised;
15. metadata does not carry hidden required semantics;
16. cross-framework adapters preserve uncertainty and failure provenance;
17. no universal Dataset, Run, Result or Error base class is required;
18. no mandatory PyCoreKit/PyCommonKit exists;
19. cross-host references remain resolvable without process-local object identity;
20. producer-consumer contract tests exist for supported integrations.

---

# 81. Normative invariants

### CONTRACT-INV-01 — Domain objects do not cross sibling boundaries directly

Portable references or public contract DTOs mediate the boundary.

### CONTRACT-INV-02 — References do not own resources

They identify or locate them.

### CONTRACT-INV-03 — Identity is not location

Stable identity and physical locator remain distinguishable.

### CONTRACT-INV-04 — Contract version is not package version

Wire evolution is independent.

### CONTRACT-INV-05 — Credentials never become ordinary reference data

Secret resolution is runtime responsibility.

### CONTRACT-INV-06 — Correlation does not replace domain identity

Each framework retains its own execution IDs.

### CONTRACT-INV-07 — Status snapshots may be stale

Authoritative state remains with the owner.

### CONTRACT-INV-08 — Physical handles are not portable references

Engine objects stay inside runtime boundaries.

### CONTRACT-INV-09 — Metadata cannot hide required semantics

Required behavior belongs in explicit contract fields/types.

### CONTRACT-INV-10 — No universal shared domain superclass

Interoperability is contract-based, not inheritance-based.

### CONTRACT-INV-11 — Resolution is explicit

Creating a reference does not perform I/O.

### CONTRACT-INV-12 — Unknown required semantics fail closed

No guessing across contract versions.

---

# 82. Final architecture statement

The PyKit V2 ecosystem shares a **reference language**, not a shared domain model.

The intended composition is:

~~~text
PyIngestKit domain
      ↓
DatasetVersionReference
      ↓
PyTransformKit adapter
      ↓
PyTransformKit domain
      ↓
TransformationExecutionReference
      ↓
PyWorkflowKit / PyIngestKit adapters
~~~

and:

~~~text
WorkflowRun
   ↓
TaskRun
   ↓
ExternalRunRef
   ↓
provider-owned execution
~~~

The central rule is:

> **Cross a framework boundary with identity, location, correlation and explicit contract semantics — not with private runtime objects.**

This specification is the baseline for the next ecosystem documents:

~~~text
PYKIT_ECOSYSTEM_V2_EXECUTION_IDENTITY_AND_CORRELATION_MODEL.md
PYKIT_ECOSYSTEM_V2_ERROR_FAILURE_RETRY_AND_UNCERTAINTY_MODEL.md
PYKIT_ECOSYSTEM_V2_DATASET_RESOURCE_AND_ARTIFACT_INTEROPERABILITY.md
PYKIT_ECOSYSTEM_V2_SERIALIZATION_AND_WIRE_CONTRACTS.md
~~~
