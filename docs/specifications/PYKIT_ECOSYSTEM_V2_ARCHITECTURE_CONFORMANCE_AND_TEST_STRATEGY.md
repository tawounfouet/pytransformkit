# PyKit Ecosystem V2 — Architecture Conformance and Test Strategy

> **Status:** NORMATIVE CONFORMANCE BASELINE  
> **Architecture generation:** V2  
> **Date:** 2026-09-28  
> **Scope:** PyIngestKit, PyTransformKit, PyWorkflowKit  
> **Compatibility posture:** architecture-as-code with executable conformance gates  
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

---

# 1. Purpose

This document defines how PyKit V2 proves continuously that its implementation still conforms to its architecture.

The governing principle is:

> **An architectural rule that cannot be verified continuously will eventually be violated accidentally.**

The architecture is therefore considered durable only when important invariants have executable evidence in tests and CI.

---

# 2. Conformance categories

The ecosystem distinguishes:

~~~text
UNIT TESTS
COMPONENT TESTS
PROPERTY TESTS
ARCHITECTURE TESTS
CONTRACT TESTS
INTEGRATION TESTS
PACKAGING TESTS
COMPATIBILITY TESTS
SECURITY TESTS
END-TO-END TESTS
PERFORMANCE TESTS
~~~

Coverage percentage alone is not architecture conformance.

---

# 3. Canonical test pyramid

~~~text
                    END TO END
                 Reference application
              ─────────────────────
              Cross-framework tests
            ─────────────────────────
            Contract / conformance
          ─────────────────────────────
          Architecture / packaging
        ─────────────────────────────────
        Unit / component / property
~~~

The broadest layer should remain fast and local.

Expensive integration scenarios should focus on high-risk semantic boundaries.

---

# 4. Invariant traceability

Important requirements SHOULD follow this chain:

~~~text
Specification
    ↓
Invariant ID
    ↓
Automated test
    ↓
CI gate
    ↓
Release evidence
~~~

Existing invariant families include ID-INV, FAIL-INV, DATA-INV, LIN-INV, OBS-INV, INT-INV, PKG-INV and WIRE-INV.

This specification introduces TEST-INV.

---

# 5. Conformance matrix

The ecosystem SHOULD maintain a matrix mapping normative rules to evidence.

| Invariant | Owner | Evidence | Gate |
|---|---|---|---|
| INT-INV-03 | ecosystem | import graph test | architecture |
| PKG-INV-02 | each package | clean install smoke | packaging |
| WIRE-INV-12 | producer + consumers | golden fixtures | contract |
| FAIL-INV-03 | integrations | uncertainty scenario | integration |
| LIN-INV-10 | native owner | lineage authority test | lineage |

A stable release should be able to identify which test proves each critical architectural rule.

---

# 6. Test ownership

Canonical ownership is:

~~~text
PyTransformKit
    transformation semantics
    engine conformance
    logical and field lineage
    no sibling dependency

PyIngestKit
    acquisition
    RAW
    DatasetVersion
    publication
    provenance
    optional transform integration

PyWorkflowKit
    workflow/task/attempt semantics
    retry
    recovery
    cancellation
    sibling workload adapters

Ecosystem reference suite
    end-to-end composition
~~~

Shared contracts are tested by both producers and consumers.

---

# 7. Core independence

Each framework MUST run its core conformance suite without sibling frameworks installed.

~~~text
PyTransformKit core
    no PyIngestKit
    no PyWorkflowKit

PyIngestKit core
    no PyTransformKit required
    no PyWorkflowKit

PyWorkflowKit core
    no PyIngestKit
    no PyTransformKit
~~~

Integration suites enable sibling dependencies explicitly.

---

# 8. Local gate

Each repository SHOULD expose one fast local validation command covering at least:

~~~text
format check
lint
type check
unit tests
architecture import checks
core smoke
~~~

The exact toolchain is non-normative.

---

# 9. Full CI gate

Release-quality CI SHOULD include:

