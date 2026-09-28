# PyIngestKit V2 — Public API Specification

> **Status:** NORMATIVE PUBLIC API BASELINE  
> **Target release:** PyIngestKit 2.0.0  
> **Date:** 2026-09-29  
> **Architecture generation:** PyKit Ecosystem V2  
> **Depends on:** PYINGESTKIT_V2_TARGET_ARCHITECTURE.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_DECLARATION_PLAN_RUNTIME_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_PUBLIC_API_DESIGN_PRINCIPLES.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_RELEASE_COMPATIBILITY_AND_VERSIONING_POLICY.md

---

# 1. Purpose

This document freezes the target public Python API of PyIngestKit 2.0.

It defines the stable vocabulary, import paths, declaration model, runtime entry points, source and decoder contracts, RAW/artifact contracts, validation and quality surfaces, DatasetVersion semantics, publication and replay APIs, stores, results, diagnostics, exceptions, serialization, plugins, optional PyTransformKit integration and V1-to-V2 compatibility posture.

> **The public API must make ingestion evidence, version identity and publication semantics explicit without turning PyIngestKit into either a transformation engine or a workflow runtime.**

---

# 2. Canonical user flow

The canonical public lifecycle is:

~~~text
declare Source
        ↓
build IngestionDefinition
        ↓
IngestionRuntime.run(...)
        ↓
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
IngestionResult
~~~

The user does not construct a public IngestionLifecycle or IngestionPlan in the common path.

---

# 3. Canonical package-root imports

PyIngestKit 2.0 SHOULD support:

~~~python
from pyingestkit import (
    ArtifactReference,
    DatasetVersion,
    DatasetVersionReference,
    IngestionDefinition,
    IngestionResult,
    IngestionRun,
    IngestionRunId,
    IngestionRuntime,
    PublishedDataset,
    ResourceReference,
    Source,
)
~~~

The package root remains curated rather than exhaustive.

---

# 4. Stable root surface

The following categories are intended to be STABLE at 2.0:

~~~text
IngestionDefinition
IngestionRuntime
IngestionRun / IngestionRunId
IngestionResult

Source
ArtifactReference
ResourceReference

DatasetVersion
DatasetVersionReference
PublishedDataset

selected policies
selected typed status values
selected public exceptions
~~~

Private repositories, ORM entities, provider clients, lifecycle orchestration helpers and decoder implementation details are not root exports.

---

# 5. Qualified public namespaces

Stable or intentionally public namespaces SHOULD include:

~~~text
pyingestkit.sources
pyingestkit.decoders
pyingestkit.validation
pyingestkit.quality
pyingestkit.artifacts
pyingestkit.datasets
pyingestkit.publication
pyingestkit.replay
pyingestkit.runtime
pyingestkit.stores
pyingestkit.serialization
pyingestkit.provenance
pyingestkit.diagnostics
pyingestkit.plugins
pyingestkit.integrations.pytransformkit
~~~

Provider-specific adapters live under qualified namespaces.

---

# 6. Import-time safety

Importing pyingestkit MUST NOT:

- contact external sources;
- resolve credentials;
- import every optional provider SDK;
- activate plugins;
- open databases;
- create files;
- mutate mandatory global registries;
- emit network telemetry;
- start ingestion.

Core import must succeed with base dependencies only.

---

# 7. Constructor safety

Public constructors MUST be side-effect free.

Constructing Source, IngestionDefinition, policies, references, store configuration or publication declarations MUST NOT perform acquisition, open connections, create targets or resolve secrets.

External effects begin only through explicit runtime operations.

---

# 8. IngestionDefinition

IngestionDefinition is the canonical authoring root.

A representative construction is:

~~~python
definition = IngestionDefinition(
    name="customers",
    source=source,
    decoder="csv",
    dataset="customers",
)
~~~

Exact overloads MAY improve ergonomics, but the semantic model remains explicit.

---

# 9. IngestionDefinition stable properties

Stable properties SHOULD include:

~~~text
name
source
decoder
dataset identity
raw policy
validation policy
versioning policy
publication policy
metadata
~~~

The object is immutable or effectively immutable.

It contains no current run ID, retry counter or provider session.

---

# 10. No mandatory public IngestionPlan

PyIngestKit 2.0 does not expose IngestionPlan as a required public type.

The runtime MAY internally normalize definitions.

Public callers should not need to write:

~~~text
definition
    → IngestionPlan
    → run
~~~

unless future implementation evidence justifies a separately inspectable compiled ingestion plan.

---

# 11. Source API

Source is the public ingestion declaration for acquisition origin and semantics.

Representative constructors SHOULD exist through typed factory methods:

~~~python
Source.file(
    path="/data/customers.csv",
)

Source.http(
    url="https://example.test/customers.csv",
)

Source.object(
    uri="s3://bucket/customers.csv",
)

