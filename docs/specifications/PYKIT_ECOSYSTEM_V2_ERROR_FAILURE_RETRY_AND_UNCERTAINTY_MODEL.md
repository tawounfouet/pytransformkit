# PyKit Ecosystem V2 — Error, Failure, Retry and Uncertainty Model

> **Status:** NORMATIVE FAILURE AND RETRY BASELINE  
> **Architecture generation:** V2  
> **Date:** 2026-09-28  
> **Scope:** PyIngestKit, PyTransformKit, PyWorkflowKit  
> **Compatibility posture:** clean-slate failure semantics  
> **Depends on:** PYKIT_ECOSYSTEM_V2_ARCHITECTURE_AND_CANONICAL_VOCABULARY.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_PUBLIC_API_DESIGN_PRINCIPLES.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_SHARED_CONTRACTS_AND_REFERENCE_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_EXECUTION_IDENTITY_AND_CORRELATION_MODEL.md

---

# 1. Purpose

This document defines the canonical V2 semantics for errors, failures, retryability, idempotency, timeout, cancellation, uncertain outcomes, reconciliation, recovery, replay and cross-framework retry ownership.

The central principle is:

> **Retry only at the layer that can correctly determine whether repeating the operation is safe.**

The model exists to prevent retry amplification such as:

~~~text
Workflow retry
    x
Ingestion retry
    x
Transformation retry
    x
Provider retry
~~~

where several layers repeat the same side effect without sharing one safety model.

---

# 2. Core distinctions

The ecosystem distinguishes:

~~~text
ERROR
FAILURE
OUTCOME
RETRY DECISION
RECOVERY
RECONCILIATION
REPLAY
~~~

An error is a detected exceptional condition.

A failure is a runtime operation that did not complete according to its contract.

An outcome is the known state of an execution.

A retry decision is the explicit decision to repeat an operation.

Recovery continues or reconstructs an existing execution.

Reconciliation determines the real outcome of an execution whose effect is uncertain.

Replay starts a new execution from preserved historical evidence or input.

These concepts MUST NOT be treated as synonyms.

---

# 3. Canonical failure categories

Every runtime-capable framework SHOULD classify failures through stable machine-readable categories.

~~~text
VALIDATION
CONFIGURATION
CAPABILITY
AUTHENTICATION
AUTHORIZATION
NOT_FOUND
CONFLICT
TRANSIENT
TIMEOUT
CANCELLED
RESOURCE_EXHAUSTED
RATE_LIMITED
INTEGRITY
CONTRACT_VIOLATION
SIDE_EFFECT_FAILED
UNKNOWN_OUTCOME
INTERNAL
EXTERNAL_PROVIDER
~~~

Framework-specific categories MAY refine this taxonomy.

Human-readable messages are diagnostic text, not stable machine contracts.

---

# 4. Root exception ownership

Each package owns one public root exception hierarchy.

~~~text
PyIngestKitError
PyTransformKitError
PyWorkflowKitError
~~~

Typical descendants include:

~~~text
PyIngestKitError
├── SourceAcquisitionError
├── RawPersistenceError
├── DecodeError
├── IngestionValidationError
├── DatasetVersionError
└── PublicationError

PyTransformKitError
├── InvalidExpressionError
├── SchemaResolutionError
├── PlanningError
├── UnsupportedCapabilityError
├── TransformationExecutionError
└── EngineContractViolation

PyWorkflowKitError
├── WorkflowDefinitionError
├── WorkflowPlanningError
├── TaskExecutionError
├── TaskTimeoutError
├── WorkflowCancelledError
└── RecoveryError
~~~

The ecosystem does not require one universal Python error superclass across all packages.

---

# 5. Stable failure evidence

Cross-framework decisions SHOULD use structured failure evidence.

Conceptually:

~~~text
FailureEvidence
    source_framework
    source_component?
    error_code
    category
    retryability
    uncertainty
    execution_reference?
    correlation_id?
    provider_code?
    message_summary?
    occurred_at?
    details?
    contract_version
~~~

FailureEvidence is durable evidence.

It is not a replacement for native in-process exceptions.

---

# 6. Retryability model

