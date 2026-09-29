# PyIngestKit V2 — Implementation Roadmap

> **Status:** NORMATIVE V2 IMPLEMENTATION ROADMAP  
> **Target release:** PyIngestKit 2.0.0  
> **Date:** 2026-09-29  
> **Architecture generation:** PyKit Ecosystem V2  
> **Migration posture:** clean-slate major release guided by semantic reuse, not legacy class preservation  
> **Depends on:** PYINGESTKIT_V2_TARGET_ARCHITECTURE.md  
> **Depends on:** PYINGESTKIT_V2_PUBLIC_API_SPEC.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_END_TO_END_ACCEPTANCE_CRITERIA.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_IMPLEMENTATION_SEQUENCE_AND_MIGRATION_PLAN.md

---

# 1. Purpose

This document defines the ordered implementation path from the existing PyIngestKit 1.x line to PyIngestKit 2.0.0.

The roadmap is intentionally clean-slate at the public-domain level.

Existing V1 code may be reused only when its behavior already satisfies V2 semantics.

The governing rule is:

> **Reuse proven ingestion behavior; do not preserve legacy Job, Pipeline or Step abstractions merely because they already exist.**

---

# 2. V2 implementation strategy

The V2 implementation proceeds from durable domain semantics outward:

~~~text
domain vocabulary
    ↓
acquisition
    ↓
RAW / Artifact
    ↓
decode / validation
    ↓
DatasetVersion
    ↓
publication
    ↓
reconciliation / replay
    ↓
runtime evidence
    ↓
providers
    ↓
serialization / plugins
    ↓
PyTransformKit integration
    ↓
migration / Customer 360
    ↓
RC
    ↓
2.0.0
~~~

---

# 3. Version milestone strategy

The roadmap uses implementation lots but does not require a package publication for every lot.

Recommended milestones:

| Milestone | Lots | Theme |
|---|---|---|
| 2.0.0a1 | LOT-00 → LOT-05 | Core domain, acquisition, RAW, basic decode |
| 2.0.0a2 | LOT-06 → LOT-08 | Validation, DatasetVersion, governed metadata |
| 2.0.0a3 | LOT-09 → LOT-12 | Publication, uncertainty, replay, runtime |
| 2.0.0b1 | LOT-13 → LOT-16 | Providers, wire contracts, plugins/security |
| 2.0.0b2 | LOT-17 → LOT-20 | PyTransformKit integration, migration, Customer 360 |
| 2.0.0rc1 | LOT-21 | Release candidate |
| 2.0.0 | LOT-22 | Stable |

---

# Phase A — Clean-Slate Domain and Local Reference Path

# 4. LOT-00 — V2 Repository and Architecture Baseline

## Scope

Prepare the V2 line without carrying ambiguous V1 public abstractions forward.

Required work:

~~~text
V2 branch/release line
package metadata review
Python support matrix
src layout
architecture tests
public-root allowlist
forbidden sibling imports
optional dependency policy
V1 inventory
migration evidence inventory
Customer 360 fixture directory
CI baseline
~~~

Explicitly classify V1 components as:

~~~text
REUSE
ADAPT
REWRITE
REMOVE
DEFER
~~~

## Exit criteria

- core imports without PyTransformKit/PyWorkflowKit;
- V2 public root contains no Job/Pipeline/Step compatibility aliases;
- architecture import rules are executable in CI;
- V1 reuse matrix exists;
- clean wheel builds.

---

# 5. LOT-01 — Shared Boundary Values and Execution Identity

## Scope

Implement PyIngestKit-owned or locally mirrored portable boundary values needed before lifecycle work:

~~~text
IngestionRunId
IngestionExecutionReference
CorrelationContext integration
FailureEvidence integration
ResourceReference
ArtifactReference
DatasetReference
DatasetVersionReference skeleton
CredentialReference integration
IdempotencyReference integration
typed status categories
structured Diagnostic
~~~

No mandatory shared-core package is introduced.

## Exit criteria

- values are immutable;
- wire identity/version placeholders exist;
- no raw credentials are serializable;
- IDs are distinct from correlation/trace IDs;
- core-only tests pass.

---

# 6. LOT-02 — Source and IngestionDefinition Domain

## Scope

Implement:

~~~text
Source
Source kinds
Source metadata
IngestionDefinition
RAW policy
validation policy hooks
dataset family identity
publication intent hooks
definition fingerprint
definition validation
root exports
~~~

The common API follows PYINGESTKIT_V2_PUBLIC_API_SPEC.md.

## Exit criteria

- Source is declarative and side-effect free;
- Source != ResourceReference;
- IngestionDefinition is immutable;
- no public IngestionPlan exists;
- serialization rejects obviously non-portable source config;
- root API snapshot passes.

---

# 7. LOT-03 — Acquisition Port and Local File Source

## Scope

Implement the first complete source connector path:

~~~text
SourceConnector Protocol
SourceConnectorDescriptor
AcquisitionRequest
AcquisitionResult
SourceRegistry
file Source
FileSourceConnector
acquisition diagnostics
checksum collection
size/media metadata
bounded file access policy
~~~

## Exit criteria

- acquisition produces structured evidence;
- file paths are validated against configured policy;
- connector registration is explicit;
- source construction performs no I/O;
- local-file connector conformance suite passes.

---

# 8. LOT-04 — RAW, ArtifactReference and FileArtifactStore

## Scope

Implement:

~~~text
RAW domain semantics
Artifact kind
ArtifactReference
ArtifactStore Protocol
PutArtifactRequest / Result
ArtifactReader abstraction
FileArtifactStore
SHA-256 integrity
immutable RAW write policy
retention metadata
manifest linkage
~~~

## Exit criteria

- persisted RAW is immutable according to policy;
- checksum is reproducible;
- ArtifactStore != Target is enforced in API and tests;
- RAW can be reopened from ArtifactReference;
- no business transformation mutates RAW.

---

# 9. LOT-05 — CSV and JSONL Decode Foundation

## Scope

Implement:

~~~text
Decoder Protocol
DecoderDescriptor
DecodeRequest / DecodeResult
DecoderRegistry
CsvDecoder
CsvDecoderConfig
JsonDecoder
NDJSON mode
encoding policy
schema evidence
row-count evidence
decode diagnostics
bounded parser policy
~~~

## Exit criteria

- Decoder does not own relational business transformation;
- CSV/JSONL fixtures decode deterministically;
- malformed inputs yield structured failures;
- parser resource limits are tested;
- runtime representation remains dependency-neutral.

Milestone candidate: 2.0.0a1.

---

# Phase B — Validation and Governed Dataset Versions

# 10. LOT-06 — Validation, Quality and Rejected Records

## Scope

Implement:

~~~text
ValidationPolicy
ValidationRule model
ValidationResult
required field
type compatibility
nullability
allowed values
uniqueness where supported
row-count bounds
schema fingerprint rule
rejected-record policy
FAIL_ALL
QUARANTINE_REJECTS
ALLOW_WITH_THRESHOLD
quality/profile evidence
report Artifact
~~~

## Exit criteria

- silent row dropping is prohibited;
- validation failure differs from runtime/provider failure;
- rejected records are explicit artifacts when retained;
- quality reports do not silently redefine DatasetVersion identity.

---

# 11. LOT-07 — Fingerprints and DatasetVersion Domain

## Scope

Implement and distinguish:

~~~text
artifact checksum
content fingerprint
schema fingerprint
dataset family identity
DatasetVersionId
DatasetVersion
DatasetVersionReference
originating IngestionRun reference
provenance links
optional TransformationExecutionReference
~~~

## Exit criteria

- DatasetVersion != Artifact;
- DatasetVersion identity is immutable;
- concrete version remains distinct from latest/current;
- DatasetVersionReference is portable and fixture-tested;
- changing governed content yields a new version identity.

---

# 12. LOT-08 — DatasetVersionStore and PublishedDataset

## Scope

Implement:

~~~text
DatasetVersionStore Protocol
InMemoryDatasetVersionStore
SQLiteDatasetVersionStore
save/get/list concrete versions
immutability enforcement
PublishedDataset
publication pointer
current/latest explicit lookup
compare-and-swap pointer semantics where supported
metadata schema versioning
~~~

## Exit criteria

- DatasetVersionStore != ArtifactStore;
- concrete version lookup never depends on mutable latest pointer;
- SQLite path supports deterministic local tests;
- concurrent pointer updates are protected;
- migration hooks exist for store schema.