Source.database(
    connection="analytics",
    query="select * from customers",
)
~~~

Provider-specific source types MAY live in qualified namespaces.

---

# 12. Source invariants

Source MUST remain declarative.

It MUST NOT contain:

~~~text
open file handle
live HTTP client
database connection
resolved secret value
provider SDK client
active export job
~~~

Source MAY contain CredentialReference, provider configuration identifiers and safe portable acquisition metadata.

---

# 13. Source versus ResourceReference

The public API preserves:

~~~text
Source
    acquisition intent and semantics

ResourceReference
    portable resource identity/location
~~~

A Source can resolve to one or more ResourceReference values during acquisition.

The two types are not aliases.

---

# 14. SourceConnector Protocol

The stable source extension Protocol SHOULD conceptually expose:

~~~python
class SourceConnector(Protocol):

    @property
    def descriptor(
        self,
    ) -> SourceConnectorDescriptor:
        ...

    def acquire(
        self,
        request: AcquisitionRequest,
    ) -> AcquisitionResult:
        ...

    def reconcile(
        self,
        request: AcquisitionReconciliationRequest,
    ) -> AcquisitionReconciliationResult:
        ...
~~~

reconcile MAY be optional through capability declaration.

Exact request/result fields are frozen by conformance tests.

---

# 15. SourceConnectorDescriptor

A connector descriptor SHOULD expose:

~~~text
id
display_name
connector_version
supported source kinds
capabilities
optional dependency status
~~~

Published connector IDs become compatibility surfaces.

---

# 16. AcquisitionResult

AcquisitionResult SHOULD expose structured evidence such as:

~~~text
status
ResourceReference or acquired stream handle
ArtifactReference when already persisted
source metadata
checksum when available
provider request/export identifiers
diagnostics
FailureEvidence
~~~

AcquisitionResult is not the final IngestionResult.

---

# 17. RAW policy

RAW policy SHOULD be represented by a typed immutable value.

Representative construction:

~~~python
from pyingestkit.artifacts import (
    RawPolicy,
)

raw_policy = RawPolicy(
    enabled=True,
    retain=True,
    checksum="sha256",
)
~~~

Exact fields MAY expand additively.

---

# 18. RAW API surface

RAW itself may be represented as a domain value under pyingestkit.artifacts or pyingestkit.runtime.

The stable public boundary for durable RAW is ArtifactReference.

Consumers SHOULD NOT rely on a provider-specific RAW storage object.

---

# 19. ArtifactReference

ArtifactReference is the portable reference to durable evidence.

It SHOULD expose:

~~~text
artifact_id
kind
resource
checksum
media_type
size when known
created_at
metadata
~~~

Exact fields are versioned through the wire contract.

Raw secret values are prohibited.

---

# 20. ArtifactStore Protocol

The stable ArtifactStore Protocol SHOULD conceptually provide:

~~~python
class ArtifactStore(Protocol):

    def put(
        self,
        request: PutArtifactRequest,
    ) -> PutArtifactResult:
        ...

    def open(
        self,
        reference: ArtifactReference,
    ) -> ArtifactReader:
        ...

    def exists(
        self,
        reference: ArtifactReference,
    ) -> bool:
        ...
~~~

Deletion/lifecycle operations MAY be capability-dependent.

---

# 21. ArtifactStore invariants

ArtifactStore semantics are about durable material evidence.

An ArtifactStore MUST NOT be assumed to provide DatasetVersion metadata semantics or publication-pointer semantics.

One backend may implement several ports explicitly, but the contracts remain distinct.

---

# 22. Decoder selection

IngestionDefinition MAY identify decoders by stable ID:

~~~python
definition = IngestionDefinition(
    name="customers",
    source=source,
    decoder="csv",
    dataset="customers",
)
~~~

A richer explicit object MAY also be supported:

~~~python
from pyingestkit.decoders import (
    CsvDecoderConfig,
)

definition = IngestionDefinition(
    name="customers",
    source=source,
    decoder=CsvDecoderConfig(
        delimiter=",",
        header=True,
    ),
    dataset="customers",
)
~~~

---

# 23. Decoder Protocol

The stable decoder extension Protocol SHOULD conceptually expose:

~~~python
class Decoder(Protocol):

    @property
    def descriptor(
        self,
    ) -> DecoderDescriptor:
        ...

    def decode(
        self,
        request: DecodeRequest,
    ) -> DecodeResult:
        ...
~~~

Decoder output remains ingestion representation, not business transformation output.

---

# 24. DecoderDescriptor

Descriptor fields SHOULD include:

~~~text
id
decoder_version
media types / formats
capabilities
portable configuration schema
~~~

Stable decoder IDs such as csv, jsonl, parquet MAY become public compatibility surfaces.

---

# 25. DecodeResult

DecodeResult SHOULD expose:

~~~text
decoded representation handle
schema evidence
row count when known
diagnostics
decoder identity/version
rejected representation evidence when applicable
~~~

