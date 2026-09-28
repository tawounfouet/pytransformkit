# PyKit Ecosystem V2 — Implementation Sequence and Migration Plan

> **Status:** NORMATIVE IMPLEMENTATION AND TRANSITION BASELINE  
> **Architecture generation:** V2  
> **Date:** 2026-09-28  
> **Scope:** PyTransformKit 1.0, PyIngestKit 2.0, PyWorkflowKit 2.0  
> **Migration posture:** architecture-first, contract-first, evidence-driven transition  
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

---

# 1. Purpose

This document converts the PyKit V2 architecture into an implementation sequence and migration strategy.

It defines what must be frozen before implementation, which framework moves first, what may be reused from existing repositories, what must be rewritten, how portable contracts are introduced without a mandatory shared core package, how the ecosystem reaches PyTransformKit 1.0, PyIngestKit 2.0 and PyWorkflowKit 2.0, and which gates must be green before stable release.

The governing principle is:

> **Implement semantic foundations before infrastructure, and prove each boundary before building the next layer on top of it.**

---

# 2. Migration philosophy

V2 is not a line-by-line refactor of the existing repositories.

Existing code is treated as:

~~~text
working implementation
historical evidence
provider knowledge
performance evidence
test vectors
migration input
~~~

but the V2 specifications remain the architectural authority.

The central migration rule is:

> **Do not migrate old code into the new architecture; migrate proven semantics into the new architecture.**

---

# 3. Clean-slate posture

PyIngestKit 2.0 and PyWorkflowKit 2.0 are clean-slate major lines.

Legacy Job, Pipeline, Step or similar generic abstractions MUST NOT survive automatically.

A legacy concept survives only when it has a clear V2 semantic owner and remains useful after the new boundaries are applied.

PyTransformKit is still pre-1.0 and should use that freedom to remove accidental complexity before 1.0.0.

---

# 4. Canonical implementation order

~~~text
PHASE 0
    public model rationalization

PHASE 1
    portable boundary contracts

PHASE 2
    PyTransformKit 1.0 target

PHASE 3
    PyIngestKit 2.0 core

PHASE 4
    PyIngestKit → PyTransformKit integration

PHASE 5
    PyWorkflowKit 2.0 core

PHASE 6
    PyWorkflowKit → sibling integrations

PHASE 7
    Customer 360 reference application

PHASE 8
    ecosystem conformance matrix

PHASE 9
    stable release qualification
~~~

Dependency direction governs this sequence.

---

# 5. Why PyTransformKit first

PyTransformKit is the lowest-level sibling.

It depends on neither PyIngestKit nor PyWorkflowKit.

Higher layers consume its transformation model, runtime results and references.

Stabilizing it first reduces downstream contract churn.

---

# 6. Why PyIngestKit second

PyIngestKit optionally composes with PyTransformKit.

It owns source acquisition, RAW, DatasetVersion, publication and replay.

Implementing it after the lower-level transformation contracts exist allows the integration to target real public APIs rather than placeholders.

---

# 7. Why PyWorkflowKit third

PyWorkflowKit optionally composes with both siblings.

Its workload adapters should be designed against concrete IngestionResult and TransformationResult contracts.

WorkflowKit therefore freezes after its providers expose usable public runtime boundaries.

---

# 8. Phase 0 — Public model rationalization

Before stable implementation continues, every proposed public architecture type MUST answer:

1. What invariant does it own?
2. What lifecycle does it own?
3. What public behavior does it own?
4. Can it be tested independently?
5. Does it serialize or compile independently?
6. Does it reduce ambiguity?

If the answers are weak, the type remains internal or is removed.

---

# 9. Phase 0 review targets

The following names require explicit justification before stabilization:

~~~text
IngestionLifecycle
IngestionPlan
TransformationGraph
OptimizedLogicalPlan
WorkflowGraph
DependencyGraph as public API
~~~

Cross-framework naming symmetry is not a sufficient reason for a public type.

---

# 10. Preferred lean model

The default target is:

~~~text
PyIngestKit

IngestionDefinition
    ↓
validated or internal compiled representation when needed
    ↓
IngestionRun


PyTransformKit

TransformationPlan
    ↓
LogicalPlan
    ↓
PhysicalPlan when required
    ↓
TransformationExecution


PyWorkflowKit

WorkflowDefinition
    ↓
ExecutionPlan
    ↓
