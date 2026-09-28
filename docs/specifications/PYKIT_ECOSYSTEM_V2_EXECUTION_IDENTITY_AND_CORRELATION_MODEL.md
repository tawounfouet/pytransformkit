# PyKit Ecosystem V2 — Execution Identity and Correlation Model

> **Status:** NORMATIVE EXECUTION IDENTITY BASELINE  
> **Architecture generation:** V2  
> **Date:** 2026-09-28  
> **Scope:** PyIngestKit, PyTransformKit, PyWorkflowKit  
> **Compatibility posture:** clean-slate execution identity model; no legacy identifier compatibility requirement  
> **Depends on:** PYKIT_ECOSYSTEM_V2_ARCHITECTURE_AND_CANONICAL_VOCABULARY.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_PUBLIC_API_DESIGN_PRINCIPLES.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_SHARED_CONTRACTS_AND_REFERENCE_MODEL.md  
> **Related:** PYTRANSFORMKIT_PYINGESTKIT_PYWORKFLOWKIT_BOUNDARIES_AND_INTEGRATION.md

---

# 1. Purpose

This document defines how execution identity, parent/child relationships, correlation, causation and tracing work across the PyKit V2 ecosystem.

The ecosystem contains several legitimate runtime identities:

~~~text
WorkflowRun
TaskRun
TaskAttempt

IngestionRun

TransformationExecution

external provider executions
~~~

These identities MUST remain distinct.

The governing principle is:

> **Correlate executions across bounded contexts; never merge their identities.**

---

# 2. Why execution identity needs its own model

A composed application can produce many runtime records for one business operation.

~~~text
WorkflowRun W-42
│
├── TaskRun TR-10
│      └── IngestionRun I-288
│
├── TaskRun TR-11
│      └── IngestionRun I-289
│
├── TaskRun TR-12
│      └── TransformationExecution T-913
│
└── TaskRun TR-13
       └── IngestionRun I-290
~~~

All executions may belong to one broader operation while still having different lifecycle, persistence, retry and recovery semantics.

A universal RunId would hide those differences.

V2 therefore separates execution identity from correlation identity.

---

# 3. Canonical identity taxonomy

The canonical native execution identities are:

~~~text
PyWorkflowKit
    WorkflowRunId
    TaskRunId
    TaskAttemptId

PyIngestKit
    IngestionRunId

PyTransformKit
    TransformationExecutionId
~~~

Additional provider-specific identifiers may exist:

~~~text
SnowflakeQueryId
SparkApplicationId
HttpRequestId
DatabaseTransactionId
ExternalJobId
~~~

They remain provider-owned.

---

# 4. Four identity concepts

The ecosystem distinguishes:

~~~text
DOMAIN EXECUTION ID
CORRELATION ID
CAUSATION ID
TRACE ID
~~~

Their meanings are different.

## Domain execution ID

Identifies one runtime entity inside its owning bounded context.

## Correlation ID

Groups related work belonging to one broader operation.

## Causation ID

Identifies the immediate operation or event that triggered another operation.

## Trace ID

Belongs to distributed observability infrastructure.

These concepts MUST NOT be used interchangeably.

---

# 5. WorkflowRunId

WorkflowRunId identifies one execution of one WorkflowDefinition.

~~~text
WorkflowDefinition
       ↓ run
WorkflowRun
       ↓
WorkflowRunId
~~~

It remains authoritative for:

- workflow state;
- workflow start/end;
- task membership;
- workflow cancellation;
- workflow recovery;
- workflow resume;
- workflow-level evidence.

Sibling frameworks may retain the ID for correlation but do not own workflow state.

---

# 6. TaskRunId

TaskRunId identifies one logical task runtime inside a WorkflowRun.

~~~text
WorkflowRun W-42
    ↓
TaskDefinition transform_customers
    ↓
TaskRun TR-17
~~~

TaskRun is a logical execution lifecycle and may contain multiple attempts.

Therefore:

~~~text
TaskRunId
    !=
TaskAttemptId
~~~