The decoded representation may remain runtime-local.

It is not a DatasetVersion by itself.

---

# 26. Decode != transform

The public API MUST NOT encourage arbitrary relational business transformations inside Decoder.

The following remain outside Decoder semantics:

~~~text
join
aggregate
window
pivot
multi-dataset enrichment
business-derived measures
complex relational reshaping
~~~

These belong to PyTransformKit or application code.

---

# 27. Validation API

Validation SHOULD use explicit contracts and policies.

Representative API:

~~~python
from pyingestkit.validation import (
    ValidationPolicy,
)

policy = ValidationPolicy(
    fail_on_error=True,
)
~~~

Definitions MAY attach validation rules through typed values or stable provider-independent rule descriptors.

---

# 28. Validation rules

Stable rule families MAY include:

~~~text
required field
type compatibility
nullability
allowed values
uniqueness
row-count bounds
schema fingerprint
custom registered rule
~~~

Arbitrary executable callbacks are non-portable unless explicitly marked trusted/local.

---

# 29. ValidationResult

ValidationResult SHOULD expose:

~~~text
status
rule outcomes
error count
warning count
rejected record count when applicable
diagnostics
ArtifactReference to detailed report when persisted
~~~

Validation results are evidence, not transformation output.

---

# 30. Rejected-record policy

The public API SHOULD provide typed policies such as:

~~~text
FAIL_ALL
QUARANTINE_REJECTS
ALLOW_WITH_THRESHOLD
~~~

A custom policy MAY exist in a qualified advanced namespace.

Silent record dropping is prohibited.

---

# 31. Quality API

Quality/profiling capabilities SHOULD live under pyingestkit.quality.

Representative configuration MAY request:

~~~text
row count
null counts
distinct counts
min/max
schema summary
selected profile metrics
~~~

Quality output may be returned inline or persisted as ArtifactReference.

---

# 32. Dataset identity

IngestionDefinition SHOULD declare a stable dataset identity separate from DatasetVersion identity.

Representative form:

~~~python
definition = IngestionDefinition(
    name="customers_ingestion",
    source=source,
    decoder="csv",
    dataset="customers",
)
~~~

The string customers identifies the governed dataset family; the concrete version is created at runtime.

---

# 33. DatasetVersion

DatasetVersion is the public immutable governed version value.

Stable properties SHOULD include:

~~~text
id
dataset
artifacts
resources
schema fingerprint
content fingerprint
provenance
created_at
originating run reference
publication evidence
~~~

DatasetVersion is not a physical dataframe or mutable latest pointer.

---

# 34. DatasetVersionId

DatasetVersionId is an immutable typed identifier.

It SHOULD support:

~~~python
str(version_id)
DatasetVersionId.parse(value)
~~~

Identity generation semantics are implementation-defined but stable within the contract.

---

# 35. DatasetVersionReference

DatasetVersionReference is the portable cross-framework reference.

Representative usage:

~~~python
ref = result.dataset_version
~~~

The reference MUST contain enough portable identity to resolve a concrete version without carrying active clients or credentials.

---

# 36. DatasetVersionStore Protocol

A stable DatasetVersionStore Protocol SHOULD conceptually support:

~~~python
class DatasetVersionStore(Protocol):

    def save(
        self,
        version: DatasetVersion,
    ) -> None:
        ...

    def get(
        self,
        reference: DatasetVersionReference,
    ) -> DatasetVersion:
        ...

    def list_versions(
        self,
        dataset: str,
    ) -> Sequence[
        DatasetVersionReference
    ]:
        ...
~~~

Current/latest lookup is explicit and must not replace concrete-version APIs.

---

# 37. PublishedDataset

PublishedDataset represents a governed named publication pointer.

Stable properties MAY include:

~~~text
name
current DatasetVersionReference
publication metadata
updated_at
~~~

A PublishedDataset pointer may move.

A DatasetVersion does not.

---

# 38. PublicationPolicy

Publication intent SHOULD use an immutable typed policy.

Representative construction:

~~~python
from pyingestkit.publication import (
    PublicationMode,
    PublicationPolicy,
)

policy = PublicationPolicy(
    mode=(
        PublicationMode
        .APPEND_NEW_VERSION
    ),
)
~~~

Exact modes are frozen in the implementation roadmap and conformance tests.

---

# 39. Publication modes

The stable semantic set SHOULD cover at least concepts equivalent to:

~~~text
CREATE_NEW
FAIL_IF_EXISTS
APPEND_NEW_VERSION
REPLACE_POINTER
REGISTER_EXISTING_RESOURCE
MATERIALIZE_AND_REGISTER
~~~

Provider-specific physical details remain adapter capabilities.

---

# 40. Target API

Publication targets SHOULD be represented through target declarations in pyingestkit.publication or provider-qualified namespaces.