WorkflowRun
~~~

Additional public layers are allowed only when implementation evidence proves independent semantics.

---

# 11. Phase 0 exit gate

Phase 0 closes when:

- package-root target exports are listed;
- every public architecture type has independent purpose;
- internal versus public graphs are explicit;
- artificial symmetry has been removed;
- Customer 360 can be described without private or questionable types;
- no implementation lot depends on unresolved public layering.

---

# 12. Phase 1 — Portable boundary contracts

The first executable cross-framework artifacts are the portable contracts.

Priority contracts include:

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

Each stable contract SHOULD have immutable representation, validation, contract ID, contract version, wire schema, golden fixtures, round-trip tests and redaction behavior.

---

# 13. No mandatory shared package in Phase 1

Phase 1 MUST NOT introduce a mandatory PyKit common package.

Equivalent contract implementations may temporarily exist in multiple repositories.

A shared contracts package is considered only after repeated stable implementation proves:

- identical semantics;
- stable schemas;
- real duplication cost;
- no dependency cycle;
- domain neutrality.

Specification sharing precedes code sharing.

---

# 14. Contract interoperability gate

Producer and consumer fixtures are the compatibility anchor.

Example:

~~~text
PyIngestKit
    writes DatasetVersionReference v1
        ↓
serialized golden fixture
        ↓
PyTransformKit integration
    reads DatasetVersionReference v1
~~~

Consumer tests must not require private provider constructors.

---

# 15. Phase 2 — PyTransformKit 1.0

PyTransformKit is stabilized before downstream V2 integrations freeze.

Recommended sequence:

~~~text
domain cleanup
    ↓
public vocabulary cleanup
    ↓
relational semantic completeness
    ↓
runtime contracts
    ↓
engine conformance
    ↓
I/O boundary
    ↓
serialization
    ↓
extension points
    ↓
1.0 release candidate
~~~

---

# 16. Existing LOT-11 to LOT-28 roadmap

The current PyTransformKit LOT-11 to LOT-28 roadmap remains a useful technical backlog.

It MUST be revalidated against V2 before the 1.0 freeze.

Where an old lot conflicts with V2 semantic ownership, dependency direction, retry rules, serialization or security boundaries, V2 takes precedence.

The old roadmap may retain its numbering while individual lots are revised.

---

# 17. PyTransformKit roadmap remapping

The remaining backlog can be grouped as:

~~~text
RELATIONAL CORE
    joins
    aggregation
    windows
    reshape
    temporal and nested semantics

SEMANTIC QUALITY
    data quality
    lineage
    observability

RUNTIME AND ENGINES
    PyArrow
    DuckDB and SQL
    I/O
    serialization
    optimizer
    plugins

QUALIFICATION
    cross-engine conformance
    performance
    API/docs/security
    release candidate
    1.0
~~~

---

# 18. PyTransformKit domain gate

Before infrastructure expansion, the framework MUST prove:

~~~text
Dataset is logical
TransformationPlan is logical
Expression AST is engine-neutral
LogicalSchema is engine-neutral
domain imports no Pandas/Polars/PyArrow/DuckDB
constructors perform no I/O
~~~

---

# 19. PyTransformKit API gate

Before 1.0 RC:

- package-root exports are curated;
- provisional exports are explicitly identified;
- obsolete aliases are removed or deliberately migrated;
- TransformationPlan is the canonical authoring root;
- runtime execution is separate from declaration;
- result and reference contracts are typed and stable enough for consumers.

---

# 20. PyTransformKit relational gate

The stable core SHOULD support enough logical operations for Customer 360 and practical data engineering:

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
targeted reshape
~~~

The operator catalog need not be exhaustive, but the semantic model must be coherent.

---

# 21. PyTransformKit runtime gate

Transformation execution MUST expose:

~~~text
TransformationExecutionId
CorrelationContext
input bindings
output bindings
engine identity
status
diagnostics
FailureEvidence
lineage evidence
~~~

TransformationPlan does not own runtime state.

---

# 22. Engine conformance gate

At least Pandas and Polars SHOULD pass one common semantic suite before 1.0.

Additional engines become stable only with explicit capability matrices and conformance evidence.

No hidden engine fallback is allowed.

---

# 23. PyTransformKit I/O boundary gate

TransformKit may own direct physical access needed for transformation execution:

