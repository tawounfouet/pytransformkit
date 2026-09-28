# PyKit Ecosystem V2 — End-to-End Acceptance Criteria

> **Status:** NORMATIVE ECOSYSTEM ACCEPTANCE BASELINE  
> **Architecture generation:** V2  
> **Date:** 2026-09-28  
> **Scope:** PyTransformKit 1.0, PyIngestKit 2.0, PyWorkflowKit 2.0  
> **Acceptance posture:** release only when architecture, contracts, runtime semantics and integration evidence are jointly green  
> **Depends on:** PYKIT_ECOSYSTEM_V2_ARCHITECTURE_AND_CANONICAL_VOCABULARY.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_PUBLIC_API_DESIGN_PRINCIPLES.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_SHARED_CONTRACTS_AND_REFERENCE_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_EXECUTION_IDENTITY_AND_CORRELATION_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_ERROR_FAILURE_RETRY_AND_UNCERTAINTY_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_DATASET_RESOURCE_AND_ARTIFACT_INTEROPERABILITY.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_LINEAGE_PROVENANCE_AND_TRACEABILITY_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_OBSERVABILITY_EVENTS_AND_TELEMETRY_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_INTEGRATION_AND_ANTI_CORRUPTION_LAYER_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_DEPENDENCY_PACKAGING_AND_OPTIONAL_EXTRAS_STRATEGY.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_SERIALIZATION_AND_WIRE_CONTRACTS.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_ARCHITECTURE_CONFORMANCE_AND_TEST_STRATEGY.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_SECURITY_AND_TRUST_BOUNDARIES.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_REFERENCE_APPLICATION_SPEC.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_RELEASE_COMPATIBILITY_AND_VERSIONING_POLICY.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_IMPLEMENTATION_SEQUENCE_AND_MIGRATION_PLAN.md

---

# 1. Purpose

This document defines the final end-to-end acceptance criteria for the PyKit V2 ecosystem.

It answers one question:

> **What must be demonstrably true before the ecosystem can be considered architecturally coherent, integration-ready and release-qualified?**

The governing principle is:

> **A package is not accepted because its unit tests pass; the ecosystem is accepted when ownership, contracts, runtime behavior, failure semantics, interoperability, security and release evidence all compose correctly.**

---

# 2. Acceptance scope

Acceptance applies across:

~~~text
PyTransformKit 1.0
PyIngestKit 2.0
PyWorkflowKit 2.0
Customer 360 reference application
cross-framework contracts
package and integration matrices
historical migration paths
release artifacts
~~~

No single repository can independently prove full ecosystem acceptance.

---

# 3. Acceptance is cumulative

The final V2 acceptance gate aggregates evidence from all normative specifications.

A release is not accepted if any critical architecture family is red.

The primary families include:

~~~text
ARCHITECTURE
PUBLIC API
IDENTITY
FAILURE / RETRY / UNCERTAINTY
DATA / RESOURCE / ARTIFACT
LINEAGE / PROVENANCE
OBSERVABILITY
INTEGRATION / ACL
PACKAGING
SERIALIZATION
SECURITY
REFERENCE APPLICATION
RELEASE / COMPATIBILITY
MIGRATION
~~~

---

# 4. Acceptance levels

The ecosystem distinguishes four acceptance levels:

~~~text
LEVEL 1 — PACKAGE READY
    one framework satisfies its own stable contract

LEVEL 2 — INTEGRATION READY
    official sibling adapters satisfy producer-consumer contracts

LEVEL 3 — ECOSYSTEM READY
    Customer 360 and full cross-framework conformance are green

LEVEL 4 — RELEASE READY
    built artifacts, compatibility matrices, migration and release evidence are green
~~~

A package may be Level 1 before the ecosystem reaches Level 4.

---

# 5. No paper acceptance

Documentation alone is insufficient.

Every critical criterion MUST have one or more of:

~~~text
automated test
golden fixture
architecture check
installed-artifact smoke
fault-injection scenario
migration fixture
reference-application scenario
release qualification report
~~~

Unverified prose is not release evidence.

---

# 6. Gate A — Public model acceptance

Before ecosystem stabilization:

1. every public root type has independent purpose;
2. artificial cross-framework symmetry has been removed;
3. public versus internal graph representations are explicit;
4. package-root exports are curated;
5. no public abstraction exists only because another framework has a similarly named abstraction.

Special review remains required for:

~~~text
IngestionLifecycle
IngestionPlan
TransformationGraph
OptimizedLogicalPlan
WorkflowGraph
DependencyGraph as public API
~~~

If their independent semantics cannot be proven, they remain internal or are removed.

---

# 7. Gate B — Dependency architecture acceptance

The package graph MUST remain:

~~~text
PyWorkflowKit
    ├── optional → PyIngestKit
    └── optional → PyTransformKit

PyIngestKit
    └── optional → PyTransformKit

PyTransformKit
    └── no sibling dependency
~~~

Acceptance requires:

- no sibling import cycle;
- no hidden reverse dependency;
- no shared package that reintroduces a cycle;
- core packages independently importable;
- optional integration extras remain optional.

---

# 8. Gate C — Core package independence

The following clean environments MUST pass:

~~~text
PyTransformKit core only
PyIngestKit core only
PyWorkflowKit core only
~~~

Each environment must prove:

- package import;
- core smoke behavior;
- no accidental sibling dependency;
- no optional backend required for unrelated features;
- no import-time network or plugin side effect.

---

# 9. Gate D — Public API acceptance

Each stable package MUST have executable protection for:

~~~text
root exports
constructors
public functions
Protocol members
exception hierarchy
enum values
stable extras
stable plugin entry points
stable CLI surface when declared
~~~

Unexpected drift in a stable surface fails release qualification.

---

# 10. Gate E — Shared contract acceptance

The following portable contract families MUST be implemented and fixture-tested where required by current integrations:

~~~text
ResourceReference
ArtifactReference
DatasetReference
DatasetVersionReference
ExecutionReference
IngestionExecutionReference
TransformationExecutionReference
WorkflowExecutionReference
ExternalRunRef
CorrelationContext
FailureEvidence
IdempotencyReference
CredentialReference
~~~

Each stable contract must define:

- contract identity;
- contract version;
- required fields;
- optional fields;
- validation;
- canonical serialization behavior;
- redaction rules;
- round-trip tests.

---

# 11. Gate F — Contract interoperability

At least the following producer-consumer flows MUST pass using real serialized fixtures:

~~~text
PyIngestKit
    DatasetVersionReference
        ↓
PyTransformKit integration

PyTransformKit
    TransformationExecutionReference
        ↓
PyWorkflowKit integration

PyIngestKit
    IngestionExecutionReference
        ↓
PyWorkflowKit integration

CorrelationContext
    ↓
all three frameworks
~~~

Consumers MUST NOT require private provider objects.

---

# 12. Gate G — Execution identity acceptance

The ecosystem MUST preserve distinct native IDs:

~~~text
WorkflowRunId
TaskRunId
TaskAttemptId
IngestionRunId
TransformationExecutionId
~~~

Acceptance requires:

- no universal run ID;
- retry creates new TaskAttemptId;
- recovery preserves the existing execution identity;
- replay creates a new ingestion execution identity;
- sibling child executions receive their own native IDs;
- CorrelationId connects related work without replacing native identity.

---

# 13. Gate H — Correlation and causation acceptance

Cross-framework execution MUST prove:

~~~text
same CorrelationId
    across one broader business operation

explicit causation
    only where direct parent-child execution exists
~~~

The suite MUST reject fabricated causation based only on shared correlation.

TraceId remains observational and MUST NOT replace durable execution identity.

---

# 14. Gate I — Failure semantics acceptance

Every framework MUST map representative failures into structured semantics covering:

~~~text
category
error code
retryability
uncertainty
native execution reference
correlation
safe diagnostic summary
~~~

Raw exception text MUST NOT be the semantic contract.

---

# 15. Gate J — Retry ownership acceptance

The ecosystem MUST prove:

~~~text
PyWorkflowKit
    owns workload retry

PyIngestKit
    owns bounded ingestion-internal retry

PyTransformKit
    owns bounded engine/provider retry
~~~

Acceptance fails if equivalent retry scope is hidden at multiple layers.

---

# 16. Gate K — Retry amplification acceptance