Representative form:

~~~python
from pyingestkit.publication import (
    Target,
)

target = Target.file(
    path="/published/customers",
)
~~~

Target construction performs no external write.

---

# 41. Target Protocol

A stable Target/Publisher extension Protocol SHOULD conceptually expose:

~~~python
class Publisher(Protocol):

    @property
    def descriptor(
        self,
    ) -> PublisherDescriptor:
        ...

    def publish(
        self,
        request: PublicationRequest,
    ) -> PublicationResult:
        ...

    def reconcile(
        self,
        request: PublicationReconciliationRequest,
    ) -> PublicationReconciliationResult:
        ...
~~~

reconcile may be capability-dependent.

---

# 42. PublicationResult

PublicationResult SHOULD distinguish:

~~~text
SUCCEEDED
FAILED
UNKNOWN_OUTCOME
CONFLICT
CANCELLED
~~~

and SHOULD expose:

~~~text
DatasetVersionReference
PublishedDataset reference when applicable
ResourceReference
idempotency evidence
provider operation reference
diagnostics
FailureEvidence
~~~

---

# 43. Write != publish in the API

The public API MUST preserve:

~~~text
physical write result
    !=
DatasetVersion publication result
~~~

A provider adapter may physically write bytes and then register/version them.

The final public publication result represents governed state, not merely successful I/O.

---

# 44. Idempotency API

Publication and acquisition requests MAY carry IdempotencyReference.

Representative use:

~~~python
from pyingestkit import (
    IdempotencyReference,
)

key = IdempotencyReference(
    scope="customers-publication",
    key="2026-09-29",
)
~~~

The presence of a key does not create idempotency if the provider cannot honor the required semantics.

---

# 45. UNKNOWN_OUTCOME

UNKNOWN_OUTCOME is a stable public semantic outcome.

The API MUST NOT collapse it to FAILED.

A publication result, run state or exception MUST preserve uncertainty when the provider may have committed.

---

# 46. Reconciliation API

Public reconciliation SHOULD be available through runtime or dedicated services.

Representative form:

~~~python
reconciled = runtime.reconcile(
    run_id
)
~~~

or:

~~~python
reconciled = (
    runtime.reconcile_publication(
        publication_reference
    )
)
~~~

Exact method shape is frozen by implementation evidence.

The semantic requirement is stable: reconciliation inspects existing external truth before unsafe retry.

---

# 47. Replay API

Replay is an explicit runtime operation.

Representative API:

~~~python
result = runtime.replay(
    prior_run=run_id,
)
~~~

or:

~~~python
result = runtime.replay(
    raw=artifact_reference,
    definition=definition,
)
~~~

Replay receives a fresh IngestionRunId and records replay provenance.

---

# 48. Replay invariants

Replay MUST NOT:

- contact the original source unless explicitly configured as reacquisition;
- reuse the original IngestionRunId;
- hide that replay occurred;
- silently turn into WorkflowKit retry semantics.

Replay starts from preserved evidence.

---

# 49. IngestionRuntime construction

Canonical construction SHOULD be dependency-injected:

~~~python
runtime = IngestionRuntime(
    sources=source_registry,
    decoders=decoder_registry,
    artifacts=artifact_store,
    versions=dataset_version_store,
    publishers=publisher_registry,
)
~~~

Optional telemetry, clock, ID generator, credential resolver and plugin registry may also be supplied.

Hidden mandatory global singletons are prohibited.

---

# 50. Runtime run API

Canonical execution:

~~~python
result = runtime.run(
    definition,
    correlation=correlation,
)
~~~

The runtime performs the declared lifecycle.

No WorkflowKit dependency is required.

---

# 51. Explicit runtime overrides

run MAY accept carefully bounded runtime-only overrides such as:

~~~text
correlation context
credential bindings
dry-run/preflight policy
runtime timeout
provider selection where declaration permits it
telemetry context
~~~

Runtime overrides MUST NOT silently rewrite core ingestion semantics.

---

# 52. IngestionRunId

IngestionRunId is an immutable typed identifier.

It SHOULD support string conversion and parsing.

A new semantic ingestion execution receives a new ID.

Bounded internal retries preserve it.

Replay creates a new ID.

---

# 53. IngestionRun

IngestionRun is the durable/inspectable runtime record.

Stable or semi-stable properties SHOULD include:

~~~text
id
status
definition fingerprint
correlation
source evidence
RAW ArtifactReference
decode evidence
validation evidence
DatasetVersionReference
publication evidence
replay origin
failure
diagnostics
timestamps
~~~

The complete persistence entity MAY contain internal fields not exposed publicly.

---

# 54. IngestionResult

IngestionResult is the caller-facing immutable outcome.

It SHOULD expose:

~~~text
run_id
status
dataset_version
artifacts
publication
diagnostics
failure
correlation
manifest reference when available
~~~

