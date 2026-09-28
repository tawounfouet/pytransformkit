# PyWorkflowKit V2 — Target Architecture

> **Status:** NORMATIVE TARGET ARCHITECTURE BASELINE
> **Target release:** PyWorkflowKit 2.0.0
> **Date:** 2026-09-28
> **Architecture generation:** PyKit Ecosystem V2
> **Tagline:** Reliable workflows without running a workflow platform.
> **Primary bounded context:** reliable execution of generic workload dependency graphs
> **Depends on:** PYKIT_ECOSYSTEM_V2_DECLARATION_PLAN_RUNTIME_MODEL.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_END_TO_END_ACCEPTANCE_CRITERIA.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_IMPLEMENTATION_SEQUENCE_AND_MIGRATION_PLAN.md
> **Depends on:** PYTRANSFORMKIT_V1_TARGET_ARCHITECTURE.md
> **Depends on:** PYINGESTKIT_V2_TARGET_ARCHITECTURE.md
> **Depends on:** all normative PyKit Ecosystem V2 cross-framework specifications

---

# 1. Purpose

This document defines the target internal architecture of PyWorkflowKit for the 2.0.0 stable release.

It translates the ecosystem-wide V2 rules into concrete PyWorkflowKit module boundaries, domain objects, execution-state semantics, runtime services, ports, executors, persistence, recovery, reconciliation, observability, serialization, extension points and sibling-framework integrations.

> **PyWorkflowKit owns reliable execution of a generic dependency graph; it does not own the domain semantics of the workloads it runs.**

> **A workflow runtime coordinates work. It must not absorb the internal state machines of PyIngestKit, PyTransformKit or external providers.**

# 2. Product mission

PyWorkflowKit exists to provide reliable workflow execution without requiring a full workflow platform.

Its canonical responsibility is:

~~~text
WorkflowDefinition
        ↓
compile / validate
        ↓
ExecutionPlan
        ↓
WorkflowRuntime
        ↓
WorkflowRun
    ├── TaskRun
    │     └── TaskAttempt
    └── ...
        ↓
WorkflowResult
~~~

The framework provides execution semantics such as dependency ordering, attempts, retry, timeout, cancellation, persistence, recovery and reconciliation while remaining embeddable as a Python library.

# 3. Bounded-context ownership

PyWorkflowKit owns:

~~~text
WorkflowDefinition
TaskDefinition
workflow dependency semantics
ExecutionPlan
workflow planning and validation
WorkflowRun
TaskRun
TaskAttempt
workflow/task state machines
task readiness
retry and backoff at workload scope
timeout semantics
cancellation semantics
fail-fast / skip propagation
local execution
executor abstraction
ExternalRunRef
durable workflow metadata
checkpoint/recovery semantics
reconciliation of external work
workflow execution lineage
workflow manifests
workflow diagnostics
workflow events / metrics / traces
executor and metadata-store plugins
~~~

PyWorkflowKit does not own:

~~~text
PyIngestKit Source / RAW / DatasetVersion lifecycle
PyTransformKit Dataset / Expression / LogicalPlan semantics
field-level transformation lineage
source acquisition provenance
DatasetVersion publication
generic data catalog
cron service
distributed scheduler control plane
worker fleet management
web UI
enterprise IAM
secret-management platform
cloud infrastructure provisioning
provider-specific business state machines
~~~

# 4. Relationship to sibling frameworks

Canonical dependency direction:

~~~text
PyWorkflowKit
    ├── optional integration → PyIngestKit
    └── optional integration → PyTransformKit

PyIngestKit
    └── optional integration → PyTransformKit

PyTransformKit
    └── no sibling dependency
~~~

PyWorkflowKit core MUST work without either sibling framework installed.

Sibling composition occurs through optional integrations and portable contracts.

# 5. Canonical public model

The target public model is:

~~~text
WorkflowDefinition
        ↓
ExecutionPlan
        ↓
WorkflowRuntime.run(...)
        ↓
WorkflowRun
    ├── TaskRun
    │     └── TaskAttempt
        ↓
WorkflowResult
~~~

There is no stable public WorkflowGraph or DependencyGraph in V2.

# 6. Architectural layers

PyWorkflowKit V2 uses five principal layers:

~~~text
AUTHORING
    workflow/task declarations and ergonomic builders

DOMAIN
    definitions, plans, run identities, state machines and policies

APPLICATION / PLANNING
    validation, compilation, readiness and retry/cancellation decisions

RUNTIME
    execution loop, attempts, executors, persistence and recovery

INFRASTRUCTURE / ADAPTERS
    metadata stores, subprocess/thread/process executors, telemetry and sibling integrations
~~~

Dependencies point inward.

The domain layer MUST NOT depend on specific executors, databases, sibling frameworks or telemetry backends.

# 7. Target package structure