At least one cross-framework scenario MUST count effective provider attempts.

The result must match the declared nested retry budget.

Undocumented SDK or driver retries that exceed the accepted amplification model fail conformance.

---

# 17. Gate L — UNKNOWN_OUTCOME acceptance

At least one side-effecting operation MUST simulate:

~~~text
request sent
    ↓
provider may have committed
    ↓
acknowledgement lost
    ↓
UNKNOWN_OUTCOME
~~~

Acceptance requires:

- no blind retry;
- reconciliation attempted where supported;
- final result distinguishes confirmed success, confirmed failure and still unknown;
- uncertainty survives every adapter boundary.

---

# 18. Gate M — Recovery acceptance

A process-loss scenario MUST prove:

~~~text
persist state
    ↓
lose process memory
    ↓
restart
    ↓
load existing identities
    ↓
reuse ExternalRunRef
    ↓
inspect or reconcile
    ↓
resume without duplicate external work where possible
~~~

Recovery MUST NOT be implemented as unconditional rerun.

---

# 19. Gate N — Cancellation acceptance

The ecosystem MUST distinguish:

~~~text
cancellation requested
cancel confirmed
cancellation unsupported
cancellation unconfirmed
provider completed despite cancellation request
~~~

A cancellation request alone MUST NOT be mapped to confirmed cancellation.

---

# 20. Gate O — PyTransformKit domain acceptance

PyTransformKit MUST prove:

~~~text
Dataset is logical
Expression AST is engine-neutral
LogicalSchema is engine-neutral
TransformationPlan owns logical transformation intent
domain imports no engine-native library
constructors perform no I/O
~~~

No Pandas, Polars, Arrow or DuckDB native object may define logical domain identity.

---

# 21. Gate P — PyTransformKit semantic acceptance

The stable transformation core SHOULD prove at least:

~~~text
projection
filter
derive
cast
sort
deduplicate
join
aggregate
window
targeted reshape as declared
~~~

Unsupported operations fail explicitly.

The semantic model, not total operator count, is the acceptance target.

---

# 22. Gate Q — Cross-engine acceptance

At least Pandas and Polars MUST produce equivalent normalized logical results for the Customer 360 transformation when both advertise required capabilities.

Acceptance compares:

~~~text
logical values
logical schema
null semantics
declared ordering semantics
field lineage
~~~

Native object equality is not required.

---

# 23. Gate R — No hidden engine fallback

If the selected engine lacks a required capability:

~~~text
explicit unsupported capability
~~~

must be emitted unless fallback was deliberately configured.

Silent engine switching fails acceptance.

---

# 24. Gate S — PyIngestKit lifecycle acceptance

PyIngestKit V2 MUST prove the semantic lifecycle:

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

Each phase must retain its own evidence and failure semantics.

---

# 25. Gate T — RAW acceptance

RAW MUST prove:

- immutability where promised;
- checksum/integrity evidence;
- source provenance;
- portable ArtifactReference;
- replay eligibility;
- explicit retention/security posture.

Business transformation MUST NOT mutate RAW.

---

# 26. Gate U — Decode versus transform acceptance

The ecosystem MUST preserve:

~~~text
DECODE != TRANSFORM
~~~

PyIngestKit may parse and coerce source representation into declared typed records.

Relational business transformation remains in PyTransformKit or application logic.

---

# 27. Gate V — DatasetVersion acceptance

DatasetVersion MUST remain distinct from:

~~~text
Logical Dataset
Artifact
Resource
PhysicalHandle
PublishedDataset pointer
latest/current alias
~~~

A concrete DatasetVersionReference MUST remain reproducible and portable according to its declared scope.

---

# 28. Gate W — Write versus publish acceptance

The ecosystem MUST demonstrate:

~~~text
physical transformation write
    !=
governed publication
~~~

A PyTransformKit output does not become a DatasetVersion until PyIngestKit publication creates governed version identity.

---

# 29. Gate X — Replay acceptance

PyIngestKit replay MUST:

- consume preserved RAW or equivalent durable source evidence;
- create a new IngestionRunId;
- preserve replay provenance;
- not masquerade as original acquisition;
- remain distinct from workflow retry and recovery.

---

