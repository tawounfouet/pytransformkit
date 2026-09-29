# PyWorkflowKit V2 — Implementation Roadmap

> **Status:** NORMATIVE V2 IMPLEMENTATION ROADMAP  
> **Target release:** PyWorkflowKit 2.0.0  
> **Date:** 2026-09-29  
> **Architecture generation:** PyKit Ecosystem V2  
> **Migration posture:** clean-slate major release guided by semantic reuse, not legacy class preservation  
> **Depends on:** PYWORKFLOWKIT_V2_TARGET_ARCHITECTURE.md  
> **Depends on:** PYWORKFLOWKIT_V2_PUBLIC_API_SPEC.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_END_TO_END_ACCEPTANCE_CRITERIA.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_IMPLEMENTATION_SEQUENCE_AND_MIGRATION_PLAN.md

---

# 1. Purpose

This document defines the ordered implementation path from the existing PyWorkflowKit 1.x line to PyWorkflowKit 2.0.0.

V2 retains proven execution semantics where they align with the new model, but the public architecture is rebuilt around:

~~~text
WorkflowDefinition
TaskDefinition
ExecutionPlan
WorkflowRun
TaskRun
TaskAttempt
ExternalRunRef
WorkflowRuntime
~~~

The governing rule is:

> **Preserve reliable execution behavior, but rebuild the runtime around explicit identities, state machines, recovery and opaque workload boundaries.**

---

# 2. V2 implementation strategy

The implementation proceeds from declaration and state semantics outward:

~~~text
public definitions
    ↓
planning
    ↓
execution identities
    ↓
state machines
    ↓
local executor
    ↓
retry / timeout / cancellation
    ↓
durable metadata
    ↓
ExternalRunRef
    ↓
recovery / reconciliation
    ↓
additional executors
    ↓
serialization / plugins
    ↓
sibling integrations
    ↓
migration / Customer 360
    ↓
RC
    ↓
2.0.0
~~~

---

# 3. Version milestone strategy

Recommended milestones:

| Milestone | Lots | Theme |
|---|---|---|
| 2.0.0a1 | LOT-00 → LOT-06 | Public model, planning, state machines, local execution |
| 2.0.0a2 | LOT-07 → LOT-11 | Retry, cancellation, durable metadata, recovery |
| 2.0.0b1 | LOT-12 → LOT-16 | Outputs, executors, serialization, plugins/security |
| 2.0.0b2 | LOT-17 → LOT-21 | PostgreSQL, sibling integrations, migration, Customer 360 |
| 2.0.0rc1 | LOT-22 | Release candidate |
| 2.0.0 | LOT-23 | Stable |

---

# Phase A — Canonical Domain, Planning and Local Runtime

# 4. LOT-00 — V2 Repository and Architecture Baseline

## Scope

Prepare the clean-slate V2 line:

~~~text
V2 package/release branch
architecture tests
public root allowlist
forbidden sibling imports
optional dependency policy
CI baseline
Python matrix
V1 semantic inventory
Customer 360 workflow fixtures
migration evidence inventory
~~~

Classify legacy components:

~~~text
REUSE
ADAPT
REWRITE
REMOVE
DEFER
~~~

## Exit criteria

- core imports without PyIngestKit/PyTransformKit;
- no server/control-plane dependency is required;
- no generic compatibility alias determines V2 domain;
- clean wheel builds;
- architecture rules execute in CI.

---

# 5. LOT-01 — Execution Identity and Shared Boundary Values

## Scope

Implement:

~~~text
WorkflowRunId
TaskRunId
TaskAttemptId
WorkflowExecutionReference
ExternalRunRef
CorrelationContext integration
FailureEvidence integration
RetryDecision skeleton
portable output/reference values
structured Diagnostic
typed execution categories
~~~

## Exit criteria

- IDs are immutable and distinct;
- correlation does not replace native identity;
- ExternalRunRef is portable and authority-neutral;
- wire-contract skeletons exist;
- no universal RunId is introduced.

---

# 6. LOT-02 — WorkflowDefinition and TaskDefinition

## Scope

Implement canonical authoring:

~~~text
WorkflowDefinition
TaskDefinition
WorkflowDefinitionBuilder
task key semantics
dependency declarations
workload descriptor abstraction
metadata
RetryPolicy skeleton
TimeoutPolicy skeleton
trigger-rule skeleton
builder/decorator adaptation hooks
definition fingerprint
root exports
~~~

## Exit criteria