~~~text
src/pyworkflowkit/
├── __init__.py
├── domain/
│   ├── workflows.py
│   ├── tasks.py
│   ├── plans.py
│   ├── runs.py
│   ├── states.py
│   ├── policies.py
│   ├── references.py
│   ├── lineage.py
│   └── errors.py
├── application/
│   ├── validation.py
│   ├── planner.py
│   ├── readiness.py
│   ├── retry.py
│   ├── cancellation.py
│   ├── recovery.py
│   └── reconciliation.py
├── runtime/
│   ├── workflow_runtime.py
│   ├── execution_loop.py
│   ├── task_runner.py
│   ├── results.py
│   ├── context.py
│   └── diagnostics.py
├── ports/
│   ├── executor.py
│   ├── metadata_store.py
│   ├── event_sink.py
│   ├── clock.py
│   └── plugins.py
├── executors/
│   ├── inline.py
│   ├── thread.py
│   ├── process.py
│   ├── async_.py
│   └── subprocess.py
├── persistence/
│   ├── memory/
│   ├── sqlite/
│   └── postgres/
├── serialization/
├── observability/
├── plugins/
└── integrations/
    ├── pyingestkit/
    └── pytransformkit/
~~~

Exact module names may evolve, but responsibility boundaries are normative.

# 8. Root package philosophy

The root package is curated rather than exhaustive.

Target root exports should center on:

~~~text
WorkflowDefinition
TaskDefinition
ExecutionPlan
WorkflowRuntime
WorkflowRun
TaskRun
TaskAttempt
WorkflowResult
WorkflowRunId
TaskRunId
TaskAttemptId
RetryPolicy
TimeoutPolicy
selected state/result/reference types
selected public exceptions
~~~

Private graph structures, persistence entities, executor internals and plugin machinery stay out of the root API.

# 9. Domain purity

Pure domain modules MUST be importable without:

~~~text
PyIngestKit
PyTransformKit
PostgreSQL drivers
SQLAlchemy
cloud SDKs
OpenTelemetry
subprocess runtime state
thread/process pools
~~~

Optional execution and persistence integrations remain outside the domain.

# 10. WorkflowDefinition

WorkflowDefinition is the canonical workflow authoring root.

It owns:

~~~text
workflow identity within the definition
TaskDefinition values
declared task dependencies
workflow-level execution policies
declared conditions
runtime-independent metadata
~~~

It MUST NOT own current run state, attempt counters, active workers, provider IDs or resolved credentials.

# 11. TaskDefinition

TaskDefinition is public because a task has independent workload semantics.

It may own:

~~~text
task key
workload declaration
dependency declarations
input/output contract declarations
retry policy reference
timeout policy
cancellation policy
condition / trigger rule
runtime-independent metadata
~~~

TaskDefinition is not a generic cross-framework Step abstraction.

# 12. Workload declaration

A TaskDefinition represents one workload boundary.

The workload may be implemented by:

~~~text
Python callable
async callable
subprocess command
registered executor payload
PyIngestKit integration
PyTransformKit integration
external provider adapter
~~~

Executable payload form is an authoring/runtime concern; task identity and attempt semantics remain framework-owned.

# 13. Workflow topology

WorkflowDefinition owns the declared dependency topology.

The topology MUST be:

- acyclic;
- deterministic;
- inspectable;
- validated before execution;
- independent from incidental object identity;
- suitable for deterministic planning.

A separate public WorkflowGraph is unnecessary.

# 14. DependencyGraph

DependencyGraph is an internal algorithmic representation.

It may support:

~~~text
cycle detection
topological sorting
reachability
ancestor/descendant queries
readiness analysis
skip propagation
~~~

It does not become a stable public domain model.

# 15. Validation layers

Workflow validation is divided into:

~~~text
STRUCTURAL
    unique task keys, dependency references, DAG integrity

SEMANTIC
    compatible policies, trigger/condition validity, output references

CAPABILITY
    selected executor/integration can run the declared workload

RUNTIME PREFLIGHT
    required resources, plugins and stores are available
~~~

Diagnostics must preserve these distinctions.

# 16. ExecutionPlan

ExecutionPlan is the public compiled workflow representation.

It may own:

~~~text
validated task topology
deterministic topological order
resolved conditions / trigger rules
effective retry/timeout policies
executor requirements
readiness prerequisites
plan fingerprint
compile-time diagnostics
~~~

ExecutionPlan MUST remain free from mutable runtime state.

# 17. Planning

Planning converts WorkflowDefinition into ExecutionPlan.

Planning MAY normalize dependencies and policy defaults.

Planning MUST NOT:

- create WorkflowRunId;
- create TaskAttemptId;
- launch work;
- resolve secret values unnecessarily;
- mutate provider state.

# 18. WorkflowDefinition versus ExecutionPlan

~~~text
WorkflowDefinition
    what the author declared

ExecutionPlan
    the validated deterministic execution semantics understood by the runtime
~~~

Both concepts remain public because they own distinct semantics.

# 19. WorkflowRun

WorkflowRun represents one execution of a WorkflowDefinition or ExecutionPlan.

It owns or references:

~~~text
WorkflowRunId
definition/plan fingerprint
CorrelationContext
workflow status
TaskRun identities
timestamps
workflow-level FailureEvidence
manifest references
recovery metadata
~~~