# 30. Gate Y — PyWorkflowKit DAG acceptance

WorkflowKit MUST prove:

~~~text
cycle detection
unknown dependency rejection
deterministic topological planning
conditional readiness
skip semantics
fail-fast
independent branch execution
~~~

WorkflowKit owns workload dependency semantics only.

---

# 31. Gate Z — Workflow state-machine acceptance

WorkflowRun, TaskRun and TaskAttempt MUST have explicit valid and invalid transition tests.

Terminal-state protection, retry, timeout, cancellation, recovery and reconciliation transitions must be covered.

---

# 32. Gate AA — Sibling workload opacity

WorkflowKit MUST treat sibling runtimes as workloads.

It MUST NOT introspect and independently schedule:

~~~text
PyIngestKit internal acquisition/decode/version stages
PyTransformKit internal transformation nodes
~~~

Sibling internals are opaque beyond public contracts.

---

# 33. Gate AB — Data handoff acceptance

Canonical input handoff MUST work:

~~~text
PyIngestKit
    ↓
DatasetVersionReference
    ↓
PyTransformKit anti-corruption layer
    ↓
InputBinding
~~~

No private persistence entity, DataFrame or provider session may cross the durable boundary.

---

# 34. Gate AC — Transform-to-publication acceptance

Canonical output handoff MUST work:

~~~text
PyTransformKit
    ↓
TransformationResult
    ↓
ResourceReference
    ↓
PyIngestKit publication
    ↓
DatasetVersionReference
~~~

TransformationExecutionReference MUST remain available in provenance.

---

# 35. Gate AD — Lineage acceptance

The ecosystem MUST preserve framework-owned lineage:

~~~text
PyIngestKit
    source / RAW / artifact / DatasetVersion provenance

PyTransformKit
    logical dataset / transformation / field lineage

PyWorkflowKit
    WorkflowRun / TaskRun / TaskAttempt / ExternalRunRef lineage
~~~

No framework may rewrite another framework's lineage as its own.

---

# 36. Gate AE — End-to-end lineage traversal

For Customer 360, acceptance requires the ability to answer:

> Which source artifacts, DatasetVersions, transformation execution and workflow attempts produced a given customer_mart DatasetVersion?

The answer may be composed from multiple owned lineage stores or records.

A universal lineage service is not required.

---

# 37. Gate AF — Field lineage acceptance

At minimum, Customer 360 MUST preserve lineage for:

~~~text
customer_id
email
country
paid_order_count
paid_revenue
first_order_at
last_order_at
has_paid_order
~~~

The suite must distinguish:

~~~text
value derivation
row-selection dependency
grouping dependency
join dependency
ordering dependency
~~~

---

# 38. Gate AG — Lineage confidence acceptance

Opaque operations MUST NOT claim exact lineage without evidence.

The model SHOULD distinguish confidence such as:

~~~text
EXACT
DECLARED
INFERRED
PARTIAL
UNKNOWN
~~~

where applicable.

---

# 39. Gate AH — Observability acceptance

The ecosystem MUST prove structured evidence for:

~~~text
events
logs
metrics
traces
diagnostics
manifests
~~~

without making any observability backend mandatory for core correctness.

---

# 40. Gate AI — Event identity acceptance

EventId MUST remain distinct from execution identity.

Event namespaces must identify the framework that owns the emitted event.

Cross-framework consumers may aggregate events without changing ownership.

---

# 41. Gate AJ — Metrics acceptance

Default metrics MUST avoid unbounded high-cardinality labels such as:

~~~text
run IDs
attempt IDs
correlation IDs
full URIs
raw SQL
exception messages
~~~

Metric names, units and stable label semantics must be documented when declared public.

---

# 42. Gate AK — Trace acceptance

TraceId and SpanId MAY connect runtime observations.

They MUST NOT become durable domain identity.

Loss of an observability backend MUST NOT invalidate domain state or cause business replay.

---

# 43. Gate AL — Telemetry failure isolation

At least one test MUST simulate telemetry exporter failure.

Acceptance requires:

- business execution continues or fails only according to explicit telemetry policy;
- no recursive telemetry failure loop;
- no duplicate business execution caused by telemetry failure.

---

# 44. Gate AM — Serialization acceptance