Milestone candidate: 2.0.0a2.

---

# Phase C — Publication, Uncertainty, Replay and Runtime

# 13. LOT-09 — Publication and Target Contracts

## Scope

Implement:

~~~text
Target
Publisher Protocol
PublisherDescriptor
PublisherRegistry
PublicationPolicy
PublicationMode
PublicationRequest
PublicationResult
REGISTER_EXISTING_RESOURCE
MATERIALIZE_AND_REGISTER
CREATE_NEW
FAIL_IF_EXISTS
APPEND_NEW_VERSION
REPLACE_POINTER
local file publisher
~~~

## Boundary rule

Physical write and governed publication remain distinct.

## Exit criteria

- Target != ArtifactStore;
- successful write does not automatically equal publication;
- DatasetVersion creation/provenance linkage is explicit;
- local publication conformance suite passes.

---

# 14. LOT-10 — Idempotency, UNKNOWN_OUTCOME and Reconciliation

## Scope

Implement:

~~~text
idempotency classification
IdempotencyReference propagation
provider operation reference
PublicationReconciliationRequest
PublicationReconciliationResult
UNKNOWN_OUTCOME
conflict/already-exists handling
reconciliation decision model
bounded retry safety
effective retry-attempt evidence
~~~

## Exit criteria

- uncertain side effects are never flattened into FAILED;
- blind retry after uncertain publication is prohibited;
- reconciliation can resolve success/failure/still-unknown;
- provider retry behavior is documented and bounded.

---

# 15. LOT-11 — Replay

## Scope

Implement explicit replay from preserved evidence:

~~~text
ReplayRequest
replay from prior IngestionRun
replay from RAW ArtifactReference
new IngestionRunId
replay provenance
definition compatibility validation
optional publication policy override
replay diagnostics
~~~

## Exit criteria

- replay does not reacquire source by default;
- replay != workflow retry;
- replay always has a new run identity;
- original RAW/evidence origin remains traceable;
- replay tests cover changed decoder/validation policy where allowed.

---

# 16. LOT-12 — IngestionRuntime, IngestionRun and Manifests

## Scope

Assemble the lifecycle into the canonical runtime:

~~~text
IngestionRuntime
IngestionRun
IngestionResult
IngestionStatus
execution context
CorrelationContext
definition fingerprint
stage diagnostics
FailureEvidence
manifest
provenance record
runtime events
metrics/traces hooks
bounded internal retry
reconcile APIs
replay APIs
~~~

Canonical flow:

~~~text
validate definition
    ↓
acquire
    ↓
persist RAW
    ↓
decode
    ↓
validate/profile
    ↓
create DatasetVersion
    ↓
publish
    ↓
persist evidence
    ↓
IngestionResult
~~~

## Exit criteria

- every run gets IngestionRunId;
- runtime supports local file happy path end to end;
- result contains portable DatasetVersionReference;
- telemetry failure cannot replay ingestion;
- manifests contain no secrets;
- runtime requires no WorkflowKit.

Milestone candidate: 2.0.0a3.

---

# Phase D — Provider Breadth and Durable Contracts

# 17. LOT-13 — HTTP, Parquet and Excel Optional Providers

## Scope

Implement optional extras:

~~~text
[http]
[parquet]
[excel]

HTTP SourceConnector
redirect/host/private-network policy
download limits
Parquet decoder
schema evidence
Excel decoder
sheet selection
bounded workbook parsing
~~~

## Exit criteria

- optional dependencies remain isolated;
- HTTP SSRF-related policy tests pass;
- Parquet/Excel core import is optional;
- provider failures map to structured categories.

---

# 18. LOT-14 — PostgreSQL Source, Target and Metadata Adapters

## Scope

Implement explicitly separate PostgreSQL roles:

~~~text
PostgreSQL source connector
PostgreSQL publication target
transaction/COPY capabilities
optional DatasetVersionStore adapter if justified
credential reference handling
connection ownership
idempotency/reconciliation semantics
~~~

## Exit criteria

- source/target/store roles are not collapsed;
- user-owned connection lifecycle is explicit;
- transaction guarantees are honestly declared;
- provider-specific SQL stays infrastructure-private;
- postgres extra installs independently.

---

# 19. LOT-15 — S3-Compatible Object Storage