It SHOULD remain smaller and more stable than private persisted run state.

---

# 55. IngestionStatus

Stable terminal outcomes SHOULD include:

~~~text
SUCCEEDED
FAILED
CANCELLED
TIMED_OUT
UNKNOWN_OUTCOME
PARTIAL when explicitly supported
~~~

Transitional runtime states MAY exist on IngestionRun without being required on final IngestionResult.

---

# 56. Failure behavior

Programmer/configuration errors normally raise typed exceptions.

Operational execution failures MUST expose structured FailureEvidence on the raised exception, IngestionResult or both according to explicit runtime policy.

Exception text alone is never the semantic API.

---

# 57. Diagnostics

A structured Diagnostic SHOULD include:

~~~text
code
severity
summary
optional details
stage
source/target context
related rule or field
~~~

Stable diagnostic codes used for automation become compatibility contracts.

---

# 58. Exception hierarchy

The public exception hierarchy SHOULD include concepts equivalent to:

~~~text
PyIngestKitError
    ValidationError
    SourceConfigurationError
    AcquisitionError
    DecodeError
    IntegrityError
    ArtifactStoreError
    DatasetVersionError
    PublicationError
    ReplayError
    SerializationError
    PluginError
    IntegrationError
~~~

Exact names may gain additive subclasses after 2.0.

---

# 59. Exception evidence

Operational exceptions SHOULD expose:

~~~text
category
code
failure_evidence
run_id when allocated
correlation
diagnostics
cause
~~~

Provider-native exceptions may remain available as cause without defining public semantics.

---

# 60. Source registry

Source connectors SHOULD use explicit registry objects.

Representative API:

~~~python
from pyingestkit.sources import (
    SourceRegistry,
)

sources = SourceRegistry()

sources.register(
    FileSourceConnector()
)
~~~

Registration is explicit and import-time global mutation is prohibited.

---

# 61. Decoder registry

Representative API:

~~~python
from pyingestkit.decoders import (
    DecoderRegistry,
)

decoders = DecoderRegistry()

decoders.register(
    CsvDecoder()
)
~~~

Duplicate registration fails unless explicit replacement is requested.

---

# 62. Publisher registry

Representative API:

~~~python
from pyingestkit.publication import (
    PublisherRegistry,
)

publishers = PublisherRegistry()

publishers.register(
    FilePublisher()
)
~~~

Provider selection is explicit through target/definition semantics.

---

# 63. Store construction

Store implementations live in qualified namespaces.

Examples MAY include:

~~~python
from pyingestkit.stores.filesystem import (
    FileArtifactStore,
)

from pyingestkit.stores.sqlite import (
    SQLiteDatasetVersionStore,
)
~~~

Core protocols remain provider-neutral.

---

# 64. Local file source

A stable local source path SHOULD be available without cloud dependencies.

Representative usage:

~~~python
source = Source.file(
    path="./data/customers.csv",
)
~~~

Path validation and symlink/root policy are runtime security concerns.

---

# 65. HTTP source

HTTP support SHOULD be optional.

Representative installation:

~~~text
pip install pyingestkit[http]
~~~

Representative source:

~~~python
source = Source.http(
    url=(
        "https://example.test/"
        "customers.csv"
    ),
    credential=credential_ref,
)
~~~

Credential values are not embedded.

---

# 66. CSV decoder

CSV is an intended stable V2 decoder.

Representative config:

~~~python
from pyingestkit.decoders import (
    CsvDecoderConfig,
)

decoder = CsvDecoderConfig(
    delimiter=",",
    header=True,
    encoding="utf-8",
)
~~~

CSV semantics must be deterministic and documented.

---

# 67. JSON / NDJSON decoder

JSON and NDJSON SHOULD be stable or clearly distinguished.

Representative config MAY use:

~~~python
JsonDecoderConfig(
    mode="ndjson",
)
~~~

Nested structure handling must be explicit rather than silently flattened.

---

# 68. Parquet decoder

Parquet support MAY live behind:

~~~text
pip install pyingestkit[parquet]
~~~

Its logical schema evidence must remain provider-neutral.

A native PyArrow table is not the durable public domain value.

---

# 69. Excel decoder

Excel support MAY live behind:

~~~text
pip install pyingestkit[excel]
~~~

Workbook/sheet selection is decoder configuration.

Excel-specific libraries remain optional implementation dependencies.

---

# 70. PostgreSQL support

PostgreSQL support MAY provide source extraction, publication target and store implementations through explicit different ports.

A single backend class SHOULD NOT blur these domain roles in the public API.

Potential extra:

~~~text
pip install pyingestkit[postgres]
~~~

---

# 71. S3-compatible support

S3-compatible support MAY provide source, ArtifactStore and Target adapters.

Potential extra:

~~~text
pip install pyingestkit[s3]
~~~

Each adapter role is explicitly selected.