Retryability is not a simple boolean.

Canonical values are:

~~~text
RETRYABLE
NON_RETRYABLE
UNKNOWN
RETRYABLE_AFTER_RECONCILIATION
~~~

A retry decision MUST consider more than retryability metadata.

At minimum:

~~~text
failure category
side-effect state
idempotency
attempt count
retry budget
deadline
cancellation state
uncertainty
provider guidance
~~~

---

# 7. Retry ownership

Retry ownership is scoped by semantics.

~~~text
PyWorkflowKit
    owns workload-level retry

PyIngestKit
    may own bounded ingestion transport or storage retry

PyTransformKit
    may own bounded engine or provider retry
~~~

The same semantic operation MUST NOT be retried independently by multiple layers without explicit coordination.

---

# 8. Workflow retry

PyWorkflowKit owns TaskRun retry.

~~~text
TaskRun TR-17
│
├── TaskAttempt TA-1
│      └── TransformationExecution T-912 FAILED
│
└── TaskAttempt TA-2
       └── TransformationExecution T-913 SUCCEEDED
~~~

Workflow retry means:

~~~text
same WorkflowRunId
same TaskRunId
new TaskAttemptId
new downstream execution identity
~~~

unless the downstream system is explicitly resuming or reconciling the same execution.

---

# 9. PyIngestKit bounded retry

PyIngestKit MAY retry low-level operations within one IngestionRun when repeat safety is known.

Typical examples:

~~~text
immutable HTTP GET
object-store read
safe content-addressed lookup
provider read after transient disconnect
stable idempotent write supported by provider contract
~~~

Such retries remain inside one IngestionRun.

PyIngestKit MUST NOT silently retry the entire ingestion lifecycle when PyWorkflowKit already owns workload retry.

---

# 10. PyTransformKit bounded retry

PyTransformKit MAY retry low-level physical-engine operations when repeat safety is known.

Typical examples:

~~~text
read-only metadata request
read-only scan
safe connection establishment
provider query using explicit idempotency semantics
~~~

A write whose commit state is unknown MUST NOT be replayed blindly.

---

# 11. Provider retry awareness

HTTP clients, database drivers, cloud SDKs and execution engines may already retry internally.

Adapters MUST understand whether provider retry is enabled.

The effective retry chain SHOULD be inspectable.

Hidden retry stacking is prohibited.

---

# 12. Retry amplification

If four layers each retry three times, one logical operation can create:

~~~text
3 x 3 x 3 x 3 = 81 physical attempts
~~~

Therefore every retry policy MUST declare its failure domain.

Examples:

~~~text
HTTP_REQUEST
OBJECT_STORE_READ
OBJECT_STORE_WRITE
DATABASE_TRANSACTION
ENGINE_QUERY
INGESTION_STAGE
INGESTION_RUN
TRANSFORMATION_EXECUTION
TASK_RUN
~~~

A retry policy without an explicit failure domain is incomplete.

---

# 13. Idempotency model

Canonical idempotency classifications are:

~~~text
NATURALLY_IDEMPOTENT
KEYED_IDEMPOTENT
CONDITIONALLY_IDEMPOTENT
NON_IDEMPOTENT
UNKNOWN
~~~

Examples of naturally idempotent operations include deterministic planning, immutable reads and content-addressed lookups.

A keyed-idempotent operation is safe only when the provider contract actually honors the key.

Conditional idempotency depends on explicit preconditions such as compare-and-swap, create-if-absent, unique constraints or stable publication keys.

Automatic retry of NON_IDEMPOTENT or UNKNOWN side effects is prohibited by default.

---

# 14. Idempotency key scope

An idempotency key has an explicit semantic scope.

A TaskAttemptId is not automatically a valid publication idempotency key.

An IngestionRunId is not automatically a valid external provider idempotency key.

Reusing an identifier as an idempotency key is allowed only when the operation contract explicitly defines that mapping.

---

# 15. Outcome model

Runtime operations SHOULD distinguish:

~~~text
SUCCEEDED
FAILED
CANCELLED
TIMED_OUT
UNKNOWN_OUTCOME
REQUIRES_RECONCILIATION
~~~