~~~text
scan CSV
scan JSONL
scan Parquet
scan Arrow
projection pushdown
predicate pushdown
partition pruning
physical output write
~~~

It MUST NOT own:

~~~text
immutable RAW lifecycle
source acquisition provenance
DatasetVersion repository
publication pointer lifecycle
ingestion replay
~~~

Those remain PyIngestKit semantics.

---

# 24. PyTransformKit 1.0 RC entry gate

PyTransformKit enters RC only when:

1. public-model rationalization is complete;
2. core domain purity is green;
3. Pandas and Polars conformance is green;
4. stable reference/wire fixtures exist;
5. Customer 360 transformation works on both engines;
6. package extras are tested;
7. architecture/import gates are green;
8. no unresolved over-layering remains.

---

# 25. Phase 3 — PyIngestKit 2.0 core

PyIngestKit V2 begins after required TransformKit contracts are stable enough for consumption.

Implementation order:

~~~text
domain vocabulary
    ↓
Source and acquisition
    ↓
RAW and Artifact
    ↓
Decode and validation
    ↓
DatasetVersion
    ↓
Publication
    ↓
Replay
    ↓
runtime/result contracts
    ↓
provenance and observability
    ↓
serialization
~~~

---

# 26. PyIngestKit canonical lifecycle

V2 MUST establish:

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

This lifecycle belongs to PyIngestKit.

---

# 27. Decode is not transform

The implementation MUST preserve:

~~~text
DECODE != TRANSFORM
~~~

Decoding parses a source representation and enforces representation/schema rules.

Business derivation, relational transformation, joins, aggregation and reusable semantic transformation belong to PyTransformKit or application logic.

---

# 28. RAW gate

RAW behavior MUST define:

~~~text
immutability
checksum
ArtifactReference
source provenance
retention metadata
replay eligibility
security classification
~~~

Replay correctness depends on this foundation.

---

# 29. DatasetVersion gate

DatasetVersion MUST be distinct from:

~~~text
logical Dataset
Artifact
Resource
PhysicalHandle
latest/current publication pointer
~~~

DatasetVersionReference must be portable and wire-tested.

---

# 30. Publication and replay gate

Publication is explicit.

A physical write does not automatically create a governed DatasetVersion.

Replay creates a new IngestionRunId from preserved RAW/source evidence and records replay provenance.

Replay is not WorkflowKit retry.

---

# 31. PyIngestKit runtime gate

The runtime MUST expose:

~~~text
IngestionRunId
CorrelationContext
status
DatasetVersionReference
ArtifactReference or ResourceReference
provenance
diagnostics
FailureEvidence
~~~

Private repositories and persistence sessions do not cross public boundaries.

---

# 32. Phase 4 — PyIngestKit to PyTransformKit integration

The official dependency direction is:

~~~text
pyingestkit[transform]
    → pytransformkit
~~~

PyTransformKit MUST remain unaware of PyIngestKit.

Canonical input flow:

~~~text
DatasetVersionReference
    ↓
DatasetVersionResolver
    ↓
ResourceReference
    ↓
PyTransformKit InputBinding
~~~

Canonical publication handoff:

~~~text
TransformationResult
    ↓
ResourceReference
    ↓
PyIngestKit publication
    ↓
DatasetVersion
~~~

---

# 33. Phase 4 exit gate

The integration is qualified when:

- serialized DatasetVersionReference fixtures cross the boundary;
- no private object crosses;
- CorrelationId survives;
- IngestionRunId and TransformationExecutionId remain distinct;
- lineage links compose;
- UNKNOWN_OUTCOME and FailureEvidence survive translation;
- PyIngestKit core still imports without PyTransformKit installed.

---

# 34. Phase 5 — PyWorkflowKit 2.0 core

WorkflowKit V2 implementation order is:

~~~text
WorkflowDefinition
    ↓
graph validation
    ↓
ExecutionPlan
    ↓
WorkflowRun / TaskRun / TaskAttempt
    ↓
state machines
    ↓
local executor
    ↓
retry / timeout / cancellation
    ↓
durable metadata
    ↓
recovery / reconciliation
    ↓
events / manifests
    ↓
extension executors
~~~

---

# 35. State-machine-first rule

WorkflowRun, TaskRun and TaskAttempt semantics are frozen before complex execution infrastructure.

The first V2 executor SHOULD be deterministic and local.

A local executor is enough to prove DAG readiness, attempt creation, retry ownership, cancellation, failure mapping and durable recovery metadata.