WorkflowRun is runtime state, not authoring state.

# 20. TaskRun

TaskRun represents the logical execution of one TaskDefinition inside one WorkflowRun.

TaskRun identity is stable across retries.

It owns the relationship between the workflow task and its sequence of TaskAttempt values.

# 21. TaskAttempt

TaskAttempt represents one concrete attempt to execute a TaskRun workload.

Every retry creates a new TaskAttemptId.

A TaskAttempt may own or reference:

~~~text
TaskAttemptId
attempt number
start/end timestamps
status
executor identity
ExternalRunRef
FailureEvidence
cancellation state
reconciliation evidence
output references
~~~

# 22. Canonical identity hierarchy

~~~text
WorkflowRunId
    └── TaskRunId
          ├── TaskAttemptId #1
          ├── TaskAttemptId #2
          └── TaskAttemptId #3
~~~

Retry changes TaskAttempt identity, not TaskRun identity.

# 23. CorrelationContext

WorkflowRuntime accepts or creates CorrelationContext.

CorrelationId links the broader business operation.

WorkflowRunId, TaskRunId and TaskAttemptId remain native execution identities.

TraceId/SpanId remain observational.

# 24. State machines

WorkflowRun, TaskRun and TaskAttempt each require explicit state-machine semantics.

State transitions MUST be validated rather than assigned arbitrarily.

Terminal states are protected.

Illegal transitions fail explicitly.

# 25. WorkflowRun states

A canonical state model may include:

~~~text
PENDING
RUNNING
SUCCEEDED
FAILED
CANCELLATION_REQUESTED
CANCELLED
TIMED_OUT
UNKNOWN_OUTCOME where workflow-level uncertainty is justified
~~~

Exact enum names are frozen in the public API specification.

# 26. TaskRun states

TaskRun state summarizes the logical task across attempts.

It may distinguish:

~~~text
PENDING
READY
RUNNING
SUCCEEDED
FAILED
SKIPPED
CANCELLED
TIMED_OUT
BLOCKED
~~~

A TaskRun does not become SUCCEEDED until one attempt succeeds according to task semantics.

# 27. TaskAttempt states

TaskAttempt tracks one concrete attempt.

It may distinguish:

~~~text
PENDING
STARTING
RUNNING
SUCCEEDED
FAILED
TIMED_OUT
CANCELLATION_REQUESTED
CANCELLED
CANCELLATION_UNCONFIRMED
UNKNOWN_OUTCOME
REQUIRES_RECONCILIATION
~~~

Attempt states preserve uncertainty rather than flattening it into FAILED.

# 28. Readiness

A task becomes runnable only when dependency and policy conditions are satisfied.

Readiness evaluates:

~~~text
upstream terminal states
trigger/condition rules
skip propagation
fail-fast policy
required input references
concurrency/resource constraints when configured
~~~

Readiness is derived from ExecutionPlan plus runtime state.

# 29. Skip semantics

SKIPPED is a first-class outcome, not an alias for success or failure.

Skip propagation MUST be deterministic and policy-driven.

A downstream task may be skipped because its trigger condition is unsatisfied without implying workload failure.

# 30. Fail-fast semantics

Fail-fast is a workflow/task policy.

It controls whether new eligible work should stop after qualifying failures.

Fail-fast MUST NOT erase already-running work or historical attempt evidence.

# 31. Retry ownership

PyWorkflowKit owns workload-level retry.

Canonical distinction:

~~~text
PyWorkflowKit
    retries the task workload by creating a new TaskAttempt

Provider / sibling runtime
    may perform bounded internal retries inside one external execution
~~~

Equivalent retry scopes MUST NOT be stacked implicitly.

# 32. RetryPolicy

RetryPolicy SHOULD model at least:

~~~text
maximum attempts
backoff
maximum delay
jitter policy when supported
retryable failure categories
deadline / total budget
reconciliation requirement
~~~

RetryPolicy is evaluated against structured FailureEvidence rather than exception-message matching.

# 33. Retry decision

Retry decisions may produce:

~~~text
RETRY
DO_NOT_RETRY
RECONCILE
ABORT
CANCEL
ESCALATE
~~~

UNKNOWN_OUTCOME generally requires reconciliation before another workload attempt.

# 34. Retry amplification

The runtime SHOULD make effective attempts observable across layers.

Example:

~~~text
TaskAttempt #1
    └── PyIngestKit IngestionRun
          └── HTTP retry x3

TaskAttempt #2
    └── new IngestionRun
~~~

Hidden provider retries count toward the real operational budget.

# 35. Timeout semantics

Timeout means the local runtime stopped waiting after a declared deadline.

Timeout does not prove that external work failed or stopped.

If the workload may still be executing, the attempt may require reconciliation.

# 36. Cancellation semantics

Cancellation is stateful and provider-dependent.

The runtime MUST distinguish:

~~~text
CANCELLATION_REQUESTED
CANCELLED
CANCELLATION_UNCONFIRMED
CANCELLATION_UNSUPPORTED
~~~

A cancellation request is not confirmed cancellation.

# 37. ExternalRunRef