Framework-specific states MAY refine these values.

UNKNOWN_OUTCOME and REQUIRES_RECONCILIATION are first-class states.

---

# 16. Known failure

A known failure means the system can establish that the intended operation did not succeed.

Examples:

~~~text
validation rejected before side effect
transaction rollback confirmed
provider rejected unsupported operation
request rejected before commit
~~~

Retry may then be evaluated normally.

---

# 17. Unknown outcome

UNKNOWN_OUTCOME means that the caller cannot prove whether the side effect occurred.

Canonical scenario:

~~~text
client sends write
    ↓
server may commit
    ↓
connection breaks
    ↓
client receives no final response
~~~

The correct outcome is not automatically FAILED.

The side effect may already exist.

---

# 18. Reconciliation

Reconciliation determines the actual state of uncertain work.

~~~text
UNKNOWN_OUTCOME
    ↓
RECONCILE
    ├── CONFIRMED_SUCCEEDED
    ├── CONFIRMED_FAILED
    └── STILL_UNKNOWN
~~~

Reconciliation is preferred over retry whenever repeating the operation may duplicate effects.

The domain/provider adapter that understands the side effect owns the reconciliation logic.

---

# 19. Reconciliation ownership

Canonical ownership examples:

~~~text
PyIngestKit
    reconciles publication and dataset-version side effects it owns

PyTransformKit adapter
    reconciles engine writes it owns

PyWorkflowKit
    coordinates task-level recovery and reconciliation
    but does not invent provider truth
~~~

WorkflowKit may ask an adapter what happened to an ExternalRunRef.

It MUST NOT infer provider success from absence of an exception alone.

---

# 20. Reconciliation result

A reconciliation contract SHOULD distinguish:

~~~text
CONFIRMED_SUCCEEDED
CONFIRMED_FAILED
STILL_UNKNOWN
NOT_FOUND
NOT_SUPPORTED
~~~

NOT_FOUND does not universally mean FAILED.

Eventually consistent systems may still require another reconciliation attempt.

---

# 21. Timeout

Timeout means a caller or runtime deadline expired.

It does not prove that the underlying operation stopped.

~~~text
client timeout
    !=
provider cancellation
    !=
known provider failure
~~~

A timeout after a side-effecting request may therefore become UNKNOWN_OUTCOME.

---

# 22. Cancellation

Cancellation is an explicit request to stop work.

Provider capability may produce:

~~~text
CANCELLED
CANCELLATION_REQUESTED
CANCELLATION_UNCONFIRMED
CANCELLATION_UNSUPPORTED
~~~

WorkflowKit MUST preserve this distinction when coordinating an external workload.

---

# 23. Recovery

Recovery resumes or reconstructs an existing execution after interruption.

Examples:

~~~text
reload WorkflowRun after crash
rebuild task readiness
reattach to external execution
continue from durable checkpoint
~~~

Recovery preserves execution identity.

It is not a new retry by default.

---

# 24. Resume

Resume is continuation of the same logical execution.

~~~text
WorkflowRun W-42 interrupted
    ↓
resume W-42
~~~

A new independent run is a rerun, not a resume.

---

# 25. Replay

Replay deliberately starts a new execution using preserved historical evidence.

Example:

~~~text
RAW artifact A-10
    ↓
replay
    ↓
IngestionRun I-205
~~~

Replay receives a new IngestionRunId unless the operation is actually recovery of the same incomplete run.

Replay provenance SHOULD reference the original evidence.

---

# 26. Rerun

Rerun creates a new execution from the same definition or plan.

~~~text
same WorkflowDefinition
    ↓
WorkflowRun W-42

rerun
    ↓
WorkflowRun W-99
~~~

Likewise:

~~~text
same TransformationPlan
    ↓
T-913
    ↓ rerun
T-1201
~~~

Rerun is not retry of the same attempt.

---

# 27. Deadline and retry budget

Retries MUST obey finite limits.

Supported dimensions may include:

~~~text
max_attempts
max_elapsed_time
overall_deadline
max_total_delay
provider quota budget
~~~

Unbounded automatic retry is prohibited.