---

# 7. TaskAttemptId

TaskAttemptId identifies one concrete execution attempt.

~~~text
TaskRun TR-17
│
├── TaskAttempt TA-1  FAILED
├── TaskAttempt TA-2  FAILED
└── TaskAttempt TA-3  SUCCEEDED
~~~

A task retry creates a new TaskAttemptId.

It normally preserves the TaskRunId.

---

# 8. IngestionRunId

IngestionRunId identifies one PyIngestKit ingestion lifecycle execution.

~~~text
IngestionDefinition customers
        ↓
IngestionRuntime.run()
        ↓
IngestionRun I-288
~~~

It remains authoritative for:

- acquisition;
- RAW evidence;
- decode activity;
- ingestion validation;
- DatasetVersion creation;
- publication evidence;
- ingestion-specific recovery/reconciliation.

PyWorkflowKit may correlate this with a TaskRun or TaskAttempt.

It MUST NOT replace IngestionRunId with a workflow identifier.

---

# 9. TransformationExecutionId

TransformationExecutionId identifies one PyTransformKit computation.

~~~text
TransformationPlan
        ↓
TransformationRuntime.execute()
        ↓
TransformationExecution T-913
~~~

It remains authoritative for:

- chosen engine;
- logical/physical planning evidence;
- transformation diagnostics;
- output bindings;
- engine-level execution evidence;
- TransformationResult.

The term Execution is intentional and distinct from WorkflowRun and IngestionRun.

---

# 10. External provider identity

External systems may expose native execution IDs.

Examples:

~~~text
Snowflake query_id
Spark application_id
Databricks run_id
HTTP request_id
database transaction_id
cloud batch job_id
~~~

These identifiers remain provider-owned.

They may be represented through ExternalRunRef or provider-specific references.

PyKit MUST NOT rename them into PyKit-native execution identities.

---

# 11. Identifier encoding

The architecture does not mandate one physical encoding.

Implementations MAY use:

- UUIDv4;
- UUIDv7;
- ULID;
- opaque random IDs;
- database-generated IDs;
- another collision-resistant scheme.

Requirements:

- stable after creation;
- opaque to consumers;
- serializable;
- unique within declared scope;
- no secrets;
- no required storage topology encoded inside the ID.

Human-readable prefixes such as wf_, tr_, ta_, ing_ or tx_ MAY be used for diagnostics but MUST NOT be the sole type system.

---

# 12. Identity immutability

Execution IDs are immutable after allocation.

State changes do not change identity.

~~~text
TransformationExecution T-913

PENDING
  ↓
RUNNING
  ↓
SUCCEEDED
~~~

remains T-913 throughout.

---

# 13. CorrelationId

CorrelationId groups executions that belong to one broader operation.

~~~text
Correlation C-42
│
├── WorkflowRun W-42
├── IngestionRun I-288
├── IngestionRun I-289
├── TransformationExecution T-913
└── IngestionRun I-290
~~~

CorrelationId SHOULD be opaque and portable.

It may originate from:

- PyWorkflowKit;
- an application;
- an API request;
- a CLI invocation;
- an upstream platform.

The first runtime boundary MAY create one when none exists.

---

# 14. Correlation propagation

When one operation starts another inside the same broader operation:

~~~text
parent.correlation_id
        ↓ propagate unchanged
child.correlation_id
~~~

Example:

~~~text
WorkflowRun W-42
correlation_id = C-42

TaskRun TR-17
correlation_id = C-42

TransformationExecution T-913
correlation_id = C-42
~~~

The CorrelationId remains stable.

---

# 15. Correlation does not imply parenthood

Two executions may share a correlation ID without one causing the other.

~~~text
WorkflowRun W-42
├── TaskRun TR-10
│      └── IngestionRun I-288
└── TaskRun TR-11
       └── IngestionRun I-289
~~~

Both ingestion runs may share C-42.

Neither caused the other.

Direct causation is modeled separately.

---

# 16. CausationId

CausationId identifies the immediate triggering entity.