~~~text
format
lint
typing
unit
property
architecture
contract
integration
packaging
supported Python matrix
optional dependency matrix
security checks
reference application
installed artifact smoke
~~~

A stable release should not bypass failed normative gates without explicit architecture review.

---

# 10. Architecture tests

Architecture tests SHOULD verify:

~~~text
dependency direction
forbidden imports
domain purity
integration namespace isolation
package-root exports
plugin boundaries
no import-time telemetry
no engine-native domain types
no private persistence types in public contracts
~~~

---

# 11. Import graph rules

The canonical sibling import rules are:

~~~text
pytransformkit
    MUST NOT import pyingestkit
    MUST NOT import pyworkflowkit

pyingestkit core
    MUST NOT import pyworkflowkit
    MUST NOT require pytransformkit

pyworkflowkit core
    MUST NOT import pyingestkit
    MUST NOT import pytransformkit
~~~

Only documented integration namespaces may cross allowed boundaries.

---

# 12. Static and runtime import analysis

CI SHOULD combine:

~~~text
STATIC ANALYSIS
    AST or dependency graph inspection

RUNTIME ANALYSIS
    clean-environment imports
    explicit integration activation
~~~

Static checks catch obvious edges.

Runtime checks catch dynamic imports and undeclared optional dependencies.

---

# 13. Domain purity

PyTransformKit domain MUST remain free from Pandas, Polars, PyArrow, DuckDB, database drivers and cloud SDKs.

PyWorkflowKit domain MUST remain free from sibling framework types and infrastructure drivers.

PyIngestKit domain MUST remain free from WorkflowKit types and mandatory TransformKit runtime internals.

---

# 14. Native type leakage

Negative tests SHOULD reject accidental public domain dependencies on:

~~~text
Pandas DataFrame
Polars DataFrame
Polars LazyFrame
Arrow Table
DuckDB Relation
database session
provider client
~~~

These belong to runtime or infrastructure boundaries.

---

# 15. Public API conformance

Stable public surfaces SHOULD be freeze-testable.

Tests SHOULD cover:

~~~text
package-root exports
public signatures
Protocol members
exception hierarchy
enum values
entry-point groups
extras names
~~~

Snapshot tests should protect intentionally stable surfaces, not incidental output.

---

# 16. Protocol conformance

Public extension interfaces require reusable behavioral conformance suites.

Examples:

~~~text
EngineAdapterConformance
SourceConnectorConformance
TaskExecutorConformance
MetadataStoreConformance
ResourceResolverConformance
EventSinkConformance
~~~

Static typing alone is insufficient.

---

# 17. PyTransformKit engine conformance

Every official engine adapter SHOULD run a common semantic suite for supported operations:

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
reshape
null semantics
schema propagation
failure mapping
capability reporting
~~~

Unsupported capabilities must fail explicitly.

---

# 18. Cross-engine differential tests

For common supported semantics:

~~~text
same logical plan
    ↓
multiple engines
    ↓
normalized semantic result comparison
~~~

Tests compare logical meaning, not native representation.

Unspecified ordering and equivalent logical types should be normalized according to contract rules.

---

# 19. No hidden engine fallback

A required test proves:

~~~text
selected engine lacks required capability
    ↓
explicit unsupported capability outcome
~~~

Silent fallback to another engine is a conformance failure unless fallback was explicitly configured.

---

# 20. Planning and optimizer conformance

PyTransformKit SHOULD prove:

~~~text
deterministic logical plan
deterministic dependency order
schema propagation
capability requirements
stable plan fingerprint
optimizer semantic equivalence
lineage preservation
~~~

Optimization cannot change declared logical meaning.

---

# 21. Expression conformance

Expression tests SHOULD cover:

~~~text
static typing
nullability
dependency extraction
serialization
canonical fingerprint
cross-engine evaluation
invalid operation rejection
lineage derivation
~~~

Opaque expressions must report reduced portability or lineage honestly.

---

# 22. PyIngestKit lifecycle conformance

PyIngestKit SHOULD test:

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

Stage ownership and evidence must remain explicit.

---