An inner retry SHOULD NOT exceed the remaining deadline of an outer execution unless explicitly justified.

---

# 28. Backoff

Runtime implementations MAY support:

~~~text
fixed
linear
exponential
exponential with jitter
provider Retry-After
~~~

Jitter is recommended when many workers may fail simultaneously.

Provider Retry-After SHOULD be respected when available, subject to outer deadlines and safety rules.

---

# 29. RetryDecision

A retry-capable runtime SHOULD be able to record a structured decision.

Conceptually:

~~~text
RetryDecision
    decision
    reason
    attempt_number
    failure_category
    retryability
    uncertainty
    next_delay?
    reconciliation_required?
~~~

Canonical decision values:

~~~text
RETRY
DO_NOT_RETRY
RECONCILE
ABORT
CANCEL
ESCALATE
~~~

Retries must be visible control flow, not hidden behavior.

---

# 30. Workflow TaskAttempt outcomes

A TaskAttempt may end as:

~~~text
SUCCEEDED
FAILED
TIMED_OUT
CANCELLED
UNKNOWN_OUTCOME
~~~

TaskRun then applies workflow policy.

If a TaskAttempt is UNKNOWN_OUTCOME, WorkflowKit MUST consult provider evidence and reconciliation semantics before launching a new attempt when duplicate side effects are possible.

---

# 31. Ingestion lifecycle failure domains

PyIngestKit may distinguish failure by stage:

~~~text
ACQUIRE
PERSIST_RAW
DECODE
VALIDATE
VERSION
PUBLISH
~~~

Examples:

~~~text
DECODE deterministic failure
    usually NON_RETRYABLE

ACQUIRE transient connection failure
    potentially RETRYABLE

PUBLISH timeout after request
    possibly REQUIRES_RECONCILIATION
~~~

---

# 32. Transformation failure domains

PyTransformKit may distinguish:

~~~text
PLANNING
CAPABILITY_RESOLUTION
INPUT_BINDING
ENGINE_EXECUTION
OUTPUT_MATERIALIZATION
WRITE
RESULT_COLLECTION
~~~

Examples:

~~~text
invalid expression
    NON_RETRYABLE

unsupported capability
    NON_RETRYABLE

temporary engine connection failure
    potentially RETRYABLE

write timeout after submission
    potentially UNKNOWN_OUTCOME
~~~

---

# 33. Validation and configuration failures

Validation and configuration failures are normally non-retryable until inputs or configuration change.

Examples:

~~~text
missing required column
invalid expression type
cyclic workflow
unsupported plugin version
missing engine
invalid endpoint
~~~

Repeating the same operation under unchanged conditions is not recovery.

---

# 34. Authentication and authorization

Authentication failure may be retryable only when credential refresh is explicitly supported.

Authorization failure is normally NON_RETRYABLE.

Repeated retries MUST NOT be used as a permission-discovery mechanism.

---

# 35. Not-found semantics

NOT_FOUND is context-dependent.

~~~text
immutable artifact missing
    likely NON_RETRYABLE

eventually consistent object not visible yet
    potentially RETRYABLE

external run not found during reconciliation
    potentially STILL_UNKNOWN
~~~

The error category alone does not decide retry.

---

# 36. Conflict semantics

CONFLICT may represent:

- an idempotent success-equivalent state;
- a temporary concurrency conflict;
- a permanent semantic incompatibility.

Example:

~~~text
publication version key already exists
~~~

may indicate that the requested side effect already succeeded earlier.

Reconcile rather than assuming failure.

---

# 37. Rate limiting and resource exhaustion

RATE_LIMITED is commonly retryable after provider-directed delay.

RESOURCE_EXHAUSTED may be transient or persistent.

Examples:

~~~text
temporary connection-pool saturation
temporary worker shortage
disk full
memory insufficient
quota exhausted
~~~

Retry must not replace capacity management or backpressure.

---

# 38. Integrity failure

Integrity failures are usually deterministic.

Examples:

~~~text
checksum mismatch
corrupt RAW artifact
unexpected content fingerprint
~~~

Repeating processing of the same corrupted artifact is normally not useful.