~~~text
TaskAttempt TA-3
      ↓ invokes
TransformationExecution T-913

T-913.causation_id = TA-3
~~~

A causation chain can reconstruct:

~~~text
API request R-1
    ↓
WorkflowRun W-42
    ↓
TaskRun TR-17
    ↓
TaskAttempt TA-3
    ↓
TransformationExecution T-913
    ↓
Snowflake query Q-88
~~~

All may share one CorrelationId.

---

# 17. ParentExecutionId

ParentExecutionId MAY be used when hierarchical nesting must be represented explicitly.

Parenthood and causation are not always identical.

Example:

~~~text
TaskAttempt TA-3
    parent_execution_id = TR-17
    causation_id        = RetryScheduledEvent E-8
~~~

Implementations SHOULD avoid redundant fields when one relationship is sufficient.

---

# 18. CorrelationContext

CorrelationContext is the portable DTO used to propagate execution relationships.

Conceptually:

~~~text
CorrelationContext
    correlation_id
    causation_id?
    parent_execution_id?

    workflow_run_id?
    task_run_id?
    task_attempt_id?

    ingestion_run_id?
    transformation_execution_id?

    trace_id?
    span_id?
~~~

Fields not relevant to a boundary remain absent.

CorrelationContext does not replace native domain IDs.

---

# 19. Workflow correlation context

PyWorkflowKit SHOULD propagate correlation metadata into each task execution.

Conceptually:

~~~text
Workflow execution context
    correlation_id
    workflow_run_id
    task_run_id
    task_attempt_id
    causation_id?
    trace_id?
~~~

Provider adapters enrich this context with external execution references after invocation.

---

# 20. Ingestion correlation context

PyIngestKit SHOULD accept optional upstream correlation metadata without requiring PyWorkflowKit.

~~~text
IngestionContext
    correlation_id
    causation_id?
    workflow_run_id?
    task_run_id?
    task_attempt_id?
~~~

Workflow fields are optional boundary metadata, not core PyIngestKit domain requirements.

---

# 21. Transformation correlation context

PyTransformKit SHOULD also accept optional correlation metadata.

~~~text
TransformationContext
    correlation_id
    causation_id?
    workflow_run_id?
    task_run_id?
    task_attempt_id?
    ingestion_run_id?
~~~

PyTransformKit does not need to import sibling runtime classes to retain these references.

---

# 22. CorrelationContext portability

CorrelationContext MUST be:

- immutable;
- serializable;
- side-effect free;
- safe to propagate;
- free from active runtime resources.

It SHOULD NOT contain complete WorkflowRun, TaskRun, IngestionRun or TransformationExecution objects.

---

# 23. Trace identity

TraceId and SpanId belong to observability.

They MAY be included in CorrelationContext.

They MUST NOT replace durable domain identities.

~~~text
trace_id
    !=
workflow_run_id
    !=
ingestion_run_id
    !=
transformation_execution_id
~~~

A tracing backend is optional; domain identity is not.

---

# 24. Definition identity versus execution identity

Definition/plan identity and runtime identity remain separate.

~~~text
workflow_definition_id
    !=
workflow_run_id

ingestion_definition_id
    !=
ingestion_run_id

transformation_plan_fingerprint
    !=
transformation_execution_id
~~~

The same definition can produce many executions.

Example:

~~~text
WorkflowDefinition daily_customer_mart v3
    ↓
WorkflowRun W-42
WorkflowRun W-43
WorkflowRun W-44
~~~

---

# 25. Same plan, different execution

Executing the same TransformationPlan twice produces distinct execution IDs.

~~~text
plan_fingerprint = P-55

TransformationExecution T-1
TransformationExecution T-2
~~~

Plan identity proves equivalent declared computation.

Execution identity proves distinct runtime occurrence.

---

# 26. Retry identity semantics

Retry behavior is layer-specific.

## Workflow task retry

~~~text
same WorkflowRunId
same TaskRunId
new TaskAttemptId
~~~