ExternalRunRef is the portable link between a TaskAttempt and execution owned outside WorkflowKit.

It may identify:

~~~text
PyIngestKit IngestionRun
PyTransformKit TransformationExecution
subprocess execution
remote provider job
external service run
~~~

WorkflowKit stores the reference without taking ownership of the external runtime's domain semantics.

# 38. TaskAttempt and ExternalRunRef

A TaskAttempt MAY have zero, one or multiple ExternalRunRef values depending on workload semantics.

For example, a provider integration may create an external submission request followed by a remote job.

The relation must remain explicit rather than hidden in logs.

# 39. Recovery

Recovery restores workflow execution after loss of local process state.

Canonical flow:

~~~text
process dies
    ↓
durable WorkflowRun / TaskRun / TaskAttempt state remains
    ↓
runtime restarts
    ↓
load unfinished runs
    ↓
inspect ExternalRunRef where present
    ↓
reconcile provider truth
    ↓
resume state machine
~~~

Recovery is not rerun.

# 40. Recovery identity

Recovery preserves:

~~~text
WorkflowRunId
TaskRunId
existing TaskAttemptId when reconciling that attempt
ExternalRunRef
CorrelationContext
~~~

A new TaskAttempt is created only when retry policy decides to retry.

# 41. Reconciliation

Reconciliation maps external/provider truth back into WorkflowKit-owned attempt state.

Possible outcomes include:

~~~text
CONFIRMED_SUCCEEDED
CONFIRMED_FAILED
CONFIRMED_CANCELLED
STILL_RUNNING
STILL_UNKNOWN
NOT_FOUND
~~~

Provider absence may remain ambiguous under eventual consistency and must not always be interpreted as failure.

# 42. Checkpoints

WorkflowKit MAY persist checkpoints for runtime progress.

A checkpoint is execution metadata, not a dataset artifact by default.

Checkpoint semantics SHOULD include versioning, ownership and recovery compatibility.

# 43. WorkflowRuntime

WorkflowRuntime is the main execution service.

It coordinates:

~~~text
WorkflowDefinition / ExecutionPlan validation
run identity
metadata persistence
task readiness
TaskRun and TaskAttempt creation
executor selection
workload launch
retry decisions
timeout and cancellation
ExternalRunRef persistence
reconciliation
recovery
events / telemetry
manifest construction
WorkflowResult construction
~~~

It does not introspect sibling internal DAGs.

# 44. Execution loop

The runtime execution loop SHOULD be explicit and deterministic.

Conceptually:

~~~text
load / create WorkflowRun
    ↓
evaluate ready tasks
    ↓
create TaskAttempt
    ↓
dispatch through Executor
    ↓
persist attempt evidence
    ↓
update TaskRun state
    ↓
recompute readiness
    ↓
repeat until terminal WorkflowRun
~~~

# 45. Executor port

Executor is the primary workload-execution extension boundary.

Its responsibilities SHOULD include:

~~~text
capability declaration
launch / execute workload
timeout/cancellation integration
result capture
ExternalRunRef when relevant
failure translation
resource ownership
~~~

Exact method signatures are frozen in PYWORKFLOWKIT_V2_PUBLIC_API_SPEC.md.

# 46. Local executor first

The first stable executor SHOULD be deterministic and local.

An inline/local executor is sufficient to prove state machines, attempt semantics, retry, failure mapping and recovery metadata.

Distributed scheduling is not required for V2 correctness.

# 47. Thread executor

A thread-based executor MAY provide concurrent in-process execution for appropriate workloads.

It must document:

~~~text
thread safety expectations
cancellation limitations
context propagation
resource ownership
exception translation
~~~

# 48. Process executor

A process-based executor MAY isolate CPU-bound or unsafe workloads more strongly than threads.

It must use explicit serialization boundaries.

Durable workflow state MUST NOT depend on arbitrary pickle/cloudpickle payloads.

# 49. Async executor

An async executor MAY support coroutine workloads.

Async execution must preserve the same TaskAttempt, retry, timeout and cancellation semantics.

Async does not create a second workflow state model.

# 50. Subprocess executor

A subprocess executor MAY launch external commands.

It SHOULD prefer executable plus argv over shell strings.

Shell mode must be explicit.

Environment propagation must be controllable and secret-safe.

A subprocess is not a full security sandbox.

# 51. Executor capability model

Executors SHOULD declare capabilities such as:

~~~text
SYNC_CALLABLE
ASYNC_CALLABLE
THREAD_CONCURRENCY
PROCESS_ISOLATION
SUBPROCESS
CANCELLATION
TIMEOUT
EXTERNAL_RECONCILIATION
STREAMING_OUTPUT
~~~

Package presence alone is not capability.

# 52. No hidden executor fallback

If a TaskDefinition requires an unsupported executor capability, planning/preflight fails explicitly unless an explicit fallback policy was configured.

WorkflowKit MUST NOT silently switch execution model in a way that changes semantics.

# 53. MetadataStore

MetadataStore persists workflow execution state.

It SHOULD support durable operations for:

~~~text
WorkflowRun
TaskRun
TaskAttempt
ExternalRunRef
state transitions
attempt history
recovery queries
manifests / references as appropriate
~~~

Persistence details remain behind the port.

# 54. Atomic state transitions

MetadataStore MUST support consistency strong enough to prevent impossible state histories.

Where concurrent runtimes are supported, state updates SHOULD use optimistic locking, compare-and-swap or transactional equivalents.

The architecture must not rely on last-write-wins for critical state transitions.

# 55. In-memory store

An in-memory metadata store SHOULD exist for:

~~~text
unit tests
simple local runs
examples
deterministic conformance
~~~

It does not provide crash recovery.

# 56. SQLite store

SQLite is the preferred durable local reference store for V2.

It SHOULD support:

~~~text
single-host durable runs
attempt history
recovery after process restart
Customer 360 local profile
migration fixtures
~~~

# 57. PostgreSQL store

A PostgreSQL metadata-store adapter MAY provide stronger multi-process or production durability.

PostgreSQL-specific schema details remain infrastructure-private.

Users should interact through the public MetadataStore contract.

# 58. Persistence schema evolution

Metadata schema is versioned.

Migrations MUST preserve execution identity, attempt history, ExternalRunRef and uncertainty.

Unsupported historical state fails explicitly rather than being silently rewritten.

# 59. Result model

WorkflowResult is the caller-facing workflow outcome.

It SHOULD expose:

~~~text
WorkflowRunId
status
task outcome summary
portable outputs
diagnostics
FailureEvidence when applicable
manifest/reference access
~~~

WorkflowResult is intentionally smaller than the full persisted WorkflowRun model.

# 60. Task outputs

Durable task outputs SHOULD be small, portable values or references.

Preferred examples:

~~~text
ResourceReference
ArtifactReference
DatasetVersionReference
IngestionExecutionReference
TransformationExecutionReference
ExternalRunRef
small JSON-compatible values
~~~

Large native DataFrames, open connections and provider clients MUST NOT become durable workflow state.

# 61. Output references and lineage

WorkflowKit records which TaskAttempt produced which portable outputs.

This is execution lineage.

It does not reinterpret data lineage or ingestion provenance owned by sibling frameworks.

# 62. Workflow execution lineage

Canonical lineage is:

~~~text
WorkflowRun
    ↓
TaskRun
    ↓
TaskAttempt
    ↓
ExternalRunRef
~~~

Additional edges MAY link portable task inputs and outputs.

Workflow dependency does not automatically imply data lineage.

# 63. Manifest

A workflow manifest SHOULD provide durable execution evidence such as:

~~~text
WorkflowRunId
definition fingerprint
ExecutionPlan fingerprint
CorrelationContext
TaskRun summaries
TaskAttempt references
ExternalRunRef values
terminal status
FailureEvidence
timestamps
contract version
~~~

Manifests MUST NOT contain raw secrets or active runtime handles.

# 64. Events

PyWorkflowKit emits framework-owned events.

Potential families include:

~~~text
workflow.run.started
workflow.run.succeeded
workflow.run.failed
task.run.ready
task.attempt.started
task.attempt.retry_scheduled
task.attempt.succeeded
task.attempt.failed
task.attempt.cancellation_requested
workflow.recovery.started
workflow.reconciliation.completed
~~~

Exact stable event names are frozen separately if promoted to public contracts.

# 65. Diagnostics

Structured diagnostics SHOULD cover:

~~~text
plan validation
readiness decisions
retry decisions
skip propagation
executor selection
timeout
cancellation
ExternalRunRef mapping
recovery
reconciliation
persistence conflicts
~~~

Users should not need to parse logs to understand why a task ran, skipped or retried.

# 66. Metrics

Default metrics SHOULD use bounded labels such as:

~~~text
executor
status
failure category
retry decision
task category when bounded
~~~

WorkflowRunId, TaskRunId, TaskAttemptId and CorrelationId MUST NOT be default metric labels.

# 67. Tracing

Tracing MAY represent:

~~~text
WorkflowRun span
    └── TaskAttempt spans
          └── sibling/provider execution spans
~~~

TraceId remains observational and does not replace durable execution IDs.

# 68. Telemetry isolation

Telemetry sink failure MUST NOT rerun tasks.

Core workflow execution must remain functional without an external telemetry backend.

Audit-grade evidence, if required, uses an explicitly stronger policy.

# 69. Serialization

Stable durable contracts use explicit contract IDs and versions.

Candidate portable surfaces include:

~~~text
WorkflowDefinition when workloads are portable
ExecutionPlan when portable
WorkflowExecutionReference
ExternalRunRef
CorrelationContext
FailureEvidence
workflow manifests
events
small task inputs/outputs
~~~

Portable subsets must be explicit.

# 70. No executable deserialization

Durable/public wire contracts MUST NOT depend on:

~~~text
pickle
cloudpickle
dill
eval
exec
arbitrary module/class reconstruction
~~~

Local executor implementation may use private process mechanics, but durable recovery state remains schema-driven.

# 71. Callable portability