- definitions are immutable after build;
- construction performs no execution;
- no public WorkflowGraph is required;
- no public DependencyGraph is required;
- TaskDefinition represents one workload boundary;
- root API snapshot passes.

---

# 7. LOT-03 — Planning and ExecutionPlan

## Scope

Implement:

~~~text
WorkflowPlanner
structural validation
cycle detection
unknown dependency rejection
deterministic topological sort
semantic validation
policy normalization
executor requirement extraction
ExecutionPlan
plan fingerprint
explain/inspection
internal DependencyGraph
~~~

## Exit criteria

- same semantic WorkflowDefinition compiles deterministically;
- compile performs no workload execution;
- ExecutionPlan contains no runtime IDs;
- graph internals remain unexported;
- plan diagnostics are structured.

---

# 8. LOT-04 — WorkflowRun / TaskRun / TaskAttempt State Machines

## Scope

Implement explicit state machines:

~~~text
WorkflowRun
TaskRun
TaskAttempt
WorkflowRunStatus
TaskRunStatus
TaskAttemptStatus
validated transitions
terminal-state protection
skip semantics
blocked semantics
unknown outcome representation
cancellation-requested state
attempt numbering
~~~

## Exit criteria

- invalid transitions fail explicitly;
- TaskRun identity survives retries;
- TaskAttempt identity never mutates into a new attempt;
- uncertainty is representable;
- state-machine property tests pass.

---

# 9. LOT-05 — In-Memory MetadataStore

## Scope

Implement:

~~~text
MetadataStore Protocol
InMemoryMetadataStore
WorkflowRun persistence
TaskRun persistence
TaskAttempt history
ExternalRunRef persistence
conditional state transition API
unfinished-run queries
manifest reference hooks
schema/version metadata
~~~

## Exit criteria

- state history is queryable;
- attempt ordering is preserved;
- invalid state overwrites are rejected;
- conformance suite for MetadataStore exists;
- in-memory implementation is deterministic.

---

# 10. LOT-06 — InlineExecutor and WorkflowRuntime MVP

## Scope

Implement:

~~~text
Executor Protocol
ExecutorDescriptor
InlineExecutor
TaskExecutionRequest / Result
WorkflowRuntime
execution loop
readiness evaluation
TaskRun creation
TaskAttempt creation
fail-fast
skip propagation
result construction
workflow diagnostics
basic events
~~~

Canonical execution:

~~~text
WorkflowDefinition / ExecutionPlan
        ↓
WorkflowRuntime
        ↓
WorkflowRun
        ↓
ready TaskRun
        ↓
TaskAttempt
        ↓
InlineExecutor
        ↓
persist result
        ↓
repeat
~~~

## Exit criteria

- local DAG executes end to end;
- WorkflowRuntime accepts WorkflowDefinition or ExecutionPlan;
- durable state is authoritative over logs;
- no retry exists yet beyond one attempt unless explicit;
- local example runs from installed wheel.

Milestone candidate: 2.0.0a1.

---

# Phase B — Reliability, Persistence and Recovery

# 11. LOT-07 — RetryPolicy and Attempt Retry

## Scope

Implement:

~~~text
RetryPolicy
BackoffStrategy
RetryDecision
structured retryability mapping
max attempts
fixed/linear/exponential backoff
jitter policy
retry budget/deadline
new TaskAttempt creation
retry diagnostics/events
injectable Clock
~~~

## Exit criteria

- retry creates a new TaskAttemptId;
- TaskRunId remains stable;
- retry decisions use structured FailureEvidence;
- timing tests are deterministic with fake clock;
- no hidden executor retry duplicates workload retry.

---

# 12. LOT-08 — Timeout and Cancellation

## Scope

Implement:

~~~text
TimeoutPolicy
execution deadline
TaskCancellationRequest / Result
WorkflowRun cancellation
TaskRun cancellation
CANCELLATION_REQUESTED
CANCELLED
CANCELLATION_UNCONFIRMED
CANCELLATION_UNSUPPORTED
timeout-to-reconciliation transition
executor cancellation capability
~~~

## Exit criteria

- timeout != confirmed failure;
- cancellation request != confirmed cancellation;
- unsupported cancellation is explicit;
- already-terminal handling is idempotent;
- state-machine conformance stays green.

---

# 13. LOT-09 — ExternalRunRef and UNKNOWN_OUTCOME

## Scope

Implement:

~~~text
ExternalRunRef full contract
external execution persistence
multiple refs per TaskAttempt where justified
UNKNOWN_OUTCOME
REQUIRES_RECONCILIATION
provider execution reference mapping
causation/correlation linkage
uncertain side-effect handling
~~~