## Workflow retry invokes PyTransformKit again

~~~text
same TaskRunId
new TaskAttemptId
new TransformationExecutionId
~~~

## Internal provider retry inside one transformation execution

Normally:

~~~text
same TransformationExecutionId
new provider request/query ID
~~~

if it remains one semantic transformation execution.

---

# 27. Ingestion retry identity

A bounded transport retry internal to one IngestionRun normally preserves:

~~~text
same IngestionRunId
~~~

while provider request IDs may change.

If WorkflowKit starts a fresh ingestion lifecycle on a new TaskAttempt:

~~~text
new TaskAttemptId
new IngestionRunId
~~~

unless PyIngestKit explicitly resumes/reconciles the existing ingestion execution.

---

# 28. Recovery identity

Recovery reconstructs or reconciles an existing execution.

It MUST NOT invent a replacement identity merely because a process restarted.

~~~text
process crash
    ↓
reload WorkflowRun W-42
    ↓
reconcile TaskRun TR-17
~~~

W-42 and TR-17 remain authoritative.

---

# 29. Resume identity

Resume normally preserves the existing execution identity.

For example:

~~~text
resume WorkflowRun W-42
~~~

continues W-42 rather than producing W-43.

A brand-new rerun is different and receives new runtime identities.

---

# 30. Replay identity

Replay is distinct from recovery.

A PyIngestKit replay from preserved RAW normally creates a new IngestionRunId:

~~~text
original IngestionRun I-100
replay   IngestionRun I-205
~~~

with provenance linking the replay to the source evidence and/or original run.

---

# 31. Correlation across asynchronous boundaries

When work crosses queues, processes, hosts, containers, subprocesses or external services, CorrelationContext SHOULD be serialized explicitly.

Process-local context variables alone are insufficient as a durable boundary contract.

---

# 32. Python contextvars

Python contextvars MAY provide in-process ergonomics.

Canonical direction:

~~~text
explicit CorrelationContext
        ↓
runtime binds local context
        ↓
logs/events inherit identifiers
~~~

Contextvars are implementation support, not the durable source of truth.

---

# 33. Threads, processes and async tasks

Supported executors MUST define how context propagates through:

~~~text
thread
process
subprocess
async task
~~~

Implicit propagation MUST NOT be assumed.

Propagation behavior should be explicit and tested.

---

# 34. Subprocess propagation

A subprocess MAY receive correlation metadata through an explicit channel such as:

- environment variables;
- stdin protocol;
- command metadata;
- manifest;
- IPC.

No secret material should be added merely to support correlation.

---

# 35. External provider correlation

Adapters MAY attach PyKit identifiers to provider-native observability fields.

Example:

~~~text
Snowflake QUERY_TAG
    correlation_id
    workflow_run_id
    task_run_id
    transformation_execution_id
~~~

Such tagging improves diagnosis.

It does not transfer execution ownership to the external provider.

---

# 36. Logging context

Each framework SHOULD enrich logs with relevant IDs when available.

Example:

~~~text
correlation_id=C-42
workflow_run_id=W-42
task_run_id=TR-17
task_attempt_id=TA-3
transformation_execution_id=T-913
~~~

Only identifiers relevant to the current scope need to be present.

---

# 37. Event identity

Durable runtime events SHOULD receive their own EventId.

~~~text
Event E-100
    type = TaskAttemptStarted
    workflow_run_id = W-42
    task_run_id = TR-17
    task_attempt_id = TA-3
    correlation_id = C-42
~~~

EventId is distinct from execution identity.

---

# 38. Event causation

Events MAY use correlation and causation fields.

~~~text
TaskAttemptFailed E-200
        ↓ causes
RetryScheduled E-201
        ↓ causes
TaskAttempt TA-4
~~~

This supports audit reconstruction without timestamp guessing.

---

# 39. Command/request identity

If asynchronous runtimes introduce command objects, command identity is separate.

~~~text
StartWorkflowCommand CMD-1
    ↓
WorkflowRun W-42
~~~

Possible command metadata:

~~~text
command_id
idempotency_key
correlation_id
causation_id
~~~

CommandId is not WorkflowRunId.

---

# 40. Idempotency identity

IdempotencyKey answers whether a logically equivalent request should produce duplicate side effects.

It is not an execution ID.

~~~text
same idempotency key
    may map to the same durable outcome

new retry attempt
    still has a new TaskAttemptId
~~~

Idempotency scope MUST be explicit.

---

# 41. Persistence ownership

Each framework persists its own execution IDs.

Conceptually:

~~~text
PyWorkflowKit store
    WorkflowRunId
    TaskRunId
    TaskAttemptId
    ExternalRunRef
    CorrelationId

PyIngestKit store
    IngestionRunId
    CorrelationId
    optional upstream refs

PyTransformKit evidence
    TransformationExecutionId
    CorrelationId
    optional upstream refs
~~~

A shared cross-framework database is not required.

---

# 42. Cross-framework referential integrity

Inside one framework, native relations MAY use database foreign keys.

Across frameworks, use portable external references by default.

Preferred:

~~~text
TaskRun.external_run_ref
~~~

rather than WorkflowKit requiring a foreign key to a PyIngestKit internal persistence table.

---

# 43. Result identity contract

Runtime results SHOULD expose native execution identity plus correlation.

~~~text
IngestionResult
    ingestion_run_id
    correlation_id
    output references

TransformationResult
    transformation_execution_id
    correlation_id
    output references

WorkflowResult
    workflow_run_id
    correlation_id
    terminal status
~~~

This enables composition without identity collapse.

---

# 44. Execution references

When execution identity crosses a framework boundary, it SHOULD use an explicit reference:

~~~text
IngestionExecutionReference
TransformationExecutionReference
WorkflowExecutionReference
ExternalRunRef
~~~

This is preferred over passing unqualified strings.

---

# 45. ExternalRunRef mapping

WorkflowKit may map provider-native PyKit executions into:

~~~text
ExternalRunRef
    provider
    external_run_id
    kind
    contract_version
~~~

Example:

~~~text
IngestionRunId I-288
    ↓
ExternalRunRef(
    provider="pyingestkit",
    external_run_id="I-288"
)

TransformationExecutionId T-913
    ↓
ExternalRunRef(
    provider="pytransformkit",
    external_run_id="T-913"
)
~~~

Provider identity remains authoritative.

---

# 46. One TaskAttempt may have multiple external runs

A TaskAttempt MAY invoke multiple provider executions.

~~~text
TaskAttempt TA-3
│
├── IngestionRun I-288
├── TransformationExecution T-913
└── external validation job X-9
~~~

Therefore the architecture MUST NOT assume exactly one ExternalRunRef per attempt.

---

# 47. Execution relationship types

When relationship semantics matter, a future ExecutionLink MAY represent:

~~~text
CAUSES
PARENT_OF
RETRIES
RESUMES
REPLAYS
OBSERVES
RECONCILES
DERIVES_EVIDENCE_FROM
~~~

Do not infer CAUSES merely because one execution references another.

---

# 48. Execution identity versus data lineage

Execution correlation is not data lineage.

~~~text
TransformationExecution T-913
    consumed DatasetVersion customers@52
~~~

is runtime/input evidence.

~~~text
customer_id → customer_key
~~~

is logical field lineage.

The IDs can connect both views, but the semantics remain distinct.

---

# 49. Execution identity versus artifact provenance

Likewise:

~~~text
IngestionRun I-288
    produced RAW artifact A-12
~~~

does not make ArtifactId an execution identity.

Execution, artifact and data identities remain separate.

---

# 50. Status ownership

Every execution type owns its state machine.

~~~text
WorkflowRunStatus
TaskRunStatus
TaskAttemptStatus
IngestionRunStatus
TransformationExecutionStatus
~~~

A correlation layer MUST NOT invent one universal authoritative Status.

Applications MAY derive aggregate status for presentation, but that aggregate is a projection with its own documented rule.