A Python callable may be valid for trusted local execution without being portable across hosts or process restarts.

WorkflowDefinition serialization MUST distinguish:

~~~text
portable workload descriptors
process-local callable references
non-portable closures
~~~

Portability MUST NOT be implied accidentally.

# 72. Plugin architecture

Plugins MAY extend:

~~~text
Executor
MetadataStore
telemetry sinks
external workload adapters
policy evaluators where explicitly supported
~~~

Discovery does not imply activation.

# 73. Plugin namespaces

Potential entry-point groups may include:

~~~text
pyworkflowkit.executors
pyworkflowkit.metadata_stores
pyworkflowkit.telemetry
~~~

Exact names are frozen later.

# 74. Optional dependencies

The base package SHOULD remain lightweight.

Potential extras may include:

~~~text
[postgres]
[otel]
[ingest]
[transform]
~~~

Thread/async support may remain standard-library based.

Optional means optional in installation, import and activation.

# 75. PyIngestKit integration

The official integration lives conceptually under:

~~~text
pyworkflowkit.integrations.pyingestkit
~~~

Canonical execution:

~~~text
TaskAttempt
    ↓
IngestionDefinition
    ↓
IngestionRuntime
    ↓
IngestionResult
    ↓
IngestionExecutionReference / ExternalRunRef
~~~

WorkflowKit does not decompose acquisition, RAW, decode, version or publication stages.

# 76. PyTransformKit integration

The official integration lives conceptually under:

~~~text
pyworkflowkit.integrations.pytransformkit
~~~

Canonical execution:

~~~text
TaskAttempt
    ↓
TransformationPlan
    ↓
TransformationRuntime
    ↓
TransformationResult
    ↓
TransformationExecutionReference / ExternalRunRef
~~~

WorkflowKit does not schedule transformation nodes individually.

# 77. Integration retry rule

Sibling adapters MUST preserve one retry owner per semantic scope.

~~~text
TaskAttempt retry
    creates a new sibling execution

bounded sibling/provider retry
    remains inside the same sibling execution
~~~

Recovery/reconciliation may reconnect to existing sibling execution instead of creating a new one.

# 78. Integration uncertainty rule

Sibling UNKNOWN_OUTCOME MUST survive mapping into WorkflowKit.

An adapter MUST NOT turn uncertain external state into ordinary FAILED merely to simplify the workflow state machine.

Where appropriate, the TaskAttempt enters reconciliation-required semantics.

# 79. Integration cancellation rule

WorkflowKit may request sibling cancellation through public adapter capabilities.

It MUST preserve the sibling's actual cancellation outcome and uncertainty.

# 80. Integration output rule

Sibling adapters return portable references and small structured metadata.

They MUST NOT place large engine-native objects into durable TaskAttempt output.

# 81. Security boundaries

PyWorkflowKit follows the ecosystem security baseline.

It MUST preserve:

~~~text
identity != authorization
explicit executable-code surfaces
CredentialReference instead of raw secret
controlled subprocess environment
explicit plugin activation
non-executable durable deserialization
redacted telemetry
reference possession != cancellation authority
~~~

# 82. Subprocess security

Subprocess execution SHOULD use executable + argv.

Shell mode must be explicit.

Working directory and environment propagation must be validated.

stdout/stderr capture must be bounded and redacted.

# 83. Remote-worker posture

PyWorkflowKit V2 core does not require a remote-worker control plane.

If remote execution is added, workers receive only scoped task input, references, correlation context and credentials needed for the workload.

Remote execution must not change WorkflowRun/TaskRun/TaskAttempt identity semantics.

# 84. Scheduling non-goal

PyWorkflowKit V2 core does not own cron or calendar scheduling.

Canonical boundary:

~~~text
external scheduler / application
        ↓
WorkflowRuntime.run(WorkflowDefinition)
~~~

A future scheduler package may trigger workflows without becoming part of core runtime semantics.

# 85. Distributed-control-plane non-goal

V2 core does not require:

~~~text
central web server
worker heartbeat service
distributed queue
cluster scheduler
web UI
multi-tenant control plane
RBAC platform
~~~

The library remains useful without these components.

# 86. Concurrency model

Concurrency is an executor/runtime policy, not a new workflow semantics layer.

The runtime may support:

~~~text
max concurrent attempts
executor-specific limits
resource pools
per-task concurrency limits
~~~

Concurrency decisions MUST preserve deterministic dependency correctness.

# 87. Resource pools

Optional resource-pool semantics MAY limit concurrent workloads by named capacity.

If exposed publicly, capacity tokens remain workflow scheduling constraints rather than provider resource ownership.

# 88. Idempotency

WorkflowKit does not assume task workloads are idempotent.

Retry decisions SHOULD consume idempotency evidence from TaskDefinition policy, adapter metadata or FailureEvidence.

Non-idempotent tasks require stronger caution after timeouts or unknown outcomes.

# 89. Determinism

Given the same WorkflowDefinition and policy inputs, ExecutionPlan construction SHOULD be deterministic.

Runtime completion order may vary under concurrency, but dependency correctness and state transitions remain deterministic.