Stable durable contracts MUST:

- declare contract ID;
- declare contract version;
- use safe schema-driven decoding;
- reject malformed required semantics;
- tolerate supported additive optional fields;
- round-trip semantically;
- remain free of active resources.

---

# 45. Gate AN — No executable serialization

Durable boundaries MUST NOT depend on:

~~~text
pickle
cloudpickle
dill
eval
exec
arbitrary class/module reconstruction
~~~

A wire payload must not select arbitrary executable code.

---

# 46. Gate AO — Golden fixture acceptance

Stable cross-framework contracts MUST have versioned golden fixtures.

Fixtures must cover:

- minimal valid form;
- full form;
- invalid required field;
- unsupported version;
- unknown optional field where supported;
- redaction/security case;
- migration case where relevant.

---

# 47. Gate AP — Migration acceptance

Every supported wire or state migration MUST be deterministic and tested.

Migration MUST NOT silently discard:

~~~text
identity
uncertainty
idempotency scope
ownership
security semantics
~~~

Unsupported legacy state fails explicitly.

---

# 48. Gate AQ — Security acceptance

Security conformance MUST prove:

~~~text
identity != authorization
references are not bearer authority by default
secrets are referenced, not serialized
plugins require explicit activation
deserialization is non-executable
resource targets are validated
subprocess shell use is explicit
telemetry is redacted
security-sensitive ambiguity fails closed
~~~

---

# 49. Gate AR — Credential acceptance

No real secret value may appear in:

~~~text
public references
golden fixtures
manifests
lineage
FailureEvidence
metric labels
logs
trace baggage
repository test data
~~~

Synthetic test credentials are allowed.

---

# 50. Gate AS — Plugin acceptance

Plugin tests MUST prove:

~~~text
not installed
    core still works

installed but not activated
    no side effects

compatible and explicitly activated
    capability works

incompatible
    rejected clearly

named only by untrusted payload
    not auto-loaded
~~~

---

# 51. Gate AT — Subprocess acceptance

If subprocess execution is supported, the implementation MUST distinguish:

~~~text
argument-vector execution
shell execution
~~~

Environment forwarding must be controllable.

stdout/stderr capture must be bounded and redacted.

A subprocess MUST NOT be documented as a full sandbox.

---

# 52. Gate AU — Packaging acceptance

For each stable package, release CI MUST prove:

~~~text
build wheel
install wheel in clean environment
import package
run installed smoke
install supported extras
run extra smoke
inspect metadata
~~~

If an sdist is published, it must also be installed and tested.

---

# 53. Gate AV — Supported Python acceptance

Every declared supported Python minor must run required package-local gates before stable release.

A Python version not tested in release qualification must not be presented as fully supported.

---

# 54. Gate AW — Dependency range acceptance

Declared dependency ranges MUST have evidence at:

~~~text
minimum supported version
latest compatible version
~~~

Official sibling compatibility additionally requires contract-version tests.

---

# 55. Gate AX — Optional dependency acceptance

For every published optional extra:

~~~text
dependency absent
    unrelated core behavior still works

dependency installed
    feature smoke/conformance passes
~~~

Optional must mean optional in installation, import and activation.

---

# 56. Gate AY — Release candidate acceptance

An RC MUST be treated as the intended stable contract.

Before RC publication:

- public API snapshots are current;
- stable wire schemas are frozen;
- compatibility matrix is declared;
- package metadata is release-like;
- built artifacts are qualified.

Breaking RC corrections require a new RC and full requalification.

---

# 57. Gate AZ — Release evidence acceptance

A stable release MUST be able to report:

~~~text
package/version
commit
artifact hashes
Python versions tested
dependency ranges tested
sibling ranges tested
wire contract versions
public API baseline
Customer 360 scenarios
migration status
known limitations
~~~

This evidence may be Markdown, JSON or another auditable representation.

---

# 58. Gate BA — Customer 360 happy path

The canonical happy path MUST pass:

~~~text
customers source
    ↓
PyIngestKit
    ↓
customers DatasetVersion

orders source
    ↓
PyIngestKit
    ↓
orders DatasetVersion

both versions
    ↓
PyTransformKit
    ↓
customer_mart Resource