# 23. RAW conformance

Tests MUST verify:

- RAW immutability where promised;
- checksum stability;
- replay from preserved RAW;
- no business transformation mutates RAW;
- provenance points to the original acquisition.

---

# 24. Decode versus transform

Tests SHOULD prove:

~~~text
representation decoding
    belongs to ingestion

business transformation
    belongs to PyTransformKit or application logic
~~~

PyIngestKit core must not evolve into a competing relational transformation engine.

---

# 25. DatasetVersion conformance

Tests SHOULD verify:

- immutable version identity;
- changed content creates a new version;
- latest/current pointer differs from immutable version;
- concrete version reference is reproducible;
- resource references are portable;
- publication provenance is retained.

---

# 26. Publication conformance

Publication tests SHOULD cover:

~~~text
success
idempotent repeat
known failure
timeout
UNKNOWN_OUTCOME
reconciliation confirmed success
reconciliation confirmed failure
still unknown
already-published conflict
~~~

WRITE and PUBLISH must remain observably distinct.

---

# 27. PyWorkflowKit graph conformance

Workflow tests SHOULD cover:

~~~text
valid DAG
cycle rejection
unknown dependency rejection
deterministic topological order
conditional readiness
skip behavior
fail-fast
independent branches
~~~

Workflow dependency semantics remain separate from transformation semantics.

---

# 28. State-machine conformance

WorkflowRun, TaskRun and TaskAttempt need explicit transition tests for:

~~~text
valid transition
invalid transition
retry
timeout
cancellation
recovery
reconciliation
terminal-state protection
~~~

Testing only final outcomes is insufficient.

---

# 29. Retry identity conformance

Canonical scenario:

~~~text
TaskRun TR-1
├── TaskAttempt A1 FAILED
└── TaskAttempt A2 SUCCEEDED
~~~

Assertions:

~~~text
same TaskRunId
different TaskAttemptId
same CorrelationId
fresh downstream execution identity
attempt history preserved
~~~

---

# 30. Recovery conformance

Crash and restart tests SHOULD prove:

~~~text
same WorkflowRunId
same persisted TaskRunId
existing ExternalRunRef retained
reattachment or reconciliation attempted
no accidental new provider execution
~~~

Recovery is not rerun.

---

# 31. Cancellation and timeout conformance

Tests MUST distinguish:

~~~text
cancellation requested
provider accepted
provider confirmed
provider unsupported
provider unconfirmed
provider completed anyway
~~~

They must also prove:

~~~text
caller timeout
    does not imply
provider execution stopped
~~~

Unknown side-effect state must remain explicit.

---

# 32. Failure taxonomy conformance

Each framework SHOULD maintain table-driven cases mapping representative failures to:

~~~text
error code
failure category
retryability
uncertainty
execution reference
correlation
~~~

Human-readable error text is not the machine oracle.

---

# 33. Retry ownership conformance

Cross-framework tests MUST prove:

~~~text
PyWorkflowKit
    owns workload retry

PyIngestKit
    owns bounded ingestion-internal retry

PyTransformKit
    owns bounded engine/provider retry
~~~

Hidden whole-run retry stacking is a conformance failure.

---

# 34. Retry amplification

At least one scenario SHOULD count actual provider attempts across nested retry scopes.

Observed attempts must stay within the declared retry budget.

Driver or SDK retries count toward the effective retry chain.

---

# 35. Idempotency conformance

Operations claiming idempotency MUST be tested against actual provider semantics.

Examples:

~~~text
same idempotency key twice
    → one logical effect

create-if-absent conflict
    → success-equivalent only when contract defines it
~~~

Generating a key alone is not proof.

---

# 36. Unknown outcome and reconciliation

Important side-effecting integrations SHOULD inject:

~~~text
request sent
provider may commit
acknowledgement lost
~~~

Expected behavior:

~~~text
UNKNOWN_OUTCOME
    ↓
no blind retry
    ↓
reconciliation when supported
~~~

Reconciliation tests include confirmed success, confirmed failure, still unknown, eventual-consistency not-found and unsupported reconciliation.