Distributed scheduling is not required for core V2 correctness.

---

# 36. Workflow identity and durable metadata gate

Before recovery claims are made, V2 MUST persist:

~~~text
WorkflowRunId
TaskRunId
TaskAttemptId
attempt history
ExternalRunRef
state transitions
recovery queries
~~~

SQLite may serve the local reference profile.

Recovery is implemented only after this durable identity model is green.

---

# 37. Workflow retry and recovery gate

WorkflowKit owns workload retry.

The runtime exposes attempt history, retry decision, backoff, deadline, FailureEvidence and ExternalRunRef.

Recovery follows:

~~~text
process restart
    ↓
reload existing WorkflowRun
    ↓
inspect or reconcile external execution
    ↓
resume state machine
~~~

A new external run is not created solely because local memory disappeared.

---

# 38. Phase 6 — Workflow sibling integrations

Official extras become:

~~~text
pyworkflowkit[ingest]
pyworkflowkit[transform]
~~~

Workflow to IngestKit:

~~~text
TaskAttempt
    ↓
IngestionRuntime
    ↓
IngestionExecutionReference
    ↓
ExternalRunRef
~~~

Workflow to TransformKit:

~~~text
TaskAttempt
    ↓
TransformationRuntime
    ↓
TransformationExecutionReference
    ↓
ExternalRunRef
~~~

WorkflowKit does not introspect sibling internal graphs.

---

# 39. Retry and cancellation integration gate

Integration tests MUST prove:

~~~text
TaskAttempt retry
    !=
bounded provider retry
~~~

Effective provider attempts are counted.

UNKNOWN_OUTCOME blocks unsafe blind retry.

Adapters preserve provider cancellation distinctions such as requested, confirmed, unsupported and unconfirmed.

---

# 40. Phase 7 — Customer 360

Customer 360 becomes executable as soon as minimum public surfaces exist.

Recommended order:

~~~text
1. synthetic customers/orders CSV
2. source IngestionDefinitions
3. source DatasetVersions
4. customer_mart TransformationPlan
5. Pandas execution
6. Polars execution
7. transform output publication
8. WorkflowDefinition
9. sibling workload adapters
10. lineage inspection
11. wire round-trip
12. retry scenario
13. UNKNOWN_OUTCOME scenario
14. recovery scenario
15. security negative scenarios
~~~

---

# 41. Customer 360 stop-the-line rule

If the reference application requires any of the following, implementation stops and architecture is corrected:

~~~text
private sibling imports
native DataFrame in durable workflow state
circular package dependency
duplicate workload retry ownership
universal run ID
implicit publication
conflated Dataset and DatasetVersion
public types with no independent purpose
~~~

The reference application is allowed to invalidate premature design assumptions.

---

# 42. Phase 8 — Ecosystem conformance

The full matrix includes:

~~~text
architecture
public API
wire contracts
packaging
optional-dependency absence
sibling integrations
retry and reconciliation
recovery
lineage
observability
security
Customer 360
~~~

Cross-repository CI may use release-candidate wheels, CI artifacts, released packages and scheduled compatibility workflows.

A monorepo is not required.

---

# 43. Release qualification order

Preferred sequence:

~~~text
PyTransformKit 1.0 RC
    ↓
PyIngestKit 2.0 RC against qualified PyTransformKit
    ↓
PyWorkflowKit 2.0 RC against qualified siblings
    ↓
Customer 360 full RC matrix
    ↓
stable releases
~~~

Preferred publication order is PyTransformKit 1.0.0, then PyIngestKit 2.0.0, then PyWorkflowKit 2.0.0.

Same-day publication is optional.

---

# 44. PyIngestKit V1 migration mapping

Migration is semantic rather than alias-driven.

Examples:

~~~text
V1 ingestion job
    → IngestionDefinition + IngestionRuntime

V1 RAW behavior
    → RAW + ArtifactReference

V1 dataset snapshot
    → DatasetVersion

V1 transformation stage
    → TransformationPlan when semantic transformation is intended

V1 orchestration graph
    → PyWorkflowKit when workload orchestration is intended
~~~

The default posture is: V1 remains on 1.x, V2 begins at 2.0, and applications unable to migrate immediately may pin V1.

---

# 45. PyWorkflowKit V1 migration mapping

Examples:

~~~text
legacy workflow
    → WorkflowDefinition

legacy workload task
    → TaskDefinition

legacy run
    → WorkflowRun

legacy retry occurrence
    → TaskAttempt

legacy provider execution tracking
    → ExternalRunRef
~~~

Legacy concepts without V2 semantic ownership are removed rather than mechanically renamed.

---

# 46. PyTransformKit migration posture

Because TransformKit is pre-1.0, migration may be more direct.

Poor legacy names or aliases SHOULD be removed before 1.0 where needed.

Temporary beta/RC deprecation warnings are allowed, but obsolete aliases should not become permanent 1.0 baggage without evidence.

---

# 47. Migration categories

The ecosystem distinguishes:

~~~text
CODE MIGRATION
WIRE MIGRATION
METADATA-STORE MIGRATION
PHYSICAL DATA MIGRATION
~~~

A Python API rewrite does not automatically require physical data migration.

Wire migrations are versioned and MUST NOT silently discard identity, uncertainty, idempotency scope, ownership or security meaning.

---

# 48. Metadata-store migration

Stateful migration tooling SHOULD:

- detect source version;
- validate before mutation;
- support backup or rollback planning;
- migrate deterministically;
- fail on unsupported state;
- produce a migration report.

V2 is not required to retain permanent knowledge of arbitrary V1 private table schemas.

When necessary, prefer:

~~~text
legacy system
    ↓
semantic export
    ↓
versioned migration representation
    ↓
V2 importer
~~~

---

# 49. Legacy coexistence

V1 and V2 applications MAY coexist in separate environments during migration.

The ecosystem does not require incompatible major versions to coexist in one Python process.

Interchange, if required, uses explicit portable formats.

---

# 50. Feature parity policy

Full V1 feature parity is not the first V2 milestone.

Priority is:

~~~text
correct semantic ownership
stable core contracts
Customer 360
retry and recovery correctness
extension model
then broader feature parity
~~~

Distributed scheduling, web UI, large connector catalogs and complete operator catalogs MAY be deferred.

---

# 51. Compatibility shims

A compatibility shim is allowed only when:

1. real migration demand exists;
2. it does not distort V2 semantics;
3. it has tests;
4. it has a removal plan;
5. it remains outside core domain models where possible.

Mechanical aliases such as Pipeline = TransformationPlan, Job = IngestionDefinition or Step = TaskDefinition are discouraged unless semantics are genuinely identical.

---

# 52. Incremental implementation slices

Large rewrites SHOULD be delivered as vertical slices.

A completed slice normally includes:

~~~text
domain type
invariants
tests
public contract
minimal runtime behavior
documentation
package build verification
~~~

Infrastructure breadth follows semantic correctness.

---

# 53. Definition of done for an implementation lot

A lot closes only when:

- intended semantics exist;
- tests are green;
- architecture invariants pass;
- public API is documented;
- wire fixtures exist when relevant;
- forbidden dependencies are absent;
- built artifacts still install;
- conformance evidence is updated.

Code presence alone is not completion.

---

# 54. Evidence priority

When legacy code conflicts with V2 design, decision priority is:

~~~text
normative semantic ownership
    ↓
Customer 360 needs
    ↓
conformance evidence
    ↓
legacy implementation convenience
~~~

Existing-code convenience is last.

---

# 55. Specification correction during implementation

If implementation evidence reveals a flawed specification:

~~~text
evidence
    ↓
architecture review
    ↓
specification update
    ↓
invariant/test update
    ↓
implementation update
~~~

Silent divergence is prohibited.

---

# 56. Phase gates

~~~text
GATE 0
    public model rationalized

GATE 1
    portable contracts proven

GATE 2
    PyTransformKit RC-ready

GATE 3
    PyIngestKit V2 core complete

GATE 4
    IngestKit → TransformKit integration green

GATE 5
    PyWorkflowKit V2 core complete

GATE 6
    Workflow sibling adapters green

GATE 7
    Customer 360 complete

GATE 8
    ecosystem conformance green

GATE 9
    stable release qualification
~~~

Higher-level stable contracts MUST NOT freeze against unresolved lower-level boundaries.

---

# 57. Safe parallel work

The following may proceed in parallel:

~~~text
documentation
test harnesses
synthetic fixtures
provider research
non-public infrastructure prototypes
benchmark harnesses
migration inventory
security threat modeling
~~~