The same bucket provider does not collapse ArtifactStore and Target semantics.

---

# 72. Provenance API

Provenance SHOULD be queryable through immutable public values under pyingestkit.provenance.

Representative use:

~~~python
provenance = result.provenance
provenance.source
provenance.raw_artifact
provenance.dataset_version
~~~

PyIngestKit provenance does not own PyTransformKit field lineage.

---

# 73. Manifest API

Ingestion manifests SHOULD use explicit versioned contracts.

Representative access:

~~~python
manifest_ref = result.manifest

manifest = (
    runtime
    .manifests
    .get(manifest_ref)
)
~~~

Exact store accessor shape may vary.

Manifest content MUST exclude raw secrets and active handles.

---

# 74. Serialization API

Portable serialization SHOULD use explicit codecs.

Representative surface:

~~~python
from pyingestkit.serialization import (
    DatasetVersionReferenceCodec,
    IngestionDefinitionCodec,
    IngestionManifestCodec,
)

payload = (
    DatasetVersionReferenceCodec
    .to_json(ref)
)

ref2 = (
    DatasetVersionReferenceCodec
    .from_json(payload)
)
~~~

Every stable payload uses contract and contract_version.

---

# 75. Portable definition restrictions

IngestionDefinition serialization MUST reject or explicitly mark non-portable constructs such as:

~~~text
arbitrary Python callbacks
live provider clients
open streams
raw credentials
unregistered executable validation rules
process-local decoded handles
~~~

No pickle-like fallback is allowed.

---

# 76. Plugin API

Discovery and activation are separate.

Representative usage:

~~~python
from pyingestkit.plugins import (
    PluginRegistry,
)

plugins = (
    PluginRegistry
    .discover()
)

plugins.activate(
    "my-source-plugin"
)
~~~

Discovery does not grant execution authority.

---

# 77. Plugin compatibility

Plugins MUST declare protocol/package compatibility.

Stable plugin extension categories may include:

~~~text
source connector
decoder
ArtifactStore
DatasetVersionStore
publisher/target
quality provider
telemetry sink
~~~

Untrusted payloads cannot activate plugins.

---

# 78. Optional extras

Candidate stable extras include:

~~~text
[http]
[excel]
[parquet]
[postgres]
[s3]
[transform]
~~~

Exact final extras are frozen by packaging tests.

Base pyingestkit import must not require them.

---

# 79. PyTransformKit integration install

The optional sibling integration SHOULD use:

~~~text
pip install pyingestkit[transform]
~~~

Core PyIngestKit remains usable without PyTransformKit.

---

# 80. PyTransformKit integration namespace

The official integration lives under:

~~~text
pyingestkit.integrations.pytransformkit
~~~

Representative imports MAY include:

~~~python
from pyingestkit.integrations.pytransformkit import (
    DatasetVersionInputAdapter,
    TransformationPublicationAdapter,
)
~~~

Exact class names are frozen only after real Customer 360 implementation evidence.

---

# 81. DatasetVersion to Transformation input

The semantic integration is:

~~~text
DatasetVersionReference
    ↓
resolve concrete ResourceReference
    ↓
PyTransformKit InputBinding
~~~

No PyIngestKit repository object crosses the boundary.

---

# 82. TransformationResult to publication

The reverse handoff is:

~~~text
PyTransformKit TransformationResult
    ↓
ResourceReference
    ↓
PyIngestKit publication
    ↓
DatasetVersion
~~~

PyIngestKit retains TransformationExecutionReference in provenance when available.

---

# 83. No duplicated transformation API

PyIngestKit MUST NOT expose root APIs equivalent to:

~~~text
join
aggregate
window
pivot
logical-plan optimizer
generic relational DAG
~~~

If needed, these operations are delegated to PyTransformKit or application code.

---

# 84. CredentialReference

CredentialReference MAY appear in Source/Target/runtime configuration through the shared ecosystem contract.

Raw credentials MUST NOT appear in:

~~~text
IngestionDefinition serialization
DatasetVersionReference
ArtifactReference
manifests
provenance
diagnostics
logs
metric labels
~~~

---

# 85. Resource security

Source and target resolution MAY accept policy objects covering:

~~~text
allowed schemes
allowed hosts
private-network access
redirects
filesystem roots
symlink behavior
maximum payload size
file types
~~~

Unknown safety-sensitive configuration fails closed.

---

# 86. Thread/process safety

Every stable connector, decoder, store and publisher documents:

~~~text
thread safety
process safety
async behavior
connection ownership
cleanup behavior
reentrancy
~~~

Normal operation must not require hidden mutable global clients.

---

# 87. Stability tiers

At 2.0:

~~~text
STABLE
    canonical root API
    Source/IngestionDefinition
    RAW/Artifact references
    DatasetVersion/PublishedDataset
    IngestionRuntime
    stable store/source/decoder/publication protocols
    stable codecs