---

# 37. Deadline and backoff conformance

Retry tests SHOULD prove:

- outer deadline is respected;
- inner timeout uses remaining budget;
- no retry begins after exhaustion;
- provider Retry-After may constrain delay;
- cancellation stops future retries;
- jitter remains within configured bounds.

Injectable clocks are preferred.

---

# 38. Reference conformance

Portable references SHOULD test:

~~~text
identity
equality
serialization
versioning
redaction
namespace validation
locator validation
portability class
lifetime
expiry
~~~

Active runtime handles must not pass durable-reference tests.

---

# 39. PhysicalHandle negative cases

Required negative scenarios:

~~~text
DataFrame
    cannot become DatasetVersionReference

PhysicalHandle
    cannot persist in durable WorkflowKit state

host-local resource
    cannot claim CROSS_HOST portability
~~~

---

# 40. Ingestion to transformation contract test

Canonical scenario:

~~~text
PyIngestKit DatasetVersionReference
    ↓ serialize
PyTransformKit integration
    ↓ decode and resolve
InputBinding
~~~

Assertions include preserved version identity, no private PyIngestKit object dependency, accepted contract version and correct resource binding.

---

# 41. Transformation to publication contract test

Canonical scenario:

~~~text
TransformationResult
    ↓
ResourceReference or ArtifactReference
    ↓
PyIngestKit publication
    ↓
new DatasetVersion
~~~

Assertions prove physical output alone does not create governed version identity.

---

# 42. Workflow sibling adapter conformance

For WorkflowKit to IngestKit and WorkflowKit to TransformKit:

- sibling runtime is treated as one workload;
- native execution identity is preserved;
- ExternalRunRef is retained;
- correlation propagates;
- retry ownership remains at workload level in WorkflowKit;
- cancellation and reconciliation remain provider-aware.

---

# 43. Internal graph isolation

WorkflowKit MUST NOT inspect and schedule internal TransformationPlan nodes or PyIngestKit lifecycle stages by default.

The sibling workload boundary is opaque except for public contracts.

Architecture tests should fail if private graph internals cross this boundary.

---

# 44. Correlation and causation conformance

Cross-framework tests SHOULD verify:

~~~text
CorrelationId
    remains stable across the broader operation

TaskAttemptId
    becomes causation when it directly launches child work

native execution IDs
    remain distinct
~~~

Shared correlation alone must not fabricate causation.

---

# 45. Lineage conformance

Owned lineage suites SHOULD prove:

~~~text
PyIngestKit
    Source → RAW → DatasetVersion → Publication

PyTransformKit
    Input Dataset/Field → Transformation → Output Dataset/Field

PyWorkflowKit
    WorkflowRun → TaskRun → TaskAttempt → ExternalRunRef
~~~

---

# 46. End-to-end lineage

The ecosystem reference flow SHOULD support traversal from:

~~~text
Source
    ↓
RAW
    ↓
customers@52
    ↓
TransformationExecution
    ↓
output Resource
    ↓
customer_mart@8
~~~

and from WorkflowRun to the external executions that produced those data objects.

---

# 47. Field lineage

PyTransformKit SHOULD maintain semantic lineage cases for:

~~~text
projection
rename
cast
derive
filter
join
aggregate
window
deduplicate
sort
pivot
~~~

Tests must distinguish field-value derivation from row filtering, grouping and ordering dependencies.

---

# 48. Lineage confidence

Opaque transformations must use appropriate confidence:

~~~text
EXACT
DECLARED
INFERRED
PARTIAL
UNKNOWN
~~~

Exact lineage must never be fabricated.

---

# 49. Observability conformance

Tests SHOULD verify:

- framework-owned event namespace;
- EventId separate from execution ID;
- CorrelationId propagation;
- TraceId remains observational;
- no secret leakage;
- diagnostics work without exporters;
- metric labels avoid high-cardinality IDs;
- telemetry failure stays inside telemetry scope.

---

# 50. No import-time side effects

A clean-process test MUST prove package import does not:

~~~text
open network sockets
start exporter threads
start metrics servers
scan and activate plugins
configure root logging
mutate global integration registries
~~~

---

# 51. Redaction conformance

Fixtures SHOULD inject secret-like values into:

~~~text
URLs
headers
DSNs
provider errors
metadata
query parameters
~~~

and verify they do not appear in logs, events, manifests, FailureEvidence or portable serialized references.

---

# 52. Metric cardinality

Default metrics MUST NOT use unbounded labels such as:

~~~text
execution ID
CorrelationId
DatasetVersionId
full URI
SQL text
exception message
~~~

Representative exported metrics should be inspected in tests.

---

# 53. Wire-contract conformance

Every stable wire contract SHOULD test:

~~~text
contract ID
contract version
minimal fixture
full fixture
unknown optional field
missing required field
unsupported version
invalid enum
invalid timestamp
duplicate key
payload limit
round trip
~~~

---

# 54. Golden fixtures and migrations

Stable shared contracts MUST have golden serialized fixtures.

Every supported migration SHOULD prove:

~~~text
historical fixture
    ↓
decode
    ↓
version-specific migration
    ↓
current DTO
    ↓
semantic assertion
~~~

Safety-sensitive meaning must survive migration.

---

# 55. Canonicalization

Fingerprint-producing contracts SHOULD prove:

- object key order does not alter fingerprint;
- insignificant formatting does not alter fingerprint;
- semantic changes do alter fingerprint;
- unordered collections canonicalize deterministically;
- timestamp normalization is stable.

---

# 56. Packaging conformance

Release CI SHOULD:

~~~text
build wheel
install wheel in clean environment
import package
run installed smoke
install optional extras
run extra smoke
inspect package metadata
~~~

If an sdist is published, it should be tested too.

---

# 57. Installation profiles

Required profiles are:

~~~text
A — PyTransformKit core
B — PyIngestKit core
C — PyWorkflowKit core
D — PyIngestKit + PyTransformKit
E — PyWorkflowKit + PyIngestKit
F — PyWorkflowKit + PyTransformKit
G — full ecosystem reference application
~~~

---

# 58. Optional dependencies

For every optional feature, CI SHOULD prove both:

~~~text
dependency absent
    core still works
    feature fails clearly

dependency installed
    official feature smoke passes
~~~

Optional must mean optional in installation, import and activation.

---

# 59. Compatibility matrices

Libraries SHOULD test:

~~~text
minimum declared dependency versions
latest allowed dependency versions
supported Python versions
supported sibling package ranges
supported wire versions
~~~

A compatibility range is a tested claim.

---

# 60. Property, state-machine and fuzz testing

High-value targets include:

~~~text
expression trees
schema transformations
DAG generation
serialization round trips
workflow state machines
ingestion lifecycle
reference parsing
wire decoding
plugin metadata
~~~

These methods supplement deterministic example tests.

---

# 61. Concurrency and determinism

Tests SHOULD cover:

- async context isolation;
- thread context isolation;
- process execution;
- concurrent state updates;
- cancellation races;
- retry races;
- metadata-store atomicity.

Deterministic artifacts such as plans, fingerprints and canonical JSON should remain stable across repeated runs.

---

# 62. Network and provider tiers

Core conformance should not require public internet access.

Provider testing may use:

~~~text
fake
local emulator
containerized service
real sandbox provider
~~~

A fake only proves semantics it actually models.

Provider-specific claims such as cancellation, transaction behavior and unknown outcome handling require appropriately faithful tests.

---

# 63. Reference application

The canonical reference application SHOULD follow:

~~~text
examples/customer_360/
├── ingestion/
│   ├── customers.py
│   └── orders.py
├── transformations/
│   └── customer_mart.py
└── workflows/
    └── daily_customer_mart.py
~~~

It is a conformance asset, not merely a tutorial.

---

# 64. Reference scenarios

The reference application SHOULD prove:

~~~text
HAPPY PATH
    Source → RAW → DatasetVersion → Transform → Publish