# 90. Clock and time

Time-dependent runtime behavior SHOULD be mediated through an injectable clock abstraction where practical.

This supports deterministic tests for retry backoff, deadlines and timeouts.

# 91. Identifier generation

Execution IDs SHOULD use an injectable generator or deterministic fixture strategy for tests.

Production identity generation must avoid relying on process-local counters for global uniqueness.

# 92. Public exceptions

PyWorkflowKit SHOULD expose a coherent public error hierarchy for:

~~~text
definition validation
planning
state transition
executor capability
execution
persistence
recovery
reconciliation
serialization
plugin/integration failures
~~~

Exact names are frozen in the public API specification.

# 93. Internal exceptions

Executor, database and provider-native exceptions are translated at adapter boundaries.

They may be retained as diagnostic causes but are not the stable public contract.

# 94. Migration from WorkflowKit V1

V2 is a clean-slate major architecture.

Migration maps semantics rather than class names.

Examples:

~~~text
legacy workflow/job
    → WorkflowDefinition

legacy task/step
    → TaskDefinition when it represents one workload

legacy run
    → WorkflowRun

legacy retry history
    → TaskAttempt sequence

legacy provider execution tracking
    → ExternalRunRef
~~~

# 95. Legacy decorator migration

Existing @task and @workflow ergonomics MAY be retained if they compile into the V2 canonical model.

Decorators are syntax sugar.

They MUST NOT create a parallel execution model.

# 96. Migration from V1 metadata stores

Existing memory/SQLite/PostgreSQL store logic may be reused if aligned with V2 run identities, state machines and ExternalRunRef.

Private schema compatibility is not guaranteed forever.

Explicit migration/export-import tooling is preferred over permanent coupling to legacy tables.

# 97. Migration from V1 executors

Existing thread/process/async/subprocess executors are implementation evidence.

They should be refactored behind the V2 Executor port and normalized around TaskAttempt semantics, cancellation, timeout, FailureEvidence and portable result boundaries.

# 98. Migration from V1 recovery

Existing recovery/reconciliation behavior should be retained only when it preserves identity and external references.

Any logic that treats restart as unconditional rerun must be removed.

# 99. Migration from V1 plugins and SDK/control-plane contracts

Plugin and SDK concepts may survive only when they remain within V2 ownership.

Control-plane contracts not required for embedded workflow execution remain optional/provisional and MUST NOT dictate core domain semantics.

# 100. Conformance strategy

PyWorkflowKit 2.0 requires:

~~~text
domain purity tests
public API snapshot
DAG validation tests
ExecutionPlan determinism tests
WorkflowRun state-machine tests
TaskRun state-machine tests
TaskAttempt state-machine tests
retry/backoff tests
timeout/cancellation tests
Executor conformance
MetadataStore conformance
recovery/reconciliation fault injection
wire golden fixtures
security negative tests
optional dependency absence tests
sibling adapter tests
built-wheel smoke
Customer 360 workflow path
~~~

# 101. Executor conformance

Reusable behavioral suites SHOULD test stable executors for:

~~~text
successful workload execution
structured failure translation
timeout semantics
cancellation capability
context propagation
result capture
resource cleanup
no hidden retry
~~~

# 102. MetadataStore conformance

Reusable suites SHOULD test:

~~~text
identity preservation
atomic state transitions
attempt history
ExternalRunRef persistence
recovery queries
schema migration behavior
concurrent update protection when supported
~~~

# 103. Local reference profile

The V2 reference profile SHOULD run with:

~~~text
inline/local executor
SQLite metadata store
synthetic workflows
JSON manifests
no external telemetry
optional PyIngestKit/PyTransformKit local packages
~~~

This profile is the deterministic baseline for CI and Customer 360.

# 104. Production extension posture

Production deployments MAY add:

~~~text
PostgreSQL metadata
thread/process concurrency
subprocess workloads
OpenTelemetry
custom executors
remote provider adapters
~~~

None become mandatory to use the core library.

# 105. Target architecture invariants

### PWK-ARCH-INV-01 — WorkflowDefinition is the authoring root

Workflow topology belongs to the definition.

### PWK-ARCH-INV-02 — ExecutionPlan is the public compiled execution contract

It owns validated deterministic execution semantics.

### PWK-ARCH-INV-03 — WorkflowGraph and DependencyGraph remain internal

Graph machinery is implementation detail rather than duplicate public domain state.

### PWK-ARCH-INV-04 — WorkflowRun, TaskRun and TaskAttempt have distinct identities

Retry creates a new TaskAttempt without replacing TaskRun identity.

### PWK-ARCH-INV-05 — Retry is owned at workload scope

Sibling/provider internal retries remain separate and observable.

### PWK-ARCH-INV-06 — Recovery is not rerun

Restart preserves existing identities and reconciles external work first.

### PWK-ARCH-INV-07 — UNKNOWN_OUTCOME is preserved

Uncertain external state is not flattened into ordinary failure.

### PWK-ARCH-INV-08 — Sibling runtimes are opaque workloads