---

# 51. Error correlation

Errors SHOULD include native execution identity and CorrelationId when available.

~~~text
TransformationExecutionError
    transformation_execution_id = T-913
    correlation_id = C-42
    error_code = ENGINE_CAPABILITY_UNSUPPORTED
~~~

Machine consumers should not rely on parsing human-readable error messages.

---

# 52. Uncertain outcome identity

UNKNOWN_OUTCOME or REQUIRES_RECONCILIATION remains attached to the original execution ID.

Do not allocate a replacement ID merely to hide uncertainty.

~~~text
TransformationExecution T-913
status = UNKNOWN_OUTCOME
~~~

Reconciliation acts on T-913.

---

# 53. Cancellation and timeout

Cancellation and timeout change state, not identity.

~~~text
WorkflowRun W-42
RUNNING
  ↓ cancel
CANCELLED
~~~

A subsequent retry may create new attempt/provider execution IDs, but the timed-out or cancelled execution keeps its original identity.

---

# 54. Fan-out

Fan-out preserves the broad correlation.

~~~text
TaskRun TR-10
    ↓

TransformationExecution T-1
TransformationExecution T-2
TransformationExecution T-3

all correlation_id = C-42
~~~

Every execution still receives a unique native ID.

---

# 55. Fan-in

When multiple related branches join, the existing CorrelationId may be preserved.

When unrelated correlation groups are intentionally merged, the new operation SHOULD create a new CorrelationId and retain explicit upstream references rather than arbitrarily choosing one old correlation.

---

# 56. Schedule identity

If scheduling is introduced, schedule identity remains separate.

~~~text
ScheduleId S-1
    ↓ triggers
WorkflowRun W-42
WorkflowRun W-43
WorkflowRun W-44
~~~

ScheduleId is not WorkflowRunId.

---

# 57. Tenant/workspace identity

Future TenantId or WorkspaceId values qualify ownership scope.

They MUST NOT be overloaded into execution IDs.

If uniqueness is tenant-scoped, the contract must say so explicitly.

---

# 58. Security

Possession of an execution ID MUST NOT imply authorization to inspect that execution.

Execution IDs are identifiers, not access tokens.

Authorization remains separate.

Identifiers SHOULD be opaque and non-sensitive.

Avoid embedding user emails, credentials, tokens or business payloads.

---

# 59. Serialization

Execution/correlation contracts MUST serialize without relying on Python object identity.

Conceptual shape:

~~~json
{
  "contract": "pykit.correlation_context",
  "contract_version": 1,
  "correlation_id": "C-42",
  "workflow_run_id": "W-42",
  "task_run_id": "TR-17",
  "task_attempt_id": "TA-3",
  "transformation_execution_id": "T-913"
}
~~~

Exact wire format belongs to PYKIT_ECOSYSTEM_V2_SERIALIZATION_AND_WIRE_CONTRACTS.md.

---

# 60. Time and sequence fields

Timestamps are useful execution evidence but are not identities.

Use timezone-aware values such as:

~~~text
created_at
started_at
finished_at
~~~

TaskAttempt MAY also expose attempt_number.

~~~text
attempt_number = 3
~~~

AttemptNumber is ordinal metadata, not a substitute for TaskAttemptId.

---

# 61. Identity allocation timing

An execution ID SHOULD be allocated before meaningful runtime side effects start.

Preferred sequence:

~~~text
allocate execution identity
        ↓
persist initial evidence
        ↓
perform external work
~~~

This allows startup failures and uncertain outcomes to remain traceable.

Preflight failures that occur before an execution exists MAY return without allocating a runtime ID; the PRE-RUN/RUN-CREATED boundary must be documented.

---

# 62. Canonical composed example