resource
    ↓
PyIngestKit publication
    ↓
customer_mart DatasetVersion
~~~

PyWorkflowKit coordinates the workload DAG.

---

# 59. Gate BB — Customer 360 engine parity

The same TransformationPlan MUST execute successfully on at least Pandas and Polars for the declared reference capability set.

The normalized logical result and lineage must agree.

---

# 60. Gate BC — Customer 360 failure path

At least one controlled failure MUST prove:

- structured FailureEvidence;
- correct framework ownership;
- correct TaskAttempt outcome;
- no hidden retry duplication;
- observable correlation.

---

# 61. Gate BD — Customer 360 uncertainty path

The publication uncertainty scenario MUST prove:

~~~text
UNKNOWN_OUTCOME
    ↓
reconciliation
    ↓
no blind duplicate publication
~~~

---

# 62. Gate BE — Customer 360 recovery path

A restart scenario MUST prove:

~~~text
WorkflowRun persisted
ExternalRunRef persisted
process restarted
existing external work inspected/reconciled
no duplicate work where avoidable
~~~

---

# 63. Gate BF — Customer 360 serialization path

The reference application MUST persist and re-read at least:

~~~text
DatasetVersionReference
TransformationExecutionReference
ExternalRunRef
CorrelationContext
FailureEvidence
EventEnvelope
LineageRecord or equivalent lineage evidence
execution manifest
~~~

through supported stable wire contracts.

---

# 64. Gate BG — Customer 360 security path

The reference application MUST demonstrate negative cases including:

~~~text
credential-bearing locator rejected or redacted
path traversal rejected
unknown plugin not activated
wire payload cannot activate code
secret absent from logs/manifests
~~~

---

# 65. Gate BH — Customer 360 built-artifact path

At least one CI job MUST run Customer 360 against built installed artifacts rather than editable source trees.

This proves real package composition.

---

# 66. Gate BI — V1-to-V2 migration readiness

Before calling PyIngestKit 2.0 or PyWorkflowKit 2.0 migration-ready:

- semantic mapping from V1 concepts exists;
- intentionally removed concepts are documented;
- compatibility aliases are not required by default;
- persisted-state migration strategy is documented;
- unsupported direct migrations are explicit;
- applications may pin V1 during transition.

---

# 67. Gate BJ — Migration artifact acceptance

Where direct V1 private-store migration would create permanent coupling, acceptance permits:

~~~text
V1 semantic export
    ↓
versioned migration representation
    ↓
V2 importer
~~~

This path must be documented and tested with fixtures.

---

# 68. Gate BK — Documentation acceptance

Stable releases MUST have current documentation for:

~~~text
installation
Getting Started
public API
supported extras
integration setup
wire contracts
failure/retry semantics
migration
security assumptions
Customer 360
compatibility ranges
~~~

Official examples should execute where practical.

---

# 69. Gate BL — No undocumented stable behavior

A behavior relied upon by the reference application and declared stable MUST be represented in public documentation or normative specification.

Release acceptance fails if essential behavior exists only as tribal knowledge in tests or implementation.

---

# 70. Gate BM — No unresolved critical TODO

Stable release acceptance requires no unresolved critical item concerning:

~~~text
identity semantics
retry ownership
unknown outcome
publication semantics
wire compatibility
security boundary
migration safety
public API ambiguity
dependency cycles
~~~

Non-critical deferred features may remain explicitly out of scope.

---

# 71. Gate BN — No architecture contradiction

If two normative specifications conflict materially, stable acceptance is blocked until the contradiction is resolved.

Implementation MUST NOT choose one silently.

The resolution process is:

~~~text
identify conflict
    ↓
architecture decision
    ↓
update normative documents
    ↓
update invariants/tests
    ↓
resume qualification
~~~

---

# 72. Gate BO — Invariant coverage

Every critical invariant family SHOULD have a mapping to test evidence.

At minimum, release qualification must account for:

~~~text
ID-INV
FAIL-INV
DATA-INV
LIN-INV
OBS-INV
INT-INV
PKG-INV
WIRE-INV
TEST-INV
SEC-INV
REF-INV
REL-INV
IMPL-INV
E2E-INV
~~~

---