## Exit criteria

- ExternalRunRef survives process restart;
- possession of ref does not imply cancellation authority;
- uncertain external work cannot be retried blindly;
- provider/sibling execution identity remains distinct from TaskAttemptId.

---

# 14. LOT-10 — SQLiteMetadataStore and Durable Local Runtime

## Scope

Implement:

~~~text
SQLiteMetadataStore
schema migrations
WorkflowRun persistence
TaskRun persistence
TaskAttempt history
ExternalRunRef
optimistic locking / transactional state updates
unfinished-run query
manifest reference storage
local crash/restart fixtures
~~~

## Exit criteria

- process restart preserves workflow state;
- state transitions are atomic enough for supported concurrency;
- migration versioning exists;
- Customer 360 local store requirements are supported;
- SQLite conformance suite passes.

---

# 15. LOT-11 — Recovery and Reconciliation

## Scope

Implement:

~~~text
WorkflowRuntime.recover
WorkflowRuntime.reconcile
reconcile_attempt
recoverable-run discovery
external reconciliation Protocol/capability
existing-attempt restoration
retry-after-reconciliation decision
NOT_FOUND / STILL_RUNNING / STILL_UNKNOWN
recovery diagnostics/events
fault-injection tests
~~~

Canonical rule:

~~~text
restart
    ↓
load existing IDs
    ↓
inspect ExternalRunRef
    ↓
reconcile
    ↓
resume state machine
~~~

## Exit criteria

- recovery preserves WorkflowRunId;
- existing TaskAttemptId is preserved during reconciliation;
- new TaskAttempt is created only by retry;
- restart is never equivalent to blind rerun;
- fault-injection suite proves no avoidable duplicate work.

Milestone candidate: 2.0.0a2.

---

# Phase C — Portable Results, Executors, Wire Contracts and Plugins

# 16. LOT-12 — Portable Outputs, Manifests and Execution Lineage

## Scope

Implement:

~~~text
WorkflowResult
TaskOutcome projection
portable task-output policy
small JSON-compatible outputs
ResourceReference
ArtifactReference
DatasetVersionReference compatibility
execution references
workflow manifest
WorkflowRun → TaskRun → TaskAttempt lineage
input/output reference edges
diagnostics
events/metrics/tracing hooks
~~~

## Exit criteria

- large native objects cannot enter durable outputs by default;
- workflow manifest is versioned;
- execution lineage is distinct from data lineage;
- telemetry failure does not rerun tasks;
- high-cardinality metric labels are controlled.

---

# 17. LOT-13 — Thread and Async Executors

## Scope

Implement and qualify:

~~~text
ThreadExecutor
AsyncExecutor
ExecutorRegistry
executor selection
context propagation
concurrency limits
resource ownership
async cancellation behavior
thread-safety documentation
Executor conformance suite
~~~

## Exit criteria

- both executors use the same TaskAttempt state model;
- no executor creates its own retry semantics;
- capability differences are explicit;
- executor selection is not based silently on package presence.

---

# 18. LOT-14 — Process and Subprocess Executors

## Scope

Implement:

~~~text
ProcessExecutor
SubprocessExecutor
SubprocessCommand
argv-first execution
explicit shell mode
environment allowlisting
working-directory policy
bounded stdout/stderr
redaction
process termination semantics
serialization boundary
executor reconciliation where available
~~~

## Exit criteria

- shell execution requires explicit opt-in;
- subprocess is not described as a security sandbox;
- durable workflow state does not depend on pickle/cloudpickle;
- timeout/cancellation semantics are explicit;
- security negative tests pass.

---

# 19. LOT-15 — Serialization and Durable Wire Contracts

## Scope

Implement explicit codecs for:

~~~text
WorkflowDefinition portable subset
ExecutionPlan portable subset
WorkflowExecutionReference
ExternalRunRef
CorrelationContext
FailureEvidence
workflow manifest
events
small task inputs/outputs
selected state records
~~~

Requirements:

~~~text
contract ID
contract_version
canonical JSON
golden fixtures
strict decoding
payload limits
non-executable deserialization
migration hooks
portability diagnostics
~~~

## Exit criteria

- arbitrary callables/closures fail portable serialization unless registered;
- no pickle/cloudpickle/dill public durable path exists;
- golden fixtures pass;
- wire versions are independent from package version.

---

# 20. LOT-16 — Plugins, Security and Runtime Extension Freeze