~~~text
Correlation C-42
│
└── WorkflowRun W-42
    │
    ├── TaskRun TR-10
    │   └── TaskAttempt TA-10.1
    │       └── IngestionRun I-288
    │           └── HTTP request H-300
    │
    ├── TaskRun TR-11
    │   └── TaskAttempt TA-11.1
    │       └── IngestionRun I-289
    │
    ├── TaskRun TR-12
    │   ├── TaskAttempt TA-12.1
    │   │   └── TransformationExecution T-912 FAILED
    │   │
    │   └── TaskAttempt TA-12.2
    │       └── TransformationExecution T-913 SUCCEEDED
    │           └── SnowflakeQuery Q-88
    │
    └── TaskRun TR-13
        └── TaskAttempt TA-13.1
            └── IngestionRun I-290
~~~

This demonstrates one correlation story while preserving every native execution identity.

---

# 63. Canonical correlation table

| Concept | Owner | Meaning | Retry behavior |
|---|---|---|---|
| CorrelationId | initiating operation / propagated | broad operation grouping | preserved |
| WorkflowRunId | PyWorkflowKit | one workflow execution | preserved through recovery |
| TaskRunId | PyWorkflowKit | one logical task run | preserved across attempts |
| TaskAttemptId | PyWorkflowKit | one concrete attempt | new per attempt |
| IngestionRunId | PyIngestKit | one ingestion lifecycle execution | fresh for new lifecycle; preserved for recovery |
| TransformationExecutionId | PyTransformKit | one transformation execution | fresh for new execution |
| External provider ID | provider | provider-owned operation | provider-specific |
| TraceId | observability | distributed trace | propagated where configured |

---

# 64. Anti-patterns

Rejected:

~~~text
one universal RunId
~~~

Rejected:

~~~text
TransformationExecutionId = TaskRunId
~~~

Rejected:

~~~text
Workflow C-1
  ↓
Ingest C-2
  ↓
Transform C-3
~~~

when all three belong to one operation.

Rejected:

~~~text
TraceId used as durable domain execution ID
~~~

Rejected:

~~~text
causation inferred only from timestamps
~~~

Rejected:

~~~text
execution IDs containing secrets or personal payloads
~~~

---

# 65. Public API direction

Runtime APIs SHOULD permit explicit correlation injection.

Illustrative:

~~~python
correlation = CorrelationContext(
    correlation_id="C-42",
    causation_id="TA-3",
)

result = transformation_runtime.execute(
    plan,
    correlation=correlation,
)
~~~

Exact signatures remain framework-specific.

When no incoming context exists, a runtime may create a new CorrelationId.

---

# 66. CLI and notebook behavior

CLI and notebook executions SHOULD remain traceable.

A CLI may generate a CorrelationId and expose it in human/machine output.

Notebook runtime executions SHOULD also produce native execution IDs and correlation where execution evidence exists.

Interactive use must not imply untraceable use.

---

# 67. Observability requirements

Execution-capable frameworks SHOULD make native IDs available to:

- structured logs;
- traces;
- events;
- result objects;
- manifests;
- diagnostics.

High-cardinality execution IDs SHOULD NOT be blindly used as metrics labels.

Use logs/traces/events for exact execution identity and metrics for stable low-cardinality dimensions.

---

# 68. Audit requirements

Audit records SHOULD preserve, where applicable:

- native execution ID;
- CorrelationId;
- CausationId;
- actor/principal reference;
- timestamp;
- action;
- target reference;
- outcome.

Audit identity itself remains separate from runtime identity.

---

# 69. Testing requirements

Each framework MUST test:

- unique identity allocation;
- identity immutability;
- correlation creation;
- correlation propagation;
- causation propagation;
- retry identity rules;
- recovery identity rules;
- serialization round-trip;
- concurrency-boundary propagation;
- adapter mapping;
- error correlation.

---

# 70. Cross-framework conformance scenarios

The ecosystem SHOULD test:

~~~text
WorkflowKit → IngestKit
WorkflowKit → TransformKit
IngestKit → TransformKit
TransformKit → IngestKit publication
~~~

For each scenario verify:

- CorrelationId preserved;
- causation linked correctly;
- native execution IDs remain distinct;
- ExternalRunRef maps to the provider ID;
- errors retain correlation;
- recovery does not allocate replacement IDs accidentally.