## Scope

Implement explicitly separate S3-compatible roles:

~~~text
S3 source connector
S3 ArtifactStore
S3 Target/Publisher
object checksum/ETag evidence
multipart behavior
credential references
prefix/object policy
eventual-consistency considerations
unknown outcome/reconciliation
~~~

## Exit criteria

- same bucket backend can implement multiple ports without conflating semantics;
- secrets are absent from references/manifests;
- multipart retry safety is documented;
- MinIO/S3-compatible conformance profile is available.

---

# 20. LOT-16 — Serialization, Plugins and Security Freeze

## Scope

Implement stable codecs for:

~~~text
IngestionDefinition portable subset
ArtifactReference
DatasetVersionReference
IngestionExecutionReference
CorrelationContext
FailureEvidence
manifest
provenance records
replay request/reference
~~~

Also stabilize:

~~~text
PluginRegistry
source/decoder/store/publisher plugin contracts
explicit activation
entry-point groups
wire golden fixtures
payload limits
non-executable deserialization
security negative tests
resource-policy tests
credential redaction
~~~

## Exit criteria

- no pickle/cloudpickle/dill durable path exists;
- plugins are never activated by payload;
- golden fixtures pass;
- base imports remain provider-optional;
- security baseline is green.

Milestone candidate: 2.0.0b1.

---

# Phase E — Transformation Integration and Migration

# 21. LOT-17 — PyTransformKit Integration

## Scope

Implement optional:

~~~text
pyingestkit[transform]
pyingestkit.integrations.pytransformkit
DatasetVersionReference → InputBinding
TransformationResult → publication input
TransformationExecutionReference provenance link
schema/reference translation
FailureEvidence translation
CorrelationContext propagation
~~~

## Exit criteria

- core PyIngestKit imports without PyTransformKit;
- integration uses only public PyTransformKit contracts;
- no DataFrame/private repository object crosses boundary;
- TransformationExecutionReference survives publication provenance;
- Customer 360 source-version handoff works.

---

# 22. LOT-18 — V1 Semantic Migration Toolkit

## Scope

Create explicit migration from the 1.x line:

~~~text
V1 concept inventory
V1 → V2 mapping guide
legacy Job → IngestionDefinition
legacy Step ownership classification
RAW export/import
DatasetVersion export/import where required
PublishedDataset pointer migration
replay migration
V1 metadata semantic export
V2 importer
migration report
compatibility-shim decision log
~~~

## Exit criteria

- migration does not require permanent V2 coupling to arbitrary V1 private tables;
- unsupported direct migrations are explicit;
- lossy conversions are reported;
- identity/provenance uncertainty is not silently discarded;
- no generic Job/Pipeline/Step aliases are needed in V2 core.

---

# 23. LOT-19 — Provider and Port Conformance Matrix

## Scope

Build reusable conformance suites:

~~~text
SourceConnectorConformance
DecoderConformance
ArtifactStoreConformance
DatasetVersionStoreConformance
PublisherConformance
ResourceResolverConformance
wire fixture matrix
optional dependency matrix
provider failure/fault injection
retry amplification checks
~~~

## Exit criteria

- stable providers pass common behavioral contracts;
- capability differences are explicit;
- no provider can claim support solely from Protocol typing;
- clean-install profiles are CI-tested.

---

# 24. LOT-20 — Customer 360 and End-to-End Beta Gate

## Scope

Implement the PyIngestKit portions of Customer 360:

~~~text
customers CSV ingestion
orders CSV ingestion
RAW persistence
DatasetVersion publication for sources
DatasetVersionReference handoff to PyTransformKit
transformation result publication
customer_mart DatasetVersion
provenance traversal
publication UNKNOWN_OUTCOME scenario
reconciliation
replay scenario
security negative scenarios
built-artifact execution
~~~

## Exit criteria

- complete local reference profile is green;
- Customer 360 can answer which source artifacts/versions produced the final version;
- write != publish remains observable;
- integration with PyTransformKit uses portable references only;
- release-blocking ecosystem acceptance gates relevant to PyIngestKit are green.

Milestone candidate: 2.0.0b2.

---

# Phase F — Release Qualification

# 25. LOT-21 — PyIngestKit 2.0 Release Candidate