## Scope

Stabilize:

~~~text
PluginRegistry
Executor plugins
MetadataStore plugins
telemetry plugins
external workload adapters
entry-point discovery
explicit activation
compatibility ranges
CredentialReference propagation
authorization hooks
subprocess trust model
plugin security
runtime resource policies
security negative suite
~~~

## Exit criteria

- discovery != activation;
- untrusted payloads cannot activate plugins;
- plugin compatibility is machine-checkable;
- core import remains side-effect free;
- security baseline is green.

Milestone candidate: 2.0.0b1.

---

# Phase D — Production Persistence and Sibling Integrations

# 21. LOT-17 — PostgreSQL MetadataStore

## Scope

Implement optional production-oriented persistence:

~~~text
pyworkflowkit[postgres]
PostgreSQLMetadataStore
transactional/optimistic state transitions
concurrent runtime protection
recovery queries
schema migrations
connection ownership
failure translation
MetadataStore conformance
~~~

## Exit criteria

- PostgreSQL remains optional;
- persistence semantics match SQLite where contract applies;
- concurrent updates cannot silently corrupt attempt history;
- provider details remain infrastructure-private.

---

# 22. LOT-18 — PyIngestKit Integration

## Scope

Implement:

~~~text
pyworkflowkit[ingest]
pyworkflowkit.integrations.pyingestkit
IngestionWorkload
TaskAttempt → IngestionRuntime.run
IngestionExecutionReference
ExternalRunRef mapping
CorrelationContext propagation
FailureEvidence mapping
UNKNOWN_OUTCOME propagation
cancellation/reconciliation capability mapping
portable DatasetVersionReference output
~~~

## Exit criteria

- WorkflowKit does not inspect acquisition/RAW/decode/version/publication internals;
- new task retry normally creates new IngestionRunId;
- recovery can reconnect through ExternalRunRef when supported;
- PyWorkflowKit core imports without PyIngestKit.

---

# 23. LOT-19 — PyTransformKit Integration

## Scope

Implement:

~~~text
pyworkflowkit[transform]
pyworkflowkit.integrations.pytransformkit
TransformationWorkload
TaskAttempt → TransformationRuntime.execute
TransformationExecutionReference
ExternalRunRef mapping
CorrelationContext propagation
FailureEvidence mapping
UNKNOWN_OUTCOME propagation
cancellation/reconciliation mapping where supported
portable ResourceReference output
~~~

## Exit criteria

- WorkflowKit never schedules TransformationPlan internal nodes;
- one transform task remains one workload boundary;
- task retry creates a new TransformationExecutionId unless recovering existing work;
- PyWorkflowKit core imports without PyTransformKit.

---

# 24. LOT-20 — Cross-Framework Retry and Recovery Conformance

## Scope

Build explicit integration conformance for:

~~~text
TaskAttempt retry versus sibling provider retry
retry amplification counting
UNKNOWN_OUTCOME
publication uncertainty
sibling cancellation
recovery after local process loss
ExternalRunRef persistence
causation/correlation propagation
portable output handoff
integration optional-dependency isolation
~~~

## Exit criteria

- no equivalent retry scope is stacked implicitly;
- uncertainty survives every adapter;
- cancellation truth is preserved;
- recovery avoids duplicate sibling execution when reconcilable;
- cross-framework contract fixtures pass.

---

# 25. LOT-21 — V1 Migration and Customer 360 Beta Gate

## Scope

This lot combines final migration evidence and end-to-end beta qualification.

Migration work:

~~~text
V1 concept inventory
legacy workflow → WorkflowDefinition
legacy task/step → TaskDefinition
legacy run → WorkflowRun
legacy retry history → TaskAttempt sequence
legacy external tracking → ExternalRunRef
metadata semantic export/import
decorator migration
executor migration
recovery migration
compatibility-shim decision log
~~~

Customer 360 work:

~~~text
ingest customers task
ingest orders task
transform task
publish task
portable task outputs
workflow retry scenario
publication UNKNOWN_OUTCOME
process restart/recovery
lineage traversal
security negative scenarios
built-artifact execution
~~~

## Exit criteria

- migration does not preserve ambiguous generic aliases by default;
- unsupported legacy state is explicit;
- Customer 360 full workflow is green;
- sibling integrations use only public contracts;
- recovery scenario proves identity preservation;
- relevant ecosystem E2E acceptance gates are green.

Milestone candidate: 2.0.0b2.

---

# Phase E — Release Qualification