FAILURE PATH
    transient or uncertain operation → correct retry/reconciliation

RECOVERY PATH
    process loss → reattach/reconcile → no duplicate execution

SERIALIZATION PATH
    durable references/events/manifests survive round trip

LINEAGE PATH
    source-to-publication and workflow-to-data traversal
~~~

---

# 65. Security baseline

CI SHOULD verify:

~~~text
no pickle at durable boundaries
no eval in decoders
no raw secrets in fixtures
no plugin auto-activation from payload
credential-bearing URI redaction
payload size limits
~~~

A dedicated security specification may extend these controls.

---

# 66. Flaky tests

Normative conformance tests MUST NOT silently qualify a release when flaky.

Temporary quarantine requires:

- affected invariant;
- reason;
- owner;
- issue;
- review date.

A skipped test is not a pass.

---

# 67. CI clarity

CI jobs SHOULD reveal their purpose.

Examples:

~~~text
core-python-3.12
architecture-boundaries
wire-contracts
integration-ingest-transform
integration-workflow-transform
wheel-smoke
reference-customer-360
~~~

---

# 68. Cross-repository conformance

Separate repositories may coordinate through:

- released packages;
- release-candidate wheels;
- CI artifacts;
- scheduled compatibility workflows;
- consumer-triggered tests.

A monorepo is not required.

---

# 69. Release candidate gate

Before stable publication, a release candidate SHOULD pass:

~~~text
package-local gates
architecture gate
public API snapshot
wire fixtures
migration tests
built artifact smoke
minimum dependency profile
latest compatible profile
sibling integration matrix
reference application
recovery and uncertainty scenarios
security checks
~~~

---

# 70. Built artifacts are authoritative

The wheel or sdist intended for publication is the release unit.

Source checkout success alone does not prove:

- package data included;
- metadata correct;
- extras correct;
- imports correct after installation.

Built artifacts must be tested.

---

# 71. Documentation conformance

Public Getting Started examples, supported scripts and official notebooks SHOULD execute against installed artifacts where practical.

Documentation drift is a public compatibility defect.

---

# 72. Negative testing

Important boundaries SHOULD include rejection scenarios such as:

~~~text
forbidden import
unsupported contract version
private object crossing ACL
credential-bearing locator
invalid state transition
unsafe retry
unsupported capability
PhysicalHandle in durable state
~~~

Happy paths alone are insufficient.

---

# 73. Fault injection

Reliability suites SHOULD inject failures:

~~~text
before provider call
after request send
after possible commit
before acknowledgement
during persistence
during cancellation
during recovery
~~~

This is required to prove uncertainty semantics rather than assume them.

---

# 74. Specification drift

When implementation evidence shows a specification must change:

~~~text
identify mismatch
    ↓
architecture decision
    ↓
update specification
    ↓
update invariant
    ↓
update tests
    ↓
update implementation
~~~

Implementation and normative documentation must not diverge silently.

---

# 75. Public-type justification

Before stabilizing a new public architecture type, maintainers SHOULD answer:

1. Which invariant does it own?
2. Which lifecycle does it own?
3. Which public behavior does it own?
4. Can it be tested independently?
5. Does it serialize independently when needed?
6. Does it reduce ambiguity rather than add ceremony?

A type with no strong answers should remain internal or be removed.

This protects V2 from artificial symmetry.

---

# 76. Architecture review checklist

Every substantial feature SHOULD answer:

1. Which bounded context owns it?
2. Does dependency direction remain valid?
3. Which public contract crosses boundaries?
4. Who owns retry?
5. Are native identities preserved?
6. Is uncertainty preserved?
7. Is serialization safe?
8. Is lineage ownership clear?
9. Does telemetry remain observational?
10. Which conformance tests protect these decisions?

---

# 77. Release qualification evidence

A stable release SHOULD be able to report:

~~~text
package/version/commit
supported Python versions
tested dependency ranges
public API baseline
supported wire contracts
integration matrix
architecture invariants
reference scenarios
built artifact hashes
~~~