PROVISIONAL
    advanced provider-specific capabilities
    optional emerging connectors

INTERNAL
    lifecycle state helpers
    provider SDK wrappers
    ORM entities
    temporary decoded representations
~~~

Stability level must be visible in documentation.

---

# 88. V1 Job/Pipeline/Step migration

Legacy generic execution vocabulary does not define V2 public API.

Semantic mapping:

~~~text
V1 Job
    → IngestionDefinition + IngestionRuntime

V1 acquisition Step
    → SourceConnector / runtime lifecycle

V1 business transform Step
    → PyTransformKit integration

V1 orchestration Pipeline
    → PyWorkflowKit when appropriate
~~~

No permanent generic alias layer is required.

---

# 89. V1 RAW migration

Existing immutable RAW/SHA256 behavior SHOULD be retained where aligned.

The public V2 expression becomes:

~~~text
RAW evidence
    → ArtifactReference
    → provenance
~~~

Implementation details may change behind the stable contract.

---

# 90. V1 DatasetVersion migration

Existing content-addressed snapshot behavior is reusable only after enforcing:

~~~text
DatasetVersion != Artifact
DatasetVersionStore != ArtifactStore
PublishedDataset != DatasetVersion
~~~

Any old conflation must be corrected before 2.0 freeze.

---

# 91. V1 replay migration

Existing replay APIs should migrate to explicit runtime.replay semantics.

Replay creates a new IngestionRunId and preserves origin references.

The old implementation may be reused only if it avoids reacquisition.

---

# 92. V1 CLI posture

CLI may remain a supported convenience surface.

Stable machine-readable CLI output, if declared, must be versioned.

CLI MUST consume public application/runtime APIs rather than private repositories or ORM models.

---

# 93. Local end-to-end example

~~~python
from pyingestkit import (
    IngestionDefinition,
    IngestionRuntime,
    Source,
)

from pyingestkit.artifacts.filesystem import (
    FileArtifactStore,
)

from pyingestkit.decoders import (
    CsvDecoder,
    DecoderRegistry,
)

from pyingestkit.sources import (
    FileSourceConnector,
    SourceRegistry,
)

from pyingestkit.stores.sqlite import (
    SQLiteDatasetVersionStore,
)

sources = SourceRegistry()

sources.register(
    FileSourceConnector()
)

decoders = DecoderRegistry()

decoders.register(
    CsvDecoder()
)

runtime = IngestionRuntime(
    sources=sources,
    decoders=decoders,
    artifacts=FileArtifactStore(
        "./artifacts"
    ),
    versions=(
        SQLiteDatasetVersionStore(
            "./metadata.db"
        )
    ),
)

definition = IngestionDefinition(
    name="customers",
    source=Source.file(
        "./data/customers.csv"
    ),
    decoder="csv",
    dataset="customers",
)

result = runtime.run(
    definition
)

print(
    result.dataset_version
)
~~~

This example is normative in architectural shape.

Concrete adapter constructor details may evolve before API freeze.

---

# 94. Publication example

~~~python
from pyingestkit.publication import (
    FileTarget,
    PublicationMode,
    PublicationPolicy,
)

definition = IngestionDefinition(
    name="customers",
    source=Source.file(
        "./data/customers.csv"
    ),
    decoder="csv",
    dataset="customers",
    publication=PublicationPolicy(
        target=FileTarget(
            "./published/customers"
        ),
        mode=(
            PublicationMode
            .APPEND_NEW_VERSION
        ),
    ),
)

result = runtime.run(
    definition
)
~~~

Successful physical writing is not by itself the full publication contract.

---

# 95. Replay example

~~~python
replayed = runtime.replay(
    prior_run=result.run_id
)

assert (
    replayed.run_id
    != result.run_id
)
~~~

The new run must expose replay provenance.

---

# 96. PyTransformKit handoff example

~~~python
from pyingestkit.integrations.pytransformkit import (
    to_input_binding,
)

binding = to_input_binding(
    result.dataset_version
)
~~~

This helper belongs to the optional integration package and may require pytransformkit[appropriate extra].

PyIngestKit core does not import TransformationPlan or TransformationRuntime.

---

# 97. API anti-patterns

Rejected public patterns include:

~~~text
IngestionDefinition.run() as the only/primary execution model
public IngestionPlan required for every ingestion
DatasetVersion storing live DataFrame
ArtifactStore used as implicit DatasetVersionStore
Target used as implicit ArtifactStore
physical write treated as automatic publication
Decoder performing joins/aggregations/business transformations
replay contacting source without explicit reacquisition mode
global mandatory provider registry
pickle-based durable definition/run serialization
raw credentials embedded in Source or DatasetVersionReference
~~~

---

# 98. Root exclusion list

The package root MUST NOT export by default:

~~~text
IngestionLifecycle
IngestionPlan
private lifecycle stage objects
ORM entities
provider SDK clients
private SourceConnector implementations
private decoder internals
private publisher internals
plugin loader internals
temporary decoded representation classes
~~~

---

# 99. Compatibility tests

Release CI MUST snapshot and compare at least:

~~~text
root exports
qualified stable exports
public signatures
constructors
Protocol members
exception hierarchy
enum members
stable source/decoder/publisher IDs
stable extra names
wire contract versions
stable plugin entry-point groups
~~~

Unexpected stable-surface drift blocks release.

---

# 100. Public API acceptance criteria

PyIngestKit V2 public API is accepted when:

1. root import works with base dependencies only;
2. IngestionDefinition is the canonical authoring root;
3. no public IngestionPlan is required;
4. Source remains declarative and side-effect free;
5. Source and ResourceReference remain distinct;
6. RAW is represented through durable artifact evidence;
7. ArtifactStore and DatasetVersionStore are separate public ports;
8. Decoder does not own relational business transformation;
9. DatasetVersion is immutable governed identity;
10. DatasetVersionReference is portable and fixture-tested;
11. PublishedDataset pointer semantics are explicit;
12. write and publish remain distinct;
13. UNKNOWN_OUTCOME is public and preserved;
14. replay creates a new IngestionRunId from preserved evidence;
15. IngestionRuntime is the primary execution service;
16. IngestionResult exposes structured version/evidence/failure information;
17. optional providers do not contaminate core import;
18. PyTransformKit integration remains optional;
19. V1 generic Job/Pipeline/Step concepts do not distort V2 root API;
20. API freeze tests pass against built wheels.

---

# 101. Normative API invariants

### PIK-API-INV-01 — Root API is curated

Only canonical ingestion concepts are promoted to package root.

### PIK-API-INV-02 — IngestionDefinition is declarative

Construction performs no acquisition, publication or credential resolution.

### PIK-API-INV-03 — No mandatory public IngestionPlan exists

Runtime may prepare execution internally without exposing artificial layers.

### PIK-API-INV-04 — Source and ResourceReference differ

Acquisition intent is not reduced to physical location.

### PIK-API-INV-05 — RAW is durable evidence

RAW is represented through artifact/provenance contracts rather than mutable runtime data.

### PIK-API-INV-06 — Stores preserve separate semantic roles

ArtifactStore, DatasetVersionStore and Target/Publisher remain distinct contracts.

### PIK-API-INV-07 — Decode is not transform

Decoder APIs do not become generic relational transformation APIs.

### PIK-API-INV-08 — DatasetVersion is immutable governed identity

Current/latest publication pointers remain separate.

### PIK-API-INV-09 — Publication preserves uncertainty

UNKNOWN_OUTCOME cannot be flattened into ordinary failure or automatic retry.

### PIK-API-INV-10 — Replay is explicit

Replay creates a new run from preserved evidence and remains distinguishable from reacquisition.

### PIK-API-INV-11 — Sibling integration is optional

PyIngestKit core remains usable without PyTransformKit or PyWorkflowKit installed.

### PIK-API-INV-12 — Stable API is machine-checkable

Exports, protocols, enums, IDs, extras and wire contracts are continuously protected in CI.

---

# 102. Canonical API surface summary

~~~text
AUTHORING
    Source
    IngestionDefinition
    validation / RAW / publication policies

ACQUISITION
    SourceConnector
    SourceRegistry
    AcquisitionResult

REPRESENTATION
    Decoder
    DecoderRegistry
    DecodeResult
    ValidationResult

EVIDENCE
    ArtifactReference
    ArtifactStore
    provenance / manifest

GOVERNED DATA
    DatasetVersion
    DatasetVersionReference
    DatasetVersionStore
    PublishedDataset

PUBLICATION
    Target / Publisher
    PublicationPolicy
    PublicationResult
    reconciliation

RUNTIME
    IngestionRuntime
    IngestionRunId
    IngestionRun
    IngestionResult
    replay

PORTABLE BOUNDARIES
    ResourceReference
    CorrelationContext
    FailureEvidence
    CredentialReference
    IdempotencyReference
    explicit codecs

OPTIONAL INTEGRATION
    pyingestkit.integrations.pytransformkit
~~~

---

# 103. Final API statement

PyIngestKit 2.0 exposes one coherent progression from source intent to governed dataset evidence:

~~~text
Source
    ↓
IngestionDefinition
    ↓
IngestionRuntime.run
    ↓
RAW Artifact
    ↓
Decode / Validate
    ↓
DatasetVersion
    ↓
Publish
    ↓
IngestionResult
~~~

> **The stable API makes acquisition explicit, RAW durable, DatasetVersion governed, publication deliberate, replay traceable and sibling integration optional.**

This specification is the normative baseline for:

~~~text
PYINGESTKIT_V2_IMPLEMENTATION_ROADMAP.md
~~~