# 73. Gate BP — No skipped critical conformance

A critical required scenario that is skipped because of flakiness, missing environment or unavailable credentials does not count as passing.

For release qualification, every mandatory scenario must either:

- execute successfully;
- or be explicitly removed from the declared support scope before release.

---

# 74. Gate BQ — Release-blocking classes

The following failures are release-blocking:

~~~text
forbidden package dependency
private cross-framework coupling
identity collapse
hidden whole-workload retry
blind retry after unknown side effect
unreadable stable wire fixture
secret leakage
unsafe executable deserialization
Customer 360 reference failure
built wheel import failure
unsupported published compatibility claim
~~~

---

# 75. Gate BR — Non-blocking deferred scope

The following MAY remain deferred if not declared stable:

~~~text
additional cloud providers
distributed scheduler
web UI
large plugin catalog
every transformation operator
every storage backend
advanced performance optimization
control plane
~~~

Deferred scope must not invalidate current stable contracts.

---

# 76. Release decision model

The ecosystem release decision is:

~~~text
Are all critical architecture gates green?
    ├── NO → not accepted
    └── YES
          ↓
Are integration and Customer 360 gates green?
    ├── NO → not accepted
    └── YES
          ↓
Are packaging, security, compatibility and migration gates green?
    ├── NO → not release-ready
    └── YES
          ↓
Release accepted
~~~

---

# 77. Framework-level release acceptance

PyTransformKit 1.0 may be accepted independently when its package-local and downstream-required contract gates are green.

PyIngestKit 2.0 acceptance additionally depends on the qualified PyTransformKit integration range it declares.

PyWorkflowKit 2.0 acceptance additionally depends on qualified sibling workload integrations it declares.

The ecosystem-wide V2 acceptance requires all three stable lines plus Customer 360.

---

# 78. PyTransformKit 1.0 minimum acceptance

PyTransformKit 1.0 MUST have:

- rationalized public model;
- curated root API;
- engine-neutral domain;
- Pandas and Polars conformance;
- stable transformation runtime identity;
- stable failure semantics;
- stable I/O boundary that does not absorb ingestion;
- stable serialization for declared durable contracts;
- package/extras qualification;
- Customer 360 transformation path green.

---

# 79. PyIngestKit 2.0 minimum acceptance

PyIngestKit 2.0 MUST have:

- clean-slate public model;
- explicit Source → RAW → Decode → Version → Publish lifecycle;
- DatasetVersion semantics;
- publication and replay;
- provenance;
- structured failures;
- portable references;
- transform integration when declared;
- wire fixtures;
- package/extras qualification;
- Customer 360 ingestion/publication paths green.

---

# 80. PyWorkflowKit 2.0 minimum acceptance

PyWorkflowKit 2.0 MUST have:

- WorkflowDefinition and ExecutionPlan semantics;
- WorkflowRun, TaskRun and TaskAttempt state machines;
- local executor;
- workload retry;
- timeout/cancellation;
- durable metadata;
- ExternalRunRef;
- recovery/reconciliation;
- sibling adapters when declared;
- wire/manifests;
- package qualification;
- Customer 360 workflow/recovery paths green.

---

# 81. Ecosystem release manifest

A final release qualification artifact SHOULD summarize:

~~~text
ecosystem architecture generation
framework versions
commit SHAs
artifact hashes
supported Python versions
supported sibling ranges
supported contract versions
acceptance gates
Customer 360 result
migration readiness
security checks
known limitations
release decision
~~~

This becomes the auditable closure record for the V2 release.

---

# 82. Acceptance status vocabulary

Recommended statuses are:

~~~text
NOT_STARTED
IN_PROGRESS
BLOCKED
PASSED
WAIVED
NOT_APPLICABLE
~~~

WAIVED MUST require explicit rationale, owner and review evidence.

A critical invariant should almost never be waived for stable release.

---

# 83. Acceptance evidence ownership

Each gate has a primary owner:

~~~text
framework repository
    package-local semantics

consumer integration repository
    adapter compatibility

Customer 360
    ecosystem composition

release workflow
    artifact qualification and final report
~~~

Evidence ownership should follow semantic ownership.

---

# 84. Acceptance review cadence