This may later become a machine-readable qualification report.

---

# 78. Acceptance criteria

This strategy is implemented correctly when:

1. critical normative invariants have automated evidence;
2. core frameworks test independently;
3. forbidden dependency edges fail CI;
4. native infrastructure types cannot leak into pure domain contracts;
5. stable public API surfaces are freeze-testable;
6. public extension points have behavioral conformance suites;
7. PyTransformKit engines share semantic tests;
8. PyIngestKit lifecycle and publication semantics are tested;
9. PyWorkflowKit state, retry and recovery are tested;
10. UNKNOWN_OUTCOME has fault-injection coverage;
11. retry amplification is observable;
12. cross-framework contracts are tested as serialized payloads;
13. correlation, lineage and observability compose end-to-end;
14. optional dependencies are tested absent and installed;
15. built artifacts are tested in clean environments;
16. Python/dependency compatibility matrices are exercised;
17. the reference application proves full composition;
18. flaky normative tests cannot silently qualify a release;
19. specification drift follows an explicit process;
20. stable releases produce auditable qualification evidence.

---

# 79. Normative invariants

### TEST-INV-01 — Architecture rules are executable

Important normative constraints have automated tests.

### TEST-INV-02 — Core conformance is sibling-independent

Each framework proves core behavior independently.

### TEST-INV-03 — Cross-framework behavior is contract-tested

Integrations rely on public contracts, not private implementation.

### TEST-INV-04 — Negative paths are first-class

Failure, timeout, cancellation, uncertainty and invalid input are explicitly tested.

### TEST-INV-05 — Built artifacts are the release unit

Wheel and sdist qualification matters more than source-tree confidence alone.

### TEST-INV-06 — Compatibility claims require evidence

Declared package and wire support is backed by matrices and fixtures.

### TEST-INV-07 — Semantic equivalence outranks native representation

Cross-engine tests compare logical meaning.

### TEST-INV-08 — Retry ownership is measurable

Nested attempts and amplification are observable.

### TEST-INV-09 — Recovery differs from rerun

Crash/restart tests preserve existing execution identity.

### TEST-INV-10 — Golden fixtures protect stable contracts

Wire and public snapshots detect accidental drift.

### TEST-INV-11 — Reference application is a conformance asset

End-to-end composition is tested continuously.

### TEST-INV-12 — Specification and implementation evolve together

Normative changes update documentation, tests and code deliberately.

---

# 80. Canonical CI architecture

~~~text
                     Pull Request
                          │
          ┌───────────────┼────────────────┐
          │               │                │
          ▼               ▼                ▼
      Static Gate     Core Test Gate   Contract Gate
    lint / typing     unit / property   wire / fixtures
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                 Architecture Gate
                 imports / boundaries
                          │
                          ▼
                Integration Matrix
              sibling / provider tests
                          │
                          ▼
                  Packaging Gate
                wheel / sdist smoke
                          │
                          ▼
                Reference App Gate
                 full V2 composition
                          │
                          ▼
              Release Qualification
~~~

---

# 81. Final architecture statement

PyKit V2 does not consider architecture complete when diagrams and Markdown are correct.

Architecture becomes durable only when CI continuously proves that:

~~~text
dependencies remain acyclic
domains remain isolated
contracts remain portable
identities remain distinct
retry ownership remains clear
uncertainty remains explicit
lineage remains owned
telemetry remains observational
packages remain independently installable
integrations remain compatible
~~~

The central rule is:

> **Specifications define the architecture; conformance tests keep it true.**

This specification is the baseline for:

~~~text
PYKIT_ECOSYSTEM_V2_SECURITY_AND_TRUST_BOUNDARIES.md
PYKIT_ECOSYSTEM_V2_REFERENCE_APPLICATION_SPEC.md
PYKIT_ECOSYSTEM_V2_RELEASE_COMPATIBILITY_AND_VERSIONING_POLICY.md
PYKIT_ECOSYSTEM_V2_IMPLEMENTATION_SEQUENCE_AND_MIGRATION_PLAN.md
~~~