Reacquisition is a separate decision.

---

# 39. Contract violation

A framework or provider violating a declared contract is NON_RETRYABLE by default.

Example:

~~~text
adapter claims capability SUPPORTED
but produces semantically invalid result
~~~

This is a correctness defect, not a transient operational failure.

---

# 40. External provider evidence

Provider errors SHOULD be normalized without losing original evidence.

Durable evidence may contain:

~~~text
stable PyKit error code
category
provider code
provider operation ID
safe message summary
retryability
uncertainty
~~~

In-process exception chaining SHOULD preserve the native provider exception where safe.

---

# 41. Partial success

Partial success is permitted only when the domain defines it precisely.

Examples:

~~~text
some partitions written
some publication targets completed
multi-output execution partially committed
~~~

A result MUST enumerate known completed and incomplete effects.

Generic PARTIAL_SUCCESS without effect details is insufficient.

---

# 42. Atomicity model

Side-effecting operations SHOULD declare their atomicity expectations:

~~~text
ATOMIC
BEST_EFFORT
MULTI_EFFECT
UNKNOWN
~~~

Retry and reconciliation depend on this.

A multi-effect operation cannot be considered retry-safe solely because one sub-operation is idempotent.

---

# 43. Compensation

Some side effects support compensation.

Examples:

~~~text
publish → unpublish
reserve → release
create → delete
~~~

Compensation is not equivalent to rollback unless the provider guarantees rollback semantics.

Compensation failure must itself be represented as evidence.

---

# 44. Workflow compensation

WorkflowKit MAY orchestrate compensation sequencing.

However:

~~~text
WorkflowKit owns sequencing
domain/provider owns compensation semantics
~~~

WorkflowKit does not invent how to reverse a PyIngestKit publication or an external provider side effect.

---

# 45. Checkpoints

Checkpoints MAY reduce recovery and replay cost.

Examples:

~~~text
PyWorkflowKit
    persisted completed task state

PyIngestKit
    RAW persisted checkpoint

PyTransformKit
    explicit materialized intermediate
~~~

A checkpoint does not automatically imply safe resume.

Checkpoint integrity and semantic validity must be defined.

---

# 46. Retry after checkpoint

Resume from checkpoint is allowed only when:

- checkpoint integrity is verified;
- upstream state remains valid;
- side-effect duplication is impossible or explicitly handled;
- the owning domain defines resume semantics.

Otherwise create a fresh execution.

---

# 47. Retry observability

Every retry SHOULD emit structured evidence.

Example:

~~~text
RetryScheduled
    execution_reference
    attempt_number
    reason
    delay
    correlation_id
~~~

Attempt histories MUST remain inspectable after eventual success.

---

# 48. Attempt accounting

Attempt counters are domain-specific.

~~~text
TaskAttempt number
    !=
provider request attempt
~~~

Preferred diagnostics:

~~~text
task_attempt_number = 2
provider_request_attempt = 4
~~~

These counters MUST NOT be merged into one ambiguous attempts field.

---

# 49. Nested retry disclosure

When nested retry is intentionally enabled, documentation and diagnostics MUST expose:

~~~text
outer retry owner
inner retry owner
failure domains
maximum amplification
deadline interaction
idempotency assumptions
~~~

Hidden nested retry is prohibited.

---

# 50. Circuit breakers and backpressure

Circuit breaking, concurrency limiting and backpressure are not retry.

They may produce states such as:

~~~text
WAITING_FOR_CAPACITY
THROTTLED
CIRCUIT_OPEN
QUEUED
~~~

Repeated retry must not be used as a substitute for proper flow control.

---

# 51. Poison input

Repeated deterministic failure for the same immutable input indicates poison input.

Examples:

~~~text
malformed CSV
corrupt artifact
invalid schema
unsupported expression
~~~

Retry SHOULD terminate early once deterministic failure is established.

---

# 52. Failure provenance

Failure evidence SHOULD preserve origin through the stack.

~~~text
Workflow TaskAttempt
    ↓
PyTransformKit adapter
    ↓
engine adapter
    ↓
external provider
~~~

The final diagnostic may retain:

~~~text
source_framework
source_component
provider
provider_code
provider_operation_id
correlation_id
~~~

without flattening everything into one generic RuntimeError.

---

# 53. Error wrapping rule

Errors SHOULD be wrapped when crossing a semantic boundary and the wrapper adds meaningful domain information.

Useful additions include:

- bounded-context meaning;
- stable error code;
- execution reference;
- retryability;
- uncertainty;
- safe diagnostic context.

Repeated wrapping at every helper function is discouraged.

---

# 54. Sensitive error data

Provider failures may contain:

- credentials;
- SQL text;
- signed URLs;
- paths;
- personal data;
- raw source records.

Persistent error evidence and logs MUST apply redaction.

Raw provider payloads are not automatically safe diagnostics.

---

# 55. WorkflowKit adapter responsibilities

A WorkflowKit adapter SHOULD translate provider outcomes into task-level evidence while preserving provider truth.

Conceptually:

~~~text
provider result
    ↓
ExternalRunRef
FailureEvidence
Uncertainty
Retryability
    ↓
TaskAttempt outcome
    ↓
TaskRetryPolicy
~~~

WorkflowKit owns the workload policy.

The adapter owns provider/domain factual mapping.

---

# 56. PyIngestKit adapter responsibilities

An ingestion adapter should know:

- acquisition safety;
- transport retry semantics;
- RAW persistence idempotency;
- publication idempotency;
- source consistency behavior;
- provider reconciliation.

These are ingestion semantics.

---

# 57. PyTransformKit adapter responsibilities

An engine adapter should know:

- read retry safety;
- query submission semantics;
- provider operation IDs;
- write idempotency;
- cancellation capabilities;
- outcome reconciliation;
- transient provider classifications.

These are engine/provider semantics.

---

# 58. Canonical safe layering

~~~text
WorkflowKit TaskRun
    owns workload retry
        ↓
TaskAttempt TA-1
        ↓
TransformationExecution T-1
    owns bounded provider retry only
        ↓
Provider operation Q-1
~~~

If T-1 fails with a known retryable failure:

~~~text
WorkflowKit may create TA-2
    ↓
new TransformationExecution T-2
~~~

If T-1 has an uncertain write outcome:

~~~text
reconcile T-1 first
~~~

before starting T-2.

---

# 59. Ingestion publication example

~~~text
IngestionRun I-500
    ↓
publish DatasetVersion V-20
    ↓
network timeout after request
~~~

Possible outcome:

~~~text
status = REQUIRES_RECONCILIATION
uncertainty = SIDE_EFFECT_MAY_HAVE_OCCURRED
~~~

Correct next step:

~~~text
query publication registry or target
    ↓
confirmed exists
    → SUCCEEDED

confirmed absent
    → retry may be considered
~~~

Blind duplicate publication is incorrect.

---

# 60. Transformation write example

~~~text
TransformationExecution T-900
    ↓
write output
    ↓
connection lost after commit request
~~~

If provider reconciliation is supported:

~~~text
REQUIRES_RECONCILIATION
    ↓
query provider state
~~~

If reconciliation is impossible, UNKNOWN_OUTCOME may require explicit operator policy.

---

# 61. Read-only example

~~~text
TransformationExecution T-100
    ↓
read immutable Parquet
    ↓
temporary network failure
~~~

A bounded retry within T-100 is reasonable when the input and read semantics are immutable and retry-safe.

---

# 62. Validation example

~~~text
TransformationPlan
    ↓
invalid typed expression
~~~

Classification:

~~~text
category = VALIDATION
retryability = NON_RETRYABLE
uncertainty = CERTAIN
~~~

No runtime retry is appropriate.

---

# 63. Workflow timeout example

~~~text
TaskAttempt TA-3
    ↓
external execution J-1 continues
    ↓
task deadline expires
~~~

If cancellation cannot be confirmed, a fresh TaskAttempt MUST NOT automatically start when J-1 may still create side effects.

The state may require reconciliation first.

---

# 64. Manual resolution

Operational tooling MAY support explicit manual resolution of uncertain executions.

Possible actions:

~~~text
confirm succeeded
confirm failed
resume reconciliation
abandon
~~~