WorkflowKit never schedules their internal domain nodes.

### PWK-ARCH-INV-09 — Durable task state uses portable references

Large native objects and active handles do not become workflow metadata.

### PWK-ARCH-INV-10 — Core remains embeddable

No scheduler server, worker fleet or control plane is required.

### PWK-ARCH-INV-11 — Durable serialization is non-executable

Recovery state does not depend on arbitrary Python object reconstruction.

### PWK-ARCH-INV-12 — Sibling integrations remain optional

PyWorkflowKit core works without PyIngestKit or PyTransformKit installed.

# 106. Canonical execution flow

~~~text
WorkflowDefinition
        ↓
Structural + semantic validation
        ↓
WorkflowPlanner
        ↓
ExecutionPlan
        ↓
WorkflowRuntime
        ↓
Create / load WorkflowRun
        ↓
Evaluate readiness
        ↓
Create TaskRun / TaskAttempt as required
        ↓
Executor
        ↓
Persist result / ExternalRunRef / FailureEvidence
        ↓
Retry / reconcile / cancel / propagate skip
        ↓
Repeat until WorkflowRun terminal
        ↓
WorkflowResult
~~~

# 107. Canonical sibling composition

~~~text
WorkflowRun
    │
    ├── TaskAttempt: ingest
    │       ↓
    │   PyIngestKit adapter
    │       ↓
    │   IngestionRun
    │
    ├── TaskAttempt: transform
    │       ↓
    │   PyTransformKit adapter
    │       ↓
    │   TransformationExecution
    │
    └── TaskAttempt: publish
            ↓
        PyIngestKit adapter
            ↓
        IngestionRun
~~~

WorkflowKit owns only the TaskAttempt and workflow dependency semantics around those external executions.

# 108. Internal dependency flow

~~~text
domain
  ↑
application / planning
  ↑
runtime
  ↑
executors / persistence / integrations
~~~

Ports are defined inward and implemented outward.

# 109. PyWorkflowKit 2.0 acceptance

PyWorkflowKit 2.0 is ready when:

1. WorkflowDefinition is the canonical authoring API;
2. TaskDefinition owns one workload boundary;
3. ExecutionPlan is deterministic and public;
4. WorkflowGraph and DependencyGraph remain internal;
5. WorkflowRun, TaskRun and TaskAttempt identities are stable;
6. state machines reject invalid transitions;
7. workload retry creates new TaskAttempt values;
8. timeout and cancellation preserve uncertainty;
9. ExternalRunRef is durable and portable;
10. recovery reuses existing identities and reconciles before rerun;
11. inline/local executor conformance is green;
12. SQLite metadata-store recovery is green;
13. task outputs remain portable and bounded;
14. wire contracts are safe and versioned;
15. plugins activate explicitly;
16. PyIngestKit/PyTransformKit integrations are optional and contract-based;
17. sibling UNKNOWN_OUTCOME semantics survive adaptation;
18. built wheels pass clean installed smoke;
19. Customer 360 workflow/recovery paths are green;
20. V1-to-V2 migration guidance and supported state migrations are documented.

# 110. Out of scope for 2.0 core architecture

PyWorkflowKit 2.0 does not require:

~~~text
cron scheduler
distributed scheduler service
worker fleet control plane
message broker
web UI
multi-tenant SaaS control plane
enterprise RBAC platform
data transformation engine
ingestion lifecycle
data catalog
every executor backend
~~~

These exclusions protect the embedded-runtime mission.

# 111. Relationship to implementation roadmap

This architecture is the basis for:

~~~text
PYWORKFLOWKIT_V2_IMPLEMENTATION_ROADMAP.md
~~~

That roadmap must order public model, planning, identities, state machines, local executor, retry, timeout/cancellation, metadata persistence, recovery, reconciliation, observability, serialization, plugins, sibling integrations, migration and release qualification.

# 112. Relationship to public API specification

This document defines what concepts exist and where they belong.

The public API specification will freeze how users import and call them:

~~~text
PYWORKFLOWKIT_V2_PUBLIC_API_SPEC.md
~~~

That document MUST preserve this architecture.

# 113. Final architecture statement

PyWorkflowKit 2.0 is an embedded workflow runtime for reliable execution of generic dependency graphs.

Its canonical shape is:

~~~text
AUTHORING
    WorkflowDefinition + TaskDefinition
        ↓
PLANNING
    ExecutionPlan
        ↓
RUNTIME
    WorkflowRuntime
        ↓
STATE
    WorkflowRun
      └── TaskRun
            └── TaskAttempt
        ↓
EXECUTION
    Executor / ExternalRunRef
        ↓
RESULT
    WorkflowResult
~~~

> **PyWorkflowKit coordinates reliable workload execution through explicit plans, attempts, retry, recovery and portable external references, while leaving the internal semantics of each workload to its owning framework or provider.**

This target architecture is the normative baseline for:

~~~text
PYWORKFLOWKIT_V2_PUBLIC_API_SPEC.md
PYWORKFLOWKIT_V2_IMPLEMENTATION_ROADMAP.md
~~~