Public contract freeze remains ordered.

---

# 58. Primary risks

~~~text
over-layered public model
shared package extracted too early
V1 abstractions leaking into V2
WorkflowKit absorbing provider semantics
TransformKit absorbing ingestion lifecycle
retry stacking
wire contracts frozen before real use
premature plugin protocols
feature-parity pressure
~~~

The phase gates are designed to contain these risks.

---

# 59. Acceptance criteria

This plan is followed correctly when:

1. public-model rationalization occurs before stable implementation freeze;
2. boundary contracts precede sibling adapters;
3. no mandatory shared core package is introduced prematurely;
4. PyTransformKit stabilizes before downstream integration freeze;
5. PyIngestKit V2 owns acquisition, RAW, DatasetVersion, publication and replay;
6. PyTransformKit remains free of ingestion/workflow dependencies;
7. PyWorkflowKit V2 owns workload state, retry and recovery;
8. sibling adapters preserve native identities and uncertainty;
9. Customer 360 exists before final release qualification;
10. cross-framework data moves by portable reference;
11. write and publication remain distinct;
12. recovery is proven before reliability claims;
13. V1-to-V2 migration is semantic rather than alias-driven;
14. wire and state migrations are explicit;
15. compatibility shims are temporary and justified;
16. exact built artifacts are qualified;
17. stable release order follows dependency direction;
18. architecture changes update specifications and tests;
19. V2 may ship before full V1 feature parity;
20. end-to-end acceptance closes the ecosystem release.

---

# 60. Normative invariants

### IMPL-INV-01 — Semantic foundations precede infrastructure

Domain ownership and public contracts are implemented first.

### IMPL-INV-02 — Public types require independent purpose

No public abstraction exists solely for cross-framework symmetry.

### IMPL-INV-03 — Dependency direction governs implementation order

Lower-level providers stabilize before higher-level consumers freeze.

### IMPL-INV-04 — Shared contracts are specification-first

No mandatory shared runtime package is extracted before stable duplication proves the need.

### IMPL-INV-05 — PyTransformKit stabilizes first

It is the lowest-level sibling and foundation for downstream integrations.

### IMPL-INV-06 — PyIngestKit V2 is semantically clean-slate

Legacy abstractions survive only when they match V2 ownership.

### IMPL-INV-07 — PyWorkflowKit V2 is state-machine-first

Identity, retry and recovery semantics precede advanced infrastructure.

### IMPL-INV-08 — Integrations follow public contracts

No adapter depends on sibling private models.

### IMPL-INV-09 — Customer 360 is an implementation gate

The ecosystem must compose end to end before stable qualification.

### IMPL-INV-10 — Migration is explicit

Code, wire, metadata and physical-data migrations are separate concerns.

### IMPL-INV-11 — Recovery is proven before reliability claims

Durable state and reconciliation precede recovery claims.

### IMPL-INV-12 — Feature parity follows architecture correctness

V2 does not reproduce V1 mistakes merely to reach parity sooner.

---

# 61. Canonical implementation map

~~~text
                 PHASE 0
        Public model rationalization
                     │
                     ▼
                 PHASE 1
         Portable boundary contracts
                     │
                     ▼
                 PHASE 2
            PyTransformKit 1.0
                     │
                     ▼
                 PHASE 3
             PyIngestKit 2.0
                     │
                     ▼
                 PHASE 4
       IngestKit → TransformKit ACL
                     │
                     ▼
                 PHASE 5
            PyWorkflowKit 2.0
                     │
                     ▼
                 PHASE 6
        WorkflowKit sibling ACLs
                     │
                     ▼
                 PHASE 7
         Customer 360 executable
                     │
                     ▼
                 PHASE 8
        Ecosystem conformance
                     │
                     ▼
                 PHASE 9
             Stable releases
~~~

---

# 62. Final architecture statement

The V2 transition is deliberately ordered by semantic dependency.

The implementation flow is:

~~~text
freeze ownership
    ↓
freeze portable boundaries
    ↓
stabilize lowest-level provider
    ↓
build higher-level domains
    ↓
add integrations
    ↓
prove composition
    ↓
qualify releases
~~~

> **Do not migrate old code into the new architecture; migrate proven semantics into the new architecture.**

This specification is the baseline for:

~~~text
PYKIT_ECOSYSTEM_V2_END_TO_END_ACCEPTANCE_CRITERIA.md

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