Every manual action MUST create audit evidence containing actor, timestamp, reason, previous state, new state and target execution.

History must never be silently rewritten.

---

# 65. Failure trees

Complex failures MAY be represented structurally.

~~~text
WorkflowRunFailure
└── TaskRun TR-17
    └── TaskAttempt TA-2
        └── TransformationExecution T-913
            └── EngineFailure
                └── ProviderError
~~~

This preserves provenance better than concatenated messages.

Parallel executions may produce multiple failure branches.

The system MUST NOT arbitrarily discard all but one failure when multiple failures are semantically relevant.

---

# 66. Fail-fast

Fail-fast is an execution policy.

It answers whether remaining work should stop after failure.

It does not redefine the failure itself.

WorkflowKit owns workflow-level fail-fast behavior.

Transformation or ingestion runtimes may own local fail-fast semantics only within their bounded context.

---

# 67. Cancellation propagation

Cross-framework cancellation is explicit.

~~~text
Workflow cancellation
    ↓
Task cancellation
    ↓
adapter cancellation request
    ↓
provider response
~~~

The provider may return:

~~~text
CONFIRMED_CANCELLED
CANCELLATION_REQUESTED
CANCELLATION_UNSUPPORTED
CANCELLATION_UNCONFIRMED
~~~

Workflow state must preserve this evidence.

---

# 68. Deadline propagation

Outer deadlines SHOULD propagate inward.

~~~text
TaskAttempt deadline
    ↓
Transformation/Ingestion runtime deadline
    ↓
provider timeout
~~~

Inner timeouts should not exceed the remaining outer deadline unless explicitly justified.

---

# 69. Failure persistence

Durable runtimes SHOULD persist enough evidence for:

- restart;
- diagnosis;
- reconciliation;
- retry decision reconstruction;
- audit.

Persisted evidence MUST NOT require deserializing arbitrary Python exception objects.

---

# 70. Error and result duality

A synchronous API MAY raise an exception while also persisting execution state.

Example:

~~~text
TransformationExecution T-913
    persisted FAILED

caller receives TransformationExecutionError
    referencing T-913
~~~

Once an execution identity exists, the durable outcome SHOULD remain queryable independently from the caller stack.

---

# 71. Preflight failure

Preflight happens before the runtime commits to an execution.

Examples:

~~~text
engine unavailable
invalid runtime configuration
unresolvable credential reference
unsupported capability
~~~

If no execution exists and no side effect occurred, preflight MAY fail without allocating an execution ID.

The PRE-RUN versus RUN-CREATED boundary must be documented.

---

# 72. Architecture constraints

Architecture tests SHOULD prevent:

- PyWorkflowKit core importing provider-specific retry implementations;
- PyTransformKit core importing WorkflowKit TaskRetryPolicy;
- PyIngestKit core importing WorkflowKit task state;
- generic shared BaseRetryManager abstractions without proven semantics;
- integration adapters silently retrying whole sibling executions;
- automatic retry of UNKNOWN_OUTCOME without reconciliation policy.

---

# 73. Cross-framework conformance scenarios

The ecosystem SHOULD test at least:

~~~text
WorkflowKit → IngestKit transient acquisition failure
WorkflowKit → IngestKit uncertain publication
WorkflowKit → TransformKit transient read failure
WorkflowKit → TransformKit uncertain write
WorkflowKit cancellation → provider cancellation
provider timeout → reconciliation
retry exhausted → preserved failure evidence
~~~

Each scenario should verify identity, correlation, retry owner, uncertainty, attempt count and final outcome.

---

# 74. Acceptance criteria

This model is correctly implemented when:

1. errors have stable machine-readable categories;
2. root exception ownership remains per framework;
3. retryability is richer than a boolean;
4. UNKNOWN_OUTCOME is first-class;
5. reconciliation is available for uncertain side effects where provider semantics permit it;
6. WorkflowKit owns workload retry;
7. PyIngestKit retries only bounded safe ingestion operations internally;
8. PyTransformKit retries only bounded safe engine operations internally;
9. provider retries are included in the effective retry model;
10. retry policies declare failure domains;
11. idempotency classification is explicit;
12. timeout does not imply provider cancellation;
13. cancellation request and cancellation confirmation are distinct;
14. recovery preserves execution identity;
15. replay and rerun create new identities;
16. failure evidence preserves execution and correlation references;
17. retry exhaustion preserves final root evidence;
18. uncertain side effects are reconciled before unsafe replay;
19. nested retries expose amplification and deadlines;
20. producer-consumer tests validate failure propagation.

---

# 75. Normative invariants

### FAIL-INV-01 — One semantic retry owner per failure domain

Multiple layers do not independently own the same retry scope.

### FAIL-INV-02 — Unknown outcome is not ordinary failure

When side effects may have occurred, uncertainty is preserved.

### FAIL-INV-03 — Reconcile before unsafe retry

Potentially committed side effects are reconciled before repetition when possible.

### FAIL-INV-04 — Idempotency must be proven

Generating a key does not create provider idempotency.

### FAIL-INV-05 — Timeout does not imply cancellation

Underlying work may still be active.

### FAIL-INV-06 — Recovery is not rerun

Recovery preserves execution identity.

### FAIL-INV-07 — Replay is a new execution

Historical input reuse does not imply identity reuse.

### FAIL-INV-08 — Failure evidence preserves origin

Adapters do not erase bounded-context or provider provenance.

### FAIL-INV-09 — Retry budgets are finite

Unbounded automatic retry is prohibited.

### FAIL-INV-10 — Validation failures are not transient by default

Retry requires changed conditions.

### FAIL-INV-11 — Provider retries belong to the effective retry chain

SDK and driver retries must not remain invisible.

### FAIL-INV-12 — Manual resolution is auditable

Human override never rewrites history silently.

---

# 76. Canonical decision flow

~~~text
Operation fails or response is lost
        ↓
Classify failure
        ↓
Determine uncertainty
        ↓
Could a side effect already exist?
        │
        ├── YES
        │     ↓
        │  Can provider/domain reconcile?
        │     │
        │     ├── YES
        │     │     ↓
        │     │  RECONCILE
        │     │     ├── confirmed success → SUCCEEDED
        │     │     ├── confirmed failure → evaluate retry
        │     │     └── still unknown → REQUIRES_RECONCILIATION
        │     │
        │     └── NO
        │           ↓
        │       UNKNOWN_OUTCOME
        │       operator/domain policy
        │
        └── NO
              ↓
        Is repetition safe?
              │
              ├── NO → FAILED
              │
              └── YES
                    ↓
              Retry budget available?
                    │
                    ├── NO → FAILED
                    └── YES → RETRY
~~~

This decision flow is normative at the semantic level.

---

# 77. Final architecture statement

The PyKit V2 ecosystem does not treat retry as a generic convenience feature.

Retry is a semantic decision based on:

~~~text
failure domain
idempotency
side-effect certainty
retry ownership
deadline
attempt budget
provider evidence
~~~

The canonical division is:

~~~text
PyWorkflowKit
    retries workloads

PyIngestKit
    retries bounded ingestion operations it can prove safe

PyTransformKit
    retries bounded engine operations it can prove safe
~~~

When the outcome of a side effect is uncertain:

~~~text
DO NOT GUESS
    ↓
PRESERVE UNCERTAINTY
    ↓
RECONCILE
    ↓
ONLY THEN DECIDE WHETHER TO RETRY
~~~

The central rule is:

> **A failed response is not always a failed operation, and a retry is not safe merely because it is technically possible.**

This specification is the baseline for:

~~~text
PYKIT_ECOSYSTEM_V2_DATASET_RESOURCE_AND_ARTIFACT_INTEROPERABILITY.md
PYKIT_ECOSYSTEM_V2_LINEAGE_PROVENANCE_AND_TRACEABILITY_MODEL.md
PYKIT_ECOSYSTEM_V2_OBSERVABILITY_EVENTS_AND_TELEMETRY_MODEL.md
PYKIT_ECOSYSTEM_V2_INTEGRATION_AND_ANTI_CORRUPTION_LAYER_MODEL.md
~~~