**Target:** 2.0.0rc1

## Scope

Run full release qualification:

~~~text
public API snapshot
Python matrix
Ruff / format / mypy
unit/property tests
architecture tests
provider conformance
wire golden fixtures
migration fixtures
retry/reconciliation fault injection
security tests
optional-extra isolation
wheel install
sdist install if published
Customer 360
docs/examples
release notes
known limitations
release evidence manifest
~~~

## Exit criteria

- no blocker remains;
- root API and stable Protocols are frozen;
- migration path is documented;
- built artifacts pass;
- RC needs no architectural redesign;
- only blocker fixes are permitted without RC reset.

---

# 26. LOT-22 — PyIngestKit 2.0.0 Stable

**Target:** 2.0.0

## Scope

- fix RC blockers only;
- rerun full matrix;
- finalize wire-contract versions;
- finalize provider compatibility matrix;
- finalize migration guide;
- finalize changelog and release notes;
- tag v2.0.0;
- publish stable artifacts;
- publish auditable qualification report.

## Stable acceptance

PyIngestKit 2.0.0 releases only when:

1. IngestionDefinition is the canonical authoring root;
2. no public IngestionPlan is required;
3. Source and ResourceReference remain distinct;
4. RAW is durable immutable evidence;
5. ArtifactStore, DatasetVersionStore and Target remain semantically distinct;
6. Decode does not become business transformation;
7. DatasetVersion is immutable governed identity;
8. PublishedDataset pointer semantics are explicit;
9. write and publish remain distinct;
10. UNKNOWN_OUTCOME and reconciliation are first-class;
11. replay is explicit and gets a new IngestionRunId;
12. IngestionRuntime and IngestionResult match the public spec;
13. optional providers remain optional;
14. PyTransformKit integration is optional and public-contract based;
15. serialization is versioned and non-executable;
16. plugins require explicit activation;
17. migration from V1 is explicit;
18. Customer 360 ingestion/publication path passes;
19. clean built artifacts install on supported Python versions;
20. no blocker remains.

---

# 27. Final lot count

The V2 roadmap contains:

~~~text
LOT-00 → LOT-22
23 implementation lots
~~~

Milestone grouping:

~~~text
Foundation / a1
    LOT-00 → LOT-05

Governed data / a2
    LOT-06 → LOT-08

Runtime lifecycle / a3
    LOT-09 → LOT-12

Providers + contracts / b1
    LOT-13 → LOT-16

Integration + migration + E2E / b2
    LOT-17 → LOT-20

RC
    LOT-21

Stable
    LOT-22
~~~

---

# 28. Definition of Done for every lot

A lot is DONE only when all applicable conditions hold:

- semantic ownership matches target architecture;
- domain and public API are typed;
- no forbidden sibling dependency is introduced;
- structured failures are used;
- unit tests pass;
- property tests pass where useful;
- port/provider conformance passes;
- security tests pass;
- optional dependency isolation is maintained;
- wire fixtures are updated when relevant;
- Ruff/format/mypy pass;
- package builds;
- installed-wheel smoke passes;
- docs/examples are updated;
- migration impact is recorded;
- acceptance evidence is retained.

---

# 29. Explicit V2 non-goals

The 2.0 roadmap does not add:

~~~text
workflow scheduler
cron service
TaskAttempt runtime
distributed worker platform
generic relational transformation engine
universal DataFrame abstraction
cloud provisioning
enterprise IAM
universal catalog governance
exactly-once claims across all providers
~~~

These are deliberate boundaries, not missing roadmap items.

---

# 30. Final roadmap statement

The V2 implementation path is:

~~~text
declare ingestion intent
        ↓
make acquisition evidence durable
        ↓
separate RAW, Artifact and governed version identity
        ↓
make publication explicit
        ↓
model uncertainty and reconciliation
        ↓
make replay traceable
        ↓
stabilize runtime evidence
        ↓
add providers behind ports
        ↓
add safe wire contracts and plugins
        ↓
integrate PyTransformKit through references
        ↓
migrate V1 semantics
        ↓
prove Customer 360
        ↓
2.0.0
~~~

> **PyIngestKit 2.0 is complete when source material can be acquired, preserved, decoded, governed, published, reconciled and replayed with durable evidence, without absorbing transformation or workflow ownership.**