# 26. LOT-22 — PyWorkflowKit 2.0 Release Candidate

**Target:** 2.0.0rc1

## Scope

Run complete qualification:

~~~text
root API snapshot
Python matrix
Ruff / format / mypy
DAG/planning tests
state-machine tests
retry/backoff tests
timeout/cancellation tests
Executor conformance
MetadataStore conformance
recovery/reconciliation fault injection
wire golden fixtures
plugin compatibility
security tests
sibling adapter conformance
optional-extra isolation
wheel install
sdist install if published
Customer 360
migration fixtures
docs/examples
release evidence manifest
~~~

## Exit criteria

- no blocker remains;
- stable states/identities/Protocols are frozen;
- built artifacts pass;
- RC requires no architecture redesign;
- only blocker fixes are permitted without RC reset.

---

# 27. LOT-23 — PyWorkflowKit 2.0.0 Stable

**Target:** 2.0.0

## Scope

- fix RC blockers only;
- rerun complete matrix;
- finalize state/wire compatibility baselines;
- finalize executor and metadata compatibility matrix;
- finalize sibling integration ranges;
- finalize migration guide;
- finalize changelog/release notes;
- tag v2.0.0;
- publish artifacts;
- produce auditable qualification report.

## Stable acceptance

PyWorkflowKit 2.0.0 releases only when:

1. WorkflowDefinition is the canonical authoring root;
2. TaskDefinition represents one workload boundary;
3. ExecutionPlan is deterministic and public;
4. WorkflowGraph/DependencyGraph remain internal;
5. WorkflowRunId, TaskRunId and TaskAttemptId are distinct;
6. retry always creates a new TaskAttempt;
7. timeout and cancellation preserve uncertainty;
8. ExternalRunRef is durable and portable;
9. recovery preserves existing identities and reconciles before rerun;
10. durable outputs are portable/small;
11. InlineExecutor is fully qualified;
12. SQLite durable recovery is qualified;
13. optional executors declare capabilities honestly;
14. MetadataStore transitions are protected;
15. serialization is versioned and non-executable;
16. plugins require explicit activation;
17. sibling integrations remain optional and opaque;
18. Customer 360 workflow/recovery path passes;
19. clean built artifacts install on supported Python versions;
20. no blocker remains.

---

# 28. Final lot count

The V2 roadmap contains:

~~~text
LOT-00 → LOT-23
24 implementation lots
~~~

Milestone grouping:

~~~text
Foundation / a1
    LOT-00 → LOT-06

Reliability / a2
    LOT-07 → LOT-11

Executors + contracts / b1
    LOT-12 → LOT-16

Persistence + integrations + migration / b2
    LOT-17 → LOT-21

RC
    LOT-22

Stable
    LOT-23
~~~

---

# 29. Definition of Done for every lot

A lot is DONE only when all applicable conditions hold:

- semantic ownership matches target architecture;
- public API and internal boundary are typed;
- state transitions are tested;
- unit/property tests pass;
- executor/store conformance passes where applicable;
- fault-injection passes where reliability claims are made;
- structured failures are used;
- security tests pass;
- optional dependencies remain isolated;
- wire fixtures are updated where relevant;
- Ruff/format/mypy pass;
- package builds;
- installed-wheel smoke passes;
- docs/examples are updated;
- migration impact is recorded;
- acceptance evidence is retained.

---

# 30. Explicit V2 non-goals

The 2.0 roadmap does not add a required:

~~~text
cron scheduler
central scheduler server
distributed worker fleet
message broker
web UI
multi-tenant SaaS control plane
enterprise RBAC platform
data transformation engine
ingestion lifecycle
data catalog
~~~

These capabilities may exist later as optional layers without changing core ownership.

---

# 31. Final roadmap statement

The V2 implementation path is:

~~~text
declare workloads
        ↓
compile deterministic execution semantics
        ↓
freeze run/task/attempt identities
        ↓
prove local execution
        ↓
add retry / timeout / cancellation
        ↓
persist durable state
        ↓
make uncertainty and ExternalRunRef explicit
        ↓
recover by reconciliation
        ↓
add executors safely
        ↓
freeze wire/plugin contracts
        ↓
integrate sibling runtimes as opaque workloads
        ↓
migrate V1 semantics
        ↓
prove Customer 360
        ↓
2.0.0
~~~

> **PyWorkflowKit 2.0 is complete when a generic workload graph can execute, fail, retry, cancel, survive restart and reconcile external work with explicit identities and evidence, without absorbing the domain semantics of the workloads it coordinates.**