---

# 71. Compatibility evolution

Adding a new optional identity field is normally backward-compatible.

Changing the meaning of an existing identity is breaking.

Examples of breaking changes:

- redefining TaskRunId to mean TaskAttemptId;
- changing CorrelationId into WorkflowRunId;
- reusing one execution ID across semantically distinct executions;
- making TraceId the only runtime identity.

Such changes require explicit contract-version evolution.

---

# 72. Acceptance criteria

This model is implemented correctly when:

1. WorkflowRunId, TaskRunId and TaskAttemptId are distinct;
2. IngestionRunId remains PyIngestKit-owned;
3. TransformationExecutionId remains PyTransformKit-owned;
4. external provider IDs remain provider-owned;
5. CorrelationId groups executions without replacing native IDs;
6. CausationId can express immediate trigger relationships;
7. task retry creates a new TaskAttemptId;
8. a fresh PyTransformKit invocation creates a new TransformationExecutionId;
9. workflow recovery preserves WorkflowRunId;
10. same TransformationPlan can produce many execution IDs;
11. CorrelationContext crosses process/framework boundaries explicitly;
12. TraceId remains observability metadata;
13. results expose native identity and correlation;
14. logs/events can carry relevant IDs;
15. no universal RunId type is required;
16. sibling frameworks do not import runtime internals merely for correlation;
17. ExternalRunRef preserves provider identity;
18. uncertain outcomes remain attached to original execution IDs;
19. durable references survive restart/cross-host use where promised;
20. end-to-end conformance tests verify propagation.

---

# 73. Normative invariants

### ID-INV-01 — Native execution identity is bounded-context owned

Workflow, ingestion and transformation identities remain distinct.

### ID-INV-02 — Correlation is not execution identity

Correlation groups work; it does not own lifecycle state.

### ID-INV-03 — Causation is explicit

Shared correlation does not imply direct parenthood.

### ID-INV-04 — Retry changes attempt identity

Every new TaskAttempt gets a new TaskAttemptId.

### ID-INV-05 — Fresh sibling execution gets fresh native identity

A new ingestion or transformation execution normally receives a new native ID.

### ID-INV-06 — Recovery preserves identity

Restart/recovery does not replace the identity of the same persisted execution.

### ID-INV-07 — Definition identity is not runtime identity

Definition IDs and plan fingerprints never substitute for execution IDs.

### ID-INV-08 — Trace identity is observational

Trace IDs never replace durable domain IDs.

### ID-INV-09 — Provider identity remains provider-owned

External IDs are referenced, not renamed into PyKit-native identities.

### ID-INV-10 — IDs are not credentials

Possession of an ID does not imply authorization.

### ID-INV-11 — Correlation crosses boundaries explicitly

Process-local state alone is insufficient for durable interoperability.

### ID-INV-12 — Unknown outcome remains on original execution

Reconciliation does not erase or replace execution identity.

---

# 74. Final architecture statement

A single PyKit operation may span:

~~~text
WorkflowRun
    ↓
TaskRun
    ↓
TaskAttempt
    ↓
IngestionRun / TransformationExecution
    ↓
External provider execution
~~~

Every layer keeps its own identity.

They are connected through:

~~~text
CorrelationId
CausationId
ExecutionReference
ExternalRunRef
TraceId
~~~

without becoming the same object.

The central rule is:

> **One operation may have many execution identities, but one correlation story.**

This specification is the baseline for:

~~~text
PYKIT_ECOSYSTEM_V2_ERROR_FAILURE_RETRY_AND_UNCERTAINTY_MODEL.md
PYKIT_ECOSYSTEM_V2_LINEAGE_PROVENANCE_AND_TRACEABILITY_MODEL.md
PYKIT_ECOSYSTEM_V2_OBSERVABILITY_EVENTS_AND_TELEMETRY_MODEL.md
PYKIT_ECOSYSTEM_V2_SERIALIZATION_AND_WIRE_CONTRACTS.md
~~~