During implementation, the acceptance matrix SHOULD be reviewed at major milestones:

~~~text
public-model freeze
PyTransformKit RC
PyIngestKit RC
PyWorkflowKit RC
Customer 360 full pass
final stable qualification
~~~

Acceptance is a living checklist before it becomes a release report.

---

# 85. Acceptance criteria for specification completion

Before framework-specific target architecture documents are frozen, this ecosystem acceptance document is considered complete only if it can evaluate:

- one framework in isolation;
- one sibling integration;
- the full Customer 360 path;
- failure and uncertainty;
- recovery;
- migration;
- security;
- packaging;
- stable release qualification.

---

# 86. Normative invariants

### E2E-INV-01 — Acceptance is ecosystem-level

Passing one repository's tests does not prove ecosystem readiness.

### E2E-INV-02 — Every critical rule has executable evidence

Architecture acceptance is evidence-based.

### E2E-INV-03 — Public boundaries remain portable

Cross-framework interaction uses stable contracts and references.

### E2E-INV-04 — Native ownership remains visible end to end

Identity, lineage, failure and publication ownership are never flattened.

### E2E-INV-05 — Uncertainty survives every layer

UNKNOWN_OUTCOME cannot be converted into ordinary failure or blind retry.

### E2E-INV-06 — Recovery preserves existing work

Restart does not imply rerun.

### E2E-INV-07 — Large data moves by reference

Durable workflow state does not become a hidden DataFrame transport.

### E2E-INV-08 — Security is part of acceptance

Secret leakage, executable deserialization or unauthorized activation blocks release.

### E2E-INV-09 — Built artifacts are the qualification unit

Source checkout success alone is insufficient.

### E2E-INV-10 — Customer 360 is mandatory ecosystem evidence

The reference application proves real composition.

### E2E-INV-11 — Migration readiness is explicit

V1-to-V2 transition paths and unsupported cases are documented and tested.

### E2E-INV-12 — Stable release requires auditable closure

The ecosystem can produce a final qualification record identifying what was tested and accepted.

---

# 87. Canonical end-to-end acceptance map

~~~text
                    ARCHITECTURE
                         │
                         ▼
                  PUBLIC CONTRACTS
                         │
                         ▼
                 PACKAGE CONFORMANCE
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
        PyTransform   PyIngest   PyWorkflow
              │          │          │
              └──────────┼──────────┘
                         ▼
                SIBLING INTEGRATIONS
                         │
                         ▼
                   CUSTOMER 360
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
          FAILURE    RECOVERY    SECURITY
              │          │          │
              └──────────┼──────────┘
                         ▼
                 PACKAGING MATRIX
                         │
                         ▼
               MIGRATION READINESS
                         │
                         ▼
              RELEASE QUALIFICATION
                         │
                         ▼
                    STABLE V2
~~~

---

# 88. Final acceptance statement

PyKit V2 is accepted only when the ecosystem proves all of the following together:

~~~text
clear semantic ownership
portable contracts
independent package boundaries
distinct execution identities
bounded retry ownership
explicit uncertainty
safe recovery
governed publication
composable lineage
backend-neutral transformation
secure serialization
optional integration packaging
Customer 360 execution
migration readiness
qualified release artifacts
~~~

The central rule is:

> **The V2 architecture is accepted when the whole system behaves correctly at its boundaries, not merely when each repository works in isolation.**

This document closes the transverse ecosystem specification layer and becomes the acceptance baseline for:

~~~text
PYTRANSFORMKIT_V1_TARGET_ARCHITECTURE.md
PYINGESTKIT_V2_TARGET_ARCHITECTURE.md
PYWORKFLOWKIT_V2_TARGET_ARCHITECTURE.md

PYTRANSFORMKIT_V1_PUBLIC_API_SPEC.md
PYINGESTKIT_V2_PUBLIC_API_SPEC.md
PYWORKFLOWKIT_V2_PUBLIC_API_SPEC.md

PYTRANSFORMKIT_V1_REVISED_IMPLEMENTATION_ROADMAP.md
PYINGESTKIT_V2_IMPLEMENTATION_ROADMAP.md
PYWORKFLOWKIT_V2_IMPLEMENTATION_ROADMAP.md
~~~
